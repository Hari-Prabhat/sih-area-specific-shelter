import os
import sys
import math
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==============================================================================
# PATH SETUP
# ==============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.join(CURRENT_DIR, "services")
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from services.climate_service import get_climate_data
from services.material_service import load_all_materials, get_material
from services.optimize import run_optimization
from services.simulation_service import (
    run_simulation,
    simulate_shelter,
    GLAZING_PROPERTIES,
    ORIENTATION_FACTORS,
    SHELTER_MODELS,
)
from services.recommender import (
    get_recommendation,
    auto_size_shelter,
    recommend_materials,
    CLIMATE_MAPPING,
    CLIMATE_DESCRIPTIONS,
)

# ==============================================================================
# PAGE CONFIG
# ==============================================================================
st.set_page_config(
    page_title="Area-Specific Shelter Designer | SIH",
    page_icon="🏕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# DARK-THEME-SAFE CSS
# ==============================================================================
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem; font-weight: 700;
        color: #38bdf8; margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem; color: #94a3b8; margin-bottom: 1.2rem;
    }
    .card {
        background-color: #1e293b;
        border-radius: 10px; padding: 18px;
        border-left: 5px solid #38bdf8;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        margin-bottom: 1rem; color: #e2e8f0;
    }
    .card h4 { color: #38bdf8; margin-top:0; margin-bottom:8px; font-size:1.05rem; }
    .card p  { color: #cbd5e1; margin:4px 0; font-size:0.92rem; line-height:1.5; }
    .card b  { color: #f1f5f9; }
    .metric-badge { font-weight:700; color:#22d3ee; font-size:1.15rem; }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# PLOTTING & VISUALIZATION HELPERS
# ==============================================================================
def plot_temperature_curves(city, outdoor_temps, indoor_temps, title_suffix=""):
    hours = list(range(len(indoor_temps)))
    fig = go.Figure()

    fig.add_hrect(
        y0=18.0, y1=24.0,
        fillcolor="rgba(46,204,113,0.15)", layer="below",
        line=dict(color="rgba(46,204,113,0.5)", width=1, dash="dash"),
        annotation_text="Comfort Zone (18–24 °C)",
        annotation_position="top left",
        annotation=dict(font_size=11, font_color="#27ae60")
    )

    fig.add_trace(go.Scatter(
        x=hours,
        y=[round(float(t), 2) for t in outdoor_temps[:len(indoor_temps)]],
        mode="lines", name="Outdoor Temp (°C)",
        line=dict(color="#3498db", width=2, dash="dot"),
        hovertemplate="Hour %{x}: %{y:.2f} °C<extra>Outdoor</extra>"
    ))

    fig.add_trace(go.Scatter(
        x=hours, y=indoor_temps,
        mode="lines", name="Indoor Predicted (°C)",
        line=dict(color="#e74c3c", width=3),
        hovertemplate="Hour %{x}: %{y:.2f} °C<extra>Indoor</extra>"
    ))

    fig.update_layout(
        title=f"<b>{city.upper()} — 168-Hour Indoor vs Outdoor Thermal Profile {title_suffix}</b>",
        xaxis=dict(
            title="Time (Hours)", tickmode="array",
            tickvals=[0, 24, 48, 72, 96, 120, 144, 168],
            ticktext=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "End"],
            showgrid=True, gridcolor="#e9ecef"
        ),
        yaxis=dict(
            title="Temperature (°C)", showgrid=True,
            gridcolor="#e9ecef", zeroline=True, zerolinecolor="#bdc3c7"
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        height=400, margin=dict(l=40, r=30, t=60, b=40)
    )
    return fig


def plot_solar_dynamics(sim_result: dict):
    """
    Renders hourly solar irradiance, incident solar power, and admitted thermal gain.
    """
    hours = list(range(len(sim_result["indoor_temperatures"])))
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=hours, y=sim_result["solar_irradiance"],
            mode="lines", name="☀️ Solar Irradiance (W/m²)",
            line=dict(color="#f59e0b", width=1.8, dash="dot"),
            hovertemplate="Hour %{x}: %{y:.1f} W/m²<extra>Irradiance</extra>"
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=hours, y=sim_result["solar_power"],
            mode="lines", name="⚡ Incident Window Power (W)",
            line=dict(color="#fbbf24", width=2),
            hovertemplate="Hour %{x}: %{y:.1f} W<extra>Incident Power</extra>"
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=hours, y=sim_result["solar_thermal_gain"],
            mode="lines", name="🔥 Useful Thermal Gain (W)",
            line=dict(color="#ef4444", width=2.5),
            fill="tozeroy", fillcolor="rgba(239, 68, 68, 0.12)",
            hovertemplate="Hour %{x}: %{y:.1f} W<extra>Admitted Gain</extra>"
        ),
        secondary_y=False,
    )

    fig.update_layout(
        title="<b>Hourly Solar Flux & Fenestration Thermal Harvesting</b>",
        xaxis=dict(
            title="Time (Hours)", tickmode="array",
            tickvals=[0, 24, 48, 72, 96, 120, 144, 168],
            ticktext=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "End"],
            showgrid=True, gridcolor="#e9ecef"
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        height=380, margin=dict(l=40, r=40, t=60, b=40)
    )
    fig.update_yaxes(title_text="Solar Power / Gain (Watts)", secondary_y=False, showgrid=True, gridcolor="#e9ecef")
    fig.update_yaxes(title_text="Irradiance (W/m²)", secondary_y=True, showgrid=False)
    return fig


def plot_component_heat_flows(sim_result: dict):
    """
    Renders hourly component heat losses and net heat flow balance in Watts.
    """
    hours = list(range(len(sim_result["indoor_temperatures"])))
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hours, y=sim_result["wall_heat_flow"],
        mode="lines", name="🧱 Wall Loss (W)",
        line=dict(color="#8b5cf6", width=2),
        hovertemplate="Hour %{x}: %{y:.1f} W<extra>Wall Loss</extra>"
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=sim_result["roof_heat_flow"],
        mode="lines", name="🏠 Roof Loss (W)",
        line=dict(color="#ec4899", width=2),
        hovertemplate="Hour %{x}: %{y:.1f} W<extra>Roof Loss</extra>"
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=sim_result["floor_heat_flow"],
        mode="lines", name="🪵 Floor Loss (W)",
        line=dict(color="#a855f7", width=1.5, dash="dot"),
        hovertemplate="Hour %{x}: %{y:.1f} W<extra>Floor Loss</extra>"
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=sim_result["window_heat_flow"],
        mode="lines", name="🪟 Glazing Loss (W)",
        line=dict(color="#06b6d4", width=2),
        hovertemplate="Hour %{x}: %{y:.1f} W<extra>Glazing Loss</extra>"
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=sim_result["ventilation_heat_flow"],
        mode="lines", name="💨 Ventilation Loss (W)",
        line=dict(color="#64748b", width=1.8, dash="dash"),
        hovertemplate="Hour %{x}: %{y:.1f} W<extra>Ventilation Loss</extra>"
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=sim_result["radiation_heat_flow"],
        mode="lines", name="🌌 Radiation Loss (W)",
        line=dict(color="#3b82f6", width=1.5, dash="dot"),
        hovertemplate="Hour %{x}: %{y:.1f} W<extra>Radiation Loss</extra>"
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=sim_result["net_heat_flow"],
        mode="lines", name="⚖️ Net Heat Flow (W)",
        line=dict(color="#10b981", width=2.5),
        hovertemplate="Hour %{x}: %{y:.1f} W<extra>Net Heat Flow</extra>"
    ))

    fig.update_layout(
        title="<b>Hourly Dynamic Component Heat Flow Rates (Watts)</b>",
        xaxis=dict(
            title="Time (Hours)", tickmode="array",
            tickvals=[0, 24, 48, 72, 96, 120, 144, 168],
            ticktext=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "End"],
            showgrid=True, gridcolor="#e9ecef"
        ),
        yaxis=dict(title="Thermal Power (Watts)", showgrid=True, gridcolor="#e9ecef"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        height=390, margin=dict(l=40, r=30, t=60, b=40)
    )
    return fig


