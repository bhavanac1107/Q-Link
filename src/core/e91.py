"""E91 (Ekert 91) protocol implementation for Q-Link.

Implements genuine entanglement-based QKD using Bell states and CHSH inequality testing:
1. Source emits entangled Bell pairs |Phi+> = (|00> + |11>) / sqrt(2).
2. Alice measures with angles:
     A1 = 0 deg (0)
     A2 = 22.5 deg (pi/8)
     A3 = 45 deg (pi/4)
3. Bob measures with angles:
     B1 = 22.5 deg (pi/8)
     B2 = 45 deg (pi/4)
     B3 = 67.5 deg (3*pi/8)
4. Matching angle rounds (A2==B1 or A3==B2) produce identical outcomes for the raw key.
5. Differing angle rounds (A1,B1), (A1,B3), (A3,B1), (A3,B3) test the CHSH Bell inequality:
     S = |E(A1, B1) - E(A1, B3) + E(A3, B1) + E(A3, B3)|
     Maximal quantum violation: S = 2*sqrt(2) approx 2.828 > 2.
     Classical / intercepted boundary: S <= 2.
6. Intercept-resend or channel noise collapses entanglement, dropping S towards <= 2
   and elevating QBER on the key rounds.
"""

from __future__ import annotations

from typing import Optional, List, Dict
import numpy as np

from .protocol import Protocol, ProtocolResult
from .alerts import compute_alert, AlertConfig


# Measurement angles in radians and degrees:
ALICE_ANGLES = np.array([0.0, np.pi / 8.0, np.pi / 4.0])           # 0°, 22.5°, 45°
BOB_ANGLES = np.array([np.pi / 8.0, np.pi / 4.0, 3.0 * np.pi / 8.0])  # 22.5°, 45°, 67.5°

ALICE_ANGLE_DEGS = ["0° (A1)", "22.5° (A2)", "45° (A3)"]
BOB_ANGLE_DEGS = ["22.5° (B1)", "45° (B2)", "67.5° (B3)"]


