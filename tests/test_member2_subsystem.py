"""
THERMOSHELTER AI — Member 2 Comprehensive Subsystem Unit Tests
==============================================================
Tests for:
1. Parametric Shelter Geometry Engine (Part 5)
   - Rectangular, compact, elongated, pitched, custom geometry
   - Surface area, volume, gross/net wall areas, S/V ratio, WWR
   - Orientation azimuth normalization
   - Strict physical validation & error rejection
2. Material & Multilayer Envelope Engine (Part 6)
   - Material layer resistance, areal mass, heat capacity
   - ISO 6946 multi-layer composite assembly R-values & U-values
   - Surface film resistances (wall, roof, floor)
   - Explicit sensible thermal mass storage capacity
   - Glazing specification & fenestration
3. Openings & Fenestration Engine
   - Valid & invalid opening dimensions & areas
   - Facade bounds validation
   - Opening operability & ventilation roles
4. Passive Systems Engine (Part 7)
   - Strategy catalog instantiation
   - Cold, hot-dry, hot-humid default strategy suites
   - Enabling / disabling toggles & parameter updates
   - Parameter bounds validation
   - Proper technical nomenclature verification
5. Canonical ShelterDesign Digital Twin
   - Fluent builder pattern
   - Leh/Ladakh extreme cold hero design construction
   - Hot-dry desert benchmark design construction
   - Full JSON serialization and deserialization roundtrip
   - Mock data validation
"""

import json
import math
import os
import pytest

