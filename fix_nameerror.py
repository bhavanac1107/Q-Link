with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_ml_section = False
for line in lines:
    if line.startswith('    st.markdown("## ML Live Diagnostics")'):
        in_ml_section = True
        new_lines.append(line)
        new_lines.append('    if not st.session_state.sim_results:\n')
        new_lines.append('        st.info("Run a simulation on the Home page to see live diagnostics.")\n')
        new_lines.append('    else:\n')
        new_lines.append('        res = st.session_state.sim_results\n')
        continue
        
    if in_ml_section:
        if line.startswith('    st.markdown("## ML Model Evaluation'):
            in_ml_section = False
            new_lines.append(line)
        elif line.strip() == '':
            new_lines.append(line)
        else:
            # Indent by 4 spaces
            new_lines.append('    ' + line)
    else:
        new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
