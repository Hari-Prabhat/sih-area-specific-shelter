"""
THERMOSHELTER AI — Phase 2 Sensitivity & Integration Tests
============================================================
Proves that the canonical engineering pipeline (ClimateProfile → ShelterDesign →
SimulationAdapter → run_simulation → SimulationResult) is fully connected and
responds correctly to changes in every design parameter.

DATA PROVENANCE NOTE:
  All fixture values used in these tests are ESTIMATED or USER_DEFINED for
  engineering testing purposes. They are NOT measured field data.

Test Categories:
  A. Insulation sensitivity
  B. Window area sensitivity
  C. Orientation sensitivity
  D. Ventilation / ACH sensitivity
  E. Thermal mass sensitivity
  F. Geometry sensitivity
  G. Material sensitivity
  H. Climate sensitivity
  I. Occupancy sensitivity
  J. Golden Engineering Scenario (THERMOCORE-LADAKH-GOLDEN)
  K. Heat-flow accounting completeness
  L. Solar thermal energy accounting
  M. Backend ClimateProfile adapter
"""

import math
import pytest
from typing import Tuple

from services.contracts import (
    ClimateProfile,
    ShelterDesign,
    SimulationInput,
    SimulationResult,
    adapt_backend_climate_profile,
)
from services.shelter.models import DataProvenance
from services.simulation_adapter import SimulationAdapter
from services.fixtures import (
    get_leh_scenario,
    get_jaisalmer_scenario,
    get_chennai_scenario,
    get_golden_ladakh_scenario,
)


# =====================================================================
# HELPER: Build deterministic climate + design pair with specific overrides
# =====================================================================

def _make_climate(
    hours: int = 48,
    base_temp: float = -5.0,
    temp_swing: float = 8.0,
    peak_solar: float = 650.0,
) -> ClimateProfile:
    """Deterministic synthetic climate profile for testing."""
    t_s, dni_s, dhi_s = [], [], []
    for h in range(hours):
        hod = h % 24
        t_s.append(round(base_temp + (temp_swing / 2.0) * math.sin((hod - 8) * math.pi / 12.0), 2))
        if 7 <= hod <= 17:
            sf = math.sin((hod - 7) * math.pi / 10.0)
            dni_s.append(round(max(0.0, peak_solar * sf), 1))
            dhi_s.append(round(max(0.0, peak_solar * 0.20 * sf), 1))
        else:
            dni_s.append(0.0)
            dhi_s.append(0.0)

    return ClimateProfile(
        city="test_city",
        latitude=34.0,
        longitude=77.0,
        hourly_temperature=t_s,
        hourly_direct_solar=dni_s,
        hourly_diffuse_solar=dhi_s,
        climate_zone="cold",
        data_source="SENSITIVITY_TEST_FIXTURE",
        data_provenance=DataProvenance.ESTIMATED,
    )


def _run(climate: ClimateProfile, **design_kwargs) -> SimulationResult:
    """Build a ShelterDesign with given kwargs and run the full simulation."""
    defaults = dict(
        length=4.0, width=3.0, height=2.8,
        wall_material="brick",
        wall_thickness_m=0.23,
        insulation_thickness_m=0.05,
        insulation_conductivity=0.025,
        roof_type="flat",
        pitch_angle_deg=0.0,
        roof_thickness_m=0.15,
        roof_conductivity=0.50,
        roof_insulation_m=0.05,
        window_area=2.0,
        glazing="double_clear",
        orientation="south",
        ach=0.5,
        occupants=2,
        shelter_type="Permanent",
        heat_per_person=80.0,
    )
    defaults.update(design_kwargs)
    design = ShelterDesign(**defaults)
    hours = len(climate.hourly_temperature)
    return SimulationAdapter.run_from_contracts(
        climate, design, hours_to_simulate=hours, substeps=30,
    )


# =====================================================================
# A. INSULATION SENSITIVITY
# =====================================================================

