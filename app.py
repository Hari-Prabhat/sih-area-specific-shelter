import os
import sys
import math
import numpy as np
import streamlit as st
import plotly.graph_objects as go

# ==============================================================================
# PATH SETUP
# ==============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.join(CURRENT_DIR, "services")
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from services.climate_service import get_climate_data
from services.material_service import load_all_materials, get_material
from services.optimize import run_optimization
from services.recommender import (
    get_recommendation,
    auto_size_shelter,
    recommend_materials,
    CLIMATE_MAPPING,
    CLIMATE_DESCRIPTIONS
)

# ==============================================================================
# PAGE CONFIG
# ==============================================================================
st.set_page_config(
    page_title="Area-Specific Shelter Designer | SIH",
    page_icon="🏕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# DARK-THEME-SAFE CSS
# ==============================================================================
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem; font-weight: 700;
        color: #38bdf8; margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem; color: #94a3b8; margin-bottom: 1.5rem;
    }
    .card {
        background-color: #1e293b;
        border-radius: 10px; padding: 18px;
        border-left: 5px solid #38bdf8;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        margin-bottom: 1rem; color: #e2e8f0;
    }
    .card h4 { color: #38bdf8; margin-top:0; margin-bottom:8px; font-size:1.05rem; }
    .card p  { color: #cbd5e1; margin:4px 0; font-size:0.92rem; line-height:1.5; }
    .card b  { color: #f1f5f9; }
    .metric-badge { font-weight:700; color:#22d3ee; font-size:1.15rem; }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# STABLE SIMULATION WRAPPER
# ==============================================================================
# thermal_engine.py uses an explicit-Euler scheme with dt=3600 s and
# U_glass = 1.0/0.006 ≈ 167 W/m²K. For ANY realistic shelter geometry the
# CFL-like stability condition is violated and temperatures explode to ±10^87.
# We CANNOT modify thermal_engine.py, so we re-implement identical physics here
# with SUB-HOUR time-stepping (dt = 60 s → 60 sub-steps per hour) to keep the
# numbers stable.  Every formula below is a line-for-line copy of thermal_engine.
# ==============================================================================
def simulate_shelter_stable(city, length, width, height,
                            wall_material_name, window_area,
                            substeps=60):
    """
    Same physics as services/thermal_engine.simulate_shelter but numerically
    stable thanks to sub-hour time-stepping.
    """
    weather = get_climate_data(city)
    if "error" in weather:
        return weather

    wall_mat = get_material(wall_material_name)
    if "error" in wall_mat:
        return wall_mat

    # Geometry
    volume = length * width * height
    roof_area = length * width
    total_wall_area = 2 * (length * height) + 2 * (width * height)
    solid_wall_area = max(0.0, total_wall_area - window_area)

    # U-values (identical to thermal_engine.py)
    wall_thickness = 0.23
    roof_thickness = 0.15
    glass_thickness = 0.006

    U_wall  = wall_mat['thermal_conductivity'] / wall_thickness
    U_roof  = 0.5 / roof_thickness
    U_glass = 1.0 / glass_thickness

    # Thermal mass (identical)
    air_density = 1.2
    air_specific_heat = 1005
    air_mass = volume * air_density
    total_thermal_mass = (air_mass * air_specific_heat) * 3.0

    dt = 3600.0 / substeps          # seconds per sub-step

    T_in = 20.0
    indoor_temps = []
    hours_to_simulate = 168

    for hour in range(hours_to_simulate):
        T_out = weather['hourly_temperature'][hour]
        solar_radiation = (weather['hourly_direct_solar'][hour]
                           + weather['hourly_diffuse_solar'][hour])

        for _ in range(substeps):
            Q_solar    = solar_radiation * window_area * 0.8
            Q_internal = 200
            Q_walls    = U_wall  * solid_wall_area * (T_in - T_out)
            Q_roof     = U_roof  * roof_area       * (T_in - T_out)
            Q_windows  = U_glass * window_area     * (T_in - T_out)
            Q_vent     = 0.33 * volume * 0.5       * (T_in - T_out)

            Q_net   = (Q_solar + Q_internal) - (Q_walls + Q_roof + Q_windows + Q_vent)
            delta_T = (Q_net / total_thermal_mass) * dt
            T_in   += delta_T

        indoor_temps.append(round(float(T_in), 4))

    return indoor_temps


# ==============================================================================
# HELPERS
# ==============================================================================
def calculate_comfort_metrics(indoor_temps):
    """Stats against 18–24 °C comfort band, all values rounded to 2 dp."""
    if not indoor_temps:
        return {"avg":0.0, "min_t":0.0, "max_t":0.0,
                "comfort_pct":0.0, "discomfort_dh":0.0}

    avg_t = round(float(np.mean(indoor_temps)), 2)
    min_t = round(float(np.min(indoor_temps)),  2)
    max_t = round(float(np.max(indoor_temps)),  2)

    in_comfort  = sum(1 for t in indoor_temps if 18.0 <= t <= 24.0)
    comfort_pct = round((in_comfort / len(indoor_temps)) * 100.0, 2)

    dh = 0.0
    for t in indoor_temps:
        if t < 18.0:
            dh += (18.0 - t)
        elif t > 24.0:
            dh += (t - 24.0)

    return {"avg": avg_t, "min_t": min_t, "max_t": max_t,
            "comfort_pct": comfort_pct, "discomfort_dh": round(float(dh), 2)}


def plot_temperature_curves(city, outdoor_temps, indoor_temps, title_suffix=""):
    hours = list(range(len(indoor_temps)))
    fig = go.Figure()

    fig.add_hrect(y0=18.0, y1=24.0,
        fillcolor="rgba(46,204,113,0.15)", layer="below",
        line=dict(color="rgba(46,204,113,0.5)", width=1, dash="dash"),
        annotation_text="Comfort Zone (18–24 °C)",
        annotation_position="top left",
        annotation=dict(font_size=11, font_color="#27ae60"))

    fig.add_trace(go.Scatter(x=hours,
        y=[round(float(t),2) for t in outdoor_temps[:len(indoor_temps)]],
        mode="lines", name="Outdoor Temp (°C)",
        line=dict(color="#3498db", width=2, dash="dot"),
        hovertemplate="Hour %{x}: %{y:.2f} °C<extra>Outdoor</extra>"))

    fig.add_trace(go.Scatter(x=hours, y=indoor_temps,
        mode="lines", name="Indoor Predicted (°C)",
        line=dict(color="#e74c3c", width=3),
        hovertemplate="Hour %{x}: %{y:.2f} °C<extra>Indoor</extra>"))

    fig.update_layout(
        title=f"<b>{city.upper()} — 168-Hour Thermal Simulation {title_suffix}</b>",
        xaxis=dict(title="Time (Hours)", tickmode="array",
            tickvals=[0,24,48,72,96,120,144,168],
            ticktext=["Day 1","Day 2","Day 3","Day 4",
                      "Day 5","Day 6","Day 7","End"],
            showgrid=True, gridcolor="#e9ecef"),
        yaxis=dict(title="Temperature (°C)", showgrid=True,
            gridcolor="#e9ecef", zeroline=True, zerolinecolor="#bdc3c7"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        height=430, margin=dict(l=40,r=30,t=60,b=40))
    return fig


def create_2d_floorplan(length, width, window_area, orientation_advice, climate_type):
    fig = go.Figure()
    wt = 0.22
    fig.add_shape(type="rect", x0=0, y0=0, x1=length, y1=width,
        line=dict(color="#2c3e50", width=4), fillcolor="#e9ecef", layer="below")
    fig.add_shape(type="rect", x0=wt, y0=wt, x1=length-wt, y1=width-wt,
        line=dict(color="#95a5a6", width=1.5, dash="dot"), fillcolor="#ffffff")

    wl = min(length*0.7, max(1.2, window_area/1.3))
    ws = (length - wl) / 2
    fig.add_shape(type="rect", x0=ws, y0=-0.08, x1=ws+wl, y1=wt+0.08,
        line=dict(color="#2980b9", width=2), fillcolor="#3498db")

    dw = 0.9
    fig.add_shape(type="rect", x0=0.3, y0=-0.08, x1=0.3+dw, y1=wt+0.08,
        line=dict(color="#d35400", width=2), fillcolor="#e67e22")

    if climate_type in ("hot_humid", "moderate"):
        fig.add_shape(type="rect", x0=ws+0.3, y0=width-wt-0.08,
            x1=ws+wl-0.3, y1=width+0.08,
            line=dict(color="#2980b9", width=2), fillcolor="#3498db")
        fig.add_annotation(x=length/2, y=width+0.35,
            text="Cross-Vent Window (N)", showarrow=False,
            font=dict(size=10, color="#2980b9"))

    fa = length * width
    fig.add_annotation(x=length/2, y=width/2,
        text=f"<b>Main Space</b><br>{fa:.1f} m² ({length:.1f}×{width:.1f})",
        showarrow=False, font=dict(size=13, color="#2c3e50"))
    fig.add_annotation(x=ws+wl/2, y=-0.35,
        text=f"<b>Glazing ({wl:.1f} m)</b>", showarrow=False,
        font=dict(size=10, color="#2980b9"))
    fig.add_annotation(x=0.3+dw/2, y=-0.35,
        text="<b>Entry (0.9 m)</b>", showarrow=False,
        font=dict(size=10, color="#d35400"))

    cx, cy = length+0.6, width-0.2
    fig.add_annotation(x=cx, y=cy, ax=cx, ay=cy-0.9,
        xref="x", yref="y", axref="x", ayref="y",
        text="<b>N</b>", showarrow=True, arrowhead=2, arrowsize=1.6,
        arrowwidth=3, arrowcolor="#c0392b", font=dict(size=15, color="#c0392b"))

    fig.update_layout(
        title="<b>2D Floor Plan</b>",
        xaxis=dict(range=[-0.8,length+1.4], showgrid=True, zeroline=False,
            title="Length (m)", gridcolor="#ecf0f1"),
        yaxis=dict(range=[-0.8,width+0.8], showgrid=True, zeroline=False,
            title="Width (m)", scaleanchor="x", scaleratio=1, gridcolor="#ecf0f1"),
        plot_bgcolor="#fafafa", paper_bgcolor="#ffffff",
        height=440, margin=dict(l=30,r=30,t=50,b=30))
    return fig


def create_3d_shelter(length, width, height, roof_type, window_area, climate_type):
    fig = go.Figure()
    pad = 1.2
    fig.add_trace(go.Mesh3d(x=[-pad,length+pad,length+pad,-pad],
        y=[-pad,-pad,width+pad,width+pad], z=[-0.02]*4,
        i=[0,0], j=[1,2], k=[2,3],
        color="#d5dbdb", opacity=0.7, name="Ground", showlegend=True))

    vx=[0,length,length,0,0,length,length,0]
    vy=[0,0,width,width,0,0,width,width]
    vz=[0,0,0,0,height,height,height,height]
    wi=[0,0,1,1,2,2,3,3]; wj=[1,5,2,6,3,7,0,4]; wk=[5,4,6,5,7,6,4,7]
    wc="#e8dfd8" if climate_type=="cold" else "#f2e9e4"
    fig.add_trace(go.Mesh3d(x=vx,y=vy,z=vz,i=wi,j=wj,k=wk,
        color=wc, opacity=0.92, name="Walls", flatshading=True, showlegend=True))

    if roof_type == "pitched":
        rh = height + 1.2
        rx=vx+[0,length]; ry=vy+[width/2,width/2]; rz=vz+[rh,rh]
        ri=[4,5,4,4,7,7]; rj=[7,6,5,9,6,9]; rk=[8,9,9,8,9,8]
        fig.add_trace(go.Mesh3d(x=rx,y=ry,z=rz,i=ri,j=rj,k=rk,
            color="#7f8c8d", opacity=0.95, name="Pitched Roof",
            flatshading=True, showlegend=True))
    else:
        fig.add_trace(go.Mesh3d(x=[0,length,length,0],y=[0,0,width,width],
            z=[height]*4, i=[0,0], j=[1,2], k=[2,3],
            color="#95a5a6", opacity=0.95, name="Flat Roof",
            flatshading=True, showlegend=True))

    ww=min(length*0.65,max(1.2,window_area/1.3))
    wh=min(height*0.55,max(1.0,window_area/ww))
    wx1=(length-ww)/2; wx2=wx1+ww
    wz1=0.85; wz2=min(height-0.2, wz1+wh)
    fig.add_trace(go.Mesh3d(x=[wx1,wx2,wx2,wx1],y=[-0.02]*4,
        z=[wz1,wz1,wz2,wz2], i=[0,0], j=[1,2], k=[2,3],
        color="#2980b9", opacity=0.85, name="Glazing", showlegend=True))

    fig.add_trace(go.Mesh3d(x=[0.3,1.2,1.2,0.3],y=[-0.02]*4,
        z=[0,0,2.05,2.05], i=[0,0], j=[1,2], k=[2,3],
        color="#d35400", opacity=0.95, name="Door", showlegend=True))

    fig.update_layout(
        title=f"<b>3D Shelter ({roof_type.title()} Roof)</b>",
        scene=dict(
            xaxis=dict(title="L (m)", showbackground=False),
            yaxis=dict(title="W (m)", showbackground=False),
            zaxis=dict(title="H (m)", showbackground=False),
            aspectmode="data",
            camera=dict(eye=dict(x=-1.55,y=-1.85,z=1.25),
                        center=dict(x=0,y=0,z=-0.1))),
        legend=dict(orientation="h", yanchor="bottom", y=0.98, xanchor="right", x=1),
        margin=dict(l=0,r=0,t=40,b=0), height=460)
    return fig


# ==============================================================================
# HEADER
# ==============================================================================
st.markdown('<div class="main-title">🏕️ Area-Specific Shelter Designer</div>',
            unsafe_allow_html=True)
st.markdown('<div class="sub-title"><i>Generative AI & Building Physics for '
            'Climate-Resilient Thermal Comfort</i></div>',
            unsafe_allow_html=True)

app_mode = st.radio("Select Interface Mode:",
                     ["👤 Simple Mode", "🛠️ Advanced Mode"],
                     horizontal=True)
st.markdown("---")


# ==============================================================================
# 👤 SIMPLE MODE
# ==============================================================================
if app_mode == "👤 Simple Mode":
    st.subheader("📋 Shelter Requirements")
    c1, c2, c3 = st.columns(3)
    with c1:
        city_s = st.selectbox("1. Location",
            ["leh","chennai","delhi","jaisalmer","bengaluru"],
            format_func=lambda x: {"leh":"🏔️ Leh (Cold)",
                "chennai":"🌊 Chennai (Humid)","delhi":"🏙️ Delhi (Composite)",
                "jaisalmer":"🏜️ Jaisalmer (Hot-Dry)",
                "bengaluru":"🌳 Bengaluru (Moderate)"}[x])
    with c2:
        people = st.slider("2. Occupants", 1, 10, 4)
    with c3:
        home_type = st.radio("3. Permanence", ["Temporary","Permanent"],
                             horizontal=True)

    if st.button("✨ Generate Climate-Optimized Design",
                 type="primary", use_container_width=True):
        with st.spinner(f"Running Bayesian optimization for {city_s.upper()}…"):
            rec = get_recommendation(city=city_s, people=people,
                                     home_type=home_type, n_trials=40)
            weather = get_climate_data(city_s)
            if "error" in weather:
                st.error(weather["error"]); st.stop()

            geo  = rec["geometry"]
            mats = rec["materials"]

            indoor_temps = simulate_shelter_stable(
                city_s, geo["length_m"], geo["width_m"], geo["height_m"],
                mats["wall_material_id"], rec["optimal_window_area_m2"])
            if isinstance(indoor_temps, dict) and "error" in indoor_temps:
                st.error(indoor_temps["error"]); st.stop()

            metrics = calculate_comfort_metrics(indoor_temps)

            st.session_state["s_rec"]     = rec
            st.session_state["s_weather"] = weather
            st.session_state["s_indoor"]  = indoor_temps
            st.session_state["s_metrics"] = metrics

    # ---------- render cached results ----------
    if "s_rec" in st.session_state and st.session_state["s_rec"]["city"]==city_s:
        rec     = st.session_state["s_rec"]
        weather = st.session_state["s_weather"]
        indoor  = st.session_state["s_indoor"]
        met     = st.session_state["s_metrics"]
        geo     = rec["geometry"]
        mats    = rec["materials"]

        st.success(f"✅ Design for **{city_s.upper()}** "
                   f"({rec['climate_name']}) — Discomfort: "
                   f"**{rec['discomfort_score']:.2f} DH**")

        # OUTPUT 1 — Recommendation Cards
        st.markdown("### 🏆 1. Recommended Envelope & Architecture")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown(f"""<div class='card'>
<h4>🧱 Wall Assembly</h4>
<p><b>Material:</b> {mats['wall_material_name']}</p>
<p><b>Thermal Mass:</b> {'High Mass' if home_type=='Permanent' else 'Lightweight Prefab'}</p>
</div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class='card'>
<h4>🏠 Roof System</h4>
<p><b>Design:</b> {mats['roof_material']}</p>
<p><b>Profile:</b> {mats['roof_type'].title()} Roof</p>
</div>""", unsafe_allow_html=True)
        with r2:
            st.markdown(f"""<div class='card'>
<h4>🛡️ Thermal Insulation</h4>
<p><b>Type:</b> {mats['insulation_type']}</p>
<p><b>Optimal Thickness:</b> <span class='metric-badge'>{rec['optimal_insulation_mm']:.2f} mm</span></p>
</div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class='card'>
<h4>🪟 Fenestration & Glazing</h4>
<p><b>Spec:</b> {mats['glazing_type']}</p>
<p><b>Window Area:</b> <span class='metric-badge'>{rec['optimal_window_area_m2']:.2f} m²</span></p>
</div>""", unsafe_allow_html=True)
        with r3:
            st.markdown(f"""<div class='card'>
<h4>🧭 Orientation & Passive Solar</h4>
<p><b>Orientation:</b> {mats['orientation_advice']}</p>
<p><b>Shading:</b> {mats['shading_advice']}</p>
</div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class='card'>
<h4>📐 Auto-Sizing Summary</h4>
<p><b>Floor:</b> {geo['floor_area_m2']:.2f} m² ({geo['length_m']:.2f} × {geo['width_m']:.2f})</p>
<p><b>Height:</b> {geo['height_m']:.2f} m &nbsp;|&nbsp; <b>Vol:</b> {geo['volume_m3']:.2f} m³</p>
</div>""", unsafe_allow_html=True)

        st.markdown("---")

        # OUTPUT 2 — Temperature Graph
        st.markdown("### 📈 2. Thermal Simulation (168 h / 1 Week)")
        st.plotly_chart(plot_temperature_curves(
            city_s, weather["hourly_temperature"], indoor,
            f"— {home_type} Shelter"), use_container_width=True)

        # OUTPUT 3 — Comfort Metrics
        st.markdown("### 📊 3. Thermal Comfort Indicators")
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        mc1.metric("Avg Indoor Temp",        f"{met['avg']:.2f} °C")
        mc2.metric("Min Indoor Temp",        f"{met['min_t']:.2f} °C")
        mc3.metric("Max Indoor Temp",        f"{met['max_t']:.2f} °C")
        mc4.metric("Comfort % (18–24 °C)",   f"{met['comfort_pct']:.2f} %")
        mc5.metric("Discomfort DH",          f"{met['discomfort_dh']:.2f} °C·h")
        st.markdown("---")

        # OUTPUT 4 & 5 — 2D Plan + 3D Model
        st.markdown("### 🏗️ 4 & 5. Floor Plan & 3D Model")
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(create_2d_floorplan(
                geo["length_m"], geo["width_m"],
                rec["optimal_window_area_m2"],
                mats["orientation_advice"], rec["climate_type"]),
                use_container_width=True)
        with g2:
            st.plotly_chart(create_3d_shelter(
                geo["length_m"], geo["width_m"], geo["height_m"],
                mats["roof_type"], rec["optimal_window_area_m2"],
                rec["climate_type"]), use_container_width=True)
        st.markdown("---")

        # OUTPUT 6 — Rationale
        st.markdown("### 💡 6. Design Rationale")
        st.info(rec["explanation"])


# ==============================================================================
# 🛠️ ADVANCED MODE
# ==============================================================================
else:
    st.subheader("🛠️ Engineering Parameter Control")

    st.sidebar.header("📍 1. Location")
    city_a = st.sidebar.selectbox("Climate Zone",
        ["leh","chennai","delhi","jaisalmer","bengaluru"])

    st.sidebar.header("📐 2. Geometry")
    l_a = st.sidebar.slider("Length (m)", 3.0, 10.0, 4.0, 0.1)
    w_a = st.sidebar.slider("Width (m)",  3.0, 10.0, 3.0, 0.1)
    h_a = st.sidebar.slider("Height (m)", 2.5,  4.0, 2.8, 0.1)
    st.sidebar.caption(f"Floor: **{l_a*w_a:.2f} m²** · Vol: **{l_a*w_a*h_a:.2f} m³**")

    st.sidebar.header("🧱 3. Materials")
    all_mat  = load_all_materials()
    mat_keys = [k for k in all_mat if "error" not in k]
    mat_key  = st.sidebar.selectbox("Wall Material", mat_keys,
        format_func=lambda k: f"{all_mat[k].get('name',k)} "
                              f"(k={all_mat[k].get('thermal_conductivity','-')})")
    ins_mm = st.sidebar.slider("Insulation (mm)", 0, 300, 50, 5)
    win_a  = st.sidebar.slider("Window Area (m²)", 0.0, 15.0, 2.0, 0.2)

    tab_sim, tab_opt = st.tabs(["🔬 Simulation", "🤖 AI Optimization"])

    with tab_sim:
        st.markdown("#### Lumped Thermal Mass Simulation")
        if st.button("🚀 Run Simulation", type="primary"):
            with st.spinner(f"Simulating {city_a.upper()}…"):
                wdata = get_climate_data(city_a)
                if "error" in wdata:
                    st.error(wdata["error"]); st.stop()

                indoor_a = simulate_shelter_stable(
                    city_a, l_a, w_a, h_a, mat_key, win_a)
                if isinstance(indoor_a, dict) and "error" in indoor_a:
                    st.error(indoor_a["error"]); st.stop()

                met_a = calculate_comfort_metrics(indoor_a)

                st.plotly_chart(plot_temperature_curves(
                    city_a, wdata["hourly_temperature"], indoor_a,
                    f"({all_mat[mat_key]['name']})"), use_container_width=True)

                st.markdown("#### 📊 Metrics")
                m1,m2,m3,m4,m5 = st.columns(5)
                m1.metric("Avg Indoor",    f"{met_a['avg']:.2f} °C")
                m2.metric("Min Indoor",    f"{met_a['min_t']:.2f} °C")
                m3.metric("Max Indoor",    f"{met_a['max_t']:.2f} °C")
                m4.metric("Comfort %",     f"{met_a['comfort_pct']:.2f} %")
                m5.metric("Discomfort DH", f"{met_a['discomfort_dh']:.2f} °C·h")

                st.markdown("#### 🏗️ 3D Preview")
                ct = CLIMATE_MAPPING.get(city_a, "composite")
                rt = "pitched" if ct=="cold" else "flat"
                st.plotly_chart(create_3d_shelter(l_a,w_a,h_a,rt,win_a,ct),
                    use_container_width=True)

    with tab_opt:
        st.markdown("#### Bayesian Optimization (Optuna TPE)")
        oc1, oc2 = st.columns(2)
        with oc1:
            trials = st.slider("Trials", 20, 100, 50, 10)
        with oc2:
            ct_a = CLIMATE_MAPPING.get(city_a, "composite")
            st.info(f"Zone: **{city_a.upper()}** "
                    f"({CLIMATE_DESCRIPTIONS.get(ct_a, ct_a)})")

        if st.button("🧠 Execute Optimization"):
            prog = st.progress(0)
            stat = st.empty()
            stat.text("Initializing TPE sampler…"); prog.progress(25)
            try:
                res = run_optimization(city_a, n_trials=trials)
                prog.progress(100); stat.text("Converged!")

                st.subheader(f"🏆 Optimal for {city_a.upper()}")
                rc1,rc2,rc3 = st.columns(3)
                rc1.metric("Insulation",
                           f"{res['insulation_thickness_m']*1000:.2f} mm")
                rc2.metric("Window Area",
                           f"{res['window_area_m2']:.2f} m²")
                rc3.metric("Discomfort",
                           f"{res['discomfort_score']:.2f} °C·h")

                st.markdown("#### 🔄 Verification")
                opt_in = simulate_shelter_stable(
                    city_a, l_a, w_a, h_a, mat_key, res["window_area_m2"])
                wopt = get_climate_data(city_a)
                st.plotly_chart(plot_temperature_curves(
                    city_a, wopt["hourly_temperature"], opt_in,
                    "(Optimized)"), use_container_width=True)
            except Exception as e:
                st.error(f"Optimization failed: {e}")