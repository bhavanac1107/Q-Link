"""B92 protocol implementation for Q-Link.

Uses the same intercept logic as BB84: Eve only has data for qubits she
actually intercepted (-1 elsewhere).
"""

from __future__ import annotations

import numpy as np

from .protocol import Protocol, ProtocolResult
from .alerts import compute_alert, AlertConfig


class B92(Protocol):
    """Simplified B92 simulation compatible with the ``Protocol`` interface."""

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
        self.alice_bases = np.zeros(self.n, dtype=np.int8)
        self.eve_bases = None
        self.eve_results = None
        self.bob_bases = np.empty(self.n, dtype=np.int8)
        self.bob_bits = np.empty(self.n, dtype=np.int8)
        self.sifted_mask = np.empty(self.n, dtype=bool)
        self.sampled_mask = np.empty(self.n, dtype=bool)
        self.qber = 0.0
        self.final_key_len = 0
        self.alert_level = "NORMAL"

    def prepare(self) -> None:
        """Alice chooses bits uniformly; basis is implicit (bit 0->Z, bit 1->X).

        In B92 the preparation basis is determined by the bit value:
          bit 0 -> |0> (Z basis, basis=0)
          bit 1 -> |+> (X basis, basis=1)
        We store this as alice_bases so the result is self-consistent.
        """
        self.alice_bits = self.rng.integers(0, 2, size=self.n, dtype=np.int8)
        # The actual basis used for preparation (not a dummy)
        self.alice_bases = np.where(self.alice_bits == 0, 0, 1).astype(np.int8)
        self._prepared_basis = self.alice_bases

    def transmit(self) -> None:
        """Apply channel error and optional Eve intercept-resend."""
        transmitted_bits = self.alice_bits.copy()
        transmitted_bases = self._prepared_basis.copy()

        if self.intercept_rate > 0.0:
            eve_intercept = self.rng.random(self.n) < self.intercept_rate
            self.eve_bases = np.full(self.n, -1, dtype=np.int8)
            self.eve_results = np.full(self.n, -1, dtype=np.int8)

            idx = np.where(eve_intercept)[0]
            if idx.size > 0:
                rand_bases = self.rng.integers(0, 2, size=idx.size, dtype=np.int8)
                self.eve_bases[idx] = rand_bases

                prep_bases_at = self._prepared_basis[idx]
                alice_bits_at = self.alice_bits[idx]
                bases_match = rand_bases == prep_bases_at
                rand_bits = self.rng.integers(0, 2, size=idx.size, dtype=np.int8)
                eve_measured = np.where(bases_match, alice_bits_at, rand_bits)
                self.eve_results[idx] = eve_measured

                transmitted_bits[idx] = eve_measured
                transmitted_bases[idx] = rand_bases
        else:
            self.eve_bases = None
            self.eve_results = None

        if self.channel_error > 0.0:
            flip_mask = self.rng.random(self.n) < self.channel_error
            transmitted_bits = np.where(flip_mask, 1 - transmitted_bits, transmitted_bits)

        self._channel_bits = transmitted_bits
        self._channel_bases = transmitted_bases

    def measure(self) -> None:
        """Bob chooses a random basis and measures."""
        self.bob_bases = self.rng.integers(0, 2, size=self.n, dtype=np.int8)
        same_basis = self.bob_bases == self._channel_bases
        self.bob_bits = np.where(
            same_basis,
            self._channel_bits,
            self.rng.integers(0, 2, size=self.n, dtype=np.int8),
        )

    def sift(self) -> None:
        """In B92, only keep qubits where Bob's basis matches the prepared basis."""
        self.sifted_mask = self.bob_bases == self._channel_bases

    def estimate_qber(self) -> None:
        """Same sampling logic as BB84."""
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
