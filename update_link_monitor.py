import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update the loop to add reject_reason
target_loop = '''                    # Outcome
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
                    })'''

replacement_loop = '''                    # Outcome
                    delivered = False
                    if status == "ACCEPTED" and hash_passed and f_len >= msg_len:
                        delivered = True
                        
                    reject_reason = ""
                    if status == "REJECTED":
                        if not hash_passed:
                            reject_reason = "Key confirmation failed"
                        else:
                            reject_reason = "QBER > 11%"
                            
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
                        "reject_reason": reject_reason,
                        "seed": sess_seed
                    })'''

if target_loop in code:
    code = code.replace(target_loop, replacement_loop)
else:
    print("Warning: target_loop not found")

# 2. Update KPIs
target_kpis = '''            # KPIs
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Transfers Delivered", total_delivered)
            c2.metric("Transfers Blocked", total_blocked)
            c3.metric("Detection Delay", f"{delay} sessions" if isinstance(delay, int) else delay)
            c4.metric("False Alarms (No Eve)", false_alarms)'''

replacement_kpis = '''            # KPIs
            qber_rejects = sum(1 for r in res_list if r['reject_reason'] == "QBER > 11%")
            hash_rejects = sum(1 for r in res_list if r['reject_reason'] == "Key confirmation failed")
            
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Transfers Delivered", total_delivered)
            c2.metric("Transfers Blocked", total_blocked)
            c3.metric("Detection Delay", f"{delay} sessions" if isinstance(delay, int) else delay)
            c4.metric("Rejected (QBER | Hash)", f"{qber_rejects} | {hash_rejects}")
            c5.metric("False Alarms (No Eve)", false_alarms)'''

if target_kpis in code:
    code = code.replace(target_kpis, replacement_kpis)
else:
    print("Warning: target_kpis not found")

# 3. Update Chart Caption
target_caption = '''            st.plotly_chart(fig1, use_container_width=True)'''

replacement_caption = '''            st.caption("Note: Sessions can be rejected by the QBER > 11% rule, or by the final SHA-256 Key Confirmation failing if uncorrected errors remain.\\n\\n*Why might QBER be lower than 25% at 100% intercept?* Under Intercept-Resend, Eve introduces a 25% error rate on average. In any single session (e.g. ~350 sifted bits from 700 qubits), normal statistical variance means the measured QBER will fluctuate around 25% (e.g., between 20% and 30%).")
            st.plotly_chart(fig1, use_container_width=True)'''

if target_caption in code:
    code = code.replace(target_caption, replacement_caption)
else:
    print("Warning: target_caption not found")

# 4. Update Chips
target_chips = '''                    bg = "#EF4444" # Red: blocked
                    text = "#FFF"
                strip_html += f"<div title='Session {r['session']} | QBER: {r['qber']*100:.1f}% | Deliv: {r['delivered']}' style='background-color: {bg}; color: {text}; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 4px; font-weight: bold; font-size: 0.8rem; cursor: help;'>{r['session']}</div>"
            strip_html += "</div>"'''

replacement_chips = '''                    bg = "#EF4444" # Red: blocked
                    text = "#FFF"
                
                chip_title = f"Session {r['session']} | QBER: {r['qber']*100:.1f}% | Deliv: {r['delivered']}"
                if r['reject_reason']:
                    chip_title += f" | Rejected: {r['reject_reason']}"
                strip_html += f"<div title='{chip_title}' style='background-color: {bg}; color: {text}; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 4px; font-weight: bold; font-size: 0.8rem; cursor: help;'>{r['session']}</div>"
            strip_html += "</div>"'''

if target_chips in code:
    code = code.replace(target_chips, replacement_chips)
else:
    print("Warning: target_chips not found")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully updated Link Monitor.")
