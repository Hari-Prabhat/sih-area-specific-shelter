"""
THERMOSHELTER AI - Simulation Dashboard & Metric Cards
======================================================
Renders the 3 SIH-mandated core simulation output sections:
  1. Indoor Temperature & Thermal Comfort (168-hr transient curves + comfort metrics)
  2. Solar Thermal Energy (incident flux, window transmission, useful thermal gain)
  3. Heat Flow & Heat Loss Breakdown (hourly dynamic components + weekly kWh breakdown)
"""

from typing import Any, Dict
import streamlit as st

from components.charts import (
    plot_temperature_curves,
    plot_solar_dynamics,
    plot_component_heat_flows,
    plot_energy_balance_breakdown,
)


def render_simulation_dashboard(
    city: str,
    sim_res: Dict[str, Any],
    title_suffix: str = "",
    is_dark: bool = True,
) -> None:
    """
    Renders the three SIH-required simulation sections using authoritative simulation results.
    """
    # -------------------------------------------------------------------------
    # 1. INDOOR TEMPERATURE & THERMAL COMFORT
    # -------------------------------------------------------------------------
    st.markdown("### 🌡️ 1. Indoor Temperature & Thermal Comfort Response")
    st.plotly_chart(
        plot_temperature_curves(
            city=city,
            outdoor_temps=sim_res["outdoor_temperature"],
            indoor_temps=sim_res["indoor_temperature"],
            title_suffix=title_suffix,
            is_dark=is_dark,
        ),
        use_container_width=True,
    )

    met = sim_res["comfort_metrics"]
    mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)
    mc1.metric("Avg Indoor Temp", f"{met['avg']:.2f} °C")
    mc2.metric("Min Indoor Temp", f"{met['min_t']:.2f} °C")
    mc3.metric("Max Indoor Temp", f"{met['max_t']:.2f} °C")
    mc4.metric("Comfort Hours", f"{sim_res['comfort_hours']:.0f} / 168 h")
    mc5.metric("Comfort % (18–24 °C)", f"{sim_res['comfort_percentage']:.1f} %")
    mc6.metric("Discomfort DH", f"{sim_res['discomfort_degree_hours']:.1f} °C·h")

    status_label = sim_res.get("comfort_status", "Comfortable")
    if status_label == "comfortable":
        st.success(f"🌿 **Comfort Status:** `Optimal Thermal Comfort Maintained` (18–24 °C zone)")
    elif "cold" in status_label.lower():
        st.warning(f"❄️ **Comfort Status:** `Heating Required` — Average indoor temperatures below 18 °C")
    else:
        st.warning(f"🔥 **Comfort Status:** `Cooling / Shading Advised` — Average indoor temperatures above 24 °C")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 2. SOLAR THERMAL ENERGY
    # -------------------------------------------------------------------------
    st.markdown("### ☀️ 2. Solar Thermal Energy Harvesting")
    sc1, sc2, sc3, sc4 = st.columns(4)
    sol_eff = (
        sim_res["integrated_solar_energy_kwh"]
        / max(0.001, sim_res["integrated_incident_solar_kwh"])
    ) * 100.0

    sc1.metric("Integrated Solar Gain", f"{sim_res['integrated_solar_energy_kwh']:.2f} kWh")
    sc2.metric("Total Incident Solar", f"{sim_res['integrated_incident_solar_kwh']:.2f} kWh")
    sc3.metric("Solar Harvesting Efficiency", f"{sol_eff:.1f} %")
    sc4.metric("Peak Useful Solar Gain", f"{max(sim_res['solar_thermal_gain']):.1f} W")

    st.plotly_chart(
        plot_solar_dynamics(sim_res, is_dark=is_dark),
        use_container_width=True,
    )
    st.markdown("---")

    # -------------------------------------------------------------------------
    # 3. HEAT FLOW & HEAT LOSS BREAKDOWN
    # -------------------------------------------------------------------------
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
        st.plotly_chart(
            plot_component_heat_flows(sim_res, is_dark=is_dark),
            use_container_width=True,
        )
    with hf_col2:
        st.plotly_chart(
            plot_energy_balance_breakdown(sim_res, is_dark=is_dark),
            use_container_width=True,
        )
    st.markdown("---")
