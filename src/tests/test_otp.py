"""Tests for OTP demo with QKD simulation keys.

Verifies:
1. eve_intercept_rate=0 and channel_error=0: Bob decrypts exactly.
2. intercept_rate=1.0: Abort condition is met and key is rejected/blocked.
3. channel_error > 0 causing key mismatch: Bob's decrypted text differs from original.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.core.bb84 import BB84
from src.analysis.otp_demo import run_otp_qkd_demo


def _extract_final_keys(res):
    """Extract Alice, Bob, and Eve usable key bits (sifted and not sampled)."""
    mask = res.sifted_mask & (~res.sampled_mask)
    alice_key = res.alice_bits[mask]
    bob_key = res.bob_bits[mask]
    eve_key = res.eve_results[mask] if res.eve_results is not None else None
    return alice_key, bob_key, eve_key


class TestOTPQKDDemo:
    def test_clean_channel_bob_decrypts_exactly(self):
        """With eve_intercept_rate=0 and channel_error=0, Bob decrypts the message exactly."""
        rng = np.random.default_rng(42)
        # 300 qubits gives plenty of key bits for a short message
        proto = BB84(n_qubits=400, rng=rng, channel_error=0.0, intercept_rate=0.0)
        res = proto.run()

        assert res.alert_level == "NORMAL"
        assert res.qber == 0.0

        alice_key, bob_key, eve_key = _extract_final_keys(res)
        msg = "Q-Link Clean OTP!"
        out = run_otp_qkd_demo(msg, alice_key, bob_key, eve_key)

        assert out["bob_bit_mismatches_count"] == 0
        assert out["bob_char_diffs"] == []
        assert out["bob_decrypted_full"] == msg

    def test_intercept_rate_1_triggers_abort(self):
        """With intercept_rate=1.0, QBER triggers ABORT, meaning key is compromised/discarded."""
        rng = np.random.default_rng(99)
        proto = BB84(n_qubits=400, rng=rng, channel_error=0.0, intercept_rate=1.0, qber_threshold=0.11)
        res = proto.run()

        assert res.alert_level == "ABORT"
        assert res.qber >= 0.11

    def test_channel_error_causes_garbled_decryption(self):
        """With channel_error > 0 and key mismatch, Bob's decrypted text differs from original."""
        rng = np.random.default_rng(123)
        # Moderate channel error that causes bit flips
        proto = BB84(n_qubits=400, rng=rng, channel_error=0.08, intercept_rate=0.0)
        res = proto.run()

        alice_key, bob_key, eve_key = _extract_final_keys(res)
        # Ensure there is at least one mismatch between Alice's and Bob's key bits
        assert not np.array_equal(alice_key, bob_key)

        msg = "Top Secret Quantum Message 12345"
        out = run_otp_qkd_demo(msg, alice_key, bob_key, eve_key)

        assert out["bob_bit_mismatches_count"] > 0
        assert len(out["bob_char_diffs"]) > 0
        assert out["bob_decrypted_full"] != msg
