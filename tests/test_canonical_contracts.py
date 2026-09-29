"""
THERMOSHELTER AI — Canonical Engineering Contracts Test Suite (Phase 1)
========================================================================
Comprehensive verification of the unified engineering data model:
1. Valid ShelterRequirements
2. Invalid ShelterRequirements
3. Valid ShelterGeometry
4. Invalid ShelterGeometry
5. Valid MaterialAssembly (ISO 6946)
6. Invalid MaterialLayer
7. Valid PassiveStrategy
8. Valid Canonical ShelterDesign
9. Invalid ShelterDesign
10. JSON Serialization & Deserialization Round-trip
11. ShelterDesign -> SimulationInput Adapter
12. ClimateProfile Serialization & Metadata
13. Unit Consistency Verification
14. Regression: No Competing Domain ShelterDesign
"""

import json
import math
import pytest

import services.contracts as contracts
import services.shelter.models as shelter_models
from services.shelter.models import (
    DataProvenance,
    GlazingDefinition,
    MaterialAssembly,
    MaterialLayer,
    OpeningDefinition,
    PassiveStrategy,
    ShelterDesign,
    ShelterGeometry,
    ShelterRequirements,
    ThermalMassDefinition,
    ZoneDefinition,
)
from services.shelter.builder import (
    ShelterDesignBuilder,
    ShelterDesignBuildError,
    build_leh_ladakh_design,
    build_hot_dry_design,
)
from services.contracts import (
    ClimateProfile,
    SimulationEnvelopeParameters,
    SimulationInput,
    SimulationResult,
    create_mock_climate_profile,
    create_mock_shelter_design,
    adapt_to_climate_profile,
    adapt_to_shelter_design,
)
from services.simulation_adapter import SimulationAdapter


# =====================================================================
# 1. VALID SHELTER REQUIREMENTS
# =====================================================================

def test_1_valid_shelter_requirements():
    req = ShelterRequirements(
        occupants=4,
        shelter_purpose="high_altitude_defense_post",
        duration_days=365,
        permanence="permanent",
        mobility="permanent",
        priorities=["maximum_heat_retention", "structural_resilience"],
        available_resources=["local_granite", "mud_mortar", "timber"],
        energy_sources=["passive_solar", "thermal_mass"],
        constraints={"min_indoor_temp_c": 12.0, "max_ach": 0.5},
        provenance=DataProvenance.USER_DEFINED,
    )
    assert req.occupants == 4
    assert req.shelter_purpose == "high_altitude_defense_post"
    assert req.duration_days == 365
    assert req.permanence == "permanent"
    assert req.provenance == "user_defined"

    d = req.to_dict()
    assert isinstance(d, dict)
    assert d["occupants"] == 4
    reconstructed = ShelterRequirements.from_dict(d)
    assert reconstructed.occupants == req.occupants
    assert reconstructed.shelter_purpose == req.shelter_purpose


# =====================================================================
# 2. INVALID SHELTER REQUIREMENTS
# =====================================================================

def test_2_invalid_shelter_requirements():
    # Occupants <= 0 rejected
    with pytest.raises(ValueError, match="strictly positive"):
        ShelterRequirements(occupants=0, shelter_purpose="emergency")

    with pytest.raises(ValueError, match="strictly positive"):
        ShelterRequirements(occupants=-3, shelter_purpose="emergency")

    # Duration days <= 0 rejected when specified
    with pytest.raises(ValueError, match="Duration days must be > 0"):
        ShelterRequirements(occupants=2, shelter_purpose="field", duration_days=0)

    with pytest.raises(ValueError, match="Duration days must be > 0"):
        ShelterRequirements(occupants=2, shelter_purpose="field", duration_days=-30)

    # Invalid permanence rejected
    with pytest.raises(ValueError, match="Invalid permanence"):
        ShelterRequirements(occupants=2, shelter_purpose="field", permanence="forever")

    # Invalid mobility rejected
    with pytest.raises(ValueError, match="Invalid mobility"):
        ShelterRequirements(occupants=2, shelter_purpose="field", mobility="flying")


# =====================================================================
# 3. VALID SHELTER GEOMETRY
# =====================================================================

