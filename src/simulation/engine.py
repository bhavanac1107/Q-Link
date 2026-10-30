"""Simulation engine for Q-Link.

Utility to run a QKD protocol simulation across different execution backends:
- NumPy (default)
- Qiskit Aer
- IBM Quantum Hardware
"""

from __future__ import annotations

from typing import Any, Optional
import numpy as np

from src.core.protocol import Protocol, ProtocolResult
from src.simulation.backends import get_backend


def run_simulation(
    protocol: Protocol,
    backend_name: str = "NumPy",
    **kwargs: Any,
) -> ProtocolResult:
    """Execute the protocol pipeline and return the populated ProtocolResult.

    Parameters
    ----------
    protocol : Protocol
        An instantiated protocol (e.g. BB84, B92, E91).
    backend_name : str
        Target backend ("NumPy", "Qiskit Aer", or "IBM Quantum hardware").
        For BB84, delegates to the chosen quantum or classical backend.
        Other protocols default gracefully to NumPy execution.
    **kwargs : Any
        Backend-specific arguments such as noise_model_name.

    Returns
    -------
    ProtocolResult
        The populated result object containing per-qubit data and derived metrics.
    """
    clean_backend = backend_name.lower()
    # Check if quantum backend requested for BB84
    proto_class_name = protocol.__class__.__name__.lower()
    if "bb84" in proto_class_name and ("aer" in clean_backend or "ibm" in clean_backend or "hardware" in clean_backend):
        backend = get_backend(backend_name, **kwargs)
        return backend.run_bb84(
            n_qubits=protocol.n,
            rng=protocol.rng,
            channel_error=protocol.channel_error,
            intercept_rate=protocol.intercept_rate,
            qber_threshold=protocol.qber_threshold,
            **kwargs,
        )

    # Standard / NumPy protocol execution
    result = protocol.run()
    if "backend" not in result.extra:
        result.extra["backend"] = "NumPy"
    if "data_source" not in result.extra:
        result.extra["data_source"] = "simulated"
    return result


__all__ = ["run_simulation"]
