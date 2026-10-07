"""
Phase 2: BB84 Quantum Key Distribution
This file implements a simulation of the BB84 QKD protocol.
"""
import numpy as np
import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

def generate_random_bits(length):
    """Generates an array of random bits (0 or 1)."""
    return np.random.randint(2, size=length)

def generate_random_bases(length):
    """
    Generates an array of random bases. 
    0 represents the Z basis (Rectilinear).
    1 represents the X basis (Diagonal).
    """
    return np.random.randint(2, size=length)

def encode_qubits(bits, bases):
    """
    Alice encodes her bits into qubits based on her randomly chosen bases.
    If bit is 1, apply X gate to flip |0> to |1>.
    If basis is 1 (X basis), apply H gate.
    """
    n = len(bits)
    qc = QuantumCircuit(n, n)
    for i in range(n):
        if bits[i] == 1:
            qc.x(i)
        if bases[i] == 1:
            qc.h(i)
    return qc

def measure_qubits(qc, bases):
    """
    Bob measures the qubits using his randomly chosen bases.
    If his basis is 1 (X basis), apply H gate before standard Z measurement.
    """
    n = len(bases)
    for i in range(n):
        if bases[i] == 1:
            qc.h(i)
        qc.measure(i, i)
    return qc

def run_bb84(num_qubits=16, seed=None):
    """
    Runs a full BB84 simulation for a given number of qubits.
    """
    print(f"--- Running BB84 Protocol ({num_qubits} qubits) ---")
    if seed is not None:
        print(f"Using fixed random seed: {seed}")
        np.random.seed(seed)
    
    # 1. Alice generates random bits and bases
    alice_bits = generate_random_bits(num_qubits)
    alice_bases = generate_random_bases(num_qubits)
    
    print(f"Alice's bits:  {alice_bits}")
    print(f"Alice's bases: {alice_bases}  (0=Z-basis, 1=X-basis)")
    
    # 2. Alice encodes the qubits
    qc = encode_qubits(alice_bits, alice_bases)
    
    # 3. Bob generates random measurement bases
    bob_bases = generate_random_bases(num_qubits)
    print(f"Bob's bases:   {bob_bases}  (0=Z-basis, 1=X-basis)")
    
    # 4. Bob measures the qubits
    qc = measure_qubits(qc, bob_bases)
    
    # 5. Simulate the circuit
    # Using AerSimulator per modern API rules
    simulator = AerSimulator()
    compiled_circuit = transpile(qc, simulator)
    
    # We only need 1 shot since Alice is sending each photon exactly once
    result = simulator.run(compiled_circuit, shots=1).result()
    counts = result.get_counts(qc)
    
    # Qiskit outputs strings from right to left (qubit 0 is the rightmost bit).
    # We reverse it to align with our array indices.
    measured_str = list(counts.keys())[0]
    bob_bits = np.array([int(b) for b in measured_str[::-1]])
    
    print(f"Bob's bits:    {bob_bits}")
    
    # 6. Sifting process
    # Alice and Bob publicly share their bases. If they used the same basis, 
    # their bits should match perfectly (in a noiseless channel with no Eve).
    sifted_key = []
    for i in range(num_qubits):
        if alice_bases[i] == bob_bases[i]:
            sifted_key.append(bob_bits[i])
            
    print("-" * 50)
    print(f"Sifted key:    {sifted_key}")
    print(f"Sifted key length: {len(sifted_key)} bits")
    print("-" * 50)
    
    print("\nExplanation:")
    print("Alice encoded her random bits into qubits using her random bases.")
    print("Bob guessed the measurement bases randomly.")
    print("When their bases matched, Bob perfectly recovered Alice's bit (since there is no noise or eavesdropper yet).")
    print("When their bases did NOT match, Bob's measurement was completely random (50% chance of being wrong).")
    print("The 'Sifted Key' is formed by discarding all bits where their bases disagreed.")
    print(f"Statistically, the sifted key is roughly {num_qubits // 2} bits long.")

if __name__ == '__main__':
    run_bb84(num_qubits=16, seed=42)
