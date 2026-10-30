"""Q-Link -- Quantum Key Distribution Simulator (Multi-Backend Dashboard).

Tabs:
  1. Single Protocol     -- run one protocol, view metrics + event log
  2. QBER Analysis       -- charts showing QBER vs. intercept rate
  3. OTP Demo            -- encrypt / decrypt a message with the shared simulation key
  4. Protocol Compare    -- run all protocols side-by-side
  5. Dataset Analysis    -- inspect modeled satellite QKD dataset (Zenodo 10.5281/zenodo.14054879)
"""

from __future__ import annotations

import sys
import os
import hashlib

# Ensure the project root is on sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import numpy as np
import pandas as pd
import streamlit as st

from src.simulation.engine import run_simulation
from src.simulation.backends import (
    is_aer_available,
    is_ibm_hardware_available,
    AVAILABLE_NOISE_MODELS,
    get_ibm_token,
)
from src.core.bb84 import BB84
from src.core.b92 import B92
from src.core.e91 import E91
from src.analysis.otp_demo import run_otp_qkd_demo, bits_to_bytes, bytes_to_bits
from src.data.loader import load_satellite_dataset

# -- Protocol registry ------------------------------------------------
PROTOCOLS = {
    "BB84": BB84,
    "B92": B92,
    "E91": E91,
}

def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

# -- Page config -------------------------------------------------------
st.set_page_config(
    page_title="Q-Link QKD Simulator",
    page_icon="🔐",
    layout="wide",
)

st.title("🔐 Q-Link — Quantum Key Distribution Simulator")

# Initialize replay state if not present
if "replayed_qber" not in st.session_state:
    st.session_state["replayed_qber"] = None
if "replayed_info" not in st.session_state:
    st.session_state["replayed_info"] = None

# -- Sidebar (shared parameters) --------------------------------------
st.sidebar.header("⚙️ Simulation Parameters")

# Backend Selector
backend_options = ["NumPy (default)"]
if is_aer_available():
    backend_options.append("Qiskit Aer simulator")
else:
    backend_options.append("Qiskit Aer simulator (not installed)")

if is_ibm_hardware_available():
    backend_options.append("IBM Quantum hardware")
else:
    backend_options.append("IBM Quantum hardware (token required in .env)")

selected_backend_label = st.sidebar.selectbox("Backend", backend_options)

selected_backend = "numpy"
selected_noise = "none"

if "Aer" in selected_backend_label:
    if not is_aer_available():
        st.sidebar.warning(
            "⚠️ Qiskit Aer is not installed. To use it in Python 3.11, run:\n"
            "`pip install qiskit qiskit-aer`\n"
            "Falling back to NumPy backend."
        )
        selected_backend = "numpy"
    else:
        selected_backend = "aer"
        noise_keys = list(AVAILABLE_NOISE_MODELS.keys())
        noise_labels = [AVAILABLE_NOISE_MODELS[k] for k in noise_keys]
        noise_idx = st.sidebar.selectbox(
            "Noise Model",
            range(len(noise_keys)),
            format_func=lambda i: noise_labels[i],
        )
        selected_noise = noise_keys[noise_idx]
        if selected_noise != "none":
            st.sidebar.info(f"Noise source: **{AVAILABLE_NOISE_MODELS[selected_noise]}**")

elif "hardware" in selected_backend_label.lower():
    if not is_ibm_hardware_available():
        st.sidebar.warning(
            "⚠️ IBM Quantum hardware requires a configured API token.\n"
            "Add `QISKIT_IBM_TOKEN=your_token` to your `.env` file to enable real hardware.\n"
            "Falling back to NumPy backend."
        )
        selected_backend = "numpy"
    else:
        selected_backend = "hardware"
        st.sidebar.warning(
            "⚠️ **IBM Quantum Open Plan (Job mode)**\n"
            "- Runs on real cloud superconducting systems; jobs queue with other users.\n"
            "- Queue times range from minutes to hours.\n"
            "- Sessions are disabled. Qubits capped to 50."
        )