def test_3_valid_shelter_geometry():
    # Rectangular nominal
    geom = ShelterGeometry(
        geometry_type="rectangular",
        length_m=5.0,
        width_m=4.0,
        height_m=2.8,
        roof_type="flat",
        roof_pitch_deg=0.0,
        orientation_deg=180.0,
    )
    assert geom.floor_area_m2 == pytest.approx(20.0)
    assert geom.volume_m3 == pytest.approx(56.0)
    assert geom.gross_wall_area_m2 == pytest.approx(50.4)
    assert geom.roof_area_m2 == pytest.approx(20.0)
    assert geom.surface_to_volume_ratio > 0.0

    # Pitched roof nominal
    pitched_geom = ShelterGeometry(
        geometry_type="rectangular",
        length_m=6.0,
        width_m=4.0,
        height_m=2.5,
        roof_type="pitched",
        roof_pitch_deg=30.0,
        orientation_deg=180.0,
    )
    assert pitched_geom.floor_area_m2 == pytest.approx(24.0)
    assert pitched_geom.roof_area_m2 > pitched_geom.floor_area_m2  # Sloped roof area is larger
    assert 0.0 <= pitched_geom.orientation_deg <= 360.0


# =====================================================================
# 4. INVALID SHELTER GEOMETRY
# =====================================================================

def test_4_invalid_shelter_geometry():
    # Non-positive dimensions rejected
    with pytest.raises(ValueError, match="strictly positive"):
        ShelterGeometry(geometry_type="rectangular", length_m=-1.0, width_m=4.0, height_m=2.5)

    with pytest.raises(ValueError, match="strictly positive"):
        ShelterGeometry(geometry_type="rectangular", length_m=5.0, width_m=0.0, height_m=2.5)

    with pytest.raises(ValueError, match="strictly positive"):
        ShelterGeometry(geometry_type="rectangular", length_m=5.0, width_m=4.0, height_m=-0.5)

    # Invalid roof pitch rejected
    with pytest.raises(ValueError, match="Roof pitch"):
        ShelterGeometry(geometry_type="rectangular", length_m=5.0, width_m=4.0, height_m=2.5, roof_pitch_deg=90.0)

    with pytest.raises(ValueError, match="Roof pitch"):
        ShelterGeometry(geometry_type="rectangular", length_m=5.0, width_m=4.0, height_m=2.5, roof_pitch_deg=-10.0)

    # Invalid orientation azimuth rejected
    with pytest.raises(ValueError, match="Orientation must be within"):
        ShelterGeometry(geometry_type="rectangular", length_m=5.0, width_m=4.0, height_m=2.5, orientation_deg=400.0)

    # Fenestration area exceeding total wall area rejected
    excessive_opening = OpeningDefinition(
        id="win_huge",
        name="Huge Window",
        opening_type="window",
        width_m=10.0,
        height_m=10.0,
        area_m2=100.0,
        facade="south",
        orientation_deg=180.0,
    )
    with pytest.raises(ValueError, match="cannot exceed total wall area"):
        ShelterGeometry(
            geometry_type="rectangular",
            length_m=4.0,
            width_m=3.0,
            height_m=2.5,
            openings=[excessive_opening],
        )


# =====================================================================
# 5. VALID MATERIAL ASSEMBLY (ISO 6946)
# =====================================================================

def test_5_valid_material_assembly():
    layer_brick = MaterialLayer(
        material_id="brick",
        name="Fired Clay Brick",
        thickness_m=0.20,
        conductivity_w_mk=0.60,
        density_kg_m3=1600.0,
        specific_heat_j_kgk=880.0,
    )
    layer_puf = MaterialLayer(
        material_id="puf",
        name="Rigid Polyurethane Foam",
        thickness_m=0.08,
        conductivity_w_mk=0.024,
        density_kg_m3=35.0,
        specific_heat_j_kgk=1400.0,
    )

    # Verify 1D conduction physics
    assert layer_brick.resistance_m2_k_w == pytest.approx(0.20 / 0.60, rel=1e-3)
    assert layer_puf.resistance_m2_k_w == pytest.approx(0.08 / 0.024, rel=1e-3)
    assert layer_brick.mass_per_m2_kg == pytest.approx(320.0)
    assert layer_brick.heat_capacity_per_m2_j_k == pytest.approx(320.0 * 880.0)

    # Verify composite assembly (ISO 6946)
    assembly = MaterialAssembly(
        assembly_id="wall_insulated_brick",
        name="Insulated Mud Brick Assembly",
        category="wall",
        layers=[layer_brick, layer_puf],
        r_inside=0.13,
        r_outside=0.04,
    )
    expected_r_layers = (0.20 / 0.60) + (0.08 / 0.024)
    expected_r_total = 0.13 + expected_r_layers + 0.04
    expected_u_value = 1.0 / expected_r_total

    assert assembly.r_total == pytest.approx(expected_r_total, rel=1e-3)
    assert assembly.u_value == pytest.approx(expected_u_value, rel=1e-3)
    assert assembly.total_thickness_m == pytest.approx(0.28, rel=1e-3)
    assert assembly.u_value < 0.35  # High-performance envelope


