from eve import simulate_qkd_protocol, estimate_qber
import numpy as np

def evaluate_security(qber, threshold=0.11):
    if qber <= threshold:
        return "ACCEPTED", f"QBER {qber*100:.2f}% is below threshold."
    return "REJECTED", f"QBER {qber*100:.2f}% exceeds threshold."

def run_test(num_qubits, eve_frac, noise, att_type, seed_base):
    attempts = 1
    max_attempts = 3
    history = []
    
    target_key_len = 100
    sim_seed = seed_base
    
    while attempts <= max_attempts:
        sim_data = simulate_qkd_protocol(num_qubits, eve_frac, noise, att_type, seed=sim_seed)
        alice_sifted = sim_data["alice_sifted"]
        bob_sifted = sim_data["bob_sifted"]
        sifted_bases = sim_data["sifted_bases"]
        qber, raw_a, raw_b, adv_feat = estimate_qber(alice_sifted, bob_sifted, sifted_bases, sample_fraction=0.25)
        
        final_key_len = len(raw_a) // 2 # approx
        status, reason = evaluate_security(qber)
        
        if status == "ACCEPTED" and final_key_len >= target_key_len:
            history.append({"attempt": attempts, "status": "ACCEPTED", "qber": qber})
            break
            
        history.append({"attempt": attempts, "status": status, "qber": qber})
        
        if attempts < max_attempts:
            attempts += 1
            if sim_seed is not None: sim_seed += 1
            if status == "ACCEPTED":
                num_qubits = int(num_qubits * 1.5)
        else:
            break
            
    return history

print("a) Eve 100% intercept")
h = run_test(500, 1.0, 0.0, "Standard Random", 42)
for att in h: print(att)

print("\nb) Noisy honest near threshold (noise=11%)")
for seed in [1, 2, 3]:
    print(f"Seed {seed}:")
    h = run_test(500, 0.0, 0.11, "Standard Random", seed)
    for att in h: print(att)
    
print("\nc) Normal run (noise=0, eve=0)")
h = run_test(500, 0.0, 0.0, "Standard Random", 100)
for att in h: print(att)
