import sys

with open('ui_effects.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = "import inspect\n" + code
code = code.replace('st.markdown(f\"\"\"', 'st.markdown(inspect.cleandoc(f\"\"\")')
code = code.replace('st.markdown(\"\"\"', 'st.markdown(inspect.cleandoc(\"\"\")')
code = code.replace('\"\"\", unsafe_allow_html=True)', '\"\"\"), unsafe_allow_html=True)')

with open('ui_effects.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("done")