def plot_energy_balance_breakdown(sim_result: dict):
    """
    Renders weekly cumulative energy balance (kWh) directly from simulation result.
    """
    losses = sim_result["component_heat_loss_kwh"]
    categories = [
        "Solar Gain", "Wall Loss", "Roof Loss", "Floor Loss",
        "Glazing Loss", "Vent Loss", "Radiation Loss", "Total Loss"
    ]
    values = [
        sim_result.get("integrated_solar_energy_kwh", 0),
        losses.get("wall_loss_kwh", 0),
        losses.get("roof_loss_kwh", 0),
        losses.get("floor_loss_kwh", 0),
        losses.get("window_loss_kwh", 0),
        losses.get("ventilation_loss_kwh", 0),
        losses.get("radiation_loss_kwh", 0),
        sim_result.get("total_heat_loss_kwh", 0),
    ]
    colors = ["#f59e0b", "#8b5cf6", "#ec4899", "#a855f7", "#06b6d4", "#64748b", "#3b82f6", "#e11d48"]

    fig = go.Figure(data=[
        go.Bar(
            x=categories, y=values,
            marker=dict(color=colors),
            text=[f"{v:.1f} kWh" for v in values],
            textposition="auto",
        )
    ])
    fig.update_layout(
        title="<b>Weekly Component Energy Totals (kWh / 168 Hours)</b>",
        yaxis=dict(title="Energy (kWh)", showgrid=True, gridcolor="#e9ecef"),
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        height=360, margin=dict(l=40, r=30, t=50, b=40)
    )
    return fig


def create_2d_floorplan(length, width, window_area, orientation_advice, climate_type):
    fig = go.Figure()
    wt = 0.22
    fig.add_shape(type="rect", x0=0, y0=0, x1=length, y1=width,
        line=dict(color="#2c3e50", width=4), fillcolor="#e9ecef", layer="below")
    fig.add_shape(type="rect", x0=wt, y0=wt, x1=length-wt, y1=width-wt,
        line=dict(color="#95a5a6", width=1.5, dash="dot"), fillcolor="#ffffff")

    wl = min(length*0.7, max(1.2, window_area/1.3))
    ws = (length - wl) / 2
    fig.add_shape(type="rect", x0=ws, y0=-0.08, x1=ws+wl, y1=wt+0.08,
        line=dict(color="#2980b9", width=2), fillcolor="#3498db")

    dw = 0.9
    fig.add_shape(type="rect", x0=0.3, y0=-0.08, x1=0.3+dw, y1=wt+0.08,
        line=dict(color="#d35400", width=2), fillcolor="#e67e22")

    if climate_type in ("hot_humid", "moderate"):
        fig.add_shape(type="rect", x0=ws+0.3, y0=width-wt-0.08,
            x1=ws+wl-0.3, y1=width+0.08,
            line=dict(color="#2980b9", width=2), fillcolor="#3498db")
        fig.add_annotation(x=length/2, y=width+0.35,
            text="Cross-Vent Window (N)", showarrow=False,
            font=dict(size=10, color="#2980b9"))

    fa = length * width
    fig.add_annotation(x=length/2, y=width/2,
        text=f"<b>Main Space</b><br>{fa:.1f} m² ({length:.1f}×{width:.1f})",
        showarrow=False, font=dict(size=13, color="#2c3e50"))
    fig.add_annotation(x=ws+wl/2, y=-0.35,
        text=f"<b>Glazing ({wl:.1f} m)</b>", showarrow=False,
        font=dict(size=10, color="#2980b9"))
    fig.add_annotation(x=0.3+dw/2, y=-0.35,
        text="<b>Entry (0.9 m)</b>", showarrow=False,
        font=dict(size=10, color="#d35400"))

    cx, cy = length+0.6, width-0.2
    fig.add_annotation(x=cx, y=cy, ax=cx, ay=cy-0.9,
        xref="x", yref="y", axref="x", ayref="y",
        text="<b>N</b>", showarrow=True, arrowhead=2, arrowsize=1.6,
        arrowwidth=3, arrowcolor="#c0392b", font=dict(size=15, color="#c0392b"))

    fig.update_layout(
        title="<b>2D Floor Plan</b>",
        xaxis=dict(range=[-0.8,length+1.4], showgrid=True, zeroline=False,
            title="Length (m)", gridcolor="#ecf0f1"),
        yaxis=dict(range=[-0.8,width+0.8], showgrid=True, zeroline=False,
            title="Width (m)", scaleanchor="x", scaleratio=1, gridcolor="#ecf0f1"),
        plot_bgcolor="#fafafa", paper_bgcolor="#ffffff",
        height=440, margin=dict(l=30,r=30,t=50,b=30))
    return fig


