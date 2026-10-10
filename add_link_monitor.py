import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update the sidebar
target_sidebar = '''        [
            "⌂ Home / Simulation", 
            "▤ Results & Analysis", 
            "⚷ Live Encryption Demo"
        ],'''
replacement_sidebar = '''        [
            "⌂ Home / Simulation", 
            "▤ Results & Analysis", 
            "⚷ Live Encryption Demo",
            "📈 Link Monitor"
        ],'''

if target_sidebar in code:
    code = code.replace(target_sidebar, replacement_sidebar)
else:
    print("WARNING: Sidebar replacement failed!")

# 2. Append the new page logic
new_page_code = """
elif page == "📈 Link Monitor":
    st.markdown("## Link Monitor: Operator View")
    st.write("Monitor consecutive key-exchange sessions on a single optical link. Eve will activate partway through the experiment.")
    
    # 1. Check for Home simulation
    if not st.session_state.get('sim_results'):
        st.warning("Run a simulation on the Home page first to set the link parameters.")
    else:
        h_res = st.session_state.sim_results
        
        st.info(f"**Link Parameters (from Home):** {h_res['num_qubits']} qubits/session, {h_res['noise_level']*100:.1f}% channel noise, {h_res['attack_type']} attack.")
        
        # Controls
        st.markdown("#### Monitor Setup")
        
        # We can use st.session_state to store form values so preset buttons work
        if 'lm_intercept' not in st.session_state:
            st.session_state.lm_intercept = 100
            
        def set_stealth():
            import random
            st.session_state.lm_intercept = random.randint(10, 15)
            
        c1, c2, c3 = st.columns(3)
        with c1:
            num_sess = st.number_input("Number of sessions", 5, 50, 20)
        with c2:
            eve_start = st.number_input("Eve starts at session #", 1, 50, 8)
        with c3:
            intercept = st.slider("Eve Intercept (%)", 10, 100, st.session_state.lm_intercept, key="lm_intercept")
            st.button("Stealth Eve Preset (10-15%)", on_click=set_stealth)
            
        c_run1, c_run2 = st.columns(2)
        with c_run1:
            run_btn = st.button("Run Monitor", type="primary", use_container_width=True)
        with c_run2:
            new_seed_btn = st.button("Re-run with new seed", use_container_width=True)
            
        if new_seed_btn:
            import random
            st.session_state.lm_seed = random.randint(0, 9999999)
            run_btn = True
            
        if 'lm_seed' not in st.session_state:
            st.session_state.lm_seed = h_res['seed']
            
        if run_btn:
            with ui_effects.custom_spinner("Running sequential sessions..."):
                import random, hashlib
                base_seed = st.session_state.lm_seed
                results_list = []
                
                # Target message size is 24 bits (e.g. transfer instruction)
                msg_len = 24
                
                for i in range(1, num_sess + 1):
                    is_eve_active = (i >= eve_start)
                    current_eve_frac = (intercept / 100.0) if is_eve_active else 0.0
                    sess_seed = base_seed + i
                    
                    s_len, qber, e_len, f_len, s_size, s_data, adv = run_simulation(
                        h_res['num_qubits'], current_eve_frac, h_res['noise_level'], h_res['attack_type'], seed=sess_seed
                    )
                    
                    status, reason = evaluate_security(qber)
                    ml_status, ml_reason, attack_prob = evaluate_security_ml(qber, h_res['num_qubits'], s_len, adv)
                    
                    hash_passed = True
                    if status == "ACCEPTED":
                        a_h = hashlib.sha256(s_data['final_alice'].tobytes()).hexdigest()[:8]
                        b_h = hashlib.sha256(s_data['final_bob'].tobytes()).hexdigest()[:8]
                        if a_h != b_h:
                            status = "REJECTED"
                            hash_passed = False
                            reason = "Key confirmation failed (Hash mismatch)."
                            
                    # Outcome
                    delivered = False
                    if status == "ACCEPTED" and hash_passed and f_len >= msg_len:
                        delivered = True
                        
                    results_list.append({
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
                        "seed": sess_seed
                    })
                    
                st.session_state.link_monitor_run = {
                    "results": results_list,
                    "num_sess": num_sess,
                    "eve_start": eve_start,
                    "intercept": intercept,
                    "base_seed": base_seed
                }
                
        # --- DISPLAY RESULTS ---
        if "link_monitor_run" in st.session_state:
            lm = st.session_state.link_monitor_run
            res_list = lm['results']
            
            # Analyze timeline
            first_detection = None
            total_delivered = sum(1 for r in res_list if r['delivered'])
            total_blocked = sum(1 for r in res_list if not r['delivered'])
            
            false_alarms = 0
            false_accepts = 0
            secret_bits_before = 0
            secret_bits_after = 0
            
            for r in res_list:
                # Security metrics
                if not r['eve_active'] and not r['delivered']:
                    false_alarms += 1
                if r['eve_active'] and r['delivered']:
                    false_accepts += 1
                    
                if r['eve_active'] and not r['delivered'] and first_detection is None:
                    first_detection = r['session']
                    
                if not r['eve_active'] and r['delivered']:
                    secret_bits_before += r['final_key']
                if r['eve_active'] and r['delivered']:
                    secret_bits_after += r['final_key']
                    
            if first_detection:
                alert_status = "🚨 ALERT: ATTACK DETECTED"
                alert_color = "#EF4444"
                alert_sub = f"Eavesdropper locked out starting at session {first_detection}."
                delay = first_detection - lm['eve_start']
            elif lm['eve_start'] <= lm['num_sess'] and false_accepts > 0:
                alert_status = "⚠️ ALERT: COMPROMISED"
                alert_color = "#F59E0B"
                alert_sub = "Eve went completely undetected by the 11% threshold!"
                delay = "Missed"
            else:
                alert_status = "✅ LINK STATUS: SECURE"
                alert_color = "#22C55E"
                alert_sub = "No attacks detected on the line."
                delay = "N/A"
                
            st.markdown(f\"\"\"
            <div style='background-color: {alert_color}20; border: 2px solid {alert_color}; border-radius: 8px; padding: 15px; text-align: center; margin: 20px 0;'>
                <h2 style='color: {alert_color}; margin: 0;'>{alert_status}</h2>
                <p style='margin: 5px 0 0 0; color: #E8ECF8;'>{alert_sub}</p>
            </div>
            \"\"\", unsafe_allow_html=True)
            
            # KPIs
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Transfers Delivered", total_delivered)
            c2.metric("Transfers Blocked", total_blocked)
            c3.metric("Detection Delay", f"{delay} sessions" if isinstance(delay, int) else delay)
            c4.metric("False Alarms (No Eve)", false_alarms)
            
            # Charts
            import plotly.graph_objects as go
            
            sessions = [r['session'] for r in res_list]
            qbers = [r['qber']*100 for r in res_list]
            probs = [r['attack_prob']*100 for r in res_list]
            
            fig1 = go.Figure()
            # Background shade for Eve
            if lm['eve_start'] <= lm['num_sess']:
                fig1.add_vrect(
                    x0=lm['eve_start'], x1=lm['num_sess'],
                    fillcolor="rgba(239, 68, 68, 0.1)", layer="below", line_width=0,
                    annotation_text="Eve Active", annotation_position="top left",
                    annotation_font_color="#EF4444"
                )
            
            # 11% Threshold
            fig1.add_hline(y=11, line_dash="dash", line_color="#F59E0B", annotation_text="11% Threshold")
            
            # QBER Line
            fig1.add_trace(go.Scatter(x=sessions, y=qbers, mode='lines+markers', name='QBER (%)', line=dict(color='#3B82F6', width=3), marker=dict(size=8)))
            
            # Detection marker
            if first_detection:
                fig1.add_trace(go.Scatter(
                    x=[first_detection], y=[qbers[first_detection-1]], mode='markers',
                    marker=dict(color='#EF4444', size=12, symbol='star'), name='First Detection'
                ))
                
            fig1.update_layout(
                title="QBER Across Sessions",
                xaxis_title="Session #", yaxis_title="QBER (%)",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E8ECF8"), height=350, margin=dict(l=40, r=40, t=40, b=40)
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            fig2 = go.Figure()
            if lm['eve_start'] <= lm['num_sess']:
                fig2.add_vrect(
                    x0=lm['eve_start'], x1=lm['num_sess'],
                    fillcolor="rgba(239, 68, 68, 0.1)", layer="below", line_width=0,
                )
            fig2.add_trace(go.Scatter(x=sessions, y=probs, mode='lines+markers', name='ML Attack Prob (%)', line=dict(color='#8B5CF6', width=3)))
            fig2.update_layout(
                title="ML Diagnostic (Attack Probability)",
                xaxis_title="Session #", yaxis_title="Probability (%)",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E8ECF8"), height=300, margin=dict(l=40, r=40, t=40, b=40),
                showlegend=True
            )
            st.caption("Note: ML is used for diagnostic scoring here. The 11% QBER rule handles the actual accept/reject decision.")
            st.plotly_chart(fig2, use_container_width=True)
            
            # Session Strip
            st.markdown("### Session Strip")
            strip_html = "<div style='display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px;'>"
            for r in res_list:
                # Color mapping
                if r['delivered']:
                    if r['ml_status'] == "REJECTED":
                        bg = "#F59E0B" # Amber: delivered but ML warned
                        text = "#000"
                    else:
                        bg = "#22C55E" # Green: secure
                        text = "#000"
                else:
                    bg = "#EF4444" # Red: blocked
                    text = "#FFF"
                strip_html += f"<div title='Session {r['session']} | QBER: {r['qber']*100:.1f}% | Deliv: {r['delivered']}' style='background-color: {bg}; color: {text}; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 4px; font-weight: bold; font-size: 0.8rem; cursor: help;'>{r['session']}</div>"
            strip_html += "</div>"
            st.markdown(strip_html, unsafe_allow_html=True)
            
            # Table
            st.markdown("### Data Export")
            import pandas as pd
            df = pd.DataFrame(res_list)
            df['qber'] = (df['qber'] * 100).round(2).astype(str) + '%'
            df['attack_prob'] = (df['attack_prob'] * 100).round(1).astype(str) + '%'
            st.dataframe(df, use_container_width=True)
            
            # JSON Report
            import json
            report = {
                "experiment_seed": lm['base_seed'],
                "settings": {
                    "qubits": h_res['num_qubits'],
                    "noise": h_res['noise_level'],
                    "attack_type": h_res['attack_type']
                },
                "scenario": {
                    "sessions": lm['num_sess'],
                    "eve_starts_at": lm['eve_start'],
                    "eve_intercept": lm['intercept']
                },
                "results": {
                    "first_detection_session": first_detection,
                    "false_accepts": false_accepts,
                    "false_alarms": false_alarms,
                    "secret_bits_before_eve": secret_bits_before,
                    "secret_bits_after_eve": secret_bits_after
                }
            }
            st.download_button(
                label="📥 Download JSON Report",
                data=json.dumps(report, indent=4),
                file_name="link_monitor_report.json",
                mime="application/json"
            )
"""

if "elif page == \"📈 Link Monitor\":" not in code:
    if code.endswith("\n\n"):
        code += new_page_code
    else:
        code += "\n\n" + new_page_code

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
    
print("Successfully injected Link Monitor.")
