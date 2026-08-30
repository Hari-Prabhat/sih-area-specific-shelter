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
from services.visual3d import build_3d_shelter

# ==============================================================================
# PAGE CONFIG
# ==============================================================================
st.set_page_config(
    page_title="Area-Specific Shelter Designer | SIH",
    page_icon="🏕️",
    layout="wide",
    initial_sidebar_state="collapsed"
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
# PLOTTING THEME CONFIGURATION (HIGH-CONTRAST DARK THEME)
# ==============================================================================
DARK_PAPER_BG = "#1e293b"      # Card slate background
DARK_PLOT_BG  = "#0f172a"      # Deep midnight plot area
DARK_GRID_COLOR = "rgba(148, 163, 184, 0.14)"
DARK_ZEROLINE_COLOR = "rgba(148, 163, 184, 0.32)"
DARK_TEXT_PRIMARY = "#f8fafc"   # Crisp bright white/slate
DARK_TEXT_MUTED   = "#94a3b8"   # Slate muted
DARK_ACCENT_CYAN  = "#38bdf8"   # High-visibility cyan for titles/highlights
DARK_FONT_FAMILY  = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"


def apply_dark_theme(fig: go.Figure, title_text: str = "", height: int = 400, show_legend: bool = True):
    """
    Applies unified high-contrast dark theme styling across all Plotly figures.
    Ensures all labels, axes, titles, and legends are crisp, visible, and aesthetically premium.
    """
    fig.update_layout(
        title=dict(
            text=f"<b>{title_text}</b>" if title_text else "",
            font=dict(family=DARK_FONT_FAMILY, size=15, color=DARK_ACCENT_CYAN),
            x=0.01,
            y=0.97
        ),
        paper_bgcolor=DARK_PAPER_BG,
        plot_bgcolor=DARK_PLOT_BG,
        font=dict(family=DARK_FONT_FAMILY, color=DARK_TEXT_PRIMARY, size=12),
        hoverlabel=dict(
            bgcolor="#0f172a",
            font_size=12,
            font_family=DARK_FONT_FAMILY,
            font_color="#ffffff",
            bordercolor=DARK_ACCENT_CYAN
        ),
        margin=dict(l=45, r=35, t=55, b=45),
        height=height,
    )
    if show_legend:
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1.0,
                font=dict(color=DARK_TEXT_PRIMARY, size=11, family=DARK_FONT_FAMILY),
                bgcolor="rgba(15, 23, 42, 0.85)",
                bordercolor="rgba(56, 189, 248, 0.25)",
                borderwidth=1,
            )
        )
    fig.update_xaxes(
        showgrid=True,
        gridcolor=DARK_GRID_COLOR,
        zeroline=False,
        tickfont=dict(color=DARK_TEXT_PRIMARY, size=11, family=DARK_FONT_FAMILY),
        title_font=dict(color=DARK_TEXT_MUTED, size=12, family=DARK_FONT_FAMILY)
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=DARK_GRID_COLOR,
        zeroline=True,
        zerolinecolor=DARK_ZEROLINE_COLOR,
        tickfont=dict(color=DARK_TEXT_PRIMARY, size=11, family=DARK_FONT_FAMILY),
        title_font=dict(color=DARK_TEXT_MUTED, size=12, family=DARK_FONT_FAMILY)
    )
    return fig


