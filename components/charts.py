"""
THERMOSHELTER AI - Centralized Chart Generation Library
======================================================
Produces all Plotly charts used across the application with the centralized
high-contrast theme, explicit axis labeling, hover templates, and physical units.
"""

from typing import Any, Dict, List, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from components.chart_theme import (
    apply_chart_theme,
    FONT_FAMILY,
    SERIES_COLORS,
    DARK_GRID_COLOR,
    DARK_TEXT_PRIMARY,
)


def plot_temperature_curves(
    city: str,
    outdoor_temps: List[float],
    indoor_temps: List[float],
    title_suffix: str = "",
    is_dark: bool = True,
) -> go.Figure:
    """
    Renders 168-hour transient indoor vs outdoor temperature response curves
    with the 18–24 °C ASHRAE thermal comfort zone band.
    """
    hours = list(range(len(indoor_temps)))
    fig = go.Figure()

    # Comfort Zone Band (18–24 °C)
    fig.add_hrect(
        y0=18.0,
        y1=24.0,
        fillcolor="rgba(34, 197, 94, 0.16)",
        layer="below",
        line=dict(color="#22c55e", width=1.5, dash="dash"),
        annotation_text="🌿 Comfort Band (18–24 °C)",
        annotation_position="top left",
        annotation=dict(
            font=dict(size=11, color="#4ade80", family=FONT_FAMILY),
            bgcolor="rgba(15, 23, 42, 0.85)" if is_dark else "rgba(255, 255, 255, 0.9)",
            bordercolor="rgba(34, 197, 94, 0.5)",
            borderwidth=1,
            borderpad=4,
        ),
    )

    # Outdoor Ambient trace
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=[round(float(t), 2) for t in outdoor_temps[: len(indoor_temps)]],
            mode="lines",
            name="Outdoor Ambient (°C)",
            line=dict(color=SERIES_COLORS["outdoor_temp"], width=2.0, dash="dash"),
            hovertemplate="Outdoor: <b>%{y:.2f} °C</b><extra></extra>",
        )
    )

    # Indoor Predicted trace
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=[round(float(t), 2) for t in indoor_temps],
            mode="lines",
            name="Indoor Predicted (°C)",
            line=dict(color=SERIES_COLORS["indoor_temp"], width=3.2),
            hovertemplate="Indoor: <b>%{y:.2f} °C</b><extra></extra>",
        )
    )

    fig.update_xaxes(
        title="Time (Simulation Hours)",
        tickmode="array",
        tickvals=[0, 24, 48, 72, 96, 120, 144, 168],
        ticktext=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "End"],
    )
    fig.update_yaxes(title="Temperature (°C)")

    apply_chart_theme(
        fig,
        title_text=f"{city.upper()} — 168-Hour Thermal Comfort Response {title_suffix}",
        height=420,
        is_dark=is_dark,
    )
    fig.update_layout(hovermode="x unified")
    return fig


def plot_solar_dynamics(sim_result: Dict[str, Any], is_dark: bool = True) -> go.Figure:
    """
    Renders hourly solar irradiance, incident solar power, and admitted thermal gain.
    """
    hours = list(range(len(sim_result["indoor_temperatures"])))
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=hours,
            y=sim_result["solar_irradiance"],
            mode="lines",
            name="☀️ Solar Irradiance (W/m²)",
            line=dict(color=SERIES_COLORS["solar_irradiance"], width=1.8, dash="dot"),
            hovertemplate="Irradiance: <b>%{y:.1f} W/m²</b><extra></extra>",
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=sim_result["solar_power"],
            mode="lines",
            name="⚡ Incident Window Power (W)",
            line=dict(color=SERIES_COLORS["solar_power"], width=2.2),
            hovertemplate="Incident Power: <b>%{y:.1f} W</b><extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=sim_result["solar_thermal_gain"],
            mode="lines",
            name="🔥 Useful Thermal Gain (W)",
            line=dict(color=SERIES_COLORS["solar_gain"], width=2.8),
            fill="tozeroy",
            fillcolor="rgba(244, 63, 94, 0.20)",
            hovertemplate="Thermal Gain: <b>%{y:.1f} W</b><extra></extra>",
        ),
        secondary_y=False,
    )

    fig.update_xaxes(
        title="Time (Simulation Hours)",
        tickmode="array",
        tickvals=[0, 24, 48, 72, 96, 120, 144, 168],
        ticktext=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "End"],
    )
    fig.update_yaxes(
        title=dict(text="Solar Power / Thermal Gain (Watts)", font=dict(color="#f43f5e", size=12)),
        secondary_y=False,
    )
    fig.update_yaxes(
        title=dict(text="Global Irradiance (W/m²)", font=dict(color="#f59e0b", size=12)),
        secondary_y=True,
        showgrid=False,
    )

    apply_chart_theme(
        fig,
        title_text="☀️ Hourly Solar Flux & Fenestration Thermal Harvesting",
        height=400,
        is_dark=is_dark,
    )
    fig.update_layout(hovermode="x unified")
    return fig


