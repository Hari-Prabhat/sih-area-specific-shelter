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
) -> float:
    """
    Evaluates one candidate shelter configuration against physical objectives.
    Returns a unified discomfort / penalty score to minimize.
    """
    is_temp = str(home_type).lower().startswith("temp")

    # 1. Insulation Thickness Candidate
    upper_ins_bound = min(0.12 if is_temp else 0.25, max_insulation_m)
    lower_ins_bound = max(0.0, min(min_insulation_m, upper_ins_bound))
    if lower_ins_bound >= upper_ins_bound:
        insulation_thickness = lower_ins_bound
    else:
        insulation_thickness = trial.suggest_float(
            "insulation_thickness_m", lower_ins_bound, upper_ins_bound, step=0.005
        )

    # 2. Window Area Candidate (within physical wall area constraints)
    total_wall_area = 2.0 * (length + width) * height
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


    # 6. Run Physical Simulation
    sim_result = run_simulation(
        city=city,
        length=length,
        width=width,
        height=height,
        wall_material=wall_mat_choice,
        insulation_thickness_m=insulation_thickness,
        window_area=window_area,
        glazing=glaze_choice,
        orientation=orient_choice,
        occupants=occupants,
        hours_to_simulate=hours_to_simulate,
        substeps=substeps,
        hourly_temperatures=hourly_temperatures,
        hourly_direct_solar=hourly_direct_solar,
        hourly_diffuse_solar=hourly_diffuse_solar,
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
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Runs Optuna TPE optimization across design parameters and returns
    both the optimal configuration and a ranked list of candidate designs.

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
    else:
        city_str = str(city) if city is not None else "leh"

    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

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
        ),
        n_trials=n_trials,
    )

    best_p = study.best_params
    best_ins = round(float(best_p.get("insulation_thickness_m", min_insulation_m)), 3)
    best_win = round(float(best_p.get("window_area_m2", min_window_area)), 2)

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
    best_sim = run_simulation(
        city=city_str,
        length=length,
        width=width,
        height=height,
        wall_material=best_mat,
        insulation_thickness_m=best_ins,
        window_area=best_win,
        glazing=best_glaze,
        orientation=best_orient,
        occupants=occupants,
        hours_to_simulate=hours_to_simulate,
        substeps=60,
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

        config_key = (round(c_ins, 2), round(c_win, 1), c_mat, c_glaze, c_orient)
        if config_key in seen_configs:
            continue
        seen_configs.add(config_key)

        # Run verification simulation for candidate
        c_sim = run_simulation(
            city=city_str,
            length=length,
            width=width,
            height=height,
            wall_material=c_mat,
            insulation_thickness_m=c_ins,
            window_area=c_win,
            glazing=c_glaze,
            orientation=c_orient,
            occupants=occupants,
            hours_to_simulate=hours_to_simulate,
            substeps=15,
        )
        if "error" in c_sim:
            continue

        c_glaze_name = GLAZING_PROPERTIES.get(c_glaze, {}).get("name", c_glaze.replace("_", " ").title())
        
        # Calculate sub-scores (0 - 100 scale)
        comfort_pct = c_sim["comfort_percentage"]
        discomfort_dh = c_sim["discomfort_degree_hours"]
        heat_loss = c_sim["total_heat_loss_kwh"]
        solar_gain = c_sim.get("integrated_solar_energy_kwh", 0.0)

        comfort_score = max(0.0, min(100.0, 100.0 - (discomfort_dh / 15.0)))
        efficiency_score = max(0.0, min(100.0, 100.0 - (heat_loss / 10.0)))
        solar_score = min(100.0, solar_gain * 2.0)

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
                "comfort": round(comfort_score, 1),
                "efficiency": round(efficiency_score, 1),
                "solar": round(solar_score, 1),
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
        })


    explanation = (
        f"Optimized {home_type} shelter configuration for {city_str.title()} achieving "
        f"{best_sim['comfort_percentage']:.1f}% comfort hours with {best_ins * 1000.0:.0f} mm insulation "
        f"and {best_mat.replace('_', ' ').title()} walls."
    )

    return {
        "city": city_str,
        "home_type": home_type,
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