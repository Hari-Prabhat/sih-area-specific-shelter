"""
================================================================================
THERMOSHELTER AI — Area-Specific Passive Shelter Design Platform
================================================================================
Scientific Bedrock: Transient Forward Euler 1D Heat Transfer & ISO 6946 Envelope Engine
Product Differentiator: Multi-Objective Bayesian Optimization & Explainable Recommendation
Target Region Hero Demo: High-Altitude Cold Climates (Leh, Ladakh) & Multi-Climatic Framework
================================================================================
"""

import os
import sys
import streamlit as st

import socket
import subprocess

# ==============================================================================
# PATH SETUP
# ==============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.join(CURRENT_DIR, "services")
COMPONENTS_DIR = os.path.join(CURRENT_DIR, "components")

for path in [CURRENT_DIR, SERVICES_DIR, COMPONENTS_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)


def ensure_backend_running() -> None:
    """Ensure FastAPI backend is running on 127.0.0.1:8000; spawn if not."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            if s.connect_ex(("127.0.0.1", 8000)) == 0:
                return  # Backend is already running and accepting connections
    except Exception:
        pass

    try:
        creation_flag = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=CURRENT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flag,
        )
    except Exception as e:
        print(f"Warning: Could not auto-start backend: {e}")


ensure_backend_running()

from components.inputs import render_requirements_inputs
from components.feature_studio import (
    render_shelter_designer_studio,
    render_material_comparison_studio,
    render_multiple_shelter_models_studio,
    render_sensitivity_analysis_studio,
)
from components.comparison import render_baseline_vs_optimized_view
from components.design_studio import render_design_studio

# ==============================================================================
# STREAMLIT PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="ThermoShelter | Area-Specific Passive Shelter Design",
    page_icon="🏕️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# UNIFIED HIGH-CONTRAST DARK/LIGHT THEME CSS
# ==============================================================================
st.markdown("""
<style>
    /* Clean typography & header styling */
    .main-title {
        font-size: 2.2rem; font-weight: 800;
        color: #38bdf8; margin-bottom: 0.1rem;
        letter-spacing: -0.5px;
    }
    .sub-title {
        font-size: 1.05rem; color: #94a3b8; margin-bottom: 1.0rem;
    }
    .workflow-bar {
        background-color: #0f172a;
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 8px;
        padding: 8px 16px;
        margin-bottom: 1.2rem;
        display: flex;
        justify-content: space-between;
        font-size: 0.82rem;
        font-weight: 600;
        color: #cbd5e1;
    }
    .workflow-step { color: #38bdf8; }
    .card {
        background-color: #1e293b;
        border-radius: 10px; padding: 18px;
        border-left: 5px solid #38bdf8;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        margin-bottom: 1rem; color: #e2e8f0;
    }
    .card h4 { color: #38bdf8; margin-top:0; margin-bottom:8px; font-size:1.02rem; }
    .card p  { color: #cbd5e1; margin:4px 0; font-size:0.90rem; line-height:1.5; }
    .card b  { color: #f1f5f9; }
    .metric-badge { font-weight:700; color:#22d3ee; font-size:1.10rem; }
</style>
""", unsafe_allow_html=True)


from i18n import t, render_language_selector, get_current_language

def main() -> None:
    """
    Main Application Orchestrator.
    """
    cur_lang = get_current_language()

    # --------------------------------------------------------------------------
    # SIDEBAR CONTROLS & PLATFORM VIEW SWITCHER
    # --------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("### 🏕️ ThermoShelter")
        app_view = st.selectbox(
            t("platform_view"),
            [
                "✨ 3D Design Studio",
                "🔬 Scientific & Bayesian Engine",
            ],
            index=0,
            format_func=lambda v, _l=cur_lang: t("view_3d_studio", lang=_l) if "3D" in v else t("view_scientific_engine", lang=_l),
            key="thermoshelter_app_view",
        )
        st.markdown("---")
        render_language_selector(key="sidebar_lang_selector", label_visibility="visible")

    # --------------------------------------------------------------------------
    # FULLSCREEN 3D DESIGN STUDIO VIEW
    # --------------------------------------------------------------------------
    if app_view == "✨ 3D Design Studio":
        render_design_studio()
        return

    # --------------------------------------------------------------------------
    # SCIENTIFIC & BAYESIAN ENGINE VIEW: HEADER & LANGUAGE SELECTOR
    # --------------------------------------------------------------------------
    head_col1, head_col2 = st.columns([3.8, 1.2])
    with head_col1:
        st.markdown(f'<div class="main-title">{t("app_title")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sub-title">{t("app_subtitle")}</div>', unsafe_allow_html=True)
    with head_col2:
        render_language_selector(key="header_lang_selector", label_visibility="visible")

    # --------------------------------------------------------------------------
    # SCIENTIFIC WORKFLOW PROGRESSION BAR
    # --------------------------------------------------------------------------
    st.markdown(f"""
    <div class="workflow-bar">
        <span><span class="workflow-step">{t("wf_step1")}</span> {t("wf_step1_sub")}</span>
        <span>→</span>
        <span><span class="workflow-step">{t("wf_step2")}</span> {t("wf_step2_sub")}</span>
        <span>→</span>
        <span><span class="workflow-step">{t("wf_step3")}</span> {t("wf_step3_sub")}</span>
        <span>→</span>
        <span><span class="workflow-step">{t("wf_step4")}</span> {t("wf_step4_sub")}</span>
        <span>→</span>
        <span><span class="workflow-step">{t("wf_step5")}</span> {t("wf_step5_sub")}</span>
        <span>→</span>
        <span><span class="workflow-step">{t("wf_step6")}</span></span>
    </div>
    """, unsafe_allow_html=True)

    # UNIFIED REQUIREMENTS & CONSTRAINTS INPUT SECTION
    req = render_requirements_inputs(
        default_city="leh",
        default_people=4,
        default_home_type="Permanent",
    )

    st.markdown("---")

    # FEATURE STUDIO NAVIGATION (INSTANT-LOADING TABS)
    cur_lang = get_current_language()
    nav_keys = [
        "studio_shelter_designer",
        "studio_baseline_vs_opt",
        "studio_material_comparison",
        "studio_multiple_models",
        "studio_sensitivity_analysis",
    ]
    nav_mode = st.radio(
        t("studio_nav_label"),
        nav_keys,
        format_func=lambda k, _l=cur_lang: t(k, lang=_l),
        horizontal=True,
        key="feature_studio_nav",
    )
    st.markdown("---")

    # INSTANT STUDIO DISPATCH
    if nav_mode in ("studio_shelter_designer", "🏠 Shelter Designer"):
        render_shelter_designer_studio(req, is_dark=True)

    elif nav_mode in ("studio_baseline_vs_opt", "⚖️ Baseline vs Optimized"):
        render_baseline_vs_optimized_view(
            comp_city=req["city"],
            comp_people=req["people"],
            comp_home_type=req["home_type"],
            is_dark=True,
        )

    elif nav_mode in ("studio_material_comparison", "🧱 Material Comparison Studio"):
        render_material_comparison_studio(req, is_dark=True)

    elif nav_mode in ("studio_multiple_models", "🏛️ Multiple Shelter Models"):
        render_multiple_shelter_models_studio(req, is_dark=True)

    elif nav_mode in ("studio_sensitivity_analysis", "📈 Sensitivity Analysis Studio"):
        render_sensitivity_analysis_studio(req, is_dark=True)


if __name__ == "__main__":
    main()