def plot_temperature_curves(city, outdoor_temps, indoor_temps, title_suffix=""):
    hours = list(range(len(indoor_temps)))
    fig = go.Figure()

    # Comfort Zone Band (18–24 °C)
    fig.add_hrect(
        y0=18.0, y1=24.0,
        fillcolor="rgba(34, 197, 94, 0.16)", layer="below",
        line=dict(color="#22c55e", width=1.5, dash="dash"),
        annotation_text="🌿 Comfort Zone (18–24 °C)",
        annotation_position="top left",
        annotation=dict(
            font=dict(size=11, color="#4ade80", family=DARK_FONT_FAMILY),
            bgcolor="rgba(15, 23, 42, 0.85)",
            bordercolor="rgba(34, 197, 94, 0.5)",
            borderwidth=1,
            borderpad=4
        )
    )

    # Outdoor Ambient trace
    fig.add_trace(go.Scatter(
        x=hours,
        y=[round(float(t), 2) for t in outdoor_temps[:len(indoor_temps)]],
        mode="lines", name="Outdoor Ambient (°C)",
        line=dict(color="#38bdf8", width=2.0, dash="dash"),
        hovertemplate="Outdoor: <b>%{y:.2f} °C</b><extra></extra>"
    ))

    # Indoor Predicted trace
    fig.add_trace(go.Scatter(
        x=hours, y=indoor_temps,
        mode="lines", name="Indoor Predicted (°C)",
        line=dict(color="#f87171", width=3.2),
        hovertemplate="Indoor: <b>%{y:.2f} °C</b><extra></extra>"
    ))

    fig.update_xaxes(
        title="Time (Simulation Hours)",
        tickmode="array",
        tickvals=[0, 24, 48, 72, 96, 120, 144, 168],
        ticktext=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "End"],
    )
    fig.update_yaxes(title="Temperature (°C)")

    apply_dark_theme(fig, f"{city.upper()} — 168-Hour Thermal Comfort Response {title_suffix}", height=420)
    fig.update_layout(hovermode="x unified")
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
            hovertemplate="Irradiance: <b>%{y:.1f} W/m²</b><extra></extra>"
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=hours, y=sim_result["solar_power"],
            mode="lines", name="⚡ Incident Window Power (W)",
            line=dict(color="#fbbf24", width=2.2),
            hovertemplate="Incident Power: <b>%{y:.1f} W</b><extra></extra>"
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=hours, y=sim_result["solar_thermal_gain"],
            mode="lines", name="🔥 Useful Thermal Gain (W)",
            line=dict(color="#f43f5e", width=2.8),
            fill="tozeroy", fillcolor="rgba(244, 63, 94, 0.20)",
            hovertemplate="Thermal Gain: <b>%{y:.1f} W</b><extra></extra>"
        ),
        secondary_y=False,
    )

    fig.update_xaxes(
        title="Time (Simulation Hours)",
        tickmode="array",
        tickvals=[0, 24, 48, 72, 96, 120, 144, 168],
        ticktext=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "End"],
        showgrid=True, gridcolor=DARK_GRID_COLOR, tickfont=dict(color=DARK_TEXT_PRIMARY)
    )
    fig.update_yaxes(
        title=dict(text="Solar Power / Thermal Gain (Watts)", font=dict(color="#f43f5e", size=12)),
        secondary_y=False, showgrid=True, gridcolor=DARK_GRID_COLOR, tickfont=dict(color=DARK_TEXT_PRIMARY)
    )
    fig.update_yaxes(
        title=dict(text="Global Irradiance (W/m²)", font=dict(color="#f59e0b", size=12)),
        secondary_y=True, showgrid=False, tickfont=dict(color="#f59e0b")
    )

    apply_dark_theme(fig, "☀️ Hourly Solar Flux & Fenestration Thermal Harvesting", height=400)
    fig.update_layout(hovermode="x unified")
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
        line=dict(color="#a78bfa", width=2.0),
        hovertemplate="Wall Loss: <b>%{y:.1f} W</b><extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=sim_result["roof_heat_flow"],
        mode="lines", name="🏠 Roof Loss (W)",
        line=dict(color="#f472b6", width=2.0),
        hovertemplate="Roof Loss: <b>%{y:.1f} W</b><extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=sim_result["floor_heat_flow"],
        mode="lines", name="🪵 Floor Loss (W)",
        line=dict(color="#c084fc", width=1.8, dash="dot"),
        hovertemplate="Floor Loss: <b>%{y:.1f} W</b><extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=sim_result["window_heat_flow"],
        mode="lines", name="🪟 Glazing Loss (W)",
        line=dict(color="#22d3ee", width=2.0),
        hovertemplate="Glazing Loss: <b>%{y:.1f} W</b><extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=sim_result["ventilation_heat_flow"],
        mode="lines", name="💨 Ventilation Loss (W)",
        line=dict(color="#94a3b8", width=1.8, dash="dash"),
        hovertemplate="Vent Loss: <b>%{y:.1f} W</b><extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=sim_result["radiation_heat_flow"],
        mode="lines", name="🌌 Radiation Loss (W)",
        line=dict(color="#60a5fa", width=1.8, dash="dot"),
        hovertemplate="Rad Loss: <b>%{y:.1f} W</b><extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=sim_result["net_heat_flow"],
        mode="lines", name="⚖️ Net Heat Flow (W)",
        line=dict(color="#34d399", width=2.8),
        hovertemplate="Net Flow: <b>%{y:.1f} W</b><extra></extra>"
    ))

    fig.update_xaxes(
        title="Time (Simulation Hours)",
        tickmode="array",
        tickvals=[0, 24, 48, 72, 96, 120, 144, 168],
        ticktext=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "End"],
    )
    fig.update_yaxes(title="Thermal Power (Watts)")

    apply_dark_theme(fig, "⚡ Hourly Dynamic Component Heat Flow Rates (Watts)", height=410)
    fig.update_layout(hovermode="x unified")
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
    colors = ["#f59e0b", "#a78bfa", "#f472b6", "#c084fc", "#22d3ee", "#94a3b8", "#60a5fa", "#ef4444"]

    fig = go.Figure(data=[
        go.Bar(
            x=categories, y=values,
            marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.15)", width=1)),
            text=[f"<b>{v:.1f} kWh</b>" for v in values],
            textfont=dict(color="#ffffff", size=11, family=DARK_FONT_FAMILY),
            textposition="auto",
            hovertemplate="<b>%{x}</b>: %{y:.2f} kWh<extra></extra>"
        )
    ])
    fig.update_xaxes(tickangle=-25, tickfont=dict(color=DARK_TEXT_PRIMARY, size=11, family=DARK_FONT_FAMILY))
    fig.update_yaxes(title="Energy (kWh)")
    apply_dark_theme(fig, "📊 Weekly Component Energy Totals (kWh / 168 h)", height=380, show_legend=False)
    return fig


