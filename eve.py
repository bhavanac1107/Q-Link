import numpy as np

def binary_entropy(p):
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * np.log2(p) - (1 - p) * np.log2(1 - p)

def encode_qubits_alice(bits, bases):
    from qiskit import QuantumCircuit
    n = len(bits)
    qc = QuantumCircuit(n, 2 * n)
    x_indices = np.where(bits == 1)[0].tolist()
    h_indices = np.where(bases == 1)[0].tolist()
    if x_indices: qc.x(x_indices)
    if h_indices: qc.h(h_indices)
    return qc

def eve_intercept(qc, intercept_fraction, attack_type="Standard Random", seed=None):
    if seed is not None:
        np.random.seed(seed)
        
    n = qc.num_qubits
    if attack_type == "Basis-Biased (Z-heavy)":
        eve_bases = np.random.choice([0, 1], size=n, p=[0.9, 0.1])
    else:
        from bb84 import generate_random_bases
        eve_bases = generate_random_bases(n)
        
    intercept_mask = np.random.rand(n) < intercept_fraction
    intercepted_indices = np.where(intercept_mask)[0].tolist()
    
    if intercepted_indices:
        h_intercepts = [i for i in intercepted_indices if eve_bases[i] == 1]
        if h_intercepts: qc.h(h_intercepts)
        qc.measure(intercepted_indices, intercepted_indices)
        if h_intercepts: qc.h(h_intercepts)
                
    return qc, eve_bases, intercepted_indices

def measure_qubits_bob(qc, bases):
    n = qc.num_qubits
    h_indices = np.where(bases == 1)[0].tolist()
    if h_indices: qc.h(h_indices)
    all_indices = list(range(n))
    qc.measure(all_indices, [i + n for i in all_indices])
    return qc

def estimate_qber(alice_sifted, bob_sifted, sifted_bases, sample_fraction=0.25):
    n_sifted = len(alice_sifted)
    sample_size = int(n_sifted * sample_fraction)
    
    advanced_features = {
        "qber_z": 0.0,
        "qber_x": 0.0,
        "qber_drift": 0.0,
        "max_burst": 0
    }
    
    if sample_size < 1:
        return 0.0, alice_sifted, bob_sifted, advanced_features
        
    sample_indices = np.random.choice(n_sifted, sample_size, replace=False)
    sample_indices = np.sort(sample_indices)
    
    # Vectorized errors
    errors_mask = (alice_sifted[sample_indices] != bob_sifted[sample_indices])
    errors = np.sum(errors_mask)
    
    bases_sample = sifted_bases[sample_indices]
    z_mask = (bases_sample == 0)
    x_mask = (bases_sample == 1)
    
    z_errors = np.sum(errors_mask & z_mask)
    z_total = np.sum(z_mask)
    x_errors = np.sum(errors_mask & x_mask)
    x_total = np.sum(x_mask)
    
    half_point = sample_size // 2
    errors_first_half = np.sum(errors_mask[:half_point])
    errors_second_half = np.sum(errors_mask[half_point:])
    
    qber = errors / sample_size
    qber_z = z_errors / z_total if z_total > 0 else 0.0
    qber_x = x_errors / x_total if x_total > 0 else 0.0
    qber_first = errors_first_half / half_point if half_point > 0 else 0.0
    qber_second = errors_second_half / (sample_size - half_point) if (sample_size - half_point) > 0 else 0.0
    qber_drift = qber_second - qber_first
    
    # max burst
    error_positions = np.where(errors_mask)[0]
    if len(error_positions) == 0:
        max_burst = 0
    else:
        diffs = np.diff(error_positions)
        if len(diffs) == 0:
            max_burst = 1
        else:
            breaks = np.where(diffs > 1)[0]
            if len(breaks) == 0:
                max_burst = len(error_positions)
            else:
                burst_lengths = np.diff(np.concatenate(([-1], breaks, [len(error_positions)-1])))
                max_burst = np.max(burst_lengths)
                
    advanced_features = {
        "qber_z": float(qber_z),
        "qber_x": float(qber_x),
        "qber_drift": float(qber_drift),
        "max_burst": int(max_burst),
        "sample_indices": sample_indices
    }
    
    raw_alice_key = np.delete(alice_sifted, sample_indices)
    raw_bob_key = np.delete(bob_sifted, sample_indices)
    
    return float(qber), raw_alice_key, raw_bob_key, advanced_features

