import inspect
import re
def strip_indent(s):
    return re.sub(r'^[ \t]+', '', s, flags=re.MULTILINE)
import streamlit as st
def inject_global_styles():
    st.markdown(strip_indent("""
        <style>
        /* Times New Roman Font application */
        p, h1, h2, h3, h4, h5, h6, li, a, div.stMarkdown, div.stText, div.stButton button, label, .glass-card, [data-testid="stMarkdownContainer"] {
            font-family: "Times New Roman", Times, "Liberation Serif", serif !important;
        }
        /* Exclude icons and code blocks */
        code, pre, .mono-font, .stCodeBlock {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace !important;
        }
        /* Material icons reset */
        .stIcon, .material-icons, .material-symbols-outlined, [data-icon], [class*="icon"], [class*="Icon"], [data-testid*="Icon"], [data-testid*="stExpanderToggleIcon"], [data-baseweb] svg, svg, svg *, span:has(> svg) {
            font-family: "Material Symbols Outlined", "Material Icons", "Material Symbols Rounded", sans-serif !important;
        }
        /* Improve readability for small text with serif */
        small, .text-muted {
            font-size: 1rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.2px;
        }
        /* Make inputs, radios, and labels larger to compensate for Times New Roman's small x-height */
        label, .stTextInput input, .stSelectbox div, .stRadio div, div[data-baseweb="select"], .stSlider div[data-testid="stThumbValue"], p {
            font-size: 1.15rem !important;
            letter-spacing: 0.3px;
        }
        /* Animated Background Particles */
            .particle-bg {
                position: fixed;
                top: 0; left: 0; width: 100vw; height: 100vh;
                pointer-events: none;
                z-index: -1;
                opacity: 0.15;
                background-image: url("data:image/svg+xml,%3Csvg width='400' height='400' viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%233B82F6' fill-opacity='1' fill-rule='evenodd'%3E%3Ccircle cx='50' cy='50' r='1.5'%3E%3Canimate attributeName='cx' values='50;150;50' dur='20s' repeatCount='indefinite'/%3E%3Canimate attributeName='cy' values='50;100;50' dur='25s' repeatCount='indefinite'/%3E%3C/circle%3E%3Ccircle cx='250' cy='150' r='1.5'%3E%3Canimate attributeName='cx' values='250;100;250' dur='30s' repeatCount='indefinite'/%3E%3Canimate attributeName='cy' values='150;300;150' dur='28s' repeatCount='indefinite'/%3E%3C/circle%3E%3Ccircle cx='150' cy='250' r='1.5'%3E%3Canimate attributeName='cx' values='150;300;150' dur='22s' repeatCount='indefinite'/%3E%3Canimate attributeName='cy' values='250;50;250' dur='26s' repeatCount='indefinite'/%3E%3C/circle%3E%3Ccircle cx='350' cy='300' r='1.5'%3E%3Canimate attributeName='cx' values='350;150;350' dur='27s' repeatCount='indefinite'/%3E%3Canimate attributeName='cy' values='300;100;300' dur='24s' repeatCount='indefinite'/%3E%3C/circle%3E%3Cpath d='M50 50 L150 250' stroke='%233B82F6' stroke-width='0.5' stroke-opacity='0.3'%3E%3Canimate attributeName='d' values='M50 50 L150 250; M150 100 L300 50; M50 50 L150 250' dur='20s' repeatCount='indefinite'/%3E%3C/path%3E%3C/g%3E%3C/svg%3E");
                background-size: 400px 400px;
                animation: bgMove 60s linear infinite;
            @keyframes bgMove {
                0% { background-position: 0 0; }
                100% { background-position: 400px 400px; }
            }
        }
        /* Fix empty bars - streamlit injects empty divs sometimes */
        .stMarkdown:empty {
            display: none !important;
        }
        </style>
    """), unsafe_allow_html=True)
    st.markdown('<div class="particle-bg"></div>', unsafe_allow_html=True)

def render_hero_card():
    # Hero card with animated atom
    st.markdown(strip_indent("""
        <div class="glass-card" style="display: flex; align-items: center; justify-content: space-between; overflow: hidden; position: relative;">
            <div style="z-index: 1;">
                <h1 style='margin-top: 0; color: #60A5FA; display: flex; align-items: center; gap: 10px;'>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                    <span style="font-family: 'Times New Roman', Times, serif !important;">Q LINK</span>
                </h1>
                <p style="font-size: 18px; color: #A8B3D1; margin-bottom: 0;">Detect · Protect · Secure</p>
            </div>
            <div class="atom-animation" style="width: 100px; height: 100px; position: relative; z-index: 0; opacity: 0.8; margin-right: 20px;">
                <svg viewBox="0 0 100 100" width="100%" height="100%">
                    <style>
                        .orbit { stroke: #3B82F6; stroke-width: 1; fill: none; stroke-opacity: 0.3; }
                        .electron { fill: #60A5FA; }
                        .nucleus { fill: #3B82F6; filter: drop-shadow(0 0 4px #60A5FA); }
                        @media (prefers-reduced-motion: reduce) {
                            .orb-anim { animation: none !important; }
                        }
                    </style>
                    <circle class="nucleus" cx="50" cy="50" r="4"/>
                    <g transform="rotate(0 50 50)">
                        <ellipse class="orbit" cx="50" cy="50" rx="40" ry="12" />
                        <circle class="electron" cx="50" cy="38" r="2">
                            <animateTransform class="orb-anim" attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="4s" repeatCount="indefinite" />
                        </circle>
                    </g>
                    <g transform="rotate(60 50 50)">
                        <ellipse class="orbit" cx="50" cy="50" rx="40" ry="12" />
                        <circle class="electron" cx="50" cy="38" r="2">
                            <animateTransform class="orb-anim" attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="4.5s" repeatCount="indefinite" />
                        </circle>
                    </g>
                    <g transform="rotate(120 50 50)">
                        <ellipse class="orbit" cx="50" cy="50" rx="40" ry="12" />
                        <circle class="electron" cx="50" cy="38" r="2">
                            <animateTransform class="orb-anim" attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="5s" repeatCount="indefinite" />
                        </circle>
                    </g>
                </svg>
            </div>
        </div>
    """), unsafe_allow_html=True)