class TestInsulationSensitivity:
    """Increasing insulation must reduce conductive heat loss."""

    def test_more_insulation_reduces_wall_heat_loss(self):
        c = _make_climate()
        r_base = _run(c, insulation_thickness_m=0.02)
        r_high = _run(c, insulation_thickness_m=0.15)

        wall_loss_base = sum(r_base.wall_heat_flow)
        wall_loss_high = sum(r_high.wall_heat_flow)

        # More insulation → less wall conductive heat loss (positive sign = loss)
        assert wall_loss_high < wall_loss_base, (
            f"Wall heat loss with high insulation ({wall_loss_high:.1f}) should be "
            f"less than baseline ({wall_loss_base:.1f})"
        )

    def test_more_insulation_reduces_total_heat_loss(self):
        c = _make_climate()
        r_base = _run(c, insulation_thickness_m=0.02)
        r_high = _run(c, insulation_thickness_m=0.15)

        assert r_high.total_heat_loss_kwh < r_base.total_heat_loss_kwh

    def test_u_value_decreases_with_insulation(self):
        c = _make_climate()
        r_base = _run(c, insulation_thickness_m=0.02)
        r_high = _run(c, insulation_thickness_m=0.15)

        assert r_high.u_values["wall_u"] < r_base.u_values["wall_u"]


# =====================================================================
# B. WINDOW AREA SENSITIVITY
# =====================================================================

class TestWindowAreaSensitivity:
    """Changing window area must affect solar gain and window heat transfer."""

    def test_larger_window_increases_solar_gain(self):
        c = _make_climate()
        r_small = _run(c, window_area=1.0)
        r_large = _run(c, window_area=4.0)

        solar_small = sum(r_small.solar_thermal_gain)
        solar_large = sum(r_large.solar_thermal_gain)

        assert solar_large > solar_small, (
            f"Solar gain with large window ({solar_large:.1f}) should exceed "
            f"small window ({solar_small:.1f})"
        )

    def test_larger_window_increases_window_heat_flow(self):
        c = _make_climate()
        r_small = _run(c, window_area=1.0)
        r_large = _run(c, window_area=4.0)

        win_flow_small = sum(abs(v) for v in r_small.window_heat_flow)
        win_flow_large = sum(abs(v) for v in r_large.window_heat_flow)

        assert win_flow_large > win_flow_small


# =====================================================================
# C. ORIENTATION SENSITIVITY
# =====================================================================

class TestOrientationSensitivity:
    """Different orientations must produce different solar responses."""

    def test_south_vs_north_solar_gain(self):
        c = _make_climate()
        r_south = _run(c, orientation="south")
        r_north = _run(c, orientation="north")

        solar_south = sum(r_south.solar_thermal_gain)
        solar_north = sum(r_north.solar_thermal_gain)

        # South facing should capture more solar energy than north
        assert solar_south > solar_north, (
            f"South solar gain ({solar_south:.1f}) should exceed "
            f"north solar gain ({solar_north:.1f})"
        )

    def test_orientation_affects_indoor_temperature(self):
        c = _make_climate()
        r_south = _run(c, orientation="south")
        r_north = _run(c, orientation="north")

        avg_south = sum(r_south.indoor_temperatures) / len(r_south.indoor_temperatures)
        avg_north = sum(r_north.indoor_temperatures) / len(r_north.indoor_temperatures)

        # In cold climate, south orientation should produce warmer interior
        assert avg_south > avg_north


# =====================================================================
# D. VENTILATION / ACH SENSITIVITY
# =====================================================================

class TestVentilationSensitivity:
    """Higher ACH must increase ventilation heat exchange."""

    def test_higher_ach_increases_ventilation_loss(self):
        c = _make_climate()
        r_low = _run(c, ach=0.3)
        r_high = _run(c, ach=2.0)

        vent_low = sum(abs(v) for v in r_low.ventilation_heat_flow)
        vent_high = sum(abs(v) for v in r_high.ventilation_heat_flow)

        assert vent_high > vent_low, (
            f"Ventilation loss with high ACH ({vent_high:.1f}) should exceed "
            f"low ACH ({vent_low:.1f})"
        )

    def test_higher_ach_increases_total_heat_loss(self):
        c = _make_climate()
        r_low = _run(c, ach=0.3)
        r_high = _run(c, ach=2.0)

        assert r_high.total_heat_loss_kwh > r_low.total_heat_loss_kwh


# =====================================================================
# E. THERMAL MASS SENSITIVITY
# =====================================================================

