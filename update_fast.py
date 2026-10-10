import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update run_simulation signature
target_def = '''def run_simulation(num_qubits, attack_strength, noise_level=0.0, attack_type="Standard Random", seed=None):
    """Runs the BB84 simulation and returns results."""
    sim_data = simulate_qkd_protocol(num_qubits, attack_strength, noise_level=noise_level, attack_type=attack_type, seed=seed)'''

replacement_def = '''def run_simulation(num_qubits, attack_strength, noise_level=0.0, attack_type="Standard Random", seed=None, fast_mode=False):
    """Runs the BB84 simulation and returns results."""
    sim_data = simulate_qkd_protocol(num_qubits, attack_strength, noise_level=noise_level, attack_type=attack_type, seed=seed, fast_mode=fast_mode)'''

code = code.replace(target_def, replacement_def)

# 2. Update Link Monitor loop for fast_mode=True and progress bar
target_loop = '''                # Target message size is 24 bits (e.g. transfer instruction)
                msg_len = 24
                
                for i in range(1, num_sess + 1):
                    is_eve_active = (i >= eve_start)
                    current_eve_frac = (intercept / 100.0) if is_eve_active else 0.0
                    sess_seed = base_seed + i
                    
                    s_len, qber, e_len, f_len, s_size, s_data, adv = run_simulation(
                        h_res['num_qubits'], current_eve_frac, h_res['noise_level'], h_res['attack_type'], seed=sess_seed
                    )'''

replacement_loop = '''                # Target message size is 24 bits (e.g. transfer instruction)
                msg_len = 24
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(1, num_sess + 1):
                    progress_bar.progress(i / num_sess)
                    status_text.text(f"Fast Simulating session {i} of {num_sess}...")
                    
                    is_eve_active = (i >= eve_start)
                    current_eve_frac = (intercept / 100.0) if is_eve_active else 0.0
                    sess_seed = base_seed + i
                    
                    s_len, qber, e_len, f_len, s_size, s_data, adv = run_simulation(
                        h_res['num_qubits'], current_eve_frac, h_res['noise_level'], h_res['attack_type'], seed=sess_seed, fast_mode=True
                    )'''

code = code.replace(target_loop, replacement_loop)

# 3. Clear progress bar at the end of loop
target_endloop = '''                    results_list.append({
                        "session": i,
                        "eve_active": is_eve_active,
                        "qber": qber,
                        "sifted": s_len,
                        "final_key": f_len,
                        "status": status,
                        "ml_status": ml_status,
                        "attack_prob": attack_prob,
                        "hash_passed": hash_passed,
                        "delivered": delivered,
                        "reject_reason": reject_reason,
                        "seed": sess_seed
                    })
                    
                st.session_state.link_monitor_run = {'''

replacement_endloop = '''                    results_list.append({
                        "session": i,
                        "eve_active": is_eve_active,
                        "qber": qber,
                        "sifted": s_len,
                        "final_key": f_len,
                        "status": status,
                        "ml_status": ml_status,
                        "attack_prob": attack_prob,
                        "hash_passed": hash_passed,
                        "delivered": delivered,
                        "reject_reason": reject_reason,
                        "seed": sess_seed
                    })
                    
                status_text.empty()
                progress_bar.empty()
                    
                st.session_state.link_monitor_run = {'''

code = code.replace(target_endloop, replacement_endloop)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully updated app.py for fast_mode.")
