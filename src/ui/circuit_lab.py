"""Quantum Circuit Lab module for Q-Link.

Provides interactive Qiskit quantum circuit visualization, gate demonstrations,
BB84 state preparation and measurement circuits, Eve intercept-resend attack
simulations, and educational explanations of foundational quantum principles.
"""

from __future__ import annotations

import math
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd
import streamlit as st

# Check Qiskit availability
try:
    import qiskit
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    import qiskit_aer
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


@st.cache_resource
def _get_aer_simulator():
    """Cache and reuse AerSimulator instance across Streamlit reruns to conserve memory."""
    if not QISKIT_AVAILABLE:
        return None
    try:
        from qiskit_aer import AerSimulator
        return AerSimulator()
    except Exception:
        return None


def _format_dirac(state: np.ndarray) -> str:
    """Format a 2-element statevector as a clean Dirac notation string."""
    a0, a1 = state[0], state[1]
    terms = []

    def _fmt_coeff(c: complex, base_ket: str) -> str:
        real = round(float(c.real), 4)
        imag = round(float(c.imag), 4)
        if abs(imag) < 1e-4:
            if abs(real) < 1e-4:
                return ""
            if abs(real - 1.0) < 1e-4:
                return base_ket
            if abs(real - (-1.0)) < 1e-4:
                return f"-{base_ket}"
            if abs(abs(real) - 1.0 / math.sqrt(2)) < 1e-3:
                sign = "-" if real < 0 else ""
                return f"{sign}\\frac{{1}}{{\\sqrt{{2}}}}{base_ket}"
            return f"{real}{base_ket}"
        elif abs(real) < 1e-4:
            sign = "-" if imag < 0 else ""
            if abs(abs(imag) - 1.0) < 1e-4:
                return f"{sign}i{base_ket}"
            return f"{sign}{abs(imag)}i{base_ket}"
        else:
            return f"({real} + {imag}i){base_ket}"

    t0 = _fmt_coeff(a0, "|0\\rangle")
    t1 = _fmt_coeff(a1, "|1\\rangle")

    if t0 and t1:
        sep = " + " if not t1.startswith("-") else " - "
        clean_t1 = t1[1:] if t1.startswith("-") else t1
        return f"{t0}{sep}{clean_t1}"
    elif t0:
        return t0
    elif t1:
        return t1
    return "0"


def _draw_circuit_mpl(qc: QuantumCircuit) -> Optional[plt.Figure]:
    """Draw a Qiskit circuit using matplotlib with dark theme styling.
    Returns None if matplotlib or pylatexenc drawer fails.
    """
    try:
        fig = qc.draw(
            output="mpl",
            style={
                "backgroundcolor": "#0e1117",
                "textcolor": "#ffffff",
                "subtextcolor": "#b0b0b0",
                "linecolor": "#4da6ff",
                "gatetextcolor": "#ffffff",
                "gatefacecolor": "#1f77b4",
                "barrierfacecolor": "#ffaa00",
            },
        )
        fig.patch.set_facecolor("#0e1117")
        return fig
    except BaseException:
        try:
            # Fallback to standard matplotlib drawer
            fig = qc.draw(output="mpl")
            fig.patch.set_facecolor("#0e1117")
            return fig
        except BaseException:
            return None


