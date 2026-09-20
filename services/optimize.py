"""
THERMOSHELTER AI - Multi-Objective Bayesian Design Optimizer
============================================================
Optimizes shelter envelope configurations using Optuna TPE (Tree-structured
Parzen Estimator) over design parameters and climate-specific boundary conditions.

Supports meaningful distinction between Temporary and Permanent shelters:
- Temporary: Prioritizes rapid deployment, lightweight modular envelopes, portability,
  and low transport weight while maintaining thermal comfort.
- Permanent: Prioritizes high envelope thermal resistance, thermal mass / inertia,
  envelope durability, and lifecycle heat retention.

Produces ranked candidate designs (#1, #2, #3) with explicit multi-objective
scoring breakdowns and transparent physical metrics.
"""

import os
import sys
from typing import Any, Dict, List, Optional, Union

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

try:
    from services.simulation_service import run_simulation, GLAZING_PROPERTIES, ORIENTATION_FACTORS
    from services.climate_service import get_climate_data
    from services.material_service import get_material
    from services.contracts import (
        OptimizationInput,
        OptimizationResult,
        OptimizationCandidate,
        adapt_to_optimization_input,
        adapt_optimization_result,
    )
except ImportError:
    from simulation_service import run_simulation, GLAZING_PROPERTIES, ORIENTATION_FACTORS
    from climate_service import get_climate_data
    from material_service import get_material
    from contracts import (
        OptimizationInput,
        OptimizationResult,
        OptimizationCandidate,
        adapt_to_optimization_input,
        adapt_optimization_result,
    )


# ---------------------------------------------------------------------
# D5-B: geometry optimization is now ENABLED (prototype constraints).
#
# The candidate/result contracts carry geometry fields, and the optimizer
# samples length -> width -> height (0.1 m step) when optimize_geometry
# is True. All geometry limits are PROPOSED PROTOTYPE ENGINEERING
# ASSUMPTIONS supplied by the caller (or the API request) - none are
# invented here. Infeasible candidates (dimension bounds, orientation-
# independent aspect ratio, per-facade opening fit, gross-wall backstop)
# are REJECTED via optuna.TrialPruned BEFORE simulation - the engine's
# 85%/15% clamps are physics guards, never the feasibility model.
# ---------------------------------------------------------------------


def _candidate_geometry_fields(sim_result: Dict[str, Any], length: float, width: float, height: float) -> Dict[str, Any]:
    """
    Builds the D5-A candidate geometry payload from ENGINE-REPORTED values.

    Authority rule: floor area and volume come from the engine's own
    ``geometry`` result block (the same values the physics used). Only when
    the engine omits a value (defensive fallback) is the canonical geometry
    formula consulted - and flagged in the docstring so tests can assert the
    engine path. surface-to-volume ratio uses the thermal-relevant gross
    envelope area (walls + roof + floor) over enclosed volume.
    """
    try:
        from services.geometry import (
            calculate_total_envelope_area,
            calculate_volume,
        )
    except ImportError:  # pragma: no cover - import-parity fallback
        from geometry import (  # type: ignore
            calculate_total_envelope_area,
            calculate_volume,
        )

    engine_geom = sim_result.get("geometry") or {}
    floor_area = engine_geom.get("floor_area_m2")
    volume = engine_geom.get("volume_m3")
    roof_area = engine_geom.get("roof_area_m2")

    floor_area_f = float(floor_area) if floor_area is not None else float(length * width)
    volume_f = float(volume) if volume is not None else float(calculate_volume(length, width, height))

    s2v: Optional[float] = None
    if volume_f > 0.0:
        if roof_area is not None:
            # Envelope area consistent with engine-reported roof geometry.
            wall_gross = 2.0 * (length + width) * height
            envelope_f = float(wall_gross) + float(roof_area) + floor_area_f
        else:
            envelope_f = float(calculate_total_envelope_area(length, width, height))
        s2v = round(envelope_f / volume_f, 4)

    return {
        "length_m": round(float(length), 3),
        "width_m": round(float(width), 3),
        "height_m": round(float(height), 3),
        "floor_area_m2": round(floor_area_f, 2),
        "surface_to_volume_ratio": s2v,
    }




# ---------------------------------------------------------------------
# Phase C: thermal-mass candidate levels. These reuse the canonical
# ShelterDesign floor-core mass semantics EXACTLY (concrete, rho=2300 kg/m3,
# c=880 J/kgK, area = length x width) so optimizer candidates and user
# designs share one physical definition. No invented constants.
# ---------------------------------------------------------------------
THERMAL_MASS_LEVELS: Dict[str, float] = {"none": 0.0, "low": 0.05, "medium": 0.10, "high": 0.20}
_TM_DENSITY_KG_M3 = 2300.0
_TM_SPECIFIC_HEAT_J_KGK = 880.0


def _thermal_mass_capacity_j_k(level: Optional[str], length: float, width: float) -> Optional[float]:
    """Engine-ready extra capacity for a mass level, or None when disabled."""
    thickness_m = THERMAL_MASS_LEVELS.get(str(level), 0.0)
    if thickness_m <= 0.0:
        return None
    return _TM_DENSITY_KG_M3 * _TM_SPECIFIC_HEAT_J_KGK * thickness_m * (length * width)


