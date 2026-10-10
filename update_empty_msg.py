with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

target = '''        else:
            if active_res['final_key_len'] < target_key_len:'''

replacement = '''        else:
            if not msg_to_send:
                st.info("Enter a message above to encrypt it using the quantum key.")
            elif active_res['final_key_len'] < target_key_len:'''

code = code.replace(target, replacement)
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
