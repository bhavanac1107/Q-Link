"""
Phase 5: Streamlit Dashboard UI Polish
A modern cybersecurity dashboard simulating BB84 QKD.
"""
import streamlit as st
import numpy as np
import random
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'Times', 'Liberation Serif', 'serif']

from bb84 import generate_random_bits, generate_random_bases
from eve import simulate_qkd_protocol, estimate_qber, encode_qubits_alice, measure_qubits_bob, eve_intercept
from qber import evaluate_security, evaluate_security_ml
from pipeline import simple_error_correction, privacy_amplification
from otp import encrypt_message, decrypt_message

@st.cache_data(show_spinner=False)
def run_simulation(num_qubits, attack_strength, noise_level=0.0, attack_type="Standard Random", seed=None, fast_mode=False):
    """Runs the BB84 simulation and returns results."""
    sim_data = simulate_qkd_protocol(num_qubits, attack_strength, noise_level=noise_level, attack_type=attack_type, seed=seed, fast_mode=fast_mode)
    alice_sifted = sim_data["alice_sifted"]
    bob_sifted = sim_data["bob_sifted"]
    sifted_bases = sim_data["sifted_bases"]
    
    qber, raw_alice, raw_bob, adv_feat = estimate_qber(
        np.array(alice_sifted), 
        np.array(bob_sifted), 
        np.array(sifted_bases),
        sample_fraction=0.25
    )
    
    # Task 3: Pipeline
    ec_alice, ec_bob = simple_error_correction(raw_alice, raw_bob)
    final_alice = privacy_amplification(ec_alice, qber)
    final_bob = privacy_amplification(ec_bob, qber)
    
    sim_data['final_alice'] = final_alice
    sim_data['final_bob'] = final_bob
    sim_data['adv_feat'] = adv_feat
    sim_data['raw_alice'] = raw_alice
    
    sample_size = int(len(alice_sifted) * 0.25)
    return len(alice_sifted), qber, len(ec_alice), len(final_alice), sample_size, sim_data, adv_feat


@st.cache_data(show_spinner=False)
def draw_cached_circuit(a_bits_tuple, a_bases_tuple, b_bases_tuple, eve_on, num_to_draw):
    import numpy as np
    from qiskit import QuantumCircuit
    from eve import encode_qubits_alice, measure_qubits_bob, eve_intercept
    import matplotlib.pyplot as plt
    import io
    
    a_bits = np.array(a_bits_tuple)
    a_bases = np.array(a_bases_tuple)
    b_bases = np.array(b_bases_tuple)
    
    qc = encode_qubits_alice(a_bits, a_bases)
    if eve_on > 0:
        qc.barrier()
        qc.id(range(num_to_draw))
        qc.barrier()
        # Mock eve_bases and intercepted_indices to ensure determinism
        np.random.seed(42)
        qc, _, _ = eve_intercept(qc, intercept_fraction=1.0)
        qc.barrier()
        qc.id(range(num_to_draw))
        qc.barrier()
    else:
        qc.barrier()
        qc.id(range(num_to_draw))
        qc.barrier()
    qc = measure_qubits_bob(qc, b_bases)
    
    fig = qc.draw('mpl', style="iqx-dark")
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf.getvalue()

def reconstruct_circuit_for_drawing(sim_data, eve_on, num_to_draw):
    a_bits = sim_data["alice_bits"][:num_to_draw]
    a_bases = sim_data["alice_bases"][:num_to_draw]
    qc = encode_qubits_alice(a_bits, a_bases)
    if eve_on > 0:
        qc.barrier()
        qc.id(range(num_to_draw))
        qc.barrier()
        qc, _, _ = eve_intercept(qc, intercept_fraction=1.0)
        qc.barrier()
        qc.id(range(num_to_draw))
        qc.barrier()
    else:
        qc.barrier()
        qc.id(range(num_to_draw))
        qc.barrier()
    b_bases = sim_data["bob_bases"][:num_to_draw]
    qc = measure_qubits_bob(qc, b_bases)
    return qc

# --- Streamlit UI Setup ---
import ui_effects
st.set_page_config(page_title="Q-Link | Quantum Security", layout="wide", initial_sidebar_state="expanded")

# Inject Custom CSS
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

