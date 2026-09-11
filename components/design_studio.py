"""
================================================================================
THERMOSHELTER AI — Interactive Design Studio Component
================================================================================
Embeds the full ThermoShelter React + Three.js Design Studio as a seamless,
true edge-to-edge fullscreen interface without outer container borders or divs.
================================================================================
"""

import os
import streamlit as st
import streamlit.components.v1 as components

# Base directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DIST_DIR = os.path.join(BASE_DIR, "frontend", "dist")
if not os.path.exists(DIST_DIR) or not os.path.exists(os.path.join(DIST_DIR, "index.html")):
    DIST_DIR = os.path.join(BASE_DIR, "thermoshelter-design-studio", "dist")

# Register the static file route in Tornado via Streamlit declare_component
_component_func = components.declare_component(
    "thermoshelter_design_studio",
    path=DIST_DIR
)


def render_design_studio() -> None:
    """
    Renders the ThermoShelter Design Studio in true edge-to-edge fullscreen.
    Hides all Streamlit headers, padding, footers, and margins so the UI
    occupies 100% of the browser window.
    """
    st.markdown(
        """
        <style>
            /* Hide Streamlit default headers, toolbars, and footers */
            header[data-testid="stHeader"] {
                display: none !important;
            }
            footer {
                display: none !important;
            }
            #MainMenu {
                display: none !important;
            }
            [data-testid="stDecoration"] {
                display: none !important;
            }
            [data-testid="stToolbar"] {
                display: none !important;
            }

            /* Strip all padding and margins from root containers */
            html, body {
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
                background-color: #0f172a !important;
            }
            .main, .block-container, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"], [data-testid="stCustomComponentV1"] {
                padding: 0 !important;
                margin: 0 !important;
                max-width: 100vw !important;
                width: 100vw !important;
                height: 100vh !important;
                overflow: hidden !important;
            }

            /* Make the iframe fixed to the entire viewport */
            iframe {
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                border: none !important;
                margin: 0 !important;
                padding: 0 !important;
                z-index: 99999 !important;
                background-color: #0f172a !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    component_url = "/component/components.design_studio.thermoshelter_design_studio/index.html"

    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                html, body {{ width: 100vw; height: 100vh; overflow: hidden; background: #0f172a; }}
                iframe {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; border: none; }}
            </style>
        </head>
        <body>
            <iframe
                src="{component_url}"
                allow="accelerometer; autoplay; camera; encrypted-media; geolocation; gyroscope; microphone; midi; payment; usb; xr-spatial-tracking"
                sandbox="allow-forms allow-modals allow-popups allow-popups-to-escape-sandbox allow-same-origin allow-scripts"
            ></iframe>
        </body>
        </html>
        """,
        height=1,  # CSS fixed position handles full viewport
        scrolling=False,
    )
