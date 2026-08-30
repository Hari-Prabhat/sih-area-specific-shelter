"""
THERMOSHELTER AI - Feature Studio Unified Controller
====================================================
Hosts and coordinates the 5 specialized engineering studios:
  1. 🏕️ Shelter Designer (Auto-sizing, Bayesian Optimization, 168-hr Simulation, 3D, Export)
  2. ⚖️ Baseline vs Optimized (Realistic comparative benchmark)
  3. 🧱 Material Comparison Studio (Multi-material envelope benchmarking)
  4. 🏛️ Multiple Shelter Models (Cross-archetype geometric & roof form evaluation)
  5. 📈 Sensitivity Analysis Studio (Dynamic parametric sweeps)

All studios load immediately upon tab selection without secondary button gates.
"""

from typing import Any, Dict, List
import math
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from components.chart_theme import apply_chart_theme, FONT_FAMILY
from components.charts import (
    plot_sensitivity_curves,
    create_2d_floorplan,
)
from components.dashboard import render_simulation_dashboard
from components.recommendations import (
    render_envelope_specifications,
    render_ranked_candidate_designs,
    render_explainable_rationale,
)
from components.shelter_3d import render_3d_and_floorplan
from components.comparison import render_baseline_vs_optimized_view
from components.validation import render_model_assumptions_and_validation
from components.export import render_export_section

from services.simulation_service import run_simulation, SHELTER_MODELS
from services.recommender import (
    get_recommendation,
    auto_size_shelter,
    recommend_materials,
    CLIMATE_MAPPING,
)
from services.material_service import load_all_materials, get_material
from services.climate_service import get_climate_data
from services.visual3d import build_3d_shelter


def render_shelter_designer_studio(
    req: Dict[str, Any],
    is_dark: bool = True,
) -> None:
    """
    Studio 1: Primary Shelter Designer & Optimization Workflow.
    Loads and simulates immediately using current requirements.
    """
    city = req["city"]
    people = req["people"]
    home_type = req["home_type"]
    max_ins_mm = req.get("max_insulation_mm", 200.0)
    max_win = req.get("max_window_area", 4.0)
    n_trials = req.get("opt_trials", 35)

    cache_key = f"des_{city}_{people}_{home_type}_{max_ins_mm}_{max_win}_{n_trials}"

    # Auto-run if not yet computed for these exact inputs
    if cache_key not in st.session_state:
        with st.spinner(f"Computing climate-optimized envelope for {city.upper()} ({home_type} Shelter)..."):
            rec = get_recommendation(
                city=city,
                people=people,
                home_type=home_type,
                n_trials=n_trials,
                max_insulation_mm=max_ins_mm,
                max_window_area=max_win,
            )
            sim_res = rec.get("simulation_result")
            if not sim_res or "error" in sim_res:
                st.error("Simulation failed. Please check weather and material availability.")
                return

            st.session_state[cache_key] = {
                "rec": rec,
                "sim_res": sim_res,
            }

    data = st.session_state[cache_key]
    rec = data["rec"]
    sim_res = data["sim_res"]

    st.success(
        f"✅ Optimized Design Active for **{city.upper()}** ({rec['climate_name']}) — Discomfort: **{sim_res['discomfort_degree_hours']:.1f} °C·h** | Comfort: **{sim_res['comfort_percentage']:.1f}%**"
    )

    # 1, 2, 3: Dashboard Sections
    render_simulation_dashboard(city, sim_res, f"— {home_type} Shelter", is_dark=is_dark)

    # 4: Envelope Specifications
    render_envelope_specifications(rec, sim_res, home_type)

    # 4b: Multi-Candidate Ranking
    render_ranked_candidate_designs(rec.get("ranked_designs", []))

    st.markdown("---")

    # 5: 3D & Floorplan
    render_3d_and_floorplan(rec, city, is_dark=is_dark)

    st.markdown("---")

    # 6: Explainable Rationale
    render_explainable_rationale(rec)

    st.markdown("---")

    # 7: Model Assumptions & Analytical Validation
    render_model_assumptions_and_validation()

    st.markdown("---")

    # 8: Export Specification
    render_export_section(rec, sim_res, city)


