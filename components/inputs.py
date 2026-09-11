"""
THERMOSHELTER AI - Unified Requirements & Design Constraint Inputs
==================================================================
Captures user design criteria, location context, shelter permanence,
and engineering constraints in a clean, unified interface.
"""

from typing import Any, Dict, Tuple
import streamlit as st

from services.recommender import CLIMATE_MAPPING, CLIMATE_DESCRIPTIONS

CITIES_METADATA = {
    "leh": {
        "display": "🏔️ Leh, Ladakh (Alpine Severe Cold)",
        "badge": "⭐ Hero Demo (High-Altitude Cold)",
        "elevation": "3,524 m",
        "winter_temp": "-18.5 °C",
        "summer_temp": "26.0 °C",
        "solar_ghi": "2,100 kWh/m²",
        "hdd": 4850,
        "source": "IMD Leh Station & NREL NSRDB / ASHRAE EPW",
        "type": "Observed Reference Dataset",
    },
    "jaisalmer": {
        "display": "🏜️ Jaisalmer, Thar (Hot & Arid Desert)",
        "badge": "Desert High Diurnal",
        "elevation": "225 m",
        "winter_temp": "7.0 °C",
        "summer_temp": "46.0 °C",
        "solar_ghi": "2,250 kWh/m²",
        "hdd": 220,
        "source": "MNRE / IMD Climatological Normals EPW",
        "type": "Observed Reference Dataset",
    },
    "chennai": {
        "display": "🌊 Chennai, Tamil Nadu (Warm & Humid Coastal)",
        "badge": "Tropical Coastal",
        "elevation": "6 m",
        "winter_temp": "20.0 °C",
        "summer_temp": "39.0 °C",
        "solar_ghi": "1,950 kWh/m²",
        "hdd": 0,
        "source": "BEE ECBC / IMD EPW",
        "type": "Observed Reference Dataset",
    },
    "delhi": {
        "display": "🏙️ Delhi, NCR (Composite / Extreme Seasonal)",
        "badge": "Seasonal Extreme",
        "elevation": "216 m",
        "winter_temp": "5.0 °C",
        "summer_temp": "43.5 °C",
        "solar_ghi": "1,900 kWh/m²",
        "hdd": 450,
        "source": "ISHRAE / BEE ECBC Weather EPW",
        "type": "Observed Reference Dataset",
    },
    "bengaluru": {
        "display": "🌳 Bengaluru, Karnataka (Temperate / Moderate)",
        "badge": "Moderate Plateau",
        "elevation": "920 m",
        "winter_temp": "15.0 °C",
        "summer_temp": "34.0 °C",
        "solar_ghi": "1,850 kWh/m²",
        "hdd": 0,
        "source": "IMD Bengaluru & ISHRAE EPW",
        "type": "Observed Reference Dataset",
    },
}


def render_climate_info_card(city: str) -> None:
    """
    Renders transparent climate metadata and data provenance for the selected city.
    """
    meta = CITIES_METADATA.get(city, CITIES_METADATA["leh"])
    st.markdown(
        f"""
    <div style="background-color: #1e293b; border-radius: 8px; padding: 14px 18px; border-left: 4px solid #38bdf8; margin-bottom: 15px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-weight: 700; color: #38bdf8; font-size: 1.05rem;">📍 {meta['display']}</span>
            <span style="background-color: #0369a1; color: #f0f9ff; padding: 2px 10px; border-radius: 12px; font-size: 0.82rem; font-weight: 600;">{meta['badge']}</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; font-size: 0.88rem; color: #cbd5e1;">
            <div><b>Elevation:</b> {meta['elevation']}</div>
            <div><b>Design Winter:</b> <span style="color: #60a5fa;">{meta['winter_temp']}</span></div>
            <div><b>Solar GHI:</b> <span style="color: #fbbf24;">{meta['solar_ghi']}</span></div>
            <div><b>Heating HDD:</b> {meta['hdd']} HDD</div>
        </div>
        <div style="margin-top: 8px; font-size: 0.80rem; color: #94a3b8; border-top: 1px solid rgba(148, 163, 184, 0.2); padding-top: 6px;">
            <b>Data Source:</b> {meta['source']} | <b>Dataset Type:</b> {meta['type']}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_requirements_inputs(
    default_city: str = "leh",
    default_people: int = 4,
    default_home_type: str = "Permanent",
) -> Dict[str, Any]:
    """
    Renders unified primary requirement controls and returns configured parameters.
    """
    st.markdown("### 📋 Shelter Mission & Requirements")
    col1, col2, col3 = st.columns([1.3, 1.0, 1.1])

    with col1:
        city = st.selectbox(
            "1. Deployment Location",
            options=list(CITIES_METADATA.keys()),
            index=list(CITIES_METADATA.keys()).index(default_city) if default_city in CITIES_METADATA else 0,
            format_func=lambda x: CITIES_METADATA[x]["display"],
            key="req_city",
        )

    with col2:
        people = st.slider(
            "2. Shelter Occupants",
            min_value=1,
            max_value=12,
            value=default_people,
            key="req_people",
            help="Determines baseline auto-sizing floor area (4.5 m²/person baseline) and internal metabolic heat generation (80 W/person).",
        )

    with col3:
        home_type = st.radio(
            "3. Shelter Permanence",
            options=["Temporary", "Permanent"],
            index=0 if default_home_type == "Temporary" else 1,
            horizontal=True,
            key="req_permanence",
            help="Temporary: lightweight modular panels & high portability. Permanent: durable masonry/stone with high thermal mass.",
        )

    # Show transparent climate provenance card
    render_climate_info_card(city)

    # Expandable Engineering Design Constraints
    with st.expander("⚙️ Engineering Design Constraints & Objectives (Optional)", expanded=False):
        c_col1, c_col2, c_col3 = st.columns(3)
        with c_col1:
            max_insulation_mm = st.slider(
                "Max Insulation Cap (mm)",
                min_value=20,
                max_value=250,
                value=120 if home_type == "Temporary" else 200,
                step=10,
                key="req_max_ins",
                help="Restricts maximum allowable envelope insulation thickness.",
            )
        with c_col2:
            max_window_area = st.slider(
                "Max Window Area (m²)",
                min_value=1.0,
                max_value=8.0,
                value=4.0,
                step=0.5,
                key="req_max_win",
                help="Limits maximum fenestration aperture size.",
            )
        with c_col3:
            opt_trials = st.selectbox(
                "Bayesian Optimizer Trials",
                options=[20, 35, 50, 75],
                index=1,
                key="req_trials",
                help="Number of Optuna TPE search iterations across design parameter combinations.",
            )

    return {
        "city": city,
        "people": people,
        "home_type": home_type,
        "max_insulation_mm": float(max_insulation_mm),
        "max_window_area": float(max_window_area),
        "opt_trials": int(opt_trials),
    }
