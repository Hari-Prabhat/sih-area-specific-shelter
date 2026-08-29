import os
import sys
import matplotlib.pyplot as plt

# Ensure services directory is discoverable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from simulation_service import simulate_shelter as _simulate_shelter
from climate_service import get_climate_data


def simulate_shelter(city, length, width, height, wall_material_name, window_area, insulation_thickness_m=0.0):
    """
    Calculates the indoor temperature of a shelter hour-by-hour.
    Delegates to the authoritative simulation_service.
    """
    return _simulate_shelter(
        city=city,
        length=length,
        width=width,
        height=height,
        wall_material_name=wall_material_name,
        window_area=window_area,
        insulation_thickness_m=insulation_thickness_m,
    )


# ==========================================
# CLI TEST HARNESS
# ==========================================
if __name__ == "__main__":
    print("Simulating a Brick Shelter in Leh during Winter...")
    
    # Simulate a 4m x 3m x 2.8m room with 2 sq meters of window
    indoor_temps = simulate_shelter(
        city="leh", 
        length=4.0, 
        width=3.0, 
        height=2.8, 
        wall_material_name="brick", 
        window_area=2.0
    )
    
    # Get outdoor temps for the same 168 hours to compare
    weather = get_climate_data("leh")
    outdoor_temps = weather['hourly_temperature'][:168]
    
    print(f"Cold outdoor temp: {min(outdoor_temps)} C")
    print(f"Warmest indoor temp: {max(indoor_temps)} C")
    
    # Draw the graph
    plt.figure(figsize=(10, 5))
    plt.plot(outdoor_temps, label="Outdoor (Leh Winter)", color="blue")
    plt.plot(indoor_temps, label="Indoor Shelter Temp", color="red")
    plt.title("Thermal Physics Simulation: Brick Shelter in Leh (1 Week)")
    plt.xlabel("Hours")
    plt.ylabel("Temperature (°C)")
    plt.legend()
    plt.grid(True)
    plt.show()