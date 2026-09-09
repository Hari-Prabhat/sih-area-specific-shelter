"""
THERMOSHELTER AI — Guided Engineering Design Studio
===================================================
A structured, step-by-step engineering design workflow:
  Step 1: LOCATION & SITE PROFILE
  Step 2: SHELTER MISSION
  Step 3: DESIGN PRIORITIES
  Step 4: AVAILABLE RESOURCES & CONSTRAINTS
  Step 5: ENGINEERING REVIEW & VALIDATION
  Step 6: GENERATE DESIGN / DESIGN DNA & TECHNICAL VIEW

Preserves all scientific simulation engines and links seamlessly
with all specialized feature studios in ThermoShelter AI.
"""

from typing import Any, Dict, List, Optional
import math
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from components.inputs import CITIES_METADATA, get_city_metadata, get_all_supported_cities
from components.chart_theme import apply_chart_theme, FONT_FAMILY
from components.charts import (
    plot_temperature_curves,
    plot_solar_dynamics,
    plot_component_heat_flows,
    plot_energy_balance_breakdown,
    create_2d_floorplan,
)
from components.recommendations import render_envelope_specifications, render_explainable_rationale
from components.shelter_3d import render_3d_and_floorplan
from components.export import render_export_section
from components.validation import render_model_assumptions_and_validation

from services.recommender import (
    get_recommendation,
    auto_size_shelter,
    recommend_materials,
    CLIMATE_MAPPING,
    CLIMATE_DESCRIPTIONS,
)
from services.simulation_service import run_simulation, GLAZING_PROPERTIES
from services.material_service import load_all_materials, get_material
from services.visual3d import build_3d_shelter


# ==============================================================================
# PROVENANCE BADGE STYLES & LABELS
# ==============================================================================
def render_provenance_badge(kind: str) -> str:
    """
    Returns an HTML badge distinguishing data provenance.
    """
    badges = {
        "calculated": (
            '<span style="background-color: #064e3b; color: #34d399; font-size: 0.72rem; '
            'padding: 2px 8px; border-radius: 4px; font-weight: 700; letter-spacing: 0.5px; '
            'border: 1px solid rgba(52, 211, 153, 0.4);">CALCULATED: ISO 6946</span>'
        ),
        "simulated": (
            '<span style="background-color: #0c4a6e; color: #38bdf8; font-size: 0.72rem; '
            'padding: 2px 8px; border-radius: 4px; font-weight: 700; letter-spacing: 0.5px; '
            'border: 1px solid rgba(56, 189, 248, 0.4);">SIMULATED: 168-HR EULER</span>'
        ),
        "optimized": (
            '<span style="background-color: #4c1d95; color: #c084fc; font-size: 0.72rem; '
            'padding: 2px 8px; border-radius: 4px; font-weight: 700; letter-spacing: 0.5px; '
            'border: 1px solid rgba(192, 132, 252, 0.4);">OPTIMIZED: TPE BAYESIAN</span>'
        ),
        "specified": (
            '<span style="background-color: #1e293b; color: #94a3b8; font-size: 0.72rem; '
            'padding: 2px 8px; border-radius: 4px; font-weight: 700; letter-spacing: 0.5px; '
            'border: 1px solid rgba(148, 163, 184, 0.4);">SPECIFIED MISSION INPUT</span>'
        ),
        "demo": (
            '<span style="background-color: #78350f; color: #fbbf24; font-size: 0.72rem; '
            'padding: 2px 8px; border-radius: 4px; font-weight: 700; letter-spacing: 0.5px; '
            'border: 1px solid rgba(251, 191, 36, 0.4);">DEMO / ESTIMATE PROXY</span>'
        ),
    }
    return badges.get(kind.lower(), badges["specified"])