def create_2d_floorplan(length, width, window_area, orientation_advice, climate_type):
    fig = go.Figure()
    wt = 0.22
    # Outer structure
    fig.add_shape(type="rect", x0=0, y0=0, x1=length, y1=width,
        line=dict(color="#38bdf8", width=4), fillcolor="#1e293b", layer="below")
    # Inner perimeter
    fig.add_shape(type="rect", x0=wt, y0=wt, x1=length-wt, y1=width-wt,
        line=dict(color="#475569", width=1.5, dash="dot"), fillcolor="#0f172a")

    wl = min(length*0.7, max(1.2, window_area/1.3))
    ws = (length - wl) / 2
    # South Glazing
    fig.add_shape(type="rect", x0=ws, y0=-0.08, x1=ws+wl, y1=wt+0.08,
        line=dict(color="#06b6d4", width=3), fillcolor="#22d3ee")

    # Door
    dw = 0.9
    fig.add_shape(type="rect", x0=0.3, y0=-0.08, x1=0.3+dw, y1=wt+0.08,
        line=dict(color="#ea580c", width=3), fillcolor="#f97316")

    if climate_type in ("hot_humid", "moderate"):
        fig.add_shape(type="rect", x0=ws+0.3, y0=width-wt-0.08,
            x1=ws+wl-0.3, y1=width+0.08,
            line=dict(color="#06b6d4", width=3), fillcolor="#22d3ee")
        fig.add_annotation(x=length/2, y=width+0.35,
            text="<b>Cross-Vent Window (N)</b>", showarrow=False,
            font=dict(size=11, color="#22d3ee", family=DARK_FONT_FAMILY))

    fa = length * width
    fig.add_annotation(x=length/2, y=width/2,
        text=f"<b>Main Living Area</b><br><span style='color:#38bdf8;'>{fa:.1f} m²</span> ({length:.1f}m × {width:.1f}m)",
        showarrow=False, font=dict(size=13, color="#f8fafc", family=DARK_FONT_FAMILY))
    fig.add_annotation(x=ws+wl/2, y=-0.38,
        text=f"<b>Primary Glazing ({wl:.1f} m)</b>", showarrow=False,
        font=dict(size=11, color="#22d3ee", family=DARK_FONT_FAMILY))
    fig.add_annotation(x=0.3+dw/2, y=-0.38,
        text="<b>Entry Door (0.9 m)</b>", showarrow=False,
        font=dict(size=11, color="#fb923c", family=DARK_FONT_FAMILY))

    cx, cy = length+0.6, width-0.2
    fig.add_annotation(x=cx, y=cy, ax=cx, ay=cy-0.9,
        xref="x", yref="y", axref="x", ayref="y",
        text="<b>N</b>", showarrow=True, arrowhead=2, arrowsize=1.6,
        arrowwidth=3, arrowcolor="#ef4444", font=dict(size=15, color="#ef4444", family=DARK_FONT_FAMILY))

    apply_dark_theme(fig, "📐 2D Floor Plan & Fenestration Layout", height=450, show_legend=False)
    fig.update_xaxes(range=[-0.8, length+1.4], title="Length (m)")
    fig.update_yaxes(range=[-0.8, width+0.8], title="Width (m)", scaleanchor="x", scaleratio=1)
    return fig