class TestThermalMassSensitivity:
    """
    Different thermal mass should change transient temperature dynamics.
    With more thermal mass, temperature swings should be dampened.
    """

    def test_high_mass_dampens_temperature_swing(self):
        c = _make_climate()
        # Low mass: lightweight wall
        r_light = _run(c, wall_material="timber", wall_thickness_m=0.10)
        # High mass: heavy brick wall
        r_heavy = _run(c, wall_material="brick", wall_thickness_m=0.30)

        swing_light = max(r_light.indoor_temperatures) - min(r_light.indoor_temperatures)
        swing_heavy = max(r_heavy.indoor_temperatures) - min(r_heavy.indoor_temperatures)

        # Heavy construction should have smaller temperature swing
        assert swing_heavy < swing_light, (
            f"Heavy wall temp swing ({swing_heavy:.2f}°C) should be less than "
            f"lightweight ({swing_light:.2f}°C)"
        )

    def test_thermal_capacity_reported_in_result(self):
        c = _make_climate()
        r = _run(c)
        assert r.effective_thermal_capacity_j_k > 0.0


# =====================================================================
# F. GEOMETRY SENSITIVITY
# =====================================================================

class TestGeometrySensitivity:
    """Changing geometry must change areas, volumes, and thermal response."""

    def test_larger_volume_changes_thermal_response(self):
        c = _make_climate()
        r_small = _run(c, length=3.0, width=2.5, height=2.4)
        r_large = _run(c, length=6.0, width=4.0, height=3.0)

        vol_small = r_small.geometry["volume_m3"]
        vol_large = r_large.geometry["volume_m3"]

        assert vol_large > vol_small
        assert r_large.total_heat_loss_kwh != r_small.total_heat_loss_kwh

    def test_geometry_areas_reported_correctly(self):
        c = _make_climate()
        r = _run(c, length=5.0, width=4.0, height=3.0)

        assert r.geometry["floor_area_m2"] == pytest.approx(20.0, abs=0.1)
        assert r.geometry["volume_m3"] == pytest.approx(60.0, abs=0.1)

    def test_larger_shelter_has_more_wall_loss(self):
        c = _make_climate()
        r_small = _run(c, length=3.0, width=2.5, height=2.4)
        r_large = _run(c, length=6.0, width=4.0, height=3.0)

        wall_loss_small = sum(abs(v) for v in r_small.wall_heat_flow)
        wall_loss_large = sum(abs(v) for v in r_large.wall_heat_flow)

        assert wall_loss_large > wall_loss_small


# =====================================================================
# G. MATERIAL SENSITIVITY
# =====================================================================

class TestMaterialSensitivity:
    """Changing envelope material must affect thermal response."""

    def test_different_wall_material_changes_u_value(self):
        c = _make_climate()
        r_brick = _run(c, wall_material="brick")
        r_timber = _run(c, wall_material="timber")

        # Different materials → different U-values
        assert r_brick.u_values["wall_u"] != r_timber.u_values["wall_u"]

    def test_different_material_changes_heat_loss(self):
        c = _make_climate()
        r_brick = _run(c, wall_material="brick")
        r_timber = _run(c, wall_material="timber")

        # Different materials produce different heat loss profiles
        assert r_brick.total_heat_loss_kwh != r_timber.total_heat_loss_kwh


# =====================================================================
# H. CLIMATE SENSITIVITY
# =====================================================================

class TestClimateSensitivity:
    """Same shelter in different climates must produce different results."""

    def test_cold_vs_hot_climate(self):
        c_cold = _make_climate(base_temp=-10.0, temp_swing=12.0)
        c_warm = _make_climate(base_temp=30.0, temp_swing=6.0)

        r_cold = _run(c_cold)
        r_warm = _run(c_warm)

        avg_cold = sum(r_cold.indoor_temperatures) / len(r_cold.indoor_temperatures)
        avg_warm = sum(r_warm.indoor_temperatures) / len(r_warm.indoor_temperatures)

        assert avg_warm > avg_cold, (
            f"Indoor temp in warm climate ({avg_warm:.1f}°C) should exceed "
            f"cold climate ({avg_cold:.1f}°C)"
        )

    def test_different_solar_changes_gains(self):
        c_low_solar = _make_climate(peak_solar=200.0)
        c_high_solar = _make_climate(peak_solar=900.0)

        r_low = _run(c_low_solar)
        r_high = _run(c_high_solar)

        solar_low = sum(r_low.solar_thermal_gain)
        solar_high = sum(r_high.solar_thermal_gain)

        assert solar_high > solar_low

    def test_leh_vs_jaisalmer_scenarios(self):
        """Uses the real scenario fixtures to confirm climate differentiation."""
        c_leh, d_leh = get_leh_scenario(hours=48)
        c_jai, d_jai = get_jaisalmer_scenario(hours=48)

        r_leh = SimulationAdapter.run_from_contracts(c_leh, d_leh, hours_to_simulate=48, substeps=30)
        r_jai = SimulationAdapter.run_from_contracts(c_jai, d_jai, hours_to_simulate=48, substeps=30)

        avg_leh = sum(r_leh.indoor_temperatures) / len(r_leh.indoor_temperatures)
        avg_jai = sum(r_jai.indoor_temperatures) / len(r_jai.indoor_temperatures)

        # Jaisalmer (hot desert) should have significantly warmer indoor temps
        assert avg_jai > avg_leh + 20.0