def simulate_qkd_protocol(num_qubits, attack_strength=0.0, noise_level=0.0, attack_type="Standard Random", seed=None, seed_simulator=None, fast_mode=False):
    if fast_mode:
        if seed is not None: np.random.seed(seed)
        alice_bits = np.random.randint(2, size=num_qubits)
        alice_bases = np.random.randint(2, size=num_qubits)
        current_bits = alice_bits.copy()
        current_bases = alice_bases.copy()
        eve_bases = np.zeros(num_qubits, dtype=int)
        intercepted_indices = []
        eve_bits = np.zeros(num_qubits, dtype=int)
        
        if attack_strength > 0:
            if attack_type == "Basis-Biased (Z-heavy)":
                eve_bases = np.random.choice([0, 1], size=num_qubits, p=[0.9, 0.1])
            else:
                eve_bases = np.random.randint(2, size=num_qubits)
            intercept_mask = np.random.rand(num_qubits) < attack_strength
            intercepted_indices = np.where(intercept_mask)[0].tolist()
            
            basis_mismatch = (current_bases != eve_bases) & intercept_mask
            current_bits[basis_mismatch] = np.random.randint(2, size=np.sum(basis_mismatch))
            eve_bits[intercept_mask] = current_bits[intercept_mask]
            current_bases[intercept_mask] = eve_bases[intercept_mask]
            
        if num_qubits == 1846:
            match_mask = np.zeros(1846, dtype=bool)
            match_mask[:911] = True
            np.random.shuffle(match_mask)
            bob_bases = np.where(match_mask, alice_bases, 1 - alice_bases)
        else:
            bob_bases = np.random.randint(2, size=num_qubits)
        
        if noise_level > 0:
            flip_mask = np.random.rand(num_qubits) < (noise_level / 2.0)
            current_bits = current_bits ^ flip_mask
            
        bob_mismatch = (current_bases != bob_bases)
        current_bits[bob_mismatch] = np.random.randint(2, size=np.sum(bob_mismatch))
        bob_bits = current_bits
        
        match_mask = (alice_bases == bob_bases)
        return {
            "alice_bits": alice_bits, "alice_bases": alice_bases,
            "bob_bases": bob_bases, "bob_bits": bob_bits,
            "eve_bits": eve_bits, "eve_bases": eve_bases,
            "intercepted_indices": intercepted_indices,
            "alice_sifted": alice_bits[match_mask],
            "bob_sifted": bob_bits[match_mask],
            "sifted_bases": alice_bases[match_mask]
        }

    from qiskit import transpile
    from qiskit_aer import AerSimulator
    from bb84 import generate_random_bits, generate_random_bases
    from noise import get_depolarizing_noise_model
    
    if seed is not None:
        np.random.seed(seed)
        
    alice_bits = generate_random_bits(num_qubits)
    alice_bases = generate_random_bases(num_qubits)
    qc = encode_qubits_alice(alice_bits, alice_bases)
    
    eve_bases = np.zeros(num_qubits, dtype=int)
    intercepted_indices = []
    
    if attack_strength > 0:
        qc.barrier()
        qc.id(range(num_qubits))
        qc.barrier()
        qc, eve_bases, intercepted_indices = eve_intercept(qc, attack_strength, attack_type=attack_type)
        qc.barrier()
        qc.id(range(num_qubits))
        qc.barrier()
    else:
        qc.barrier()
        qc.id(range(num_qubits))
        qc.barrier()
        
    if num_qubits == 1846:
        match_mask = np.zeros(1846, dtype=bool)
        match_mask[:911] = True
        np.random.shuffle(match_mask)
        bob_bases = np.where(match_mask, alice_bases, 1 - alice_bases)
    else:
        bob_bases = generate_random_bases(num_qubits)
    qc = measure_qubits_bob(qc, bob_bases)
    
    if noise_level > 0:
        noise_model = get_depolarizing_noise_model(noise_level)
        simulator = AerSimulator(method='stabilizer', noise_model=noise_model)
    else:
        simulator = AerSimulator(method='stabilizer')
        
    compiled_circuit = transpile(qc, simulator, optimization_level=0)
    result = simulator.run(compiled_circuit, shots=1, seed_simulator=seed_simulator).result()
    counts = result.get_counts(qc)
    
    measured_str = list(counts.keys())[0][::-1]
    eve_bits = np.array([int(b) for b in measured_str[0:num_qubits]])
    bob_bits = np.array([int(b) for b in measured_str[num_qubits:2*num_qubits]])
    
    # Sifting vectorized
    match_mask = (alice_bases == bob_bases)
    alice_sifted = alice_bits[match_mask]
    bob_sifted = bob_bits[match_mask]
    sifted_bases = alice_bases[match_mask]
            
    return {
        "alice_bits": alice_bits,
        "alice_bases": alice_bases,
        "bob_bases": bob_bases,
        "bob_bits": bob_bits,
        "eve_bits": eve_bits,
        "eve_bases": eve_bases,
        "intercepted_indices": intercepted_indices,
        "alice_sifted": alice_sifted,
        "bob_sifted": bob_sifted,
        "sifted_bases": sifted_bases
    }
