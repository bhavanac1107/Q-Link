"""BB84 protocol implementation for Q-Link.

This class inherits from the abstract ``Protocol`` defined in
``src.core.protocol`` and provides concrete implementations of all steps.
It stores per-qubit arrays so that later stages can reuse them without
refactoring.
"""

from __future__ import annotations

import numpy as np

from .protocol import Protocol, ProtocolResult
from .alerts import compute_alert, AlertConfig


class BB84(Protocol):
    """Concrete BB84 protocol simulation."""

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
        self.eve_bases = None      # type: ignore[assignment]
        self.eve_results = None    # type: ignore[assignment]
        self.bob_bases = np.empty(self.n, dtype=np.int8)
        self.bob_bits = np.empty(self.n, dtype=np.int8)
        self.sifted_mask = np.empty(self.n, dtype=bool)
        self.sampled_mask = np.empty(self.n, dtype=bool)
        self.qber = 0.0
        self.final_key_len = 0
        self.alert_level = "NORMAL"

    # -----------------------------------------------------------------
    # Step implementations
    # -----------------------------------------------------------------
    def prepare(self) -> None:
        """Alice randomly selects bits (0/1) and bases (0=Z, 1=X)."""
        self.alice_bits = self.rng.integers(0, 2, size=self.n, dtype=np.int8)
        self.alice_bases = self.rng.integers(0, 2, size=self.n, dtype=np.int8)

    def transmit(self) -> None:
        """Simulate the quantum channel and optional Eve intercept-resend.

        * Channel error flips the transmitted bit with probability
          ``channel_error`` regardless of basis.
        * Eve intercepts with probability ``intercept_rate``.  When she
          intercepts she measures in a random basis; if her basis matches
          Alice's she obtains Alice's bit *exactly*, otherwise she gets a
          random bit.  She resends a qubit prepared in her basis with the
          measured bit.
        * Qubits Eve did NOT intercept have ``-1`` in the eve_bases and
          eve_results arrays so the UI can show them as blank.
        """
        transmitted_bits = self.alice_bits.copy()
        transmitted_bases = self.alice_bases.copy()

        if self.intercept_rate > 0.0:
            eve_intercept = self.rng.random(self.n) < self.intercept_rate

            # -1 means "Eve did not touch this qubit"
            self.eve_bases = np.full(self.n, -1, dtype=np.int8)
            self.eve_results = np.full(self.n, -1, dtype=np.int8)

            idx = np.where(eve_intercept)[0]
            if idx.size > 0:
                # Eve picks a random basis for each intercepted qubit
                rand_bases = self.rng.integers(0, 2, size=idx.size, dtype=np.int8)
                self.eve_bases[idx] = rand_bases

                # Measurement outcome:
                #   same basis as Alice  -> Eve gets Alice's bit exactly
                #   different basis      -> Eve gets a random bit
                alice_bases_at = self.alice_bases[idx]
                alice_bits_at = self.alice_bits[idx]
                bases_match = rand_bases == alice_bases_at
                rand_bits = self.rng.integers(0, 2, size=idx.size, dtype=np.int8)
                eve_measured = np.where(bases_match, alice_bits_at, rand_bits)
                self.eve_results[idx] = eve_measured

                # Eve resends her measured bit in her basis
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
        """Bob chooses random bases and measures the received qubits."""
        self.bob_bases = self.rng.integers(0, 2, size=self.n, dtype=np.int8)
        same_basis = self.bob_bases == self._channel_bases
        self.bob_bits = np.where(
            same_basis,
            self._channel_bits,
            self.rng.integers(0, 2, size=self.n, dtype=np.int8),
        )

    def sift(self) -> None:
        """Create a mask of positions where Alice and Bob used the same basis."""
        self.sifted_mask = self.alice_bases == self.bob_bases

    def estimate_qber(self) -> None:
        """Randomly sample a subset of the sifted key to estimate QBER.

        The sampled test bits are revealed publicly and strictly removed from
        the final secret key. If the sifted key is empty, QBER is NaN and
        final key length is 0.
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
        """Classical error reconciliation placeholder.
        No error correction is applied in this simulation model; uncorrected
        bits are kept directly in the raw key.
        """
        pass

    def privacy_amplify(self) -> None:
        """Privacy amplification placeholder.
        No hashing or shortening is applied beyond test bit exclusion.
        """
        pass

    def build_result(self) -> ProtocolResult:
        """Collect all data into a ``ProtocolResult`` instance."""
        self.alert_level = compute_alert(
            self.qber, AlertConfig(self.qber_threshold)
        ).value
        extra = {
            "protocol": "BB84",
            "method": "Prepare-and-measure 4-state (BB84)",
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