def render_material_comparison_studio(
    req: Dict[str, Any],
    is_dark: bool = True,
) -> None:
    """
    Studio 3: Multi-Material Envelope Comparison Studio.
    Compares all candidate structural materials under strictly identical geometry & boundary conditions.
    """
    st.subheader("🧱 Multi-Material Envelope Comparison Studio")
    st.caption("Compare structural materials under strictly identical climate, geometry, and occupancy.")

    m_c1, m_c2, m_c3, m_c4 = st.columns(4)
    with m_c1:
        mat_city = st.selectbox(
            "Climate Zone",
            ["leh", "jaisalmer", "chennai", "delhi", "bengaluru"],
            index=["leh", "jaisalmer", "chennai", "delhi", "bengaluru"].index(req["city"])
            if req["city"] in ["leh", "jaisalmer", "chennai", "delhi", "bengaluru"]
            else 0,
            format_func=lambda x: {
                "leh": "🏔️ Leh (Cold)",
                "jaisalmer": "🏜️ Jaisalmer (Hot-Dry)",
                "chennai": "🌊 Chennai (Humid)",
                "delhi": "🏙️ Delhi (Composite)",
                "bengaluru": "🌳 Bengaluru (Moderate)",
            }[x],
            key="m_city_sel",
        )
    with m_c2:
        m_ins_mm = st.slider("Added Insulation (mm)", 0, 200, 50, 10, key="m_ins_val")
    with m_c3:
        m_win = st.slider("Window Aperture (m²)", 1.0, 8.0, 2.5, 0.5, key="m_win_val")
    with m_c4:
        m_occ = st.slider("Occupants", 1, 8, req["people"], key="m_occ_val")

    all_mat = load_all_materials()
    candidate_materials = [
        k for k in all_mat if "error" not in k and isinstance(all_mat[k], dict) and all_mat[k].get("category") == "wall"
    ]
    if not candidate_materials:
        candidate_materials = ["brick", "concrete", "puf_insulation", "stone", "mud"]

    cache_key = f"mat_{mat_city}_{m_ins_mm}_{m_win}_{m_occ}"
    if cache_key not in st.session_state:
        with st.spinner("Simulating candidate envelope materials…"):
            mat_results = []
            for m_key in candidate_materials[:8]:  # Top 8 distinct wall materials
                m_info = all_mat.get(m_key, {})
                sim = run_simulation(
                    city=mat_city,
                    length=4.5,
                    width=3.2,
                    height=2.8,
                    wall_material=m_key,
                    insulation_thickness_m=m_ins_mm / 1000.0,
                    window_area=m_win,
                    occupants=m_occ,
                    hours_to_simulate=168,
                )
                if "error" not in sim:
                    mat_results.append({
                        "key": m_key,
                        "name": m_info.get("name", m_key.title()),
                        "conductivity": m_info.get("thermal_conductivity", "-"),
                        "density": m_info.get("density", "-"),
                        "wall_u": sim["u_values"]["wall_u"],
                        "wall_r": sim["u_values"]["wall_r_total"],
                        "avg_t": sim["comfort_metrics"]["avg"],
                        "min_t": sim["comfort_metrics"]["min_t"],
                        "max_t": sim["comfort_metrics"]["max_t"],
                        "comfort_hrs": sim["comfort_hours"],
                        "comfort_pct": sim["comfort_percentage"],
                        "discomfort_dh": sim["discomfort_degree_hours"],
                        "total_loss_kwh": sim["total_heat_loss_kwh"],
                        "indoor_temps": sim["indoor_temperature"],
                        "outdoor_temps": sim["outdoor_temperature"],
                    })
            st.session_state[cache_key] = mat_results

    me_data = st.session_state[cache_key]

    # Multi-Material Thermal Curves
    st.markdown("### 📈 Multi-Material Thermal Curves")
    fig_mat = go.Figure()
    fig_mat.add_hrect(
        y0=18.0,
        y1=24.0,
        fillcolor="rgba(34, 197, 94, 0.16)",
        layer="below",
        line=dict(color="#22c55e", width=1.5, dash="dash"),
        annotation_text="🌿 Comfort Band (18–24 °C)",
        annotation_position="top left",
    )
    if me_data:
        fig_mat.add_trace(
            go.Scatter(
                x=list(range(168)),
                y=me_data[0]["outdoor_temps"],
                mode="lines",
                name="Outdoor Ambient",
                line=dict(color="#94a3b8", width=1.8, dash="dot"),
                hovertemplate="Outdoor: <b>%{y:.2f} °C</b><extra></extra>",
            )
        )

    mat_colors = ["#38bdf8", "#f43f5e", "#10b981", "#fbbf24", "#a78bfa", "#f472b6", "#22d3ee", "#a3e635"]
    for idx, item in enumerate(me_data):
        fig_mat.add_trace(
            go.Scatter(
                x=list(range(168)),
                y=item["indoor_temps"],
                mode="lines",
                name=item["name"],
                line=dict(color=mat_colors[idx % len(mat_colors)], width=2.4),
                hovertemplate=f"{item['name']}: <b>%{{y:.2f}} °C</b><extra></extra>",
            )
        )

    fig_mat.update_xaxes(
        title="Time (Simulation Hours)",
        tickmode="array",
        tickvals=[0, 24, 48, 72, 96, 120, 144, 168],
        ticktext=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "End"],
    )
    fig_mat.update_yaxes(title="Indoor Temperature (°C)")
    apply_chart_theme(
        fig_mat,
        title_text=f"📈 Indoor Temperature Progression Across Envelope Materials ({mat_city.upper()})",
        height=440,
        is_dark=is_dark,
    )
    fig_mat.update_layout(hovermode="x unified")
    st.plotly_chart(fig_mat, use_container_width=True)

    # Comparative Summary Table
    st.markdown("### 📋 Material Performance Comparison Table")
    m_table_rows = []
    for r in me_data:
        m_table_rows.append({
            "Material": r["name"],
            "k (W/m·K)": r["conductivity"],
            "Density (kg/m³)": r["density"],
            "Wall U-Value (W/m²K)": f"{r['wall_u']:.3f}",
            "Avg Temp (°C)": f"{r['avg_t']:.1f}",
            "Min Temp (°C)": f"{r['min_t']:.1f}",
            "Comfort Hours": f"{r['comfort_hrs']:.0f} h ({r['comfort_pct']:.1f}%)",
            "Discomfort (°C·h)": f"{r['discomfort_dh']:.1f}",
            "Weekly Loss (kWh)": f"{r['total_loss_kwh']:.1f}",
        })
    st.dataframe(pd.DataFrame(m_table_rows), use_container_width=True)


