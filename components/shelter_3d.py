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
    """
    geo = rec["geometry"]
    mats = rec["materials"]

    st.markdown("### 🏗️ 5. Architectural Floor Plan & 3D Interactive Model")
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
            ),
            use_container_width=True,
        )