def plot_component_heat_flows(sim_result: Dict[str, Any], is_dark: bool = True) -> go.Figure:
    """
    Renders hourly component heat losses and net heat flow balance in Watts.
    """
    hours = list(range(len(sim_result["indoor_temperatures"])))
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=hours,
            y=sim_result["wall_heat_flow"],
            mode="lines",
            name="🧱 Wall Loss (W)",
            line=dict(color=SERIES_COLORS["wall_loss"], width=2.0),
            hovertemplate="Wall Loss: <b>%{y:.1f} W</b><extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=sim_result["roof_heat_flow"],
            mode="lines",
            name="🏠 Roof Loss (W)",
            line=dict(color=SERIES_COLORS["roof_loss"], width=2.0),
            hovertemplate="Roof Loss: <b>%{y:.1f} W</b><extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=sim_result["floor_heat_flow"],
            mode="lines",
            name="🪵 Floor Loss (W)",
            line=dict(color=SERIES_COLORS["floor_loss"], width=1.8, dash="dot"),
            hovertemplate="Floor Loss: <b>%{y:.1f} W</b><extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=sim_result["window_heat_flow"],
            mode="lines",
            name="🪟 Glazing Loss (W)",
            line=dict(color=SERIES_COLORS["glazing_loss"], width=2.0),
            hovertemplate="Glazing Loss: <b>%{y:.1f} W</b><extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=sim_result["ventilation_heat_flow"],
            mode="lines",
            name="💨 Ventilation Loss (W)",
            line=dict(color=SERIES_COLORS["ventilation_loss"], width=1.8, dash="dash"),
            hovertemplate="Vent Loss: <b>%{y:.1f} W</b><extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=sim_result["radiation_heat_flow"],
            mode="lines",
            name="🌌 Radiation Loss (W)",
            line=dict(color=SERIES_COLORS["radiation_loss"], width=1.8, dash="dot"),
            hovertemplate="Rad Loss: <b>%{y:.1f} W</b><extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=sim_result["net_heat_flow"],
            mode="lines",
            name="⚖️ Net Heat Flow (W)",
            line=dict(color=SERIES_COLORS["net_heat_flow"], width=2.8),
            hovertemplate="Net Flow: <b>%{y:.1f} W</b><extra></extra>",
        )
    )

    fig.update_xaxes(
        title="Time (Simulation Hours)",
        tickmode="array",
        tickvals=[0, 24, 48, 72, 96, 120, 144, 168],
        ticktext=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "End"],
    )
    fig.update_yaxes(title="Thermal Power (Watts)")

    apply_chart_theme(
        fig,
        title_text="⚡ Hourly Dynamic Component Heat Flow Rates (Watts)",
        height=410,
        is_dark=is_dark,
    )
    fig.update_layout(hovermode="x unified")
    return fig


def plot_energy_balance_breakdown(sim_result: Dict[str, Any], is_dark: bool = True) -> go.Figure:
    """
    Renders weekly cumulative energy balance (kWh) directly from simulation results.
    """
    losses = sim_result["component_heat_loss_kwh"]
    categories = [
        "Solar Gain",
        "Wall Loss",
        "Roof Loss",
        "Floor Loss",
        "Glazing Loss",
        "Vent Loss",
        "Radiation Loss",
        "Total Loss",
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
    colors = [
        SERIES_COLORS["solar_irradiance"],
        SERIES_COLORS["wall_loss"],
        SERIES_COLORS["roof_loss"],
        SERIES_COLORS["floor_loss"],
        SERIES_COLORS["glazing_loss"],
        SERIES_COLORS["ventilation_loss"],
        SERIES_COLORS["radiation_loss"],
        "#ef4444",
    ]

    fig = go.Figure(
        data=[
            go.Bar(
                x=categories,
                y=values,
                marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.15)", width=1)),
                text=[f"<b>{v:.1f} kWh</b>" for v in values],
                textfont=dict(color="#ffffff", size=11, family=FONT_FAMILY),
                textposition="auto",
                hovertemplate="<b>%{x}</b>: %{y:.2f} kWh<extra></extra>",
            )
        ]
    )
    fig.update_xaxes(tickangle=-25)
    fig.update_yaxes(title="Energy (kWh)")
    apply_chart_theme(
        fig,
        title_text="📊 Weekly Component Energy Totals (kWh / 168 h)",
        height=380,
        show_legend=False,
        is_dark=is_dark,
    )
    return fig


