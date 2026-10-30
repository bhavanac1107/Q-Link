import os
import sys
import numpy as np
import pandas as pd
import time

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eve import simulate_qkd_protocol, estimate_qber
from qber import evaluate_security

def run_experiment():
    noise_levels_pct = [0, 2, 4, 6, 8, 10]
    eves = [False, True]
    trials = 30
    num_qubits = 712
    
    os.makedirs('results', exist_ok=True)
    
    results = []
    
    print("Running noise sweep experiment...")
    print(f"Qubits: {num_qubits}, Trials: {trials}")
    print("-" * 50)
    
    seed = 1000
    for noise_pct in noise_levels_pct:
        noise = noise_pct / 100.0
        for eve in eves:
            attack_str = 1.0 if eve else 0.0
            
            qbers = []
            accepts = 0
            
            for t in range(trials):
                seed += 1
                sim_data = simulate_qkd_protocol(num_qubits, attack_strength=attack_str, noise_level=noise, seed=seed, seed_simulator=seed)
                
                alice = sim_data["alice_sifted"]
                bob = sim_data["bob_sifted"]
                
                qber, final_alice, _ = estimate_qber(alice, bob, sample_fraction=0.25)
                
                status, _ = evaluate_security(qber)
                accepted = 1 if status == "ACCEPTED" else 0
                final_len = len(final_alice) if status == "ACCEPTED" else 0
                
                results.append({
                    "noise": noise_pct,
                    "eve": "ON" if eve else "OFF",
                    "trial": t + 1,
                    "sifted_len": len(alice),
                    "qber": qber,
                    "accepted": accepted,
                    "final_key_len": final_len
                })
                
                qbers.append(qber)
                accepts += accepted
                
            qber_mean = np.mean(qbers)
            qber_std = np.std(qbers)
            accept_rate = accepts / trials
            
            eve_str = "ON " if eve else "OFF"
            print(f"Noise: {noise_pct:>2}% | Eve: {eve_str} | QBER: {qber_mean*100:>5.2f}% ± {qber_std*100:>5.2f}% | Accept Rate: {accept_rate*100:>5.1f}%")
            
    df = pd.DataFrame(results)
    df.to_csv("results/noise_sweep.csv", index=False)
    print("-" * 50)
    print("Results saved to results/noise_sweep.csv")

if __name__ == "__main__":
    start = time.time()
    run_experiment()
    print(f"Finished in {time.time() - start:.1f}s")
