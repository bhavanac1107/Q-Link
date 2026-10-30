import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# I will find the exact bounds of the Live Encryption Demo page
start_marker = 'elif page == "⚷ Live Encryption Demo":\n'
end_marker = 'def get_charts_code():'

start_idx = code.find(start_marker)
end_idx = len(code) # It's the last page, so it goes to the end of the file or up to some unrelated code

# But let's check what's actually after the demo.
