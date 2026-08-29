import optuna
from climate_service import get_climate_data

# Suppress Optuna's default verbose logging to keep the terminal clean
optuna.logging.set_verbosity(optuna.logging.WARNING)

def objective(trial):
    """
    This function represents ONE design trial. Optuna will call this 100 times.
    """
    # 1. AI Suggests Design Parameters
    insulation_thickness = trial.suggest_float("insulation_thickness_m", 0.02, 0.25)
    window_area = trial.suggest_float("window_area_m2", 0.5, 10.0)
    
    # 2. Fetch Leh Weather (First 168 hours = 1 Winter Week)
    weather = get_climate_data("leh")
    outdoor_temps = weather['hourly_temperature'][:168]
    solar_rad = [d + s for d, s in zip(weather['hourly_direct_solar'][:168], weather['hourly_diffuse_solar'][:168])]
    
    # 3. Physics Constants (PUF Insulation k=0.025, Glass k=1.0)
    U_wall = 0.025 / insulation_thickness
    U_glass = 1.0 / 0.006 # 6mm single glass
    U_roof = 0.025 / 0.15 # 15cm roof insulation
    
    length, width, height = 4.0, 3.0, 2.8
    volume = length * width * height
    total_wall_area = 2*(length*height) + 2*(width*height)
    solid_wall_area = max(0, total_wall_area - window_area)
    roof_area = length * width
    
    # Thermal Mass
    total_thermal_mass = volume * 1.2 * 1005 * 3.0 
    
    T_in = 15.0 # Start temperature
    discomfort = 0.0 # The score we want to minimize
    
    # 4. Run the Physics Loop
    for hour in range(168):
        T_out = outdoor_temps[hour]
        Q_solar = solar_rad[hour] * window_area * 0.8 # 0.8 SHGC
        Q_internal = 200 # People + lights
        
        Q_walls = U_wall * solid_wall_area * (T_in - T_out)
        Q_roof = U_roof * roof_area * (T_in - T_out)
        Q_windows = U_glass * window_area * (T_in - T_out)
        Q_vent = 0.33 * volume * 0.5 * (T_in - T_out) # 0.5 ACH
        
        Q_net = (Q_solar + Q_internal) - (Q_walls + Q_roof + Q_windows + Q_vent)
        delta_T = (Q_net / total_thermal_mass) * 3600
        T_in += delta_T
        
        # 5. Calculate Discomfort Penalty (Target: 15C to 25C)
        if T_in < 15.0:
            discomfort += (15.0 - T_in) # Penalty for being too cold
        elif T_in > 25.0:
            discomfort += (T_in - 25.0) # Penalty for being too hot
            
    return discomfort # Optuna wants to make this number as close to 0 as possible

if __name__ == "__main__":
    print("🧠 Starting AI Optimization for Leh Shelter...")
    print("Testing 100 different designs...\n")
    
    # Create the AI study (TPE is a Bayesian sampler - sounds fancy for judges!)
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler())
    study.optimize(objective, n_trials=100)
    
    print("\n" + "="*40)
    print("🏆 OPTIMIZATION COMPLETE 🏆")
    print("="*40)
    print(f"Best Discomfort Score: {study.best_value:.2f} degree-hours")
    print("\n👉 RECOMMENDED DESIGN FOR LEH:")
    print(f" - Insulation Thickness: {study.best_params['insulation_thickness_m']:.3f} meters ({study.best_params['insulation_thickness_m']*1000:.0f} mm)")
    print(f" - Window Area:          {study.best_params['window_area_m2']:.2f} m²")