# =====================================================================
# 6. INVALID MATERIAL LAYER
# =====================================================================

def test_6_invalid_material_layer():
    # Negative thickness rejected
    with pytest.raises(ValueError, match="thickness must be strictly positive"):
        MaterialLayer("m1", "Layer", thickness_m=-0.05, conductivity_w_mk=0.5, density_kg_m3=1000.0, specific_heat_j_kgk=900.0)

    # Non-positive conductivity rejected
    with pytest.raises(ValueError, match="Conductivity must be strictly positive"):
        MaterialLayer("m1", "Layer", thickness_m=0.10, conductivity_w_mk=0.0, density_kg_m3=1000.0, specific_heat_j_kgk=900.0)

    # Non-positive density rejected
    with pytest.raises(ValueError, match="Density must be strictly positive"):
        MaterialLayer("m1", "Layer", thickness_m=0.10, conductivity_w_mk=0.5, density_kg_m3=-10.0, specific_heat_j_kgk=900.0)

    # Non-positive specific heat rejected
    with pytest.raises(ValueError, match="Specific heat must be strictly positive"):
        MaterialLayer("m1", "Layer", thickness_m=0.10, conductivity_w_mk=0.5, density_kg_m3=1000.0, specific_heat_j_kgk=0.0)

    # Invalid emissivity (> 1.0 or < 0.0) rejected
    with pytest.raises(ValueError, match="Emissivity must be between"):
        MaterialLayer("m1", "Layer", thickness_m=0.10, conductivity_w_mk=0.5, density_kg_m3=1000.0, specific_heat_j_kgk=900.0, emissivity=1.5)

    # Invalid solar absorptivity rejected
    with pytest.raises(ValueError, match="Solar absorptivity must be between"):
        MaterialLayer("m1", "Layer", thickness_m=0.10, conductivity_w_mk=0.5, density_kg_m3=1000.0, specific_heat_j_kgk=900.0, solar_absorptivity=-0.1)


# =====================================================================
# 7. VALID PASSIVE STRATEGY
# =====================================================================

def test_7_valid_passive_strategy():
    strategy_cold = PassiveStrategy(
        id="solar_direct_gain_cold",
        name="Direct Solar Harvesting & Thermal Mass Storage",
        category="cold_region",
        climate_applicability=["cold", "extreme_cold"],
        enabled=True,
        parameters={"south_window_wwr": 0.25, "thermal_storage_type": "trombe_wall"},
        provenance=DataProvenance.OPTIMIZED,
    )
    assert strategy_cold.category == "cold_region"
    assert strategy_cold.enabled is True
    assert strategy_cold.parameters["south_window_wwr"] == 0.25

    # Valid categories
    for cat in ("cold_region", "hot_dry", "hot_humid", "variable_seasonal"):
        s = PassiveStrategy(id=f"strat_{cat}", name="Test Strategy", category=cat)
        assert s.category == cat

    # Invalid category rejected
    with pytest.raises(ValueError, match="Invalid strategy category"):
        PassiveStrategy(id="s_bad", name="Bad Strategy", category="arctic_tundra")


# =====================================================================
# 8. VALID CANONICAL SHELTER DESIGN
# =====================================================================