def create_3d_shelter(length, width, height, roof_type, window_area, climate_type):
    fig = go.Figure()
    pad = 1.2
    fig.add_trace(go.Mesh3d(x=[-pad,length+pad,length+pad,-pad],
        y=[-pad,-pad,width+pad,width+pad], z=[-0.02]*4,
        i=[0,0], j=[1,2], k=[2,3],
        color="#d5dbdb", opacity=0.7, name="Ground", showlegend=True))

    vx=[0,length,length,0,0,length,length,0]
    vy=[0,0,width,width,0,0,width,width]
    vz=[0,0,0,0,height,height,height,height]
    wi=[0,0,1,1,2,2,3,3]; wj=[1,5,2,6,3,7,0,4]; wk=[5,4,6,5,7,6,4,7]
    wc="#e8dfd8" if climate_type=="cold" else "#f2e9e4"
    fig.add_trace(go.Mesh3d(x=vx,y=vy,z=vz,i=wi,j=wj,k=wk,
        color=wc, opacity=0.92, name="Walls", flatshading=True, showlegend=True))

    if roof_type == "pitched":
        rh = height + 1.2
        rx=vx+[0,length]; ry=vy+[width/2,width/2]; rz=vz+[rh,rh]
        ri=[4,5,4,4,7,7]; rj=[7,6,5,9,6,9]; rk=[8,9,9,8,9,8]
        fig.add_trace(go.Mesh3d(x=rx,y=ry,z=rz,i=ri,j=rj,k=rk,
            color="#7f8c8d", opacity=0.95, name="Pitched Roof",
            flatshading=True, showlegend=True))
    else:
        fig.add_trace(go.Mesh3d(x=[0,length,length,0],y=[0,0,width,width],
            z=[height]*4, i=[0,0], j=[1,2], k=[2,3],
            color="#95a5a6", opacity=0.95, name="Flat Roof",
            flatshading=True, showlegend=True))

    ww=min(length*0.65,max(1.2,window_area/1.3))
    wh=min(height*0.55,max(1.0,window_area/ww))
    wx1=(length-ww)/2; wx2=wx1+ww
    wz1=0.85; wz2=min(height-0.2, wz1+wh)
    fig.add_trace(go.Mesh3d(x=[wx1,wx2,wx2,wx1],y=[-0.02]*4,
        z=[wz1,wz1,wz2,wz2], i=[0,0], j=[1,2], k=[2,3],
        color="#2980b9", opacity=0.85, name="Glazing", showlegend=True))

    fig.add_trace(go.Mesh3d(x=[0.3,1.2,1.2,0.3],y=[-0.02]*4,
        z=[0,0,2.05,2.05], i=[0,0], j=[1,2], k=[2,3],
        color="#d35400", opacity=0.95, name="Door", showlegend=True))

    fig.update_layout(
        title=f"<b>3D Shelter Model ({roof_type.title()} Roof)</b>",
        scene=dict(
            xaxis=dict(title="L (m)", showbackground=False),
            yaxis=dict(title="W (m)", showbackground=False),
            zaxis=dict(title="H (m)", showbackground=False),
            aspectmode="data",
            camera=dict(eye=dict(x=-1.55,y=-1.85,z=1.25),
                        center=dict(x=0,y=0,z=-0.1))),
        legend=dict(orientation="h", yanchor="bottom", y=0.98, xanchor="right", x=1),
        margin=dict(l=0,r=0,t=40,b=0), height=460)
    return fig


def render_three_simulation_sections(city: str, sim_res: dict, title_suffix: str = ""):
    """
    Renders the three SIH-required simulation sections using the authoritative simulation result directly.
    """
    # 1. INDOOR TEMPERATURE SECTION
    st.markdown("### 🌡️ 1. Indoor Temperature & Thermal Comfort")
    st.plotly_chart(plot_temperature_curves(
        city, sim_res["outdoor_temperature"], sim_res["indoor_temperature"],
        title_suffix), use_container_width=True)

    mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)
    met = sim_res["comfort_metrics"]
    mc1.metric("Avg Indoor Temp", f"{met['avg']:.2f} °C")
    mc2.metric("Min Indoor Temp", f"{met['min_t']:.2f} °C")
    mc3.metric("Max Indoor Temp", f"{met['max_t']:.2f} °C")
    mc4.metric("Comfort Hours", f"{sim_res['comfort_hours']:.0f} / 168 h")
    mc5.metric("Comfort % (18–24 °C)", f"{sim_res['comfort_percentage']:.1f} %")
    mc6.metric("Discomfort DH", f"{sim_res['discomfort_degree_hours']:.1f} °C·h")

    st.caption(f"**Comfort Status:** `{sim_res['comfort_status']}`")
    st.markdown("---")

    # 2. SOLAR THERMAL ENERGY SECTION
    st.markdown("### ☀️ 2. Solar Thermal Energy")
    sc1, sc2, sc3, sc4 = st.columns(4)
    sol_eff = (sim_res["integrated_solar_energy_kwh"] / max(0.001, sim_res["integrated_incident_solar_kwh"])) * 100.0
    sc1.metric("Integrated Solar Gain", f"{sim_res['integrated_solar_energy_kwh']:.2f} kWh")
    sc2.metric("Total Incident Solar", f"{sim_res['integrated_incident_solar_kwh']:.2f} kWh")
    sc3.metric("Solar Harvesting Efficiency", f"{sol_eff:.1f} %")
    sc4.metric("Peak Useful Solar Gain", f"{max(sim_res['solar_thermal_gain']):.1f} W")

    st.plotly_chart(plot_solar_dynamics(sim_res), use_container_width=True)
    st.markdown("---")

    # 3. HEAT FLOW / HEAT LOSS SECTION
    st.markdown("### ⚡ 3. Heat Flow & Heat Loss Breakdown")
    cl = sim_res["component_heat_loss_kwh"]
    hc1, hc2, hc3, hc4, hc5, hc6, hc7 = st.columns(7)
    hc1.metric("Total Loss", f"{sim_res['total_heat_loss_kwh']:.1f} kWh")
    hc2.metric("Wall Loss", f"{cl['wall_loss_kwh']:.1f} kWh")
    hc3.metric("Roof Loss", f"{cl['roof_loss_kwh']:.1f} kWh")
    hc4.metric("Floor Loss", f"{cl['floor_loss_kwh']:.1f} kWh")
    hc5.metric("Glazing Loss", f"{cl['window_loss_kwh']:.1f} kWh")
    hc6.metric("Vent Loss", f"{cl['ventilation_loss_kwh']:.1f} kWh")
    hc7.metric("Radiation Loss", f"{cl['radiation_loss_kwh']:.1f} kWh")

    hf_col1, hf_col2 = st.columns([1.3, 1.0])
    with hf_col1:
        st.plotly_chart(plot_component_heat_flows(sim_res), use_container_width=True)
    with hf_col2:
        st.plotly_chart(plot_energy_balance_breakdown(sim_res), use_container_width=True)
    st.markdown("---")