def render_multiple_shelter_models_studio(
    req: Dict[str, Any],
    is_dark: bool = True,
) -> None:
    """
    Studio 4: Multiple Shelter Archetype Models.
    Evaluates how building form and roof geometry impact thermal performance under identical floor area.
    """
    st.subheader("🏛️ Multiple Shelter Archetype Models")
    st.caption("Simulate and benchmark distinct shelter geometric forms and roof systems under identical floor area.")

    sm_col1, sm_col2, sm_col3 = st.columns(3)
    with sm_col1:
        arch_city = st.selectbox(
            "Climate Zone",
            ["leh", "jaisalmer", "chennai", "delhi", "bengaluru"],
            index=["leh", "jaisalmer", "chennai", "delhi", "bengaluru"].index(req["city"])
            if req["city"] in ["leh", "jaisalmer", "chennai", "delhi", "bengaluru"]
            else 0,
            format_func=lambda x: {
                "leh": "🏔️ Leh (Cold)",
                "jaisalmer": "🏜️ Jaisalmer (Hot-Dry)",
                "chennai": "🌊 Chennai (Humid)",
                "delhi": "🏙️ Delhi (Composite)",
                "bengaluru": "🌳 Bengaluru (Moderate)",
            }[x],
            key="arch_c_sel",
        )
    with sm_col2:
        model_choice = st.selectbox(
            "Shelter Archetype Model",
            list(SHELTER_MODELS.keys()),
            format_func=lambda k: SHELTER_MODELS[k]["name"],
            key="arch_m_choice",
        )
    with sm_col3:
        arch_occ = st.slider("Occupants", 1, 8, req["people"], key="arch_occ_val")

    sel_spec = SHELTER_MODELS[model_choice]
    st.info(f"**Model Profile:** {sel_spec['description']}")

    # Dimension Controls based on selected model
    if model_choice == "custom_dimensions":
        cd1, cd2, cd3, cd4 = st.columns(4)
        with cd1: arch_l = st.slider("Length (m)", 2.5, 10.0, 4.0, 0.1, key="cd_l")
        with cd2: arch_w = st.slider("Width (m)", 2.5, 10.0, 3.0, 0.1, key="cd_w")
        with cd3: arch_h = st.slider("Height (m)", 2.2, 4.0, 2.8, 0.1, key="cd_h")
        with cd4: arch_rf = st.selectbox("Roof Type", ["flat", "pitched"], key="cd_rf")
    else:
        def_dims = sel_spec["default_dimensions"]
        arch_l = def_dims["length"]
        arch_w = def_dims["width"]
        arch_h = def_dims["height"]
        arch_rf = sel_spec["roof_type"]
        st.caption(f"📐 Geometry: **{arch_l:.2f} m × {arch_w:.2f} m × {arch_h:.2f} m** | Roof: **{arch_rf.title()}**")

    cache_key = f"arch_{arch_city}_{model_choice}_{arch_l}_{arch_w}_{arch_h}_{arch_rf}_{arch_occ}"
    if cache_key not in st.session_state:
        with st.spinner(f"Simulating {sel_spec['name']} in {arch_city.upper()}…"):
            sim_arch = run_simulation(
                city=arch_city,
                length=arch_l,
                width=arch_w,
                height=arch_h,
                roof_type=arch_rf,
                shelter_model=model_choice,
                wall_material="brick",
                insulation_thickness_m=0.06,
                window_area=2.2,
                occupants=arch_occ,
                hours_to_simulate=168,
            )

            # Benchmark all 4 standard models under identical floor area
            comp_models = []
            std_floor_area = arch_l * arch_w
            for m_key in ["rectangular_flat", "rectangular_pitched", "compact_shelter", "elongated_shelter"]:
                m_def = SHELTER_MODELS[m_key]
                d = m_def["default_dimensions"]
                scale = math.sqrt(std_floor_area / (d["length"] * d["width"]))
                scaled_l = d["length"] * scale
                scaled_w = d["width"] * scale
                s_res = run_simulation(
                    city=arch_city,
                    length=scaled_l,
                    width=scaled_w,
                    height=arch_h,
                    roof_type=m_def["roof_type"],
                    shelter_model=m_key,
                    wall_material="brick",
                    insulation_thickness_m=0.06,
                    window_area=2.2,
                    occupants=arch_occ,
                )
                if "error" not in s_res:
                    comp_models.append({
                        "key": m_key,
                        "name": m_def["name"],
                        "roof": m_def["roof_type"].title(),
                        "aspect": f"{scaled_l/scaled_w:.2f}:1",
                        "envelope_area": s_res["geometry"]["solid_wall_area_m2"] + s_res["geometry"]["roof_area_m2"] + s_res["geometry"]["floor_area_m2"],
                        "volume": s_res["geometry"]["volume_m3"],
                        "comfort_pct": s_res["comfort_percentage"],
                        "discomfort_dh": s_res["discomfort_degree_hours"],
                        "heat_loss_kwh": s_res["total_heat_loss_kwh"],
                        "indoor_temps": s_res["indoor_temperature"],
                    })

            st.session_state[cache_key] = {
                "cur_sim": sim_arch,
                "comp_models": comp_models,
            }

    arch_data = st.session_state[cache_key]
    cur_sim = arch_data["cur_sim"]

    # 3D Model & Floor Plan
    st.markdown("### 🏗️ 3D Model & Floor Plan")
    a_g1, a_g2 = st.columns(2)
    ct = CLIMATE_MAPPING.get(arch_city, "composite")

    with a_g1:
        st.plotly_chart(
            build_3d_shelter(
                climate_type=ct,
                length=arch_l,
                width=arch_w,
                height=arch_h,
                window_area=2.2,
                wall_material="brick",
                insulation_mm=60.0,
                glazing_name="Double Clear Glazing",
                city_name=arch_city,
            ),
            use_container_width=True,
        )
    with a_g2:
        st.plotly_chart(
            create_2d_floorplan(arch_l, arch_w, 2.2, "South Facade", ct, is_dark=is_dark),
            use_container_width=True,
        )

    st.markdown("---")
    render_simulation_dashboard(arch_city, cur_sim, f"— {sel_spec['name']}", is_dark=is_dark)

    # Cross-Archetype Comparative Matrix
    st.markdown("### 📊 Cross-Archetype Comparative Matrix (Identical Floor Area)")
    arch_matrix_rows = []
    for m in arch_data["comp_models"]:
        arch_matrix_rows.append({
            "Archetype Model": m["name"],
            "Roof Profile": m["roof"],
            "Aspect Ratio (L:W)": m["aspect"],
            "Total Envelope Area (m²)": f"{m['envelope_area']:.1f}",
            "Enclosed Volume (m³)": f"{m['volume']:.1f}",
            "Comfort Percentage": f"{m['comfort_pct']:.1f} %",
            "Discomfort Score (°C·h)": f"{m['discomfort_dh']:.1f}",
            "Total Heat Loss (kWh)": f"{m['heat_loss_kwh']:.1f}",
        })
    st.dataframe(pd.DataFrame(arch_matrix_rows), use_container_width=True)


