"""Qiskit quantum circuit generator for BB84 QKD protocol.

Encodes:
- Alice's state preparation (|0>, |1>, |+>, |->) via X and H gates.
- Eve's optional intercept-resend in basis Z or X (H gate, measurement, H gate).
- Channel bit-flip error (simulated as Pauli-X or noise model).
- Bob's measurement in basis Z or X (H gate, measurement).
"""

from __future__ import annotations

from typing import Tuple, Dict, Any, Optional

try:
    from qiskit import QuantumCircuit
    QISKIT_AVAILABLE = True
except ImportError:
    QuantumCircuit = None
    QISKIT_AVAILABLE = False


def build_bb84_circuit(
    alice_bit: int,
    alice_basis: int,
    eve_intercept: bool,
    eve_basis: Optional[int],
    bob_basis: int,
    channel_error: float = 0.0,
) -> Any:
    """Build a single-qubit BB84 quantum circuit for a given parameter tuple.

    Parameters
    ----------
    alice_bit : int (0 or 1)
    alice_basis : int (0 = Z, 1 = X)
    eve_intercept : bool
    eve_basis : Optional[int] (0 = Z, 1 = X)
    bob_basis : int (0 = Z, 1 = X)
    channel_error : float (probability of channel bit flip)

    Returns
    -------
    QuantumCircuit with 1 qubit and either 1 or 2 classical bits:
      - If eve_intercept: clbit 0 = Eve, clbit 1 = Bob
      - If not eve_intercept: clbit 0 = Bob
    """
    if not QISKIT_AVAILABLE:
        raise ImportError("qiskit is required to build Qiskit BB84 circuits.")

    if eve_intercept:
        qc = QuantumCircuit(1, 2)
        c_eve = 0
        c_bob = 1
    else:
        qc = QuantumCircuit(1, 1)
        c_bob = 0

    # 1. Alice Preparation
    # Basis: 0 = Z (|0> or |1>), 1 = X (|+> or |->)
    if alice_bit == 1:
        qc.x(0)
    if alice_basis == 1:
        qc.h(0)

    # 2. Eve Intercept-Resend (if active)
    if eve_intercept and eve_basis is not None:
        if eve_basis == 1:
            qc.h(0)  # Rotate to X basis
        qc.measure(0, c_eve)
        if eve_basis == 1:
            qc.h(0)  # Resend measured state in X basis

    # 3. Bob Measurement
    if bob_basis == 1:
        qc.h(0)  # Rotate to X basis
    qc.measure(0, c_bob)

    return qc