def _objective(
    trial: Any,
    city: str,
    home_type: str = "Permanent",
    length: float = 4.0,
    width: float = 3.0,
    height: float = 2.8,
    wall_material: Optional[str] = None,
    glazing: Optional[str] = None,
    orientation: Optional[str] = None,
    occupants: int = 2,
    # D5-B door fidelity: canonical design door area (m2) - the single
    # authoritative opening value, used by BOTH pre-simulation feasibility
    # and the candidate simulation so the evaluated door always equals the
    # door the applied design will represent. Default matches the
    # engine/canonical default (2.0 m2) for backward compatibility.
    door_area: float = 2.0,
    min_insulation_m: float = 0.0,
    max_insulation_m: float = 0.20,
    min_window_area: float = 0.5,
    max_window_area: Optional[float] = None,
    allowed_wall_materials: Optional[List[str]] = None,
    allowed_glazings: Optional[List[str]] = None,
    allowed_orientations: Optional[List[str]] = None,
    substeps: int = 15,
    hours_to_simulate: int = 168,
    weights: Optional[Dict[str, float]] = None,
    hourly_temperatures: Optional[List[float]] = None,
    hourly_direct_solar: Optional[List[float]] = None,
    hourly_diffuse_solar: Optional[List[float]] = None,
    thermal_mass_level: Optional[str] = None,
    climate_scenario: Optional[Dict[str, Any]] = None,
    # D5-B geometry search (prototype constraints supplied by the caller):
    optimize_geometry: bool = False,
    min_length_m: Optional[float] = None,
    max_length_m: Optional[float] = None,
    min_width_m: Optional[float] = None,
    max_width_m: Optional[float] = None,
    min_height_m: Optional[float] = None,
    max_height_m: Optional[float] = None,
    min_aspect_ratio: Optional[float] = None,
    max_aspect_ratio: Optional[float] = None,
) -> float:
    """
    Evaluates one candidate shelter configuration against physical objectives.
    Returns a unified discomfort / penalty score to minimize.

    Phase C: when a climate scenario is supplied, the candidate is evaluated
    against the scenario's hourly vectors (same climate as direct simulation);
    the city key is only a fallback label and can never override the vectors.
    """
    is_temp = str(home_type).lower().startswith("temp")

    # ------------------------------------------------------------------
    # 0. D5-B GEOMETRY CANDIDATES FIRST (length -> width -> height).
    #
    # 0.1 m sampling step: PROPOSED PROTOTYPE OPTIMIZATION ASSUMPTION
    # (not an existing-project precedent). With optimize_geometry=False
    # NO geometry parameters are suggested and the suggest order below is
    # byte-identical to Phase C (insulation -> window -> material ->
    # glazing -> orientation -> thermal mass), preserving seeded-sampler
    # reproducibility of the fixed-geometry search.
    # ------------------------------------------------------------------
    if optimize_geometry:
        trial_length = float(
            trial.suggest_float("length", float(min_length_m), float(max_length_m), step=0.1)
        )
        trial_width = float(
            trial.suggest_float("width", float(min_width_m), float(max_width_m), step=0.1)
        )
        trial_height = float(
            trial.suggest_float("height", float(min_height_m), float(max_height_m), step=0.1)
        )
    else:
        trial_length, trial_width, trial_height = float(length), float(width), float(height)

    # 1. Insulation Thickness Candidate
    upper_ins_bound = min(0.12 if is_temp else 0.25, max_insulation_m)
    lower_ins_bound = max(0.0, min(min_insulation_m, upper_ins_bound))
    if lower_ins_bound >= upper_ins_bound:
        insulation_thickness = lower_ins_bound
    else:
        insulation_thickness = trial.suggest_float(
            "insulation_thickness_m", lower_ins_bound, upper_ins_bound, step=0.005
        )

    # 2. Window Area Candidate (within physical wall area constraints;
    # D5-B: bounds derive from the ACTUAL TRIAL geometry when optimizing)
    total_wall_area = 2.0 * (trial_length + trial_width) * trial_height
    upper_win_limit = min(12.0, total_wall_area * 0.40)
    if max_window_area is not None:
        upper_win_limit = min(upper_win_limit, max_window_area)
    lower_win_limit = max(0.2, min_window_area)
    upper_win_limit = max(lower_win_limit, upper_win_limit)

    if lower_win_limit >= upper_win_limit:
        window_area = lower_win_limit
    else:
        window_area = trial.suggest_float(
            "window_area_m2", lower_win_limit, round(upper_win_limit, 1), step=0.1
        )

    # ------------------------------------------------------------------
    # 2b. D5-B: deterministic PRE-SIMULATION feasibility rejection.
    # Infeasible geometries are PRUNED (never simulated, never clamped):
    # dimension bounds, orientation-independent aspect ratio
    # (max(L/W, W/L)), per-facade opening fit, and the gross-wall backstop.
    # ------------------------------------------------------------------
    if optimize_geometry:
        try:
            from services.geometry_feasibility import evaluate_geometry_feasibility
        except ImportError:  # pragma: no cover - import-parity fallback
            from geometry_feasibility import evaluate_geometry_feasibility  # type: ignore
        import optuna as _optuna

        verdict = evaluate_geometry_feasibility(
            trial_length,
            trial_width,
            trial_height,
            window_area=float(window_area),
            door_area=float(door_area),  # canonical design door area (D5-B fidelity)
            min_aspect_ratio=min_aspect_ratio,
            max_aspect_ratio=max_aspect_ratio,
            bounds={
                "length": (float(min_length_m), float(max_length_m)),
                "width": (float(min_width_m), float(max_width_m)),
                "height": (float(min_height_m), float(max_height_m)),
            },
        )
        if not verdict["feasible"]:
            raise _optuna.TrialPruned(verdict["reason"])

    # 3. Wall Material Candidate by Shelter Permanence or Allowed List
    if wall_material and wall_material != "auto":
        wall_mat_choice = wall_material
    elif allowed_wall_materials and len(allowed_wall_materials) > 0:
        wall_mat_choice = trial.suggest_categorical("wall_material", allowed_wall_materials)
    else:
        if is_temp:
            # Temporary: lightweight prefab, PUF panels, timber, brick
            wall_mat_choice = trial.suggest_categorical(
                "wall_material", ["puf_insulation", "eps_insulation", "wood", "brick"]
            )
        else:
            # Permanent: heavy thermal mass, brick, mud, stone, concrete, PUF
            wall_mat_choice = trial.suggest_categorical(
                "wall_material", ["brick", "mud", "stone", "concrete", "puf_insulation"]
            )

    # 4. Glazing Candidate
    if glazing and glazing != "auto":
        glaze_choice = glazing
    elif allowed_glazings and len(allowed_glazings) > 0:
        glaze_choice = trial.suggest_categorical("glazing", allowed_glazings)
    else:
        glaze_choice = trial.suggest_categorical(
            "glazing", ["single_clear", "double_clear", "double_low_e", "triple_low_e"]
        )

    # 5. Orientation Candidate
    if orientation and orientation != "auto":
        orient_choice = orientation
    elif allowed_orientations and len(allowed_orientations) > 0:
        orient_choice = trial.suggest_categorical("orientation", allowed_orientations)
    else:
        orient_choice = trial.suggest_categorical("orientation", ["south", "north", "east", "west"])


    # 5b. Thermal Mass Candidate (Phase C) - none / low / medium / high
    if thermal_mass_level and thermal_mass_level in THERMAL_MASS_LEVELS:
        tm_level_choice = str(thermal_mass_level)
    else:
        tm_level_choice = trial.suggest_categorical(
            "thermal_mass_level", ["none", "low", "medium", "high"]
        )

    # 6. Run Physical Simulation (D5-B: with the TRIAL geometry)
    sim_result = run_simulation(
        city=city,
        length=trial_length,
        width=trial_width,
        height=trial_height,
        wall_material=wall_mat_choice,
        insulation_thickness_m=insulation_thickness,
        window_area=window_area,
        glazing=glaze_choice,
        orientation=orient_choice,
        occupants=occupants,
        door_area=door_area,
        hours_to_simulate=hours_to_simulate,
        substeps=substeps,
        hourly_temperatures=hourly_temperatures,
        hourly_direct_solar=hourly_direct_solar,
        hourly_diffuse_solar=hourly_diffuse_solar,
        extra_thermal_capacity_j_k=_thermal_mass_capacity_j_k(tm_level_choice, trial_length, trial_width),
    )

    if "error" in sim_result:
        raise ValueError(sim_result["error"])

    discomfort_dh = sim_result["comfort_metrics"]["discomfort_dh"]
    total_loss_kwh = sim_result["total_heat_loss_kwh"]
    solar_gain_kwh = sim_result.get("integrated_solar_energy_kwh", 0.0)

    # 7. Permanence-Specific Penalty / Multi-Objective Formulation
    if weights is not None and isinstance(weights, dict):
        w_comfort = weights.get("comfort", 0.50)
        w_eff = weights.get("efficiency", 0.35)
        w_solar = weights.get("solar", 0.15)
        comfort_score = max(0.0, min(100.0, 100.0 - (discomfort_dh / 15.0)))
        efficiency_score = max(0.0, min(100.0, 100.0 - (total_loss_kwh / 10.0)))
        solar_score = min(100.0, solar_gain_kwh * 2.0)
        utility = w_comfort * comfort_score + w_eff * efficiency_score + w_solar * solar_score
        score = 100.0 - utility
        if is_temp:
            mat_info = get_material(wall_mat_choice)
            density = float(mat_info.get("density", 1800.0))
            score += max(0.0, (density - 100.0) / 100.0) * 0.05
    else:
        if is_temp:
            # Penalize excessive heavy material density (transport difficulty)
            mat_info = get_material(wall_mat_choice)
            density = float(mat_info.get("density", 1800.0))
            weight_penalty = max(0.0, (density - 100.0) / 100.0) * 0.05
            # Weighted objective: primary discomfort + moderate loss + weight penalty
            score = discomfort_dh + 0.15 * total_loss_kwh + weight_penalty
        else:
            # Permanent: reward thermal mass stability & envelope efficiency
            # Total heat loss has higher long-term energy cost
            score = discomfort_dh + 0.35 * total_loss_kwh

    return float(score)


