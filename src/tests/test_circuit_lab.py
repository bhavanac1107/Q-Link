"""Automated unit tests for Quantum Circuit Lab module.

Verifies:
1. Pauli-X gate flips |0> to |1> and |1> to |0>.
2. Hadamard gate creates superposition |+> and |-> with 50/50 measurement probabilities.
3. Identity gate leaves states unchanged.
4. BB84 matching bases yield deterministic identical bits without Eve.
5. BB84 mismatched bases yield 50/50 outcomes.
6. Eve's intercept-resend attack introduces quantum measurement disturbance.
7. Full random-basis intercept-resend approaches ~25% QBER in the sifted key.
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from src.ui.circuit_lab import _format_dirac


class TestQuantumGates:
    """Verify fundamental quantum logic gates."""

    def test_pauli_x_gate_bit_flip(self):
        """X|0> = |1> and X|1> = |0>."""
        # On |0>
        qc0 = QuantumCircuit(1)
        qc0.x(0)
        sv0 = Statevector.from_instruction(qc0).data
        assert abs(sv0[0]) < 1e-6 and abs(sv0[1] - 1.0) < 1e-6

        # On |1>
        qc1 = QuantumCircuit(1)
        qc1.x(0)
        qc1.x(0)
        sv1 = Statevector.from_instruction(qc1).data
        assert abs(sv1[0] - 1.0) < 1e-6 and abs(sv1[1]) < 1e-6

    def test_hadamard_gate_superposition(self):
        """H|0> = |+> = (|0> + |1>)/sqrt(2) and H|1> = |-> = (|0> - |1>)/sqrt(2)."""
        # H on |0>
        qc0 = QuantumCircuit(1)
        qc0.h(0)
        sv0 = Statevector.from_instruction(qc0).data
        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        assert abs(sv0[0] - inv_sqrt2) < 1e-5
        assert abs(sv0[1] - inv_sqrt2) < 1e-5

        # H on |1>
        qc1 = QuantumCircuit(1)
        qc1.x(0)
        qc1.h(0)
        sv1 = Statevector.from_instruction(qc1).data
        assert abs(sv1[0] - inv_sqrt2) < 1e-5
        assert abs(sv1[1] - (-inv_sqrt2)) < 1e-5

        # Measurement probabilities on AerSimulator
        qc_meas = QuantumCircuit(1, 1)
        qc_meas.h(0)
        qc_meas.measure(0, 0)
        sim = AerSimulator()
        counts = sim.run(qc_meas, shots=5000).result().get_counts()
        p0 = counts.get("0", 0) / 5000
        p1 = counts.get("1", 0) / 5000
        assert 0.46 <= p0 <= 0.54
        assert 0.46 <= p1 <= 0.54

    def test_identity_gate(self):
        """I|psi> = |psi>."""
        qc = QuantumCircuit(1)
        qc.id(0)
        sv = Statevector.from_instruction(qc).data
        assert abs(sv[0] - 1.0) < 1e-6 and abs(sv[1]) < 1e-6


class TestBB84QuantumCircuits:
    """Verify BB84 state preparation, measurement, and eavesdropping."""

    def _build_circuit(self, alice_bit: int, alice_basis: int, eve_active: bool, eve_basis: int, bob_basis: int):
        if eve_active:
            qc = QuantumCircuit(1, 2)
            c_eve, c_bob = 0, 1
        else:
            qc = QuantumCircuit(1, 1)
            c_bob = 0

        # Alice prep
        if alice_bit == 1:
            qc.x(0)
        if alice_basis == 1:
            qc.h(0)

        # Eve attack
        if eve_active:
            if eve_basis == 1:
                qc.h(0)
            qc.measure(0, c_eve)
            if eve_basis == 1:
                qc.h(0)

        # Bob measurement
        if bob_basis == 1:
            qc.h(0)
        qc.measure(0, c_bob)
        return qc

    def test_matching_bases_noiseless_deterministic(self):
        """Matching bases in clean channel yield identical bits with 100% determinism."""
        sim = AerSimulator()
        # Test Z basis match: bit 0
        qc_z0 = self._build_circuit(0, 0, False, 0, 0)
        counts = sim.run(qc_z0, shots=500).result().get_counts()
        assert counts == {"0": 500}

        # Test Z basis match: bit 1
        qc_z1 = self._build_circuit(1, 0, False, 0, 0)
        counts = sim.run(qc_z1, shots=500).result().get_counts()
        assert counts == {"1": 500}

        # Test X basis match: bit 0
        qc_x0 = self._build_circuit(0, 1, False, 0, 1)
        counts = sim.run(qc_x0, shots=500).result().get_counts()
        assert counts == {"0": 500}

        # Test X basis match: bit 1
        qc_x1 = self._build_circuit(1, 1, False, 0, 1)
        counts = sim.run(qc_x1, shots=500).result().get_counts()
        assert counts == {"1": 500}

    def test_mismatched_bases_random_outcomes(self):
        """Mismatched bases produce 50/50 random outcomes."""
        sim = AerSimulator()
        # Alice Z bit 0, Bob X
        qc = self._build_circuit(0, 0, False, 0, 1)
        counts = sim.run(qc, shots=4000).result().get_counts()
        p0 = counts.get("0", 0) / 4000
        p1 = counts.get("1", 0) / 4000
        assert 0.46 <= p0 <= 0.54
        assert 0.46 <= p1 <= 0.54

    def test_eve_intercept_resend_disturbance(self):
        """Eve measuring in conjugate basis disturbs matching-basis outcomes."""
        sim = AerSimulator()
        # Alice Z bit 0, Eve X basis, Bob Z basis
        qc = self._build_circuit(0, 0, True, 1, 0)
        counts = sim.run(qc, shots=4000).result().get_counts()
        # In Qiskit bitstring order is "c_bob c_eve"
        # Bob bit is the first character
        bob_0 = sum(cnt for bs, cnt in counts.items() if bs[0] == "0")
        bob_1 = sum(cnt for bs, cnt in counts.items() if bs[0] == "1")
        # Error rate on Bob should be ~50%
        err_rate = bob_1 / 4000
        assert 0.46 <= err_rate <= 0.54

    def test_full_intercept_resend_qber_approaches_25_percent(self):
        """Under full random-basis intercept-resend, sifted key QBER approaches ~25%."""
        rng = np.random.default_rng(42)
        n = 2000
        sim = AerSimulator()

        a_bits = rng.integers(0, 2, size=n)
        a_bases = rng.integers(0, 2, size=n)
        e_bases = rng.integers(0, 2, size=n)
        b_bases = rng.integers(0, 2, size=n)

        sifted_mismatches = 0
        sifted_total = 0

        for i in range(n):
            if a_bases[i] == b_bases[i]:  # Only sifted key bits
                qc = self._build_circuit(int(a_bits[i]), int(a_bases[i]), True, int(e_bases[i]), int(b_bases[i]))
                res = sim.run(qc, shots=1).result().get_counts()
                bitstr = list(res.keys())[0]
                bob_bit = int(bitstr[0])
                if bob_bit != a_bits[i]:
                    sifted_mismatches += 1
                sifted_total += 1

        assert sifted_total > 800
        qber = sifted_mismatches / sifted_total
        assert 0.20 <= qber <= 0.30, f"Expected QBER ~25%, got {qber:.3%}"


class TestDiracFormatting:
    def test_dirac_formatting(self):
        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        assert "|0\\rangle" in _format_dirac(np.array([1.0, 0.0]))
        assert "|1\\rangle" in _format_dirac(np.array([0.0, 1.0]))
        assert "\\frac{1}{\\sqrt{2}}" in _format_dirac(np.array([inv_sqrt2, inv_sqrt2]))
