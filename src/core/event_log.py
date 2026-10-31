"""Event log utilities for Q-Link.

Provides protocol-aware event log representation for BB84, B92, and E91:
- BB84: alice_bit, alice_basis, bob_basis, bob_bit, sifted, sampled.
- B92: alice_bit, alice_state, bob_basis, bob_measured, bob_inferred_bit, outcome, sifted, sampled.
- E91: alice_bit, alice_angle, bob_angle, bob_bit, round_type, sifted, sampled.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import numpy as np
import pandas as pd

from .protocol import ProtocolResult


@dataclass
class EventLog:
    """Container holding a per-qubit timeline for a QKD run."""

    qubit_index: np.ndarray
    alice_bit: np.ndarray
    alice_basis: np.ndarray
    eve_basis: Optional[np.ndarray]
    eve_bit: Optional[np.ndarray]
    bob_basis: np.ndarray
    bob_bit: np.ndarray
    sifted: np.ndarray
    sampled: Optional[np.ndarray] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_result(cls, result: ProtocolResult) -> "EventLog":
        """Create an ``EventLog`` from a ``ProtocolResult`` instance."""
        n = result.n_qubits
        return cls(
            qubit_index=np.arange(n),
            alice_bit=result.alice_bits,
            alice_basis=result.alice_bases,
            eve_basis=result.eve_bases,
            eve_bit=result.eve_results,
            bob_basis=result.bob_bases,
            bob_bit=result.bob_bits,
            sifted=result.sifted_mask,
            sampled=result.sampled_mask,
            extra=result.extra or {},
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Return a protocol-appropriate pandas DataFrame for the event log."""
        proto = self.extra.get("protocol", "BB84")
        data: Dict[str, Any] = {}

        if proto == "B92" or "outcome_status" in self.extra:
            data["alice_bit"] = self.alice_bit.tolist()
            data["alice_state"] = self.extra.get(
                "encoded_states",
                ["|0>" if b == 0 else "|+>" for b in self.alice_bit],
            )
            data["bob_basis"] = [
                "Z" if b == 0 else "X" for b in self.bob_basis
            ]
            if "bob_measurements" in self.extra:
                data["bob_measured"] = self.extra["bob_measurements"]
            inferred = [
                int(b) if b in (0, 1) else "—" for b in self.bob_bit
            ]
            data["bob_inferred_bit"] = inferred
            data["outcome"] = self.extra.get(
                "outcome_status",
                ["CONCLUSIVE" if s else "INCONCLUSIVE" for s in self.sifted],
            )
            data["sifted"] = self.sifted.tolist()
            if self.sampled is not None:
                data["sampled"] = self.sampled.tolist()

        elif proto == "E91" or "round_types" in self.extra:
            data["alice_bit"] = self.alice_bit.tolist()
            data["alice_angle"] = self.extra.get(
                "alice_angles_str",
                [f"Setting {b}" for b in self.alice_basis],
            )
            data["bob_angle"] = self.extra.get(
                "bob_angles_str",
                [f"Setting {b}" for b in self.bob_basis],
            )
            data["bob_bit"] = self.bob_bit.tolist()
            data["round_type"] = self.extra.get(
                "round_types",
                ["KEY" if s else "TEST" for s in self.sifted],
            )
            data["sifted"] = self.sifted.tolist()
            if self.sampled is not None:
                data["sampled"] = self.sampled.tolist()

        else:  # BB84 and standard fallback
            data["alice_bit"] = self.alice_bit.tolist()
            data["alice_basis"] = [
                "Z" if b == 0 else "X" for b in self.alice_basis
            ]
            data["bob_basis"] = [
                "Z" if b == 0 else "X" for b in self.bob_basis
            ]
            data["bob_bit"] = self.bob_bit.tolist()
            data["sifted"] = self.sifted.tolist()
            if self.sampled is not None:
                data["sampled"] = self.sampled.tolist()

        # Eve interception tracking
        if self.eve_basis is not None and self.eve_bit is not None:
            eve_basis_col = []
            eve_bit_col = []
            for eb, er in zip(self.eve_basis, self.eve_bit):
                if eb < 0:
                    eve_basis_col.append("—")
                    eve_bit_col.append("—")
                else:
                    if proto == "E91":
                        all_e_angles = ["0°", "22.5°", "45°", "67.5°"]
                        eve_basis_col.append(all_e_angles[eb] if eb < len(all_e_angles) else str(eb))
                    else:
                        eve_basis_col.append("Z" if eb == 0 else "X")
                    eve_bit_col.append(int(er))
            data["eve_basis"] = eve_basis_col
            data["eve_result"] = eve_bit_col

        return pd.DataFrame(data)

    def as_dicts(self) -> List[Dict]:
        """Return a list of plain dictionaries."""
        df = self.to_dataframe()
        return df.to_dict(orient="records")
