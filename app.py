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
from components.design_studio import render_design_studio, render_site_profile
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
# UNIFIED HIGH-CONTRAST ENGINEERING DESIGN THEME CSS
# ==============================================================================
st.markdown("""
<style>
    /* Clean typography & header styling */
    .main-title {
        font-size: 2.3rem; font-weight: 800;
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
        padding: 10px 18px;
        margin-bottom: 1.2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.84rem;
        font-weight: 600;
        color: #cbd5e1;
        flex-wrap: wrap;
        gap: 6px;
    }
    .workflow-step { color: #38bdf8; font-weight: 700; }
    .card {
        background-color: #1e293b;
        border-radius: 10px; padding: 18px;
        border-left: 5px solid #38bdf8;
        box-shadow: 0 4px 12px rgba(0,0,0,0.35);
        margin-bottom: 1rem; color: #e2e8f0;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .card:hover {
        box-shadow: 0 6px 16px rgba(56, 189, 248, 0.15);
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
    Coordinates the Guided Design Studio and 5 specialized engineering studios.
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
        <span><span class="workflow-step">1. LOCATION</span> (Ladakh & Regions)</span>
        <span>➔</span>
        <span><span class="workflow-step">2. MISSION</span> (Occupancy & Role)</span>
        <span>➔</span>
        <span><span class="workflow-step">3. PRIORITIES</span> (Thermal / Energy)</span>
        <span>➔</span>
        <span><span class="workflow-step">4. RESOURCES</span> (Solar / Mass)</span>
        <span>➔</span>
        <span><span class="workflow-step">5. REVIEW</span> (Audit Criteria)</span>
        <span>➔</span>
        <span><span class="workflow-step">6. GENERATE</span> (DNA & ISO 6946)</span>
    </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # FEATURE STUDIO NAVIGATION
    # --------------------------------------------------------------------------
    nav_mode = st.radio(
        "Select Architectural-Engineering Studio:",
        [
            "🎯 Design Studio (Guided Workflow)",
            "🏠 Shelter Designer",
            "⚖️ Baseline vs Optimized",
            "🧱 Material Comparison Studio",
            "🏛️ Multiple Shelter Models",
            "📈 Sensitivity Analysis Studio",
        ],
        horizontal=True,
        key="feature_studio_nav",
        help="Switch between the step-by-step Design Studio or specialized physical analysis studios.",
    )
    st.markdown("---")

    # --------------------------------------------------------------------------
    # RETRIEVE SYNCHRONIZED REQUIREMENTS FROM SESSION STATE
    # --------------------------------------------------------------------------
    synced = st.session_state.get("design_requirements", {})
    def_city = synced.get("city", "leh")
    def_people = synced.get("people", 4)
    def_home_type = synced.get("home_type", "Permanent")

    # --------------------------------------------------------------------------
    # STUDIO DISPATCH
    # --------------------------------------------------------------------------
    if nav_mode == "🎯 Design Studio (Guided Workflow)":
        render_design_studio(is_dark=True)

    elif nav_mode == "🏠 Shelter Designer":
        st.info("ℹ️ **Active Requirements Context:** Parameters configured here or in Design Studio automatically update the simulation.")
        req = render_requirements_inputs(
            default_city=def_city,
            default_people=def_people,
            default_home_type=def_home_type,
        )
        st.markdown("---")
        render_shelter_designer_studio(req, is_dark=True)

    elif nav_mode == "⚖️ Baseline vs Optimized":
        req = render_requirements_inputs(
            default_city=def_city,
            default_people=def_people,
            default_home_type=def_home_type,
        )
        st.markdown("---")
        render_baseline_vs_optimized_view(
            comp_city=req["city"],
            comp_people=req["people"],
            comp_home_type=req["home_type"],
            is_dark=True,
        )

    elif nav_mode == "🧱 Material Comparison Studio":
        req = render_requirements_inputs(
            default_city=def_city,
            default_people=def_people,
            default_home_type=def_home_type,
        )
        st.markdown("---")
        render_material_comparison_studio(req, is_dark=True)

    elif nav_mode == "🏛️ Multiple Shelter Models":
        req = render_requirements_inputs(
            default_city=def_city,
            default_people=def_people,
            default_home_type=def_home_type,
        )
        st.markdown("---")
        render_multiple_shelter_models_studio(req, is_dark=True)

    elif nav_mode == "📈 Sensitivity Analysis Studio":
        req = render_requirements_inputs(
            default_city=def_city,
            default_people=def_people,
            default_home_type=def_home_type,
        )
        st.markdown("---")
        render_sensitivity_analysis_studio(req, is_dark=True)


if __name__ == "__main__":
    main()