# ==============================================================================
# HEADER
# ==============================================================================
st.markdown('<div class="main-title">🏕️ Area-Specific Shelter Designer</div>',
            unsafe_allow_html=True)
st.markdown('<div class="sub-title"><i>Generative AI & Building Physics for '
            'Climate-Resilient Thermal Comfort Maintenance</i></div>',
            unsafe_allow_html=True)

nav_mode = st.radio(
    "Select Feature Studio:",
    [
        "🏕️ Shelter Designer",
        "⚖️ Baseline vs Optimized",
        "🧱 Material Comparison Studio",
        "🏛️ Multiple Shelter Models",
    ],
    horizontal=True
)
st.markdown("---")


# ==============================================================================
# 🏕️ FEATURE 1: SHELTER DESIGNER (SIMPLE & ADVANCED)
# ==============================================================================
if nav_mode == "🏕️ Shelter Designer":
    app_mode = st.sidebar.radio("Interface Mode:", ["👤 Simple Mode", "🛠️ Advanced Mode"])

    if app_mode == "👤 Simple Mode":
        st.subheader("📋 Shelter Requirements")
        c1, c2, c3 = st.columns(3)
        with c1:
            city_s = st.selectbox("1. Location",
                ["leh","chennai","delhi","jaisalmer","bengaluru"],
                format_func=lambda x: {"leh":"🏔️ Leh (Cold)",
                    "chennai":"🌊 Chennai (Humid)","delhi":"🏙️ Delhi (Composite)",
                    "jaisalmer":"🏜️ Jaisalmer (Hot-Dry)",
                    "bengaluru":"🌳 Bengaluru (Moderate)"}[x])
        with c2:
            people = st.slider("2. Occupants", 1, 10, 4)
        with c3:
            home_type = st.radio("3. Permanence", ["Temporary","Permanent"], horizontal=True)

        if st.button("✨ Generate Climate-Optimized Design", type="primary", use_container_width=True):
            with st.spinner(f"Running Bayesian optimization for {city_s.upper()}…"):
                rec = get_recommendation(city=city_s, people=people, home_type=home_type, n_trials=40)
                weather = get_climate_data(city_s)
                if "error" in weather:
                    st.error(weather["error"]); st.stop()

                geo  = rec["geometry"]
                mats = rec["materials"]

                sim_res = run_simulation(
                    city=city_s,
                    length=geo["length_m"],
                    width=geo["width_m"],
                    height=geo["height_m"],
                    wall_material=rec.get("optimal_wall_material", mats["wall_material_id"]),
                    insulation_thickness_m=rec["optimal_insulation_m"],
                    window_area=rec["optimal_window_area_m2"],
                    glazing=rec.get("optimal_glazing", "double_clear"),
                    orientation=rec.get("optimal_orientation", "south"),
                    occupants=people,
                    hours_to_simulate=168,
                )
                if "error" in sim_res:
                    st.error(sim_res["error"]); st.stop()

                st.session_state["s_rec"]        = rec
                st.session_state["s_weather"]    = weather
                st.session_state["s_sim_result"] = sim_res

        if "s_rec" in st.session_state and st.session_state["s_rec"]["city"]==city_s:
            rec     = st.session_state["s_rec"]
            sim_res = st.session_state["s_sim_result"]
            geo     = rec["geometry"]
            mats    = rec["materials"]
            u_vals  = sim_res["u_values"]

            st.success(f"✅ Design for **{city_s.upper()}** ({rec['climate_name']}) — Discomfort: **{sim_res['discomfort_degree_hours']:.2f} DH**")

            render_three_simulation_sections(city_s, sim_res, f"— {home_type} Shelter")

            st.markdown("### 🏆 4. Recommended Envelope Specifications")
            r1, r2, r3 = st.columns(3)
            with r1:
                st.markdown(f"""<div class='card'>
<h4>🧱 Wall Assembly</h4>
<p><b>Material:</b> {mats['wall_material_name']}</p>
<p><b>Assembly U-Value:</b> {u_vals['wall_u']:.3f} W/m²K (R = {u_vals['wall_r_total']:.2f} m²K/W)</p>
<p><b>Thermal Mass:</b> {'High Mass' if home_type=='Permanent' else 'Lightweight Prefab'}</p>
</div>""", unsafe_allow_html=True)
                st.markdown(f"""<div class='card'>
<h4>🏠 Roof System</h4>
<p><b>Design:</b> {mats['roof_material']}</p>
<p><b>Roof U-Value:</b> {u_vals['roof_u']:.3f} W/m²K (R = {u_vals['roof_r_total']:.2f} m²K/W)</p>
<p><b>Profile:</b> {mats['roof_type'].title()} Roof</p>
</div>""", unsafe_allow_html=True)
            with r2:
                st.markdown(f"""<div class='card'>
<h4>🛡️ Thermal Insulation</h4>
<p><b>Type:</b> {mats['insulation_type']}</p>
<p><b>Optimal Thickness:</b> <span class='metric-badge'>{rec['optimal_insulation_mm']:.2f} mm</span></p>
</div>""", unsafe_allow_html=True)
                st.markdown(f"""<div class='card'>
<h4>🪟 Fenestration & Glazing</h4>
<p><b>Spec:</b> {rec.get('optimal_glazing_name', mats['glazing_type'])}</p>
<p><b>Window Area:</b> <span class='metric-badge'>{rec['optimal_window_area_m2']:.2f} m²</span></p>
</div>""", unsafe_allow_html=True)
            with r3:
                st.markdown(f"""<div class='card'>
<h4>🧭 Orientation & Passive Solar</h4>
<p><b>Orientation:</b> {rec.get('optimal_orientation', 'south').title()} ({mats['orientation_advice']})</p>
<p><b>Shading:</b> {mats['shading_advice']}</p>
</div>""", unsafe_allow_html=True)
                st.markdown(f"""<div class='card'>
<h4>📐 Auto-Sizing Summary</h4>
<p><b>Floor:</b> {geo['floor_area_m2']:.2f} m² ({geo['length_m']:.2f} × {geo['width_m']:.2f})</p>
<p><b>Height:</b> {geo['height_m']:.2f} m &nbsp;|&nbsp; <b>Vol:</b> {geo['volume_m3']:.2f} m³</p>
</div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 🏗️ 5. Floor Plan & 3D Interactive Model")
            g1, g2 = st.columns(2)
            with g1:
                st.plotly_chart(create_2d_floorplan(
                    geo["length_m"], geo["width_m"],
                    rec["optimal_window_area_m2"],
                    mats["orientation_advice"], rec["climate_type"]),
                    use_container_width=True)
            with g2:
                st.plotly_chart(create_3d_shelter(
                    geo["length_m"], geo["width_m"], geo["height_m"],
                    mats["roof_type"], rec["optimal_window_area_m2"],
                    rec["climate_type"]), use_container_width=True)
            st.markdown("---")
            st.markdown("### 💡 6. Design Rationale & Physics Explanation")
            st.info(rec["explanation"])

    else:
        st.subheader("🛠️ Engineering Parameter Control")
        st.sidebar.header("📍 1. Location")
        city_a = st.sidebar.selectbox("Climate Zone", ["leh","chennai","delhi","jaisalmer","bengaluru"])

        st.sidebar.header("📐 2. Geometry")
        l_a = st.sidebar.slider("Length (m)", 3.0, 10.0, 4.0, 0.1)
        w_a = st.sidebar.slider("Width (m)",  3.0, 10.0, 3.0, 0.1)
        h_a = st.sidebar.slider("Height (m)", 2.5,  4.0, 2.8, 0.1)
        rf_type_a = st.sidebar.selectbox("Roof Type", ["flat", "pitched"])

        st.sidebar.header("🧱 3. Materials & Envelope")
        all_mat  = load_all_materials()
        mat_keys = [k for k in all_mat if "error" not in k]
        mat_key  = st.sidebar.selectbox("Wall Material", mat_keys,
            format_func=lambda k: f"{all_mat[k].get('name',k)} (k={all_mat[k].get('thermal_conductivity','-')})")
        ins_mm = st.sidebar.slider("Insulation (mm)", 0, 300, 50, 5)
        win_a  = st.sidebar.slider("Window Area (m²)", 0.0, 15.0, 2.0, 0.2)
        glaze_key = st.sidebar.selectbox("Glazing Type", list(GLAZING_PROPERTIES.keys()), index=1,
            format_func=lambda k: GLAZING_PROPERTIES[k]["name"])
        orient_key = st.sidebar.selectbox("Glazing Orientation", ["south", "north", "east", "west"], index=0,
            format_func=lambda k: f"{k.title()} Facade")
        occ_a  = st.sidebar.slider("Occupants", 1, 10, 2)

        tab_sim, tab_opt = st.tabs(["🔬 Simulation", "🤖 AI Optimization"])

        with tab_sim:
            st.markdown("#### Physical Building Simulation")
            if st.button("🚀 Run Simulation", type="primary"):
                with st.spinner(f"Simulating {city_a.upper()}…"):
                    sim_res_a = run_simulation(
                        city=city_a,
                        length=l_a,
                        width=w_a,
                        height=h_a,
                        roof_type=rf_type_a,
                        wall_material=mat_key,
                        insulation_thickness_m=ins_mm / 1000.0,
                        window_area=win_a,
                        glazing=glaze_key,
                        orientation=orient_key,
                        occupants=occ_a,
                        hours_to_simulate=168,
                    )
                    if "error" in sim_res_a:
                        st.error(sim_res_a["error"]); st.stop()

                    render_three_simulation_sections(
                        city_a, sim_res_a,
                        f"({all_mat[mat_key]['name']} + {ins_mm}mm Ins, {GLAZING_PROPERTIES[glaze_key]['name']})"
                    )

                    st.markdown("#### 🏗️ 3D Preview")
                    ct = CLIMATE_MAPPING.get(city_a, "composite")
                    st.plotly_chart(create_3d_shelter(l_a,w_a,h_a,rf_type_a,win_a,ct), use_container_width=True)

        with tab_opt:
            st.markdown("#### Multi-Variable Bayesian Optimization (Optuna TPE)")
            oc1, oc2 = st.columns(2)
            with oc1:
                trials = st.slider("Trials", 20, 100, 40, 10)
            with oc2:
                ct_a = CLIMATE_MAPPING.get(city_a, "composite")
                st.info(f"Zone: **{city_a.upper()}** ({CLIMATE_DESCRIPTIONS.get(ct_a, ct_a)})")

            if st.button("🧠 Execute Optimization"):
                prog = st.progress(0); stat = st.empty()
                stat.text("Optimizing 5-parameter envelope space…"); prog.progress(25)
                try:
                    res = run_optimization(
                        city=city_a,
                        length=l_a,
                        width=w_a,
                        height=h_a,
                        wall_material=None,
                        glazing=None,
                        orientation=None,
                        occupants=occ_a,
                        n_trials=trials
                    )
                    prog.progress(100); stat.text("Converged!")
                    st.subheader(f"🏆 Optimal Parameters for {city_a.upper()}")
                    rc1, rc2, rc3, rc4, rc5 = st.columns(5)
                    rc1.metric("Insulation", f"{res['insulation_mm']:.1f} mm")
                    rc2.metric("Window Area", f"{res['window_area_m2']:.2f} m²")
                    rc3.metric("Wall Material", all_mat.get(res['wall_material'], {}).get('name', res['wall_material']))
                    rc4.metric("Glazing Spec", res['glazing_name'])
                    rc5.metric("Orientation", res['orientation'].title())

                    st.markdown(f"**Discomfort Score:** `{res['discomfort_score']:.2f} °C·h`")
                    opt_sim = res.get("simulation_result")
                    render_three_simulation_sections(
                        city_a, opt_sim,
                        f"(Optimized: {res['insulation_mm']:.0f}mm Ins, {res['window_area_m2']:.1f}m² Win)"
                    )
                except Exception as e:
                    st.error(f"Optimization failed: {e}")


# ==============================================================================
# ⚖️ FEATURE 2: BASELINE VS OPTIMIZED COMPARISON
# ==============================================================================
elif nav_mode == "⚖️ Baseline vs Optimized":
    st.subheader("⚖️ Baseline (Uninsulated/Standard) vs AI-Optimized Shelter")
    st.caption("Demonstrating energy savings and thermal comfort gains under identical climate and geometry.")

    b_col1, b_col2, b_col3 = st.columns(3)
    with b_col1:
        comp_city = st.selectbox("Select Climate Zone", ["leh", "chennai", "delhi", "jaisalmer", "bengaluru"],
            format_func=lambda x: {"leh":"🏔️ Leh (Cold)", "chennai":"🌊 Chennai (Humid)",
                                   "delhi":"🏙️ Delhi (Composite)", "jaisalmer":"🏜️ Jaisalmer (Hot-Dry)",
                                   "bengaluru":"🌳 Bengaluru (Moderate)"}[x])
    with b_col2:
        comp_people = st.slider("Occupants", 1, 10, 4)
    with b_col3:
        comp_home_type = st.radio("Permanence", ["Temporary", "Permanent"], horizontal=True)

    if st.button("🚀 Run Comparative Benchmark", type="primary", use_container_width=True):
        with st.spinner("Simulating Baseline vs Optimized shelter responses…"):
            # 1. Get Optimized specs
            rec_comp = get_recommendation(comp_city, people=comp_people, home_type=comp_home_type, n_trials=35)
            geo_c = rec_comp["geometry"]
            mats_c = rec_comp["materials"]

            # 2. Run Baseline Simulation (uninsulated brick, single clear glass, 2.0m² window)
            sim_baseline = run_simulation(
                city=comp_city,
                length=geo_c["length_m"],
                width=geo_c["width_m"],
                height=geo_c["height_m"],
                wall_material="brick",
                insulation_thickness_m=0.0,
                window_area=2.0,
                glazing="single_clear",
                orientation="south",
                occupants=comp_people,
                hours_to_simulate=168,
            )

            # 3. Run Optimized Simulation
            sim_opt = run_simulation(
                city=comp_city,
                length=geo_c["length_m"],
                width=geo_c["width_m"],
                height=geo_c["height_m"],
                wall_material=rec_comp.get("optimal_wall_material", mats_c["wall_material_id"]),
                insulation_thickness_m=rec_comp["optimal_insulation_m"],
                window_area=rec_comp["optimal_window_area_m2"],
                glazing=rec_comp.get("optimal_glazing", "double_clear"),
                orientation=rec_comp.get("optimal_orientation", "south"),
                occupants=comp_people,
                hours_to_simulate=168,
            )

            st.session_state["comp_res"] = {
                "city": comp_city,
                "baseline": sim_baseline,
                "optimized": sim_opt,
                "rec": rec_comp,
            }

    if "comp_res" in st.session_state and st.session_state["comp_res"]["city"] == comp_city:
        cdata = st.session_state["comp_res"]
        s_base = cdata["baseline"]
        s_opt = cdata["optimized"]
        r_info = cdata["rec"]

        # Comparative Delta Metrics
        st.markdown("### 📊 Performance Impact Summary")
        d1, d2, d3, d4 = st.columns(4)

        base_dh = s_base["discomfort_degree_hours"]
        opt_dh = s_opt["discomfort_degree_hours"]
        dh_reduction = ((base_dh - opt_dh) / max(0.01, base_dh)) * 100.0

        base_loss = s_base["total_heat_loss_kwh"]
        opt_loss = s_opt["total_heat_loss_kwh"]
        loss_reduction = ((base_loss - opt_loss) / max(0.01, base_loss)) * 100.0

        d1.metric("Comfort Hours", f"{s_opt['comfort_hours']:.0f} h", delta=f"{s_opt['comfort_hours'] - s_base['comfort_hours']:+.0f} h vs Baseline")
        d2.metric("Comfort %", f"{s_opt['comfort_percentage']:.1f} %", delta=f"{s_opt['comfort_percentage'] - s_base['comfort_percentage']:+.1f}%")
        d3.metric("Discomfort Degree-Hours", f"{opt_dh:.1f} °C·h", delta=f"-{dh_reduction:.1f}% Reduction", delta_color="inverse")
        d4.metric("Total Envelope Heat Loss", f"{opt_loss:.1f} kWh", delta=f"-{loss_reduction:.1f}% Loss Cut", delta_color="inverse")

        st.markdown("---")

        # Overlaid Temperature Comparison Plot
        st.markdown("### 📈 168-Hour Thermal Response Overlay")
        hours = list(range(len(s_opt["indoor_temperature"])))
        fig_comp = go.Figure()

        fig_comp.add_hrect(
            y0=18.0, y1=24.0, fillcolor="rgba(46,204,113,0.15)", layer="below",
            line=dict(color="rgba(46,204,113,0.5)", width=1, dash="dash"),
            annotation_text="Comfort Band (18–24 °C)", annotation_position="top left"
        )
        fig_comp.add_trace(go.Scatter(
            x=hours, y=s_base["outdoor_temperature"],
            mode="lines", name="Ambient Outdoor (°C)",
            line=dict(color="#64748b", width=1.5, dash="dot")
        ))
        fig_comp.add_trace(go.Scatter(
            x=hours, y=s_base["indoor_temperature"],
            mode="lines", name="❌ Baseline Indoor (°C)",
            line=dict(color="#ef4444", width=2.5, dash="dash")
        ))
        fig_comp.add_trace(go.Scatter(
            x=hours, y=s_opt["indoor_temperature"],
            mode="lines", name="✅ Optimized Indoor (°C)",
            line=dict(color="#10b981", width=3)
        ))

        fig_comp.update_layout(
            title="<b>Baseline vs AI-Optimized Indoor Thermal Response</b>",
            xaxis=dict(title="Time (Hours)", showgrid=True, gridcolor="#e9ecef"),
            yaxis=dict(title="Temperature (°C)", showgrid=True, gridcolor="#e9ecef"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", height=420
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        # Side-by-side specs comparison table
        st.markdown("### 📋 Design Specifications Comparison")
        comp_df = pd.DataFrame({
            "Specification": [
                "Wall Material", "Insulation Thickness", "Wall U-Value",
                "Roof U-Value", "Glazing Type", "Window Area", "Orientation",
                "Comfort Hours", "Discomfort Score", "Weekly Heat Loss"
            ],
            "Baseline Design": [
                "Standard Brick Masonry", "0 mm (Uninsulated)", f"{s_base['u_values']['wall_u']:.3f} W/m²K",
                f"{s_base['u_values']['roof_u']:.3f} W/m²K", "Single Glazed Clear", "2.00 m²", "South Facade",
                f"{s_base['comfort_hours']:.0f} / 168 h ({s_base['comfort_percentage']:.1f}%)",
                f"{s_base['discomfort_degree_hours']:.1f} °C·h", f"{s_base['total_heat_loss_kwh']:.1f} kWh"
            ],
            "AI-Optimized Design": [
                r_info.get("optimal_wall_material", "brick").title(),
                f"{r_info['optimal_insulation_mm']:.0f} mm PUF", f"{s_opt['u_values']['wall_u']:.3f} W/m²K",
                f"{s_opt['u_values']['roof_u']:.3f} W/m²K", r_info.get("optimal_glazing_name", "Double Clear"),
                f"{r_info['optimal_window_area_m2']:.2f} m²", f"{r_info.get('optimal_orientation', 'south').title()} Facade",
                f"{s_opt['comfort_hours']:.0f} / 168 h ({s_opt['comfort_percentage']:.1f}%)",
                f"{s_opt['discomfort_degree_hours']:.1f} °C·h", f"{s_opt['total_heat_loss_kwh']:.1f} kWh"
            ]
        })
        st.table(comp_df)


# ==============================================================================
# 🧱 FEATURE 3: MATERIAL COMPARISON STUDIO
# ==============================================================================
elif nav_mode == "🧱 Material Comparison Studio":
    st.subheader("🧱 Multi-Material Envelope Comparison Studio")
    st.caption("Compare the thermal performance of structural materials under strictly identical climate, geometry, and occupancy.")

    m_c1, m_c2, m_c3, m_c4 = st.columns(4)
    with m_c1:
        mat_city = st.selectbox("Climate Zone", ["leh", "chennai", "delhi", "jaisalmer", "bengaluru"],
            format_func=lambda x: {"leh":"🏔️ Leh (Cold)", "chennai":"🌊 Chennai (Humid)",
                                   "delhi":"🏙️ Delhi (Composite)", "jaisalmer":"🏜️ Jaisalmer (Hot-Dry)",
                                   "bengaluru":"🌳 Bengaluru (Moderate)"}[x], key="m_city")
    with m_c2:
        m_ins_mm = st.slider("Added Insulation (mm)", 0, 200, 50, 10, key="m_ins")
    with m_c3:
        m_win = st.slider("Window Area (m²)", 1.0, 10.0, 2.5, 0.5, key="m_win")
    with m_c4:
        m_occ = st.slider("Occupants", 1, 8, 3, key="m_occ")

    all_mat = load_all_materials()
    candidate_materials = [k for k in all_mat if "error" not in k and isinstance(all_mat[k], dict)]

    if st.button("🧪 Evaluate Envelope Materials", type="primary", use_container_width=True):
        with st.spinner("Simulating all candidate materials through the authoritative engine…"):
            mat_results = []
            for m_key in candidate_materials:
                m_info = all_mat[m_key]
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
            st.session_state["mat_eval"] = {
                "city": mat_city,
                "results": mat_results,
            }

    if "mat_eval" in st.session_state and st.session_state["mat_eval"]["city"] == mat_city:
        me_data = st.session_state["mat_eval"]["results"]

        st.markdown("### 📈 Multi-Material Thermal Curves")
        fig_mat = go.Figure()
        fig_mat.add_hrect(
            y0=18.0, y1=24.0, fillcolor="rgba(46,204,113,0.15)", layer="below",
            line=dict(color="rgba(46,204,113,0.5)", width=1, dash="dash"),
            annotation_text="Comfort Band (18–24 °C)", annotation_position="top left"
        )
        if me_data:
            fig_mat.add_trace(go.Scatter(
                x=list(range(168)), y=me_data[0]["outdoor_temps"],
                mode="lines", name="Outdoor Ambient",
                line=dict(color="#94a3b8", width=1.5, dash="dot")
            ))

        colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"]
        for idx, item in enumerate(me_data):
            fig_mat.add_trace(go.Scatter(
                x=list(range(168)), y=item["indoor_temps"],
                mode="lines", name=item["name"],
                line=dict(color=colors[idx % len(colors)], width=2.2)
            ))

        fig_mat.update_layout(
            title=f"<b>Indoor Temperature Progression Across Materials ({mat_city.upper()})</b>",
            xaxis=dict(title="Time (Hours)", showgrid=True, gridcolor="#e9ecef"),
            yaxis=dict(title="Indoor Temp (°C)", showgrid=True, gridcolor="#e9ecef"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", height=420
        )
        st.plotly_chart(fig_mat, use_container_width=True)

        # Comparative Summary Table
        st.markdown("### 📋 Material Performance Comparison Table")
        m_table_rows = []
        for r in me_data:
            m_table_rows.append({
                "Material": r["name"],
                "k (W/mK)": r["conductivity"],
                "Wall U-Value (W/m²K)": f"{r['wall_u']:.3f}",
                "Avg Temp (°C)": f"{r['avg_t']:.1f}",
                "Min Temp (°C)": f"{r['min_t']:.1f}",
                "Max Temp (°C)": f"{r['max_t']:.1f}",
                "Comfort Hours": f"{r['comfort_hrs']:.0f} h ({r['comfort_pct']:.1f}%)",
                "Discomfort (°C·h)": f"{r['discomfort_dh']:.1f}",
                "Total Loss (kWh)": f"{r['total_loss_kwh']:.1f}",
            })
        st.dataframe(pd.DataFrame(m_table_rows), use_container_width=True)

        # Comparative Bar Charts
        st.markdown("### 📊 Discomfort & Envelope Heat Loss Comparison")
        mc_col1, mc_col2 = st.columns(2)
        names = [r["name"] for r in me_data]

        with mc_col1:
            fig_dh = go.Figure(go.Bar(
                x=names, y=[r["discomfort_dh"] for r in me_data],
                marker=dict(color="#f59e0b"),
                text=[f"{r['discomfort_dh']:.0f} DH" for r in me_data], textposition="auto"
            ))
            fig_dh.update_layout(title="<b>Discomfort Degree-Hours (Lower is Better)</b>", yaxis_title="°C·h", height=320)
            st.plotly_chart(fig_dh, use_container_width=True)

        with mc_col2:
            fig_hl = go.Figure(go.Bar(
                x=names, y=[r["total_loss_kwh"] for r in me_data],
                marker=dict(color="#ef4444"),
                text=[f"{r['total_loss_kwh']:.0f} kWh" for r in me_data], textposition="auto"
            ))
            fig_hl.update_layout(title="<b>Total Weekly Heat Loss (Lower is Better)</b>", yaxis_title="kWh", height=320)
            st.plotly_chart(fig_hl, use_container_width=True)


# ==============================================================================
# 🏛️ FEATURE 4: MULTIPLE SHELTER MODELS
# ==============================================================================
elif nav_mode == "🏛️ Multiple Shelter Models":
    st.subheader("🏛️ Multiple Shelter Archetype Models")
    st.caption("Simulate and benchmark distinct shelter geometric forms and roof systems using the unified simulation pipeline.")

    sm_col1, sm_col2, sm_col3 = st.columns(3)
    with sm_col1:
        arch_city = st.selectbox("Climate Zone", ["leh", "chennai", "delhi", "jaisalmer", "bengaluru"],
            format_func=lambda x: {"leh":"🏔️ Leh (Cold)", "chennai":"🌊 Chennai (Humid)",
                                   "delhi":"🏙️ Delhi (Composite)", "jaisalmer":"🏜️ Jaisalmer (Hot-Dry)",
                                   "bengaluru":"🌳 Bengaluru (Moderate)"}[x], key="arch_c")
    with sm_col2:
        model_choice = st.selectbox(
            "Shelter Archetype Model",
            list(SHELTER_MODELS.keys()),
            format_func=lambda k: SHELTER_MODELS[k]["name"]
        )
    with sm_col3:
        arch_occ = st.slider("Occupants", 1, 8, 3, key="arch_occ")

    sel_spec = SHELTER_MODELS[model_choice]
    st.info(f"**Model Profile:** {sel_spec['description']}")

    # Dimension Controls based on selected model
    if model_choice == "custom_dimensions":
        cd1, cd2, cd3, cd4 = st.columns(4)
        with cd1: arch_l = st.slider("Length (m)", 2.5, 10.0, 4.0, 0.1)
        with cd2: arch_w = st.slider("Width (m)", 2.5, 10.0, 3.0, 0.1)
        with cd3: arch_h = st.slider("Height (m)", 2.2, 4.0, 2.8, 0.1)
        with cd4: arch_rf = st.selectbox("Roof Type", ["flat", "pitched"])
    else:
        def_dims = sel_spec["default_dimensions"]
        arch_l = def_dims["length"]
        arch_w = def_dims["width"]
        arch_h = def_dims["height"]
        arch_rf = sel_spec["roof_type"]
        st.caption(f"📐 Geometry: **{arch_l:.2f} m × {arch_w:.2f} m × {arch_h:.2f} m** | Roof: **{arch_rf.title()}**")

    if st.button("🚀 Run Archetype Simulation", type="primary", use_container_width=True):
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
            if "error" in sim_arch:
                st.error(sim_arch["error"]); st.stop()

            # Benchmark all 4 standard models under identical floor area
            comp_models = []
            std_floor_area = arch_l * arch_w
            for m_key in ["rectangular_flat", "rectangular_pitched", "compact_shelter", "elongated_shelter"]:
                m_def = SHELTER_MODELS[m_key]
                d = m_def["default_dimensions"]
                # Scale dimensions to identical floor area for fair geometric comparison
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

            st.session_state["arch_eval"] = {
                "city": arch_city,
                "current_sim": sim_arch,
                "current_model": sel_spec["name"],
                "roof_type": arch_rf,
                "dims": (arch_l, arch_w, arch_h),
                "comp_models": comp_models,
            }

    if "arch_eval" in st.session_state and st.session_state["arch_eval"]["city"] == arch_city:
        a_data = st.session_state["arch_eval"]
        cur_sim = a_data["current_sim"]
        dims = a_data["dims"]

        # Render 3D representation
        st.markdown("### 🏗️ 3D Model & Floor Plan")
        a_g1, a_g2 = st.columns(2)
        with a_g1:
            ct = CLIMATE_MAPPING.get(arch_city, "composite")
            st.plotly_chart(create_3d_shelter(dims[0], dims[1], dims[2], a_data["roof_type"], 2.2, ct), use_container_width=True)
        with a_g2:
            st.plotly_chart(create_2d_floorplan(dims[0], dims[1], 2.2, "South Facade", ct), use_container_width=True)

        st.markdown("---")
        # Render the 3 simulation sections for the chosen model
        render_three_simulation_sections(arch_city, cur_sim, f"— {a_data['current_model']}")

        # Render Cross-Archetype Benchmark Matrix
        st.markdown("### 📊 Cross-Archetype Comparative Matrix (Identical Floor Area)")
        st.caption("Evaluates how building form and roof geometry impact thermal performance under identical floor area.")
        arch_matrix_rows = []
        for m in a_data["comp_models"]:
            arch_matrix_rows.append({
                "Archetype Model": m["name"],
                "Roof Profile": m["roof"],
                "Aspect Ratio (L:W)": m["aspect"],
                "Total Envelope Surface (m²)": f"{m['envelope_area']:.1f}",
                "Enclosed Volume (m³)": f"{m['volume']:.1f}",
                "Comfort Percentage": f"{m['comfort_pct']:.1f} %",
                "Discomfort Score (°C·h)": f"{m['discomfort_dh']:.1f}",
                "Total Heat Loss (kWh)": f"{m['heat_loss_kwh']:.1f}",
            })
        st.dataframe(pd.DataFrame(arch_matrix_rows), use_container_width=True)