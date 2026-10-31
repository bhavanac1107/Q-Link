"""Comprehensive automated test suite for Q-Link protocols: BB84, B92, and E91.

Verifies:
1. BB84 retains matching-basis positions and rejects mismatched-basis positions.
2. B92 distinguishes conclusive from inconclusive measurement outcomes.
3. B92 does not use BB84 basis matching as its sifting rule.
4. E91 prepares entangled states, generates key on matching angles, and calculates CHSH Bell correlation S.
5. QBER calculation handles mismatches and empty test samples safely.
6. Revealed test bits are excluded from the final key.
7. Zero Eve interception works correctly (clean channel, no eavesdropping data).
8. Eve interception produces expected qualitative degradation (e.g. BB84 QBER ~ 25% under 100% intercept).
9. Zero channel noise behaves consistently (QBER == 0.0 in ideal conditions).
10. Reproducible seeds produce identical deterministic results.
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from src.core.bb84 import BB84
from src.core.b92 import B92
from src.core.e91 import E91
from src.core.event_log import EventLog
from src.simulation.engine import run_simulation


# =====================================================================
# 1. BB84 Basis Matching & Sifting
# =====================================================================
def test_bb84_sifting_basis_matching():
    """BB84 retains positions where Alice and Bob bases match, and rejects others."""
    rng = np.random.default_rng(123)
    proto = BB84(n_qubits=1000, rng=rng)
    res = proto.run()

    # Sifted mask MUST strictly equal alice_bases == bob_bases
    expected_sifted = (res.alice_bases == res.bob_bases)
    np.testing.assert_array_equal(res.sifted_mask, expected_sifted)

    # In clean channel, sifted key bits must be identical between Alice and Bob
    sifted_idx = np.where(res.sifted_mask)[0]
    assert len(sifted_idx) > 0
    np.testing.assert_array_equal(res.alice_bits[sifted_idx], res.bob_bits[sifted_idx])


# =====================================================================
# 2. B92 Conclusive vs Inconclusive Outcomes
# =====================================================================
def test_b92_conclusive_inconclusive_distinction():
    """B92 distinguishes conclusive outcomes from inconclusive outcomes."""
    rng = np.random.default_rng(456)
    proto = B92(n_qubits=2000, rng=rng)
    res = proto.run()

    # Bob's inferred bits on conclusive rounds must be 0 or 1
    conclusive_idx = np.where(res.sifted_mask)[0]
    inconclusive_idx = np.where(~res.sifted_mask)[0]

    assert len(conclusive_idx) > 0
    assert len(inconclusive_idx) > 0

    # Conclusive rounds have inferred bits 0 or 1
    assert np.all(np.isin(res.bob_bits[conclusive_idx], [0, 1]))

    # Inconclusive rounds are marked -1
    assert np.all(res.bob_bits[inconclusive_idx] == -1)

    # In a noiseless channel with no Eve, conclusive detections must be 100% correct!
    np.testing.assert_array_equal(
        res.alice_bits[conclusive_idx], res.bob_bits[conclusive_idx]
    )

    # Conclusive rate should be close to theoretical 25% (tolerance +/- 4%)
    rate = len(conclusive_idx) / 2000
    assert 0.20 <= rate <= 0.30, f"Expected conclusive rate ~25%, got {rate:.1%}"


# =====================================================================
# 3. B92 Does NOT Use BB84 Basis Matching for Sifting
# =====================================================================
def test_b92_does_not_use_bb84_basis_matching():
    """B92 sifting is based on conclusive detection, NOT alice_basis == bob_basis."""
    rng = np.random.default_rng(789)
    proto = B92(n_qubits=2000, rng=rng)
    res = proto.run()

    # Check that sifted mask is NOT alice_bases == bob_bases
    bb84_rule_mask = (res.alice_bases == res.bob_bases)
    assert not np.array_equal(res.sifted_mask, bb84_rule_mask)

    # In fact, in ideal B92, conclusive detections occur when Bob chooses the OPPOSITE basis!
    conclusive_idx = np.where(res.sifted_mask)[0]
    assert np.all(res.alice_bases[conclusive_idx] != res.bob_bases[conclusive_idx])


# =====================================================================
# 4. E91 Entanglement & CHSH Bell Inequality Test
# =====================================================================
def test_e91_entanglement_and_chsh_violation():
    """E91 generates key on matching angles and observes Bell violation S > 2.0 when clean."""
    rng = np.random.default_rng(42)
    proto = E91(n_qubits=5000, rng=rng)
    res = proto.run()

    # Sifted mask retains matching angle rounds (KEY)
    key_idx = np.where(res.sifted_mask)[0]
    assert len(key_idx) > 0

    # In clean channel, key rounds have perfect correlation (QBER == 0)
    np.testing.assert_array_equal(res.alice_bits[key_idx], res.bob_bits[key_idx])
    assert res.qber == 0.0

    # CHSH parameter S must violate the classical Bell inequality S > 2.0
    # Theoretical quantum limit for Bell state is 2*sqrt(2) ~ 2.828
    s_val = res.extra.get("chsh_s", 0.0)
    assert s_val > 2.0, f"CHSH S must violate Bell inequality (> 2.0), got {s_val:.3f}"
    assert 2.5 <= s_val <= 3.0, f"Expected S near 2*sqrt(2) (2.828), got {s_val:.3f}"
    assert res.extra.get("chsh_violation") is True


# =====================================================================
# 5. QBER Calculation Handles Mismatches & Empty Samples
# =====================================================================
def test_qber_calculation_and_empty_sample_handling():
    """QBER calculation accurately counts mismatches and handles empty samples safely."""
    # Test empty sifted key handling
    proto = BB84(n_qubits=0, rng=np.random.default_rng(1))
    res = proto.run()
    assert math.isnan(res.qber)
    assert res.final_key_len == 0
    assert res.alert_level == "ABORT"

    # Test QBER with controlled channel error
    rng = np.random.default_rng(2)
    proto_noisy = BB84(n_qubits=5000, rng=rng, channel_error=0.08)
    res_noisy = proto_noisy.run()
    # With channel error 8%, QBER on sifted key should be ~8% (tolerance +/- 2.5%)
    assert 0.055 <= res_noisy.qber <= 0.105


# =====================================================================
# 6. Revealed Test Bits Are Excluded from Final Key
# =====================================================================
def test_revealed_test_bits_excluded_from_final_key():
    """Sampled bits used to calculate QBER are strictly subtracted from the usable key."""
    for ProtoClass in [BB84, B92, E91]:
        rng = np.random.default_rng(99)
        proto = ProtoClass(n_qubits=1000, rng=rng)
        res = proto.run()

        sifted_len = int(res.sifted_mask.sum())
        sample_size = int(res.sampled_mask.sum())

        assert sample_size > 0
        # Final key length must be exactly sifted_len - sample_size
        assert res.final_key_len == sifted_len - sample_size

        # Usable mask test
        usable_mask = res.sifted_mask & (~res.sampled_mask)
        assert int(usable_mask.sum()) == res.final_key_len


# =====================================================================
# 7. Zero Eve Interception Behavior
# =====================================================================
def test_zero_eve_interception():
    """With intercept_rate=0, Eve arrays are None and no eavesdropping data exists."""
    for ProtoClass in [BB84, B92, E91]:
        rng = np.random.default_rng(101)
        res = ProtoClass(n_qubits=500, rng=rng, intercept_rate=0.0).run()
        assert res.eve_bases is None
        assert res.eve_results is None


# =====================================================================
# 8. Eve Interception Qualitative Behavior (BB84 ~ 25% QBER)
# =====================================================================
def test_eve_interception_qualitative_behavior():
    """In ideal BB84 under 100% intercept-resend, expected QBER is ~25%."""
    rng = np.random.default_rng(202)
    proto = BB84(n_qubits=10000, rng=rng, intercept_rate=1.0, channel_error=0.0)
    res = proto.run()

    # Eve arrays must be populated with non-negative indices
    assert res.eve_bases is not None
    assert np.all(res.eve_bases >= 0)

    # Expected QBER approaches 25% (tolerance +/- 3%)
    assert 0.22 <= res.qber <= 0.28, f"Expected QBER ~25%, got {res.qber:.3%}"
    assert res.alert_level == "ABORT"


# =====================================================================
# 9. Zero Channel Noise Behavior
# =====================================================================
def test_zero_channel_noise_ideal_model():
    """Under zero channel noise and zero Eve, QBER is exactly 0.0 for all protocols."""
    for ProtoClass in [BB84, B92, E91]:
        rng = np.random.default_rng(303)
        res = ProtoClass(n_qubits=1000, rng=rng, channel_error=0.0, intercept_rate=0.0).run()
        assert res.qber == 0.0, f"Protocol {ProtoClass.__name__} expected QBER 0.0, got {res.qber}"
        assert res.alert_level == "NORMAL"


# =====================================================================
# 10. Reproducible Seeds Produce Identical Results
# =====================================================================
def test_reproducible_seeds():
    """Deterministic RNG seeds produce identical simulation results across runs."""
    for ProtoClass in [BB84, B92, E91]:
        res1 = ProtoClass(n_qubits=500, rng=np.random.default_rng(777), intercept_rate=0.3).run()
        res2 = ProtoClass(n_qubits=500, rng=np.random.default_rng(777), intercept_rate=0.3).run()

        np.testing.assert_array_equal(res1.alice_bits, res2.alice_bits)
        np.testing.assert_array_equal(res1.bob_bits, res2.bob_bits)
        np.testing.assert_array_equal(res1.sifted_mask, res2.sifted_mask)
        np.testing.assert_array_equal(res1.sampled_mask, res2.sampled_mask)
        assert res1.qber == res2.qber
        assert res1.final_key_len == res2.final_key_len