def _geometry_search_fields(inp: OptimizationInput) -> Dict[str, Any]:
    """Extracts the D5-B geometry search configuration from a contract input."""
    return {
        "optimize_geometry": bool(getattr(inp, "optimize_geometry", False)),
        "min_length_m": getattr(inp, "min_length_m", None),
        "max_length_m": getattr(inp, "max_length_m", None),
        "min_width_m": getattr(inp, "min_width_m", None),
        "max_width_m": getattr(inp, "max_width_m", None),
        "min_height_m": getattr(inp, "min_height_m", None),
        "max_height_m": getattr(inp, "max_height_m", None),
        "min_aspect_ratio": getattr(inp, "min_aspect_ratio", None),
        "max_aspect_ratio": getattr(inp, "max_aspect_ratio", None),
    }


def optimize_shelter(opt_input: Union[OptimizationInput, Dict[str, Any]]) -> OptimizationResult:
    """
    Executes multi-objective Bayesian optimization from a structured OptimizationInput contract
    and returns a standardized, typed OptimizationResult contract.

    Parameters:
        opt_input (OptimizationInput | dict): Input optimization bounds, target city, and design specs.

    Returns:
        OptimizationResult: Fully typed and validated optimization result contract.
    """
    contract_input = adapt_to_optimization_input(opt_input)

    raw_dict = run_optimization(
        city=contract_input.city,
        home_type=contract_input.home_type,
        length=contract_input.length,
        width=contract_input.width,
        height=contract_input.height,
        wall_material=contract_input.wall_material,
        glazing=contract_input.glazing,
        orientation=contract_input.orientation,
        occupants=contract_input.occupants,
        min_insulation_m=contract_input.min_insulation_m,
        max_insulation_m=contract_input.max_insulation_m,
        min_window_area=contract_input.min_window_area,
        max_window_area=contract_input.max_window_area,
        allowed_wall_materials=contract_input.allowed_wall_materials,
        allowed_glazings=contract_input.allowed_glazings,
        allowed_orientations=contract_input.allowed_orientations,
        n_trials=contract_input.n_trials,
        substeps=contract_input.substeps,
        hours_to_simulate=contract_input.hours_to_simulate,
        weights=contract_input.weights,
        climate_scenario=contract_input.climate_scenario,
        **_geometry_search_fields(contract_input),
    )

    return adapt_optimization_result(raw_dict)


