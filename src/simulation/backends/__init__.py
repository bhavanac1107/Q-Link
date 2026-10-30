"""Backend registration and factory for Q-Link simulation engines.

Supports:
- NumPy (default, always available)
- Qiskit Aer (optional, available when qiskit and qiskit-aer are installed)
- IBM Quantum Hardware (optional, available when QISKIT_IBM_TOKEN is configured)
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from .base import Backend
from .numpy_backend import NumPyBackend
from .qiskit_circuits import QISKIT_AVAILABLE
from .ibm_hardware_backend import IBMHardwareBackend, get_ibm_token
from .noise import AVAILABLE_NOISE_MODELS, get_available_noise_model_names, load_noise_model

try:
    from .qiskit_aer_backend import QiskitAerBackend
    import qiskit_aer
    AER_AVAILABLE = True
except ImportError:
    QiskitAerBackend = None
    AER_AVAILABLE = False


def is_qiskit_available() -> bool:
    """Return True if qiskit is importable."""
    return QISKIT_AVAILABLE


def is_aer_available() -> bool:
    """Return True if both qiskit and qiskit_aer are available."""
    return bool(QISKIT_AVAILABLE and AER_AVAILABLE)


def is_ibm_hardware_available() -> bool:
    """Return True if qiskit is available and an IBM Quantum token is configured."""
    return bool(QISKIT_AVAILABLE and IBMHardwareBackend.is_configured())


def get_backend(name: str = "NumPy", **kwargs: Any) -> Backend:
    """Factory to retrieve a backend instance by name."""
    clean_name = name.lower()
    if "aer" in clean_name:
        if not is_aer_available():
            raise ImportError("Qiskit Aer backend is not installed. Run: pip install qiskit qiskit-aer")
        noise_model = kwargs.get("noise_model_name", "none")
        return QiskitAerBackend(noise_model_name=noise_model)
    elif "ibm" in clean_name or "hardware" in clean_name:
        if not is_qiskit_available():
            raise ImportError("Qiskit is not installed.")
        return IBMHardwareBackend()
    else:
        # Default to NumPy
        return NumPyBackend()


def list_available_backend_options() -> List[Dict[str, Any]]:
    """List selectable backends with their availability and status info."""
    options = [
        {
            "id": "numpy",
            "name": "NumPy (default)",
            "available": True,
            "description": "Fast vectorized simulation without quantum dependencies.",
        },
        {
            "id": "aer",
            "name": "Qiskit Aer simulator",
            "available": is_aer_available(),
            "description": "Simulates quantum circuits using Qiskit Aer with optional device noise models.",
        },
        {
            "id": "hardware",
            "name": "IBM Quantum hardware",
            "available": is_ibm_hardware_available(),
            "description": "Executes on real IBM Quantum superconducting hardware via Open Plan (job mode).",
        },
    ]
    return options