def test_8_valid_canonical_shelter_design():
    # Hero benchmark design: Leh/Ladakh extreme cold
    design = build_leh_ladakh_design()
    assert isinstance(design, ShelterDesign)
    assert design.requirements.occupants == 4
    assert design.requirements.permanence == "permanent"
    assert design.geometry.length_m == 5.0
    assert design.geometry.width_m == 4.0
    assert design.geometry.floor_area_m2 == pytest.approx(20.0)
    assert design.wall_assembly.u_value > 0.0
    assert design.roof_assembly.u_value > 0.0
    assert design.floor_assembly.u_value > 0.0
    assert design.glazing.u_value > 0.0
    assert len(design.openings) >= 1
    assert len(design.thermal_mass_elements) >= 1
    assert len(design.passive_strategies) >= 1

    # Convenience properties
    assert design.length == 5.0
    assert design.width == 4.0
    assert design.height == 2.7
    assert design.occupants == 4
    assert design.shelter_type == "Permanent"


# =====================================================================
# 9. INVALID SHELTER DESIGN
# =====================================================================

def test_9_invalid_shelter_design():
    # Builder requires all mandatory components
    builder = ShelterDesignBuilder("d_invalid", "Incomplete Design")
    with pytest.raises(ShelterDesignBuildError, match="Requirements must be specified"):
        builder.build()

    builder.set_requirements(ShelterRequirements(occupants=2, shelter_purpose="test"))
    with pytest.raises(ShelterDesignBuildError, match="Geometry must be specified"):
        builder.build()

    # Flat instantiation validation checks
    with pytest.raises(ValueError, match="length must be strictly positive"):
        ShelterDesign(length=-2.0, width=3.0, height=2.8)

    with pytest.raises(ValueError, match="cannot exceed total wall area"):
        ShelterDesign(length=4.0, width=3.0, height=2.8, window_area=80.0)

    with pytest.raises(ValueError, match="shelter_type must be 'Permanent' or 'Temporary'"):
        ShelterDesign(shelter_type="Igloo")


# =====================================================================
# 10. JSON SERIALIZATION & DESERIALIZATION ROUND-TRIP
# =====================================================================

def test_10_json_serialization_deserialization():
    design = build_leh_ladakh_design()

    # Serialize to JSON string
    json_str = design.to_json(indent=2)
    assert isinstance(json_str, str)
    assert len(json_str) > 100

    # Deserialize back to ShelterDesign
    restored = ShelterDesign.from_json(json_str)
    assert isinstance(restored, ShelterDesign)
    assert restored.design_id == design.design_id
    assert restored.name == design.name
    assert restored.requirements.occupants == design.requirements.occupants
    assert restored.geometry.length_m == design.geometry.length_m
    assert restored.geometry.floor_area_m2 == design.geometry.floor_area_m2
    assert restored.wall_assembly.u_value == pytest.approx(design.wall_assembly.u_value)
    assert restored.glazing.u_value == pytest.approx(design.glazing.u_value)
    assert len(restored.openings) == len(design.openings)
    assert len(restored.thermal_mass_elements) == len(design.thermal_mass_elements)
    assert len(restored.passive_strategies) == len(design.passive_strategies)


# =====================================================================
# 11. SHELTER DESIGN -> SIMULATION INPUT ADAPTER
# =====================================================================

def test_11_shelter_design_to_simulation_input():
    climate = create_mock_climate_profile("leh", hours=168)
    design = build_leh_ladakh_design()

    # Adapt to SimulationInput
    sim_input = SimulationAdapter.to_simulation_input(
        climate=climate,
        design=design,
        hours_to_simulate=168,
        substeps=60,
        initial_indoor_temp=18.0,
    )

    assert isinstance(sim_input, SimulationInput)
    assert sim_input.climate.city == "leh"
    assert sim_input.design.design_id == design.design_id
    assert sim_input.hours_to_simulate == 168
    assert sim_input.substeps == 60
    assert sim_input.initial_indoor_temp == 18.0

    # Derived SimulationEnvelopeParameters
    assert sim_input.envelope_parameters is not None
    assert isinstance(sim_input.envelope_parameters, SimulationEnvelopeParameters)
    assert sim_input.envelope_parameters.wall_u_value == pytest.approx(design.wall_assembly.u_value)
    assert sim_input.envelope_parameters.roof_u_value == pytest.approx(design.roof_assembly.u_value)
    assert sim_input.envelope_parameters.window_u_value == pytest.approx(design.glazing.u_value)
    assert sim_input.envelope_parameters.effective_thermal_capacity_j_k > 0.0

    # Roundtrip serialization of SimulationInput
    sim_dict = sim_input.to_dict()
    reconstructed_input = SimulationInput.from_dict(sim_dict)
    assert reconstructed_input.climate.city == "leh"
    assert reconstructed_input.design.geometry.length_m == design.geometry.length_m


