import sys

with open('ui_effects.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('placeholder.markdown(f\"\"\"', 'placeholder.markdown(inspect.cleandoc(f\"\"\")')

with open('ui_effects.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("done")
