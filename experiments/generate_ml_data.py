import os
import sys
import numpy as np
import pandas as pd
import time
import random

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eve import simulate_qkd_protocol, estimate_qber

def generate_data(num_samples=1000):
    os.makedirs('results', exist_ok=True)
    results = []
    
    print(f"Generating {num_samples} samples for ML dataset...")
    
    seed = 4200
    for i in range(num_samples):
        # Randomly choose parameters
        num_qubits = random.randint(100, 2000)
        noise_pct = random.uniform(0, 10.0)
        noise = noise_pct / 100.0
        
        eve_present = random.choice([True, False])
        if eve_present:
            attack_str = random.uniform(0.1, 1.0)
        else:
            attack_str = 0.0
            
        seed += 1
        
        # We need to run simulation
        # It takes about 0.05-0.2s per run for 100-2000 qubits
        sim_data = simulate_qkd_protocol(num_qubits, attack_strength=attack_str, noise_level=noise, seed=seed, seed_simulator=seed)
        
        alice = sim_data["alice_sifted"]
        bob = sim_data["bob_sifted"]
        
        # We only estimate qber, no need to do privacy amplification for dataset feature extraction
        qber, _, _ = estimate_qber(alice, bob, sample_fraction=0.25)
        
        results.append({
            "num_qubits": num_qubits,
            "noise_pct": noise_pct,
            "attack_strength": attack_str,
            "qber": qber,
            "sifted_len": len(alice),
            "eve_present": 1 if eve_present else 0
        })
        
        if (i + 1) % 50 == 0:
            print(f"Generated {i + 1}/{num_samples} samples...")
            
    df = pd.DataFrame(results)
    df.to_csv("results/ml_dataset.csv", index=False)
    print("Dataset saved to results/ml_dataset.csv")

if __name__ == "__main__":
    start = time.time()
    generate_data(250)
    print(f"Finished in {time.time() - start:.1f}s")