def render_channel_illustration(eve_on=False):
    st.markdown("### Illustration")
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if eve_on:
        st.markdown(strip_indent("""
        <svg viewBox="0 0 600 50" width="100%" height="50">
            <style>
                .line { stroke: #3B82F6; stroke-width: 2; stroke-opacity: 0.3; }
                .line-red { stroke: #EF4444; stroke-width: 2; stroke-opacity: 0.3; }
                .photon { fill: #60A5FA; filter: drop-shadow(0 0 3px #60A5FA); }
                .photon-red { fill: #F87171; filter: drop-shadow(0 0 3px #EF4444); }
                .node { fill: #131F45; stroke: #3B82F6; stroke-width: 2; }
                .node-eve { fill: #131F45; stroke: #EF4444; stroke-width: 2; }
                .text { fill: #A8B3D1; font-family: 'Times New Roman', serif; font-size: 14px; text-anchor: middle; }
                 @media (prefers-reduced-motion: reduce) { .anim { animation: none !important; } }
            </style>
            <!-- Lines -->
            <line class="line" x1="50" y1="25" x2="300" y2="25" />
            <line class="line-red" x1="300" y1="25" x2="550" y2="25" />
            <!-- Photons -->
            <circle class="photon" cx="50" cy="25" r="3">
                <animate class="anim" attributeName="cx" values="50;300" dur="2s" repeatCount="indefinite" />
            </circle>
            <circle class="photon-red" cx="300" cy="25" r="3">
                <animate class="anim" attributeName="cx" values="300;550" dur="2s" repeatCount="indefinite" />
            </circle>
            <!-- Nodes -->
            <rect class="node" x="10" y="10" width="80" height="30" rx="4" />
            <text class="text" x="50" y="30">Alice</text>
            <rect class="node-eve" x="260" y="10" width="80" height="30" rx="4" />
            <text class="text" x="300" y="30" fill="#F87171">Eve</text>
            <rect class="node" x="510" y="10" width="80" height="30" rx="4" />
            <text class="text" x="550" y="30">Bob</text>
        </svg>
        """), unsafe_allow_html=True)
    else:
        st.markdown(strip_indent("""
        <svg viewBox="0 0 600 50" width="100%" height="50">
            <style>
                .line { stroke: #3B82F6; stroke-width: 2; stroke-opacity: 0.3; }
                .photon { fill: #60A5FA; filter: drop-shadow(0 0 3px #60A5FA); }
                .node { fill: #131F45; stroke: #3B82F6; stroke-width: 2; }
                .text { fill: #A8B3D1; font-family: 'Times New Roman', serif; font-size: 14px; text-anchor: middle; }
                 @media (prefers-reduced-motion: reduce) { .anim { animation: none !important; } }
            </style>
            <!-- Lines -->
            <line class="line" x1="50" y1="25" x2="550" y2="25" />
            <!-- Photons -->
            <circle class="photon" cx="50" cy="25" r="3">
                <animate class="anim" attributeName="cx" values="50;550" dur="3s" repeatCount="indefinite" />
            </circle>
            <circle class="photon" cx="50" cy="25" r="3">
                <animate class="anim" attributeName="cx" values="50;550" dur="3s" begin="1s" repeatCount="indefinite" />
            </circle>
            <circle class="photon" cx="50" cy="25" r="3">
                <animate class="anim" attributeName="cx" values="50;550" dur="3s" begin="2s" repeatCount="indefinite" />
            </circle>
            <!-- Nodes -->
            <rect class="node" x="10" y="10" width="80" height="30" rx="4" />
            <text class="text" x="50" y="30">Alice</text>
            <rect class="node" x="510" y="10" width="80" height="30" rx="4" />
            <text class="text" x="550" y="30">Bob</text>
        </svg>
        """), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
import contextlib
@contextlib.contextmanager
def custom_spinner(text="Loading..."):
    placeholder = st.empty()
    placeholder.markdown(strip_indent(f"""
        <div style="display: flex; align-items: center; gap: 10px; color: #60A5FA; padding: 10px 0;">
            <svg width="24" height="24" viewBox="0 0 100 100">
                <style>
                    .custom-spin {{ transform-origin: 50px 50px; animation: spin 2s linear infinite; }}
                    @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
                    .orb {{ stroke: #3B82F6; stroke-width: 4; fill: none; stroke-opacity: 0.3; }}
                    .dot {{ fill: #60A5FA; filter: drop-shadow(0 0 2px #60A5FA); }}
                    @media (prefers-reduced-motion: reduce) {{ .custom-spin {{ animation: none !important; }} }}
                </style>
                <circle class="orb" cx="50" cy="50" r="40" />
                <g class="custom-spin">
                    <circle class="dot" cx="90" cy="50" r="6"/>
                    <circle class="dot" cx="10" cy="50" r="6"/>
                </g>
            </svg>
            <span style="font-family: 'Times New Roman', serif;">{text}</span>
        </div>
    """), unsafe_allow_html=True)
    try:
        yield
    finally:
        placeholder.empty()
