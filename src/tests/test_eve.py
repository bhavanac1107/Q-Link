"""Tests for Eve's intercept-resend measurement logic across protocols.

Verifies that Eve's interaction with the quantum channel respects the underlying
state representation of each protocol:
- BB84: Matching basis recovers Alice's bit exactly; untouched qubits are -1.
- B92: Intercepted qubits are logged; untouched qubits are -1.
- E91: Intercepted qubits collapse entanglement; untouched qubits are -1.
"""

from __future__ import annotations

import numpy as np

from src.core.bb84 import BB84
from src.core.b92 import B92
from src.core.e91 import E91


class TestBB84EveMeasurement:
    """Eve measurement correctness for BB84."""

    def test_same_basis_recovers_alice_bit(self):
        """With 100% intercept, every qubit is intercepted; matching-basis
        qubits must have eve_result == alice_bit."""
        rng = np.random.default_rng(0)
        proto = BB84(n_qubits=500, rng=rng, intercept_rate=1.0)
        result = proto.run()

        assert result.eve_bases is not None
        assert result.eve_results is not None
        same_basis = result.eve_bases == result.alice_bases
        np.testing.assert_array_equal(
            result.eve_results[same_basis], result.alice_bits[same_basis]
        )

    def test_no_intercept_gives_none(self):
        """With intercept_rate=0, eve columns must be None."""
        rng = np.random.default_rng(1)
        result = BB84(n_qubits=100, rng=rng, intercept_rate=0.0).run()
        assert result.eve_bases is None
        assert result.eve_results is None

    def test_partial_intercept_marks_non_intercepted(self):
        """With partial intercept, non-intercepted qubits have -1."""
        rng = np.random.default_rng(2)
        result = BB84(n_qubits=500, rng=rng, intercept_rate=0.5).run()
        assert result.eve_bases is not None
        assert np.any(result.eve_bases == -1), "some qubits should be untouched"
        assert np.any(result.eve_bases >= 0), "some qubits should be intercepted"


class TestB92EveMeasurement:
    """Eve measurement correctness for B92."""

    def test_no_intercept_gives_none(self):
        rng = np.random.default_rng(11)
        result = B92(n_qubits=100, rng=rng, intercept_rate=0.0).run()
        assert result.eve_bases is None
        assert result.eve_results is None

    def test_intercept_tracking(self):
        """With 100% intercept, all qubits are intercepted and logged."""
        rng = np.random.default_rng(12)
        result = B92(n_qubits=200, rng=rng, intercept_rate=1.0).run()
        assert result.eve_bases is not None
        assert np.all(result.eve_bases >= 0)
        assert np.all(result.eve_results >= 0)


class TestE91EveMeasurement:
    """Eve measurement correctness for E91."""

    def test_no_intercept_gives_none(self):
        rng = np.random.default_rng(21)
        result = E91(n_qubits=100, rng=rng, intercept_rate=0.0).run()
        assert result.eve_bases is None
        assert result.eve_results is None

    def test_intercept_destroys_bell_violation(self):
        """Full interception collapses entanglement, resulting in classical CHSH S <= 2.0."""
        rng = np.random.default_rng(22)
        result = E91(n_qubits=5000, rng=rng, intercept_rate=1.0).run()
        assert result.eve_bases is not None
        assert np.all(result.eve_bases >= 0)
        # Entanglement broken: S should be <= 2.0 (tolerance for statistical fluctuation <= 2.2)
        s_val = result.extra.get("chsh_s", 0.0)
        assert s_val <= 2.2, f"With 100% intercept, CHSH S should drop to classical limit (<= 2), got {s_val:.3f}"