def render_sensitivity_analysis_studio(
    req: Dict[str, Any],
    is_dark: bool = True,
) -> None:
    """
    Studio 5: Sensitivity Analysis Studio.
    Demonstrates how changing design variables affects comfort percentage and heat loss.
    """
    st.subheader("📈 Parametric Sensitivity Analysis Studio")
    st.caption("Investigate the thermodynamic sensitivity of comfort percentage and envelope heat losses across design parameters.")

    s_col1, s_col2 = st.columns(2)
    with s_col1:
        param_choice = st.selectbox(
            "Select Parameter to Sweep",
            ["Insulation Thickness (mm)", "Window Aperture Area (m²)", "Glazing Type"],
            key="sens_param_choice",
        )
    with s_col2:
        sens_city = st.selectbox(
            "Climate Zone",
            ["leh", "jaisalmer", "chennai", "delhi", "bengaluru"],
            index=["leh", "jaisalmer", "chennai", "delhi", "bengaluru"].index(req["city"])
            if req["city"] in ["leh", "jaisalmer", "chennai", "delhi", "bengaluru"]
            else 0,
            format_func=lambda x: {
                "leh": "🏔️ Leh (Cold)",
                "jaisalmer": "🏜️ Jaisalmer (Hot-Dry)",
                "chennai": "🌊 Chennai (Humid)",
                "delhi": "🏙️ Delhi (Composite)",
                "bengaluru": "🌳 Bengaluru (Moderate)",
            }[x],
            key="sens_city_choice",
        )

    cache_key = f"sens_{sens_city}_{param_choice}"
    if cache_key not in st.session_state:
        with st.spinner("Running parametric sweep across design space…"):
            if param_choice.startswith("Insulation"):
                val_range = [0, 20, 40, 60, 80, 100, 120, 150, 180, 200]
                comfort_list = []
                loss_list = []
                for v in val_range:
                    sim = run_simulation(
                        city=sens_city,
                        length=4.5,
                        width=3.2,
                        height=2.8,
                        insulation_thickness_m=v / 1000.0,
                        window_area=2.5,
                        occupants=req["people"],
                        hours_to_simulate=168,
                    )
                    comfort_list.append(sim["comfort_percentage"])
                    loss_list.append(sim["total_heat_loss_kwh"])
                st.session_state[cache_key] = {
                    "name": "Insulation Thickness",
                    "values": val_range,
                    "unit": "mm",
                    "comfort": comfort_list,
                    "loss": loss_list,
                }
            else:
                val_range = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
                comfort_list = []
                loss_list = []
                for v in val_range:
                    sim = run_simulation(
                        city=sens_city,
                        length=4.5,
                        width=3.2,
                        height=2.8,
                        insulation_thickness_m=0.06,
                        window_area=v,
                        occupants=req["people"],
                        hours_to_simulate=168,
                    )
                    comfort_list.append(sim["comfort_percentage"])
                    loss_list.append(sim["total_heat_loss_kwh"])
                st.session_state[cache_key] = {
                    "name": "Window Aperture Area",
                    "values": val_range,
                    "unit": "m²",
                    "comfort": comfort_list,
                    "loss": loss_list,
                }

    sens_data = st.session_state[cache_key]
    st.plotly_chart(
        plot_sensitivity_curves(
            param_name=sens_data["name"],
            param_values=sens_data["values"],
            comfort_percentages=sens_data["comfort"],
            heat_losses_kwh=sens_data["loss"],
            unit=sens_data["unit"],
            is_dark=is_dark,
        ),
        use_container_width=True,
    )
