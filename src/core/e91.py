"""E91 protocol implementation for Q-Link.

A simplified entanglement-based protocol.  Uses the same per-qubit Eve
masking (-1 for non-intercepted qubits) as BB84 and B92.
"""

from __future__ import annotations

import numpy as np

from .protocol import Protocol, ProtocolResult
from .alerts import compute_alert, AlertConfig


class E91(Protocol):
    """Simplified E91 (entanglement-based) simulation."""

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
            n_qubits, rng,
            channel_error=channel_error,
            intercept_rate=intercept_rate,
            qber_threshold=qber_threshold,
        )
        self.alice_bits = np.empty(self.n, dtype=np.int8)
        self.alice_bases = np.empty(self.n, dtype=np.int8)
        self.bob_bits = np.empty(self.n, dtype=np.int8)
        self.bob_bases = np.empty(self.n, dtype=np.int8)
        self.eve_bases = None
        self.eve_results = None
        self.sifted_mask = np.ones(self.n, dtype=bool)
        self.sampled_mask = np.empty(self.n, dtype=bool)
        self.qber = 0.0
        self.final_key_len = 0
        self.alert_level = "NORMAL"

    def prepare(self) -> None:
        """Generate perfectly correlated bits for Alice and Bob."""
        self.alice_bits = self.rng.integers(0, 2, size=self.n, dtype=np.int8)
        self.bob_bits = self.alice_bits.copy()
        self.alice_bases = self.rng.integers(0, 2, size=self.n, dtype=np.int8)
        self.bob_bases = self.rng.integers(0, 2, size=self.n, dtype=np.int8)

    def transmit(self) -> None:
        """Apply channel error and optional Eve intercept-resend."""
        if self.channel_error > 0.0:
            flip_a = self.rng.random(self.n) < self.channel_error
            self.alice_bits = np.where(flip_a, 1 - self.alice_bits, self.alice_bits)
            flip_b = self.rng.random(self.n) < self.channel_error
            self.bob_bits = np.where(flip_b, 1 - self.bob_bits, self.bob_bits)

        if self.intercept_rate > 0.0:
            eve_intercept = self.rng.random(self.n) < self.intercept_rate
            self.eve_bases = np.full(self.n, -1, dtype=np.int8)
            self.eve_results = np.full(self.n, -1, dtype=np.int8)

            idx = np.where(eve_intercept)[0]
            if idx.size > 0:
                rand_bases = self.rng.integers(0, 2, size=idx.size, dtype=np.int8)
                self.eve_bases[idx] = rand_bases

                alice_bases_at = self.alice_bases[idx]
                alice_bits_at = self.alice_bits[idx]
                bases_match = rand_bases == alice_bases_at
                rand_bits = self.rng.integers(0, 2, size=idx.size, dtype=np.int8)
                eve_measured = np.where(bases_match, alice_bits_at, rand_bits)
                self.eve_results[idx] = eve_measured

                self.alice_bits[idx] = eve_measured
                self.alice_bases[idx] = rand_bases
        else:
            self.eve_bases = None
            self.eve_results = None

    def measure(self) -> None:
        """Measurements are already represented by the bits set in ``prepare``."""
        pass

    def sift(self) -> None:
        """Entanglement keeps all bits; sift mask stays true everywhere."""
        self.sifted_mask = np.ones(self.n, dtype=bool)

    def estimate_qber(self) -> None:
        """Sample a subset of the sifted key to estimate QBER."""
        sifted_indices = np.where(self.sifted_mask)[0]
        sifted_len = sifted_indices.size
        if sifted_len == 0:
            self.qber = 0.0
            self.sampled_mask = np.zeros(self.n, dtype=bool)
            self.final_key_len = 0
            return
        sample_size = max(1, int(0.01 * sifted_len))
        sample_indices = self.rng.choice(sifted_indices, size=sample_size, replace=False)
        self.sampled_mask = np.zeros(self.n, dtype=bool)
        self.sampled_mask[sample_indices] = True
        mismatches = self.alice_bits[sample_indices] != self.bob_bits[sample_indices]
        self.qber = mismatches.mean()
        self.final_key_len = sifted_len - sample_size

    def reconcile(self) -> None:
        pass

    def privacy_amplify(self) -> None:
        pass

    def build_result(self) -> ProtocolResult:
        self.alert_level = compute_alert(
            self.qber, AlertConfig(self.qber_threshold)
        ).value
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
        )
