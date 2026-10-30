import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

toggle_code = '''
    st.markdown("<br>", unsafe_allow_html=True)
    animations_on = st.toggle("Animations ON", value=True)
'''

code = code.replace('    st.markdown("<div class=\'sidebar-note\' style=\'margin-top: 12px; text-align: center;\'>Note: Classical channel must be authenticated. Real QKD uses photons over fiber; this is a simulation.</div>", unsafe_allow_html=True)', '    st.markdown("<div class=\'sidebar-note\' style=\'margin-top: 12px; text-align: center;\'>Note: Classical channel must be authenticated. Real QKD uses photons over fiber; this is a simulation.</div>", unsafe_allow_html=True)' + toggle_code)

code = code.replace('ui_effects.inject_global_styles()', 'ui_effects.inject_global_styles(animations_on)')
code = code.replace('ui_effects.render_hero_card()', 'ui_effects.render_hero_card(animations_on)')
code = code.replace('ui_effects.render_channel_illustration(eve_on=(res[\'eve_fraction\'] > 0))', 'ui_effects.render_channel_illustration(eve_on=(res[\'eve_fraction\'] > 0), animations_on=animations_on)')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

with open('ui_effects.py', 'r', encoding='utf-8') as f:
    code_ui = f.read()

code_ui = code_ui.replace('def inject_global_styles():', 'def inject_global_styles(animations_on=True):')
code_ui = code_ui.replace('def render_hero_card():', 'def render_hero_card(animations_on=True):')
code_ui = code_ui.replace('def render_channel_illustration(eve_on=False):', 'def render_channel_illustration(eve_on=False, animations_on=True):')

css_off = '''        /* Animated Background Particles */
        @media (prefers-reduced-motion: no-preference) {'''
new_css = '''        /* Animated Background Particles */'''
code_ui = code_ui.replace(css_off, new_css)
code_ui = code_ui.replace('            }\n            @keyframes bgMove', '            @keyframes bgMove') # removed the closing brace of media query

bg_div = '        <div class="particle-bg"></div>'
bg_code = '''
    if animations_on:
        st.markdown('<div class="particle-bg"></div>', unsafe_allow_html=True)
'''
code_ui = code_ui.replace(bg_div, '')

code_ui = code_ui.replace('"""), unsafe_allow_html=True)', '"""), unsafe_allow_html=True)\n' + bg_code, 1)

code_ui = code_ui.replace('.orb-anim { animation: none !important; }', '.orb-anim { animation: none !important; }') # just a check
# Disable animations if animations_on is False in hero_card
hero_anim_disable = '''
                        @media (prefers-reduced-motion: reduce) {
                            .orb-anim { animation: none !important; }
                        }
'''
hero_anim_new = '''
                        { "" if animations_on else ".orb-anim { animation: none !important; }" }
                        @media (prefers-reduced-motion: reduce) {
                            .orb-anim { animation: none !important; }
                        }
'''
code_ui = code_ui.replace(hero_anim_disable, hero_anim_new)

# disable for illustration
ill_anim_disable = '@media (prefers-reduced-motion: reduce) { .anim { animation: none !important; } }'
ill_anim_new = f'{{ "" if animations_on else ".anim {{ animation: none !important; }}" }} @media (prefers-reduced-motion: reduce) {{ .anim {{ animation: none !important; }} }}'
code_ui = code_ui.replace(ill_anim_disable, ill_anim_new)

# custom spinner
code_ui = code_ui.replace('def custom_spinner(text="Loading..."):', 'def custom_spinner(text="Loading...", animations_on=True):')
code_ui = code_ui.replace('@media (prefers-reduced-motion: reduce) { .custom-spin { animation: none !important; } }', '{ "" if animations_on else ".custom-spin { animation: none !important; }" } @media (prefers-reduced-motion: reduce) { .custom-spin { animation: none !important; } }')

# Fix background particle count to <= 40. Wait, there are only 4 circles and 1 path in the SVG, so that's 5 particles.

with open('ui_effects.py', 'w', encoding='utf-8') as f:
    f.write(code_ui)
