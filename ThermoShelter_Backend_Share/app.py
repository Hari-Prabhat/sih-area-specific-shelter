"""
================================================================================
THERMOSHELTER AI — Area-Specific Passive Shelter Design Platform
================================================================================
Scientific Bedrock: Transient Forward Euler 1D Heat Transfer & ISO 6946 Envelope Engine
Product Differentiator: Multi-Objective Bayesian Optimization & Explainable Recommendation
Target Region Hero Demo: High-Altitude Cold Climates (Leh, Ladakh) & Multi-Climatic Framework

Architecture:
    app.py  (UI orchestration only — no physics here)
        ↓
    components/* (rendering logic)
        ↓
    services/* (engineering models: climate, simulation, optimize, recommender)
        ↓
    simulation / optimization / physics results
================================================================================
"""

import os
import sys
import statistics
import streamlit as st

# ==============================================================================
# PATH SETUP
# ==============================================================================
CURRENT_DIR   = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR  = os.path.join(CURRENT_DIR, "services")
COMPONENTS_DIR = os.path.join(CURRENT_DIR, "components")

for path in [CURRENT_DIR, SERVICES_DIR, COMPONENTS_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

# ==============================================================================
# COMPONENT IMPORTS  (reuse every existing module — zero duplication of physics)
# ==============================================================================
from components.inputs import render_requirements_inputs, render_climate_info_card
from components.dashboard import render_simulation_dashboard
from components.feature_studio import (
    render_shelter_designer_studio,
    render_material_comparison_studio,
    render_multiple_shelter_models_studio,
    render_sensitivity_analysis_studio,
)
from components.comparison import render_baseline_vs_optimized_view
from components.recommendations import (
    render_envelope_specifications,
    render_ranked_candidate_designs,
    render_explainable_rationale,
)
from components.shelter_3d import render_3d_and_floorplan
from components.validation import render_model_assumptions_and_validation
from components.export import render_export_section, generate_markdown_report
from components.charts import (
    plot_temperature_curves,
    plot_solar_dynamics,
    plot_component_heat_flows,
    plot_energy_balance_breakdown,
    create_2d_floorplan,
)

from services.recommender import (
    get_recommendation,
    auto_size_shelter,
    recommend_materials,
    CLIMATE_MAPPING,
)
from services.climate_service import get_climate_data

# ==============================================================================
# PAGE CONFIG  (must be first Streamlit call)
# ==============================================================================
st.set_page_config(
    page_title="ThermoShelter | Engineering Platform",
    page_icon="🏕️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# GLOBAL CSS  — professional engineering dark theme
# ==============================================================================
st.markdown("""
<style>
    /* Card components */
    .card {
        background-color: #1e293b;
        border-radius: 10px; padding: 16px;
        border-left: 5px solid #38bdf8;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        margin-bottom: 1rem; color: #e2e8f0;
    }
    .card h4 { color: #38bdf8; margin-top:0; margin-bottom:8px; font-size:1.02rem; }
    .card p  { color: #cbd5e1; margin:4px 0; font-size:0.90rem; line-height:1.5; }
    .card b  { color: #f1f5f9; }
    .metric-badge { font-weight:700; color:#22d3ee; font-size:1.10rem; }

    /* Section headers */
    .section-hdr {
        font-size: 1.1rem; font-weight: 700; color: #38bdf8;
        border-bottom: 1px solid rgba(56,189,248,0.25);
        padding-bottom: 4px; margin-bottom: 12px; margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# UTILITY HELPERS
# ==============================================================================

def _hdr(text: str) -> None:
    """Render a blue section header line."""
    st.markdown(f'<div class="section-hdr">{text}</div>', unsafe_allow_html=True)


def _req_bar(req: dict) -> None:
    """Compact requirements status bar shown at the top of most pages."""
    from components.inputs import CITIES_METADATA
    meta = CITIES_METADATA.get(req["city"], {})
    disp = meta.get("display", req["city"].title())
    st.info(
        f"📍 **{disp}** · {req['people']} occupants · {req['home_type']} shelter  |  "
        "*Change via* **1 · Climate & Requirements**"
    )


def _rec_cache_key(req: dict) -> str:
    return (
        f"rec_{req['city']}_{req['people']}_{req['home_type']}_"
        f"{req.get('max_insulation_mm', 200.0)}_{req.get('max_window_area', 4.0)}_"
        f"{req.get('opt_trials', 35)}"
    )


def _ensure_rec(req: dict):
    """Run (or retrieve from cache) the full optimization for the current req."""
    key = _rec_cache_key(req)
    if key not in st.session_state:
        with st.spinner(
            f"⏳ Bayesian optimization for **{req['city'].upper()}** "
            f"({req['home_type']}, {req.get('opt_trials', 35)} trials)…"
        ):
            rec = get_recommendation(
                city=req["city"],
                people=req["people"],
                home_type=req["home_type"],
                n_trials=req.get("opt_trials", 35),
                max_insulation_mm=req.get("max_insulation_mm", 200.0),
                max_window_area=req.get("max_window_area", 4.0),
            )
        if not rec or not rec.get("simulation_result"):
            st.error("Optimization failed — check climate data and material availability.")
            return None
        if "error" in (rec.get("simulation_result") or {}):
            st.error("Simulation returned an error.")
            return None
        st.session_state[key] = rec
        st.success(
            f"✅ Optimized for **{req['city'].upper()}** — "
            f"Comfort: **{rec['simulation_result']['comfort_percentage']:.1f}%** | "
            f"Discomfort: **{rec['simulation_result']['discomfort_degree_hours']:.1f} °C·h**"
        )
    return st.session_state[key]


# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
NAV_ITEMS = [
    ("🏠  Dashboard",              "dashboard"),
    ("─────────────────────────",  None),
    ("1 · Climate & Requirements", "climate"),
    ("2 · Shelter Designer",       "shelter_designer"),
    ("3 · Simulation Dashboard",   "simulation"),
    ("4 · Optimization & Recs",    "optimization"),
    ("5 · Candidate Ranking",      "candidates"),
    ("6 · Baseline vs Optimized",  "baseline_vs_opt"),
    ("7 · Material Comparison",    "material_comparison"),
    ("8 · Shelter Archetypes",     "archetypes"),
    ("9 · Sensitivity Analysis",   "sensitivity"),
    ("10 · Analytical Validation", "validation"),
    ("11 · 3D Digital Twin",       "twin_3d"),
    ("12 · 2D Floorplan",          "floorplan_2d"),
    ("13 · Engineering Report",    "export"),
]

_nav_labels      = [label for label, _ in NAV_ITEMS if _ is not None]
_nav_label_to_id = {label: pid for label, pid in NAV_ITEMS if pid is not None}

with st.sidebar:
    st.markdown("## 🏕️ ThermoShelter")
    st.markdown(
        "<span style='color:#94a3b8;font-size:0.80rem;'>"
        "Area-Specific Passive Shelter Design<br>"
        "ISO 6946 · Optuna Bayesian Opt · Streamlit</span>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "🏠  Dashboard"

    chosen_label = st.radio(
        "Navigation",
        _nav_labels,
        index=_nav_labels.index(st.session_state["nav_page"])
        if st.session_state["nav_page"] in _nav_labels else 0,
        key="nav_radio",
        label_visibility="collapsed",
    )
    st.session_state["nav_page"] = chosen_label
    PAGE_ID = _nav_label_to_id.get(chosen_label, "dashboard")

    st.markdown("---")
    st.markdown(
        "<span style='color:#64748b;font-size:0.74rem;'>"
        "Member 1 · Climate Engine<br>"
        "Member 2 · Geometry · Materials · Passive<br>"
        "Member 3 · Simulation · Optimization<br>"
        "Integration · Full-stack Streamlit UI</span>",
        unsafe_allow_html=True,
    )


# ==============================================================================
# GLOBAL REQUIREMENTS  (persist across pages via session_state)
# ==============================================================================
if "global_req" not in st.session_state:
    st.session_state["global_req"] = {
        "city": "leh",
        "people": 4,
        "home_type": "Permanent",
        "max_insulation_mm": 200.0,
        "max_window_area": 4.0,
        "opt_trials": 35,
    }


# ==============================================================================
# PAGE FUNCTIONS
# ==============================================================================

# ── DASHBOARD ──────────────────────────────────────────────────────────────────
def page_dashboard() -> None:
    st.markdown(
        "<span style='font-size:1.7rem;font-weight:800;color:#38bdf8;'>"
        "🏕️ ThermoShelter Engineering Platform</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<span style='font-size:0.9rem;color:#94a3b8;'>"
        "Transient Building Physics · ISO 6946 · Bayesian Optimization · "
        "Area-Specific Passive Design for India</span>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    req     = st.session_state["global_req"]
    rec_key = _rec_cache_key(req)

    # Workflow overview
    _hdr("🗺️ Engineering Workflow")
    wf_cols = st.columns(6)
    steps = [
        ("1. CLIMATE",   "Location & EPW data"),
        ("2. DESIGN",    "Geometry & materials"),
        ("3. SIMULATE",  "168-hr transient"),
        ("4. OPTIMIZE",  "Bayesian search"),
        ("5. COMPARE",   "Baseline vs opt"),
        ("6. EXPORT",    "Markdown / JSON"),
    ]
    for col, (title, desc) in zip(wf_cols, steps):
        col.markdown(
            f"<div style='text-align:center;background:#1e293b;border-radius:8px;"
            f"padding:10px 4px;border-top:3px solid #38bdf8;'>"
            f"<b style='color:#38bdf8;font-size:0.80rem;'>{title}</b><br>"
            f"<span style='color:#94a3b8;font-size:0.74rem;'>{desc}</span></div>",
            unsafe_allow_html=True,
        )
    st.markdown("---")

    # Live metrics if optimized
    if rec_key in st.session_state:
        rec = st.session_state[rec_key]
        sim = rec["simulation_result"]
        geo = rec["geometry"]
        met = sim["comfort_metrics"]
        cl  = sim["component_heat_loss_kwh"]

        _hdr("📊 Current Design Summary")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Climate",        rec["climate_name"].split("/")[0].strip())
        m2.metric("Avg Indoor",     f"{met['avg']:.1f} °C")
        m3.metric("Comfort %",      f"{sim['comfort_percentage']:.1f} %")
        m4.metric("Discomfort DH",  f"{sim['discomfort_degree_hours']:.1f} °C·h")
        m5.metric("Solar Harvest",  f"{sim['integrated_solar_energy_kwh']:.2f} kWh")
        m6.metric("Weekly Loss",    f"{sim['total_heat_loss_kwh']:.1f} kWh")

        da, db = st.columns(2)
        with da:
            st.markdown("**🏗️ Shelter Configuration**")
            st.markdown(
                f"- **City:** {req['city'].upper()}  "
                f"· **Occupants:** {req['people']}\n"
                f"- **Floor Area:** {geo['floor_area_m2']:.1f} m²  "
                f"({geo['length_m']:.1f} m × {geo['width_m']:.1f} m)\n"
                f"- **Height:** {geo['height_m']:.1f} m  "
                f"| **Volume:** {geo['volume_m3']:.1f} m³\n"
                f"- **Wall U-Value:** {sim['u_values']['wall_u']:.3f} W/m²K\n"
                f"- **Insulation:** {rec['optimal_insulation_mm']:.0f} mm PUF\n"
                f"- **Window Area:** {rec['optimal_window_area_m2']:.2f} m²  "
                f"| **Glazing:** {rec.get('optimal_glazing_name','Double Clear')}"
            )
        with db:
            st.markdown("**⚡ Thermal Performance**")
            st.markdown(
                f"- **Comfort Hours:** {sim['comfort_hours']:.0f} / 168 h\n"
                f"- **Min Indoor:** {met['min_t']:.1f} °C  "
                f"| **Max Indoor:** {met['max_t']:.1f} °C\n"
                f"- **Wall Loss:** {cl['wall_loss_kwh']:.1f} kWh  "
                f"| **Roof Loss:** {cl['roof_loss_kwh']:.1f} kWh\n"
                f"- **Ventilation Loss:** {cl['ventilation_loss_kwh']:.1f} kWh\n"
                f"- **Orientation:** "
                f"{rec.get('optimal_orientation','south').title()}-facing facade"
            )

        st.markdown("---")
        st.markdown("**📈 168-Hour Temperature Preview**")
        st.plotly_chart(
            plot_temperature_curves(
                city=req["city"],
                outdoor_temps=sim["outdoor_temperature"],
                indoor_temps=sim["indoor_temperature"],
                title_suffix="— Dashboard Preview",
                is_dark=True,
            ),
            use_container_width=True,
        )

    else:
        st.info(
            "💡 **No simulation run yet.** Navigate to "
            "**1 · Climate & Requirements** to configure your project, "
            "then go to **4 · Optimization & Recs** to run the AI engine."
        )
        st.markdown("#### Quick-start")
        qs1, qs2 = st.columns([1, 2])
        with qs1:
            city_qs  = st.selectbox(
                "Climate Zone",
                ["leh", "jaisalmer", "chennai", "delhi", "bengaluru"],
                format_func=lambda x: {
                    "leh":       "🏔️ Leh (Alpine Cold)",
                    "jaisalmer": "🏜️ Jaisalmer (Hot-Dry)",
                    "chennai":   "🌊 Chennai (Humid)",
                    "delhi":     "🏙️ Delhi (Composite)",
                    "bengaluru": "🌳 Bengaluru (Moderate)",
                }[x],
                key="qs_city",
            )
            ppl_qs  = st.slider("Occupants", 1, 12, 4, key="qs_ppl")
            home_qs = st.radio("Shelter Type", ["Temporary", "Permanent"],
                               horizontal=True, key="qs_home")
        with qs2:
            st.markdown("&nbsp;")
            if st.button("🚀 Set & Go to Optimization", type="primary",
                         use_container_width=True):
                st.session_state["global_req"] = {
                    "city": city_qs, "people": ppl_qs,
                    "home_type": home_qs,
                    "max_insulation_mm": 200.0,
                    "max_window_area": 4.0,
                    "opt_trials": 35,
                }
                st.session_state["nav_page"] = "4 · Optimization & Recs"
                st.rerun()


# ── 1. CLIMATE & REQUIREMENTS ─────────────────────────────────────────────────
def page_climate() -> None:
    _hdr("1 · Climate & Requirements")
    st.caption(
        "Select deployment location, occupancy, and shelter permanence. "
        "All downstream modules use these parameters."
    )

    old_req = st.session_state["global_req"]
    req = render_requirements_inputs(
        default_city=old_req["city"],
        default_people=old_req["people"],
        default_home_type=old_req["home_type"],
    )

    # Invalidate cached simulations when requirements change
    if req != old_req:
        for k in list(st.session_state.keys()):
            if k.startswith(("rec_", "des_", "comp_", "mat_", "arch_", "sens_")):
                del st.session_state[k]
        st.session_state["global_req"] = req

    st.markdown("---")

    # Climate data preview
    _hdr("🌤️ Hourly Weather Data Preview (First 168 Hours)")
    climate_data = get_climate_data(req["city"])
    if "error" not in climate_data:
        temps = climate_data["hourly_temperature"][:168]
        cd1, cd2 = st.columns([3, 2])
        with cd1:
            st.plotly_chart(
                plot_temperature_curves(
                    city=req["city"],
                    outdoor_temps=temps,
                    indoor_temps=temps,
                    title_suffix="— Outdoor Ambient (EPW Reference)",
                    is_dark=True,
                ),
                use_container_width=True,
            )
        with cd2:
            st.markdown("**Dataset Statistics**")
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Mean", f"{statistics.mean(temps):.1f} °C")
            s2.metric("Min",  f"{min(temps):.1f} °C")
            s3.metric("Max",  f"{max(temps):.1f} °C")
            s4.metric("Hours", f"{len(climate_data['hourly_temperature'])}")
            st.markdown(
                "**Data Provenance**\n"
                f"- Lat: {climate_data.get('latitude', 'N/A')}  "
                f"| Lon: {climate_data.get('longitude', 'N/A')}\n"
                "- Source: IMD / NREL NSRDB / ASHRAE EPW\n"
                "- Format: EnergyPlus Weather (EPW) or CSV fallback"
            )
    else:
        st.warning(f"⚠️ {climate_data['error']}")

    st.markdown("---")
    _hdr("📋 Active Engineering Constraints")
    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("Max Insulation Cap", f"{req.get('max_insulation_mm', 200):.0f} mm")
    rc2.metric("Max Window Area",    f"{req.get('max_window_area', 4.0):.1f} m²")
    rc3.metric("Optimizer Trials",   f"{req.get('opt_trials', 35)} trials")


# ── 2. SHELTER DESIGNER ───────────────────────────────────────────────────────
def page_shelter_designer() -> None:
    _hdr("2 · Shelter Designer")
    st.caption(
        "Full design studio: auto-sizing, material & passive system selection, "
        "168-hr transient simulation, 3D model, and export."
    )
    render_shelter_designer_studio(st.session_state["global_req"], is_dark=True)


# ── 3. SIMULATION DASHBOARD ───────────────────────────────────────────────────
def page_simulation() -> None:
    _hdr("3 · Simulation Dashboard")
    req     = st.session_state["global_req"]
    rec_key = _rec_cache_key(req)

    if rec_key not in st.session_state:
        st.info(
            "Simulation not yet computed. Run **4 · Optimization & Recs** first."
        )
        if st.button("⚡ Run Now", type="primary"):
            if _ensure_rec(req):
                st.rerun()
        return

    rec = st.session_state[rec_key]
    sim = rec["simulation_result"]
    _req_bar(req)

    t_temp, t_solar, t_heat, t_energy = st.tabs([
        "🌡️ Temperature Curves",
        "☀️ Solar Dynamics",
        "⚡ Component Heat Flows",
        "📊 Energy Balance",
    ])

    with t_temp:
        st.plotly_chart(
            plot_temperature_curves(
                city=req["city"],
                outdoor_temps=sim["outdoor_temperature"],
                indoor_temps=sim["indoor_temperature"],
                title_suffix=f"— {req['home_type']} Shelter",
                is_dark=True,
            ),
            use_container_width=True,
        )
        met = sim["comfort_metrics"]
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Avg Indoor",    f"{met['avg']:.2f} °C")
        c2.metric("Min Indoor",    f"{met['min_t']:.2f} °C")
        c3.metric("Max Indoor",    f"{met['max_t']:.2f} °C")
        c4.metric("Comfort Hours", f"{sim['comfort_hours']:.0f} / 168 h")
        c5.metric("Comfort %",     f"{sim['comfort_percentage']:.1f} %")
        c6.metric("Discomfort DH", f"{sim['discomfort_degree_hours']:.1f} °C·h")
        status = sim.get("comfort_status", "comfortable")
        if status == "comfortable":
            st.success("🌿 **Optimal Thermal Comfort** — indoor temperatures maintained within 18–24 °C")
        elif "cold" in str(status).lower():
            st.warning("❄️ **Heating Required** — average indoor below 18 °C")
        else:
            st.warning("🔥 **Cooling / Shading Advised** — average indoor above 24 °C")

    with t_solar:
        sc1, sc2, sc3, sc4 = st.columns(4)
        eff = (sim["integrated_solar_energy_kwh"] /
               max(0.001, sim["integrated_incident_solar_kwh"])) * 100.0
        sc1.metric("Solar Gain",       f"{sim['integrated_solar_energy_kwh']:.2f} kWh")
        sc2.metric("Total Incident",   f"{sim['integrated_incident_solar_kwh']:.2f} kWh")
        sc3.metric("Solar Efficiency", f"{eff:.1f} %")
        sc4.metric("Peak Gain",        f"{max(sim['solar_thermal_gain']):.1f} W")
        st.plotly_chart(plot_solar_dynamics(sim, is_dark=True), use_container_width=True)

    with t_heat:
        cl = sim["component_heat_loss_kwh"]
        h1, h2, h3, h4, h5, h6, h7 = st.columns(7)
        h1.metric("Total Loss",     f"{sim['total_heat_loss_kwh']:.1f} kWh")
        h2.metric("Wall Loss",      f"{cl['wall_loss_kwh']:.1f} kWh")
        h3.metric("Roof Loss",      f"{cl['roof_loss_kwh']:.1f} kWh")
        h4.metric("Floor Loss",     f"{cl['floor_loss_kwh']:.1f} kWh")
        h5.metric("Glazing Loss",   f"{cl['window_loss_kwh']:.1f} kWh")
        h6.metric("Vent Loss",      f"{cl['ventilation_loss_kwh']:.1f} kWh")
        h7.metric("Radiation Loss", f"{cl['radiation_loss_kwh']:.1f} kWh")
        st.plotly_chart(plot_component_heat_flows(sim, is_dark=True), use_container_width=True)

    with t_energy:
        st.plotly_chart(plot_energy_balance_breakdown(sim, is_dark=True), use_container_width=True)


# ── 4. OPTIMIZATION & RECOMMENDATIONS ────────────────────────────────────────
def page_optimization() -> None:
    _hdr("4 · Optimization & Recommendations")
    st.caption(
        "Multi-objective Bayesian (Optuna TPE) optimization selects the envelope "
        "configuration minimising discomfort degree-hours and envelope heat loss."
    )
    req     = st.session_state["global_req"]
    rec_key = _rec_cache_key(req)
    _req_bar(req)

    if rec_key not in st.session_state:
        if st.button("🚀 Run Bayesian Optimization", type="primary", use_container_width=True):
            if _ensure_rec(req):
                st.rerun()
        return

    rec = st.session_state[rec_key]
    sim = rec["simulation_result"]

    t1, t2, t3 = st.tabs([
        "🏆 Envelope Specifications",
        "💡 Design Rationale",
        "🌿 Passive Design Explanations",
    ])

    with t1:
        render_envelope_specifications(rec, sim, req["home_type"])
        st.markdown("---")
        _hdr("🌡️ Thermal Comfort Metrics")
        met = sim["comfort_metrics"]
        tm1, tm2, tm3, tm4, tm5 = st.columns(5)
        tm1.metric("Avg Indoor",    f"{met['avg']:.2f} °C")
        tm2.metric("Min Indoor",    f"{met['min_t']:.2f} °C")
        tm3.metric("Max Indoor",    f"{met['max_t']:.2f} °C")
        tm4.metric("Comfort Hours", f"{sim['comfort_hours']:.0f} / 168 h")
        tm5.metric("Comfort %",     f"{sim['comfort_percentage']:.1f} %")

    with t2:
        render_explainable_rationale(rec)

    with t3:
        mats = rec["materials"]
        st.markdown("### 🧭 Passive Solar Strategy")
        st.info(mats.get("orientation_advice", "Maximise south-facing glazing for passive solar gain."))
        st.markdown("### 🌿 Shading Design Guidance")
        st.info(mats.get("shading_advice", "Fixed horizontal overhangs sized to block summer sun."))
        if "passive_cooling" in mats:
            st.markdown("### 💨 Passive Cooling Approach")
            st.info(mats["passive_cooling"])
        st.markdown("### 🧱 Thermal Mass & Material Summary")
        st.markdown(
            f"- **Wall Material:** {mats.get('wall_material_name', 'N/A')}\n"
            f"- **Roof System:** {mats.get('roof_material', 'N/A')}\n"
            f"- **Insulation Type:** {mats.get('insulation_type', 'PUF Core')}\n"
            f"- **Optimal Insulation:** {rec['optimal_insulation_mm']:.0f} mm"
        )


# ── 5. CANDIDATE RANKING ──────────────────────────────────────────────────────
def page_candidates() -> None:
    _hdr("5 · Candidate Ranking")
    st.caption(
        "Top-ranked candidate designs from the Bayesian optimizer, "
        "sorted by composite performance score."
    )
    req     = st.session_state["global_req"]
    rec_key = _rec_cache_key(req)

    if rec_key not in st.session_state:
        st.info("Run **4 · Optimization & Recs** to populate candidate rankings.")
        return

    rec = st.session_state[rec_key]
    _req_bar(req)
    render_ranked_candidate_designs(rec.get("ranked_designs", []))

    qe = rec.get("quantitative_evidence", {})
    if qe:
        st.markdown("---")
        _hdr("📐 Best Design — Quantitative Evidence")
        q1, q2, q3, q4, q5 = st.columns(5)
        q1.metric("Wall U-Value",   f"{qe.get('wall_u_val', 0):.3f} W/m²K")
        q2.metric("Wall R-Total",   f"{qe.get('wall_r_val', 0):.2f} m²K/W")
        q3.metric("Roof U-Value",   f"{qe.get('roof_u_val', 0):.3f} W/m²K")
        q4.metric("Comfort Hours",  f"{qe.get('comfort_hours', 0):.0f} h")
        q5.metric("Solar Harvest",  f"{qe.get('solar_energy_kwh', 0):.2f} kWh")


# ── 6. BASELINE VS OPTIMIZED ──────────────────────────────────────────────────
def page_baseline_vs_opt() -> None:
    _hdr("6 · Baseline vs AI-Optimized")
    req = st.session_state["global_req"]
    render_baseline_vs_optimized_view(
        comp_city=req["city"],
        comp_people=req["people"],
        comp_home_type=req["home_type"],
        is_dark=True,
    )


# ── 7. MATERIAL COMPARISON ────────────────────────────────────────────────────
def page_material_comparison() -> None:
    _hdr("7 · Material Comparison Studio")
    render_material_comparison_studio(st.session_state["global_req"], is_dark=True)


# ── 8. SHELTER ARCHETYPES ─────────────────────────────────────────────────────
def page_archetypes() -> None:
    _hdr("8 · Shelter Archetypes")
    render_multiple_shelter_models_studio(st.session_state["global_req"], is_dark=True)


# ── 9. SENSITIVITY ANALYSIS ───────────────────────────────────────────────────
def page_sensitivity() -> None:
    _hdr("9 · Sensitivity Analysis Studio")
    render_sensitivity_analysis_studio(st.session_state["global_req"], is_dark=True)


# ── 10. ANALYTICAL VALIDATION ────────────────────────────────────────────────
def page_validation() -> None:
    _hdr("10 · Analytical Validation")
    st.caption(
        "Verifies the ThermoShelter physics engine against exact closed-form "
        "analytical solutions — ISO 6946 steady-state and transient benchmarks."
    )
    render_model_assumptions_and_validation()


# ── 11. 3D DIGITAL TWIN ───────────────────────────────────────────────────────
def page_3d_twin() -> None:
    _hdr("11 · 3D Digital Twin")
    req     = st.session_state["global_req"]
    rec_key = _rec_cache_key(req)

    if rec_key not in st.session_state:
        st.info("Showing default geometry — run **4 · Optimization & Recs** for real specs.")
        from services.visual3d import build_3d_shelter
        geo = auto_size_shelter(req["people"], req["home_type"])
        ct  = CLIMATE_MAPPING.get(req["city"], "composite")
        st.plotly_chart(
            build_3d_shelter(
                climate_type=ct,
                length=geo["length_m"],
                width=geo["width_m"],
                height=geo["height_m"],
                window_area=2.5,
                wall_material="brick",
                insulation_mm=60.0,
                glazing_name="Double Clear Glazing",
                city_name=req["city"],
            ),
            use_container_width=True,
        )
        return

    rec = st.session_state[rec_key]
    _req_bar(req)
    render_3d_and_floorplan(rec, req["city"], is_dark=True)

    geo = rec["geometry"]
    st.markdown("---")
    _hdr("📐 Active Design Dimensions")
    d1, d2, d3, d4, d5 = st.columns(5)
    d1.metric("Length",     f"{geo['length_m']:.2f} m")
    d2.metric("Width",      f"{geo['width_m']:.2f} m")
    d3.metric("Height",     f"{geo['height_m']:.2f} m")
    d4.metric("Floor Area", f"{geo['floor_area_m2']:.2f} m²")
    d5.metric("Volume",     f"{geo['volume_m3']:.2f} m³")


# ── 12. 2D FLOORPLAN ──────────────────────────────────────────────────────────
def page_floorplan() -> None:
    _hdr("12 · 2D Floor Plan")
    req     = st.session_state["global_req"]
    rec_key = _rec_cache_key(req)

    if rec_key in st.session_state:
        rec          = st.session_state[rec_key]
        geo          = rec["geometry"]
        mats         = rec["materials"]
        length_def   = geo["length_m"]
        width_def    = geo["width_m"]
        win_def      = rec["optimal_window_area_m2"]
        orient_adv   = mats.get("orientation_advice", "South Facade")
        climate_type = rec["climate_type"]
        _req_bar(req)
    else:
        geo          = auto_size_shelter(req["people"], req["home_type"])
        climate_type = CLIMATE_MAPPING.get(req["city"], "composite")
        mats         = recommend_materials(climate_type, req["home_type"])
        length_def   = geo["length_m"]
        width_def    = geo["width_m"]
        win_def      = 2.5
        orient_adv   = mats.get("orientation_advice", "South Facade")
        st.info("Showing auto-sized geometry. Run **4 · Optimization** for optimized floorplan.")

    st.caption("Use sliders to explore how dimensions affect the floor plan layout.")
    sl1, sl2, sl3 = st.columns(3)
    with sl1:
        length = st.slider("Length (m)", 2.5, 12.0, float(round(length_def, 1)), 0.1, key="fp_l")
    with sl2:
        width  = st.slider("Width (m)",  2.0, 10.0, float(round(width_def, 1)),  0.1, key="fp_w")
    with sl3:
        win_area = st.slider("Window Area (m²)", 0.5, 8.0, float(round(win_def, 1)), 0.5, key="fp_wa")

    st.plotly_chart(
        create_2d_floorplan(
            length=length,
            width=width,
            window_area=win_area,
            orientation_advice=orient_adv,
            climate_type=climate_type,
            is_dark=True,
        ),
        use_container_width=True,
    )
    st.markdown(
        f"**Floor area:** {length * width:.1f} m²  |  "
        f"**L × W:** {length:.2f} m × {width:.2f} m  |  "
        f"**South glazing:** {win_area:.2f} m²"
    )


# ── 13. ENGINEERING REPORT / EXPORT ──────────────────────────────────────────
def page_export() -> None:
    _hdr("13 · Engineering Report & Export")
    st.caption(
        "Download full engineering specification as Markdown or JSON. "
        "Report reflects the CURRENT selected design and simulation results."
    )
    req     = st.session_state["global_req"]
    rec_key = _rec_cache_key(req)

    if rec_key not in st.session_state:
        st.info("Run **4 · Optimization & Recs** first to generate the engineering report.")
        return

    rec = st.session_state[rec_key]
    sim = rec["simulation_result"]
    _req_bar(req)

    with st.expander("📖 Engineering Assumptions (click to expand)", expanded=False):
        render_model_assumptions_and_validation()

    st.markdown("---")
    render_export_section(rec, sim, req["city"])

    st.markdown("---")
    with st.expander("📄 Preview Markdown Report", expanded=False):
        st.markdown(generate_markdown_report(rec, sim, req["city"]))


# ==============================================================================
# PAGE DISPATCHER
# ==============================================================================
_PAGES = {
    "dashboard":           page_dashboard,
    "climate":             page_climate,
    "shelter_designer":    page_shelter_designer,
    "simulation":          page_simulation,
    "optimization":        page_optimization,
    "candidates":          page_candidates,
    "baseline_vs_opt":     page_baseline_vs_opt,
    "material_comparison": page_material_comparison,
    "archetypes":          page_archetypes,
    "sensitivity":         page_sensitivity,
    "validation":          page_validation,
    "twin_3d":             page_3d_twin,
    "floorplan_2d":        page_floorplan,
    "export":              page_export,
}


def main() -> None:
    _PAGES.get(PAGE_ID, page_dashboard)()


if __name__ == "__main__":
    main()