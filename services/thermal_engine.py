import os
import matplotlib.pyplot as plt
from climate_service import get_climate_data
from material_service import get_material

def simulate_shelter(city, length, width, height, wall_material_name, window_area):
    """
    Calculates the indoor temperature of a shelter hour-by-hour.
    """
    # 1. Fetch Data
    weather = get_climate_data(city)
    if "error" in weather:
        return weather
        
    wall_mat = get_material(wall_material_name)
    if "error" in wall_mat:
        return wall_mat

    # 2. Define Geometry & Constants
    volume = length * width * height
    roof_area = length * width
    floor_area = length * width
    total_wall_area = 2 * (length * height) + 2 * (width * height)
    
    # Subtract window area from solid wall area
    solid_wall_area = total_wall_area - window_area
    if solid_wall_area < 0: solid_wall_area = 0

    # 3. Calculate U-Values (Heat Transfer Coefficients)
    # U = k / thickness (Assuming 0.2m wall thickness, 0.05m insulation, 0.15m roof)
    wall_thickness = 0.23  # meters (standard brick wall)
    roof_thickness = 0.15  
    glass_thickness = 0.006 # 6mm glass
    
    U_wall = wall_mat['thermal_conductivity'] / wall_thickness
    U_roof = 0.5 / roof_thickness # Assuming standard concrete roof
    U_glass = 1.0 / glass_thickness # Single pane glass
    
    # 4. Calculate Thermal Mass (Capacitance)
    # Heat capacity of the air inside + the floor/furniture (simplified)
    air_density = 1.2 # kg/m3
    air_specific_heat = 1005 # J/kgK
    air_mass = volume * air_density
    
    # Add thermal mass of the floor and interior (simplified as 2x air mass for stability)
    total_thermal_mass = (air_mass * air_specific_heat) * 3.0 

    # 5. Run the 8760 Hour Simulation
    indoor_temps = []
    T_in = 20.0 # Starting temperature (20 C)
    
    # We only simulate the first 168 hours (1 week) for a fast visual graph
    hours_to_simulate = 168 
    
    for hour in range(hours_to_simulate):
        T_out = weather['hourly_temperature'][hour]
        solar_radiation = weather['hourly_direct_solar'][hour] + weather['hourly_diffuse_solar'][hour]
        
        # HEAT GAINS (Watts)
        # Solar heat coming through windows (SHGC = 0.8 for standard glass)
        Q_solar = solar_radiation * window_area * 0.8 
        
        # Internal heat from 2 people + lights (approx 200 Watts)
        Q_internal = 200 
        
        # HEAT LOSSES (Watts)
        # Q = U * Area * (T_in - T_out)
        Q_walls = U_wall * solid_wall_area * (T_in - T_out)
        Q_roof = U_roof * roof_area * (T_in - T_out)
        Q_windows = U_glass * window_area * (T_in - T_out)
        
        # Ventilation/Infiltration losses (Air leaking out)
        # Formula: 0.33 * Volume * AirChangesPerHour * (T_in - T_out)
        ACH = 0.5 # 0.5 air changes per hour (standard shelter)
        Q_vent = 0.33 * volume * ACH * (T_in - T_out)
        
        # TOTAL NET HEAT FLOW
        Q_net = (Q_solar + Q_internal) - (Q_walls + Q_roof + Q_windows + Q_vent)
        
        # UPDATE TEMPERATURE
        # Delta T = Q_net / Thermal Mass (converted for 1 hour = 3600 seconds)
        delta_T = (Q_net / total_thermal_mass) * 3600
        T_in = T_in + delta_T
        
        indoor_temps.append(T_in)

    return indoor_temps

# ==========================================
# TEST IT RIGHT NOW
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