class E91(Protocol):
    """Scientifically authentic E91 entanglement-based simulation with CHSH Bell test."""

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
        self.alice_bases = np.empty(self.n, dtype=np.int8)  # Index 0, 1, 2 for A1, A2, A3
        self.bob_bits = np.empty(self.n, dtype=np.int8)
        self.bob_bases = np.empty(self.n, dtype=np.int8)    # Index 0, 1, 2 for B1, B2, B3

        self.eve_bases: Optional[np.ndarray] = None
        self.eve_results: Optional[np.ndarray] = None

        self.round_types: List[str] = []
        self.sifted_mask = np.empty(self.n, dtype=bool)
        self.sampled_mask = np.empty(self.n, dtype=bool)

        self.chsh_s: float = float("nan")
        self.bell_violated: bool = False
        self.correlations: Dict[str, float] = {}

        self.qber = 0.0
        self.final_key_len = 0
        self.alert_level = "NORMAL"

    def prepare(self) -> None:
        """Alice and Bob independently select their measurement settings."""
        self.alice_bases = self.rng.integers(0, 3, size=self.n, dtype=np.int8)
        self.bob_bases = self.rng.integers(0, 3, size=self.n, dtype=np.int8)

    def transmit(self) -> None:
        """Simulate distribution of entangled pairs through quantum channel with optional Eve."""
        pass  # Entanglement measurement correlation modeled directly in measure()

    def measure(self) -> None:
        """Measure entangled pairs according to chosen angles under quantum state mechanics."""
        a_angles = ALICE_ANGLES[self.alice_bases]
        b_angles = BOB_ANGLES[self.bob_bases]

        # Check for Eve intercept-resend attack
        eve_active = self.intercept_rate > 0.0
        if eve_active:
            eve_intercept_mask = self.rng.random(self.n) < self.intercept_rate
            self.eve_bases = np.full(self.n, -1, dtype=np.int8)
            self.eve_results = np.full(self.n, -1, dtype=np.int8)
        else:
            eve_intercept_mask = np.zeros(self.n, dtype=bool)
            self.eve_bases = None
            self.eve_results = None

        self.alice_bits = np.empty(self.n, dtype=np.int8)
        self.bob_bits = np.empty(self.n, dtype=np.int8)
        self.round_types = []

        all_angles = [0.0, np.pi / 8.0, np.pi / 4.0, 3.0 * np.pi / 8.0]

        for i in range(self.n):
            theta_a = a_angles[i]
            theta_b = b_angles[i]
            idx_a = self.alice_bases[i]
            idx_b = self.bob_bases[i]

            # Round classification:
            # Key rounds: matching angle A2 == B1 (22.5°) or A3 == B2 (45°)
            if (idx_a == 1 and idx_b == 0) or (idx_a == 2 and idx_b == 1):
                rtype = "KEY"
            elif (idx_a in (0, 2)) and (idx_b in (0, 2)):
                # (A1, B1), (A1, B3), (A3, B1), (A3, B3) -> CHSH Bell test
                rtype = "CHSH"
            else:
                rtype = "UNUSED"
            self.round_types.append(rtype)

            if eve_intercept_mask[i]:
                # Eve intercepts: measures in random basis, collapsing the entangled state
                eve_setting = int(self.rng.integers(0, 4))
                theta_e = all_angles[eve_setting]
                self.eve_bases[i] = eve_setting

                # Eve measures qubit in state |theta_e>
                eve_bit = int(self.rng.integers(0, 2))
                self.eve_results[i] = eve_bit

                # Alice and Bob now measure classical separable state conditioned on Eve's outcome
                # P(same as Eve) = cos^2(theta - theta_e)
                p_a_same = np.cos(theta_a - theta_e) ** 2
                bit_a = eve_bit if self.rng.random() < p_a_same else (1 - eve_bit)

                p_b_same = np.cos(theta_b - theta_e) ** 2
                bit_b = eve_bit if self.rng.random() < p_b_same else (1 - eve_bit)

            else:
                # Intact quantum entangled Bell pair |Phi+>
                # Alice outcome: 0 or 1 with 50/50 probability
                bit_a = int(self.rng.integers(0, 2))

                # Bob outcome correlation: P(bit_b == bit_a) = cos^2(theta_a - theta_b)
                p_same = np.cos(theta_a - theta_b) ** 2
                bit_b = bit_a if self.rng.random() < p_same else (1 - bit_a)

            # Apply channel error if present
            if self.channel_error > 0.0:
                if self.rng.random() < self.channel_error:
                    bit_a = 1 - bit_a
                if self.rng.random() < self.channel_error:
                    bit_b = 1 - bit_b

            self.alice_bits[i] = bit_a
            self.bob_bits[i] = bit_b

    def sift(self) -> None:
        """In E91, sifting retains ONLY matching-angle key rounds.
        Rounds used for CHSH Bell inequality testing are separated from key generation.
        """
        self.sifted_mask = np.array([rt == "KEY" for rt in self.round_types], dtype=bool)

    def estimate_qber(self) -> None:
        """Sample a subset of the key rounds to estimate QBER, and compute CHSH Bell statistic S."""
        sifted_indices = np.where(self.sifted_mask)[0]
        sifted_len = sifted_indices.size

        if sifted_len == 0:
            self.qber = float("nan")
            self.sampled_mask = np.zeros(self.n, dtype=bool)
            self.final_key_len = 0
        else:
            sample_size = max(1, int(0.10 * sifted_len))
            sample_indices = self.rng.choice(sifted_indices, size=sample_size, replace=False)

            self.sampled_mask = np.zeros(self.n, dtype=bool)
            self.sampled_mask[sample_indices] = True

            mismatches = self.alice_bits[sample_indices] != self.bob_bits[sample_indices]
            self.qber = float(np.mean(mismatches))
            self.final_key_len = sifted_len - sample_size

        # -------------------------------------------------------------
        # Compute CHSH Bell Parameter S from CHSH rounds:
        # S = |E(A1, B1) - E(A1, B3) + E(A3, B1) + E(A3, B3)|
        # -------------------------------------------------------------
        def compute_e(idx_a: int, idx_b: int) -> Optional[float]:
            mask = (self.alice_bases == idx_a) & (self.bob_bases == idx_b)
            if not np.any(mask):
                return None
            same = np.sum(self.alice_bits[mask] == self.bob_bits[mask])
            diff = np.sum(self.alice_bits[mask] != self.bob_bits[mask])
            return float((same - diff) / (same + diff))

        e_a1_b1 = compute_e(0, 0)  # A1=0°, B1=22.5°
        e_a1_b3 = compute_e(0, 2)  # A1=0°, B3=67.5°
        e_a3_b1 = compute_e(2, 0)  # A3=45°, B1=22.5°
        e_a3_b3 = compute_e(2, 2)  # A3=45°, B3=67.5°

        self.correlations = {
            "E(A1, B1)": e_a1_b1,
            "E(A1, B3)": e_a1_b3,
            "E(A3, B1)": e_a3_b1,
            "E(A3, B3)": e_a3_b3,
        }

        if None not in (e_a1_b1, e_a1_b3, e_a3_b1, e_a3_b3):
            self.chsh_s = float(abs(e_a1_b1 - e_a1_b3 + e_a3_b1 + e_a3_b3))
            self.bell_violated = bool(self.chsh_s > 2.0)
        else:
            self.chsh_s = float("nan")
            self.bell_violated = False

    def reconcile(self) -> None:
        """Reconciliation placeholder."""
        pass

    def privacy_amplify(self) -> None:
        """Privacy amplification placeholder."""
        pass

    def build_result(self) -> ProtocolResult:
        """Assemble ProtocolResult with E91 CHSH Bell inequality diagnostics."""
        # Alert calculation: abort if QBER is elevated OR if Bell test failed (S <= 2.0)
        base_alert = compute_alert(self.qber, AlertConfig(self.qber_threshold)).value
        if not np.isnan(self.chsh_s):
            if self.chsh_s <= 2.0 and base_alert == "NORMAL":
                self.alert_level = "WARNING"
            else:
                self.alert_level = base_alert
        else:
            self.alert_level = base_alert

        chsh_rounds_count = sum(1 for rt in self.round_types if rt == "CHSH")
        key_rounds_count = sum(1 for rt in self.round_types if rt == "KEY")

        bell_status_str = (
            f"VIOLATED (S = {self.chsh_s:.3f} > 2.0, Quantum Entanglement Confirmed)"
            if self.bell_violated
            else f"NOT VIOLATED (S = {self.chsh_s:.3f} <= 2.0, Classical or Compromised Channel)"
            if not np.isnan(self.chsh_s)
            else "INSUFFICIENT STATS (No CHSH pairs sampled)"
        )

        extra = {
            "protocol": "E91",
            "method": "Entanglement-based Bell state with CHSH test (E91)",
            "chsh_s": self.chsh_s,
            "chsh_violation": self.bell_violated,
            "bell_status": bell_status_str,
            "correlations": self.correlations,
            "round_types": self.round_types,
            "key_rounds_count": key_rounds_count,
            "chsh_rounds_count": chsh_rounds_count,
            "alice_angles_str": [ALICE_ANGLE_DEGS[b] for b in self.alice_bases],
            "bob_angles_str": [BOB_ANGLE_DEGS[b] for b in self.bob_bases],
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