# If user replayed a record from dataset, show notice and button to clear
if st.session_state["replayed_qber"] is not None:
    st.sidebar.info(
        f"🔁 **Replay Active** ({st.session_state['replayed_info']}):\n"
        f"Channel Error set from dataset QBER: `{st.session_state['replayed_qber']:.3%}`\n"
        f"*(values from dataset, modeled)*"
    )
    if st.sidebar.button("Reset to manual parameters"):
        st.session_state["replayed_qber"] = None
        st.session_state["replayed_info"] = None
        safe_rerun()

selected_proto = st.sidebar.selectbox("Protocol", list(PROTOCOLS.keys()))

max_qubit_limit = 50 if selected_backend == "hardware" else 1500
default_qubits = min(400, max_qubit_limit)
num_qubits = st.sidebar.slider("Number of qubits", 10, max_qubit_limit, default_qubits)

default_err = float(st.session_state["replayed_qber"]) if st.session_state["replayed_qber"] is not None else 0.00
error_rate = st.sidebar.slider("Channel error rate", 0.00, 0.25, min(0.25, default_err), 0.01)
intercept_rate = st.sidebar.slider("Eve intercept rate", 0.00, 0.50, 0.00, 0.01)
eve_active = intercept_rate > 0.0
qber_threshold = st.sidebar.slider("QBER abort threshold", 0.01, 0.25, 0.11, 0.01)
seed = st.sidebar.number_input("Random seed", value=42, step=1)

st.sidebar.markdown("---")
st.sidebar.caption(
    "All tabs share this active simulation. Adjusting parameters updates the single session run automatically."
)


# -- Simulation Runner & Shared State ---------------------------------
def get_simulation_hash(proto_name, n, err, eve, threshold, s, backend_name, noise_name):
    param_str = f"{proto_name}_{n}_{err:.4f}_{eve:.4f}_{threshold:.4f}_{s}_{backend_name}_{noise_name}"
    return hashlib.sha256(param_str.encode("utf-8")).hexdigest()


def run_protocol_instance(proto_name, n, err, eve, threshold, s, backend_name="numpy", noise_name="none"):
    rng = np.random.default_rng(int(s))
    proto_cls = PROTOCOLS[proto_name]
    proto = proto_cls(
        n_qubits=n,
        rng=rng,
        channel_error=err,
        intercept_rate=eve,
        qber_threshold=threshold,
    )
    try:
        return run_simulation(
            proto,
            backend_name=backend_name,
            noise_model_name=noise_name,
        )
    except Exception as e:
        st.error(f"Execution error on backend {backend_name}: {e}")
        # Fall back cleanly to NumPy on error
        return run_simulation(proto, backend_name="numpy")


# Cache active simulation into st.session_state keyed by hash
current_hash = get_simulation_hash(
    selected_proto, num_qubits, error_rate, intercept_rate, qber_threshold, int(seed),
    selected_backend, selected_noise,
)

if "active_sim_hash" not in st.session_state or st.session_state.get("active_sim_hash") != current_hash:
    st.session_state["active_sim_result"] = run_protocol_instance(
        selected_proto, num_qubits, error_rate, intercept_rate, qber_threshold, int(seed),
        selected_backend, selected_noise,
    )
    st.session_state["active_sim_hash"] = current_hash

# Read the shared simulation result
shared_result = st.session_state["active_sim_result"]


def _eve_column(arr, label):
    """Convert an eve array to display strings: -1 -> '—'."""
    if arr is None:
        return []
    is_basis = "basis" in label.lower()
    out = []
    for v in arr:
        if v == -1:
            out.append("—")
        elif is_basis:
            out.append("Z" if v == 0 else "X")
        else:
            out.append(str(v))
    return out


# -- Tabs --------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧪 Single Protocol",
    "📈 QBER Analysis",
    "🔑 OTP Demo",
    "⚖️ Protocol Comparison",
    "🛰️ Dataset Analysis",
])

