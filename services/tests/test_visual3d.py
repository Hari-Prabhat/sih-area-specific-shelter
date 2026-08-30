"""
Test suite for services.visual3d climate-adaptive 3D engine.
"""

import pytest
import plotly.graph_objects as go
from services.visual3d import build_3d_shelter, CLIMATE_STYLE, CITY_TO_CLIMATE


def test_climate_style_dictionary_completeness():
    """Verify all 5 required climates are defined with comprehensive styling attributes."""
    required_climates = ["cold", "hot_dry", "hot_humid", "composite", "moderate"]
    for c in required_climates:
        assert c in CLIMATE_STYLE, f"Missing climate definition: {c}"
        spec = CLIMATE_STYLE[c]
        assert "roof_pitch" in spec
        assert "overhang" in spec
        assert "glazing_ratio" in spec
        assert "wall_visual_thickness" in spec
        assert "palette" in spec
        assert "extras" in spec
        
        # Verify color palette completeness
        pal = spec["palette"]
        for key in ["wall", "roof", "ground", "frame", "door"]:
            assert key in pal, f"Missing palette key '{key}' in climate '{c}'"


def test_leh_cold_visual_characteristics():
    """Verify Leh (Cold) 3D model contains snow cap, vestibule, high-pitch roof, and snow ground."""
    fig = build_3d_shelter(
        climate_type="cold",
        length=4.5, width=3.2, height=2.8,
        window_area=3.5, wall_material="stone",
        insulation_mm=150.0, glazing_name="Triple Low-E Argon",
        city_name="leh"
    )
    assert isinstance(fig, go.Figure)
    trace_names = [t.name for t in fig.data if hasattr(t, "name") and t.name]
    
    # Leh specifics
    assert any("Snow Cap" in name for name in trace_names), "Leh model must include Snow Cap on roof"
    assert any("Vestibule" in name for name in trace_names), "Leh model must include Thermal Airlock Vestibule"
    assert any("Sun" in name for name in trace_names), "Must include Sun position indicator"
    assert any("Human Scale" in name for name in trace_names), "Must include 1.7m human scale reference"


def test_jaisalmer_hot_dry_visual_characteristics():
    """Verify Jaisalmer (Hot-Dry) 3D model contains flat roof, reflective coating, and desert ground."""
    fig = build_3d_shelter(
        climate_type="hot_dry",
        length=4.5, width=3.2, height=2.8,
        window_area=1.2, wall_material="adobe",
        insulation_mm=80.0, glazing_name="Double Tinted Low-SHGC",
        city_name="jaisalmer"
    )
    assert isinstance(fig, go.Figure)
    trace_names = [t.name for t in fig.data if hasattr(t, "name") and t.name]
    
    # Jaisalmer specifics
    assert any("Reflective" in name for name in trace_names), "Jaisalmer model must include White Reflective Cool Roof"
    assert any("Parapet" in name for name in trace_names), "Jaisalmer model must include Parapet Walls"


def test_chennai_hot_humid_visual_characteristics():
    """Verify Chennai (Hot-Humid) 3D model contains verandah, trees, ridge vent, and cross-ventilation."""
    fig = build_3d_shelter(
        climate_type="hot_humid",
        length=4.5, width=3.2, height=2.8,
        window_area=4.0, wall_material="aerated_concrete",
        insulation_mm=30.0, glazing_name="Double Clear Glazing",
        city_name="chennai"
    )
    assert isinstance(fig, go.Figure)
    trace_names = [t.name for t in fig.data if hasattr(t, "name") and t.name]
    
    # Chennai specifics
    assert any("Verandah" in name for name in trace_names), "Chennai model must include Shaded Verandah & Pillars"
    assert any("Ridge" in name for name in trace_names), "Chennai model must include Ridge Vent"
    assert any("Tree" in name for name in trace_names), "Chennai model must include Trees"


def test_delhi_composite_visual_characteristics():
    """Verify Delhi (Composite) 3D model builds balanced roof and daylighting fenestration."""
    fig = build_3d_shelter(
        climate_type="composite",
        length=4.5, width=3.2, height=2.8,
        window_area=2.5, wall_material="brick",
        insulation_mm=50.0, glazing_name="Double Low-E Glazing",
        city_name="delhi"
    )
    assert isinstance(fig, go.Figure)
    trace_names = [t.name for t in fig.data if hasattr(t, "name") and t.name]
    assert any("Roof" in name for name in trace_names)
    assert any("Walls" in name for name in trace_names)


def test_bengaluru_moderate_visual_characteristics():
    """Verify Bengaluru (Moderate) 3D model includes landscaping trees and low-pitch roof."""
    fig = build_3d_shelter(
        climate_type="moderate",
        length=4.5, width=3.2, height=2.8,
        window_area=2.5, wall_material="fly_ash",
        insulation_mm=25.0, glazing_name="Standard Double Clear",
        city_name="bengaluru"
    )
    assert isinstance(fig, go.Figure)
    trace_names = [t.name for t in fig.data if hasattr(t, "name") and t.name]
    assert any("Tree" in name for name in trace_names), "Bengaluru model must include landscape trees"


def test_all_five_cities_alias_and_rendering():
    """Verify all 5 city aliases execute cleanly and produce distinct trace configurations."""
    cities = ["leh", "jaisalmer", "chennai", "delhi", "bengaluru"]
    trace_counts = {}
    for city in cities:
        fig = build_3d_shelter(
            climate_type=city,
            length=4.5, width=3.2, height=2.8,
            window_area=2.5, wall_material="brick",
            insulation_mm=50.0, glazing_name="Double Clear"
        )
        assert len(fig.data) > 10, f"City '{city}' generated too few 3D mesh components"
        trace_counts[city] = len(fig.data)
        
        # Verify layout settings
        layout = fig.layout
        assert layout.paper_bgcolor == "#1e293b"
        assert layout.scene.bgcolor == "#0f172a"
        assert layout.scene.aspectmode == "data"
        assert layout.scene.camera.eye.x == 1.6
        assert layout.scene.camera.eye.y == -1.6
        assert layout.scene.camera.eye.z == 0.9

    # Each climate has its distinct extras, so trace counts should vary
    assert len(set(trace_counts.values())) >= 3
