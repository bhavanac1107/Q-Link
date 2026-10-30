"""Noise model utilities for Qiskit Aer simulations in Q-Link.

Provides optional device noise models built from snapshot/fake backends in
qiskit_ibm_runtime.fake_provider for offline testing.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List

AVAILABLE_NOISE_MODELS: Dict[str, str] = {
    "none": "None (ideal simulation)",
    "fake_manila": "FakeManila (5 qubits, snapshot)",
    "fake_sherbrooke": "FakeSherbrooke (127 qubits, snapshot)",
    "fake_brisbane": "FakeBrisbane (127 qubits, snapshot)",
}


def get_available_noise_model_names() -> List[str]:
    """Return list of supported noise model identifier keys."""
    return list(AVAILABLE_NOISE_MODELS.keys())


def load_noise_model(name: str) -> Optional[Any]:
    """Load a Qiskit Aer NoiseModel from a fake backend snapshot.

    Returns None if name is 'none' or if noise packages are not installed.
    """
    if not name or name.lower() == "none":
        return None

    try:
        from qiskit_aer.noise import NoiseModel
    except ImportError:
        return None

    fake_backend = None

    # Try qiskit_ibm_runtime.fake_provider
    try:
        from qiskit_ibm_runtime import fake_provider
        name_lower = name.lower()
        if "manila" in name_lower:
            cls = getattr(fake_provider, "FakeManilaV2", None) or getattr(fake_provider, "FakeManila", None)
            if cls: fake_backend = cls()
        elif "sherbrooke" in name_lower:
            cls = getattr(fake_provider, "FakeSherbrooke", None)
            if cls: fake_backend = cls()
        elif "brisbane" in name_lower:
            cls = getattr(fake_provider, "FakeBrisbane", None)
            if cls: fake_backend = cls()
        elif "kyoto" in name_lower:
            cls = getattr(fake_provider, "FakeKyoto", None)
            if cls: fake_backend = cls()
    except Exception:
        pass

    # Fallback to qiskit.providers.fake_provider if older qiskit
    if fake_backend is None:
        try:
            from qiskit.providers import fake_provider
            name_lower = name.lower()
            if "manila" in name_lower:
                cls = getattr(fake_provider, "FakeManilaV2", None) or getattr(fake_provider, "FakeManila", None)
                if cls: fake_backend = cls()
            elif "sherbrooke" in name_lower:
                cls = getattr(fake_provider, "FakeSherbrooke", None)
                if cls: fake_backend = cls()
        except Exception:
            pass

    if fake_backend is not None:
        try:
            return NoiseModel.from_backend(fake_backend)
        except Exception:
            return None

    return None
