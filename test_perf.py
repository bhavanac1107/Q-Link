import time
from app import run_simulation
import warnings
warnings.filterwarnings("ignore")

qubit_counts = [8, 16, 20, 712, 2000]

print("Performance and Correctness Test")
print("================================")

for num_qubits in qubit_counts:
    for eve_on in [False, True]:
        start = time.time()
        sifted_len, qber, final_key_len, sample_size, sim_data = run_simulation(num_qubits, eve_on)
        end = time.time()
        
        print(f"Qubits: {num_qubits:4d} | Eve ON: {str(eve_on):5s} | Time: {end-start:.3f}s")
        print(f"  Sifted Key: {sifted_len} bits | QBER: {qber*100:.1f}% | Final Key: {final_key_len} bits")
        
        if not eve_on:
            # Check correctness: With Eve OFF, all matched bases should have matching bits
            a_bits = sim_data["alice_bits"]
            a_bases = sim_data["alice_bases"]
            b_bases = sim_data["bob_bases"]
            b_bits = sim_data["bob_bits"]
            
            errors = 0
            matches = 0
            for i in range(num_qubits):
                if a_bases[i] == b_bases[i]:
                    matches += 1
                    if a_bits[i] != b_bits[i]:
                        errors += 1
            if errors == 0:
                print(f"  Correctness Check: PASS (0 errors in {matches} matching bases)")
            else:
                print(f"  Correctness Check: FAIL ({errors} errors in {matches} matching bases)")
        print("-" * 50)
