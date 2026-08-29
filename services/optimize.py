import os
import sys
import optuna

# Ensure services directory is discoverable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from services.climate_service import get_climate_data
except ImportError:
    from climate_service import get_climate_data

# Suppress Optuna's default verbose logging to keep terminal and UI clean
optuna.logging.set_verbosity(optuna.logging.WARNING)

def _objective(trial, city: str, substeps: int = 60):
    """
    Evaluates one design trial for a specific climate zone using a numerically
    stable sub-hour explicit time-stepping scheme.
    """
    # 1. AI Suggests Design Parameters
    insulation_thickness = trial.suggest_float("insulation_thickness_m", 0.02, 0.25)
    window_area = trial.suggest_float("window_area_m2", 0.5, 10.0)
    
    # 2. Fetch Weather (First 168 hours = 1 Week)
    weather = get_climate_data(city)
    if "error" in weather:
        raise ValueError(weather["error"])
        
    outdoor_temps = weather['hourly_temperature'][:168]
    solar_rad = [d + s for d, s in zip(weather['hourly_direct_solar'][:168], weather['hourly_diffuse_solar'][:168])]
    
    # 3. Physics Constants (PUF Insulation k=0.025, Glass k=1.0)
    U_wall = 0.025 / insulation_thickness
    U_glass = 1.0 / 0.006  # 6mm single glass
    U_roof = 0.025 / 0.15  # 15cm roof insulation
    
    length, width, height = 4.0, 3.0, 2.8
    volume = length * width * height
    total_wall_area = 2 * (length * height) + 2 * (width * height)
    solid_wall_area = max(0.0, total_wall_area - window_area)
    roof_area = length * width
    
    # Thermal Mass
    total_thermal_mass = volume * 1.2 * 1005 * 3.0 
    
    dt = 3600.0 / substeps  # Time step in seconds (60 seconds per sub-step)
    
    T_in = 20.0  # Start temperature
    discomfort = 0.0  # The score to minimize (degree-hours)
    
    # 4. Run Stable Physics Loop
    for hour in range(168):
        T_out = outdoor_temps[hour]
        solar_radiation = solar_rad[hour]
        
        for _ in range(substeps):
            Q_solar = solar_radiation * window_area * 0.8  # 0.8 SHGC
            Q_internal = 200  # People + lights (Watts)
            
            Q_walls = U_wall * solid_wall_area * (T_in - T_out)
            Q_roof = U_roof * roof_area * (T_in - T_out)
            Q_windows = U_glass * window_area * (T_in - T_out)
            Q_vent = 0.33 * volume * 0.5 * (T_in - T_out)  # 0.5 ACH
            
            Q_net = (Q_solar + Q_internal) - (Q_walls + Q_roof + Q_windows + Q_vent)
            delta_T = (Q_net / total_thermal_mass) * dt
            T_in += delta_T
        
        # 5. Calculate Discomfort Penalty per hour (Target: 18°C to 24°C)
        if T_in < 18.0:
            discomfort += (18.0 - T_in)
        elif T_in > 24.0:
            discomfort += (T_in - 24.0)
            
    return discomfort


def run_optimization(city: str, n_trials: int = 50) -> dict:
    """
    Runs Optuna optimization for a shelter in the given city.
    
    Returns:
        dict: {
            "insulation_thickness_m": float,
            "window_area_m2": float,
            "discomfort_score": float
        }
    """
    weather = get_climate_data(city)
    if "error" in weather:
        raise ValueError(weather["error"])
        
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(lambda trial: _objective(trial, city, substeps=60), n_trials=n_trials)
    
    return {
        "insulation_thickness_m": round(float(study.best_params["insulation_thickness_m"]), 3),
        "window_area_m2": round(float(study.best_params["window_area_m2"]), 2),
        "discomfort_score": round(float(study.best_value), 2)
    }


if __name__ == "__main__":
    test_city = "chennai"
    print(f"🧠 Running optimization for {test_city.upper()} (50 trials)...")
    res = run_optimization(test_city, n_trials=50)
    print(f"Optimal Insulation: {res['insulation_thickness_m'] * 1000:.0f} mm")
    print(f"Optimal Window Area: {res['window_area_m2']:.2f} m²")
    print(f"Discomfort Score: {res['discomfort_score']:.2f} degree-hours")