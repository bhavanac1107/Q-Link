"""Qiskit Aer simulation backend for Q-Link.

Executes batched BB84 circuits on AerSimulator (ideal or with fake-backend noise models).
Uses basis-combination batching (at most 24 single-qubit circuits per job with shots=count)
for high throughput and low overhead.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, List, Tuple
import numpy as np

from src.core.protocol import ProtocolResult
from src.core.alerts import compute_alert, AlertConfig
from .base import Backend
from .qiskit_circuits import build_bb84_circuit, QISKIT_AVAILABLE
from .noise import load_noise_model, AVAILABLE_NOISE_MODELS


class QiskitAerBackend(Backend):
    """Qiskit Aer simulator backend with optional device noise models."""

    name: str = "Qiskit Aer"
    data_source: str = "simulated"

    def __init__(self, noise_model_name: str = "none") -> None:
        self.noise_model_name = noise_model_name

    def run_bb84(
        self,
        n_qubits: int,
        rng: np.random.Generator,
        *,
        channel_error: float = 0.0,
        intercept_rate: float = 0.0,
        qber_threshold: float = 0.11,
        **kwargs: Any,
    ) -> ProtocolResult:
        if not QISKIT_AVAILABLE:
            raise ImportError(
                "qiskit and qiskit-aer are required to run on Qiskit Aer backend. "
                "Install them with: pip install qiskit qiskit-aer"
            )

        try:
            from qiskit_aer import AerSimulator
        except ImportError:
            raise ImportError(
                "qiskit-aer is required to run on Qiskit Aer backend. "
                "Install it with: pip install qiskit-aer"
            )

        # 1. Prepare AerSimulator with optional noise model
        noise_name = kwargs.get("noise_model_name", self.noise_model_name)
        noise_model = load_noise_model(noise_name)
        sim_kwargs: Dict[str, Any] = {}
        if noise_model is not None:
            sim_kwargs["noise_model"] = noise_model

        # AerSimulator instance
        simulator = AerSimulator(**sim_kwargs)

        # 2. Draw Alice's bits and bases
        alice_bits = rng.integers(0, 2, size=n_qubits, dtype=np.int8)
        alice_bases = rng.integers(0, 2, size=n_qubits, dtype=np.int8)

        # 3. Draw Eve's intercept decisions and bases
        if intercept_rate > 0.0:
            eve_intercept_mask = rng.random(n_qubits) < intercept_rate
            eve_bases_raw = rng.integers(0, 2, size=n_qubits, dtype=np.int8)
        else:
            eve_intercept_mask = np.zeros(n_qubits, dtype=bool)
            eve_bases_raw = np.zeros(n_qubits, dtype=np.int8)

        # 4. Draw Bob's bases
        bob_bases = rng.integers(0, 2, size=n_qubits, dtype=np.int8)

        # 5. Group qubits into configuration keys:
        # (a_bit, a_basis, is_intercepted, e_basis, b_basis)
        config_to_indices: Dict[Tuple, List[int]] = {}
        for i in range(n_qubits):
            is_int = bool(eve_intercept_mask[i])
            e_b = int(eve_bases_raw[i]) if is_int else None
            key = (int(alice_bits[i]), int(alice_bases[i]), is_int, e_b, int(bob_bases[i]))
            if key not in config_to_indices:
                config_to_indices[key] = []
            config_to_indices[key].append(i)

        # 6. Build batched circuits (at most 24 circuits total)
        circuits: List[Any] = []
        key_list: List[Tuple] = []
        shot_counts: List[int] = []

        for key, indices in config_to_indices.items():
            a_bit, a_base, is_int, e_b, b_base = key
            qc = build_bb84_circuit(
                alice_bit=a_bit,
                alice_basis=a_base,
                eve_intercept=is_int,
                eve_basis=e_b,
                bob_basis=b_base,
            )
            circuits.append(qc)
            key_list.append(key)
            shot_counts.append(len(indices))

        # 7. Execute batch on Aer simulator
        # Run individual circuits with shots=count and memory=True
        bob_bits = np.empty(n_qubits, dtype=np.int8)
        if intercept_rate > 0.0:
            eve_bases = np.full(n_qubits, -1, dtype=np.int8)
            eve_results = np.full(n_qubits, -1, dtype=np.int8)
        else:
            eve_bases = None
            eve_results = None

        for qc, key, count in zip(circuits, key_list, shot_counts):
            indices = config_to_indices[key]
            is_int = key[2]

            # Execute circuit for this configuration
            # In AerSimulator, run with shots=count and memory=True
            job = simulator.run(qc, shots=count, memory=True)
            result_obj = job.result()
            memory = result_obj.get_memory(qc)

            # Assign measured bits to qubit indices
            for pos, mem_str in enumerate(memory):
                idx = indices[pos]
                # Qiskit orders classical bits right-to-left: 'c[1] c[0]'
                clean_str = mem_str.replace(" ", "")
                if is_int:
                    # c[0] = Eve, c[1] = Bob
                    b_val = int(clean_str[0])
                    e_val = int(clean_str[-1])
                    bob_bits[idx] = b_val
                    if eve_bases is not None:
                        eve_bases[idx] = key[3]
                    if eve_results is not None:
                        eve_results[idx] = e_val
                else:
                    # Single classical bit = Bob
                    bob_bits[idx] = int(clean_str[0])

        # 8. Apply channel bit-flip noise if channel_error > 0
        if channel_error > 0.0:
            flip_mask = rng.random(n_qubits) < channel_error
            bob_bits = np.where(flip_mask, 1 - bob_bits, bob_bits).astype(np.int8)

        # 9. Sifting
        sifted_mask = alice_bases == bob_bases

        # 10. QBER estimation
        sifted_indices = np.where(sifted_mask)[0]
        sifted_len = sifted_indices.size
        if sifted_len == 0:
            qber = float("nan")
            sampled_mask = np.zeros(n_qubits, dtype=bool)
            final_key_len = 0
        else:
            sample_size = max(1, int(0.10 * sifted_len))
            sample_indices = rng.choice(sifted_indices, size=sample_size, replace=False)
            sampled_mask = np.zeros(n_qubits, dtype=bool)
            sampled_mask[sample_indices] = True
            mismatches = alice_bits[sample_indices] != bob_bits[sample_indices]
            qber = float(mismatches.mean())
            final_key_len = sifted_len - sample_size

        alert_level = compute_alert(qber, AlertConfig(qber_threshold)).value

        noise_desc = AVAILABLE_NOISE_MODELS.get(noise_name, noise_name)

        return ProtocolResult(
            n_qubits=n_qubits,
            alice_bits=alice_bits,
            alice_bases=alice_bases,
            eve_bases=eve_bases,
            eve_results=eve_results,
            bob_bases=bob_bases,
            bob_bits=bob_bits,
            sifted_mask=sifted_mask,
            sampled_mask=sampled_mask,
            qber=qber,
            final_key_len=final_key_len,
            alert_level=alert_level,
            extra={
                "backend": self.name,
                "data_source": self.data_source,
                "noise_source": noise_desc,
                "noise_model_name": noise_name,
            },
        )