def create_3d_shelter(length, width, height, roof_type, window_area, climate_type, wall_material="brick", insulation_mm=50.0, glazing_name="Double Clear"):
    """
    Delegates to the authoritative climate-adaptive 3D engine in services.visual3d.
    """
    return build_3d_shelter(
        climate_type=climate_type,
        length=length,
        width=width,
        height=height,
        window_area=window_area,
        wall_material=wall_material,
        insulation_mm=insulation_mm,
        glazing_name=glazing_name
    )


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
# 🏕️ FEATURE 1: SHELTER DESIGNER
# ==============================================================================
if nav_mode == "🏕️ Shelter Designer":
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
                    city_name=city_s
                ),
                use_container_width=True
            )
        st.markdown("---")
        st.markdown("### 💡 6. Design Rationale & Physics Explanation")
        st.info(rec["explanation"])


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
            y0=18.0, y1=24.0, fillcolor="rgba(34, 197, 94, 0.16)", layer="below",
            line=dict(color="#22c55e", width=1.5, dash="dash"),
            annotation_text="🌿 Comfort Band (18–24 °C)", annotation_position="top left",
            annotation=dict(
                font=dict(size=11, color="#4ade80", family=DARK_FONT_FAMILY),
                bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="rgba(34, 197, 94, 0.5)", borderwidth=1, borderpad=4
            )
        )
        fig_comp.add_trace(go.Scatter(
            x=hours, y=s_base["outdoor_temperature"],
            mode="lines", name="Ambient Outdoor (°C)",
            line=dict(color="#94a3b8", width=1.8, dash="dot"),
            hovertemplate="Outdoor: <b>%{y:.2f} °C</b><extra></extra>"
        ))
        fig_comp.add_trace(go.Scatter(
            x=hours, y=s_base["indoor_temperature"],
            mode="lines", name="❌ Baseline Indoor (°C)",
            line=dict(color="#ef4444", width=2.8, dash="dash"),
            hovertemplate="Baseline: <b>%{y:.2f} °C</b><extra></extra>"
        ))
        fig_comp.add_trace(go.Scatter(
            x=hours, y=s_opt["indoor_temperature"],
            mode="lines", name="✅ Optimized Indoor (°C)",
            line=dict(color="#10b981", width=3.5),
            hovertemplate="Optimized: <b>%{y:.2f} °C</b><extra></extra>"
        ))

        fig_comp.update_xaxes(
            title="Time (Simulation Hours)",
            tickmode="array",
            tickvals=[0, 24, 48, 72, 96, 120, 144, 168],
            ticktext=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "End"],
        )
        fig_comp.update_yaxes(title="Temperature (°C)")
        apply_dark_theme(fig_comp, "📈 Baseline vs AI-Optimized Indoor Thermal Response", height=440)
        fig_comp.update_layout(hovermode="x unified")
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
            y0=18.0, y1=24.0, fillcolor="rgba(34, 197, 94, 0.16)", layer="below",
            line=dict(color="#22c55e", width=1.5, dash="dash"),
            annotation_text="🌿 Comfort Band (18–24 °C)", annotation_position="top left",
            annotation=dict(
                font=dict(size=11, color="#4ade80", family=DARK_FONT_FAMILY),
                bgcolor="rgba(15, 23, 42, 0.85)", bordercolor="rgba(34, 197, 94, 0.5)", borderwidth=1, borderpad=4
            )
        )
        if me_data:
            fig_mat.add_trace(go.Scatter(
                x=list(range(168)), y=me_data[0]["outdoor_temps"],
                mode="lines", name="Outdoor Ambient",
                line=dict(color="#94a3b8", width=1.8, dash="dot"),
                hovertemplate="Outdoor: <b>%{y:.2f} °C</b><extra></extra>"
            ))

        mat_colors = ["#38bdf8", "#f43f5e", "#10b981", "#fbbf24", "#a78bfa", "#f472b6", "#22d3ee", "#a3e635"]
        for idx, item in enumerate(me_data):
            fig_mat.add_trace(go.Scatter(
                x=list(range(168)), y=item["indoor_temps"],
                mode="lines", name=item["name"],
                line=dict(color=mat_colors[idx % len(mat_colors)], width=2.4),
                hovertemplate=f"{item['name']}: <b>%{{y:.2f}} °C</b><extra></extra>"
            ))

        fig_mat.update_xaxes(
            title="Time (Simulation Hours)",
            tickmode="array",
            tickvals=[0, 24, 48, 72, 96, 120, 144, 168],
            ticktext=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "End"],
        )
        fig_mat.update_yaxes(title="Indoor Temperature (°C)")
        apply_dark_theme(fig_mat, f"📈 Indoor Temperature Progression Across Materials ({mat_city.upper()})", height=440)
        fig_mat.update_layout(hovermode="x unified")
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
                marker=dict(color="#f59e0b", line=dict(color="rgba(255,255,255,0.2)", width=1)),
                text=[f"<b>{r['discomfort_dh']:.0f} °C·h</b>" for r in me_data],
                textfont=dict(color="#ffffff", size=11, family=DARK_FONT_FAMILY),
                textposition="auto",
                hovertemplate="<b>%{x}</b>: %{y:.1f} °C·h<extra></extra>"
            ))
            fig_dh.update_xaxes(tickangle=-25, tickfont=dict(color=DARK_TEXT_PRIMARY, size=11))
            fig_dh.update_yaxes(title="Discomfort (°C·h)")
            apply_dark_theme(fig_dh, "📉 Discomfort Degree-Hours (Lower is Better)", height=350, show_legend=False)
            st.plotly_chart(fig_dh, use_container_width=True)

        with mc_col2:
            fig_hl = go.Figure(go.Bar(
                x=names, y=[r["total_loss_kwh"] for r in me_data],
                marker=dict(color="#ef4444", line=dict(color="rgba(255,255,255,0.2)", width=1)),
                text=[f"<b>{r['total_loss_kwh']:.0f} kWh</b>" for r in me_data],
                textfont=dict(color="#ffffff", size=11, family=DARK_FONT_FAMILY),
                textposition="auto",
                hovertemplate="<b>%{x}</b>: %{y:.1f} kWh<extra></extra>"
            ))
            fig_hl.update_xaxes(tickangle=-25, tickfont=dict(color=DARK_TEXT_PRIMARY, size=11))
            fig_hl.update_yaxes(title="Weekly Heat Loss (kWh)")
            apply_dark_theme(fig_hl, "⚡ Total Weekly Heat Loss (Lower is Better)", height=350, show_legend=False)
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
            st.plotly_chart(
                build_3d_shelter(
                    climate_type=ct,
                    length=dims[0],
                    width=dims[1],
                    height=dims[2],
                    window_area=2.2,
                    wall_material="brick",
                    insulation_mm=60.0,
                    glazing_name="Double Clear Glazing",
                    city_name=arch_city
                ),
                use_container_width=True
            )
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