"""Tests for Q-Link Stage 1 simulation engine and BB84 execution."""

from __future__ import annotations

import numpy as np
import pytest

from src.core.bb84 import BB84
from src.simulation.engine import run_simulation


@pytest.fixture
def rng() -> np.random.Generator:
    """Return a reproducible NumPy random generator (seed 42)."""
    return np.random.default_rng(42)


def test_no_noise_no_eve(rng: np.random.Generator) -> None:
    protocol = BB84(n_qubits=20000, rng=rng, channel_error=0.0, intercept_rate=0.0)
    result = run_simulation(protocol)
    assert result.qber == pytest.approx(0.0, abs=0.005)
    assert result.alert_level == "NORMAL"
    assert result.sifted_mask.sum() > 0
    # Per-qubit arrays length check
    assert len(result.alice_bits) == 20000
    assert len(result.bob_bits) == 20000


def test_channel_error(rng: np.random.Generator) -> None:
    protocol = BB84(n_qubits=20000, rng=rng, channel_error=0.02, intercept_rate=0.0)
    result = run_simulation(protocol)
    assert result.qber == pytest.approx(0.02, abs=0.008)
    assert result.alert_level == "NORMAL"


def test_full_intercept(rng: np.random.Generator) -> None:
    protocol = BB84(n_qubits=20000, rng=rng, channel_error=0.0, intercept_rate=1.0)
    result = run_simulation(protocol)
    assert result.qber == pytest.approx(0.25, abs=0.02)
    assert result.alert_level == "ABORT"


def test_partial_intercept(rng: np.random.Generator) -> None:
    protocol = BB84(n_qubits=20000, rng=rng, channel_error=0.0, intercept_rate=0.4)
    result = run_simulation(protocol)
    assert result.qber == pytest.approx(0.10, abs=0.015)
    assert result.alert_level == "WARNING"


def test_sampled_bits_removed(rng: np.random.Generator) -> None:
    protocol = BB84(n_qubits=20000, rng=rng, channel_error=0.0, intercept_rate=0.0)
    result = run_simulation(protocol)
    sifted_len = int(result.sifted_mask.sum())
    sample_size = int(result.sampled_mask.sum())
    assert result.final_key_len == sifted_len - sample_size
    assert sample_size >= 1


def test_array_lengths(rng: np.random.Generator) -> None:
    protocol = BB84(n_qubits=20000, rng=rng, channel_error=0.01, intercept_rate=0.2)
    result = run_simulation(protocol)
    for arr in [
        result.alice_bits,
        result.alice_bases,
        result.bob_bits,
        result.bob_bases,
        result.sifted_mask,
        result.sampled_mask,
    ]:
        assert len(arr) == 20000
    if result.eve_bases is not None:
        assert len(result.eve_bases) == 20000
    if result.eve_results is not None:
        assert len(result.eve_results) == 20000
