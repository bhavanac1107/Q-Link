import sys
import re
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()
start_str = '        st.markdown("## Evaluation Charts")'
end_str = 'elif page == "⚷ Live Encryption Demo":'
match = re.search(re.escape(start_str) + '.*?(?=' + re.escape(end_str) + ')', code, re.DOTALL)
if match:
    with open('charts_code.txt', 'w', encoding='utf-8') as out:
        out.write(match.group(0))
