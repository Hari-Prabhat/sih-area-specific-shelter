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

# ==============================================================================
# PATH SETUP
# ==============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.join(CURRENT_DIR, "services")
COMPONENTS_DIR = os.path.join(CURRENT_DIR, "components")

for path in [CURRENT_DIR, SERVICES_DIR, COMPONENTS_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from components.inputs import render_requirements_inputs
from components.feature_studio import (
    render_shelter_designer_studio,
    render_material_comparison_studio,
    render_multiple_shelter_models_studio,
    render_sensitivity_analysis_studio,
)
from components.comparison import render_baseline_vs_optimized_view

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


def main() -> None:
    """
    Main Application Orchestrator.
    """
    # --------------------------------------------------------------------------
    # HEADER & PRODUCT WORKFLOW
    # --------------------------------------------------------------------------
    st.markdown('<div class="main-title">🏕️ ThermoShelter </div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Area-Specific Passive Shelter Design, Transient Building Physics & Bayesian Optimization Platform</div>',
        unsafe_allow_html=True,
    )

    st.markdown("""
    <div class="workflow-bar">
        <span><span class="workflow-step">1. CLIMATE</span> (Ladakh & Regions)</span>
        <span>→</span>
        <span><span class="workflow-step">2. REQUIREMENTS</span> (Permanence & Sizing)</span>
        <span>→</span>
        <span><span class="workflow-step">3. SIMULATE</span> (168-hr ISO 6946)</span>
        <span>→</span>
        <span><span class="workflow-step">4. OPTIMIZE</span> (Bayesian Search)</span>
        <span>→</span>
        <span><span class="workflow-step">5. COMPARE</span> (Baseline vs Opt)</span>
        <span>→</span>
        <span><span class="workflow-step">6. 3D VISUALIZE</span></span>
    </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # UNIFIED REQUIREMENTS & CONSTRAINTS INPUT SECTION
    # --------------------------------------------------------------------------
    req = render_requirements_inputs(
        default_city="leh",
        default_people=4,
        default_home_type="Permanent",
    )

    st.markdown("---")

    # --------------------------------------------------------------------------
    # FEATURE STUDIO NAVIGATION (INSTANT-LOADING TABS)
    # --------------------------------------------------------------------------
    nav_mode = st.radio(
        "Select Feature Studio:",
        [
            "🏠 Shelter Designer",
            "⚖️ Baseline vs Optimized",
            "🧱 Material Comparison Studio",
            "🏛️ Multiple Shelter Models",
            "📈 Sensitivity Analysis Studio",
        ],
        horizontal=True,
        key="feature_studio_nav",
    )
    st.markdown("---")

    # --------------------------------------------------------------------------
    # INSTANT STUDIO DISPATCH (NO SECONDARY BUTTONS REQUIRED)
    # --------------------------------------------------------------------------
    if nav_mode == "🏠 Shelter Designer":
        render_shelter_designer_studio(req, is_dark=True)

    elif nav_mode == "⚖️ Baseline vs Optimized":
        render_baseline_vs_optimized_view(
            comp_city=req["city"],
            comp_people=req["people"],
            comp_home_type=req["home_type"],
            is_dark=True,
        )

    elif nav_mode == "🧱 Material Comparison Studio":
        render_material_comparison_studio(req, is_dark=True)

    elif nav_mode == "🏛️ Multiple Shelter Models":
        render_multiple_shelter_models_studio(req, is_dark=True)

    elif nav_mode == "📈 Sensitivity Analysis Studio":
        render_sensitivity_analysis_studio(req, is_dark=True)


if __name__ == "__main__":
    main()