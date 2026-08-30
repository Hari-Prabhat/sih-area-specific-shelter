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
from typing import Any, Dict, List, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from simulation_service import run_simulation, GLAZING_PROPERTIES, ORIENTATION_FACTORS
from climate_service import get_climate_data
from material_service import get_material


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
    max_insulation_m: float = 0.20,
    max_window_area: Optional[float] = None,
    substeps: int = 15,
) -> float:
    """
    Evaluates one candidate shelter configuration against physical objectives.
    Returns a unified discomfort / penalty score to minimize.
    """
    is_temp = str(home_type).lower().startswith("temp")

    # 1. Insulation Thickness Candidate
    max_ins = min(0.12 if is_temp else 0.25, max_insulation_m)
    insulation_thickness = trial.suggest_float("insulation_thickness_m", 0.0, max_ins, step=0.005)

    # 2. Window Area Candidate (within physical wall area constraints)
    total_wall_area = 2.0 * (length + width) * height
    upper_win_limit = min(12.0, total_wall_area * 0.40)
    if max_window_area is not None:
        upper_win_limit = min(upper_win_limit, max_window_area)
    upper_win_limit = max(1.0, upper_win_limit)

    window_area = trial.suggest_float("window_area_m2", 0.5, round(upper_win_limit, 1), step=0.1)

    # 3. Wall Material Candidate by Shelter Permanence
    if wall_material and wall_material != "auto":
        wall_mat_choice = wall_material
    else:
        if is_temp:
            # Temporary: lightweight prefab, PUF panels, timber
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
    else:
        glaze_choice = trial.suggest_categorical(
            "glazing", ["single_clear", "double_clear", "double_low_e", "triple_low_e"]
        )

    # 5. Orientation Candidate
    if orientation and orientation != "auto":
        orient_choice = orientation
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
        hours_to_simulate=168,
        substeps=substeps,
    )

    if "error" in sim_result:
        raise ValueError(sim_result["error"])

    discomfort_dh = sim_result["comfort_metrics"]["discomfort_dh"]
    total_loss_kwh = sim_result["total_heat_loss_kwh"]

    # 7. Permanence-Specific Penalty / Objective Formulation
    # Score to minimize
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


def run_optimization(
    city: str,
    home_type: str = "Permanent",
    length: float = 4.0,
    width: float = 3.0,
    height: float = 2.8,
    wall_material: Optional[str] = None,
    glazing: Optional[str] = None,
    orientation: Optional[str] = None,
    occupants: int = 2,
    max_insulation_m: float = 0.20,
    max_window_area: Optional[float] = None,
    n_trials: int = 40,
) -> Dict[str, Any]:
    """
    Runs Optuna TPE optimization across design parameters and returns
    both the optimal configuration and a ranked list of candidate designs.

    Returns:
        dict containing:
          - 'city', 'home_type'
          - 'insulation_thickness_m', 'insulation_mm'
          - 'window_area_m2', 'wall_material', 'glazing', 'glazing_name', 'orientation'
          - 'discomfort_score'
          - 'simulation_result'
          - 'ranked_designs': List of top 3 distinct candidate designs with scores
    """
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    weather = get_climate_data(city)
    if "error" in weather:
        raise ValueError(weather["error"])

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42)
    )
    study.optimize(
        lambda trial: _objective(
            trial=trial,
            city=city,
            home_type=home_type,
            length=length,
            width=width,
            height=height,
            wall_material=wall_material,
            glazing=glazing,
            orientation=orientation,
            occupants=occupants,
            max_insulation_m=max_insulation_m,
            max_window_area=max_window_area,
            substeps=15,
        ),
        n_trials=n_trials,
    )

    best_p = study.best_params
    best_ins = round(float(best_p.get("insulation_thickness_m", 0.05)), 3)
    best_win = round(float(best_p.get("window_area_m2", 2.0)), 2)
    best_mat = str(best_p.get("wall_material", wall_material if wall_material and wall_material != "auto" else "brick"))
    best_glaze = str(best_p.get("glazing", glazing if glazing and glazing != "auto" else "double_clear"))
    best_orient = str(best_p.get("orientation", orientation if orientation and orientation != "auto" else "south"))
    best_score = round(float(study.best_value), 2)

    # Run final authoritative simulation with the best design
    best_sim = run_simulation(
        city=city,
        length=length,
        width=width,
        height=height,
        wall_material=best_mat,
        insulation_thickness_m=best_ins,
        window_area=best_win,
        glazing=best_glaze,
        orientation=best_orient,
        occupants=occupants,
        hours_to_simulate=168,
    )

    glaze_name = GLAZING_PROPERTIES.get(best_glaze, {}).get("name", best_glaze)

    # Compile Ranked Candidate Designs from Completed Trials
    completed_trials = [t for t in study.trials if t.value is not None and t.state.name == "COMPLETE"]
    completed_trials.sort(key=lambda t: t.value)

    ranked_designs = []
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
            city=city,
            length=length,
            width=width,
            height=height,
            wall_material=c_mat,
            insulation_thickness_m=c_ins,
            window_area=c_win,
            glazing=c_glaze,
            orientation=c_orient,
            occupants=occupants,
            hours_to_simulate=168,
        )
        if "error" in c_sim:
            continue

        c_glaze_name = GLAZING_PROPERTIES.get(c_glaze, {}).get("name", c_glaze)
        
        # Calculate sub-scores (0 - 100 scale)
        comfort_pct = c_sim["comfort_percentage"]
        discomfort_dh = c_sim["discomfort_degree_hours"]
        heat_loss = c_sim["total_heat_loss_kwh"]
        solar_gain = c_sim["integrated_solar_energy_kwh"]

        comfort_score = max(0.0, min(100.0, 100.0 - (discomfort_dh / 15.0)))
        efficiency_score = max(0.0, min(100.0, 100.0 - (heat_loss / 10.0)))
        solar_score = min(100.0, solar_gain * 2.0)
        overall_score = round(0.50 * comfort_score + 0.35 * efficiency_score + 0.15 * solar_score, 1)

        design_label = f"Design #{len(ranked_designs) + 1}"
        if len(ranked_designs) == 0:
            rationale = "Optimal Multi-Criteria Balance (Highest Comfort & Envelope Retention)"
        elif len(ranked_designs) == 1:
            rationale = "High Thermal Efficiency Alternative"
        else:
            rationale = "Balanced Alternative Configuration"

        ranked_designs.append({
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
        })

        if len(ranked_designs) >= 3:
            break

    return {
        "city": city,
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