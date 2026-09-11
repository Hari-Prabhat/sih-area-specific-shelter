"""
Unit tests for 3D Digital Twin visualizer (services/visual3d.py)
"""

import pytest
from services.visual3d import build_3d_shelter, CLIMATE_STYLE


@pytest.mark.parametrize("climate", ["cold", "hot_dry", "hot_humid", "composite", "moderate"])
def test_build_3d_shelter_all_climates(climate):
    fig = build_3d_shelter(
        climate_type=climate,
        length=5.0,
        width=3.5,
        height=2.8,
        window_area=2.0,
        wall_material="brick",
        insulation_mm=50.0,
        glazing_name="Double Low-E",
        view_mode="normal",
    )
    assert fig is not None
    # Verify rich architectural digital twin: should have at least 50 mesh components
    assert len(fig.data) >= 50
    assert "3D Digital Twin" in fig.layout.title.text


@pytest.mark.parametrize("view_mode", ["normal", "envelope", "thermal", "solar", "ventilation"])
def test_build_3d_shelter_all_view_modes(view_mode):
    fig = build_3d_shelter(
        climate_type="cold",
        length=4.5,
        width=3.2,
        height=2.7,
        window_area=2.2,
        wall_material="stone",
        insulation_mm=75.0,
        glazing_name="Triple Clear",
        view_mode=view_mode,
    )
    assert fig is not None
    assert len(fig.data) >= 50
    assert fig.layout.paper_bgcolor == "#1e293b"


def test_build_3d_shelter_fallback_climate():
    fig = build_3d_shelter(
        climate_type="nonexistent_climate",
        length=4.0,
        width=3.0,
        height=2.5,
        window_area=1.5,
    )
    assert fig is not None
    assert len(fig.data) >= 50