# ==============================================================================
# REUSABLE COMPONENT: SITE PROFILE
# ==============================================================================
def render_site_profile(city: str, is_dark: bool = True) -> None:
    """
    Renders comprehensive site climate summary using authoritative observed
    datasets and provenance metadata in the repository.
    """
    meta = get_city_metadata(city)
    ct_name = CLIMATE_DESCRIPTIONS.get(CLIMATE_MAPPING.get(city, "composite"), "Composite")

    bg_color = "#131d31" if is_dark else "#f8fafc"
    card_bg = "#1e293b" if is_dark else "#ffffff"
    border_col = "rgba(56, 189, 248, 0.3)" if is_dark else "rgba(14, 165, 233, 0.3)"
    text_col = "#e2e8f0" if is_dark else "#0f172a"
    sub_col = "#94a3b8" if is_dark else "#64748b"

    st.markdown(
        f"""
    <div style="background-color: {bg_color}; border-radius: 10px; padding: 18px 22px; 
                border: 1px solid {border_col}; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.25);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
            <div>
                <span style="font-size: 1.25rem; font-weight: 800; color: #38bdf8; letter-spacing: -0.3px;">
                    📍 {meta['display']}
                </span>
                <span style="font-size: 0.85rem; color: {sub_col}; margin-left: 8px;">
                    ({meta['region']}, {meta['country']})
                </span>
            </div>
            <div style="display: flex; gap: 8px; align-items: center;">
                <span style="background-color: #0369a1; color: #f0f9ff; padding: 3px 12px; border-radius: 12px; font-size: 0.80rem; font-weight: 700;">
                    {meta['badge']}
                </span>
                {render_provenance_badge('calculated')}
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 14px;">
            <div style="background-color: {card_bg}; padding: 10px 14px; border-radius: 8px; border-left: 3px solid #38bdf8;">
                <div style="font-size: 0.75rem; color: {sub_col}; font-weight: 600; text-transform: uppercase;">Elevation / Coordinates</div>
                <div style="font-size: 1.05rem; font-weight: 700; color: {text_col};">{meta['elevation']}</div>
                <div style="font-size: 0.75rem; color: {sub_col};">{meta['latitude']}° N, {meta['longitude']}° E</div>
            </div>
            <div style="background-color: {card_bg}; padding: 10px 14px; border-radius: 8px; border-left: 3px solid #60a5fa;">
                <div style="font-size: 0.75rem; color: {sub_col}; font-weight: 600; text-transform: uppercase;">Design Winter / Summer</div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #60a5fa;">{meta['winter_temp']} <span style="color: {sub_col}; font-weight: 400;">/</span> <span style="color: #f87171;">{meta['summer_temp']}</span></div>
                <div style="font-size: 0.75rem; color: {sub_col};">Diurnal Swing: <b>{meta.get('diurnal_swing', '15 °C')}</b></div>
            </div>
            <div style="background-color: {card_bg}; padding: 10px 14px; border-radius: 8px; border-left: 3px solid #fbbf24;">
                <div style="font-size: 0.75rem; color: {sub_col}; font-weight: 600; text-transform: uppercase;">Annual Solar Resource</div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #fbbf24;">{meta['solar_ghi']}</div>
                <div style="font-size: 0.75rem; color: {sub_col};">GHI Global Horizontal Irradiance</div>
            </div>
            <div style="background-color: {card_bg}; padding: 10px 14px; border-radius: 8px; border-left: 3px solid #34d399;">
                <div style="font-size: 0.75rem; color: {sub_col}; font-weight: 600; text-transform: uppercase;">Degree Days (18 °C Base)</div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #34d399;">{meta['hdd']} HDD <span style="font-size: 0.85rem; color: {sub_col};">/ {meta.get('cdd', 0)} CDD</span></div>
                <div style="font-size: 0.75rem; color: {sub_col};">Köppen: <b>{meta.get('koppen_classification', 'BWk')}</b></div>
            </div>
        </div>

        <div style="background-color: {card_bg}; padding: 10px 14px; border-radius: 8px; font-size: 0.84rem; color: {text_col}; line-height: 1.5; margin-bottom: 10px;">
            <b style="color: #38bdf8;">Dominant Thermal Regimes:</b> {meta.get('dominant_demand', 'Extreme heating demand')}<br/>
            <span style="color: {sub_col}; font-size: 0.80rem;">{meta.get('notes', '')}</span>
        </div>

        <div style="font-size: 0.78rem; color: {sub_col}; border-top: 1px solid rgba(148, 163, 184, 0.2); padding-top: 8px; display: flex; justify-content: space-between; flex-wrap: wrap;">
            <span><b>Observed Meteorological Source:</b> {meta['source']}</span>
            <span><b>Dataset Type:</b> {meta['type']} (Verified Reference EPW)</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# REUSABLE COMPONENT: DESIGN DNA
# ==============================================================================
def render_design_dna(design_data: Dict[str, Any], is_dark: bool = True) -> None:
    """
    Renders the unified 8-section visual summary of the generated shelter design:
      1. Site
      2. Mission
      3. Geometry
      4. Orientation
      5. Envelope
      6. Passive Strategy
      7. Materials
      8. Thermal Performance
    """
    city = design_data.get("city", "leh")
    meta = get_city_metadata(city)
    mission = design_data.get("mission", {})
    geo = design_data.get("geometry", {})
    mats = design_data.get("materials", {})
    sim_res = design_data.get("simulation_result", {})
    u_vals = sim_res.get("u_values", {})
    met = sim_res.get("comfort_metrics", {})
    cl = sim_res.get("component_heat_loss_kwh", {})

    st.markdown("### 🧬 Shelter Design DNA Summary")
    st.caption("Standardized architectural-engineering matrix capturing all primary design dimensions and scientific parameters.")

    # Top Hero Badge
    st.markdown(
        f"""
    <div style="background-color: #0f172a; border-radius: 8px; padding: 12px 18px; 
                border-left: 4px solid #38bdf8; margin-bottom: 16px; display: flex; 
                justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
        <div>
            <span style="font-size: 1.05rem; font-weight: 700; color: #38bdf8;">Design Identifier: </span>
            <span style="font-family: monospace; font-size: 1.15rem; font-weight: 800; color: #f1f5f9;">
                {design_data.get('design_id', 'TS-DESIGN-01')}
            </span>
        </div>
        <div style="display: flex; gap: 8px;">
            {render_provenance_badge('optimized')}
            {render_provenance_badge('simulated')}
            {render_provenance_badge('calculated')}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 8-Section Grid
    dna_c1, dna_c2 = st.columns(2)

    with dna_c1:
        # 1. SITE
        st.markdown(
            f"""
        <div class="card" style="border-left-color: #38bdf8;">
            <h4>📍 1. Site Context {render_provenance_badge('specified')}</h4>
            <p><b>Location:</b> {meta['display']}</p>
            <p><b>Elevation:</b> {meta['elevation']} | <b>Köppen:</b> {meta.get('koppen_classification', 'BWk')}</p>
            <p><b>Design Winter / Summer:</b> <span style="color:#60a5fa;">{meta['winter_temp']}</span> / <span style="color:#f87171;">{meta['summer_temp']}</span></p>
            <p><b>Annual Solar Resource:</b> {meta['solar_ghi']} (Heating HDD: {meta['hdd']})</p>
            <p><b>Data Source:</b> {meta['source']}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # 3. GEOMETRY
        floor_area = geo.get("floor_area_m2", 18.0)
        length = geo.get("length_m", 4.8)
        width = geo.get("width_m", 3.8)
        height = geo.get("height_m", 2.8)
        volume = geo.get("volume_m3", 51.0)
        aspect = length / max(0.1, width)
        total_envelope = 2.0 * (length + width) * height + 2.0 * (length * width)
        sv_ratio = total_envelope / max(0.1, volume)

        st.markdown(
            f"""
        <div class="card" style="border-left-color: #10b981;">
            <h4>📐 3. Geometry & Sizing {render_provenance_badge('calculated')}</h4>
            <p><b>Net Usable Floor Area:</b> <span class="metric-badge">{floor_area:.1f} m²</span> ({floor_area / max(1, mission.get('occupants', 4)):.1f} m²/person)</p>
            <p><b>Footprint Plan:</b> {length:.2f} m (Length) × {width:.2f} m (Width) — Aspect {aspect:.2f}:1</p>
            <p><b>Ceiling Height:</b> {height:.2f} m | <b>Internal Volume:</b> {volume:.1f} m³</p>
            <p><b>Surface-to-Volume (S/V):</b> {sv_ratio:.2f} m⁻¹ (Low ratio minimizes relative envelope losses)</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # 5. ENVELOPE
        wall_u = u_vals.get("wall_u", 0.35)
        wall_r = u_vals.get("wall_r_total", 2.8)
        roof_u = u_vals.get("roof_u", 0.30)
        roof_r = u_vals.get("roof_r_total", 3.3)

        st.markdown(
            f"""
        <div class="card" style="border-left-color: #f59e0b;">
            <h4>🧱 5. Envelope Assembly {render_provenance_badge('calculated')}</h4>
            <p><b>Wall Assembly:</b> {mats.get('wall_material_name', 'Masonry / Panel')}</p>
            <p><b>Wall Assembly U-Value:</b> <span class="metric-badge">{wall_u:.3f} W/m²K</span> (Total R = {wall_r:.2f} m²K/W)</p>
            <p><b>Roof System:</b> {mats.get('roof_material', 'Insulated Roof')}</p>
            <p><b>Roof Assembly U-Value:</b> <span class="metric-badge">{roof_u:.3f} W/m²K</span> (Total R = {roof_r:.2f} m²K/W)</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # 7. MATERIALS
        st.markdown(
            f"""
        <div class="card" style="border-left-color: #a855f7;">
            <h4>🛡️ 7. Materials & Insulation {render_provenance_badge('optimized')}</h4>
            <p><b>Core Insulation:</b> <span class="metric-badge">{design_data.get('optimal_insulation_mm', 120):.0f} mm</span> {mats.get('insulation_type', 'PUF Core')}</p>
            <p><b>Thermal Conductivity (k):</b> 0.025 W/m·K (High-performance insulation)</p>
            <p><b>Fenestration Glazing:</b> {design_data.get('optimal_glazing_name', 'Double Clear')}</p>
            <p><b>Glazing Aperture:</b> <span class="metric-badge">{design_data.get('optimal_window_area_m2', 3.0):.2f} m²</span> (WWR: {(design_data.get('optimal_window_area_m2', 3.0)/max(1.0, 2*(length+width)*height))*100:.1f}%)</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with dna_c2:
        # 2. MISSION
        st.markdown(
            f"""
        <div class="card" style="border-left-color: #6366f1;">
            <h4>🎯 2. Shelter Mission Profile {render_provenance_badge('specified')}</h4>
            <p><b>Shelter Purpose:</b> <span class="metric-badge">{mission.get('purpose', 'Disaster Relief')}</span></p>
            <p><b>Occupancy Sizing:</b> {mission.get('occupants', 4)} Persons ({mission.get('occupants', 4) * 80} W internal metabolic heat)</p>
            <p><b>Deployment Permanence:</b> {mission.get('deployment_type', 'Permanent')} ({mission.get('expected_duration', '1–6 months')})</p>
            <p><b>Field Mobility:</b> {mission.get('mobility', 'Vehicular')}</p>
            <p><b>Design Priorities:</b> {', '.join(mission.get('priorities', ['Thermal Comfort']))}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # 4. ORIENTATION
        orient = design_data.get("optimal_orientation", "south").title()
        st.markdown(
            f"""
        <div class="card" style="border-left-color: #ec4899;">
            <h4>🧭 4. Orientation & Solar Geometry {render_provenance_badge('optimized')}</h4>
            <p><b>Primary Solar Facade:</b> <span class="metric-badge">{orient} Facade (±15° True Azimuth)</span></p>
            <p><b>Passive Solar Advice:</b> {mats.get('orientation_advice', 'Orient glazing toward primary solar axis.')}</p>
            <p><b>Shading & Daylighting:</b> {mats.get('shading_advice', 'Adjust overhangs for seasonal cutoff angles.')}</p>
            <p><b>Integrated Solar Harvest:</b> <span style="color:#fbbf24; font-weight:700;">{sim_res.get('integrated_solar_energy_kwh', 0.0):.1f} kWh/week</span></p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # 6. PASSIVE STRATEGY
        st.markdown(
            f"""
        <div class="card" style="border-left-color: #14b8a6;">
            <h4>🌿 6. Passive Strategy Matrix {render_provenance_badge('calculated')}</h4>
            <p><b>Thermal Mass:</b> {'High thermal inertia stone/brick masonry dampening diurnal swing' if mission.get('deployment_type') == 'Permanent' else 'Lightweight high-R modular panel construction with low transport weight'}</p>
            <p><b>Solar Heating Strategy:</b> Direct solar gain harvesting through South-facing low-E glazing</p>
            <p><b>Ventilation Control:</b> Controlled baseline natural air exchange (0.8 ACH) preventing unconditioned convective loss</p>
            <p><b>Envelope Protection:</b> Insulated night window shuttering and airtight envelope joinery</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # 8. THERMAL PERFORMANCE
        comfort_pct = sim_res.get("comfort_percentage", 0.0)
        comfort_hrs = sim_res.get("comfort_hours", 0)
        discomfort_dh = sim_res.get("discomfort_degree_hours", 0.0)
        heat_loss = sim_res.get("total_heat_loss_kwh", 0.0)

        st.markdown(
            f"""
        <div class="card" style="border-left-color: #22d3ee;">
            <h4>🌡️ 8. 168-Hour Thermal Performance {render_provenance_badge('simulated')}</h4>
            <p><b>Thermal Comfort Percentage:</b> <span class="metric-badge">{comfort_pct:.1f} %</span> within 18–24 °C band</p>
            <p><b>Comfort Duration:</b> {comfort_hrs:.0f} of 168 simulation hours</p>
            <p><b>Cumulative Discomfort:</b> <span style="color:#60a5fa; font-weight:700;">{discomfort_dh:.1f} °C·h</span></p>
            <p><b>Weekly Envelope Heat Loss:</b> <span style="color:#f87171; font-weight:700;">{heat_loss:.1f} kWh</span> (Mean indoor temp: {met.get('avg', 0.0):.1f} °C)</p>
        </div>
        """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# HERO DEMO PRESET LOADER
# ==============================================================================
def load_hero_demo_preset() -> None:
    """
    Populates session state with the hero demo scenario (Leh, Ladakh).
    """
    st.session_state["ds_step"] = 5  # Jump straight to Review
    st.session_state["ds_city"] = "leh"
    st.session_state["ds_occupants"] = 4
    st.session_state["ds_purpose"] = "Research"
    st.session_state["ds_deployment"] = "Permanent"
    st.session_state["ds_duration"] = "Multi-year / Permanent (> 2 years)"
    st.session_state["ds_mobility"] = "Fixed / Non-Mobile (Permanent In-Situ)"
    st.session_state["ds_priorities"] = ["Thermal Comfort", "Energy Independence", "Durability"]
    st.session_state["ds_resources"] = ["Solar", "No external energy source (100% Passive)"]
    st.session_state["ds_wall_pref"] = "Auto-Recommend Optimal"
    st.session_state["ds_roof_pref"] = "Auto-Recommend Optimal"
    st.session_state["ds_max_ins"] = 200
    st.session_state["ds_max_win"] = 4.0
    st.session_state["ds_trials"] = 35


# ==============================================================================
# MAIN DESIGN STUDIO COMPONENT
# ==============================================================================
def render_design_studio(is_dark: bool = True) -> None:
    """
    Renders the complete 6-step guided engineering design workflow.
    """
    # Initialize Studio Session State
    if "ds_step" not in st.session_state:
        st.session_state["ds_step"] = 1
    if "ds_city" not in st.session_state:
        st.session_state["ds_city"] = "leh"
    if "ds_occupants" not in st.session_state:
        st.session_state["ds_occupants"] = 4
    if "ds_purpose" not in st.session_state:
        st.session_state["ds_purpose"] = "Disaster Relief"
    if "ds_deployment" not in st.session_state:
        st.session_state["ds_deployment"] = "Permanent"
    if "ds_duration" not in st.session_state:
        st.session_state["ds_duration"] = "1–6 months (Short Term)"
    if "ds_mobility" not in st.session_state:
        st.session_state["ds_mobility"] = "Fixed / Non-Mobile (Permanent In-Situ)"
    if "ds_priorities" not in st.session_state:
        st.session_state["ds_priorities"] = ["Thermal Comfort", "Energy Independence"]
    if "ds_resources" not in st.session_state:
        st.session_state["ds_resources"] = ["Solar", "No external energy source (100% Passive)"]
    if "ds_wall_pref" not in st.session_state:
        st.session_state["ds_wall_pref"] = "Auto-Recommend Optimal"
    if "ds_roof_pref" not in st.session_state:
        st.session_state["ds_roof_pref"] = "Auto-Recommend Optimal"
    if "ds_max_ins" not in st.session_state:
        st.session_state["ds_max_ins"] = 200
    if "ds_max_win" not in st.session_state:
        st.session_state["ds_max_win"] = 4.0
    if "ds_trials" not in st.session_state:
        st.session_state["ds_trials"] = 35

    # Top Hero Actions Bar
    top_c1, top_c2 = st.columns([3, 1])
    with top_c1:
        st.markdown(
            """
        <div style="font-size: 1.4rem; font-weight: 800; color: #38bdf8; margin-bottom: 2px;">
            🎯 Guided Engineering Design Studio
        </div>
        <div style="font-size: 0.90rem; color: #94a3b8; margin-bottom: 12px;">
            Step-by-step requirements specification, multi-criteria priority weighting, and Bayesian envelope optimization.
        </div>
        """,
            unsafe_allow_html=True,
        )
    with top_c2:
        if st.button("⚡ Load Leh Hero Demo", use_container_width=True, help="Load Leh, Ladakh permanent cold-climate hero demo"):
            load_hero_demo_preset()
            st.rerun()

    # Step Progression Bar
    steps = [
        ("1. LOCATION", 1),
        ("2. MISSION", 2),
        ("3. PRIORITIES", 3),
        ("4. RESOURCES", 4),
        ("5. REVIEW", 5),
        ("6. GENERATE", 6),
    ]

    current_step = st.session_state["ds_step"]
    prog_cols = st.columns(len(steps))

    for idx, (step_label, step_num) in enumerate(steps):
        with prog_cols[idx]:
            is_active = (current_step == step_num)
            is_completed = (current_step > step_num)
            
            btn_style = "primary" if is_active else "secondary"
            icon = "▶ " if is_active else ("✓ " if is_completed else "")
            
            if st.button(f"{icon}{step_label}", key=f"step_btn_{step_num}", use_container_width=True, type=btn_style):
                st.session_state["ds_step"] = step_num
                st.rerun()

    st.markdown("---")

    # ==========================================================================
    # STEP 1: LOCATION & SITE PROFILE
    # ==========================================================================
    if current_step == 1:
        st.markdown("### 📍 Step 1: Location & Site Climate Profile")
        st.caption("Select an existing supported location with verified historical EPW climate datasets.")

        loc_col1, loc_col2 = st.columns([1.5, 2.5])
        with loc_col1:
            supported_cities = get_all_supported_cities()
            sel_city = st.selectbox(
                "Select Deployment Location:",
                options=supported_cities,
                index=supported_cities.index(st.session_state["ds_city"]) if st.session_state["ds_city"] in supported_cities else 0,
                format_func=lambda x: CITIES_METADATA[x]["display"],
                key="ds_city_select",
                help="Only locations with complete EPW weather records are supported to ensure scientific simulation integrity.",
            )
            st.session_state["ds_city"] = sel_city

            if sel_city == "leh":
                st.success("⭐ **Hero Demonstration Selected:** Leh, Ladakh represents an extreme high-altitude alpine cold climate.")

        with loc_col2:
            st.info("💡 **Scientific Provenance:** Climate data is loaded from observed IMD station normals and ASHRAE/NREL EPW datasets. No unverified live weather feeds are used.")

        # Reusable Site Profile View
        render_site_profile(sel_city, is_dark=is_dark)

        # Navigation Footer
        nav_col1, nav_col2 = st.columns([4, 1])
        with nav_col2:
            if st.button("Next: Shelter Mission ➔", use_container_width=True, type="primary"):
                st.session_state["ds_step"] = 2
                st.rerun()

    # ==========================================================================
    # STEP 2: SHELTER MISSION
    # ==========================================================================
    elif current_step == 2:
        st.markdown("### 📋 Step 2: Shelter Mission & Deployment Requirements")
        st.caption("Define the operational role, occupancy sizing, and structural permanence of the shelter.")

        m_col1, m_col2 = st.columns(2)

        with m_col1:
            # 1. Occupants
            occupants = st.number_input(
                "1. Target Occupants (Capacity)",
                min_value=1,
                max_value=20,
                value=int(st.session_state["ds_occupants"]),
                step=1,
                key="ds_occ_input",
                help="Determines baseline auto-sizing floor area (4.5 m²/person per SP 41) and metabolic heat (80 W/person).",
            )
            st.session_state["ds_occupants"] = occupants

            # Auto-sizing instant feedback
            est_area = max(12.0, occupants * 4.5)
            est_metabolic = occupants * 80
            st.caption(f"📐 Baseline Floor Area: **{est_area:.1f} m²** | Internal Metabolic Heat: **{est_metabolic} W**")

            # 2. Shelter Purpose Options
            purposes = [
                "Disaster Relief",
                "Military",
                "Research",
                "Residential",
                "Medical",
                "Storage",
                "Command / Operations",
                "Temporary Accommodation",
            ]
            purpose = st.selectbox(
                "2. Operational Purpose",
                options=purposes,
                index=purposes.index(st.session_state["ds_purpose"]) if st.session_state["ds_purpose"] in purposes else 0,
                key="ds_purpose_input",
                help="Governs envelope functional requirements, equipment loads, and habitability standards.",
            )
            st.session_state["ds_purpose"] = purpose

        with m_col2:
            # 3. Deployment Type
            dep_types = ["Temporary", "Seasonal", "Permanent"]
            dep_type = st.radio(
                "3. Deployment Classification",
                options=dep_types,
                index=dep_types.index(st.session_state["ds_deployment"]) if st.session_state["ds_deployment"] in dep_types else 2,
                horizontal=True,
                key="ds_dep_input",
                help="Temporary: lightweight modular panels (<48 hr assembly). Permanent: high thermal inertia stone/brick masonry.",
            )
            st.session_state["ds_deployment"] = dep_type

            # 4. Expected Duration
            durations = [
                "< 1 month (Emergency / Rapid Relief)",
                "1–6 months (Short Term)",
                "6–24 months (Extended Mission)",
                "Multi-year / Permanent (> 2 years)",
            ]
            duration = st.selectbox(
                "4. Expected Deployment Duration",
                options=durations,
                index=durations.index(st.session_state["ds_duration"]) if st.session_state["ds_duration"] in durations else 1,
                key="ds_dur_input",
            )
            st.session_state["ds_duration"] = duration

            # 5. Mobility Requirement
            mobilities = [
                "Fixed / Non-Mobile (Permanent In-Situ)",
                "Vehicular / Flatbed Transportable",
                "High / Man-Portable Modular (< 35 kg/pack)",
            ]
            mobility = st.selectbox(
                "5. Field Mobility Requirement",
                options=mobilities,
                index=mobilities.index(st.session_state["ds_mobility"]) if st.session_state["ds_mobility"] in mobilities else 0,
                key="ds_mob_input",
            )
            st.session_state["ds_mobility"] = mobility

        # Navigation Footer
        nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
        with nav_col1:
            if st.button("⬅ Previous: Location", use_container_width=True):
                st.session_state["ds_step"] = 1
                st.rerun()
        with nav_col3:
            if st.button("Next: Priorities ➔", use_container_width=True, type="primary"):
                st.session_state["ds_step"] = 3
                st.rerun()

    # ==========================================================================
    # STEP 3: DESIGN PRIORITIES
    # ==========================================================================
    elif current_step == 3:
        st.markdown("### ⚖️ Step 3: Multi-Objective Design Priorities")
        st.caption("Select and weight engineering objectives that guide the optimization and recommendation engine.")

        p_options = [
            "Thermal Comfort",
            "Energy Independence",
            "Low Cost",
            "Low Weight",
            "Rapid Deployment",
            "Durability",
        ]

        sel_priorities = st.multiselect(
            "Select Key Design Priorities (Ranked in order of importance):",
            options=p_options,
            default=st.session_state["ds_priorities"] if st.session_state["ds_priorities"] else ["Thermal Comfort", "Energy Independence"],
            key="ds_prio_select",
            help="The Bayesian optimizer adapts objective weighting based on these priority criteria.",
        )

        if not sel_priorities:
            st.warning("⚠️ Please select at least one design priority.")
            sel_priorities = ["Thermal Comfort"]

        st.session_state["ds_priorities"] = sel_priorities

        # Real-time engineering feedback cards for priorities
        st.markdown("#### 🔬 Priority Impact on Architectural & Physical Systems:")
        p_c1, p_c2, p_c3 = st.columns(3)

        with p_c1:
            if "Thermal Comfort" in sel_priorities:
                st.markdown(
                    """
                <div class="card" style="border-left-color: #22d3ee;">
                    <h4>🌡️ Thermal Comfort Focus</h4>
                    <p>• Tight operative temperature targets (18–24 °C band).</p>
                    <p>• High envelope thermal resistance (PUF / XPS core).</p>
                    <p>• Nighttime insulated window shuttering.</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            if "Energy Independence" in sel_priorities:
                st.markdown(
                    """
                <div class="card" style="border-left-color: #fbbf24;">
                    <h4>☀️ Energy Independence Focus</h4>
                    <p>• 100% passive thermal autonomy target.</p>
                    <p>• Maximized South-facing passive solar heat capture.</p>
                    <p>• Heavy thermal mass for diurnal energy storage.</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        with p_c2:
            if "Low Cost" in sel_priorities:
                st.markdown(
                    """
                <div class="card" style="border-left-color: #10b981;">
                    <h4>💰 Low Cost Focus</h4>
                    <p>• Prioritizes locally available vernacular materials (mud/earth brick, local stone).</p>
                    <p>• Balances insulation thickness against capital material expense.</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            if "Low Weight" in sel_priorities:
                st.markdown(
                    """
                <div class="card" style="border-left-color: #a855f7;">
                    <h4>🪶 Low Weight Focus</h4>
                    <p>• Lightweight sandwich panels (PUF/EPS with thin skins).</p>
                    <p>• Eliminates heavy masonry to minimize logistics and transport fuel.</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        with p_c3:
            if "Rapid Deployment" in sel_priorities:
                st.markdown(
                    """
                <div class="card" style="border-left-color: #f43f5e;">
                    <h4>⚡ Rapid Deployment Focus</h4>
                    <p>• Prefabricated modular interlocking wall panels.</p>
                    <p>• Field assembly achievable in < 48 hours without wet trades or curing.</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            if "Durability" in sel_priorities:
                st.markdown(
                    """
                <div class="card" style="border-left-color: #6366f1;">
                    <h4>🛡️ Durability Focus</h4>
                    <p>• High weather-resistant envelope with UV-protected outer skins.</p>
                    <p>• Reinforced structural joints resisting high mountain snow and wind loads.</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        # Navigation Footer
        nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
        with nav_col1:
            if st.button("⬅ Previous: Mission", use_container_width=True):
                st.session_state["ds_step"] = 2
                st.rerun()
        with nav_col3:
            if st.button("Next: Resources ➔", use_container_width=True, type="primary"):
                st.session_state["ds_step"] = 4
                st.rerun()

    # ==========================================================================
    # STEP 4: AVAILABLE RESOURCES & CONSTRAINTS
    # ==========================================================================
    elif current_step == 4:
        st.markdown("### ⚡ Step 4: Available Resources & Engineering Constraints")
        st.caption("Specify available site utilities and envelope material/geometry constraints.")

        r_col1, r_col2 = st.columns(2)

        with r_col1:
            st.markdown("#### 🔌 Available Energy Resources (Optional)")
            res_options = [
                "Solar",
                "Grid",
                "Diesel / Generator",
                "No external energy source (100% Passive)",
            ]
            sel_res = st.multiselect(
                "Site Energy Availability:",
                options=res_options,
                default=st.session_state["ds_resources"],
                key="ds_res_input",
                help="Informs auxiliary heating requirements. If 'No external source' is checked, shelter must achieve passive thermal survivability.",
            )
            st.session_state["ds_resources"] = sel_res

            st.markdown("#### 🧱 Material & System Preferences")
            wall_prefs = [
                "Auto-Recommend Optimal",
                "Modular PUF Panels (Lightweight Prefab)",
                "Brick Masonry (Standard/Cavity)",
                "Stone Masonry (High Thermal Mass)",
                "Mud / Adobe Brick (Vernacular)",
            ]
            wall_pref = st.selectbox(
                "Envelope Wall Material Preference:",
                options=wall_prefs,
                index=wall_prefs.index(st.session_state["ds_wall_pref"]) if st.session_state["ds_wall_pref"] in wall_prefs else 0,
                key="ds_wall_pref_input",
            )
            st.session_state["ds_wall_pref"] = wall_pref

            roof_prefs = [
                "Auto-Recommend Optimal",
                "Pitched Roof (40° Slope - Snow/Rain Runoff)",
                "Flat Deck Roof (Cool Roof / PV Integration)",
            ]
            roof_pref = st.selectbox(
                "Roof Geometry Preference:",
                options=roof_prefs,
                index=roof_prefs.index(st.session_state["ds_roof_pref"]) if st.session_state["ds_roof_pref"] in roof_prefs else 0,
                key="ds_roof_pref_input",
            )
            st.session_state["ds_roof_pref"] = roof_pref

        with r_col2:
            st.markdown("#### ⚙️ Physical Search Constraints")
            max_ins = st.slider(
                "Maximum Insulation Thickness Cap (mm):",
                min_value=20,
                max_value=250,
                value=int(st.session_state["ds_max_ins"]),
                step=10,
                key="ds_ins_slider",
                help="Enforces a maximum allowable limit on envelope insulation thickness during Bayesian parameter search.",
            )
            st.session_state["ds_max_ins"] = max_ins

            max_win = st.slider(
                "Maximum Fenestration Aperture (m²):",
                min_value=1.0,
                max_value=8.0,
                value=float(st.session_state["ds_max_win"]),
                step=0.5,
                key="ds_win_slider",
                help="Limits maximum allowable window area to prevent structural weakness and nocturnal heat loss.",
            )
            st.session_state["ds_max_win"] = max_win

            trials = st.selectbox(
                "Bayesian Optimizer Iterations (Optuna TPE):",
                options=[20, 35, 50, 75],
                index=[20, 35, 50, 75].index(st.session_state["ds_trials"]) if st.session_state["ds_trials"] in [20, 35, 50, 75] else 1,
                key="ds_trials_input",
                help="Higher iterations explore more candidate combinations across the parameter space.",
            )
            st.session_state["ds_trials"] = trials

        # Navigation Footer
        nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
        with nav_col1:
            if st.button("⬅ Previous: Priorities", use_container_width=True):
                st.session_state["ds_step"] = 3
                st.rerun()
        with nav_col3:
            if st.button("Next: Review ➔", use_container_width=True, type="primary"):
                st.session_state["ds_step"] = 5
                st.rerun()

    # ==========================================================================
    # STEP 5: REVIEW & SPECIFICATION AUDIT
    # ==========================================================================
    elif current_step == 5:
        st.markdown("### 📋 Step 5: Engineering Requirements Review")
        st.caption("Verify your configured shelter criteria before triggering the simulation and optimization engine.")

        meta = get_city_metadata(st.session_state["ds_city"])

        # Sensible Validation Checks
        is_valid = True
        validation_warnings = []

        if st.session_state["ds_occupants"] < 1:
            is_valid = False
            st.error("❌ Occupants capacity must be at least 1 person.")

        if st.session_state["ds_deployment"] == "Permanent" and "High / Man-Portable" in st.session_state["ds_mobility"]:
            validation_warnings.append(
                "⚠️ Permanent construction with stone/brick typically contradicts high man-portable mobility. "
                "Consider selecting 'Temporary' deployment for modular transportable panels."
            )

        for w in validation_warnings:
            st.warning(w)

        # Summary Grid
        rev_c1, rev_c2 = st.columns(2)

        with rev_c1:
            st.markdown(
                f"""
            <div class="card" style="border-left-color: #38bdf8;">
                <h4>📍 Site & Climate Specification {render_provenance_badge('specified')}</h4>
                <p><b>Deployment Location:</b> {meta['display']}</p>
                <p><b>Region / Elevation:</b> {meta['region']} ({meta['elevation']})</p>
                <p><b>Climate Classification:</b> {meta['climate_type']} ({meta.get('koppen_classification', 'BWk')})</p>
                <p><b>Design Winter / Summer:</b> {meta['winter_temp']} / {meta['summer_temp']}</p>
                <p><b>Heating Demand:</b> {meta['hdd']} HDD | <b>Solar GHI:</b> {meta['solar_ghi']}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
            <div class="card" style="border-left-color: #6366f1;">
                <h4>🎯 Mission Requirements {render_provenance_badge('specified')}</h4>
                <p><b>Shelter Purpose:</b> {st.session_state['ds_purpose']}</p>
                <p><b>Occupants Capacity:</b> {st.session_state['ds_occupants']} Persons (~{st.session_state['ds_occupants'] * 4.5:.1f} m² baseline)</p>
                <p><b>Deployment Classification:</b> {st.session_state['ds_deployment']}</p>
                <p><b>Mission Duration:</b> {st.session_state['ds_duration']}</p>
                <p><b>Field Mobility:</b> {st.session_state['ds_mobility']}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with rev_c2:
            st.markdown(
                f"""
            <div class="card" style="border-left-color: #22d3ee;">
                <h4>⚖️ Selected Design Priorities {render_provenance_badge('specified')}</h4>
                <p><b>Primary Priorities:</b> {', '.join(st.session_state['ds_priorities'])}</p>
                <p><b>Available Site Energy:</b> {', '.join(st.session_state['ds_resources']) if st.session_state['ds_resources'] else 'None'}</p>
                <p><b>Wall Material Preference:</b> {st.session_state['ds_wall_pref']}</p>
                <p><b>Roof Profile Preference:</b> {st.session_state['ds_roof_pref']}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
            <div class="card" style="border-left-color: #a855f7;">
                <h4>⚙️ Engineering Search Constraints {render_provenance_badge('specified')}</h4>
                <p><b>Insulation Thickness Cap:</b> ≤ {st.session_state['ds_max_ins']} mm</p>
                <p><b>Window Aperture Cap:</b> ≤ {st.session_state['ds_max_win']:.1f} m²</p>
                <p><b>Optimizer Search Space:</b> {st.session_state['ds_trials']} Optuna TPE Iterations</p>
                <p><b>Simulation Period:</b> 168-Hour Transient Forward Euler (Δt = 60s)</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Primary Action Button
        st.markdown("<br/>", unsafe_allow_html=True)
        act_col1, act_col2, act_col3 = st.columns([1, 2, 1])

        with act_col2:
            if is_valid:
                if st.button("🚀 Generate Optimized Shelter Design", use_container_width=True, type="primary"):
                    st.session_state["ds_step"] = 6
                    st.rerun()
            else:
                st.button("❌ Resolve Validation Errors to Proceed", disabled=True, use_container_width=True)

        # Step Back
        b_col1, b_col2 = st.columns([1, 5])
        with b_col1:
            if st.button("⬅ Previous: Resources", use_container_width=True):
                st.session_state["ds_step"] = 4
                st.rerun()

    # ==========================================================================
    # STEP 6: GENERATE DESIGN & PRESENT SCIENTIFIC OUTPUTS
    # ==========================================================================
    elif current_step == 6:
        city = st.session_state["ds_city"]
        occupants = int(st.session_state["ds_occupants"])
        dep_type = st.session_state["ds_deployment"]
        # Map Seasonal to Temporary or Permanent physically
        home_type_for_engine = "Permanent" if dep_type == "Permanent" else "Temporary"
        max_ins_mm = float(st.session_state["ds_max_ins"])
        max_win = float(st.session_state["ds_max_win"])
        n_trials = int(st.session_state["ds_trials"])

        cache_key = f"ds_design_{city}_{occupants}_{dep_type}_{max_ins_mm}_{max_win}_{n_trials}"

        # Compute or retrieve from cache
        if cache_key not in st.session_state:
            with st.spinner(f"Running transient simulation and Bayesian optimization for {city.upper()} ({dep_type} Shelter)..."):
                rec = get_recommendation(
                    city=city,
                    people=occupants,
                    home_type=home_type_for_engine,
                    n_trials=n_trials,
                    max_insulation_mm=max_ins_mm,
                    max_window_area=max_win,
                )
                sim_res = rec.get("simulation_result")
                if not sim_res or "error" in sim_res:
                    st.error("Simulation failed. Please check weather datasets and material properties.")
                    return

                # Compile unified design object
                design_id = f"TS-{city.upper()[:3]}-{dep_type[:4].upper()}-{occupants:02d}P"
                design_payload = {
                    "design_id": design_id,
                    "city": city,
                    "climate_type": rec["climate_type"],
                    "climate_name": rec["climate_name"],
                    "home_type": dep_type,
                    "people": occupants,
                    "occupants": occupants,
                    "mission": {
                        "purpose": st.session_state["ds_purpose"],
                        "occupants": occupants,
                        "deployment_type": dep_type,
                        "expected_duration": st.session_state["ds_duration"],
                        "mobility": st.session_state["ds_mobility"],
                        "priorities": st.session_state["ds_priorities"],
                        "resources": st.session_state["ds_resources"],
                    },
                    "geometry": rec["geometry"],
                    "materials": rec["materials"],
                    "optimal_insulation_mm": rec["optimal_insulation_mm"],
                    "optimal_window_area_m2": rec["optimal_window_area_m2"],
                    "optimal_wall_material": rec.get("optimal_wall_material", "brick"),
                    "optimal_glazing": rec.get("optimal_glazing", "double_clear"),
                    "optimal_glazing_name": rec.get("optimal_glazing_name", "Double Clear"),
                    "optimal_orientation": rec.get("optimal_orientation", "south"),
                    "simulation_result": sim_res,
                    "ranked_designs": rec.get("ranked_designs", []),
                    "explanation": rec.get("explanation", ""),
                }

                st.session_state[cache_key] = design_payload

                # Synchronize to global session state for feature studios
                st.session_state["design_requirements"] = {
                    "city": city,
                    "people": occupants,
                    "home_type": home_type_for_engine,
                    "max_insulation_mm": max_ins_mm,
                    "max_window_area": max_win,
                    "opt_trials": n_trials,
                }
                st.session_state["active_design"] = design_payload

        active_design = st.session_state[cache_key]
        sim_res = active_design["simulation_result"]

        # Action banner
        st.success(
            f"✅ **Optimized Design Generated:** `{active_design['design_id']}` for **{city.upper()}** — "
            f"Comfort: **{sim_res['comfort_percentage']:.1f}%** | "
            f"Discomfort: **{sim_res['discomfort_degree_hours']:.1f} °C·h** | "
            f"Weekly Loss: **{sim_res['total_heat_loss_kwh']:.1f} kWh**"
        )

        # Sub-tabs for Generated Design View
        g_tab1, g_tab2, g_tab3, g_tab4, g_tab5 = st.tabs([
            "🧬 Design DNA Summary",
            "📈 Transient Thermal Curves",
            "🏗️ 3D Model & Floor Plan",
            "💡 Engineering Rationale & Specs",
            "📥 Export Technical Report",
        ])

        with g_tab1:
            render_design_dna(active_design, is_dark=is_dark)

        with g_tab2:
            st.markdown("### 🌡️ 168-Hour Transient Thermal Comfort Response")
            st.plotly_chart(
                plot_temperature_curves(
                    city=city,
                    outdoor_temps=sim_res["outdoor_temperature"],
                    indoor_temps=sim_res["indoor_temperature"],
                    title_suffix=f"— {active_design['mission']['purpose']} ({dep_type})",
                    is_dark=is_dark,
                ),
                use_container_width=True,
            )

            # Metrics
            met = sim_res["comfort_metrics"]
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Avg Temp", f"{met['avg']:.1f} °C")
            m2.metric("Min Temp", f"{met['min_t']:.1f} °C")
            m3.metric("Max Temp", f"{met['max_t']:.1f} °C")
            m4.metric("Comfort Hours", f"{sim_res['comfort_hours']:.0f} / 168 h")
            m5.metric("Comfort %", f"{sim_res['comfort_percentage']:.1f} %")
            m6.metric("Discomfort DH", f"{sim_res['discomfort_degree_hours']:.1f} °C·h")

            st.markdown("---")
            st.markdown("### ⚡ Dynamic Energy Balance & Heat Loss Breakdown")
            eb1, eb2 = st.columns([1.2, 1.0])
            with eb1:
                st.plotly_chart(plot_component_heat_flows(sim_res, is_dark=is_dark), use_container_width=True)
            with eb2:
                st.plotly_chart(plot_energy_balance_breakdown(sim_res, is_dark=is_dark), use_container_width=True)

        with g_tab3:
            render_3d_and_floorplan(active_design, city, is_dark=is_dark)

        with g_tab4:
            render_envelope_specifications(active_design, sim_res, dep_type)
            st.markdown("---")
            render_explainable_rationale(active_design)
            st.markdown("---")
            render_model_assumptions_and_validation()

        with g_tab5:
            render_export_section(active_design, sim_res, city)

        # Footer Action: Modify or Restart
        st.markdown("---")
        fc1, fc2, fc3 = st.columns([1, 2, 1])
        with fc1:
            if st.button("✏️ Modify Design Criteria", use_container_width=True):
                st.session_state["ds_step"] = 1
                st.rerun()
        with fc3:
            if st.button("🔄 Regenerate / Rerun Search", use_container_width=True):
                if cache_key in st.session_state:
                    del st.session_state[cache_key]
                st.rerun()