# =====================================================================
# I. OCCUPANCY SENSITIVITY
# =====================================================================

class TestOccupancySensitivity:
    """Changing occupant count must affect internal heat gains."""

    def test_more_occupants_increases_internal_gains(self):
        c = _make_climate()
        r_few = _run(c, occupants=1)
        r_many = _run(c, occupants=8)

        internal_few = sum(r_few.hourly_internal_gain)
        internal_many = sum(r_many.hourly_internal_gain)

        assert internal_many > internal_few, (
            f"Internal gains with 8 occupants ({internal_many:.1f}) should exceed "
            f"1 occupant ({internal_few:.1f})"
        )

    def test_more_occupants_raises_indoor_temperature(self):
        c = _make_climate()
        r_few = _run(c, occupants=1)
        r_many = _run(c, occupants=8)

        avg_few = sum(r_few.indoor_temperatures) / len(r_few.indoor_temperatures)
        avg_many = sum(r_many.indoor_temperatures) / len(r_many.indoor_temperatures)

        assert avg_many > avg_few


# =====================================================================
# J. GOLDEN ENGINEERING SCENARIO (THERMOCORE-LADAKH-GOLDEN)
# =====================================================================

class TestGoldenLadakhScenario:
    """
    End-to-end integration test using the THERMOCORE-LADAKH-GOLDEN fixture.
    Runs through the REAL thermal simulation path and validates comprehensive
    result structure.
    """

    def test_golden_scenario_runs_successfully(self):
        climate, design = get_golden_ladakh_scenario()
        result = SimulationAdapter.run_from_contracts(
            climate, design, hours_to_simulate=168, substeps=60,
        )

        assert isinstance(result, SimulationResult)
        assert result.city == "leh"
        assert len(result.indoor_temperatures) == 168
        assert len(result.outdoor_temperatures) == 168

    def test_golden_design_identity(self):
        climate, design = get_golden_ladakh_scenario()
        assert design.design_id == "THERMOCORE-LADAKH-GOLDEN"
        assert design.occupants == 4
        assert design.wall_material == "stone"
        assert design.insulation_thickness_m == 0.10
        assert design.orientation == "south"
        assert design.ach == 0.4
        assert design.shelter_type == "Permanent"

    def test_golden_climate_provenance(self):
        climate, _ = get_golden_ladakh_scenario()
        assert climate.data_provenance == "estimated"
        assert climate.data_source == "THERMOCORE_GOLDEN_FIXTURE"
        assert climate.elevation_m == 3500.0
        assert climate.climate_zone == "cold"

    def test_golden_thermal_mass_included(self):
        _, design = get_golden_ladakh_scenario()
        assert len(design.thermal_mass_elements) >= 1
        trombe = design.thermal_mass_elements[0]
        assert trombe.id == "trombe_south"
        assert trombe.thermal_capacity_j_per_k > 0.0

    def test_golden_passive_strategies_present(self):
        _, design = get_golden_ladakh_scenario()
        assert len(design.passive_strategies) >= 2
        strategy_ids = {s.id for s in design.passive_strategies}
        assert "solar_collection" in strategy_ids
        assert "thermal_mass_storage" in strategy_ids

    def test_golden_full_result_structure(self):
        climate, design = get_golden_ladakh_scenario()
        result = SimulationAdapter.run_from_contracts(
            climate, design, hours_to_simulate=168, substeps=60,
        )

        # Timeseries present
        assert len(result.solar_thermal_gain) == 168
        assert len(result.wall_heat_flow) == 168
        assert len(result.roof_heat_flow) == 168
        assert len(result.floor_heat_flow) == 168
        assert len(result.window_heat_flow) == 168
        assert len(result.ventilation_heat_flow) == 168
        assert len(result.radiation_heat_flow) == 168
        assert len(result.net_heat_flow) == 168
        assert len(result.hourly_internal_gain) == 168

        # Energy totals
        assert result.total_heat_loss_kwh > 0.0
        assert result.integrated_solar_energy_kwh > 0.0
        assert "wall_loss_kwh" in result.component_heat_loss_kwh
        assert "roof_loss_kwh" in result.component_heat_loss_kwh

        # Comfort metrics
        assert "avg" in result.comfort_metrics
        assert 0.0 <= result.comfort_percentage <= 100.0

        # U-values
        assert result.u_values["wall_u"] > 0.0
        assert result.u_values["roof_u"] > 0.0

    def test_golden_simulation_produces_physical_results(self):
        """Verify the golden scenario produces physically plausible results."""
        climate, design = get_golden_ladakh_scenario()
        result = SimulationAdapter.run_from_contracts(
            climate, design, hours_to_simulate=168, substeps=60,
        )

        avg_indoor = result.comfort_metrics["avg"]
        avg_outdoor = sum(result.outdoor_temperatures) / len(result.outdoor_temperatures)

        # Indoor should be warmer than outdoor in cold climate (shelter provides heating retention)
        assert avg_indoor > avg_outdoor, (
            f"Indoor avg ({avg_indoor:.1f}°C) should be warmer than "
            f"outdoor avg ({avg_outdoor:.1f}°C) in cold climate"
        )

        # With good insulation and solar, indoor should be significantly warmer
        assert avg_indoor > avg_outdoor + 3.0, (
            f"Well-insulated shelter should raise indoor temp at least 3°C above outdoor"
        )


