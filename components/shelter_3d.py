"""
THERMOSHELTER AI - 3D Interactive Model & 2D Floorplan Visualizer
================================================================
Renders the climate-adaptive 3D Plotly architectural model and 2D floor plan
tightly coupled to calculated design geometry and material choices.
"""

from typing import Any, Dict
import streamlit as st

from components.charts import create_2d_floorplan
from services.visual3d import build_3d_shelter


def render_3d_and_floorplan(
    rec: Dict[str, Any],
    city: str,
    is_dark: bool = True,
) -> None:
    """
    Renders side-by-side 2D floor plan and dynamic 3D Plotly shelter model.
    Includes view-mode toggles for envelope cutaways, thermal twins, solar,
    and passive ventilation airflow paths.
    """
    geo = rec["geometry"]
    mats = rec["materials"]

    st.markdown("### 🏗️ 5. Architectural Floor Plan & 3D Interactive Model")

    view_mode_descriptions = {
        "normal": "🏛️ **Standard Architectural**: Realistic foundation, thermal walls, fenestrations, roof slope & site context.",
        "envelope": "🔬 **Envelope Cutaway**: Transparent exterior exposing wall core assemblies, insulation batting & thermal mass.",
        "thermal": "🌡️ **Thermal Twin**: Surface heat flux gradient calibrated to simulation loads & ambient differential.",
        "solar": "☀️ **Solar & Daylighting**: Active photovoltaic arrays, passive solar glazing bands & cardinal orientation.",
        "ventilation": "💨 **Passive Ventilation**: Airflow vectors, ridge vent caps & cross-ventilation aperture alignments.",
    }

    view_mode_opts = {
        "🏛️ Architectural": "normal",
        "🔬 Envelope Cutaway": "envelope",
        "🌡️ Thermal Twin": "thermal",
        "☀️ Solar & Daylighting": "solar",
        "💨 Ventilation Flow": "ventilation",
    }

    g1, g2 = st.columns(2)

    with g1:
        st.plotly_chart(
            create_2d_floorplan(
                length=geo["length_m"],
                width=geo["width_m"],
                window_area=rec["optimal_window_area_m2"],
                orientation_advice=mats["orientation_advice"],
                climate_type=rec["climate_type"],
                is_dark=is_dark,
            ),
            use_container_width=True,
        )

    with g2:
        selected_mode_key = st.radio(
            "Digital Twin View Mode",
            options=list(view_mode_opts.keys()),
            index=0,
            horizontal=True,
            help="Switch between architectural rendering, structural envelope cutaways, thermal gradients, solar panels, and ventilation pathways.",
            key=f"twin_view_mode_{city}",
        )
        mode_val = view_mode_opts[selected_mode_key]

        st.plotly_chart(
            build_3d_shelter(
                climate_type=rec["climate_type"],
                length=geo["length_m"],
                width=geo["width_m"],
                height=geo["height_m"],
                window_area=rec["optimal_window_area_m2"],
                wall_material=rec.get("optimal_wall_material", mats["wall_material_id"]),
                insulation_mm=rec["optimal_insulation_mm"],
                glazing_name=rec.get("optimal_glazing_name", mats.get("glazing_type", "Double Clear")),
                city_name=city,
                view_mode=mode_val,
            ),
            use_container_width=True,
        )
        st.caption(view_mode_descriptions[mode_val])
