"""B92 protocol implementation for Q-Link.

Implements genuine B92 protocol physics:
1. Alice encodes bit 0 as |0> (Z basis) and bit 1 as |+> (X basis).
2. Bob measures randomly in Z basis ({|0>, |1>}) or X basis ({|+>, |->}).
3. Bob's conclusive detection rule:
   - Measuring |1> in Z rules out |0> -> Conclusively infers Alice sent bit 1.
   - Measuring |-> in X rules out |+> -> Conclusively infers Alice sent bit 0.
   - Measuring |0> in Z or |+> in X is INCONCLUSIVE.
4. Sifting keeps ONLY conclusive rounds (NOT based on alice_basis == bob_basis).
5. Theoretical efficiency without eavesdropping/noise is ~25%.
"""

from __future__ import annotations

from typing import Optional, List
import numpy as np

from .protocol import Protocol, ProtocolResult
from .alerts import compute_alert, AlertConfig


# Quantum state representations:
# 0: |0> (computational zero)
# 1: |+> (Hadamard plus)
# 2: |1> (computational one)
# 3: |-> (Hadamard minus)
STATE_0 = 0
STATE_PLUS = 1
STATE_1 = 2
STATE_MINUS = 3

STATE_NAMES = {
    STATE_0: "|0>",
    STATE_PLUS: "|+>",
    STATE_1: "|1>",
    STATE_MINUS: "|->",
}


