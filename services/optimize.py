import os
import sys
from typing import Any, Dict, List, Optional

# Ensure services directory is discoverable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from simulation_service import run_simulation, GLAZING_PROPERTIES, ORIENTATION_FACTORS
from climate_service import get_climate_data


def _objective(
    trial: Any,
    city: str,
    length: float = 4.0,
    width: float = 3.0,
    height: float = 2.8,
    wall_material: Optional[str] = None,
    glazing: Optional[str] = None,
    orientation: Optional[str] = None,
    occupants: int = 2,
    substeps: int = 15,
) -> float:
    """
    Evaluates one candidate design combination using the authoritative simulation_service.
    """
    # 1. Parameter candidate suggestions
    insulation_thickness = trial.suggest_float("insulation_thickness_m", 0.0, 0.25, step=0.005)

    # Max reasonable window area (up to 40% of total wall area)
    total_wall_area = 2.0 * (length + width) * height
    max_win = min(12.0, total_wall_area * 0.40)
    window_area = trial.suggest_float("window_area_m2", 0.5, round(max_win, 1), step=0.1)

    # Wall Material
    if wall_material and wall_material != "auto":
        wall_mat_choice = wall_material
    else:
        wall_mat_choice = trial.suggest_categorical("wall_material", ["brick", "concrete", "puf_insulation"])

    # Glazing
    if glazing and glazing != "auto":
        glaze_choice = glazing
    else:
        glaze_choice = trial.suggest_categorical(
            "glazing", ["single_clear", "double_clear", "double_low_e", "triple_low_e"]
        )

    # Orientation
    if orientation and orientation != "auto":
        orient_choice = orientation
    else:
        orient_choice = trial.suggest_categorical("orientation", ["south", "north", "east", "west"])

    # 2. Run authoritative simulation
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

    # 3. Discomfort score to minimize
    discomfort = sim_result["comfort_metrics"]["discomfort_dh"]
    return float(discomfort)


def run_optimization(
    city: str,
    length: float = 4.0,
    width: float = 3.0,
    height: float = 2.8,
    wall_material: Optional[str] = None,
    glazing: Optional[str] = None,
    orientation: Optional[str] = None,
    occupants: int = 2,
    n_trials: int = 40,
) -> Dict[str, Any]:
    """
    Runs Optuna TPE optimization across design parameters:
      - insulation thickness (m)
      - window area (m²)
      - wall material
      - glazing spec
      - solar orientation

    Returns:
        dict containing best parameters, discomfort score, and full verification simulation.
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
            length=length,
            width=width,
            height=height,
            wall_material=wall_material,
            glazing=glazing,
            orientation=orientation,
            occupants=occupants,
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

    # Run final authoritative simulation with the best candidate design
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

    return {
        "city": city,
        "insulation_thickness_m": best_ins,
        "insulation_mm": round(best_ins * 1000.0, 1),
        "window_area_m2": best_win,
        "wall_material": best_mat,
        "glazing": best_glaze,
        "glazing_name": glaze_name,
        "orientation": best_orient,
        "discomfort_score": best_score,
        "simulation_result": best_sim,
    }


if __name__ == "__main__":
    test_city = "leh"
    print(f"🧠 Running optimization for {test_city.upper()} (40 trials)...")
    res = run_optimization(test_city, n_trials=40)
    print(f"Optimal Insulation: {res['insulation_mm']} mm")
    print(f"Optimal Window Area: {res['window_area_m2']:.2f} m²")
    print(f"Optimal Material: {res['wall_material']}")
    print(f"Optimal Glazing: {res['glazing_name']}")
    print(f"Optimal Orientation: {res['orientation'].title()}")
    print(f"Discomfort Score: {res['discomfort_score']:.2f} degree-hours")
