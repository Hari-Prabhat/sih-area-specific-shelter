"""
Tests for Chart Theme, Analytical Validation & Export Modules
"""

import pytest
from components.chart_theme import apply_chart_theme
from components.charts import (
    plot_temperature_curves,
    plot_solar_dynamics,
    plot_component_heat_flows,
    plot_energy_balance_breakdown,
    plot_baseline_vs_optimized,
    plot_sensitivity_curves,
    create_2d_floorplan,
)
from components.validation import run_analytical_validation_benchmark
from components.export import generate_markdown_report
from services.simulation_service import run_simulation
from services.recommender import get_recommendation


def test_analytical_validation_benchmark_accuracy():
    """Verify analytical validation error is under 0.01% against closed-form reference."""
    benchmark = run_analytical_validation_benchmark()
    ss = benchmark["steady_state"]
    tr = benchmark["transient"]

    assert ss["rel_error_pct"] < 0.01
    assert "PASS" in ss["status"]
    assert tr["mae_k"] < 1e-6


def test_chart_theme_dark_and_light_modes():
    """Verify Plotly chart theme sets correct background and font colors."""
    import plotly.graph_objects as go

    fig_dark = go.Figure()
    apply_chart_theme(fig_dark, title_text="Dark Test", is_dark=True)
    assert fig_dark.layout.paper_bgcolor == "#1e293b"
    assert fig_dark.layout.font.color == "#f8fafc"

    fig_light = go.Figure()
    apply_chart_theme(fig_light, title_text="Light Test", is_dark=False)
    assert fig_light.layout.paper_bgcolor == "#ffffff"
    assert fig_light.layout.font.color == "#0f172a"


def test_all_chart_generators():
    """Verify all chart generator functions execute and produce valid Plotly figures."""
    sim = run_simulation(city="leh", occupants=2, hours_to_simulate=168)

    fig_temp = plot_temperature_curves("leh", sim["outdoor_temperature"], sim["indoor_temperature"])
    assert fig_temp is not None
    assert len(fig_temp.data) >= 2

    fig_solar = plot_solar_dynamics(sim)
    assert fig_solar is not None
    assert len(fig_solar.data) == 3

    fig_heat = plot_component_heat_flows(sim)
    assert fig_heat is not None
    assert len(fig_heat.data) == 7

    fig_energy = plot_energy_balance_breakdown(sim)
    assert fig_energy is not None

    fig_floor = create_2d_floorplan(4.5, 3.2, 2.5, "South Facade", "cold")
    assert fig_floor is not None

    fig_sens = plot_sensitivity_curves("Insulation", [0, 50, 100], [50, 75, 90], [150, 100, 70])
    assert fig_sens is not None


def test_export_markdown_report_content():
    """Verify generated markdown report contains required engineering sections."""
    rec = get_recommendation("leh", people=4, home_type="Permanent", n_trials=5)
    sim = rec["simulation_result"]

    md = generate_markdown_report(rec, sim, "leh")
    assert "THERMOSHELTER AI" in md
    assert "Architectural Geometry & Sizing" in md
    assert "Optimized Thermal Envelope Specifications" in md
    assert "168-Hour Transient Thermal Performance" in md
    assert "Model Assumptions & Validation" in md
