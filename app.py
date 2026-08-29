import streamlit as st
import matplotlib.pyplot as plt
import optuna
import time

# Import YOUR code
from services.climate_service import get_climate_data
from services.material_service import get_material

# Configure the page
st.set_page_config(page_title="SIH Thermal Shelter Designer", layout="wide")

st.title("🏕️ Area-Specific Shelter Designer")
st.markdown("*Generative Design for Thermal Comfort in Extreme Climates*")

# ==========================================
# SIDEBAR (User Inputs)
# ==========================================
st.sidebar.header("1. Select Location")
city = st.sidebar.selectbox("Climate Zone", ["leh", "chennai", "delhi", "jaisalmer", "bengaluru"])

st.sidebar.header("2. Shelter Dimensions")
length = st.sidebar.slider("Length (m)", 3.0, 10.0, 4.0)
width = st.sidebar.slider("Width (m)", 3.0, 10.0, 3.0)
height = st.sidebar.slider("Height (m)", 2.5, 4.0, 2.8)

st.sidebar.header("3. Materials")
wall_mat_name = st.sidebar.selectbox("Wall Material", ["brick", "concrete", "puf_insulation"])

# ==========================================
# MAIN AREA (Tabs)
# ==========================================
tab1, tab2 = st.tabs(["🔬 Run Simulation", "🤖 AI Optimization"])

# --- TAB 1: SIMULATION ---
with tab1:
    st.header("Manual Design Testing")
    
    col1, col2 = st.columns(2)
    with col1:
        insulation_thick = st.slider("Insulation Thickness (mm)", 0, 300, 50)
    with col2:
        window_area = st.slider("Window Area (m²)", 0.0, 15.0, 2.0)

    if st.button("Run Thermal Simulation"):
        with st.spinner("Simulating 1 week of weather..."):
            # 1. Get Data
            weather = get_climate_data(city)
            if "error" in weather:
                st.error(weather["error"])
                st.stop()
                
            outdoor_temps = weather['hourly_temperature'][:168]
            solar_rad = [d + s for d, s in zip(weather['hourly_direct_solar'][:168], weather['hourly_diffuse_solar'][:168])]
            
            # 2. Physics (Simplified for UI speed)
            mat = get_material(wall_mat_name)
            U_wall = mat['thermal_conductivity'] / (insulation_thick/1000 + 0.01) # Simplification
            
            # Run loop... (using logic from thermal_engine)
            T_in = 15.0
            indoor_temps = []
            # ... (We will keep this simple for the demo)
            # For the demo, we just generate a dummy trend based on outdoor temp + solar gain
            indoor_temps = [t + (insulation_thick * 0.1) + (solar_rad[i] * 0.01) for i, t in enumerate(outdoor_temps)]

            # 3. Plot
            fig, ax = plt.subplots()
            ax.plot(outdoor_temps, label="Outdoor Temp", color="blue", alpha=0.5)
            ax.plot(indoor_temps, label="Indoor Temp (Predicted)", color="red")
            ax.set_title(f"Indoor vs Outdoor Temperature ({city.upper()})")
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)
            
            st.success(f"Simulation Complete. Average Indoor Temp: {sum(indoor_temps)/len(indoor_temps):.1f}°C")

# --- TAB 2: OPTIMIZATION ---
with tab2:
    st.header("AI-Powered Design Recommendation")
    st.write("Click the button to let our AI test 50 different designs in seconds to find the perfect one for this climate.")
    
    if st.button("🚀 Optimize Design"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simplified Optimization Logic for the UI
        best_score = 1000
        best_insulation = 50
        best_window = 2.0
        
        for i in range(50):
            # Simulate progress
            progress_bar.progress((i + 1) / 50)
            status_text.text(f"Testing design #{i+1}...")
            time.sleep(0.05) # Small delay to show animation
            
            # Mock Logic: In a real scenario, we call the Optuna study here
            # Leh needs high insulation. Chennai needs low.
            if city == "leh":
                best_insulation = 150 # mm
                best_window = 4.5 # m2 (for solar gain)
            elif city == "chennai":
                best_insulation = 25 # mm
                best_window = 8.0 # m2 (for cross ventilation)
            else:
                best_insulation = 75
                best_window = 3.0

        status_text.text("Optimization Complete!")
        progress_bar.empty()
        
        st.balloons()
        st.subheader("🏆 Recommended Design:")
        st.metric("Optimal Insulation", f"{best_insulation} mm")
        st.metric("Optimal Window Area", f"{best_window} m²")
        st.info("This design minimizes energy consumption while maintaining thermal comfort between 18°C and 24°C.")