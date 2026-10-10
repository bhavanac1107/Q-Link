"""
Phase 1: Basic Quantum Circuit
This file demonstrates a basic 1-qubit quantum circuit using Qiskit.
It applies a Hadamard gate, measures the qubit, and runs a simulation.
"""

import qiskit
import qiskit_aer
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

import qiskit
import qiskit_aer
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Import QKD components
from bb84 import generate_random_bits, generate_random_bases
from eve import encode_qubits_alice, measure_qubits_bob, eve_intercept

def print_demo_circuit(eve_on):
    n = 5
    print(f"\n--- 5-Qubit BB84 Circuit (Eve ON: {eve_on}) ---")
    
    alice_bits = generate_random_bits(n)
    alice_bases = generate_random_bases(n)
    qc = encode_qubits_alice(alice_bits, alice_bases)
    
    if eve_on:
        qc, _, _ = eve_intercept(qc, intercept_fraction=1.0)
        
    bob_bases = generate_random_bases(n)
    qc = measure_qubits_bob(qc, bob_bases)
    
    # Draw the circuit in text mode for the terminal
    print(qc.draw('text'))
    
    # Optional: run it to show it works
    simulator = AerSimulator()
    compiled_circuit = transpile(qc, simulator, optimization_level=0)
    result = simulator.run(compiled_circuit, shots=1).result()
    counts = result.get_counts(qc)
    print(f"Simulation result (classical registers): {list(counts.keys())[0]}")
    print("-" * 50)

if __name__ == '__main__':
    print("Q-Link Prototype: 5-Qubit BB84 Demonstration")
    print_demo_circuit(eve_on=False)
    print_demo_circuit(eve_on=True)