def plot_baseline_vs_optimized(
    s_base: Dict[str, Any],
    s_opt: Dict[str, Any],
    is_dark: bool = True,
) -> go.Figure:
    """
    Renders comparative 168-hour overlay curves of Baseline vs AI-Optimized shelter response.
    """
    hours = list(range(len(s_opt["indoor_temperature"])))
    fig = go.Figure()

    fig.add_hrect(
        y0=18.0,
        y1=24.0,
        fillcolor="rgba(34, 197, 94, 0.16)",
        layer="below",
        line=dict(color="#22c55e", width=1.5, dash="dash"),
        annotation_text="🌿 Comfort Band (18–24 °C)",
        annotation_position="top left",
        annotation=dict(
            font=dict(size=11, color="#4ade80", family=FONT_FAMILY),
            bgcolor="rgba(15, 23, 42, 0.85)" if is_dark else "rgba(255, 255, 255, 0.9)",
            bordercolor="rgba(34, 197, 94, 0.5)",
            borderwidth=1,
            borderpad=4,
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=s_base["outdoor_temperature"],
            mode="lines",
            name="Ambient Outdoor (°C)",
            line=dict(color="#94a3b8", width=1.8, dash="dot"),
            hovertemplate="Outdoor: <b>%{y:.2f} °C</b><extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=s_base["indoor_temperature"],
            mode="lines",
            name="❌ Baseline Indoor (°C)",
            line=dict(color=SERIES_COLORS["baseline_temp"], width=2.8, dash="dash"),
            hovertemplate="Baseline: <b>%{y:.2f} °C</b><extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=s_opt["indoor_temperature"],
            mode="lines",
            name="✅ Optimized Indoor (°C)",
            line=dict(color=SERIES_COLORS["optimized_temp"], width=3.5),
            hovertemplate="Optimized: <b>%{y:.2f} °C</b><extra></extra>",
        )
    )

    fig.update_xaxes(
        title="Time (Simulation Hours)",
        tickmode="array",
        tickvals=[0, 24, 48, 72, 96, 120, 144, 168],
        ticktext=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "End"],
    )
    fig.update_yaxes(title="Temperature (°C)")
    apply_chart_theme(
        fig,
        title_text="📈 Baseline vs AI-Optimized Indoor Thermal Response",
        height=440,
        is_dark=is_dark,
    )
    fig.update_layout(hovermode="x unified")
    return fig


