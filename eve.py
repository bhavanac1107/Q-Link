"""
Phase 3: Eve Attack and QBER Sampling
This file simulates an eavesdropper (Eve) who intercepts and resends qubits.
It also calculates the Quantum Bit Error Rate (QBER).
"""
import numpy as np
import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Import the base generation functions from Phase 2
from bb84 import generate_random_bits, generate_random_bases

def encode_qubits_alice(bits, bases):
    """Alice encodes her bits."""
    n = len(bits)
    # We need classical registers for Eve and Bob.
    # We will use 2 classical registers of size n:
    # index 0 to n-1 for Eve, index n to 2n-1 for Bob.
    qc = QuantumCircuit(n, 2 * n)
    for i in range(n):
        if bits[i] == 1:
            qc.x(i)
        if bases[i] == 1:
            qc.h(i)
    return qc

def eve_intercept(qc, intercept_fraction, seed=None):
    """
    Eve intercepts a fraction of the qubits, measures them in a random basis,
    and resends them (which happens automatically by measuring and rotating back).
    """
    if seed is not None:
        np.random.seed(seed)
        
    n = qc.num_qubits
    eve_bases = generate_random_bases(n)
    intercepted_indices = []
    
    for i in range(n):
        if np.random.rand() < intercept_fraction:
            intercepted_indices.append(i)
            # Eve chooses basis
            if eve_bases[i] == 1:
                qc.h(i)
            
            # Eve measures into her classical register (indices 0 to n-1)
            qc.measure(i, i)
            
            # Eve resends the qubit in the basis she measured
            # Since the measurement collapsed it to Z, applying H again 
            # puts it back into the X basis if she measured in X.
            if eve_bases[i] == 1:
                qc.h(i)
                
    return qc, eve_bases, intercepted_indices

def measure_qubits_bob(qc, bases):
    """Bob measures the qubits."""
    n = qc.num_qubits
    for i in range(n):
        if bases[i] == 1:
            qc.h(i)
        # Bob measures into his classical register (indices n to 2n-1)
        qc.measure(i, i + n)
    return qc

def estimate_qber(alice_sifted, bob_sifted, sample_fraction=0.25):
    """
    Calculates QBER using a random sample of the sifted key.
    The sampled bits are discarded from the final key.
    """
    n_sifted = len(alice_sifted)
    sample_size = int(n_sifted * sample_fraction)
    
    if sample_size < 1:
        print("Warning: Sifted key is too short for a meaningful QBER sample.")
        return 0.0, alice_sifted, bob_sifted  # Return full key if too small
        
    # Choose random indices to sample
    sample_indices = np.random.choice(n_sifted, sample_size, replace=False)
    
    errors = 0
    for idx in sample_indices:
        if alice_sifted[idx] != bob_sifted[idx]:
            errors += 1
            
    qber = errors / sample_size
    
    # Discard sampled bits from the final key
    final_alice_key = np.delete(alice_sifted, sample_indices)
    final_bob_key = np.delete(bob_sifted, sample_indices)
    
    return qber, final_alice_key, final_bob_key

def simulate_qkd_protocol(num_qubits, attack_strength=0.0, seed=None):
    """
    Simulates the BB84 protocol for any number of qubits.
    Because Qiskit AerSimulator limits max qubits to 29 by default,
    this function processes qubits in batches of 24.
    """
    if seed is not None:
        np.random.seed(seed)
        
    alice_sifted_all = []
    bob_sifted_all = []
    
    batch_size = 24
    simulator = AerSimulator()
    
    for i in range(0, num_qubits, batch_size):
        current_batch = min(batch_size, num_qubits - i)
        
        # 1. Alice
        alice_bits = generate_random_bits(current_batch)
        alice_bases = generate_random_bases(current_batch)
        qc = encode_qubits_alice(alice_bits, alice_bases)
        
        # 2. Eve
        if attack_strength > 0:
            qc, _, _ = eve_intercept(qc, attack_strength)
            
        # 3. Bob
        bob_bases = generate_random_bases(current_batch)
        qc = measure_qubits_bob(qc, bob_bases)
        
        # 4. Simulate
        # Use optimization_level=0 to drastically speed up transpilation in the loop
        compiled_circuit = transpile(qc, simulator, optimization_level=0)
        result = simulator.run(compiled_circuit, shots=1).result()
        counts = result.get_counts(qc)
        
        measured_str = list(counts.keys())[0][::-1]
        bob_bits = np.array([int(b) for b in measured_str[current_batch:2*current_batch]])
        
        # 5. Sift
        for j in range(current_batch):
            if alice_bases[j] == bob_bases[j]:
                alice_sifted_all.append(alice_bits[j])
                bob_sifted_all.append(bob_bits[j])
                
    return np.array(alice_sifted_all), np.array(bob_sifted_all)

def run_eve_simulation(num_qubits=32, attack_strength=1.0, seed=42):
    print(f"--- Running BB84 Protocol with Eve ({num_qubits} qubits) ---")
    print(f"Eve Attack Strength: {attack_strength * 100}%")
    
    alice_sifted, bob_sifted = simulate_qkd_protocol(num_qubits, attack_strength, seed)
    
    print("-" * 50)
    print(f"Sifted key length: {len(alice_sifted)} bits")
    
    # 7. QBER Estimation
    # We use 25% of the sifted key for QBER estimation
    qber, final_alice, final_bob = estimate_qber(alice_sifted, bob_sifted, sample_fraction=0.25)
    
    print(f"Estimated QBER: {qber * 100:.1f}%")
    print(f"Final secret key length (after discarding sample): {len(final_alice)} bits")
    
    if qber > 0:
        print("ATTENTION: Errors detected! An eavesdropper may be present.")
    else:
        print("Channel looks secure.")
        
    print("-" * 50)
    
if __name__ == '__main__':
    run_eve_simulation(num_qubits=24, attack_strength=1.0, seed=100)
    print("\nNow running with Eve turned OFF (0% attack strength)...")
    run_eve_simulation(num_qubits=24, attack_strength=0.0, seed=101)
