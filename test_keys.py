import numpy as np
from bb84 import generate_random_bits, generate_random_bases
from eve import simulate_qkd_protocol, estimate_qber
from pipeline import simple_error_correction, privacy_amplification
import hashlib

def test_keys():
    for seed in range(20):
        print(f"--- SEED {seed} ---")
        num_qubits = 2000
        sim_data = simulate_qkd_protocol(num_qubits, attack_strength=0.0, noise_level=0.0, seed=seed)
        
        alice_sifted = sim_data["alice_sifted"]
        bob_sifted = sim_data["bob_sifted"]
        sifted_bases = sim_data["sifted_bases"]
        
        qber, raw_a, raw_b, adv = estimate_qber(alice_sifted, bob_sifted, sifted_bases, 0.25)
        print(f"QBER: {qber}")
        
        ec_a, ec_b = simple_error_correction(raw_a, raw_b)
        
        diff_raw = np.sum(raw_a != raw_b)
        diff_ec = np.sum(ec_a != ec_b)
        print(f"Raw Diff: {diff_raw}, EC Diff: {diff_ec}")
        
        fin_a = privacy_amplification(ec_a, qber)
        fin_b = privacy_amplification(ec_b, qber)
        
        if len(fin_a) > 0 and len(fin_b) > 0:
            diff_fin = np.sum(fin_a != fin_b)
            print(f"Fin Diff: {diff_fin}")
            
            hash_a = hashlib.sha256(fin_a.tobytes()).hexdigest()
            hash_b = hashlib.sha256(fin_b.tobytes()).hexdigest()
            
            if hash_a != hash_b:
                print("HASH MISMATCH!")
            else:
                print("HASH OK")
        else:
            print("KEY EMPTY")

if __name__ == '__main__':
    test_keys()