def plot_sensitivity_curves(
    param_name: str,
    param_values: List[float],
    comfort_percentages: List[float],
    heat_losses_kwh: List[float],
    unit: str = "mm",
    is_dark: bool = True,
) -> go.Figure:
    """
    Renders sensitivity analysis curves showing how a design variable affects
    comfort percentage and total envelope heat loss.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=param_values,
            y=comfort_percentages,
            mode="lines+markers",
            name="🌿 Comfort % (18–24 °C)",
            line=dict(color="#10b981", width=3.0),
            marker=dict(size=7, color="#10b981"),
            hovertemplate=f"{param_name}: <b>%{{x}} {unit}</b><br>Comfort: <b>%{{y:.1f}} %</b><extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=param_values,
            y=heat_losses_kwh,
            mode="lines+markers",
            name="⚡ Total Weekly Heat Loss (kWh)",
            line=dict(color="#f43f5e", width=2.6, dash="dash"),
            marker=dict(size=6, color="#f43f5e"),
            hovertemplate=f"{param_name}: <b>%{{x}} {unit}</b><br>Heat Loss: <b>%{{y:.1f}} kWh</b><extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_xaxes(title=f"{param_name} ({unit})")
    fig.update_yaxes(
        title=dict(text="Comfort Percentage (%)", font=dict(color="#10b981", size=12)),
        secondary_y=False,
    )
    fig.update_yaxes(
        title=dict(text="Total Heat Loss (kWh)", font=dict(color="#f43f5e", size=12)),
        secondary_y=True,
        showgrid=False,
    )

    apply_chart_theme(
        fig,
        title_text=f"📈 Sensitivity Analysis: {param_name} vs Comfort & Heat Loss",
        height=400,
        is_dark=is_dark,
    )
    fig.update_layout(hovermode="x unified")
    return fig


def create_2d_floorplan(
    length: float,
    width: float,
    window_area: float,
    orientation_advice: str,
    climate_type: str,
    is_dark: bool = True,
) -> go.Figure:
    """
    Renders 2D architectural floor plan with fenestration and north arrow.
    """
    fig = go.Figure()
    wt = 0.22  # Wall visual thickness

    # Outer structure
    fig.add_shape(
        type="rect",
        x0=0,
        y0=0,
        x1=length,
        y1=width,
        line=dict(color="#38bdf8", width=4),
        fillcolor="#1e293b" if is_dark else "#f1f5f9",
        layer="below",
    )
    # Inner perimeter
    fig.add_shape(
        type="rect",
        x0=wt,
        y0=wt,
        x1=length - wt,
        y1=width - wt,
        line=dict(color="#475569", width=1.5, dash="dot"),
        fillcolor="#0f172a" if is_dark else "#ffffff",
    )

    wl = min(length * 0.7, max(1.2, window_area / 1.3))
    ws = (length - wl) / 2
    # South Glazing
    fig.add_shape(
        type="rect",
        x0=ws,
        y0=-0.08,
        x1=ws + wl,
        y1=wt + 0.08,
        line=dict(color="#06b6d4", width=3),
        fillcolor="#22d3ee",
    )

    # Door
    dw = 0.9
    fig.add_shape(
        type="rect",
        x0=0.3,
        y0=-0.08,
        x1=0.3 + dw,
        y1=wt + 0.08,
        line=dict(color="#ea580c", width=3),
        fillcolor="#f97316",
    )

    if climate_type in ("hot_humid", "moderate"):
        fig.add_shape(
            type="rect",
            x0=ws + 0.3,
            y0=width - wt - 0.08,
            x1=ws + wl - 0.3,
            y1=width + 0.08,
            line=dict(color="#06b6d4", width=3),
            fillcolor="#22d3ee",
        )
        fig.add_annotation(
            x=length / 2,
            y=width + 0.35,
            text="<b>Cross-Vent Window (N)</b>",
            showarrow=False,
            font=dict(size=11, color="#22d3ee", family=FONT_FAMILY),
        )

    fa = length * width
    fig.add_annotation(
        x=length / 2,
        y=width / 2,
        text=f"<b>Main Living Area</b><br><span style='color:#38bdf8;'>{fa:.1f} m²</span> ({length:.1f}m × {width:.1f}m)",
        showarrow=False,
        font=dict(size=13, color="#f8fafc" if is_dark else "#0f172a", family=FONT_FAMILY),
    )
    fig.add_annotation(
        x=ws + wl / 2,
        y=-0.38,
        text=f"<b>Primary Glazing ({wl:.1f} m)</b>",
        showarrow=False,
        font=dict(size=11, color="#22d3ee", family=FONT_FAMILY),
    )
    fig.add_annotation(
        x=0.3 + dw / 2,
        y=-0.38,
        text="<b>Entry Door (0.9 m)</b>",
        showarrow=False,
        font=dict(size=11, color="#fb923c", family=FONT_FAMILY),
    )

    cx, cy = length + 0.6, width - 0.2
    fig.add_annotation(
        x=cx,
        y=cy,
        ax=cx,
        ay=cy - 0.9,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        text="<b>N</b>",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.6,
        arrowwidth=3,
        arrowcolor="#ef4444",
        font=dict(size=15, color="#ef4444", family=FONT_FAMILY),
    )

    apply_chart_theme(
        fig,
        title_text="📐 2D Floor Plan & Fenestration Layout",
        height=450,
        show_legend=False,
        is_dark=is_dark,
    )
    fig.update_xaxes(range=[-0.8, length + 1.4], title="Length (m)")
    fig.update_yaxes(range=[-0.8, width + 0.8], title="Width (m)", scaleanchor="x", scaleratio=1)
    return fig
