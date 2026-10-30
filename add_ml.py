import re
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

ml_section = """    st.markdown("---")
    st.markdown("## ML Live Diagnostics")
    st.caption("Real-time analysis of the current simulation run by the trained Machine Learning model.")
    
    if res.get('adv_feat') is not None:
        from qber import evaluate_security_ml
        ml_status, ml_reason, attack_prob = evaluate_security_ml(res['qber'], res['num_qubits'], res['sifted_len'], res['adv_feat'])
        
        ml_col1, ml_col2 = st.columns([1, 2])
        with ml_col1:
            fig_prob = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = attack_prob * 100,
                title = {'text': "ML Attack Probability", 'font': {'color': '#E8ECF8'}},
                gauge = {
                    'axis': {'range': [None, 100], 'tickcolor': '#E8ECF8'},
                    'bar': {'color': "#EF4444" if ml_status == "REJECTED" else "#22C55E"},
                    'bgcolor': "rgba(255,255,255,0.1)",
                    'borderwidth': 2,
                    'bordercolor': "rgba(120,150,255,0.18)",
                    'steps': [
                        {'range': [0, 50], 'color': 'rgba(34,197,94,0.1)'},
                        {'range': [50, 100], 'color': 'rgba(239,68,68,0.2)'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 50
                    }
                }
            ))
            fig_prob.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Times New Roman, Times, serif", color="#E8ECF8"), height=300)
            st.plotly_chart(fig_prob, use_container_width=True)
            
        with ml_col2:
            st.markdown(f"<div class='glass-card' style='height: 100%;'>", unsafe_allow_html=True)
            if ml_status == "REJECTED":
                st.markdown("<h3 style='color: #EF4444; margin-top: 0;'>✕ Attack Detected</h3>", unsafe_allow_html=True)
            else:
                st.markdown("<h3 style='color: #22C55E; margin-top: 0;'>✓ Channel Secure</h3>", unsafe_allow_html=True)
                
            st.write(ml_reason)
            
            st.markdown("**Features given to the model:**")
            st.write(f"- Block Variance: `{res['adv_feat']['block_var']:.4f}`")
            st.write(f"- Max Block QBER: `{res['adv_feat']['max_block']:.4f}`")
            st.write(f"- Basis Asymmetry: `{res['adv_feat']['basis_asym']:.4f}`")
            st.write(f"- Z-Basis QBER: `{res['adv_feat']['z_qber']:.4f}`")
            st.write(f"- X-Basis QBER: `{res['adv_feat']['x_qber']:.4f}`")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No advanced features available for this run.")
"""

code = code.replace('    st.markdown("---")\n    st.markdown("## ML Model Evaluation (Offline)")', ml_section + '\n    st.markdown("---")\n    st.markdown("## ML Model Evaluation (Offline)")')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
