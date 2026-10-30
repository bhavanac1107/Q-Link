import numpy as np

def generate_random_bits(length):
    return np.random.randint(2, size=length)

def generate_random_bases(length):
    return np.random.randint(2, size=length)

def encode_qubits(bits, bases):
    from qiskit import QuantumCircuit
    n = len(bits)
    qc = QuantumCircuit(n, n)
    x_indices = np.where(bits == 1)[0].tolist()
    h_indices = np.where(bases == 1)[0].tolist()
    if x_indices: qc.x(x_indices)
    if h_indices: qc.h(h_indices)
    return qc

def measure_qubits(qc, bases):
    n = len(bases)
    h_indices = np.where(bases == 1)[0].tolist()
    if h_indices: qc.h(h_indices)
    all_indices = list(range(n))
    qc.measure(all_indices, all_indices)
    return qc

def run_bb84(num_qubits=16, seed=None):
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    if seed is not None:
        np.random.seed(seed)
    alice_bits = generate_random_bits(num_qubits)
    alice_bases = generate_random_bases(num_qubits)
    qc = encode_qubits(alice_bits, alice_bases)
    bob_bases = generate_random_bases(num_qubits)
    qc = measure_qubits(qc, bob_bases)
    simulator = AerSimulator(method='stabilizer')
    compiled_circuit = transpile(qc, simulator, optimization_level=0)
    result = simulator.run(compiled_circuit, shots=1, seed_simulator=seed).result()
    counts = result.get_counts(qc)
    measured_str = list(counts.keys())[0]
    bob_bits = np.array([int(b) for b in measured_str[::-1]])
    
    # Sifting vectorized
    match_mask = (alice_bases == bob_bases)
    sifted_key = bob_bits[match_mask].tolist()
    return sifted_key
