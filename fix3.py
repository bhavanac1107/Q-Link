import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

drawing_func = """
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
"""

code = code.replace('def reconstruct_circuit_for_drawing(sim_data, eve_on, num_to_draw):', drawing_func + '\ndef reconstruct_circuit_for_drawing(sim_data, eve_on, num_to_draw):')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