def run_optimization(
    city: Optional[Union[str, OptimizationInput, Dict[str, Any]]] = None,
    home_type: str = "Permanent",
    length: float = 4.0,
    width: float = 3.0,
    height: float = 2.8,
    wall_material: Optional[str] = None,
    glazing: Optional[str] = None,
    orientation: Optional[str] = None,
    occupants: int = 2,
    # D5-B door fidelity: canonical design door area (m2); overridden from
    # OptimizationInput when an input object is supplied.
    door_area: float = 2.0,
    min_insulation_m: float = 0.0,
    max_insulation_m: float = 0.20,
    min_window_area: float = 0.5,
    max_window_area: Optional[float] = None,
    allowed_wall_materials: Optional[List[str]] = None,
    allowed_glazings: Optional[List[str]] = None,
    allowed_orientations: Optional[List[str]] = None,
    n_trials: int = 40,
    substeps: int = 15,
    hours_to_simulate: int = 168,
    weights: Optional[Dict[str, float]] = None,
    climate_scenario: Optional[Dict[str, Any]] = None,
    scenario_kind: Optional[str] = None,
    # D5-B geometry search (prototype constraints supplied by the caller):
    optimize_geometry: bool = False,
    min_length_m: Optional[float] = None,
    max_length_m: Optional[float] = None,
    min_width_m: Optional[float] = None,
    max_width_m: Optional[float] = None,
    min_height_m: Optional[float] = None,
    max_height_m: Optional[float] = None,
    min_aspect_ratio: Optional[float] = None,
    max_aspect_ratio: Optional[float] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Runs Optuna TPE optimization across design parameters and returns
    both the optimal configuration and a ranked list of candidate designs.

    D5-B geometry search: when optimize_geometry is True, length -> width ->
    height are sampled first (0.1 m step - PROPOSED PROTOTYPE OPTIMIZATION
    ASSUMPTION), the window-area bounds derive from the sampled trial
    geometry, and infeasible candidates (orientation-independent aspect
    ratio max(L/W, W/L), per-facade opening fit, gross-wall backstop) are
    pruned BEFORE simulation. All geometry limits are caller-supplied
    PROPOSED PROTOTYPE ENGINEERING ASSUMPTIONS - none are invented here.

    Phase C climate scenario contract:
      - climate_scenario: canonical ClimateProfile dict. When supplied it is
        THE climate for every candidate evaluation (resolved once here, then
        reused in-memory for all trials - the weather API is never called per
        candidate). City-key statistics are NOT used and cannot override it.
      - scenario_kind: optional deterministic design-week selection over the
        scenario series ('cold' | 'hot' | 'typical'); None keeps the series'
        own defined window (live/forecast week, or the head of a design-year
        dataset) - documented in services/climate_scenario.py.

    Accepts either an OptimizationInput instance as the first positional argument,
    or standard keyword arguments.

    Returns:
        dict containing:
          - 'city', 'home_type'
          - 'insulation_thickness_m', 'insulation_mm'
          - 'window_area_m2', 'wall_material', 'glazing', 'glazing_name', 'orientation'
          - 'discomfort_score'
          - 'simulation_result'
          - 'ranked_designs': List of top candidate designs with scores
          - 'n_trials': Number of trials executed
    """
    # Handle polymorphic input: if city is OptimizationInput or dict
    if isinstance(city, OptimizationInput):
        inp = city
        city_str = inp.city
        home_type = inp.home_type
        length = inp.length
        width = inp.width
        height = inp.height
        wall_material = inp.wall_material
        glazing = inp.glazing
        orientation = inp.orientation
        occupants = inp.occupants
        door_area = float(inp.door_area_m2)
        min_insulation_m = inp.min_insulation_m
        max_insulation_m = inp.max_insulation_m
        min_window_area = inp.min_window_area
        max_window_area = inp.max_window_area
        allowed_wall_materials = inp.allowed_wall_materials
        allowed_glazings = inp.allowed_glazings
        allowed_orientations = inp.allowed_orientations
        n_trials = inp.n_trials
        substeps = inp.substeps
        hours_to_simulate = inp.hours_to_simulate
        weights = inp.weights
        climate_scenario = inp.climate_scenario or climate_scenario
        geom = _geometry_search_fields(inp)
        optimize_geometry = geom["optimize_geometry"]
        min_length_m, max_length_m = geom["min_length_m"], geom["max_length_m"]
        min_width_m, max_width_m = geom["min_width_m"], geom["max_width_m"]
        min_height_m, max_height_m = geom["min_height_m"], geom["max_height_m"]
        min_aspect_ratio, max_aspect_ratio = geom["min_aspect_ratio"], geom["max_aspect_ratio"]
    elif isinstance(city, dict) and "city" in city:
        inp = OptimizationInput.from_dict(city)
        city_str = inp.city
        home_type = inp.home_type
        length = inp.length
        width = inp.width
        height = inp.height
        wall_material = inp.wall_material
        glazing = inp.glazing
        orientation = inp.orientation
        occupants = inp.occupants
        door_area = float(inp.door_area_m2)
        min_insulation_m = inp.min_insulation_m
        max_insulation_m = inp.max_insulation_m
        min_window_area = inp.min_window_area
        max_window_area = inp.max_window_area
        allowed_wall_materials = inp.allowed_wall_materials
        allowed_glazings = inp.allowed_glazings
        allowed_orientations = inp.allowed_orientations
        n_trials = inp.n_trials
        substeps = inp.substeps
        hours_to_simulate = inp.hours_to_simulate
        weights = inp.weights
        climate_scenario = inp.climate_scenario or climate_scenario
        geom = _geometry_search_fields(inp)
        optimize_geometry = geom["optimize_geometry"]
        min_length_m, max_length_m = geom["min_length_m"], geom["max_length_m"]
        min_width_m, max_width_m = geom["min_width_m"], geom["max_width_m"]
        min_height_m, max_height_m = geom["min_height_m"], geom["max_height_m"]
        min_aspect_ratio, max_aspect_ratio = geom["min_aspect_ratio"], geom["max_aspect_ratio"]
    else:
        city_str = str(city) if city is not None else "leh"
        # Plain-kwargs path: honour the canonical design's door area under
        # its contract name (door_area_m2) so a spread input object's door
        # value cannot be silently dropped (D5-B door fidelity).
        if kwargs.get("door_area_m2") is not None:
            door_area = float(kwargs["door_area_m2"])

    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    # ------------------------------------------------------------------
    # Phase C: establish THE climate scenario (once, before any trial).
    # With a scenario present, city-statistics are never fetched and can
    # never override the location-derived vectors. The scenario dict
    # carries its own provenance/fallback flags, so optimization and
    # direct simulation always see the SAME dataset (Part 14).
    # ------------------------------------------------------------------
    hourly_t: Optional[List[float]] = None
    hourly_ds: Optional[List[float]] = None
    hourly_dfs: Optional[List[float]] = None
    scenario_dict: Optional[Dict[str, Any]] = None
    scenario_provenance: Optional[str] = None
    scenario_data_mode: Optional[str] = None
    scenario_fallback_used = False
    city_label = city_str

    if climate_scenario is not None:
        try:
            from services.contracts import adapt_to_climate_profile as _adapt_cp
        except ImportError:
            from contracts import adapt_to_climate_profile as _adapt_cp  # type: ignore
        from services.climate_scenario import resolve_optimization_scenario

        profile = _adapt_cp(dict(climate_scenario))
        scenario = resolve_optimization_scenario(
            profile, hours=hours_to_simulate, scenario_kind=scenario_kind
        )
        scenario_dict = scenario.to_dict()
        scenario_provenance = scenario.data_provenance
        scenario_data_mode = climate_scenario.get("data_mode")
        scenario_fallback_used = bool(climate_scenario.get("fallback_used", False))
        hourly_t = scenario.hourly_temperature
        hourly_ds = scenario.hourly_direct_solar
        hourly_dfs = scenario.hourly_diffuse_solar
        if scenario.city:
            city_label = scenario.city
    else:
        weather = get_climate_data(city_str)
        if "error" in weather:
            raise ValueError(weather["error"])

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42)
    )
    study.optimize(
        lambda trial: _objective(
            trial=trial,
            city=city_str,
            home_type=home_type,
            length=length,
            width=width,
            height=height,
            wall_material=wall_material,
            glazing=glazing,
            orientation=orientation,
            occupants=occupants,
            door_area=door_area,
            min_insulation_m=min_insulation_m,
            max_insulation_m=max_insulation_m,
            min_window_area=min_window_area,
            max_window_area=max_window_area,
            allowed_wall_materials=allowed_wall_materials,
            allowed_glazings=allowed_glazings,
            allowed_orientations=allowed_orientations,
            substeps=substeps,
            hours_to_simulate=hours_to_simulate,
            weights=weights,
            hourly_temperatures=hourly_t,
            hourly_direct_solar=hourly_ds,
            hourly_diffuse_solar=hourly_dfs,
            climate_scenario=scenario_dict,
            optimize_geometry=optimize_geometry,
            min_length_m=min_length_m,
            max_length_m=max_length_m,
            min_width_m=min_width_m,
            max_width_m=max_width_m,
            min_height_m=min_height_m,
            max_height_m=max_height_m,
            min_aspect_ratio=min_aspect_ratio,
            max_aspect_ratio=max_aspect_ratio,
        ),
        n_trials=n_trials,
    )

    # D5-B: transparency - count candidates rejected by pre-simulation
    # feasibility (never clamped, never simulated).
    n_pruned = sum(1 for t in study.trials if t.state.name == "PRUNED")

    best_p = study.best_params
    best_ins = round(float(best_p.get("insulation_thickness_m", min_insulation_m)), 3)
    best_win = round(float(best_p.get("window_area_m2", min_window_area)), 2)
    # D5-B: the best trial's geometry is authoritative when searching.
    best_len = round(float(best_p.get("length", length)), 3)
    best_wid = round(float(best_p.get("width", width)), 3)
    best_hgt = round(float(best_p.get("height", height)), 3)

    fallback_mat = (
        wall_material
        if wall_material and wall_material != "auto"
        else (allowed_wall_materials[0] if allowed_wall_materials and len(allowed_wall_materials) > 0 else "brick")
    )
    fallback_glaze = (
        glazing
        if glazing and glazing != "auto"
        else (allowed_glazings[0] if allowed_glazings and len(allowed_glazings) > 0 else "double_clear")
    )
    fallback_orient = (
        orientation
        if orientation and orientation != "auto"
        else (allowed_orientations[0] if allowed_orientations and len(allowed_orientations) > 0 else "south")
    )

    best_mat = str(best_p.get("wall_material", fallback_mat))
    best_glaze = str(best_p.get("glazing", fallback_glaze))
    best_orient = str(best_p.get("orientation", fallback_orient))
    best_score = round(float(study.best_value), 2)


    # Run final authoritative simulation with the best design (full accuracy substeps=60)
    # D5-B: with the BEST TRIAL's geometry when geometry search is enabled.
    best_sim = run_simulation(
        city=city_label,
        length=best_len,
        width=best_wid,
        height=best_hgt,
        wall_material=best_mat,
        insulation_thickness_m=best_ins,
        window_area=best_win,
        glazing=best_glaze,
        orientation=best_orient,
        occupants=occupants,
        door_area=door_area,
        hours_to_simulate=hours_to_simulate,
        substeps=60,
        hourly_temperatures=hourly_t,
        hourly_direct_solar=hourly_ds,
        hourly_diffuse_solar=hourly_dfs,
    )

    glaze_name = GLAZING_PROPERTIES.get(best_glaze, {}).get("name", best_glaze.replace("_", " ").title())

    # Compile Ranked Candidate Designs from Completed Trials
    completed_trials = [t for t in study.trials if t.value is not None and t.state.name == "COMPLETE"]
    completed_trials.sort(key=lambda t: t.value)

    ranked_designs: List[Dict[str, Any]] = []
    seen_configs = set()

    for idx, t in enumerate(completed_trials):
        p = t.params
        c_ins = round(float(p.get("insulation_thickness_m", best_ins)), 3)
        c_win = round(float(p.get("window_area_m2", best_win)), 2)
        c_mat = str(p.get("wall_material", best_mat))
        c_glaze = str(p.get("glazing", best_glaze))
        c_orient = str(p.get("orientation", best_orient))
        c_tm_level = str(p.get("thermal_mass_level", "none"))
        # D5-B: each candidate carries ITS OWN trial geometry (never the base).
        c_len = round(float(p.get("length", best_len)), 3)
        c_wid = round(float(p.get("width", best_wid)), 3)
        c_hgt = round(float(p.get("height", best_hgt)), 3)

        config_key = (
            round(c_ins, 2), round(c_win, 1), c_mat, c_glaze, c_orient, c_tm_level,
            c_len, c_wid, c_hgt,
        )
        if config_key in seen_configs:
            continue
        seen_configs.add(config_key)

        # Run verification simulation for candidate (SAME scenario vectors;
        # Phase C: the candidate's chosen thermal mass reaches the engine;
        # D5-B: with the CANDIDATE's own trial geometry)
        c_sim = run_simulation(
            city=city_label,
            length=c_len,
            width=c_wid,
            height=c_hgt,
            wall_material=c_mat,
            insulation_thickness_m=c_ins,
            window_area=c_win,
            glazing=c_glaze,
            orientation=c_orient,
            occupants=occupants,
            door_area=door_area,
            hours_to_simulate=hours_to_simulate,
            substeps=15,
            hourly_temperatures=hourly_t,
            hourly_direct_solar=hourly_ds,
            hourly_diffuse_solar=hourly_dfs,
            extra_thermal_capacity_j_k=_thermal_mass_capacity_j_k(c_tm_level, c_len, c_wid),
        )
        if "error" in c_sim:
            continue

        c_glaze_name = GLAZING_PROPERTIES.get(c_glaze, {}).get("name", c_glaze.replace("_", " ").title())

        # Calculate sub-scores (0 - 100 scale)
        comfort_pct = c_sim["comfort_percentage"]
        discomfort_dh = c_sim["discomfort_degree_hours"]
        heat_loss = c_sim["total_heat_loss_kwh"]
        solar_gain = c_sim.get("integrated_solar_energy_kwh", 0.0)

        comfort_score = round(max(0.0, min(100.0, 100.0 - (discomfort_dh / 15.0))), 1)
        efficiency_score = round(max(0.0, min(100.0, 100.0 - (heat_loss / 10.0))), 1)
        solar_score = round(min(100.0, solar_gain * 2.0), 1)

        w_c = weights.get("comfort", 0.50) if weights else 0.50
        w_e = weights.get("efficiency", 0.35) if weights else 0.35
        w_s = weights.get("solar", 0.15) if weights else 0.15
        overall_score = round(w_c * comfort_score + w_e * efficiency_score + w_s * solar_score, 1)

        design_label = f"Design #{len(ranked_designs) + 1}"
        if len(ranked_designs) == 0:
            rationale = "Optimal Multi-Criteria Balance (Highest Comfort & Envelope Retention)"
        elif len(ranked_designs) == 1:
            rationale = "High Thermal Efficiency Alternative"
        else:
            rationale = "Balanced Alternative Configuration"

        candidate_record = {
            "rank": len(ranked_designs) + 1,
            "label": design_label,
            "rationale": rationale,
            "overall_score": overall_score,
            "sub_scores": {
                "comfort": comfort_score,
                "efficiency": efficiency_score,
                "solar": solar_score,
            },
            "insulation_mm": round(c_ins * 1000.0, 1),
            "insulation_thickness_m": c_ins,
            "window_area_m2": c_win,
            "wall_material": c_mat,
            "wall_material_name": get_material(c_mat).get("name", c_mat.title()),
            "glazing": c_glaze,
            "glazing_name": c_glaze_name,
            "orientation": c_orient,
            "comfort_hours": c_sim["comfort_hours"],
            "comfort_percentage": c_sim["comfort_percentage"],
            "discomfort_dh": discomfort_dh,
            "total_heat_loss_kwh": heat_loss,
            "solar_gain_kwh": solar_gain,
            "u_values": c_sim["u_values"],
            "heating_demand_kwh": c_sim.get("heating_demand_kwh", c_sim.get("energy_totals_kwh", {}).get("heating_demand_kwh", 0.0)),
            "cooling_demand_kwh": c_sim.get("cooling_demand_kwh", c_sim.get("energy_totals_kwh", {}).get("cooling_demand_kwh", 0.0)),
            "total_conditioning_demand_kwh": c_sim.get("total_conditioning_demand_kwh", c_sim.get("energy_totals_kwh", {}).get("total_conditioning_demand_kwh", 0.0)),
            "effective_thermal_capacity_j_k": c_sim.get("effective_thermal_capacity_j_k", 0.0),
            "climate_provenance": scenario_provenance,
            "climate_data_mode": scenario_data_mode,
            "climate_fallback_used": scenario_fallback_used,
            "thermal_mass_level": c_tm_level,
            # D5-B: candidate geometry from its OWN ENGINE-REPORTED values
            # (the same simulated envelope Apply/Blueprint/3D/Report will show).
            **_candidate_geometry_fields(c_sim, c_len, c_wid, c_hgt),
        }
        ranked_designs.append(candidate_record)

        if len(ranked_designs) >= 3:
            break

    # If no candidates were compiled (edge case), add best_design
    if len(ranked_designs) == 0:
        c_sim = best_sim
        comfort_score = max(0.0, min(100.0, 100.0 - (c_sim["discomfort_degree_hours"] / 15.0)))
        efficiency_score = max(0.0, min(100.0, 100.0 - (c_sim["total_heat_loss_kwh"] / 10.0)))
        solar_score = min(100.0, c_sim.get("integrated_solar_energy_kwh", 0.0) * 2.0)
        w_c = weights.get("comfort", 0.50) if weights else 0.50
        w_e = weights.get("efficiency", 0.35) if weights else 0.35
        w_s = weights.get("solar", 0.15) if weights else 0.15
        overall_score = round(w_c * comfort_score + w_e * efficiency_score + w_s * solar_score, 1)

        ranked_designs.append({
            "rank": 1,
            "label": "Design #1",
            "rationale": "Optimal Multi-Criteria Balance (Highest Comfort & Envelope Retention)",
            "overall_score": overall_score,
            "sub_scores": {
                "comfort": round(comfort_score, 1),
                "efficiency": round(efficiency_score, 1),
                "solar": round(solar_score, 1),
            },
            "insulation_mm": round(best_ins * 1000.0, 1),
            "insulation_thickness_m": best_ins,
            "window_area_m2": best_win,
            "wall_material": best_mat,
            "wall_material_name": get_material(best_mat).get("name", best_mat.title()),
            "glazing": best_glaze,
            "glazing_name": glaze_name,
            "orientation": best_orient,
            "comfort_hours": c_sim["comfort_hours"],
            "comfort_percentage": c_sim["comfort_percentage"],
            "discomfort_dh": c_sim["discomfort_degree_hours"],
            "total_heat_loss_kwh": c_sim["total_heat_loss_kwh"],
            "solar_gain_kwh": c_sim.get("integrated_solar_energy_kwh", 0.0),
            "u_values": c_sim["u_values"],
            "heating_demand_kwh": c_sim.get("heating_demand_kwh", c_sim.get("energy_totals_kwh", {}).get("heating_demand_kwh", 0.0)),
            "cooling_demand_kwh": c_sim.get("cooling_demand_kwh", c_sim.get("energy_totals_kwh", {}).get("cooling_demand_kwh", 0.0)),
            "total_conditioning_demand_kwh": c_sim.get("total_conditioning_demand_kwh", c_sim.get("energy_totals_kwh", {}).get("total_conditioning_demand_kwh", 0.0)),
            "effective_thermal_capacity_j_k": c_sim.get("effective_thermal_capacity_j_k", 0.0),
            # D5-B: edge-case candidate also reports the best trial's geometry.
            **_candidate_geometry_fields(c_sim, best_len, best_wid, best_hgt),
        })


    scenario_note = ""
    if scenario_dict is not None:
        scenario_note = (
            f" Evaluated against the location-derived climate scenario "
            f"(provenance: {scenario_provenance or 'unknown'}"
            + (", fallback dataset" if scenario_fallback_used else "")
            + ")."
        )

    explanation = (
        f"Optimized {home_type} shelter configuration for {str(city_label).title()} achieving "
        f"{best_sim['comfort_percentage']:.1f}% comfort hours with {best_ins * 1000.0:.0f} mm insulation "
        f"and {best_mat.replace('_', ' ').title()} walls."
        + scenario_note
    )

    return {
        "city": city_label,
        "home_type": home_type,
        "n_pruned": n_pruned,
        "insulation_thickness_m": best_ins,
        "insulation_mm": round(best_ins * 1000.0, 1),
        "window_area_m2": best_win,
        "wall_material": best_mat,
        "glazing": best_glaze,
        "glazing_name": glaze_name,
        "orientation": best_orient,
        "discomfort_score": best_score,
        "simulation_result": best_sim,
        "ranked_designs": ranked_designs,
        "n_trials": n_trials,
        "explanation": explanation,
        "climate_scenario": scenario_dict,
        "climate_provenance": scenario_provenance,
        "climate_data_mode": scenario_data_mode,
        "climate_fallback_used": scenario_fallback_used,
    }


if __name__ == "__main__":
    test_city = "leh"
    print(f"🧠 Running optimization for {test_city.upper()} (Temporary Shelter)...")
    res = run_optimization(test_city, home_type="Temporary", n_trials=30)
    print(f"Optimal Insulation: {res['insulation_mm']} mm")
    print(f"Optimal Window Area: {res['window_area_m2']:.2f} m²")
    print(f"Optimal Material: {res['wall_material']}")
    print(f"Ranked Designs: {len(res['ranked_designs'])}")
    for d in res['ranked_designs']:
        print(f" - {d['label']}: {d['wall_material']} | {d['insulation_mm']}mm | Score: {d['overall_score']}")