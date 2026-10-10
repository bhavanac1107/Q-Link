with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if '"ℹ About"' in line and ',' in line: # Part of a list/tuple
        line = line.replace(', "ℹ About"', '')
        line = line.replace('"ℹ About",', '')
        line = line.replace('"ℹ About"', '')
        new_lines.append(line)
    elif line.strip() == '"ℹ About"':
        continue
    elif line.startswith('elif page == "ℹ About"'):
        skip = True
    elif skip and not line.startswith(' '): # End of block
        if line.strip(): # if not empty
            skip = False
            new_lines.append(line)
    elif not skip:
        new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
