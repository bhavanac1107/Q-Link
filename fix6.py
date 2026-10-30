import re
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()
code = code.replace('ui_effects.custom_spinner("Preparing qubits, measuring, and sifting...")', 'ui_effects.custom_spinner("Preparing qubits, measuring, and sifting...", animations_on=animations_on)')
code = code.replace('ui_effects.custom_spinner("Running Real-World QKD Pipeline...")', 'ui_effects.custom_spinner("Running Real-World QKD Pipeline...", animations_on=animations_on)')
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