from services.shelter.models import (
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
from services.shelter.geometry_engine import (
    GeometryValidationError,
    calculate_geometry_metrics,
    create_compact_geometry,
    create_custom_geometry,
    create_elongated_geometry,
    create_pitched_roof_geometry,
    create_rectangular_geometry,
    normalize_azimuth,
    validate_geometry,
)
from services.shelter.envelope_engine import (
    calculate_assembly_metrics,
    calculate_thermal_capacity,
    create_glazing,
    create_material_assembly,
    create_material_layer,
    create_thermal_mass,
)
from services.shelter.passive_systems import (
    PassiveStrategyValidationError,
    create_passive_strategy,
    get_default_cold_region_strategies,
    get_default_hot_dry_strategies,
    get_default_hot_humid_strategies,
    get_strategy_catalog,
    validate_passive_strategy,
)
from services.shelter.builder import (
    ShelterDesignBuildError,
    ShelterDesignBuilder,
    build_hot_dry_design,
    build_leh_ladakh_design,
    load_shelter_design_from_file,
    save_shelter_design_to_file,
)


# =====================================================================
# 1. PARAMETRIC GEOMETRY TESTS
# =====================================================================

class TestParametricGeometry:
    """Tests for geometry calculations, roof shapes, and validations."""

    def test_rectangular_geometry_nominal(self):
        # 5.0m x 4.0m x 2.5m flat roof
        geom = create_rectangular_geometry(length_m=5.0, width_m=4.0, height_m=2.5)
        assert geom.floor_area_m2 == pytest.approx(20.0)
        assert geom.volume_m3 == pytest.approx(50.0)
        # Gross wall area = 2 * (5 + 4) * 2.5 = 45.0
        assert geom.gross_wall_area_m2 == pytest.approx(45.0)
        assert geom.net_wall_area_m2 == pytest.approx(45.0)
        assert geom.roof_area_m2 == pytest.approx(20.0)
        # Total envelope = 20 (floor) + 20 (roof) + 45 (walls) = 85.0
        assert geom.total_envelope_area_m2 == pytest.approx(85.0)
        # S/V ratio = 85 / 50 = 1.7
        assert geom.surface_to_volume_ratio == pytest.approx(1.7)
        assert geom.orientation_deg == pytest.approx(180.0)  # Default South

    def test_compact_geometry_surface_area_reduction(self):
        # A compact 16m² shelter (4x4) has lower wall area than an elongated 16m² shelter (8x2)
        compact = create_compact_geometry(length_m=4.0, width_m=4.0, height_m=2.5)
        elongated = create_rectangular_geometry(length_m=8.0, width_m=2.0, height_m=2.5)

        assert compact.floor_area_m2 == elongated.floor_area_m2
        assert compact.volume_m3 == elongated.volume_m3
        # Compact wall = 2 * (4+4) * 2.5 = 40; Elongated wall = 2 * (8+2) * 2.5 = 50
        assert compact.gross_wall_area_m2 < elongated.gross_wall_area_m2
        assert compact.surface_to_volume_ratio < elongated.surface_to_volume_ratio
        assert compact.geometry_type == "compact"

    def test_elongated_geometry(self):
        elongated = create_elongated_geometry(floor_area_m2=25.0, aspect_ratio=2.5, height_m=2.6)
        assert elongated.geometry_type == "elongated"
        assert elongated.floor_area_m2 == pytest.approx(25.0, abs=0.1)
        assert elongated.length_m > elongated.width_m
        assert (elongated.length_m / elongated.width_m) == pytest.approx(2.5, abs=0.1)

    def test_pitched_roof_geometry(self):
        # 6.0m x 4.0m x 2.5m with 30° roof pitch
        # span = 4.0m -> ridge_height = 2.0 * tan(30°) = 2.0 * 0.57735 = 1.1547m
        # roof_area = (6.0 * 4.0) / cos(30°) = 24.0 / 0.866025 = 27.7128m²
        # attic_volume = 0.5 * 4.0 * 1.1547 * 6.0 = 13.8564m³
        geom = create_pitched_roof_geometry(length_m=6.0, width_m=4.0, height_m=2.5, roof_pitch_deg=30.0)
        assert geom.roof_type == "pitched"
        assert geom.roof_pitch_deg == 30.0
        assert geom.ridge_height_m == pytest.approx(1.1547, rel=1e-3)
        assert geom.roof_area_m2 == pytest.approx(27.7128, rel=1e-3)
        base_vol = 6.0 * 4.0 * 2.5  # 60.0
        assert geom.volume_m3 > base_vol
        assert geom.volume_m3 == pytest.approx(60.0 + 13.8564, rel=1e-3)

    def test_orientation_azimuth_normalization(self):
        assert normalize_azimuth(0.0) == 0.0
        assert normalize_azimuth(90.0) == 90.0
        assert normalize_azimuth(180.0) == 180.0
        assert normalize_azimuth(270.0) == 270.0
        assert normalize_azimuth(360.0) == 0.0
        assert normalize_azimuth(450.0) == 90.0
        assert normalize_azimuth(-90.0) == 270.0

    def test_invalid_dimensions_rejected(self):
        with pytest.raises(GeometryValidationError, match="positive"):
            create_rectangular_geometry(length_m=-5.0, width_m=4.0, height_m=2.5)
        with pytest.raises(GeometryValidationError, match="positive"):
            create_rectangular_geometry(length_m=5.0, width_m=0.0, height_m=2.5)
        with pytest.raises(GeometryValidationError, match="positive"):
            create_rectangular_geometry(length_m=5.0, width_m=4.0, height_m=-2.5)

    def test_invalid_roof_pitch_rejected(self):
        with pytest.raises(GeometryValidationError, match="pitch"):
            create_rectangular_geometry(5.0, 4.0, 2.5, roof_type="pitched", roof_pitch_deg=-5.0)
        with pytest.raises(GeometryValidationError, match="pitch"):
            create_rectangular_geometry(5.0, 4.0, 2.5, roof_type="pitched", roof_pitch_deg=90.0)

    def test_openings_exceeding_wall_rejected(self):
        # Gross wall area = 2 * (3 + 3) * 2.0 = 24.0 m²
        # South facade = 3 * 2 = 6.0 m²
        huge_window = OpeningDefinition(
            id="huge_win",
            name="Too Big Window",
            opening_type="window",
            width_m=4.0,
            height_m=2.0,
            area_m2=8.0,  # 8.0 m² > 6.0 m² south wall!
            facade="south",
            orientation_deg=180.0,
        )
        with pytest.raises(GeometryValidationError, match="exceed"):
            create_rectangular_geometry(length_m=3.0, width_m=3.0, height_m=2.0, openings=[huge_window])

    def test_zones_exceeding_floor_area_rejected(self):
        z1 = ZoneDefinition(id="z1", name="Z1", zone_type="occupied", floor_area_m2=15.0, volume_m3=30.0)
        z2 = ZoneDefinition(id="z2", name="Z2", zone_type="buffer", floor_area_m2=15.0, volume_m3=30.0)
        # Total zone floor = 30.0 m² > 20.0 m² shelter floor
        with pytest.raises(GeometryValidationError, match="zone"):
            create_rectangular_geometry(length_m=5.0, width_m=4.0, height_m=2.5, zones=[z1, z2])


# =====================================================================
# 2. MATERIAL & MULTILAYER ENVELOPE TESTS
# =====================================================================

class TestMaterialAndEnvelopeEngine:
    """Tests for material properties, multilayer assembly R & U-values, and thermal mass."""

    def test_material_layer_from_db(self):
        layer = create_material_layer("mud_brick", thickness_m=0.20)
        assert layer.material_id == "mud_brick"
        assert layer.thickness_m == 0.20
        # Mud brick conductivity typical is 0.60 W/mK
        assert layer.conductivity_w_mk == pytest.approx(0.60)
        # R = 0.20 / 0.60 = 0.3333 m²K/W
        assert layer.resistance_m2_k_w == pytest.approx(0.3333, abs=1e-3)
        # Density = 1600 kg/m³ -> Areal mass = 1600 * 0.20 = 320 kg/m²
        assert layer.mass_per_m2_kg == pytest.approx(320.0)
        # Specific heat = 1000 J/kgK -> Capacitance = 320 * 1000 = 320,000 J/m²K
        assert layer.heat_capacity_per_m2_j_k == pytest.approx(320000.0)
        assert layer.data_status == "literature/reference"

    def test_material_layer_user_defined(self):
        layer = create_material_layer(
            material_id="aerogel_custom",
            thickness_m=0.03,
            conductivity_w_mk=0.015,
            density_kg_m3=150.0,
            specific_heat_j_kgk=1200.0,
        )
        assert layer.data_status == "user-defined"
        assert layer.resistance_m2_k_w == pytest.approx(2.0)  # 0.03 / 0.015 = 2.0

    def test_material_layer_invalid_inputs(self):
        with pytest.raises(ValueError, match="thickness"):
            create_material_layer("mud_brick", thickness_m=-0.10)
        with pytest.raises(ValueError, match="not found"):
            create_material_layer("non_existent_mat_xyz", thickness_m=0.10)

    def test_multilayer_assembly_iso6946_conformance(self):
        # Wall with 20cm mud brick (k=0.6) + 10cm PUF (k=0.024)
        # R_mud = 0.20 / 0.6 = 0.3333
        # R_puf = 0.10 / 0.024 = 4.1667
        # R_layers = 4.5000
        # R_inside = 0.13, R_outside = 0.04 -> R_total = 0.17 + 4.50 = 4.6700
        # U = 1 / 4.6700 = 0.2141 W/m²K
        l1 = create_material_layer("mud_brick", thickness_m=0.20)
        l2 = create_material_layer("polyurethane_foam", thickness_m=0.10)
        assembly = create_material_assembly("wall_insulated", "Mud + PUF Wall", "wall", [l1, l2])

        assert assembly.r_inside == pytest.approx(0.13)
        assert assembly.r_outside == pytest.approx(0.04)
        assert assembly.r_layers == pytest.approx(4.500, abs=1e-2)
        assert assembly.r_total == pytest.approx(4.670, abs=1e-2)
        assert assembly.u_value == pytest.approx(1.0 / 4.670, abs=1e-3)
        assert assembly.total_thickness_m == pytest.approx(0.30)

    def test_roof_assembly_horizontal_surface_film(self):
        # Roof assembly should use horizontal film resistances: R_in=0.10, R_out=0.04
        l_roof = create_material_layer("wood_timber_pine", thickness_m=0.05)
        roof = create_material_assembly("roof_timber", "Timber Roof", "roof", [l_roof])
        assert roof.r_inside == pytest.approx(0.10)
        assert roof.r_outside == pytest.approx(0.04)

    def test_thermal_mass_calculation(self):
        # 10 m² of 0.20m thick concrete:
        # V = 2.0 m³
        # Concrete rho = 2300 kg/m³, cp = 880 J/kgK (from materials.json)
        # mass = 2.0 * 2300 = 4600 kg
        # capacitance = 4600 * 880 = 4,048,000 J/K
        tm = create_thermal_mass(
            id="tm_concrete_slab",
            name="Concrete Floor Slab",
            material_id="concrete_standard",
            thickness_m=0.20,
            area_m2=10.0,
            location="floor_slab",
        )
        assert tm.volume_m3 == pytest.approx(2.0)
        assert tm.mass_kg == pytest.approx(4600.0)
        assert tm.thermal_capacity_j_per_k == pytest.approx(4048000.0)

    def test_glazing_spec_from_db(self):
        gl = create_glazing("double_low_e_argon_16mm")
        assert gl.id == "double_low_e_argon_16mm"
        assert gl.u_value == pytest.approx(1.2)
        assert gl.shgc == pytest.approx(0.55)
        assert gl.visible_transmittance == pytest.approx(0.72)
        assert gl.is_argon_filled is True


# =====================================================================
# 3. OPENINGS & FENESTRATION TESTS
# =====================================================================

class TestOpenings:
    """Tests for fenestrations, shading factors, and ventilation roles."""

    def test_opening_creation_valid(self):
        op = OpeningDefinition(
            id="w1",
            name="South Window",
            opening_type="window",
            width_m=1.5,
            height_m=1.2,
            area_m2=1.8,
            facade="south",
            orientation_deg=180.0,
            is_operable=True,
            glazing_id="double_low_e_argon_16mm",
            shading_factor=0.85,
            overhang_depth_m=0.4,
            ventilation_role="inlet",
        )
        assert op.area_m2 == 1.8
        assert op.is_operable is True
        assert op.ventilation_role == "inlet"

    def test_opening_invalid_negative_dimensions(self):
        with pytest.raises(ValueError, match="positive"):
            OpeningDefinition(
                id="w_bad",
                name="Bad",
                opening_type="window",
                width_m=-1.0,
                height_m=1.2,
                area_m2=1.2,
                facade="south",
                orientation_deg=180.0,
            )

    def test_opening_invalid_shading_factor(self):
        with pytest.raises(ValueError, match="Shading factor"):
            OpeningDefinition(
                id="w_bad_shade",
                name="Bad",
                opening_type="window",
                width_m=1.0,
                height_m=1.0,
                area_m2=1.0,
                facade="south",
                orientation_deg=180.0,
                shading_factor=1.5,  # > 1.0
            )


# =====================================================================
# 4. PASSIVE SYSTEMS ENGINE TESTS
# =====================================================================

class TestPassiveSystems:
    """Tests for passive design strategies and technical naming."""

    def test_strategy_catalog_retrieval(self):
        catalog = get_strategy_catalog()
        assert len(catalog) >= 10
        assert "high_performance_insulation" in catalog
        assert "night_cooling_and_mass_precooling" in catalog
        assert "natural_cross_ventilation" in catalog

    def test_cold_region_strategies_suite(self):
        cold_strats = get_default_cold_region_strategies()
        assert len(cold_strats) == 6
        strat_ids = [s.id for s in cold_strats]
        assert "high_performance_insulation" in strat_ids
        assert "direct_solar_gain_south_aperture" in strat_ids
        assert "sensible_thermal_mass_storage" in strat_ids
        assert "entry_airlock_vestibule" in strat_ids
        assert "controlled_low_rate_ventilation" in strat_ids

    def test_hot_dry_technical_nomenclature(self):
        hot_strats = get_default_hot_dry_strategies()
        night_flush = next(s for s in hot_strats if s.id == "night_cooling_and_mass_precooling")
        # Must match exact technical terminology
        assert night_flush.name == "Night-Time Cool-Air Flushing and Thermal-Mass Pre-Cooling"
        assert "storing cold air" not in night_flush.name.lower()

    def test_strategy_enable_disable_toggle(self):
        strat = create_passive_strategy("entry_airlock_vestibule", enabled=True)
        assert strat.enabled is True
        strat.enabled = False
        assert strat.enabled is False

    def test_strategy_parameter_validation(self):
        # Negative ACH should be rejected
        with pytest.raises(PassiveStrategyValidationError, match="ach"):
            create_passive_strategy(
                "night_cooling_and_mass_precooling",
                parameters={"night_flush_ach": -2.0},
            )

    def test_custom_passive_strategy(self):
        custom = create_passive_strategy(
            strategy_id="evaporative_water_wall",
            name="Evaporative Cooling Water Wall",
            category="hot_dry",
            climate_applicability=["hot_dry"],
            parameters={"water_flow_rate_l_min": 5.0},
        )
        assert custom.category == "hot_dry"
        assert custom.parameters["water_flow_rate_l_min"] == 5.0


# =====================================================================
# 5. SHELTER DESIGN & BUILDER TESTS
# =====================================================================

class TestShelterDesignAndBuilder:
    """Tests for ShelterDesignBuilder, presets, JSON serialization and roundtrip."""

    def test_leh_ladakh_hero_design_completeness(self):
        design = build_leh_ladakh_design()
        assert design.design_id == "shelter_leh_ladakh_hero"
        assert design.requirements.occupants == 4
        assert design.requirements.permanence == "permanent"
        assert design.geometry.floor_area_m2 == pytest.approx(20.0)
        assert design.wall_assembly.u_value < 0.26  # Meets cold-climate high-insulation target
        assert design.roof_assembly.u_value < 0.20
        assert len(design.openings) == 3
        assert len(design.zones) == 3
        assert len(design.thermal_mass_elements) == 2
        assert len(design.passive_strategies) == 6

    def test_hot_dry_benchmark_design_completeness(self):
        design = build_hot_dry_design()
        assert design.design_id == "shelter_hot_dry_benchmark"
        assert design.requirements.occupants == 4
        assert design.geometry.geometry_type == "rectangular"
        assert len(design.passive_strategies) == 4

    def test_json_serialization_roundtrip(self):
        original = build_leh_ladakh_design()
        json_str = original.to_json(indent=2)
        assert isinstance(json_str, str)
        assert len(json_str) > 500

        restored = ShelterDesign.from_json(json_str)
        assert restored.design_id == original.design_id
        assert restored.name == original.name
        assert restored.requirements.occupants == original.requirements.occupants
        assert restored.geometry.floor_area_m2 == pytest.approx(original.geometry.floor_area_m2)
        assert restored.wall_assembly.u_value == pytest.approx(original.wall_assembly.u_value)
        assert restored.roof_assembly.u_value == pytest.approx(original.roof_assembly.u_value)
        assert len(restored.openings) == len(original.openings)
        assert len(restored.zones) == len(original.zones)
        assert len(restored.passive_strategies) == len(original.passive_strategies)

    def test_builder_missing_requirements_raises(self):
        builder = ShelterDesignBuilder("d1", "Incomplete")
        geom = create_rectangular_geometry(4.0, 3.0, 2.5)
        builder.set_geometry(geom)
        with pytest.raises(ShelterDesignBuildError, match="Requirements"):
            builder.build()

    def test_builder_missing_wall_assembly_raises(self):
        builder = ShelterDesignBuilder("d1", "Incomplete")
        req = ShelterRequirements(occupants=2, shelter_purpose="test")
        geom = create_rectangular_geometry(4.0, 3.0, 2.5)
        builder.set_requirements(req)
        builder.set_geometry(geom)
        with pytest.raises(ShelterDesignBuildError, match="Wall MaterialAssembly"):
            builder.build()

    def test_mock_data_files_consistency(self):
        """Verifies that all mock files in data/mock/ load properly and validate against domain models."""
        mock_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "mock")
        assert os.path.exists(mock_dir), "data/mock directory must exist"

        # 1. Test mock requirements
        with open(os.path.join(mock_dir, "mock_shelter_requirements.json"), "r") as f:
            req_dict = json.load(f)
        req = ShelterRequirements.from_dict(req_dict)
        assert req.occupants > 0

        # 2. Test mock geometry
        with open(os.path.join(mock_dir, "mock_shelter_geometry.json"), "r") as f:
            geom_dict = json.load(f)
        geom = ShelterGeometry.from_dict(geom_dict)
        validate_geometry(geom)
        assert geom.floor_area_m2 > 0

        # 3. Test mock assemblies
        with open(os.path.join(mock_dir, "mock_material_assembly.json"), "r") as f:
            assemb_dict = json.load(f)
        wall_assemb = MaterialAssembly.from_dict(assemb_dict["wall_assembly"])
        assert wall_assemb.u_value > 0

        # 4. Test mock passive strategies
        with open(os.path.join(mock_dir, "mock_passive_strategy.json"), "r") as f:
            strat_list = json.load(f)
        assert len(strat_list) > 0
        s0 = PassiveStrategy.from_dict(strat_list[0])
        validate_passive_strategy(s0)

        # 5. Test mock Leh shelter design
        with open(os.path.join(mock_dir, "mock_shelter_design_leh.json"), "r") as f:
            leh_design = ShelterDesign.from_json(f.read())
        assert leh_design.design_id == "shelter_leh_ladakh_hero"
        assert leh_design.geometry.floor_area_m2 > 0
        assert leh_design.wall_assembly.u_value > 0