# =====================================================================
# Main Render Function
# =====================================================================
def render_circuit_lab() -> None:
    """Render the Quantum Circuit Lab interface in the active Streamlit tab."""
    st.header("🔬 Quantum Circuit Lab (Qiskit Module)")
    st.caption(
        "Interactive quantum circuit builder, gate playground, BB84 state preparation, "
        "and physical eavesdropping simulation executed on the **Qiskit AerSimulator**."
    )

    if not QISKIT_AVAILABLE:
        st.error(
            "⚠️ **Qiskit is not currently available.** Please install Qiskit and Qiskit-Aer with:\n\n"
            "```powershell\npip install qiskit qiskit-aer matplotlib\n```"
        )
        return

    # Sub-navigation for the Lab
    lab_tabs = st.tabs([
        "⚛️ Quantum Gates Playground",
        "🔐 BB84 Circuit Builder (Single-Qubit)",
        "📊 Multi-Qubit Qiskit Experiment",
        "📚 Understanding Quantum Concepts",
    ])

    # -----------------------------------------------------------------
    # Sub-Tab 1: Quantum Gates Playground
    # -----------------------------------------------------------------
    with lab_tabs[0]:
        st.subheader("⚛️ Fundamental Quantum Gates Playground")
        st.write(
            "Explore single-qubit unitary quantum logic gates. Observe the circuit representation, "
            "theoretical statevector evolution, and empirical measurement outcome distribution."
        )

        col_g1, col_g2 = st.columns([1, 2])
        with col_g1:
            gate_choice = st.radio(
                "Select Quantum Gate:",
                ["Pauli-X (Bit Flip)", "Hadamard H (Superposition)", "Identity I (No-Op)"],
                index=0,
                key="gate_choice",
            )
            input_state_choice = st.radio(
                "Select Input State:",
                ["|0⟩ (Ground / Computational 0)", "|1⟩ (Excited / Computational 1)"],
                index=0,
                key="input_state",
            )
            shots_gate = st.select_slider(
                "Measurement Shots:",
                options=[100, 500, 1024, 4096],
                value=1024,
                key="gate_shots",
            )

        # Build Qiskit Circuit for chosen gate
        qc_gate = QuantumCircuit(1, 1)
        qc_state_only = QuantumCircuit(1)

        # 1. State preparation
        input_bit = 1 if "1" in input_state_choice else 0
        if input_bit == 1:
            qc_gate.x(0)
            qc_state_only.x(0)
        qc_gate.barrier(label="Input")

        # 2. Gate application
        gate_symbol = "X"
        if "Pauli-X" in gate_choice:
            qc_gate.x(0)
            qc_state_only.x(0)
            gate_symbol = "X"
            matrix_latex = r"X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}"
            explanation_text = (
                "The **Pauli-X** gate performs a **quantum bit-flip**, analogous to the classical NOT gate. "
                "It rotates the state by $\\pi$ radians around the X-axis of the Bloch sphere:\n"
                "- $X|0\\rangle = |1\\rangle$\n"
                "- $X|1\\rangle = |0\\rangle$"
            )
        elif "Hadamard" in gate_choice:
            qc_gate.h(0)
            qc_state_only.h(0)
            gate_symbol = "H"
            matrix_latex = r"H = \frac{1}{\sqrt{2}} \begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}"
            explanation_text = (
                "The **Hadamard (H)** gate maps computational basis states into **equally weighted superpositions**. "
                "It creates coherent quantum parallelism:\n"
                "- $H|0\\rangle = |+\\rangle = \\frac{1}{\\sqrt{2}}(|0\\rangle + |1\\rangle)$\n"
                "- $H|1\\rangle = |-\\rangle = \\frac{1}{\\sqrt{2}}(|0\\rangle - |1\\rangle)$"
            )
        else:
            qc_gate.id(0)
            qc_state_only.id(0)
            gate_symbol = "I"
            matrix_latex = r"I = \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}"
            explanation_text = (
                "The **Identity (I)** gate leaves the quantum state completely unchanged. "
                "It represents an ideal idle quantum operation or noiseless transmission:\n"
                "- $I|\\psi\\rangle = |\\psi\\rangle$"
            )

        qc_gate.barrier(label=f"Apply {gate_symbol}")
        qc_gate.measure(0, 0)

        # Theoretical Statevector
        sv = Statevector.from_instruction(qc_state_only)
        sv_array = sv.data
        dirac_str = _format_dirac(sv_array)

        # Simulation on AerSimulator
        sim = _get_aer_simulator()
        if sim is not None:
            job = sim.run(qc_gate, shots=shots_gate)
            counts = job.result().get_counts()
        else:
            counts = {"0": shots_gate} if input_bit == 0 else {"1": shots_gate}

        with col_g2:
            st.markdown(f"#### 📐 Circuit Diagram: `{gate_choice}`")
            fig_gate = _draw_circuit_mpl(qc_gate)
            if fig_gate is not None:
                st.pyplot(fig_gate, clear_figure=True)
                plt.close("all")
            else:
                st.code(str(qc_gate.draw(output="text")))
                st.caption("Graphical circuit drawing is unavailable; showing ASCII text representation.")

        st.markdown("---")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("#### 🧮 Mathematical Matrix & Transformation")
            st.latex(matrix_latex)
            st.markdown(explanation_text)
            st.markdown(f"**Theoretical Output Statevector:**")
            st.latex(rf"|\psi\rangle = {dirac_str}")

            prob0 = abs(sv_array[0]) ** 2
            prob1 = abs(sv_array[1]) ** 2
            st.write(f"- $P(|0\\rangle) = |\\alpha|^2 = {prob0:.1%}$")
            st.write(f"- $P(|1\\rangle) = |\\beta|^2 = {prob1:.1%}$")

        with col_m2:
            st.markdown(f"#### 📊 Qiskit Aer Measurement Histogram ({shots_gate} shots)")
            cnt0 = counts.get("0", 0)
            cnt1 = counts.get("1", 0)
            hist_df = pd.DataFrame({
                "Outcome": ["|0⟩", "|1⟩"],
                "Counts": [cnt0, cnt1],
                "Probability": [cnt0 / shots_gate, cnt1 / shots_gate],
            })
            st.bar_chart(hist_df.set_index("Outcome")["Counts"], use_container_width=True)
            st.caption(
                f"Observed frequencies: **|0⟩:** {cnt0} ({cnt0/shots_gate:.1%}) | "
                f"**|1⟩:** {cnt1} ({cnt1/shots_gate:.1%})"
            )

    # -----------------------------------------------------------------
    # Sub-Tab 2: BB84 Circuit Builder (Single-Qubit Step-by-Step)
    # -----------------------------------------------------------------
    with lab_tabs[1]:
        st.subheader("🔐 BB84 Quantum Circuit: Step-by-Step State Prep & Measurement")
        st.write(
            "Construct an authentic single-qubit **BB84 prepare-and-measure quantum circuit**. "
            "Select Alice's encoding, choose Bob's measurement basis, and optionally enable Eve's "
            "intercept-resend attack to observe quantum measurement disturbance directly."
        )

        col_b_a, col_b_e, col_b_b = st.columns(3)

        with col_b_a:
            st.markdown("### 👩‍💻 1. Alice (State Prep)")
            alice_bit_in = st.radio("Alice's Raw Bit:", [0, 1], index=0, horizontal=True, key="b84_a_bit")
            alice_basis_in = st.radio(
                "Alice's Basis:",
                ["Z (Rectilinear, {|0⟩, |1⟩})", "X (Diagonal, {|+⟩, |−⟩})"],
                index=0,
                key="b84_a_basis",
            )
            a_basis_code = 0 if "Z" in alice_basis_in else 1

            if a_basis_code == 0:
                prep_desc = "Identity `I` (leaves |0⟩)" if alice_bit_in == 0 else "Pauli-X `X` (flips to |1⟩)"
                state_label = "|0⟩" if alice_bit_in == 0 else "|1⟩"
            else:
                prep_desc = "Hadamard `H` (prepares |+⟩)" if alice_bit_in == 0 else "`X` then `H` (prepares |−⟩)"
                state_label = "|+⟩" if alice_bit_in == 0 else "|−⟩"

            st.info(f"**Target State:** `{state_label}`\n\n**Gate Sequence:** {prep_desc}")

        with col_b_e:
            st.markdown("### 👁️ 2. Eve (Intercept-Resend)")
            eve_active = st.checkbox("Enable Eve Attack", value=False, key="b84_eve_toggle")
            if eve_active:
                eve_basis_in = st.radio(
                    "Eve's Intercept Basis:",
                    ["Random (50% Z / 50% X)", "Z Basis ({|0⟩, |1⟩})", "X Basis ({|+⟩, |−⟩})"],
                    index=0,
                    key="b84_eve_basis",
                )
                if "Random" in eve_basis_in:
                    e_basis_code = int(np.random.choice([0, 1]))
                    st.caption(f"🎲 Random draw selected: **{'Z' if e_basis_code == 0 else 'X'} Basis**")
                else:
                    e_basis_code = 0 if "Z" in eve_basis_in else 1
                st.warning("⚠️ Eve intercepts qubit, measures, and resends her measured state to Bob.")
            else:
                e_basis_code = None
                st.success("🔒 Eve is inactive. Quantum state passes undisturbed through channel.")

        with col_b_b:
            st.markdown("### 👨‍💻 3. Bob (Measurement)")
            bob_basis_in = st.radio(
                "Bob's Measurement Basis:",
                ["Z (Rectilinear, {|0⟩, |1⟩})", "X (Diagonal, {|+⟩, |−⟩})"],
                index=0,
                key="b84_b_basis",
            )
            b_basis_code = 0 if "Z" in bob_basis_in else 1
            if b_basis_code == 0:
                meas_desc = "Direct measurement in computational basis ({|0⟩, |1⟩})."
            else:
                meas_desc = "Apply Hadamard `H` before measurement to rotate diagonal basis to computational basis."
            st.info(f"**Measurement Mode:**\n\n{meas_desc}")

        col_ctrl1, col_ctrl2 = st.columns([1, 3])
        with col_ctrl1:
            shots_bb84 = st.select_slider(
                "Execution Shots:",
                options=[1, 100, 500, 1024, 4096],
                value=1024,
                key="b84_shots",
                help="1 shot simulates a single discrete photon pulse. 1024 shots visualizes quantum probability statistics.",
            )

        # Build Qiskit BB84 Circuit
        if eve_active:
            qc_bb84 = QuantumCircuit(1, 2)
            c_eve = 0
            c_bob = 1
        else:
            qc_bb84 = QuantumCircuit(1, 1)
            c_bob = 0

        # Alice preparation gates
        if alice_bit_in == 1:
            qc_bb84.x(0)
        if a_basis_code == 1:
            qc_bb84.h(0)
        qc_bb84.barrier(label="Alice Prep")

        # Eve attack gates
        if eve_active and e_basis_code is not None:
            if e_basis_code == 1:
                qc_bb84.h(0)
            qc_bb84.measure(0, c_eve)
            if e_basis_code == 1:
                qc_bb84.h(0)
            qc_bb84.barrier(label="Eve Attack")

        # Bob measurement gates
        if b_basis_code == 1:
            qc_bb84.h(0)
        qc_bb84.measure(0, c_bob)

        # Render Circuit Diagram
        st.markdown("#### 📐 Full Qiskit BB84 Circuit Diagram")
        fig_bb84 = _draw_circuit_mpl(qc_bb84)
        if fig_bb84 is not None:
            st.pyplot(fig_bb84, clear_figure=True)
            plt.close("all")
        else:
            st.code(str(qc_bb84.draw(output="text")))
            st.caption("Graphical circuit drawing is unavailable; showing ASCII text representation.")

        # Execute on AerSimulator
        sim = _get_aer_simulator()
        if sim is not None:
            job = sim.run(qc_bb84, shots=shots_bb84)
            result = job.result()
            counts_bb84 = result.get_counts()
        else:
            counts_bb84 = {"0": shots_bb84}

        # Parse counts: in Qiskit bitstring order is c_{n-1}...c_0 (c_bob c_eve or c_bob)
        st.markdown("---")
        st.subheader("⚡ Qiskit Execution & Sifting Analysis")

        bases_match = a_basis_code == b_basis_code
        col_res1, col_res2 = st.columns([1, 1])

        with col_res1:
            st.markdown("##### 🔍 Sifting & Basis Reconciliation")
            if bases_match:
                st.success("✅ **Bases Match!** (Alice: " + ("Z" if a_basis_code == 0 else "X") +
                           ", Bob: " + ("Z" if b_basis_code == 0 else "X") + ") → **Bit is SIFTED (retained).**")
            else:
                st.warning("⚠️ **Bases Mismatch!** (Alice: " + ("Z" if a_basis_code == 0 else "X") +
                           ", Bob: " + ("Z" if b_basis_code == 0 else "X") + ") → **Bit is DISCARDED (inconclusive).**")

            # Extract Bob's measurement distribution
            bob_outcomes: Dict[str, int] = {}
            for bitstr, cnt in counts_bb84.items():
                # If Eve is active, bitstr is "b_bob b_eve" (length 2), else "b_bob"
                bob_bit = bitstr[0] if len(bitstr) == 2 else bitstr
                bob_outcomes[bob_bit] = bob_outcomes.get(bob_bit, 0) + cnt

            cnt_b0 = bob_outcomes.get("0", 0)
            cnt_b1 = bob_outcomes.get("1", 0)

            st.write(f"- **Alice's Input Bit:** `{alice_bit_in}`")
            st.write(f"- **Bob's Observed Bit 0:** {cnt_b0} times ({cnt_b0/shots_bb84:.1%})")
            st.write(f"- **Bob's Observed Bit 1:** {cnt_b1} times ({cnt_b1/shots_bb84:.1%})")

            # QBER and quantum disturbance analysis
            if bases_match:
                if not eve_active:
                    st.info(
                        "🔒 **Ideal Noiseless Channel:** Because Alice and Bob's bases match and no eavesdropper "
                        f"disturbed the qubit, Bob measures bit `{alice_bit_in}` with **100% determinism** (QBER = 0.0%)."
                    )
                else:
                    if e_basis_code == a_basis_code:
                        st.info(
                            "👁️ **Eve measured in matching basis:** Eve's measurement did not disturb the state. "
                            "Bob still obtains Alice's bit."
                        )
                    else:
                        st.error(
                            "🚨 **Quantum Measurement Disturbance:** Eve intercepted in the **conjugate basis**, "
                            "collapsing the state into a superposition relative to Bob's basis. This introduces "
                            "an expected **50% error probability** on Bob's measurement outcome!"
                        )

        with col_res2:
            st.markdown(f"##### 📊 Measurement Histogram ({shots_bb84} shots)")
            hist_bb84_df = pd.DataFrame({
                "Bitstring": list(counts_bb84.keys()),
                "Count": list(counts_bb84.values()),
            })
            st.bar_chart(hist_bb84_df.set_index("Bitstring")["Count"], use_container_width=True)
            if eve_active:
                st.caption("Bitstring legend: `[Bob bit][Eve bit]` (Qiskit MSB convention)")
            else:
                st.caption("Bitstring legend: `[Bob bit]`")

    # -----------------------------------------------------------------
    # Sub-Tab 3: Multi-Qubit Qiskit Batch Experiment
    # -----------------------------------------------------------------
    with lab_tabs[2]:
        st.subheader("📊 Multi-Qubit Qiskit Batch Experiment")
        st.write(
            "Execute an end-to-end BB84 protocol run using the **Qiskit AerSimulator**. "
            "Verify empirical sifting efficiency (~50%) and observe the emergence of the "
            "**~25% theoretical QBER threshold** under a full random-basis intercept-resend attack."
        )

        col_m_ctrl1, col_m_ctrl2, col_m_ctrl3 = st.columns(3)
        with col_m_ctrl1:
            n_batch_qubits = st.slider("Number of Qubits:", 10, 500, 100, step=10, key="batch_n_qubits")
        with col_m_ctrl2:
            batch_eve_rate = st.slider("Eve Intercept Rate:", 0.0, 1.0, 0.0, step=0.05, format="%.2f", key="batch_eve_rate")
        with col_m_ctrl3:
            batch_seed = st.number_input("RNG Seed:", 0, 999999, 42, key="batch_seed")

        if st.button("🚀 Run Qiskit Batch Simulation", key="run_batch_qiskit"):
            rng = np.random.default_rng(int(batch_seed))
            sim = _get_aer_simulator()
            if sim is None:
                st.error("AerSimulator is not available.")
                return

            # Generate random classical bits and bases
            alice_bits = rng.integers(0, 2, size=n_batch_qubits, dtype=np.int8)
            alice_bases = rng.integers(0, 2, size=n_batch_qubits, dtype=np.int8)
            bob_bases = rng.integers(0, 2, size=n_batch_qubits, dtype=np.int8)

            eve_intercept_mask = rng.random(n_batch_qubits) < batch_eve_rate
            eve_bases = np.full(n_batch_qubits, -1, dtype=np.int8)
            eve_results = np.full(n_batch_qubits, -1, dtype=np.int8)
            bob_bits = np.empty(n_batch_qubits, dtype=np.int8)

            # Progress bar for circuit execution
            prog = st.progress(0.0)
            for i in range(n_batch_qubits):
                a_bit = int(alice_bits[i])
                a_basis = int(alice_bases[i])
                b_basis = int(bob_bases[i])
                is_intercepted = bool(eve_intercept_mask[i])

                if is_intercepted:
                    e_basis = int(rng.integers(0, 2))
                    eve_bases[i] = e_basis
                    qc_i = QuantumCircuit(1, 2)
                    c_e, c_b = 0, 1
                else:
                    e_basis = None
                    qc_i = QuantumCircuit(1, 1)
                    c_b = 0

                # Alice prep
                if a_bit == 1:
                    qc_i.x(0)
                if a_basis == 1:
                    qc_i.h(0)

                # Eve attack
                if is_intercepted and e_basis is not None:
                    if e_basis == 1:
                        qc_i.h(0)
                    qc_i.measure(0, c_e)
                    if e_basis == 1:
                        qc_i.h(0)

                # Bob measurement
                if b_basis == 1:
                    qc_i.h(0)
                qc_i.measure(0, c_b)

                # Execute single shot for realistic physical pulse
                job_i = sim.run(qc_i, shots=1)
                result_i = job_i.result().get_counts()
                bitstr_i = list(result_i.keys())[0]

                if is_intercepted:
                    # Qiskit bitstring order: "b_bob b_eve"
                    b_meas = int(bitstr_i[0])
                    e_meas = int(bitstr_i[1])
                    eve_results[i] = e_meas
                else:
                    b_meas = int(bitstr_i)

                bob_bits[i] = b_meas
                prog.progress((i + 1) / n_batch_qubits)
            prog.empty()

            # Sifting: retain where Alice and Bob bases match
            sifted_mask = alice_bases == bob_bases
            sifted_len = int(sifted_mask.sum())

            if sifted_len == 0:
                qber_batch = float("nan")
                final_key_len = 0
            else:
                sample_size = max(1, int(0.10 * sifted_len))
                sifted_idx = np.where(sifted_mask)[0]
                sample_idx = rng.choice(sifted_idx, size=sample_size, replace=False)
                mismatches = alice_bits[sample_idx] != bob_bits[sample_idx]
                qber_batch = float(np.mean(mismatches))
                final_key_len = sifted_len - sample_size

            # Display Batch Metrics
            st.markdown("#### 📈 Batch Simulation Results")
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Qubits Sent", n_batch_qubits)
            col_m2.metric("Sifted Bits", f"{sifted_len} ({sifted_len/n_batch_qubits:.1%})")
            qber_str = f"{qber_batch:.2%}" if not np.isnan(qber_batch) else "N/A"
            col_m3.metric("Estimated QBER", qber_str)
            col_m4.metric("Final Key Length", f"{final_key_len} bits")

            if not np.isnan(qber_batch):
                if qber_batch >= 0.11:
                    st.error(f"⛔ **ABORT:** QBER ({qber_batch:.2%}) exceeds 11% threshold! Eavesdropping detected by Alice and Bob.")
                elif qber_batch > 0.08:
                    st.warning(f"⚠️ **WARNING:** Elevated QBER ({qber_batch:.2%}). Channel noise or eavesdropping detected.")
                else:
                    st.success(f"✅ **NORMAL:** QBER ({qber_batch:.2%}) is within tolerance. Secret key established.")

            if batch_eve_rate == 1.0:
                st.info(
                    "💡 **Empirical Proof of Quantum Theory:** Under a 100% intercept-resend attack, Eve measures in the "
                    "conjugate basis half the time, randomizing Bob's outcomes. Over sufficient trials, the observed QBER "
                    "approaches the theoretical value of **~25.0%**."
                )

            # Table preview of first 15 qubits
            st.markdown("##### First 15 Simulated Qubits:")
            preview_n = min(15, n_batch_qubits)
            preview_data = {
                "Qubit": list(range(preview_n)),
                "Alice Bit": alice_bits[:preview_n],
                "Alice Basis": ["Z" if b == 0 else "X" for b in alice_bases[:preview_n]],
                "Bob Basis": ["Z" if b == 0 else "X" for b in bob_bases[:preview_n]],
                "Bob Measured": bob_bits[:preview_n],
                "Sifted": sifted_mask[:preview_n],
            }
            if batch_eve_rate > 0.0:
                preview_data["Eve Basis"] = ["—" if eb < 0 else ("Z" if eb == 0 else "X") for eb in eve_bases[:preview_n]]
                preview_data["Eve Bit"] = ["—" if er < 0 else str(er) for er in eve_results[:preview_n]]

            st.dataframe(pd.DataFrame(preview_data), use_container_width=True)

    # -----------------------------------------------------------------
    # Sub-Tab 4: Educational Explanation Panel
    # -----------------------------------------------------------------
    with lab_tabs[3]:
        st.subheader("📚 Understanding Quantum Concepts")
        st.write(
            "Foundational principles of quantum information science underpinning quantum key distribution:"
        )

        with st.expander("1. Qubit (Quantum Bit)", expanded=True):
            st.markdown(
                "A **qubit** is the fundamental unit of quantum information. Unlike a classical bit that is "
                "strictly `0` or `1`, a qubit exists in a two-dimensional Hilbert space spanned by the orthonormal "
                "basis vectors $|0\\rangle$ and $|1\\rangle$:\n\n"
                r"$$|\psi\rangle = \alpha|0\rangle + \beta|1\rangle \quad \text{where } \alpha, \beta \in \mathbb{C} \text{ and } |\alpha|^2 + |\beta|^2 = 1$$"
                "\n\nGeometrically, any pure qubit state can be parameterized on the surface of the **Bloch sphere**:\n\n"
                r"$$|\psi\rangle = \cos\left(\frac{\theta}{2}\right)|0\rangle + e^{i\phi}\sin\left(\frac{\theta}{2}\right)|1\rangle$$"
            )

        with st.expander("2. Quantum Superposition", expanded=False):
            st.markdown(
                "**Superposition** is the principle that a quantum system can exist simultaneously in a linear combination "
                "of its basis states until a measurement is performed. The coefficients $\\alpha$ and $\\beta$ are probability amplitudes:\n\n"
                "- $|+\\rangle = \\frac{1}{\\sqrt{2}}(|0\\rangle + |1\\rangle)$\n"
                "- $|-\\rangle = \\frac{1}{\\sqrt{2}}(|0\\rangle - |1\\rangle)$\n\n"
                "Superposition enables quantum key distribution to encode information in non-orthogonal quantum states that "
                "cannot be distinguished with certainty by an eavesdropper."
            )

        with st.expander("3. Quantum Measurement & Wave Function Collapse", expanded=False):
            st.markdown(
                r"According to **Born's Rule**, measuring a state $|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$ "
                "in the computational basis yields outcome $0$ with probability $|\alpha|^2$ and outcome $1$ with probability $|\beta|^2$:\n\n"
                r"$$P(0) = |\langle 0|\psi\rangle|^2 = |\alpha|^2, \quad P(1) = |\langle 1|\psi\rangle|^2 = |\beta|^2$$"
                "\n\nCrucially, quantum measurement is an **irreversible projection**: it collapses the superposition into the measured eigenstate."
            )

        with st.expander("4. Quantum Gates & Unitary Transformations", expanded=False):
            st.markdown(
                "Quantum logic gates are reversible, norm-preserving operations represented by **unitary matrices** ($U^\\dagger U = I$):\n\n"
                r"$$\text{Pauli-X: } X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}, \quad \text{Hadamard: } H = \frac{1}{\sqrt{2}} \begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}, \quad \text{Pauli-Z: } Z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}$$"
                "\n\nIn BB84, Alice applies $X$ and $H$ gates to prepare states in either the computational (Z) or diagonal (X) basis."
            )

        with st.expander("5. Quantum Entanglement & Bell States", expanded=False):
            st.markdown(
                "**Entanglement** is a quantum property where composite quantum systems cannot be factored into product states "
                "of individual subsystems ($|\\Phi\\rangle \\neq |\\psi_A\\rangle \\otimes |\\psi_B\\rangle$). The maximally entangled Bell states are:\n\n"
                r"$$|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}, \quad |\Phi^-\rangle = \frac{|00\rangle - |11\rangle}{\sqrt{2}}, \quad |\Psi^+\rangle = \frac{|01\rangle + |10\rangle}{\sqrt{2}}, \quad |\Psi^-\rangle = \frac{|01\rangle - |10\rangle}{\sqrt{2}}$$"
                "\n\n> **Protocol Clarification:** Basic BB84 is a **prepare-and-measure** scheme using single photons and does *not* require entanglement. "
                "In contrast, the **E91 protocol** directly uses entangled Bell pairs and verifies channel security via violation of the **CHSH Bell inequality** ($S > 2$)."
            )

        with st.expander("6. The No-Cloning Theorem", expanded=False):
            st.markdown(
                "Proven by Wootters and Zurek (1982), the **No-Cloning Theorem** states that it is impossible to create an identical copy "
                "of an arbitrary unknown quantum state using unitary transformations:\n\n"
                r"$$\text{If } U(|\psi\rangle|0\rangle) = |\psi\rangle|\psi\rangle \text{ and } U(|\phi\rangle|0\rangle) = |\phi\rangle|\phi\rangle \implies \langle\psi|\phi\rangle = \langle\psi|\phi\rangle^2 \implies \langle\psi|\phi\rangle \in \{0, 1\}$$"
                "\n\nThis fundamental law of quantum physics guarantees that Eve cannot duplicate transmitted qubits during transit without measuring and disturbing them."
            )

        with st.expander("7. Measurement Disturbance & Eavesdropping Detection", expanded=False):
            st.markdown(
                "Because the rectilinear ($Z$) and diagonal ($X$) measurement operators do not commute:\n\n"
                r"$$[X, Z] = XZ - ZX = -2iY \neq 0$$"
                "\n\nMeasuring in the $X$ basis completely randomizes the $Z$ projection, and vice versa. "
                "When Eve intercepts and measures in an incorrect basis, she irreversibly alters the quantum state. "
                "For a full random intercept-resend attack in BB84, this introduces an unmistakable **25% error rate (QBER)** into the sifted key."
            )

        with st.expander("8. BB84 Protocol Architecture", expanded=False):
            st.markdown(
                "Proposed by Charles Bennett and Gilles Brassard in 1984, BB84 operates in four distinct phases:\n\n"
                "1. **Quantum State Preparation:** Alice chooses bits and bases uniformly at random, preparing $|0\\rangle, |1\\rangle, |+\\rangle, |-\\rangle$.\n"
                "2. **Quantum Channel Transmission:** Qubits are transmitted across a fiber or free-space optical link.\n"
                "3. **Sifting (Basis Reconciliation):** Alice and Bob publicly announce measurement bases over an authenticated classical channel and discard events where bases mismatched (~50% retention).\n"
                "4. **Parameter Estimation & Privacy Amplification:** Alice and Bob compare a random subset of sifted bits to calculate QBER. If $\\text{QBER} < \\text{threshold}$ (typically 11%), error correction and privacy amplification distill a provably secure final key."
            )
