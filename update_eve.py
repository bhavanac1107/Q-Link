import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('eve.py', 'r', encoding='utf-8') as f:
    code = f.read()

target = 'def simulate_qkd_protocol(num_qubits, attack_strength=0.0, noise_level=0.0, attack_type="Standard Random", seed=None, seed_simulator=None):'
replacement = '''def simulate_qkd_protocol(num_qubits, attack_strength=0.0, noise_level=0.0, attack_type="Standard Random", seed=None, seed_simulator=None, fast_mode=False):
    if fast_mode:
        import numpy as np
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
'''

code = code.replace(target, replacement)
with open('eve.py', 'w', encoding='utf-8') as f:
    f.write(code)
