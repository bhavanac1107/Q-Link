import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_draw_code = '''        qc_demo = reconstruct_circuit_for_drawing(sim_data, eve_fraction, num_to_draw)
        
        st.markdown("<div class='glass-card' style='padding: 20px; overflow-x: auto;'>", unsafe_allow_html=True)
        try:
            fig = qc_demo.draw('mpl', style="iqx-dark")
            st.pyplot(fig, transparent=True)
        except Exception as e:
            st.text(qc_demo.draw('text'))
        st.markdown("</div>", unsafe_allow_html=True)'''

new_draw_code = '''        a_bits_tuple = tuple(sim_data["alice_bits"][:num_to_draw].tolist())
        a_bases_tuple = tuple(sim_data["alice_bases"][:num_to_draw].tolist())
        b_bases_tuple = tuple(sim_data["bob_bases"][:num_to_draw].tolist())
        img_bytes = draw_cached_circuit(a_bits_tuple, a_bases_tuple, b_bases_tuple, eve_fraction, num_to_draw)
        
        st.markdown("<div class='glass-card' style='padding: 20px; overflow-x: auto;'>", unsafe_allow_html=True)
        st.image(img_bytes, output_format="PNG")
        st.markdown("</div>", unsafe_allow_html=True)'''

if old_draw_code in code:
    code = code.replace(old_draw_code, new_draw_code)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Replaced circuit rendering")
else:
    print("Could not find old draw code")