# =====================================================================
# 12. CLIMATE PROFILE SERIALIZATION & METADATA
# =====================================================================

def test_12_climate_profile_serialization_and_metadata():
    n_hours = 48
    profile = ClimateProfile(
        city="leh",
        latitude=34.1526,
        longitude=77.5771,
        hourly_temperature=[-10.0 + 5.0 * math.sin(i / 4.0) for i in range(n_hours)],
        hourly_direct_solar=[500.0 if 8 <= (i % 24) <= 16 else 0.0 for i in range(n_hours)],
        hourly_diffuse_solar=[120.0 if 8 <= (i % 24) <= 16 else 0.0 for i in range(n_hours)],
        hourly_wind_speed=[3.2] * n_hours,
        hourly_humidity=[35.0] * n_hours,
        climate_zone="cold",
        elevation_m=3500.0,
        timezone_offset_hours=5.5,
        hourly_cloud_cover=[0.1] * n_hours,
        hourly_precipitation=[0.0] * n_hours,
        timestamps=[f"2026-01-01T{i%24:02d}:00:00+05:30" for i in range(n_hours)],
        data_source="EPW_Leh_ISD_Normals",
        data_provenance=DataProvenance.HISTORICAL,
        data_confidence=0.98,
    )
    assert profile.elevation_m == 3500.0
    assert profile.timezone_offset_hours == 5.5
    assert profile.data_provenance == "historical"
    assert profile.data_confidence == 0.98

    # Serialization roundtrip
    d = profile.to_dict()
    restored_cp = ClimateProfile.from_dict(d)
    assert restored_cp.city == "leh"
    assert restored_cp.elevation_m == 3500.0
    assert restored_cp.timezone_offset_hours == 5.5
    assert len(restored_cp.hourly_cloud_cover) == n_hours
    assert len(restored_cp.hourly_precipitation) == n_hours
    assert restored_cp.data_confidence == 0.98


# =====================================================================
# 13. UNIT CONSISTENCY VERIFICATION
# =====================================================================

def test_13_unit_consistency():
    design = build_leh_ladakh_design()

    # 1. Dimensions strictly in meters (m)
    assert design.geometry.length_m > 0.0
    assert design.geometry.width_m > 0.0
    assert design.geometry.height_m > 0.0

    # 2. Areas in square meters (m²)
    assert design.geometry.floor_area_m2 == pytest.approx(design.geometry.length_m * design.geometry.width_m)
    assert design.geometry.roof_area_m2 > 0.0

    # 3. Volumes in cubic meters (m³)
    assert design.geometry.volume_m3 > 0.0

    # 4. Material conductivity in W/(m·K)
    for layer in design.wall_assembly.layers:
        assert 0.01 <= layer.conductivity_w_mk <= 10.0  # Physical engineering material conductivity range
        assert layer.thickness_m > 0.0  # Thickness in meters

    # 5. U-values in W/(m²·K)
    assert 0.05 <= design.wall_assembly.u_value <= 10.0
    assert 0.05 <= design.roof_assembly.u_value <= 10.0
    assert 0.1 <= design.glazing.u_value <= 7.0

    # 6. Thermal capacity in J/(kg·K) and J/K
    for tm in design.thermal_mass_elements:
        assert tm.specific_heat_j_kgk > 0.0  # J/(kg·K)
        assert tm.thermal_capacity_j_per_k > 0.0  # J/K
        assert tm.density_kg_m3 > 0.0  # kg/m³


# =====================================================================
# 14. REGRESSION: NO COMPETING DOMAIN SHELTER DESIGN
# =====================================================================

def test_regression_no_competing_domain_shelter_design():
    """
    REGRESSION TEST:
    Proves that services.contracts.ShelterDesign is identically
    services.shelter.models.ShelterDesign. There must NOT be a second
    competing domain-level ShelterDesign anywhere in the codebase.
    """
    assert contracts.ShelterDesign is shelter_models.ShelterDesign
    assert issubclass(contracts.ShelterDesign, shelter_models.ShelterDesign)
    assert contracts.ShelterDesign.__module__ == "services.shelter.models"
