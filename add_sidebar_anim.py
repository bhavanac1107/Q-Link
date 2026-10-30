with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

sidebar_html = """<div style='display: flex; align-items: center; gap: 10px; margin-bottom: 15px;'>
    <svg viewBox="0 0 100 100" width="36" height="36" style="flex-shrink: 0;">
<circle class="nucleus" cx="50" cy="50" r="6" fill="#3B82F6"/>
<g transform="rotate(0 50 50)"><ellipse cx="50" cy="50" rx="40" ry="12" stroke="#3B82F6" stroke-width="3" fill="none" stroke-opacity="0.3"/><circle cx="50" cy="38" r="5" fill="#60A5FA"><animateTransform attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="4s" repeatCount="indefinite" /></circle></g>
<g transform="rotate(60 50 50)"><ellipse cx="50" cy="50" rx="40" ry="12" stroke="#3B82F6" stroke-width="3" fill="none" stroke-opacity="0.3"/><circle cx="50" cy="38" r="5" fill="#60A5FA"><animateTransform attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="4.5s" repeatCount="indefinite" /></circle></g>
<g transform="rotate(120 50 50)"><ellipse cx="50" cy="50" rx="40" ry="12" stroke="#3B82F6" stroke-width="3" fill="none" stroke-opacity="0.3"/><circle cx="50" cy="38" r="5" fill="#60A5FA"><animateTransform attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="5s" repeatCount="indefinite" /></circle></g>
    </svg>
    <h2 style='margin: 0;'>Q<span style='color: #3B82F6; font-family: "Times New Roman", Times, serif !important;'> LINK</span></h2>
</div>"""

code = code.replace(
    'st.markdown("## ⛨ Q<span style=\'color: #3B82F6; font-family: \\"Times New Roman\\", Times, serif !important;\'> LINK</span>", unsafe_allow_html=True)',
    f'st.markdown("""{sidebar_html}""", unsafe_allow_html=True)'
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
