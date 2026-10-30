"""Core protocol abstractions and result container for Q-Link.

Defines shared data structures for all protocol implementations.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import numpy as np


@dataclass
class ProtocolResult:
    """Container for per-qubit simulation data and derived metrics."""
    n_qubits: int
    alice_bits: np.ndarray
    alice_bases: np.ndarray
    eve_bases: Optional[np.ndarray] = None
    eve_results: Optional[np.ndarray] = None
    bob_bases: np.ndarray = None  # type: ignore[assignment]
    bob_bits: np.ndarray = None  # type: ignore[assignment]
    sifted_mask: np.ndarray = None  # type: ignore[assignment]
    sampled_mask: np.ndarray = None  # type: ignore[assignment]
    qber: float = 0.0
    final_key_len: int = 0
    alert_level: str = "NORMAL"
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.sifted_mask is not None:
            self.sifted_mask = np.asarray(self.sifted_mask, dtype=bool)
        if self.sampled_mask is not None:
            self.sampled_mask = np.asarray(self.sampled_mask, dtype=bool)


class Protocol(abc.ABC):
    """Abstract base class for a QKD protocol simulation."""

    def __init__(
        self,
        n_qubits: int,
        rng: np.random.Generator,
        *,
        channel_error: float = 0.0,
        intercept_rate: float = 0.0,
        qber_threshold: float = 0.11,
    ) -> None:
        self.n = n_qubits
        self.rng = rng
        self.channel_error = channel_error
        self.intercept_rate = intercept_rate
        self.qber_threshold = qber_threshold

    @abc.abstractmethod
    def prepare(self) -> None:
        ...

    @abc.abstractmethod
    def transmit(self) -> None:
        ...

    @abc.abstractmethod
    def measure(self) -> None:
        ...

    @abc.abstractmethod
    def sift(self) -> None:
        ...

    @abc.abstractmethod
    def estimate_qber(self) -> None:
        ...

    @abc.abstractmethod
    def reconcile(self) -> None:
        ...

    @abc.abstractmethod
    def privacy_amplify(self) -> None:
        ...

    @abc.abstractmethod
    def build_result(self) -> ProtocolResult:
        ...

    def run(self) -> ProtocolResult:
        self.prepare()
        self.transmit()
        self.measure()
        self.sift()
        self.estimate_qber()
        self.reconcile()
        self.privacy_amplify()
        return self.build_result()
