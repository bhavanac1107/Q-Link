import re
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('    st.markdown("<br>", unsafe_allow_html=True)\n    animations_on = st.toggle("Animations ON", value=True)\n\nui_effects.inject_global_styles(animations_on)', 'ui_effects.inject_global_styles()')
code = code.replace('ui_effects.render_hero_card(animations_on)', 'ui_effects.render_hero_card()')
code = code.replace('ui_effects.render_channel_illustration(eve_on=(res[\'eve_fraction\'] > 0), animations_on=animations_on)', 'ui_effects.render_channel_illustration(eve_on=(res[\'eve_fraction\'] > 0))')
code = code.replace(', animations_on=animations_on', '')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

with open('ui_effects.py', 'r', encoding='utf-8') as f:
    ui_code = f.read()

ui_code = ui_code.replace('def inject_global_styles(animations_on=True):', 'def inject_global_styles():')
ui_code = ui_code.replace('def render_hero_card(animations_on=True):', 'def render_hero_card():')
ui_code = ui_code.replace('def render_channel_illustration(eve_on=False, animations_on=True):', 'def render_channel_illustration(eve_on=False):')
ui_code = ui_code.replace('def custom_spinner(text="Loading...", animations_on=True):', 'def custom_spinner(text="Loading..."):')

ui_code = ui_code.replace('{ "" if animations_on else ".orb-anim { animation: none !important; }" }', '')
ui_code = ui_code.replace('{ "" if animations_on else ".anim { animation: none !important; }" }', '')
ui_code = ui_code.replace('{ "" if animations_on else ".custom-spin { animation: none !important; }" }', '')

# For particle background, change:
#     if animations_on:
#         st.markdown('<div class="particle-bg"></div>', unsafe_allow_html=True)
# to just always output it
ui_code = ui_code.replace('    if animations_on:\n        st.markdown(\'<div class="particle-bg"></div>\', unsafe_allow_html=True)', '    st.markdown(\'<div class="particle-bg"></div>\', unsafe_allow_html=True)')

with open('ui_effects.py', 'w', encoding='utf-8') as f:
    f.write(ui_code)
