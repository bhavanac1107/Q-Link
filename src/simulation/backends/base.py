"""Abstract base class for Q-Link simulation backends.

All backends (NumPy, Qiskit Aer, IBM Quantum hardware) implement this interface
and return an identical ProtocolResult dataclass.
"""

from __future__ import annotations

import abc
from typing import Any, Dict, Optional
import numpy as np

from src.core.protocol import ProtocolResult


class Backend(abc.ABC):
    """Abstract interface for quantum execution backends."""

    name: str = "base"
    data_source: str = "simulated"  # "simulated" or "hardware"

    @abc.abstractmethod
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
        """Run BB84 on this backend and return a standard ProtocolResult."""
        ...