# =====================================================================
# K. HEAT-FLOW ACCOUNTING COMPLETENESS
# =====================================================================

class TestHeatFlowAccounting:
    """
    Verify that SimulationResult exposes all information needed for
    a future React dashboard.
    """

    def test_all_dashboard_timeseries_present(self):
        c = _make_climate()
        r = _run(c)

        # These are the categories needed for the dashboard
        assert len(r.indoor_temperatures) > 0, "indoor temperature over time"
        assert len(r.outdoor_temperatures) > 0, "outdoor temperature over time"
        assert len(r.solar_thermal_gain) > 0, "solar gains"
        assert len(r.wall_heat_flow) > 0, "wall heat flow"
        assert len(r.roof_heat_flow) > 0, "roof heat flow"
        assert len(r.floor_heat_flow) > 0, "floor heat flow"
        assert len(r.window_heat_flow) > 0, "window/glazing heat flow"
        assert len(r.ventilation_heat_flow) > 0, "ventilation heat flow"
        assert len(r.hourly_internal_gain) > 0, "internal gains"
        assert len(r.radiation_heat_flow) > 0, "radiation heat flow"
        assert len(r.net_heat_flow) > 0, "net heat balance"

    def test_thermal_storage_flow_present(self):
        c = _make_climate()
        r = _run(c)
        assert r.thermal_storage_flow is not None, "thermal storage flow should be present"
        assert len(r.thermal_storage_flow) > 0

    def test_energy_totals_present(self):
        c = _make_climate()
        r = _run(c)

        et = r.energy_totals_kwh
        assert "solar_gain_kwh" in et
        assert "wall_loss_kwh" in et
        assert "roof_loss_kwh" in et
        assert "floor_loss_kwh" in et
        assert "window_loss_kwh" in et
        assert "vent_loss_kwh" in et
        assert "radiation_loss_kwh" in et
        assert "heating_demand_kwh" in et
        assert "cooling_demand_kwh" in et

    def test_component_heat_loss_breakdown(self):
        c = _make_climate()
        r = _run(c)

        chl = r.component_heat_loss_kwh
        assert "wall_loss_kwh" in chl
        assert "roof_loss_kwh" in chl
        assert "floor_loss_kwh" in chl
        assert "window_loss_kwh" in chl
        assert "ventilation_loss_kwh" in chl
        assert "radiation_loss_kwh" in chl


# =====================================================================
# L. SOLAR THERMAL ENERGY ACCOUNTING
# =====================================================================