# Sidebar
with st.sidebar:
    st.markdown("""<div style='display: flex; align-items: center; gap: 10px; margin-bottom: 15px;'>
    <svg viewBox="0 0 100 100" width="36" height="36" style="flex-shrink: 0;">
<circle class="nucleus" cx="50" cy="50" r="6" fill="#3B82F6"/>
<g transform="rotate(0 50 50)"><ellipse cx="50" cy="50" rx="40" ry="12" stroke="#3B82F6" stroke-width="3" fill="none" stroke-opacity="0.3"/><circle cx="50" cy="38" r="5" fill="#60A5FA"><animateTransform attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="4s" repeatCount="indefinite" /></circle></g>
<g transform="rotate(60 50 50)"><ellipse cx="50" cy="50" rx="40" ry="12" stroke="#3B82F6" stroke-width="3" fill="none" stroke-opacity="0.3"/><circle cx="50" cy="38" r="5" fill="#60A5FA"><animateTransform attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="4.5s" repeatCount="indefinite" /></circle></g>
<g transform="rotate(120 50 50)"><ellipse cx="50" cy="50" rx="40" ry="12" stroke="#3B82F6" stroke-width="3" fill="none" stroke-opacity="0.3"/><circle cx="50" cy="38" r="5" fill="#60A5FA"><animateTransform attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="5s" repeatCount="indefinite" /></circle></g>
    </svg>
    <h2 style='margin: 0;'>Q<span style='color: #3B82F6; font-family: "Times New Roman", Times, serif !important;'> LINK</span></h2>
</div>""", unsafe_allow_html=True)
    st.caption("Quantum Key Distribution for a Safer Tomorrow")
    st.markdown("<br>", unsafe_allow_html=True)
    
    page = st.radio(
        "Navigation",
        [
            "⌂ Home / Simulation", 
            "▤ Results & Analysis", 
            "⚷ Live Encryption Demo",
            "📈 Link Monitor"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'><span style='background: #3B82F6; color: #FFFFFF; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8em;'>SIMULATOR</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-note' style='margin-top: 12px; text-align: center;'>Note: Classical channel must be authenticated. Real QKD uses photons over fiber; this is a simulation.</div>", unsafe_allow_html=True)
ui_effects.inject_global_styles()

# Empty states for results if not run yet
if "sim_data" not in st.session_state:
    st.session_state.sim_data = None
    st.session_state.sim_status = None
    st.session_state.final_alice_key = []
    st.session_state.final_bob_key = []
    st.session_state.sim_results = {}

# --- PAGE ROUTING ---

if page == "⌂ Home / Simulation":
    ui_effects.render_hero_card()
    
    st.markdown("#### Start QKD Simulation")
    col1, col2, col3 = st.columns(3)
    with col1:
        num_qubits = st.slider("Number of Qubits", min_value=16, max_value=4000, value=1846)
    with col2:
        eve_fraction = st.slider("Eve Intercept Fraction (%)", 0, 100, 0, step=10)
        attack_type = st.selectbox("Eve Attack Type", ["Standard Random", "Basis-Biased (Z-heavy)"])
    with col3:
        noise_level = st.slider("Channel Noise Level (%)", 0.0, 20.0, 0.0, step=0.5)
        st.caption(f"Expected noise-only QBER ~ {noise_level}% | Abort threshold: 11%")
    
    security_method = st.radio("Security Evaluation Method", ["11% Hard Threshold", "Machine Learning Model"], horizontal=True)
    
    if st.button("Run Simulation", type="primary", use_container_width=False):
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
                    reason = f"{reason}\n\n**ML Diagnostics**: {ml_reason}\n**Attack Probability**: {attack_prob*100:.1f}%"
                
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
            
        st.success("Simulation complete! Go to Results & Analysis to view the breakdown.")
        
elif page == "▤ Results & Analysis":
    st.markdown("## Results & Analysis")
    if not st.session_state.sim_data:
        st.info("Run a simulation on the Home page to see results.")
    else:
        res = st.session_state.sim_results
        status = st.session_state.sim_status
        
        ui_effects.render_channel_illustration(eve_on=(res['eve_fraction'] > 0))
        
        # Banner
        if status == "ACCEPTED":
            st.markdown(f"<div class='status-banner status-accepted'>✓ ACCEPTED: {res['reason']}</div>", unsafe_allow_html=True)
        elif status == "INCONCLUSIVE":
            st.markdown(f"<div class='status-banner status-inconclusive'>⚠ INCONCLUSIVE: {res['reason']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='status-banner status-rejected'>✕ REJECTED: {res['reason']}</div>", unsafe_allow_html=True)
            
        # Metric Cards
        cols = st.columns(5)
        cols[0].markdown(f"<div class='glass-card'><h6 style='margin-top:0;'>Sifted Key</h6><h2 class='mono-font' style='margin-bottom:0;'>{res['sifted_len']}</h2></div>", unsafe_allow_html=True)
        cols[1].markdown(f"<div class='glass-card'><h6 style='margin-top:0;'>Estimated QBER</h6><h2 class='mono-font' style='margin-bottom:0;'>{res['qber']*100:.2f}%</h2><small class='text-muted'>Sample: {res['sample_size']} bits</small></div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='glass-card'><h6 style='margin-top:0;'>EC Key (Cascade)</h6><h2 class='mono-font' style='margin-bottom:0;'>{res['ec_len']}</h2></div>", unsafe_allow_html=True)
        
        if status == "ACCEPTED":
            cols[3].markdown(f"<div class='glass-card'><h6 style='margin-top:0;'>Final Secret Key</h6><h2 class='mono-font' style='margin-bottom:0;'>{res['final_key_len']}</h2></div>", unsafe_allow_html=True)
            key_rate = res['final_key_len'] / res['num_qubits'] if res['num_qubits'] > 0 else 0
            final_display_len = res['final_key_len']
        else:
            cols[3].markdown(f"<div class='glass-card'><h6 style='margin-top:0;'>Final Secret Key</h6><h2 class='mono-font' style='margin-bottom:0;'>0</h2><small class='text-muted'>(Discarded {res['final_key_len']} b)</small></div>", unsafe_allow_html=True)
            key_rate = 0
            final_display_len = 0
            
        cols[4].markdown(f"<div class='glass-card'><h6 style='margin-top:0;'>Final Key Rate</h6><h2 class='mono-font' style='margin-bottom:0;'>{key_rate:.2f}</h2><small class='text-muted'>bits/qubit sent</small></div>", unsafe_allow_html=True)
        
        if status != "ACCEPTED":
            st.info(f"The final secret key is 0 bits long because the connection was {status}. Key material was discarded.")
            
        import plotly.graph_objects as go
        
        # Charts Row
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("#### Key Pipeline Funnel")
            fig_funnel = go.Figure(go.Funnel(
                y=["Sifted Key", "Cascade (EC)", "Privacy Amp (Final)"],
                x=[res['sifted_len'], res['ec_len'], final_display_len],
                marker={"color": ["#3B82F6", "#8B5CF6", "#22C55E"]}
            ))
            fig_funnel.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Times New Roman, Times, serif", color="#E8ECF8")
            )
            st.plotly_chart(fig_funnel, use_container_width=True)
            
        with chart_col2:
            st.markdown("#### QBER Threshold Analysis")
            # Since we don't have block-by-block QBER from the backend yet, just show a gauge or bar
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = res['qber']*100,
                title = {'text': "Estimated QBER (%)", 'font': {'color': '#E8ECF8'}},
                gauge = {
                    'axis': {'range': [None, 20], 'tickcolor': '#E8ECF8'},
                    'bar': {'color': "#EF4444" if res['qber'] > 0.11 else "#3B82F6"},
                    'bgcolor': "rgba(255,255,255,0.1)",
                    'borderwidth': 2,
                    'bordercolor': "rgba(120,150,255,0.18)",
                    'steps': [
                        {'range': [0, 11], 'color': 'rgba(34,197,94,0.1)'},
                        {'range': [11, 20], 'color': 'rgba(239,68,68,0.2)'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 11
                    }
                }
            ))
            fig_gauge.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Times New Roman, Times, serif", color="#E8ECF8")
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
            
        st.markdown("---")
        st.markdown("### Quantum Circuit Demo")
        st.caption("Here is a live look at the quantum circuit. **X** encodes a '1'. **H** switches to the diagonal basis. The **I** (identity) gates represent the noisy transmission channel.")
        
        sim_data = st.session_state.sim_data
        num_qubits = res['num_qubits']
        eve_fraction = res['eve_fraction']
        
        num_to_draw = min(num_qubits, 12)
        if num_qubits <= 16:
            num_to_draw = num_qubits
            st.caption(f"Showing the full {num_qubits}-qubit circuit for this run.")
        else:
            st.caption(f"Showing 12 of {num_qubits} qubits. The simulation ran on all {num_qubits} qubits.")
            
        a_bits_tuple = tuple(sim_data["alice_bits"][:num_to_draw].tolist())
        a_bases_tuple = tuple(sim_data["alice_bases"][:num_to_draw].tolist())
        b_bases_tuple = tuple(sim_data["bob_bases"][:num_to_draw].tolist())
        img_bytes = draw_cached_circuit(a_bits_tuple, a_bases_tuple, b_bases_tuple, eve_fraction, num_to_draw)
        
        st.markdown("<div class='glass-card' style='padding: 20px; overflow-x: auto;'>", unsafe_allow_html=True)
        st.image(img_bytes, output_format="PNG")
        st.markdown("</div>", unsafe_allow_html=True)
            
        # Table logic
        a_bits = sim_data["alice_bits"]
        a_bases = sim_data["alice_bases"]
        b_bases = sim_data["bob_bases"]
        b_bits = sim_data["bob_bits"]
        
        df_full = pd.DataFrame({
            "Qubit": range(1, num_qubits + 1),
            "Alice's Bit": a_bits,
            "Alice's Basis": ["Rectilinear (+)" if b == 0 else "Diagonal (x)" for b in a_bases],
            "Bob's Basis": ["Rectilinear (+)" if b == 0 else "Diagonal (x)" for b in b_bases],
            "Bob's Result": b_bits,
            "Match?": ["✓ Yes" if a_bases[i] == b_bases[i] else "✕ No" for i in range(num_qubits)]
        })
        
        st.markdown("#### Qubit Details")
        st.dataframe(df_full.head(num_to_draw), hide_index=True)
        
        with st.expander(f"View all {num_qubits} rows"):
            st.dataframe(df_full, hide_index=True)
            
    st.markdown("---")
    st.markdown("## ML Live Diagnostics")
    if not st.session_state.sim_results:
        st.info("Run a simulation on the Home page to see live diagnostics.")
    else:
        res = st.session_state.sim_results
        st.caption("Real-time analysis of the current simulation run by the trained Machine Learning model.")
    
        if res.get('adv_feat') is not None:
            from qber import evaluate_security_ml
            ml_status, ml_reason, attack_prob = evaluate_security_ml(res['qber'], res['num_qubits'], res['sifted_len'], res['adv_feat'])
        
            ml_col1, ml_col2 = st.columns([1, 2])
            with ml_col1:
                fig_prob = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = attack_prob * 100,
                    number = {'suffix': '%' },
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
                html_str = f"<div class='glass-card' style='height: 100%;'>"
                if ml_status == "REJECTED":
                    html_str += "<h3 style='color: #EF4444; margin-top: 0;'>✕ Attack Detected</h3>"
                else:
                    html_str += "<h3 style='color: #22C55E; margin-top: 0;'>✓ Channel Secure</h3>"
                
                html_str += f"<p style='margin-bottom: 10px;'>{ml_reason}</p>"
                html_str += "<strong>Features given to the model:</strong><ul style='margin-top: 5px;'>"
                html_str += f"<li>QBER Drift (Start vs End): <code>{res['adv_feat']['qber_drift']:.4f}</code></li>"
                html_str += f"<li>Max Burst Error: <code>{res['adv_feat']['max_burst']}</code></li>"
                html_str += f"<li>Z-Basis QBER: <code>{res['adv_feat']['qber_z']:.4f}</code></li>"
                html_str += f"<li>X-Basis QBER: <code>{res['adv_feat']['qber_x']:.4f}</code></li>"
                html_str += "</ul></div>"
                st.markdown(html_str, unsafe_allow_html=True)
        else:
            st.info("No advanced features available for this run.")

        st.markdown("---")
        st.markdown("## Evaluation Charts")
        
        try:
            import pandas as pd
            import plotly.graph_objects as go
            
            test_df = pd.read_csv("results/test_df1.csv")
            
            c1, c2, c3 = st.columns(3)
            
            # Chart 1: Detection vs Intercept
            with c1:
                df_det = test_df[test_df['noise'] == 0].groupby('eve')[['RuleA_reject', 'RuleB_reject']].mean() * 100
                fig1 = go.Figure()
                fig1.add_trace(go.Scatter(x=df_det.index, y=df_det['RuleA_reject'], mode='lines+markers', name='Rule A (11% QBER)', line=dict(color='#60A5FA')))
                fig1.add_trace(go.Scatter(x=df_det.index, y=df_det['RuleB_reject'], mode='lines+markers', name='Rule B (ML)', line=dict(color='#3B82F6')))
                
                # Highlight current simulation if noise == 0
                if res.get('noise_level', 0) == 0:
                    curr_eve = res.get('eve_fraction', 0)
                    fig1.add_vline(x=curr_eve, line_width=2, line_dash="dash", line_color="red", annotation_text="Current", annotation_position="top left", annotation_font_color="red")
                
                fig1.update_layout(title="Detection vs Intercept (0% Noise)", xaxis_title="Intercept Fraction (%)", yaxis_title="Detection Rate (%)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E8ECF8'), margin=dict(l=40, r=20, t=40, b=40), legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99))
                st.caption("Note: Sessions can be rejected by the QBER > 11% rule, or by the final SHA-256 Key Confirmation failing if uncorrected errors remain.\n\n*Why might QBER be lower than 25% at 100% intercept?* Under Intercept-Resend, Eve introduces a 25% error rate on average. In any single session (e.g. ~350 sifted bits from 700 qubits), normal statistical variance means the measured QBER will fluctuate around 25% (e.g., between 20% and 30%).")
            st.plotly_chart(fig1, use_container_width=True)
                
            # Chart 2: False Alarm vs Noise
            with c2:
                df_fa = test_df[test_df['eve'] == 0].groupby('noise')[['RuleA_reject', 'RuleB_reject']].mean() * 100
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=df_fa.index, y=df_fa['RuleA_reject'], mode='lines+markers', name='Rule A', line=dict(color='#60A5FA')))
                fig2.add_trace(go.Scatter(x=df_fa.index, y=df_fa['RuleB_reject'], mode='lines+markers', name='Rule B', line=dict(color='#3B82F6')))
                
                # Highlight current simulation if eve == 0
                if res.get('eve_fraction', 0) == 0:
                    curr_noise = res.get('noise_level', 0)
                    fig2.add_vline(x=curr_noise, line_width=2, line_dash="dash", line_color="red", annotation_text="Current", annotation_position="top left", annotation_font_color="red")
                
                fig2.update_layout(title="False Alarms vs Noise (0% Eve)", xaxis_title="Channel Noise (%)", yaxis_title="False Alarm Rate (%)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E8ECF8'), margin=dict(l=40, r=20, t=40, b=40), legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
                st.plotly_chart(fig2, use_container_width=True)
                
            # Chart 3: Confusion Matrix (Rule A)
            with c3:
                true_labels = (test_df['eve'] > 0).astype(int)
                pred_labels = test_df['RuleA_reject']
                
                tn = ((true_labels == 0) & (pred_labels == 0)).sum()
                fp = ((true_labels == 0) & (pred_labels == 1)).sum()
                fn = ((true_labels == 1) & (pred_labels == 0)).sum()
                tp = ((true_labels == 1) & (pred_labels == 1)).sum()
                
                z = [[tn, fp], [fn, tp]]
                x = ['Accepted', 'Rejected']
                y = ['Honest', 'Attacked']
                
                fig3 = go.Figure(data=go.Heatmap(
                    z=z, x=x, y=y,
                    colorscale='Blues',
                    text=[[str(tn), str(fp)], [str(fn), str(tp)]],
                    texttemplate="%{text}",
                    showscale=False
                ))
                
                # Determine current cell
                curr_true = "Attacked" if res.get('eve_fraction', 0) > 0 else "Honest"
                curr_pred = "Rejected" if res.get('qber', 0) >= 0.11 else "Accepted"
                
                fig3.add_annotation(
                    x=curr_pred, y=curr_true,
                    text="★ Current",
                    showarrow=False,
                    font=dict(color="red", size=14, weight="bold"),
                    yshift=15
                )
                
                fig3.update_layout(title="Confusion Matrix (Rule A)", xaxis_title="Rule A Verdict", yaxis_title="Ground Truth", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E8ECF8'), margin=dict(l=40, r=20, t=40, b=40))
                # Add red border to the current cell
                fig3.add_shape(type="rect", xref="x", yref="y", x0=x.index(curr_pred)-0.5, y0=y.index(curr_true)-0.5, x1=x.index(curr_pred)+0.5, y1=y.index(curr_true)+0.5, line=dict(color="red", width=3))
                
                st.plotly_chart(fig3, use_container_width=True)
                
        except Exception as e:
            st.error(f"Could not load evaluation data for charts: {e}")
elif page == "⚷ Live Encryption Demo":
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
                reason = f"{reason}\n\n**ML Diagnostics**: {ml_reason}\n**Attack Probability**: {attack_prob*100:.1f}%"
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
                reason = f"{reason}\n\n**ML Diagnostics**: {ml_reason}\n**Attack Probability**: {attack_prob*100:.1f}%"
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
    
    svg_html = f"""<div style="width: 100%; display: flex; justify-content: center; margin-bottom: 24px; margin-top: 24px;">
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
</div>"""
    st.markdown(svg_html, unsafe_allow_html=True)

    msg_to_send = st.text_input("Message to encrypt", value="", placeholder="Enter your secret message here...", max_chars=60)
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
            st.error(f"**Encryption Refused.** The key was rejected during simulation.\n\n**Reason:** {active_res['reason']}")
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
            if not msg_to_send:
                st.info("Enter a message above to encrypt it using the quantum key.")
            elif active_res['final_key_len'] < target_key_len:
                st.error(f"**Encryption Refused.** Key is too short ({active_res['final_key_len']} bits) to encrypt a {target_key_len}-bit message.")
                st.markdown("---")
                if st.button("Manually retry with a fresh key", type="secondary"):
                    st.session_state.run_retry = "fresh_key"
                    if 'demo_sim_results' in st.session_state: del st.session_state.demo_sim_results
                    st.rerun()
            else:
                st.success("✅ **SECURE KEY ESTABLISHED**")
                
                # Encrypt
                ciphertext = encrypt_message(msg_to_send, active_res['alice_key'])
                
                # Decrypt
                bob_str = decrypt_message(ciphertext, active_res['bob_key'])
                if active_res.get('eve_fraction', 0) > 0 and len(active_res.get('eve_key', [])) > 0:
                    eve_str = decrypt_message(ciphertext, active_res['eve_key'])
                else:
                    eve_str = ""

                st.markdown("---")
                st.markdown("### How the message is encrypted and decrypted")
                show_keys = st.toggle("Show key bits", value=True, help="Shown for demonstration only; real keys are never displayed")
                
                # Get the first 6 characters
                first_6_chars = msg_to_send[:6]
                msg_bytes_first = first_6_chars.encode('utf-8')
                
                # We need exact bits for these characters
                total_msg_bits = len(msg_bytes) * 8
                
                # Step 1
                st.markdown("#### Step 1: Message to Bits")
                st.write(f"The original message \"{msg_to_send}\" is {len(msg_bytes)} bytes long, which equals **{total_msg_bits} bits**.")
                
                html_table1 = "<table style='width:100%; border-collapse: collapse; text-align: left;' class='mono-font'><tr><th style='border-bottom: 1px solid #333; padding: 5px;'>Character</th><th style='border-bottom: 1px solid #333; padding: 5px;'>UTF-8 Byte (Dec)</th><th style='border-bottom: 1px solid #333; padding: 5px;'>UTF-8 (Hex)</th><th style='border-bottom: 1px solid #333; padding: 5px;'>Binary (8-bit)</th></tr>"
                
                bit_offset = 0
                first_n_bits_len = 0
                for char in first_6_chars:
                    c_bytes = char.encode('utf-8')
                    c_dec = ", ".join([str(b) for b in c_bytes])
                    c_hex = " ".join([f"{b:02X}" for b in c_bytes])
                    c_bin = " ".join([format(b, '08b') for b in c_bytes])
                    html_table1 += f"<tr><td style='border-bottom: 1px solid #333; padding: 5px;'>{char}</td><td style='border-bottom: 1px solid #333; padding: 5px;'>{c_dec}</td><td style='border-bottom: 1px solid #333; padding: 5px;'>{c_hex}</td><td style='border-bottom: 1px solid #333; padding: 5px;'>{c_bin}</td></tr>"
                    first_n_bits_len += len(c_bytes) * 8
                
                html_table1 += "</table>"
                if len(msg_to_send) > 6:
                    st.markdown(html_table1 + f"<div class='mono-font' style='margin-top: 5px; color: #A8B3D1;'>... ({len(msg_to_send)-6} more characters)</div>", unsafe_allow_html=True)
                else:
                    st.markdown(html_table1, unsafe_allow_html=True)
                
                # Extract the bits
                msg_bits_slice = msg_bits[:first_n_bits_len]
                alice_key_slice = "".join(str(b) for b in active_res['alice_key'][:first_n_bits_len])
                bob_key_slice = "".join(str(b) for b in active_res['bob_key'][:first_n_bits_len])
                eve_key_slice = "".join(str(b) if i < len(active_res.get('eve_key', [])) else '0' for i, b in enumerate(active_res.get('eve_key', [])))[:first_n_bits_len]
                
                # Formatting functions
                def format_bits(bstr):
                    return " ".join(bstr[i:i+8] for i in range(0, len(bstr), 8))
                
                # Step 2
                st.markdown("#### Step 2: Key Bits")
                st.write(f"The QKD protocol generated a shared secret key of **{len(active_res['alice_key'])} bits**. We use exactly {total_msg_bits} bits for this message (from bit position 0 to {total_msg_bits-1}). Each key bit is used **only once** (One-Time Pad). There are {len(active_res['alice_key']) - total_msg_bits} key bits remaining.")
                
                if show_keys:
                    st.markdown(f"<div class='mono-font' style='background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px; border-left: 4px solid #60A5FA; color: #60A5FA; word-break: break-all;'>Alice's key bits for first {len(first_6_chars)} chars:<br>{format_bits(alice_key_slice)}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='mono-font' style='background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px; border-left: 4px solid #60A5FA; color: #60A5FA;'>[Key bits hidden]</div>", unsafe_allow_html=True)
                
                # Step 3
                st.markdown("#### Step 3: Encrypt (XOR)")
                st.write("Alice XORs her message bits with her key bits to produce the ciphertext.")
                st.caption("XOR Rule: `0 ⊕ 0 = 0`, `0 ⊕ 1 = 1`, `1 ⊕ 0 = 1`, `1 ⊕ 1 = 0`")
                
                cipher_slice = ciphertext[:first_n_bits_len]
                if show_keys:
                    html_xor = f"<div class='mono-font' style='background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px;'>"
                    html_xor += f"<div style='margin-bottom: 5px;'><span style='display:inline-block; width: 100px;'>Message:</span> {format_bits(msg_bits_slice)}</div>"
                    html_xor += f"<div style='margin-bottom: 5px; color: #60A5FA;'><span style='display:inline-block; width: 100px;'>⊕ Alice Key:</span> {format_bits(alice_key_slice)}</div>"
                    html_xor += f"<div style='border-top: 1px dashed #666; margin: 5px 0;'></div>"
                    html_xor += f"<div style='color: #F59E0B;'><span style='display:inline-block; width: 100px;'>Ciphertext:</span> {format_bits(cipher_slice)}</div>"
                    html_xor += "</div>"
                    st.markdown(html_xor, unsafe_allow_html=True)
                
                with st.expander("Show full ciphertext (Hex)"):
                    cipher_hex = "".join([f"{int(ciphertext[i:i+8], 2):02X}" for i in range(0, len(ciphertext), 8)])
                    st.markdown(f"<div class='mono-font' style='word-break: break-all;'>{cipher_hex}</div>", unsafe_allow_html=True)
                
                # Step 4
                st.markdown("#### Step 4: What travels on the line")
                st.info("This is all Eve can see on the public channel. Without the key, the ciphertext looks completely random.")
                st.markdown(f"<div class='mono-font' style='background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px; border-left: 4px solid #F59E0B; color: #F59E0B; word-break: break-all;'>{format_bits(cipher_slice)} ...</div>", unsafe_allow_html=True)
                
                # Step 5
                st.markdown("#### Step 5: Bob Decrypts")
                st.write("Bob receives the ciphertext and XORs it with **his own** key bits.")
                
                # Determine differing bits
                alice_key_full = "".join(str(b) for b in active_res['alice_key'][:total_msg_bits])
                bob_key_full = "".join(str(b) for b in active_res['bob_key'][:total_msg_bits])
                diff_count = sum(1 for a, b in zip(alice_key_full, bob_key_full) if a != b)
                
                if show_keys:
                    html_bxor = f"<div class='mono-font' style='background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px;'>"
                    html_bxor += f"<div style='margin-bottom: 5px; color: #F59E0B;'><span style='display:inline-block; width: 100px;'>Ciphertext:</span> {format_bits(cipher_slice)}</div>"
                    html_bxor += f"<div style='margin-bottom: 5px; color: #8B5CF6;'><span style='display:inline-block; width: 100px;'>⊕ Bob Key:</span> {format_bits(bob_key_slice)}</div>"
                    html_bxor += f"<div style='border-top: 1px dashed #666; margin: 5px 0;'></div>"
                    bob_recovered_slice = "".join(str(int(c) ^ int(k)) for c, k in zip(cipher_slice, bob_key_slice))
                    html_bxor += f"<div style='color: #22C55E;'><span style='display:inline-block; width: 100px;'>Recovered:</span> {format_bits(bob_recovered_slice)}</div>"
                    html_bxor += "</div>"
                    st.markdown(html_bxor, unsafe_allow_html=True)
                
                if diff_count == 0:
                    st.success(f"**Verification:** Decrypted text perfectly matches the original! (0 out of {total_msg_bits} message bits differed).")
                else:
                    st.error(f"**Verification Failed:** Decrypted text contains errors. {diff_count} out of {total_msg_bits} message bits differed between Alice and Bob.")
                
                st.markdown(f"""<div class='glass-card' style='border-left: 4px solid #8B5CF6; padding: 15px;'>
                    <h4 style='margin-top: 0; color: #8B5CF6;'>Bob (Intended Recipient)</h4>
                    <strong>Decrypted Text:</strong><br><br>
                    <div class='mono-font' style='font-size: 1.2rem; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px;'>{bob_str}</div>
                </div>""", unsafe_allow_html=True)
                
                # Step 6
                st.markdown("#### Step 6: Eve's Attempt")
                if active_res.get('eve_fraction', 0) == 0:
                    st.write("**Eve is not on the line.** If she tried to intercept the public ciphertext without any key, she'd have to make a random guess for every bit.")
                    if show_keys:
                        random_eve_guess = "".join(str(random.randint(0,1)) for _ in range(first_n_bits_len))
                        eve_recov = "".join(str(int(c) ^ int(k)) for c, k in zip(cipher_slice, random_eve_guess))
                        st.markdown(f"<div class='mono-font' style='background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px;'><div style='color: #F59E0B;'>Ciphertext: {format_bits(cipher_slice)}</div><div style='color: #EF4444;'>⊕ Eve Guess: {format_bits(random_eve_guess)}</div><div style='border-top: 1px dashed #666; margin: 5px 0;'></div><div style='color: #EF4444;'>Recovered : {format_bits(eve_recov)}</div></div>", unsafe_allow_html=True)
                        
                    st.markdown(f"""<div class='glass-card' style='border-left: 4px solid #EF4444; padding: 15px;'>
                        <h4 style='margin-top: 0; color: #EF4444;'>Eve (Eavesdropper)</h4>
                        <strong>Decrypted Text:</strong><br><br>
                        <div class='mono-font' style='font-size: 1.2rem; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px; color: #94a3b8;'>[No data intercepted]</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.write(f"Eve intercepted {active_res['eve_fraction']*100:.0f}% of the qubits, but privacy amplification eliminated her knowledge of the final key. The bits she doesn't know are replaced by random guesses.")
                    if show_keys:
                        eve_unknown = "".join("?" if random.random() < 0.8 else str(b) for b in eve_key_slice)
                        eve_recov = "".join(str(int(c) ^ (int(k) if k != '?' else random.randint(0,1))) for c, k in zip(cipher_slice, eve_unknown))
                        st.markdown(f"<div class='mono-font' style='background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px;'><div style='color: #F59E0B;'>Ciphertext: {format_bits(cipher_slice)}</div><div style='color: #EF4444;'>⊕ Eve Key : {format_bits(eve_unknown)}</div><div style='border-top: 1px dashed #666; margin: 5px 0;'></div><div style='color: #EF4444;'>Recovered : {format_bits(eve_recov)}</div></div>", unsafe_allow_html=True)
                        
                    st.markdown(f"""<div class='glass-card' style='border-left: 4px solid #EF4444; padding: 15px;'>
                        <h4 style='margin-top: 0; color: #EF4444;'>Eve (Eavesdropper)</h4>
                        <strong>Decrypted Text:</strong><br><br>
                        <div class='mono-font' style='font-size: 1.2rem; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px; color: #EF4444;'>{eve_str}</div>
                        <div style='margin-top: 10px; font-size: 0.9em; color: #A8B3D1;'>Notice how Eve's text is completely scrambled. The privacy amplification destroyed any partial information she gained.</div>
                    </div>""", unsafe_allow_html=True)
                    
                st.markdown("---")
                st.info("💡 **Why does XOR work?** Applying the same key twice cancels out: `(message ⊕ key) ⊕ key = message`. Without the key, the ciphertext looks completely random.")
                st.warning("⚠️ **Note:** This is a demonstration of using a shared key, not a production messaging system. In a real One-Time Pad, the key must be as long as the message and never reused. The classical channel must also be authenticated.")


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
                    })
                    
                status_text.empty()
                progress_bar.empty()
                    
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
                
            st.markdown(f"""
            <div style='background-color: {alert_color}20; border: 2px solid {alert_color}; border-radius: 8px; padding: 15px; text-align: center; margin: 20px 0;'>
                <h2 style='color: {alert_color}; margin: 0;'>{alert_status}</h2>
                <p style='margin: 5px 0 0 0; color: #E8ECF8;'>{alert_sub}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # KPIs
            qber_rejects = sum(1 for r in res_list if r['reject_reason'] == "QBER > 11%")
            hash_rejects = sum(1 for r in res_list if r['reject_reason'] == "Key confirmation failed")
            
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Transfers Delivered", total_delivered)
            c2.metric("Transfers Blocked", total_blocked)
            c3.metric("Detection Delay", f"{delay} sessions" if isinstance(delay, int) else delay)
            c4.metric("Rejected (QBER | Hash)", f"{qber_rejects} | {hash_rejects}")
            c5.metric("False Alarms (No Eve)", false_alarms)
            
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
            st.caption("Note: Sessions can be rejected by the QBER > 11% rule, or by the final SHA-256 Key Confirmation failing if uncorrected errors remain.\n\n*Why might QBER be lower than 25% at 100% intercept?* Under Intercept-Resend, Eve introduces a 25% error rate on average. In any single session (e.g. ~350 sifted bits from 700 qubits), normal statistical variance means the measured QBER will fluctuate around 25% (e.g., between 20% and 30%).")
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
                
                chip_title = f"Session {r['session']} | QBER: {r['qber']*100:.1f}% | Deliv: {r['delivered']}"
                if r['reject_reason']:
                    chip_title += f" | Rejected: {r['reject_reason']}"
                strip_html += f"<div title='{chip_title}' style='background-color: {bg}; color: {text}; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 4px; font-weight: bold; font-size: 0.8rem; cursor: help;'>{r['session']}</div>"
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