class B92(Protocol):
    """Scientifically authentic B92 quantum key distribution simulation."""

    def __init__(
        self,
        n_qubits: int,
        rng: np.random.Generator,
        *,
        channel_error: float = 0.0,
        intercept_rate: float = 0.0,
        qber_threshold: float = 0.11,
    ) -> None:
        super().__init__(
            n_qubits,
            rng,
            channel_error=channel_error,
            intercept_rate=intercept_rate,
            qber_threshold=qber_threshold,
        )
        self.alice_bits = np.empty(self.n, dtype=np.int8)
        self.alice_bases = np.empty(self.n, dtype=np.int8)
        self.alice_states = np.empty(self.n, dtype=np.int8)

        self.eve_bases: Optional[np.ndarray] = None
        self.eve_results: Optional[np.ndarray] = None

        self.bob_bases = np.empty(self.n, dtype=np.int8)
        self.bob_raw_measurements = np.empty(self.n, dtype=np.int8)
        self.bob_bits = np.empty(self.n, dtype=np.int8)  # Inferred bit (0, 1, or -1)
        self.conclusive_mask = np.empty(self.n, dtype=bool)

        self.sifted_mask = np.empty(self.n, dtype=bool)
        self.sampled_mask = np.empty(self.n, dtype=bool)
        self.qber = 0.0
        self.final_key_len = 0
        self.alert_level = "NORMAL"

    def prepare(self) -> None:
        """Alice encodes bits as non-orthogonal quantum states:
        Bit 0 -> |0> (basis 0: Z)
        Bit 1 -> |+> (basis 1: X)
        """
        self.alice_bits = self.rng.integers(0, 2, size=self.n, dtype=np.int8)
        # Alice's preparation basis: 0=Z, 1=X
        self.alice_bases = self.alice_bits.copy()
        # Quantum state: bit 0 -> STATE_0 (|0>), bit 1 -> STATE_PLUS (|+>)
        self.alice_states = np.where(self.alice_bits == 0, STATE_0, STATE_PLUS).astype(np.int8)

    def transmit(self) -> None:
        """Simulate quantum channel with optional Eve intercept-resend and noise."""
        curr_states = self.alice_states.copy()

        if self.intercept_rate > 0.0:
            intercept_mask = self.rng.random(self.n) < self.intercept_rate
            self.eve_bases = np.full(self.n, -1, dtype=np.int8)
            self.eve_results = np.full(self.n, -1, dtype=np.int8)

            idx = np.where(intercept_mask)[0]
            if idx.size > 0:
                # Eve randomly chooses measurement basis: 0=Z, 1=X
                eve_b = self.rng.integers(0, 2, size=idx.size, dtype=np.int8)
                self.eve_bases[idx] = eve_b

                # Eve measures the incoming quantum state
                eve_out_states = np.empty(idx.size, dtype=np.int8)
                eve_measured_bits = np.empty(idx.size, dtype=np.int8)

                for k, i_qubit in enumerate(idx):
                    state = curr_states[i_qubit]
                    basis = eve_b[k]

                    if basis == 0:  # Z basis measurement {|0>, |1>}
                        if state == STATE_0:
                            m_bit = 0
                            out_state = STATE_0
                        elif state == STATE_1:
                            m_bit = 1
                            out_state = STATE_1
                        else:  # STATE_PLUS or STATE_MINUS: 50% |0>, 50% |1>
                            m_bit = int(self.rng.integers(0, 2))
                            out_state = STATE_0 if m_bit == 0 else STATE_1
                    else:  # X basis measurement {|+>, |->}
                        if state == STATE_PLUS:
                            m_bit = 0
                            out_state = STATE_PLUS
                        elif state == STATE_MINUS:
                            m_bit = 1
                            out_state = STATE_MINUS
                        else:  # STATE_0 or STATE_1: 50% |+>, 50% |->
                            m_bit = int(self.rng.integers(0, 2))
                            out_state = STATE_PLUS if m_bit == 0 else STATE_MINUS

                    eve_measured_bits[k] = m_bit
                    eve_out_states[k] = out_state

                self.eve_results[idx] = eve_measured_bits
                # Eve resends her prepared post-measurement state into the channel
                curr_states[idx] = eve_out_states
        else:
            self.eve_bases = None
            self.eve_results = None

        # Channel noise (depolarizing / bit flip in current basis)
        if self.channel_error > 0.0:
            noise_mask = self.rng.random(self.n) < self.channel_error
            for i in np.where(noise_mask)[0]:
                s = curr_states[i]
                if s == STATE_0:
                    curr_states[i] = STATE_1
                elif s == STATE_1:
                    curr_states[i] = STATE_0
                elif s == STATE_PLUS:
                    curr_states[i] = STATE_MINUS
                elif s == STATE_MINUS:
                    curr_states[i] = STATE_PLUS

        self._received_states = curr_states

    def measure(self) -> None:
        """Bob independently chooses measurement basis (0=Z, 1=X) and projects.

        - If Bob measures in Z ({|0>, |1>}):
          * |1> is CONCLUSIVE -> Infers Alice sent bit 1 (since <1|0> = 0).
          * |0> is INCONCLUSIVE (both |0> and |+> can produce |0>).
        - If Bob measures in X ({|+>, |->}):
          * |-> is CONCLUSIVE -> Infers Alice sent bit 0 (since <-|+> = 0).
          * |+> is INCONCLUSIVE (both |+> and |0> can produce |+>).
        """
        self.bob_bases = self.rng.integers(0, 2, size=self.n, dtype=np.int8)
        self.bob_raw_measurements = np.empty(self.n, dtype=np.int8)
        self.bob_bits = np.full(self.n, -1, dtype=np.int8)
        self.conclusive_mask = np.zeros(self.n, dtype=bool)

        for i in range(self.n):
            state = self._received_states[i]
            b_basis = self.bob_bases[i]

            if b_basis == 0:  # Bob measures in Z basis {|0>, |1>}
                if state == STATE_0:
                    m = STATE_0
                elif state == STATE_1:
                    m = STATE_1
                else:  # STATE_PLUS or STATE_MINUS
                    m = STATE_0 if self.rng.random() < 0.5 else STATE_1
                
                self.bob_raw_measurements[i] = m
                if m == STATE_1:
                    self.conclusive_mask[i] = True
                    self.bob_bits[i] = 1  # Conclusively ruled out |0> -> sent bit was 1
            else:  # Bob measures in X basis {|+>, |->}
                if state == STATE_PLUS:
                    m = STATE_PLUS
                elif state == STATE_MINUS:
                    m = STATE_MINUS
                else:  # STATE_0 or STATE_1
                    m = STATE_PLUS if self.rng.random() < 0.5 else STATE_MINUS

                self.bob_raw_measurements[i] = m
                if m == STATE_MINUS:
                    self.conclusive_mask[i] = True
                    self.bob_bits[i] = 0  # Conclusively ruled out |+> -> sent bit was 0

    def sift(self) -> None:
        """In B92, sifting retains ONLY conclusive detections.
        Bob announces which pulses yielded a conclusive result without revealing
        the inferred bit value. This is NOT based on basis matching!
        """
        self.sifted_mask = self.conclusive_mask.copy()

    def estimate_qber(self) -> None:
        """Sample a subset of the conclusive key to estimate QBER.
        Sampled test bits are excluded from the final secret key.
        """
        sifted_indices = np.where(self.sifted_mask)[0]
        sifted_len = sifted_indices.size

        if sifted_len == 0:
            self.qber = float("nan")
            self.sampled_mask = np.zeros(self.n, dtype=bool)
            self.final_key_len = 0
            return

        sample_size = max(1, int(0.10 * sifted_len))
        sample_indices = self.rng.choice(sifted_indices, size=sample_size, replace=False)

        self.sampled_mask = np.zeros(self.n, dtype=bool)
        self.sampled_mask[sample_indices] = True

        mismatches = self.alice_bits[sample_indices] != self.bob_bits[sample_indices]
        self.qber = float(np.mean(mismatches))
        self.final_key_len = sifted_len - sample_size

    def reconcile(self) -> None:
        """Error reconciliation placeholder."""
        pass

    def privacy_amplify(self) -> None:
        """Privacy amplification placeholder."""
        pass

    def build_result(self) -> ProtocolResult:
        """Build standard ProtocolResult and attach B92-specific diagnostic metadata."""
        self.alert_level = compute_alert(
            self.qber, AlertConfig(self.qber_threshold)
        ).value

        # Build human-readable state and outcome representations for UI
        encoded_state_names = [STATE_NAMES[s] for s in self.alice_states]
        bob_meas_names = [STATE_NAMES[s] for s in self.bob_raw_measurements]
        outcome_status = [
            "CONCLUSIVE" if c else "INCONCLUSIVE" for c in self.conclusive_mask
        ]

        extra = {
            "protocol": "B92",
            "method": "Non-orthogonal 2-state POVM (B92)",
            "encoded_states": encoded_state_names,
            "bob_measurements": bob_meas_names,
            "outcome_status": outcome_status,
            "conclusive_count": int(self.conclusive_mask.sum()),
            "inconclusive_count": int((~self.conclusive_mask).sum()),
            "conclusive_rate": float(self.conclusive_mask.mean()),
            "sifted_count": int(self.sifted_mask.sum()),
            "sample_size": int(self.sampled_mask.sum()),
            "post_processing": "None (raw sifted key after sample exclusion)",
        }

        return ProtocolResult(
            n_qubits=self.n,
            alice_bits=self.alice_bits,
            alice_bases=self.alice_bases,
            eve_bases=self.eve_bases,
            eve_results=self.eve_results,
            bob_bases=self.bob_bases,
            bob_bits=self.bob_bits,
            sifted_mask=self.sifted_mask,
            sampled_mask=self.sampled_mask,
            qber=self.qber,
            final_key_len=self.final_key_len,
            alert_level=self.alert_level,
            extra=extra,
        )
