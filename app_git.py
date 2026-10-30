"""
Phase 4: Streamlit Dashboard (First Prototype)
A minimal single-page app with Number of Qubits, Eve ON/OFF, Start button,
QBER calculation, and Accept/Reject result.
"""

import streamlit as st
import numpy as np

# Import our QKD components
from bb84 import generate_random_bits, generate_random_bases
from eve import simulate_qkd_protocol, estimate_qber
from qber import evaluate_security

def run_simulation(num_qubits, eve_on):
    """Runs the BB84 simulation and returns results."""
    attack_strength = 1.0 if eve_on else 0.0
    alice_sifted, bob_sifted = simulate_qkd_protocol(num_qubits, attack_strength)
    
    qber, final_alice, final_bob = estimate_qber(
        np.array(alice_sifted), 
        np.array(bob_sifted), 
        sample_fraction=0.25
    )
    
    sample_size = int(len(alice_sifted) * 0.25)
    return len(alice_sifted), qber, len(final_alice), sample_size

# --- Streamlit UI ---
st.set_page_config(page_title="Q-Link Prototype", layout="centered")

st.title("Q-Link")
st.subheader("Quantum Key Distribution with Attack Detection")

st.markdown("---")

# Inputs
col1, col2 = st.columns(2)
with col1:
    num_qubits = st.slider("Number of Qubits", min_value=16, max_value=2000, value=100)
with col2:
    eve_on = st.toggle("Eve Attack (Eavesdropper)", value=False)

if st.button("Start QKD Simulation"):
    with st.spinner("Running Quantum Simulation on AerSimulator..."):
        sifted_len, qber, final_key_len, sample_size = run_simulation(num_qubits, eve_on)
        
        if sample_size < 30:
            status = "INCONCLUSIVE"
            reason = "sample too small, increase the qubit count"
        else:
            status, reason = evaluate_security(qber)
            
        if status in ["REJECTED", "INCONCLUSIVE"]:
            final_key_len = 0  # Discard key
            
        st.markdown("### Results (SIMULATOR)")
        
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("Sifted Key Length", f"{sifted_len} bits")
        col_res2.metric("Estimated QBER", f"{qber*100:.1f}% (sample: {sample_size})")
        col_res3.metric("Final Secret Key", f"{final_key_len} bits")
        
        if status == "ACCEPTED":
            st.success(f"**Security Status: {status}**\n\n{reason}")
        elif status == "INCONCLUSIVE":
            st.warning(f"**Security Status: {status}**\n\n{reason}")
        else:
            st.error(f"**Security Status: {status}**\n\n{reason}")
            
    st.info("Note: The exact QBER may vary significantly on small qubit counts due to statistical randomness.")