# =====================================================================
# TAB 1 -- Single Protocol Run
# =====================================================================
with tab1:
    res = shared_result
    st.subheader(f"Simulation Status: {selected_proto}")

    # Backend & Data Source info header
    col_b1, col_b2, col_b3 = st.columns(3)
    backend_display = res.extra.get("backend", "NumPy")
    data_source_display = res.extra.get("data_source", "simulated")
    col_b1.write(f"🖥️ **Backend:** `{backend_display}`")
    col_b2.write(f"🏷️ **Data Source:** `{data_source_display}`")

    if res.extra.get("device_label"):
        col_b3.info(f"📡 {res.extra.get('device_label')}")
    elif res.extra.get("noise_source") and res.extra.get("noise_source") != "none":
        col_b3.write(f"⚡ **Noise Source:** `{res.extra.get('noise_source')}`")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Protocol", selected_proto)
    col2.metric("QBER", f"{res.qber:.3%}")
    col3.metric("Final Key Length", f"{res.final_key_len} bits")
    col4.metric("Alert Level", res.alert_level)

    if res.alert_level == "ABORT":
        st.error(f"⛔ ABORT — QBER ({res.qber:.2%}) exceeds abort threshold ({qber_threshold:.2%})! Key discarded.")
    elif res.alert_level == "WARNING":
        st.warning(f"⚠️ WARNING — Elevated QBER ({res.qber:.2%}). Channel noise or eavesdropping detected.")
    else:
        st.success(f"✅ NORMAL — QBER ({res.qber:.2%}) is within safe boundary. Channel secure.")

    eve_active = intercept_rate > 0.0
    if eve_active:
        st.info(f"👁️ Eve is **active** ({intercept_rate:.0%} intercept rate). Non-intercepted qubits show **—**.")
    else:
        st.info("🔒 Eve is **inactive** (0% intercept rate).")

    st.subheader("Per-Qubit Event Log")
    log_data = {
        "alice_bit": res.alice_bits,
        "alice_basis": np.where(res.alice_bases == 0, "Z", "X"),
        "bob_basis": np.where(res.bob_bases == 0, "Z", "X"),
        "bob_bit": res.bob_bits,
        "sifted": res.sifted_mask,
        "sampled": res.sampled_mask,
    }

    if eve_active and res.eve_bases is not None:
        log_data["eve_basis"] = _eve_column(res.eve_bases, "eve_basis")
        log_data["eve_result"] = _eve_column(res.eve_results, "eve_result")

    df = pd.DataFrame(log_data)
    page_size = 25
    total_pages = max(1, (len(df) + page_size - 1) // page_size)
    page = st.number_input("Page", 1, total_pages, 1, key="log_page")
    start = (page - 1) * page_size
    st.dataframe(df.iloc[start : start + page_size], use_container_width=True)
    st.caption(f"Showing rows {start}–{min(start + page_size, len(df))} of {len(df)}")


# =====================================================================
# TAB 2 -- QBER Analysis Charts
# =====================================================================
with tab2:
    st.subheader("QBER vs. Eve Intercept Rate")
    st.caption(
        f"Sweeps intercept rate from 0% to 50% using backend `{selected_backend}` with seed `{seed}`."
    )
    if st.button("📊 Run Analysis Sweep", key="gen_chart"):
        sweep_rates = np.linspace(0.0, 0.50, 16)
        chart_rows = []
        prog = st.progress(0)
        for i, eve_r in enumerate(sweep_rates):
            for pname in PROTOCOLS:
                r_sim = run_protocol_instance(
                    pname, num_qubits, error_rate, float(eve_r), qber_threshold, int(seed),
                    backend_name=selected_backend, noise_name=selected_noise,
                )
                chart_rows.append({
                    "intercept_rate": eve_r,
                    "protocol": pname,
                    "QBER": r_sim.qber,
                    "key_len": r_sim.final_key_len,
                })
            prog.progress((i + 1) / len(sweep_rates))
        prog.empty()

        chart_df = pd.DataFrame(chart_rows)

        st.line_chart(
            chart_df.pivot(index="intercept_rate", columns="protocol", values="QBER"),
            use_container_width=True,
        )

        st.subheader("Final Usable Key Length vs. Intercept Rate")
        st.line_chart(
            chart_df.pivot(index="intercept_rate", columns="protocol", values="key_len"),
            use_container_width=True,
        )
        st.info(f"Current Abort Threshold: **{qber_threshold:.1%}** | Backend: `{selected_backend}`")
    else:
        st.info("Click **📊 Run Analysis Sweep** to generate the charts.")


# =====================================================================
# TAB 3 -- One-Time Pad Demo
# =====================================================================
with tab3:
    st.subheader("🔑 One-Time Pad Demonstration")
    st.caption(
        f"Demonstrates encryption with Alice's key and decryption with Bob's key from the shared simulation "
        f"[Backend: `{shared_result.extra.get('backend', 'NumPy')}` | Data Source: `{shared_result.extra.get('data_source', 'simulated')}`]."
    )

    res = shared_result

    force_demo = False
    if res.alert_level == "ABORT":
        st.error(
            f"⛔ ABORT — QBER is {res.qber:.2%} (Threshold: {qber_threshold:.2%}). "
            "Key discarded, no encryption possible!"
        )
        force_demo = st.checkbox("🔓 Simulate compromised transmission anyway (observe key errors & Eve's view)", value=False)
    elif res.alert_level == "WARNING":
        st.warning(
            f"⚠️ WARNING — QBER is {res.qber:.2%} (Elevated). Key may contain errors or be partially intercepted!"
        )
    else:
        st.success(
            f"✅ NORMAL — QBER is {res.qber:.2%}. Key exchange safe."
        )

    usable_mask = res.sifted_mask & (~res.sampled_mask)
    alice_final_bits = res.alice_bits[usable_mask]
    bob_final_bits = res.bob_bits[usable_mask]
    eve_final_bits = res.eve_results[usable_mask] if res.eve_results is not None else None

    total_key_bits = len(alice_final_bits)
    st.write(f"**Available QKD Key Length:** `{total_key_bits}` bits ({total_key_bits // 8} bytes)")

    otp_message = st.text_input("Message to Encrypt", value="Quantum secure transmission!")
    msg_bytes_len = len(otp_message.encode("utf-8"))
    msg_bits_len = msg_bytes_len * 8

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Message Bits Needed", f"{msg_bits_len} bits ({msg_bytes_len} bytes)")
    col_m2.metric("Key Bits Available", f"{total_key_bits} bits")

    if total_key_bits < msg_bits_len and total_key_bits > 0:
        st.warning(
            f"⚠️ Message requires {msg_bits_len} bits, but key only has {total_key_bits} bits. "
            f"Only the first {total_key_bits // 8} characters will be encrypted; remainder stays in plaintext."
        )

    use_custom = st.checkbox("Use custom key (not from simulation)")
    custom_key_str = ""
    if use_custom:
        # Default 256-bit repeating sequence so it covers full text messages
        default_custom = "10110010110100111001011001011010" * 8
        custom_key_str = st.text_input("Enter custom binary or text key:", value=default_custom)

    is_aborted = (res.alert_level == "ABORT" and not use_custom and not force_demo)
    button_disabled = is_aborted or (total_key_bits == 0 and not use_custom)

    if st.button("🔒 Encrypt & Decrypt", disabled=button_disabled, key="otp_exec"):
        if use_custom:
            c_bits = [1 if ch == "1" else 0 for ch in custom_key_str if ch in ("0", "1")]
            if not c_bits:
                c_bits = bytes_to_bits(custom_key_str.encode("utf-8"))
            a_key = c_bits
            b_key = c_bits
            if eve_active:
                # Simulate Eve intercept-resend on custom key
                rng_eve = np.random.default_rng(int(seed) + 999)
                e_key = []
                for b in a_key:
                    if rng_eve.random() < intercept_rate:
                        # 75% accuracy under intercept-resend
                        eb = b if rng_eve.random() < 0.75 else (1 - b)
                        e_key.append(eb)
                    else:
                        e_key.append(-1)
            else:
                e_key = None
        else:
            a_key = alice_final_bits
            b_key = bob_final_bits
            e_key = eve_final_bits

        demo_res = run_otp_qkd_demo(otp_message, a_key, b_key, e_key)

        st.markdown("---")
        st.subheader("Encryption & Decryption Results")

        col_enc1, col_enc2 = st.columns(2)
        with col_enc1:
            st.markdown("#### 👩 Alice's Encryption")
            st.write("**Plaintext:**")
            st.code(demo_res["original_full"])
            st.write("**Ciphertext (Hex):**")
            st.code(demo_res["ciphertext_hex"] if demo_res["ciphertext_hex"] else "[Empty]")

        with col_enc2:
            st.markdown("#### 👨 Bob's Decryption")
            st.write("**Bob's Decrypted Text:**")
            st.code(demo_res["bob_decrypted_full"])

            if demo_res["bob_bit_mismatches_count"] > 0:
                st.error(
                    f"❌ **Key Mismatch Detected!** Bob's key has {demo_res['bob_bit_mismatches_count']} bit errors."
                )
                if demo_res["bob_char_diffs"]:
                    st.write("**Character Differences:**")
                    diff_df = pd.DataFrame(demo_res["bob_char_diffs"])
                    st.dataframe(diff_df, hide_index=True)
            else:
                st.success("✅ **Perfect Decryption!** Bob's key matched Alice's key completely.")

        st.markdown("---")
        st.subheader("👁️ Eve's View")
        if eve_active and e_key is not None:
            col_eve1, col_eve2 = st.columns(2)
            with col_eve1:
                st.write("**Intercepted Ciphertext:**")
                st.code(demo_res["ciphertext_hex"] if demo_res["ciphertext_hex"] else "[Empty]")
                st.write(
                    f"**Intercepted Key Bits Known:** {demo_res['eve_bits_known']} / {demo_res['covered_bits']} bits "
                    f"({(demo_res['eve_bits_known'] / max(1, demo_res['covered_bits'])):.1%})"
                )
            with col_eve2:
                st.write("**Eve's Decryption Attempt:**")
                st.code(demo_res["eve_decrypted_full"] if demo_res["eve_decrypted_full"] else "[No data]")
                st.caption(
                    "Eve decodes using the bits she intercepted. When her bases match, she recovers characters; "
                    "when bases mismatch or unintercepted, characters appear corrupted."
                )
        elif eve_active and (e_key is None or len(e_key) == 0):
            st.warning(f"Eve is active ({intercept_rate:.0%} intercept rate), but did not intercept any bits on the usable key slice.")
        else:
            st.info("🔒 Eve is inactive (0% intercept rate). No eavesdropping occurred.")


# =====================================================================
# TAB 4 -- Protocol Comparison
# =====================================================================
with tab4:
    st.subheader("⚖️ Head-to-Head Protocol Comparison")
    st.caption(f"Executes all protocols using current sidebar settings and backend `{selected_backend}`.")

    if st.button("🏁 Run Comparison", key="compare"):
        rows = []
        for pname in PROTOCOLS:
            r = run_protocol_instance(
                pname, num_qubits, error_rate, intercept_rate, qber_threshold, int(seed),
                backend_name=selected_backend, noise_name=selected_noise,
            )
            rows.append({
                "Protocol": pname,
                "Backend": r.extra.get("backend", "NumPy"),
                "Qubits Sent": r.n_qubits,
                "Sifted Bits": int(r.sifted_mask.sum()),
                "QBER": f"{r.qber:.3%}",
                "Final Key Len": r.final_key_len,
                "Alert Level": r.alert_level,
                "Data Source": r.extra.get("data_source", "simulated"),
            })
        comp_df = pd.DataFrame(rows)
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

        st.subheader("Final Key Length by Protocol")
        bar_df = pd.DataFrame({r["Protocol"]: [r["Final Key Len"]] for r in rows})
        st.bar_chart(bar_df)
    else:
        st.info("Click **🏁 Run Comparison** to evaluate all protocols.")


# =====================================================================
# TAB 5 -- Dataset Analysis
# =====================================================================
with tab5:
    st.subheader("🛰️ Satellite QKD Dataset Analysis")
    st.info(
        "📌 **Dataset Metadata & Citation:**\n"
        "- **Data Source:** `modeled` (Computational orbit, atmospheric channel, and QKD simulation — not experimentally measured).\n"
        "- **DOI:** [10.5281/zenodo.14054879](https://doi.org/10.5281/zenodo.14054879) | **License:** CC BY 4.0\n"
        "- **Protocols:** Decoy-BB84 (`DV_Protocol`) & BBM92 (`ENT_protocol`)."
    )

    @st.cache_data
    def get_loaded_dataset():
        return load_satellite_dataset(subsample_factor=2)

    with st.spinner("Loading local satellite dataset..."):
        full_ds = get_loaded_dataset()

    if full_ds.empty:
        st.error("No dataset records could be loaded from C:\\Projects\\QLink\\data\\raw\\satellite.")
    else:
        st.markdown("#### 🔍 Filter Dataset")
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)

        avail_protos = list(full_ds["protocol"].unique())
        sel_proto_filter = f_col1.multiselect("Protocol", avail_protos, default=avail_protos)

        avail_links = list(full_ds["link_type"].unique())
        sel_link_filter = f_col2.multiselect("Link Type", avail_links, default=avail_links)

        min_elev = float(full_ds["elevation_deg"].dropna().min() or 0.0)
        max_elev = float(full_ds["elevation_deg"].dropna().max() or 90.0)
        elev_range = f_col3.slider("Elevation (deg)", min_elev, max_elev, (min_elev, max_elev), 1.0)

        min_qber = float(full_ds["qber"].min())
        max_qber = float(full_ds["qber"].max())
        qber_filter_range = f_col4.slider("QBER Range", 0.0, 0.50, (0.0, 0.50), 0.01)

        mask = (
            full_ds["protocol"].isin(sel_proto_filter)
            & full_ds["link_type"].isin(sel_link_filter)
            & (full_ds["qber"] >= qber_filter_range[0])
            & (full_ds["qber"] <= qber_filter_range[1])
        )
        if "elevation_deg" in full_ds.columns:
            mask = mask & (
                full_ds["elevation_deg"].isna()
                | (
                    (full_ds["elevation_deg"] >= elev_range[0])
                    & (full_ds["elevation_deg"] <= elev_range[1])
                )
            )

        filtered_ds = full_ds[mask].reset_index(drop=True)
        st.caption(f"Showing **{len(filtered_ds):,}** of **{len(full_ds):,}** total modeled records.")

        st.dataframe(
            filtered_ds[[
                "session_id", "protocol", "link_type", "distance_km",
                "link_loss_db", "qber", "key_rate", "outcome", "data_source"
            ]].head(100),
            use_container_width=True,
        )
        st.caption("Displaying up to first 100 filtered rows. Note: `distance_km` is omitted (null) for orbital geometries.")

        st.markdown("---")

        st.markdown("#### 📊 Modeled Relationship Charts")
        c_chart1, c_chart2 = st.columns(2)

        chart_sample = filtered_ds.dropna(subset=["link_loss_db", "qber"]).sample(
            min(500, len(filtered_ds)), random_state=42
        ) if len(filtered_ds) > 0 else filtered_ds

        with c_chart1:
            st.markdown("**QBER vs. Link Loss (dB)** [Source: `modeled`]")
            if not chart_sample.empty:
                st.scatter_chart(
                    chart_sample,
                    x="link_loss_db",
                    y="qber",
                    color="protocol",
                    use_container_width=True,
                )
            else:
                st.info("No data in current filter.")

        with c_chart2:
            st.markdown("**Secret Key Rate (bps) vs. Link Loss (dB)** [Source: `modeled`]")
            if not chart_sample.empty:
                st.scatter_chart(
                    chart_sample,
                    x="link_loss_db",
                    y="key_rate",
                    color="protocol",
                    use_container_width=True,
                )
            else:
                st.info("No data in current filter.")

        st.markdown("---")

        st.markdown("#### 📋 Summary Statistics per Protocol")
        summary_rows = []
        for p_name, group in filtered_ds.groupby("protocol"):
            q_mean = group["qber"].mean()
            q_median = group["qber"].median()
            skr_mean = group["key_rate"].mean()
            exceed_abort = (group["qber"] >= qber_threshold).mean() * 100.0

            summary_rows.append({
                "Protocol": p_name,
                "Mean QBER": f"{q_mean:.3%}",
                "Median QBER": f"{q_median:.3%}",
                "Mean Key Rate (bps)": f"{skr_mean:,.2f}",
                f"% Exceeding Abort Threshold ({qber_threshold:.1%})": f"{exceed_abort:.1f}%",
                "Data Source": "modeled",
            })

        if summary_rows:
            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
            st.caption("Citation: Zenodo 10.5281/zenodo.14054879 (CC BY 4.0) | Data Source: modeled")

        st.markdown("---")

        st.markdown("#### 🔬 Compare with My Simulation")
        cur_sim = shared_result
        sim_qber = cur_sim.qber

        ds_qber_mean = filtered_ds["qber"].mean()
        ds_qber_min = filtered_ds["qber"].min()
        ds_qber_max = filtered_ds["qber"].max()

        comp_col1, comp_col2 = st.columns(2)
        with comp_col1:
            st.metric("My Simulation QBER", f"{sim_qber:.3%}")
            st.metric("Dataset Mean QBER", f"{ds_qber_mean:.3%}" if pd.notna(ds_qber_mean) else "N/A")
            st.caption(f"Dataset Range: [{ds_qber_min:.3%} - {ds_qber_max:.3%}]")

        with comp_col2:
            st.markdown(
                "**Why Simulation & Dataset Values Differ:**\n"
                "- **No Eavesdropping in Dataset:** The satellite dataset models purely physical environmental noise "
                "(atmospheric turbulence, solar/lunar background photons, detector dark counts, and beam diffraction). "
                "It does **not** include an active Eve intercept-resend attack.\n"
                "- **Idealized Simulation Channel:** Your active simulation models discrete quantum gate operations "
                "with an adjustable Eve intercept rate and uniform bit error rate, rather than orbital link geometry."
            )

        st.markdown("---")

        st.markdown("#### 🔁 Replay a Record into Simulation")
        st.caption("Select any modeled row from the dataset to load its QBER directly as channel error into your simulation.")

        if not filtered_ds.empty:
            sel_idx = st.selectbox(
                "Select Record to Replay:",
                range(min(50, len(filtered_ds))),
                format_func=lambda i: f"{filtered_ds.iloc[i]['session_id']} | Loss: {filtered_ds.iloc[i]['link_loss_db']} dB | QBER: {filtered_ds.iloc[i]['qber']:.3%} | SKR: {filtered_ds.iloc[i]['key_rate']} bps",
            )
            selected_row = filtered_ds.iloc[sel_idx]

            if st.button("🚀 Replay Selected Record into Simulation"):
                st.session_state["replayed_qber"] = float(selected_row["qber"])
                st.session_state["replayed_info"] = f"{selected_row['session_id']} ({selected_row['link_type']})"
                st.success(
                    f"Loaded record `{selected_row['session_id']}`! "
                    f"Channel error set to `{selected_row['qber']:.3%}`. *(values from dataset, modeled)*"
                )
                safe_rerun()
