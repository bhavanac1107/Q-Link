import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add random seed to Home Page simulation and store all required fields
home_sim_old = """    if st.button("Run Simulation", type="primary", use_container_width=False):
        with ui_effects.custom_spinner("Preparing qubits, measuring, and sifting..."):
            sifted_len, qber, ec_len, final_key_len, sample_size, sim_data, adv_feat = run_simulation(
                num_qubits, eve_fraction / 100.0, noise_level / 100.0, attack_type
            )
            
            st.session_state.final_alice_key = sim_data.get('final_alice', [])
            st.session_state.final_bob_key = sim_data.get('final_bob', [])
            st.session_state.sim_data = sim_data
            
            if sample_size < 30:
                status = "INCONCLUSIVE"
                reason = f"Sample of {sample_size} bits is too small for a reliable QBER. Increase the number of qubits."
            else:
                status, reason = evaluate_security(qber)
                
                if security_method == "Machine Learning Model":
                    ml_status, ml_reason, attack_prob = evaluate_security_ml(qber, num_qubits, sifted_len, adv_feat)
                    reason = f"{reason}\\n\\n**ML Diagnostics**: {ml_reason}\\n**Attack Probability**: {attack_prob*100:.1f}%"
                
            st.session_state.sim_status = status
            
            st.session_state.sim_results = {
                "sifted_len": sifted_len,
                "qber": qber,
                "ec_len": ec_len,
                "final_key_len": final_key_len,
                "sample_size": sample_size,
                "reason": reason,
                "num_qubits": num_qubits,
                "eve_fraction": eve_fraction,
                "noise_level": noise_level,
                "attack_type": attack_type,
                "adv_feat": sim_data.get('adv_feat', None)
            }
            
        st.success("Simulation complete! Go to Results & Analysis to view the breakdown.")"""

home_sim_new = """    if st.button("Run Simulation", type="primary", use_container_width=False):
        with ui_effects.custom_spinner("Preparing qubits, measuring, and sifting..."):
            import random, hashlib
            sim_seed = random.randint(0, 9999999)
            sifted_len, qber, ec_len, final_key_len, sample_size, sim_data, adv_feat = run_simulation(
                num_qubits, eve_fraction / 100.0, noise_level / 100.0, attack_type, seed=sim_seed
            )
            
            st.session_state.final_alice_key = sim_data.get('final_alice', [])
            st.session_state.final_bob_key = sim_data.get('final_bob', [])
            st.session_state.sim_data = sim_data
            
            hash_passed = True
            if sample_size < 30:
                status = "INCONCLUSIVE"
                reason = f"Sample of {sample_size} bits is too small for a reliable QBER. Increase the number of qubits."
            else:
                status, reason = evaluate_security(qber)
                
                # Key Confirmation
                if status == "ACCEPTED":
                    alice_hash = hashlib.sha256(sim_data['final_alice'].tobytes()).hexdigest()[:8]
                    bob_hash = hashlib.sha256(sim_data['final_bob'].tobytes()).hexdigest()[:8]
                    if alice_hash != bob_hash:
                        status = "REJECTED"
                        hash_passed = False
                        reason = f"Key confirmation failed (Hash mismatch). Uncorrected errors remain!"
                
                if security_method == "Machine Learning Model":
                    ml_status, ml_reason, attack_prob = evaluate_security_ml(qber, num_qubits, sifted_len, adv_feat)
                    reason = f"{reason}\\n\\n**ML Diagnostics**: {ml_reason}\\n**Attack Probability**: {attack_prob*100:.1f}%"
                
            st.session_state.sim_status = status
            
            st.session_state.sim_results = {
                "sifted_len": sifted_len,
                "qber": qber,
                "ec_len": ec_len,
                "final_key_len": final_key_len,
                "sample_size": sample_size,
                "reason": reason,
                "num_qubits": num_qubits,
                "eve_fraction": eve_fraction,
                "noise_level": noise_level,
                "attack_type": attack_type,
                "adv_feat": sim_data.get('adv_feat', None),
                "seed": sim_seed,
                "alice_key": sim_data.get('final_alice', []),
                "bob_key": sim_data.get('final_bob', []),
                "eve_key": sim_data.get('eve_final', []),
                "status": status,
                "hash_passed": hash_passed,
                "security_method": security_method
            }
            
        st.success("Simulation complete! Go to Results & Analysis to view the breakdown.")"""

code = code.replace(home_sim_old, home_sim_new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
