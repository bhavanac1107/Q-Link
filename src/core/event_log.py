"""Event log utilities for Q-Link.

The ``EventLog`` class provides a convenient way to inspect the per-qubit
trajectory of a simulation run (Alice's bits/bases, Eve's optional actions,
Bob's bases/bits, and the sifted mask).  It can be converted to a pandas
DataFrame for interactive exploration or to a simple list of dictionaries
for UI rendering.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional

from .protocol import ProtocolResult


@dataclass
class EventLog:
    """Container holding a per-qubit timeline for a QKD run.

    Attributes
    ----------
    qubit_index : np.ndarray
        Array of qubit indices (0 ... n-1).
    alice_bit : np.ndarray
        Alice's raw key bits.
    alice_basis : np.ndarray
        Alice's preparation bases (0 = Z, 1 = X).
    eve_basis : Optional[np.ndarray]
        Eve's measurement bases (``None`` if no intercept).
    eve_bit : Optional[np.ndarray]
        Bits measured by Eve (``None`` if no intercept).
    bob_basis : np.ndarray
        Bob's measurement bases.
    bob_bit : np.ndarray
        Bits measured by Bob.
    sifted : np.ndarray
        Boolean mask indicating whether the qubit was kept after sifting.
    """
    qubit_index: np.ndarray
    alice_bit: np.ndarray
    alice_basis: np.ndarray
    eve_basis: Optional[np.ndarray]
    eve_bit: Optional[np.ndarray]
    bob_basis: np.ndarray
    bob_bit: np.ndarray
    sifted: np.ndarray

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
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Return a pandas ``DataFrame`` with one row per qubit."""
        data: Dict[str, list] = {
            "index": self.qubit_index.tolist(),
            "alice_bit": self.alice_bit.tolist(),
            "alice_basis": self.alice_basis.tolist(),
            "bob_basis": self.bob_basis.tolist(),
            "bob_bit": self.bob_bit.tolist(),
            "sifted": self.sifted.tolist(),
        }
        if self.eve_basis is not None:
            data["eve_basis"] = self.eve_basis.tolist()
        if self.eve_bit is not None:
            data["eve_bit"] = self.eve_bit.tolist()
        return pd.DataFrame(data)

    def as_dicts(self) -> List[Dict]:
        """Return a list of plain dictionaries (JSON-serialisable)."""
        rows: List[Dict] = []
        for i in range(self.qubit_index.size):
            row: Dict = {
                "index": int(self.qubit_index[i]),
                "alice_bit": int(self.alice_bit[i]),
                "alice_basis": int(self.alice_basis[i]),
                "bob_basis": int(self.bob_basis[i]),
                "bob_bit": int(self.bob_bit[i]),
                "sifted": bool(self.sifted[i]),
            }
            if self.eve_basis is not None:
                row["eve_basis"] = int(self.eve_basis[i])
            if self.eve_bit is not None:
                row["eve_bit"] = int(self.eve_bit[i])
            rows.append(row)
        return rows
