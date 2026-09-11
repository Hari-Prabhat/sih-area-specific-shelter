"""
THERMOSHELTER AI - Recommendations & Envelope Specifications UI
===============================================================
Renders the optimal envelope specifications, multi-candidate ranked optimization
results, and explainable design rationale backed by computed numerical evidence.
"""

from typing import Any, Dict, List
import streamlit as st
import pandas as pd


def render_envelope_specifications(
    rec: Dict[str, Any],
    sim_res: Dict[str, Any],
    home_type: str = "Permanent",
) -> None:
    """
    Renders the 6 technical envelope specification cards.
    """
    geo = rec["geometry"]
    mats = rec["materials"]
    u_vals = sim_res["u_values"]

    st.markdown("### 🏆 4. Recommended Envelope Specifications")
    r1, r2, r3 = st.columns(3)

    with r1:
        st.markdown(
            f"""<div class='card'>
<h4>🧱 Wall Assembly</h4>
<p><b>Material:</b> {mats['wall_material_name']}</p>
<p><b>Assembly U-Value:</b> <span class='metric-badge'>{u_vals.get('wall_u', 0.50):.3f} W/m²K</span></p>
<p><b>Total Thermal R:</b> {u_vals.get('wall_r_total', 2.0):.2f} m²K/W</p>
<p><b>Thermal Mass:</b> {'High Thermal Mass' if home_type == 'Permanent' else 'Lightweight Prefab Panel'}</p>
</div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class='card'>
<h4>🏠 Roof System</h4>
<p><b>Design:</b> {mats['roof_material']}</p>
<p><b>Roof U-Value:</b> <span class='metric-badge'>{u_vals.get('roof_u', 0.40):.3f} W/m²K</span></p>
<p><b>Total Roof R:</b> {u_vals.get('roof_r_total', 2.5):.2f} m²K/W</p>
<p><b>Profile:</b> {mats['roof_type'].title()} Roof</p>
</div>""",
            unsafe_allow_html=True,
        )

    with r2:
        st.markdown(
            f"""<div class='card'>
<h4>🛡️ Thermal Insulation</h4>
<p><b>Type:</b> {mats['insulation_type']}</p>
<p><b>Optimal Thickness:</b> <span class='metric-badge'>{rec['optimal_insulation_mm']:.1f} mm</span></p>
<p><b>Core Conductivity:</b> 0.025 W/m·K (PUF Core)</p>
<p><b>Added Insulation R:</b> {u_vals.get('wall_r_total', 2.0) - u_vals.get('wall_base_r', 0.5):.2f} m²K/W</p>
</div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class='card'>
<h4>🪟 Fenestration & Glazing</h4>
<p><b>Specification:</b> {rec.get('optimal_glazing_name', mats['glazing_type'])}</p>
<p><b>Aperture Area:</b> <span class='metric-badge'>{rec['optimal_window_area_m2']:.2f} m²</span></p>
<p><b>Glazing U-Value:</b> {u_vals.get('glass_u', u_vals.get('window_u', 2.80)):.2f} W/m²K</p>
<p><b>WWR:</b> {(rec['optimal_window_area_m2'] / max(1.0, 2.0 * (geo['length_m'] + geo['width_m']) * geo['height_m'])) * 100.0:.1f} %</p>
</div>""",
            unsafe_allow_html=True,
        )

    with r3:
        st.markdown(
            f"""<div class='card'>
<h4>🧭 Orientation & Passive Solar</h4>
<p><b>Orientation:</b> <span class='metric-badge'>{rec.get('optimal_orientation', 'south').title()} Facade</span></p>
<p><b>Solar Strategy:</b> {mats['orientation_advice']}</p>
<p><b>Shading Design:</b> {mats['shading_advice']}</p>
</div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class='card'>
<h4>📐 Auto-Sizing Summary</h4>
<p><b>Floor Area:</b> {geo['floor_area_m2']:.1f} m² ({geo['length_m']:.1f}m × {geo['width_m']:.1f}m)</p>
<p><b>Height:</b> {geo['height_m']:.1f} m | <b>Volume:</b> {geo['volume_m3']:.1f} m³</p>
<p><b>Target Occupants:</b> {rec['people']} Persons</p>
</div>""",
            unsafe_allow_html=True,
        )


def render_ranked_candidate_designs(ranked_designs: List[Dict[str, Any]]) -> None:
    """
    Renders top candidate configurations produced by the Bayesian optimizer.
    """
    if not ranked_designs:
        return

    st.markdown("### 🥇 Multi-Candidate Optimization Ranking")
    st.caption("The optimizer evaluates candidate envelope parameter combinations and ranks them using multi-objective scoring.")

    table_rows = []
    for d in ranked_designs:
        sub = d.get("sub_scores", {})
        table_rows.append({
            "Rank": d["label"],
            "Wall Material": d["wall_material_name"],
            "Insulation (mm)": f"{d['insulation_mm']:.0f} mm",
            "Window (m²)": f"{d['window_area_m2']:.2f} m²",
            "Glazing Spec": d["glazing_name"],
            "Orientation": d["orientation"].title(),
            "Comfort Hours": f"{d['comfort_hours']:.0f} h ({d['comfort_percentage']:.1f}%)",
            "Discomfort (°C·h)": f"{d['discomfort_dh']:.1f}",
            "Weekly Loss (kWh)": f"{d['total_heat_loss_kwh']:.1f}",
            "Composite Score": f"{d['overall_score']:.1f} / 100",
        })

    st.dataframe(pd.DataFrame(table_rows), use_container_width=True)


def render_explainable_rationale(rec: Dict[str, Any]) -> None:
    """
    Renders the quantitative, physics-backed explainable recommendation box.
    """
    st.markdown("### 💡 6. Design Rationale & Physics Explanation")
    st.info(rec["explanation"])