class TestSolarEnergyAccounting:
    """
    Verify the solar energy chain is properly distinguished:
    1. Incident solar (total irradiance on window area)
    2. Transmitted/captured solar gain (after SHGC and orientation)
    """

    def test_incident_vs_captured_solar(self):
        c = _make_climate()
        r = _run(c, window_area=3.0, glazing="double_clear", orientation="south")

        assert r.integrated_incident_solar_kwh > 0.0
        assert r.integrated_solar_energy_kwh > 0.0

        # Captured solar must be less than or equal to incident
        # (SHGC < 1.0 and orientation factor may reduce)
        assert r.integrated_solar_energy_kwh <= r.integrated_incident_solar_kwh, (
            f"Captured solar ({r.integrated_solar_energy_kwh:.2f} kWh) cannot exceed "
            f"incident solar ({r.integrated_incident_solar_kwh:.2f} kWh)"
        )

    def test_solar_power_vs_solar_gain_distinction(self):
        c = _make_climate()
        r = _run(c, window_area=2.0, glazing="double_clear")

        # solar_power = incident power on window (irradiance × area)
        # solar_thermal_gain = useful gain through glazing (with SHGC)
        for sp, sg in zip(r.solar_power, r.solar_thermal_gain):
            if sp > 0:
                assert sg <= sp, (
                    f"Solar gain ({sg:.1f}W) must not exceed "
                    f"incident solar power ({sp:.1f}W)"
                )


# =====================================================================
# M. BACKEND CLIMATE PROFILE ADAPTER
# =====================================================================

class TestBackendClimateAdapter:
    """Test the adapter that maps backend.climate.schemas.ClimateProfile
    to services.contracts.ClimateProfile."""

    def test_adapter_with_mock_backend_profile(self):
        """Build a mock Pydantic object matching the backend schema and adapt it."""
        from pydantic import BaseModel, Field
        from typing import List, Optional, Dict, Any
        from enum import Enum

        # Minimal mock of backend schema structure
        class MockDataProvenance(str, Enum):
            HISTORICAL = "HISTORICAL"
            ESTIMATED = "ESTIMATED"

        class MockDataConfidence(str, Enum):
            HIGH = "HIGH"
            MEDIUM = "MEDIUM"

        class MockClimateZone(str, Enum):
            COLD = "COLD"
            HOT_DRY = "HOT DRY"

        class MockLocation(BaseModel):
            place_name: str = "Leh, Ladakh"
            latitude: float = 34.15
            longitude: float = 77.58
            elevation: Optional[float] = 3500.0
            timezone: Optional[str] = "Asia/Kolkata"

        class MockClimateMetrics(BaseModel):
            classification: MockClimateZone = MockClimateZone.COLD
            annual_mean_temperature: float = -2.0
            minimum_temperature: float = -20.0
            maximum_temperature: float = 15.0
            diurnal_range_mean: Optional[float] = 12.0

        class MockSolarData(BaseModel):
            GHI: float = 450.0
            DNI: Optional[float] = 600.0
            DHI: Optional[float] = 120.0

        class MockWindData(BaseModel):
            average_speed: float = 2.5

        class MockHumidityData(BaseModel):
            average_relative_humidity: float = 35.0

        class MockDesignExtremes(BaseModel):
            cold_extreme: float = -25.0
            hot_extreme: float = 20.0

        class MockDataQuality(BaseModel):
            confidence: MockDataConfidence = MockDataConfidence.HIGH
            provenance: MockDataProvenance = MockDataProvenance.HISTORICAL
            sources: List[str] = ["IMD", "NREL"]

        class MockBackendProfile(BaseModel):
            version: str = "1.0.0"
            location: MockLocation = MockLocation()
            climate: MockClimateMetrics = MockClimateMetrics()
            solar: MockSolarData = MockSolarData()
            wind: MockWindData = MockWindData()
            humidity: MockHumidityData = MockHumidityData()
            design_extremes: MockDesignExtremes = MockDesignExtremes()
            data_quality: MockDataQuality = MockDataQuality()

        backend_profile = MockBackendProfile()
        canonical = adapt_backend_climate_profile(backend_profile)

        assert isinstance(canonical, ClimateProfile)
        assert canonical.city == "leh"
        assert canonical.latitude == 34.15
        assert canonical.longitude == 77.58
        assert canonical.elevation_m == 3500.0
        assert canonical.climate_zone == "cold"
        assert len(canonical.hourly_temperature) == 168
        assert len(canonical.hourly_direct_solar) == 168
        assert canonical.data_provenance == "estimated"  # synthesized, so ESTIMATED
        assert canonical.data_confidence == 0.95  # HIGH → 0.95

    def test_adapter_rejects_non_pydantic_object(self):
        with pytest.raises(TypeError, match="Expected a Pydantic"):
            adapt_backend_climate_profile({"city": "test"})
