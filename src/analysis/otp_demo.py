"""One-time-pad encryption demo for Q-Link.

Alice encrypts a message with HER final key bits via bitwise XOR.
Bob decrypts the ciphertext with HIS final key bits.
Eve attempts decryption using whatever key bits she intercepted on those positions.
If key bits are shorter than message bits, only the covered prefix is encrypted/decrypted.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import numpy as np


def bits_to_bytes(bit_array: np.ndarray | list[int]) -> bytes:
    """Pack an array or list of 0/1 bits (MSB first) into bytes.
    Only complete groups of 8 bits are converted.
    """
    bits = [int(b) for b in bit_array]
    num_bytes = len(bits) // 8
    byte_vals = []
    for i in range(num_bytes):
        byte_chunk = bits[i * 8 : (i + 1) * 8]
        val = 0
        for bit in byte_chunk:
            val = (val << 1) | (bit & 1)
        byte_vals.append(val)
    return bytes(byte_vals)


def bytes_to_bits(data: bytes) -> list[int]:
    """Convert bytes into a list of 0/1 bits (MSB first)."""
    bits: list[int] = []
    for b in data:
        for shift in range(7, -1, -1):
            bits.append((b >> shift) & 1)
    return bits


def run_otp_qkd_demo(
    message: str,
    alice_key_bits: np.ndarray | list[int],
    bob_key_bits: np.ndarray | list[int],
    eve_key_bits: Optional[np.ndarray | list[int]] = None,
) -> Dict[str, Any]:
    """Run an OTP demo using separate key bit arrays for Alice, Bob, and optionally Eve.

    Parameters
    ----------
    message : str
        Plain-text message (UTF-8).
    alice_key_bits : np.ndarray | list[int]
        Alice's usable final key bits (0 or 1).
    bob_key_bits : np.ndarray | list[int]
        Bob's usable final key bits (0 or 1).
    eve_key_bits : Optional[np.ndarray | list[int]]
        Eve's measured bits on the same key positions (-1 for unintercepted, 0 or 1 for measured).

    Returns
    -------
    dict
        Structured results including:
        - message_bits_len, key_bits_len, bits_covered
        - original, original_covered, original_uncovered
        - ciphertext_bits, ciphertext_hex
        - bob_decrypted_text, bob_bit_errors, bob_char_diffs
        - eve_key_bits_known, eve_decrypted_text
    """
    msg_bytes = message.encode("utf-8")
    msg_bits = bytes_to_bits(msg_bytes)
    total_msg_bits = len(msg_bits)

    a_bits = [int(b) for b in alice_key_bits]
    b_bits = [int(b) for b in bob_key_bits]

    avail_key_bits = min(len(a_bits), len(b_bits))
    covered_bits = min(total_msg_bits, avail_key_bits)
    covered_bytes_count = covered_bits // 8
    actual_covered_bits = covered_bytes_count * 8

    # Message slice that gets encrypted
    covered_msg_bytes = msg_bytes[:covered_bytes_count]
    uncovered_msg_bytes = msg_bytes[covered_bytes_count:]
    covered_msg_bits = msg_bits[:actual_covered_bits]

    # Alice encrypts covered bits
    a_slice = a_bits[:actual_covered_bits]
    cipher_bits = [m ^ k for m, k in zip(covered_msg_bits, a_slice)]
    cipher_bytes = bits_to_bytes(cipher_bits)

    # Bob decrypts with Bob's key bits
    b_slice = b_bits[:actual_covered_bits]
    bob_decrypted_bits = [c ^ k for c, k in zip(cipher_bits, b_slice)]
    bob_decrypted_bytes = bits_to_bytes(bob_decrypted_bits)
    bob_decrypted_covered_text = bob_decrypted_bytes.decode("utf-8", errors="replace")
    uncovered_text = uncovered_msg_bytes.decode("utf-8", errors="replace")
    bob_full_text = bob_decrypted_covered_text + uncovered_text

    # Compare Bob's key vs Alice's key
    bit_mismatches = [i for i in range(actual_covered_bits) if a_slice[i] != b_slice[i]]
    
    char_diffs = []
    orig_covered_text = covered_msg_bytes.decode("utf-8", errors="replace")
    for idx, (orig_c, bob_c) in enumerate(zip(orig_covered_text, bob_decrypted_covered_text)):
        if orig_c != bob_c:
            char_diffs.append({
                "pos": idx,
                "original": orig_c,
                "bob": bob_c,
            })

    # Eve's attempt
    eve_decrypted_text = None
    eve_bits_known = 0
    if eve_key_bits is not None:
        e_raw = [int(b) for b in eve_key_bits[:actual_covered_bits]]
        # Where Eve didn't intercept (-1), she guesses 0 (or random bit; let's treat -1 as unknown/0)
        eve_slice = [b if b in (0, 1) else 0 for b in e_raw]
        eve_bits_known = sum(1 for b in e_raw if b in (0, 1))
        eve_decrypted_bits = [c ^ k for c, k in zip(cipher_bits, eve_slice)]
        eve_decrypted_bytes = bits_to_bytes(eve_decrypted_bits)
        eve_decrypted_text = eve_decrypted_bytes.decode("utf-8", errors="replace") + uncovered_text

    return {
        "total_msg_bits": total_msg_bits,
        "avail_key_bits": avail_key_bits,
        "covered_bits": actual_covered_bits,
        "original_full": message,
        "original_covered": orig_covered_text,
        "uncovered_text": uncovered_text,
        "ciphertext_hex": cipher_bytes.hex(),
        "bob_decrypted_full": bob_full_text,
        "bob_bit_mismatches_count": len(bit_mismatches),
        "bob_char_diffs": char_diffs,
        "eve_decrypted_full": eve_decrypted_text,
        "eve_bits_known": eve_bits_known,
    }
