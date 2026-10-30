"""Tests for Qiskit Aer backend in Q-Link.

Verifies:
1. With no noise and no Eve: QBER is ~0.
2. With full intercept-resend (intercept_rate=1.0): QBER is ~0.25 (tolerance 0.02).
3. Backend metadata and data_source formatting.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.simulation.backends import get_backend, is_aer_available


@pytest.fixture
def aer_backend():
    """Ensure qiskit and qiskit_aer are installed before running Aer tests."""
    pytest.importorskip("qiskit")
    pytest.importorskip("qiskit_aer")
    return get_backend("aer", noise_model_name="none")


class TestQiskitAerBackend:
    def test_aer_clean_channel_zero_qber(self, aer_backend):
        """With no noise and no Eve, QBER should be zero."""
        rng = np.random.default_rng(42)
        n_qubits = 1000
        result = aer_backend.run_bb84(
            n_qubits=n_qubits,
            rng=rng,
            channel_error=0.0,
            intercept_rate=0.0,
            qber_threshold=0.11,
        )

        assert result.extra["backend"] == "Qiskit Aer"
        assert result.extra["data_source"] == "simulated"
        assert result.qber == pytest.approx(0.0, abs=1e-4)
        assert result.alert_level == "NORMAL"
        assert result.eve_bases is None
        assert result.eve_results is None

    def test_aer_full_intercept_resend_qber_25_percent(self, aer_backend):
        """With 100% intercept-resend, theoretical QBER is 25% (tolerance 0.02)."""
        rng = np.random.default_rng(12345)
        # Using 4000 qubits yields ~2000 sifted bits, ensuring tight statistical bounds
        n_qubits = 4000
        result = aer_backend.run_bb84(
            n_qubits=n_qubits,
            rng=rng,
            channel_error=0.0,
            intercept_rate=1.0,
            qber_threshold=0.11,
        )

        assert result.extra["backend"] == "Qiskit Aer"
        assert result.extra["data_source"] == "simulated"
        assert result.alert_level == "ABORT"
        assert result.eve_bases is not None
        assert result.eve_results is not None
        # Verify tolerance of 0.02 around theoretical 0.25
        assert result.qber == pytest.approx(0.25, abs=0.02)

    def test_aer_metadata_and_shapes(self, aer_backend):
        """Verify result structure matches ProtocolResult schema."""
        rng = np.random.default_rng(99)
        n_qubits = 200
        result = aer_backend.run_bb84(
            n_qubits=n_qubits,
            rng=rng,
            channel_error=0.03,
            intercept_rate=0.10,
        )

        assert len(result.alice_bits) == n_qubits
        assert len(result.alice_bases) == n_qubits
        assert len(result.bob_bits) == n_qubits
        assert len(result.bob_bases) == n_qubits
        assert result.sifted_mask.shape == (n_qubits,)
        assert result.sampled_mask.shape == (n_qubits,)
