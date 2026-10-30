import re

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
for i, line in enumerate(lines):
    if 'elif page ==' in line and 'Live' in line:
        start_idx = i
        break

new_demo_code = """elif page == "⚷ Live Encryption Demo":
    st.markdown("## Live Encryption Demo: Secure Comms")
    st.write("Bank Branch A (Alice) wants to send a secure message to the Data Center (Bob) over an optical fiber.")
    
    # Process retries
    run_retry = st.session_state.pop("run_retry", None)
    if run_retry == "eve_removed" and "sim_results" in st.session_state:
        with ui_effects.custom_spinner("Retrying with a fresh key (Eve removed)..."):
            import random, hashlib
            res = st.session_state.sim_results
            new_seed = random.randint(0, 9999999)
            s_len, qber, e_len, f_len, s_size, s_data, adv = run_simulation(
                res['num_qubits'], 0.0, res['noise_level'], res['attack_type'], seed=new_seed
            )
            status, reason = evaluate_security(qber)
            hash_passed = True
            if status == "ACCEPTED":
                a_hash = hashlib.sha256(s_data['final_alice'].tobytes()).hexdigest()[:8]
                b_hash = hashlib.sha256(s_data['final_bob'].tobytes()).hexdigest()[:8]
                if a_hash != b_hash:
                    status = "REJECTED"
                    hash_passed = False
                    reason = "Key confirmation failed (Hash mismatch). Uncorrected errors remain!"
            if res['security_method'] == "Machine Learning Model":
                ml_status, ml_reason, attack_prob = evaluate_security_ml(qber, res['num_qubits'], s_len, adv)
                reason = f"{reason}\\n\\n**ML Diagnostics**: {ml_reason}\\n**Attack Probability**: {attack_prob*100:.1f}%"
            st.session_state.sim_status = status
            st.session_state.sim_results.update({"sifted_len": s_len, "qber": qber, "ec_len": e_len, "final_key_len": f_len, "sample_size": s_size, "reason": reason, "eve_fraction": 0.0, "adv_feat": adv, "seed": new_seed, "alice_key": s_data.get('final_alice', []), "bob_key": s_data.get('final_bob', []), "eve_key": s_data.get('eve_final', []), "status": status, "hash_passed": hash_passed})
    elif run_retry == "fresh_key" and "sim_results" in st.session_state:
        with ui_effects.custom_spinner("Retrying with a fresh key..."):
            import random, hashlib
            res = st.session_state.sim_results
            new_seed = random.randint(0, 9999999)
            s_len, qber, e_len, f_len, s_size, s_data, adv = run_simulation(
                res['num_qubits'], res['eve_fraction'], res['noise_level'], res['attack_type'], seed=new_seed
            )
            status, reason = evaluate_security(qber)
            hash_passed = True
            if status == "ACCEPTED":
                a_hash = hashlib.sha256(s_data['final_alice'].tobytes()).hexdigest()[:8]
                b_hash = hashlib.sha256(s_data['final_bob'].tobytes()).hexdigest()[:8]
                if a_hash != b_hash:
                    status = "REJECTED"
                    hash_passed = False
                    reason = "Key confirmation failed (Hash mismatch). Uncorrected errors remain!"
            if res['security_method'] == "Machine Learning Model":
                ml_status, ml_reason, attack_prob = evaluate_security_ml(qber, res['num_qubits'], s_len, adv)
                reason = f"{reason}\\n\\n**ML Diagnostics**: {ml_reason}\\n**Attack Probability**: {attack_prob*100:.1f}%"
            st.session_state.sim_status = status
            st.session_state.sim_results.update({"sifted_len": s_len, "qber": qber, "ec_len": e_len, "final_key_len": f_len, "sample_size": s_size, "reason": reason, "adv_feat": adv, "seed": new_seed, "alice_key": s_data.get('final_alice', []), "bob_key": s_data.get('final_bob', []), "eve_key": s_data.get('eve_final', []), "status": status, "hash_passed": hash_passed})

    # SVG Diagram
    fiber_color = "#94a3b8"
    dot_color = "#94a3b8"
    eve_visible = False
    
    active_res = st.session_state.get('demo_sim_results', st.session_state.get('sim_results'))
    
    if active_res:
        status = active_res['status']
        if status == "ACCEPTED" and active_res['hash_passed']:
            fiber_color = "#22C55E"
            dot_color = "#22C55E"
        elif status == "REJECTED" or not active_res['hash_passed']:
            fiber_color = "#EF4444"
            dot_color = "#EF4444"
        else:
            fiber_color = "#F59E0B"
            dot_color = "#F59E0B"
            
        if active_res.get('eve_fraction', 0) > 0:
            eve_visible = True
            
    eve_svg = '<g transform="translate(270, 20)"><rect width="60" height="40" rx="8" fill="#131F45" stroke="#EF4444" stroke-width="2"/><text x="30" y="25" fill="#EF4444" font-size="14" font-family="sans-serif" font-weight="bold" text-anchor="middle">EVE</text></g>' if eve_visible else ''
    
    svg_html = f\"\"\"<div style="width: 100%; display: flex; justify-content: center; margin-bottom: 24px; margin-top: 24px;">
<svg width="100%" viewBox="0 0 600 150">
<line x1="100" y1="75" x2="500" y2="75" stroke="{fiber_color}" stroke-width="4" stroke-dasharray="8 4" />
<circle cx="100" cy="75" r="6" fill="{dot_color}">
<animate attributeName="cx" from="100" to="500" dur="2s" repeatCount="indefinite" />
</circle>
{eve_svg}
<rect x="20" y="35" width="80" height="80" rx="12" fill="#131F45" stroke="#3B82F6" stroke-width="2" />
<path d="M60 45 L40 60 L80 60 Z" fill="#3B82F6" />
<rect x="45" y="65" width="10" height="20" fill="#3B82F6" />
<rect x="65" y="65" width="10" height="20" fill="#3B82F6" />
<text x="60" y="140" fill="#E8ECF8" font-size="14" font-family="sans-serif" font-weight="bold" text-anchor="middle">Bank A</text>
<rect x="500" y="35" width="80" height="80" rx="12" fill="#131F45" stroke="#8B5CF6" stroke-width="2" />
<rect x="520" y="50" width="40" height="15" rx="2" fill="#8B5CF6" />
<rect x="520" y="70" width="40" height="15" rx="2" fill="#8B5CF6" />
<rect x="520" y="90" width="40" height="15" rx="2" fill="#8B5CF6" />
<text x="540" y="140" fill="#E8ECF8" font-size="14" font-family="sans-serif" font-weight="bold" text-anchor="middle">Data Center</text>
</svg>
</div>\"\"\"
    st.markdown(svg_html, unsafe_allow_html=True)

    msg_to_send = st.text_input("Message to encrypt", value="Transfer INR 5,00,000 to account ending 4821", max_chars=60)
    msg_bytes = msg_to_send.encode('utf-8')
    msg_bits = ''.join(format(b, '08b') for b in msg_bytes)
    target_key_len = len(msg_bits)
    
    st.markdown("#### Encryption Settings")
    if not st.session_state.get('sim_results'):
        st.warning("Run a simulation on the Home page first to generate a quantum key.")
    else:
        res = st.session_state.sim_results
        st.info(f"Using your last simulation: {res['num_qubits']} qubits, Eve {res['eve_fraction']*100:.0f}%, noise {res['noise_level']*100:.1f}%, seed {res['seed']}")
        
        with st.expander("Advanced: custom settings for this demo (creates a separate session)"):
            c1, c2 = st.columns(2)
            with c1:
                c_num_qubits = st.slider("Qubits (Custom)", 16, 4000, 700, key="c_qubits")
                c_noise = st.slider("Noise (%)", 0.0, 20.0, 0.0, key="c_noise")
            with c2:
                c_eve = st.slider("Eve (%)", 0, 100, 50, key="c_eve")
                c_seed = st.number_input("Seed", 0, 9999999, 42, key="c_seed")
            if st.button("Run Custom Session"):
                with ui_effects.custom_spinner("Running custom..."):
                    import hashlib
                    s_len, qber, e_len, f_len, s_size, s_data, adv = run_simulation(c_num_qubits, c_eve/100.0, c_noise/100.0, "Standard Random", seed=c_seed)
                    status, reason = evaluate_security(qber)
                    hp = True
                    if status == "ACCEPTED":
                        if hashlib.sha256(s_data['final_alice'].tobytes()).hexdigest()[:8] != hashlib.sha256(s_data['final_bob'].tobytes()).hexdigest()[:8]:
                            status = "REJECTED"
                            hp = False
                            reason = "Hash mismatch!"
                    st.session_state.demo_sim_results = {"sifted_len": s_len, "qber": qber, "ec_len": e_len, "final_key_len": f_len, "sample_size": s_size, "reason": reason, "num_qubits": c_num_qubits, "eve_fraction": c_eve/100.0, "noise_level": c_noise/100.0, "attack_type": "Standard Random", "adv_feat": adv, "seed": c_seed, "alice_key": s_data.get('final_alice', []), "bob_key": s_data.get('final_bob', []), "eve_key": s_data.get('eve_final', []), "status": status, "hash_passed": hp, "security_method": "11% Hard Threshold"}
                    st.rerun()
            if st.button("Clear Custom Session") and "demo_sim_results" in st.session_state:
                del st.session_state.demo_sim_results
                st.rerun()

        if active_res['status'] != "ACCEPTED" or not active_res['hash_passed']:
            st.error(f"**Encryption Refused.** The key was rejected during simulation.\\n\\n**Reason:** {active_res['reason']}")
            st.markdown("---")
            st.markdown("### Event Log")
            with st.expander(f"Attempt 1 - {active_res['status']}", expanded=True):
                st.write(f"**QBER:** {active_res['qber']*100:.2f}%")
                st.write(f"**Sifted Length:** {active_res['sifted_len']}")
                st.write(f"**Final Key Length:** {active_res['final_key_len']}")
                st.write(f"**Reason:** {active_res['reason']}")
                if not active_res['hash_passed']:
                    import hashlib
                    a_h = hashlib.sha256(active_res['alice_key'].tobytes()).hexdigest()[:8]
                    b_h = hashlib.sha256(active_res['bob_key'].tobytes()).hexdigest()[:8]
                    st.write(f"Alice Hash: `{a_h}` | Bob Hash: `{b_h}`")
            
            st.markdown("---")
            if active_res.get('eve_fraction', 0) > 0:
                if st.button("Manually restart link without Eve", type="secondary"):
                    st.session_state.run_retry = "eve_removed"
                    if 'demo_sim_results' in st.session_state: del st.session_state.demo_sim_results
                    st.rerun()
            else:
                if st.button("Manually retry with a fresh key", type="secondary"):
                    st.session_state.run_retry = "fresh_key"
                    if 'demo_sim_results' in st.session_state: del st.session_state.demo_sim_results
                    st.rerun()
        else:
            if active_res['final_key_len'] < target_key_len:
                st.error(f"**Encryption Refused.** Key is too short ({active_res['final_key_len']} bits) to encrypt a {target_key_len}-bit message.")
                st.markdown("---")
                if st.button("Manually retry with a fresh key", type="secondary"):
                    st.session_state.run_retry = "fresh_key"
                    if 'demo_sim_results' in st.session_state: del st.session_state.demo_sim_results
                    st.rerun()
            else:
                st.success("✅ **SECURE KEY ESTABLISHED**")
                
                # Encrypt
                ciphertext, key_used, _ = encrypt_message(msg_bits, active_res['alice_key'])
                
                # Bob decrypts with HIS key
                decrypted_bits = decrypt_message(ciphertext, active_res['bob_key'])
                
                # Eve decrypts with HER key
                if active_res.get('eve_fraction', 0) > 0 and len(active_res.get('eve_key', [])) > 0:
                    eve_decrypted_bits = decrypt_message(ciphertext, active_res['eve_key'])
                else:
                    eve_decrypted_bits = "0" * len(msg_bits)
                    
                def bits_to_str(bits):
                    try:
                        chars = [chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8)]
                        return "".join(c if c.isprintable() else '' for c in chars)
                    except:
                        return "" * (len(bits)//8)
                
                bob_str = bits_to_str(decrypted_bits)
                eve_str = bits_to_str(eve_decrypted_bits)
                
                st.markdown("---")
                st.markdown("### Decryption: Bob vs Eve")
                
                col_b, col_e = st.columns(2)
                with col_b:
                    st.markdown(f"<div class='glass-card' style='border-left: 4px solid #8B5CF6;'>", unsafe_allow_html=True)
                    st.markdown("<h4 style='margin-top: 0; color: #8B5CF6;'>Bob (Intended Recipient)</h4>", unsafe_allow_html=True)
                    st.markdown(f"**Decrypted Text:**\\n\\n<div class='mono-font' style='font-size: 1.2rem; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px;'>{bob_str}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col_e:
                    st.markdown(f"<div class='glass-card' style='border-left: 4px solid #EF4444;'>", unsafe_allow_html=True)
                    st.markdown("<h4 style='margin-top: 0; color: #EF4444;'>Eve (Eavesdropper)</h4>", unsafe_allow_html=True)
                    if active_res.get('eve_fraction', 0) == 0:
                        st.markdown("**Status:** Eve is not present on the line.")
                        st.markdown(f"**Decrypted Text:**\\n\\n<div class='mono-font' style='font-size: 1.2rem; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px; color: #94a3b8;'>[No data intercepted]</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**Status:** Intercepted {active_res.get('eve_fraction', 0)*100:.0f}% of qubits.")
                        st.markdown(f"**Decrypted Text:**\\n\\n<div class='mono-font' style='font-size: 1.2rem; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px; color: #EF4444;'>{eve_str}</div>", unsafe_allow_html=True)
                        st.caption("Notice how Eve's text is completely scrambled. The privacy amplification destroyed any partial information she gained.")
                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("### Event Log")
                with st.expander(f"Attempt 1 - {active_res['status']}", expanded=False):
                    st.write(f"**QBER:** {active_res['qber']*100:.2f}%")
                    st.write(f"**Sifted Length:** {active_res['sifted_len']}")
                    st.write(f"**Final Key Length:** {active_res['final_key_len']}")
                    import hashlib
                    a_h = hashlib.sha256(active_res['alice_key'].tobytes()).hexdigest()[:8]
                    b_h = hashlib.sha256(active_res['bob_key'].tobytes()).hexdigest()[:8]
                    st.write(f"Alice Hash: `{a_h}` | Bob Hash: `{b_h}`")
                
                if st.button("Manually retry with a fresh key", type="secondary"):
                    st.session_state.run_retry = "fresh_key"
                    if 'demo_sim_results' in st.session_state: del st.session_state.demo_sim_results
                    st.rerun()
"""

new_lines = lines[:start_idx] + [new_demo_code + "\\n"]

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
