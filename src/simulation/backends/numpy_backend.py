"""Default NumPy simulation backend for Q-Link.

Wraps the pure-Python / NumPy implementation of BB84. Does not require Qiskit.
"""

from __future__ import annotations

from typing import Any
import numpy as np

from src.core.bb84 import BB84
from src.core.protocol import ProtocolResult
from .base import Backend


class NumPyBackend(Backend):
    """Native NumPy execution backend."""

    name: str = "NumPy"
    data_source: str = "simulated"

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
        proto = BB84(
            n_qubits=n_qubits,
            rng=rng,
            channel_error=channel_error,
            intercept_rate=intercept_rate,
            qber_threshold=qber_threshold,
        )
        res = proto.run()
        res.extra["backend"] = self.name
        res.extra["data_source"] = self.data_source
        res.extra["noise_source"] = "none"
        return res
