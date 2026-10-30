"""Tests for Eve's intercept-resend measurement logic.

Key invariant: when Eve intercepts a qubit and her randomly chosen basis
matches Alice's preparation basis, Eve MUST obtain Alice's bit exactly.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.core.bb84 import BB84
from src.core.b92 import B92
from src.core.e91 import E91


# -------------------------------------------------------------------
# Helper
# -------------------------------------------------------------------
def _check_eve_same_basis_gets_alice_bit(result):
    """Assert that every intercepted qubit where Eve's basis == Alice's basis
    has eve_result == alice_bit.  Also check that non-intercepted qubits
    have eve_bases == -1 and eve_results == -1.
    """
    if result.eve_bases is None:
        # Eve was not active at all -- nothing to check
        return

    eve_b = result.eve_bases
    eve_r = result.eve_results

    # Non-intercepted qubits must be -1
    not_intercepted = eve_b == -1
    assert np.all(eve_r[not_intercepted] == -1), (
        "eve_results should be -1 for non-intercepted qubits"
    )

    # Intercepted qubits where Eve's basis matches Alice's basis
    intercepted = eve_b >= 0
    if not np.any(intercepted):
        return

    same_basis = (eve_b[intercepted] == result.alice_bases[intercepted])
    eve_bits_same = eve_r[intercepted][same_basis]
    alice_bits_same = result.alice_bits[intercepted][same_basis]

    assert np.array_equal(eve_bits_same, alice_bits_same), (
        f"Eve should recover Alice's bit when bases match.\n"
        f"  eve_results (same basis): {eve_bits_same}\n"
        f"  alice_bits  (same basis): {alice_bits_same}"
    )


# -------------------------------------------------------------------
# BB84
# -------------------------------------------------------------------
class TestBB84EveMeasurement:
    """Eve measurement correctness for BB84."""

    def test_same_basis_recovers_alice_bit(self):
        """With 100% intercept, every qubit is intercepted; matching-basis
        qubits must have eve_result == alice_bit."""
        rng = np.random.default_rng(0)
        proto = BB84(n_qubits=500, rng=rng, intercept_rate=1.0)
        result = proto.run()
        _check_eve_same_basis_gets_alice_bit(result)

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
        _check_eve_same_basis_gets_alice_bit(result)


# -------------------------------------------------------------------
# B92
# -------------------------------------------------------------------
class TestB92EveMeasurement:
    def test_same_basis_recovers_alice_bit(self):
        rng = np.random.default_rng(10)
        result = B92(n_qubits=500, rng=rng, intercept_rate=1.0).run()
        _check_eve_same_basis_gets_alice_bit(result)

    def test_no_intercept_gives_none(self):
        rng = np.random.default_rng(11)
        result = B92(n_qubits=100, rng=rng, intercept_rate=0.0).run()
        assert result.eve_bases is None
        assert result.eve_results is None


# -------------------------------------------------------------------
# E91
# -------------------------------------------------------------------
class TestE91EveMeasurement:
    def test_same_basis_recovers_alice_bit(self):
        rng = np.random.default_rng(20)
        result = E91(n_qubits=500, rng=rng, intercept_rate=1.0).run()
        _check_eve_same_basis_gets_alice_bit(result)

    def test_no_intercept_gives_none(self):
        rng = np.random.default_rng(21)
        result = E91(n_qubits=100, rng=rng, intercept_rate=0.0).run()
        assert result.eve_bases is None
        assert result.eve_results is None
