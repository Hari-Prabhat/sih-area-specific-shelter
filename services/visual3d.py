"""
THERMOSHELTER AI - Climate-Adaptive Visual 3D Engine
=====================================================
Generates photo-realistic, climate-specific 3D architectural shelter models
using pure Plotly (Mesh3d) with physics-grounded geometries, lighting,
fenestration strategies, and environmental contextualization.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import plotly.graph_objects as go

# ==============================================================================
# 1. CLIMATE STYLE SPECIFICATIONS
# ==============================================================================
CLIMATE_STYLE: Dict[str, Dict[str, Any]] = {
    "cold": {
        "city_alias": "leh",
        "name": "Severe Cold / Alpine (Leh, Ladakh)",
        "roof_pitch": 45.0,
        "overhang": 0.30,
        "glazing_ratio": 0.70,  # 70% glazing on South wall
        "glazing_facades": ["south"],
        "wall_visual_thickness": 0.35,
        "palette": {
            "wall": "#78716c",          # Local mountain stone / rammed earth
            "wall_name": "Stone Masonry & Heavy Insulation",
            "roof": "#334155",          # Snow-shedding dark slate / metal
            "roof_name": "45° Snow-Shedding Insulated Metal Roof",
            "ground": "#f1f5f9",        # Snow / ice terrain
            "frame": "#1e293b",
            "door": "#78350f",
        },
        "extras": ["snow_cap", "vestibule"],
        "description": "High-pitch snow-shedding roof, 70% South-facing passive solar glazing, thermal airlock vestibule, heavy stone envelope."
    },
    "hot_dry": {
        "city_alias": "jaisalmer",
        "name": "Hot & Arid Desert (Jaisalmer, Thar)",
        "roof_pitch": 0.0,
        "overhang": 0.60,
        "glazing_ratio": 0.10,  # 10% small recessed apertures
        "glazing_facades": ["south", "north"],
        "wall_visual_thickness": 0.45,
        "palette": {
            "wall": "#d97706",          # Adobe sandstone / dense earth
            "wall_name": "Dense Sandstone / Adobe Thermal Mass",
            "roof": "#fafaf9",          # High-albedo cool roof (SRI > 85)
            "roof_name": "Reflective Flat Cool Roof (Albedo > 0.85)",
            "ground": "#eab308",        # Golden desert sand
            "frame": "#451a03",
            "door": "#92400e",
        },
        "extras": ["reflective_roof", "parapet"],
        "description": "Flat high-albedo cool roof, 450mm thermal mass walls, minimal recessed glazing to restrict extreme daytime radiant gain."
    },
    "hot_humid": {
        "city_alias": "chennai",
        "name": "Warm & Humid Coastal (Chennai, Coromandel)",
        "roof_pitch": 30.0,
        "overhang": 1.00,
        "glazing_ratio": 0.40,  # 40% on two opposite walls (cross-vent)
        "glazing_facades": ["south", "north"],
        "wall_visual_thickness": 0.15,
        "palette": {
            "wall": "#f8fafc",          # Clean white coastal reflective finish
            "wall_name": "Lightweight Aerated Cavity Wall",
            "roof": "#c2410c",          # Terracotta mangalore tile
            "roof_name": "30° Ventilated Pitched Terracotta Roof",
            "ground": "#15803d",        # Tropical lush green
            "frame": "#1e293b",
            "door": "#b45309",
        },
        "extras": ["verandah", "trees", "ridge_vent"],
        "description": "Deep 1.0m rain/sun overhangs, shaded verandah with timber posts, 100% cross-ventilation fenestration, ridge ventilation."
    },
    "composite": {
        "city_alias": "delhi",
        "name": "Composite / Extreme Seasonal (Delhi, NCR)",
        "roof_pitch": 20.0,
        "overhang": 0.60,
        "glazing_ratio": 0.40,  # 40% South-oriented
        "glazing_facades": ["south"],
        "wall_visual_thickness": 0.25,
        "palette": {
            "wall": "#b91c1c",          # Terracotta fired clay brick
            "wall_name": "Insulated Double Brick Cavity",
            "roof": "#475569",          # Composite insulation deck
            "roof_name": "20° Slope Composite Insulated Deck",
            "ground": "#65a30d",        # Northern plains turf
            "frame": "#0f172a",
            "door": "#7c2d12",
        },
        "extras": ["chajja_overhangs"],
        "description": "Balanced envelope for severe winter and summer extremes; South daylighting with chajja solar shading overhangs."
    },
    "moderate": {
        "city_alias": "bengaluru",
        "name": "Temperate Plateau (Bengaluru, Deccan)",
        "roof_pitch": 10.0,
        "overhang": 0.60,
        "glazing_ratio": 0.30,  # 30% two sides
        "glazing_facades": ["south", "north"],
        "wall_visual_thickness": 0.15,
        "palette": {
            "wall": "#fef3c7",          # Modern light cream
            "wall_name": "Fly-Ash Masonry / Modular Panel",
            "roof": "#1e293b",          # Modern charcoal deck
            "roof_name": "Low-Pitch Modern Charcoal Roof",
            "ground": "#16a34a",        # Plateau garden lawn
            "frame": "#0f172a",
            "door": "#a16207",
        },
        "extras": ["trees"],
        "description": "Optimized natural ventilation and daylighting apertures with perimeter landscaping to leverage mild annual climate."
    }
}

# Aliases mapping
CITY_TO_CLIMATE = {
    "leh": "cold",
    "jaisalmer": "hot_dry",
    "chennai": "hot_humid",
    "delhi": "composite",
    "bengaluru": "moderate"
}

LIGHTING_CONFIG = dict(
    ambient=0.65,
    diffuse=0.75,
    specular=0.25,
    roughness=0.45,
    fresnel=0.20
)
LIGHT_POSITION = dict(x=6, y=-10, z=12)


# ==============================================================================
# 2. 3D MESH GEOMETRY HELPERS
# ==============================================================================
def _add_box_mesh(
    fig: go.Figure,
    x0: float, y0: float, z0: float,
    dx: float, dy: float, dz: float,
    color: str,
    name: str,
    hovertext: str,
    opacity: float = 1.0,
    showlegend: bool = False
):
    """
    Constructs an authoritative 6-sided 3D rectangular box mesh with outward normals.
    """
    x = [x0, x0+dx, x0+dx, x0,    x0, x0+dx, x0+dx, x0]
    y = [y0, y0,    y0+dy, y0+dy, y0, y0,    y0+dy, y0+dy]
    z = [z0, z0,    z0,    z0,    z0+dz, z0+dz, z0+dz, z0+dz]

    i = [0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1]
    j = [2, 3, 5, 6, 1, 5, 3, 7, 4, 7, 6, 2]
    k = [1, 2, 6, 7, 5, 4, 7, 6, 7, 3, 5, 6]

    fig.add_trace(go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color=color, opacity=opacity, name=name,
        hoverinfo="text", hovertext=hovertext,
        lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
        flatshading=False, showlegend=showlegend
    ))


def _add_cylinder_mesh(
    fig: go.Figure,
    cx: float, cy: float, z_bottom: float,
    radius: float, height: float,
    color: str, name: str, hovertext: str,
    n_segments: int = 12
):
    """
    Adds a vertical cylinder mesh (e.g. for tree trunks and posts).
    """
    x, y, z = [], [], []
    for s in range(n_segments):
        theta = 2.0 * math.pi * s / n_segments
        x.append(cx + radius * math.cos(theta))
        y.append(cy + radius * math.sin(theta))
        z.append(z_bottom)

    for s in range(n_segments):
        theta = 2.0 * math.pi * s / n_segments
        x.append(cx + radius * math.cos(theta))
        y.append(cy + radius * math.sin(theta))
        z.append(z_bottom + height)

    i, j, k = [], [], []
    for s in range(n_segments):
        nxt = (s + 1) % n_segments
        # Quad side
        i.extend([s, s])
        j.extend([nxt, s + n_segments])
        k.extend([s + n_segments, nxt + n_segments])

    fig.add_trace(go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color=color, opacity=1.0, name=name,
        hoverinfo="text", hovertext=hovertext,
        lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
        flatshading=True, showlegend=False
    ))


def _add_cone_canopy(
    fig: go.Figure,
    cx: float, cy: float, z_base: float,
    radius: float, height: float,
    color: str, name: str, hovertext: str,
    n_segments: int = 12
):
    """
    Adds a low-poly tree canopy cone mesh.
    """
    x = [cx + radius * math.cos(2 * math.pi * s / n_segments) for s in range(n_segments)]
    y = [cy + radius * math.sin(2 * math.pi * s / n_segments) for s in range(n_segments)]
    z = [z_base] * n_segments

    # Apex point
    x.append(cx); y.append(cy); z.append(z_base + height)
    apex_idx = n_segments

    # Base center point
    x.append(cx); y.append(cy); z.append(z_base)
    base_idx = n_segments + 1

    i, j, k = [], [], []
    for s in range(n_segments):
        nxt = (s + 1) % n_segments
        # Cone face
        i.append(s); j.append(nxt); k.append(apex_idx)
        # Base disk
        i.append(s); j.append(base_idx); k.append(nxt)

    fig.add_trace(go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color=color, opacity=0.95, name=name,
        hoverinfo="text", hovertext=hovertext,
        lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
        flatshading=True, showlegend=False
    ))


# ==============================================================================
# 3. COMPONENT GENERATORS
# ==============================================================================
def _add_human_scale_figure(fig: go.Figure, hx: float, hy: float, hz: float = 0.0):
    """
    Adds a stylized 1.70m human figure for visual scale reference.
    """
    hover = "<b>👤 Human Scale Reference</b><br>Height: 1.70 m (5'7\")<br>Reference for internal volume & fenestration scale"
    # Legs (Navy pants)
    _add_box_mesh(fig, hx - 0.12, hy - 0.08, hz, 0.24, 0.16, 0.85, "#1e3a8a", "Human Scale (1.7m)", hover)
    # Torso (Sky cyan shirt)
    _add_box_mesh(fig, hx - 0.18, hy - 0.10, hz + 0.85, 0.36, 0.20, 0.60, "#0284c7", "Human Scale (1.7m)", hover)
    # Head (Peach skin tone)
    _add_box_mesh(fig, hx - 0.09, hy - 0.09, hz + 1.45, 0.18, 0.18, 0.22, "#fed7aa", "Human Scale (1.7m)", hover, showlegend=True)


def _add_sun_and_cardinal_compass(fig: go.Figure, length: float, width: float, height: float):
    """
    Adds a solar trajectory sun indicator and 3D cardinal North compass.
    """
    # 1. Sun Sphere on South side
    sx, sy, sz = length / 2.0, -width * 0.9 - 2.2, height + 3.0
    _add_box_mesh(
        fig, sx - 0.4, sy - 0.4, sz - 0.4, 0.8, 0.8, 0.8,
        "#facc15", "☀️ Sun (South Solar Axis)",
        "<b>☀️ South Solar Axis</b><br>Primary incident winter solar radiation direction<br>Harvested via South-facing fenestration",
        opacity=0.95, showlegend=True
    )

    # 2. 3D North Arrow on Ground
    nx, ny, nz = length + 1.2, width - 0.5, 0.02
    _add_box_mesh(fig, nx - 0.08, ny - 0.8, nz, 0.16, 0.8, 0.05, "#ef4444", "🧭 Compass North", "<b>North Cardinal Axis</b>")
    # Arrowhead
    x_arr = [nx - 0.35, nx + 0.35, nx]
    y_arr = [ny,        ny,        ny + 0.6]
    z_arr = [nz,        nz,        nz]
    fig.add_trace(go.Mesh3d(
        x=x_arr, y=y_arr, z=z_arr, i=[0], j=[1], k=[2],
        color="#ef4444", name="🧭 North Arrow",
        hoverinfo="text", hovertext="<b>🧭 True North Indicator</b>",
        showlegend=False
    ))


def _add_tree(fig: go.Figure, tx: float, ty: float, tz: float = 0.0, scale: float = 1.0):
    """
    Adds a low-poly landscaped tree for tropical and temperate microclimates.
    """
    hover = "<b>🌳 Microclimate Tree Buffer</b><br>Provides natural passive shading and evaporative cooling."
    # Trunk
    _add_cylinder_mesh(fig, tx, ty, tz, 0.14 * scale, 1.6 * scale, "#78350f", "Tree", hover)
    # Tier 1 Canopy
    _add_cone_canopy(fig, tx, ty, tz + 1.2 * scale, 1.4 * scale, 1.8 * scale, "#15803d", "Tree", hover)
    # Tier 2 Canopy
    _add_cone_canopy(fig, tx, ty, tz + 2.2 * scale, 1.0 * scale, 1.6 * scale, "#16a34a", "Tree", hover)


def _add_pitched_roof(
    fig: go.Figure,
    length: float, width: float, height: float,
    roof_pitch_deg: float, overhang: float,
    roof_color: str, roof_name: str,
    extras: List[str]
):
    """
    Builds a realistic 3D pitched gabled roof with overhangs and climate extras (snow cap, ridge vent).
    """
    pitch_rad = math.radians(roof_pitch_deg)
    y_mid = width / 2.0
    ridge_h = (y_mid + overhang) * math.tan(pitch_rad)
    z_ridge = height + ridge_h

    x_min, x_max = -overhang, length + overhang
    y_min, y_max = -overhang, width + overhang

    # South Roof Slope
    xs = [x_min, x_max, x_max, x_min]
    ys = [y_min, y_min, y_mid, y_mid]
    zs = [height, height, z_ridge, z_ridge]

    # North Roof Slope
    xn = [x_min, x_max, x_max, x_min]
    yn = [y_mid, y_mid, y_max, y_max]
    zn = [z_ridge, z_ridge, height, height]

    i_s = [0, 0]; j_s = [1, 2]; k_s = [2, 3]

    hover_roof = f"<b>🏠 {roof_name}</b><br>Slope: {roof_pitch_deg:.0f}° | Overhang: {overhang:.2f} m<br>Attic Thermal Buffer Zone"

    fig.add_trace(go.Mesh3d(
        x=xs, y=ys, z=zs, i=i_s, j=j_s, k=k_s,
        color=roof_color, opacity=0.96, name="Roof (South Pitch)",
        hoverinfo="text", hovertext=hover_roof,
        lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
        flatshading=True, showlegend=True
    ))

    fig.add_trace(go.Mesh3d(
        x=xn, y=yn, z=zn, i=i_s, j=j_s, k=k_s,
        color=roof_color, opacity=0.96, name="Roof (North Pitch)",
        hoverinfo="text", hovertext=hover_roof,
        lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
        flatshading=True, showlegend=False
    ))

    # Gabled Attic End Walls (West & East)
    # West Gable (x = 0)
    fig.add_trace(go.Mesh3d(
        x=[0, 0, 0],
        y=[0, width, y_mid],
        z=[height, height, height + (y_mid * math.tan(pitch_rad))],
        i=[0], j=[1], k=[2],
        color=roof_color, opacity=0.90, name="Attic Gable",
        hoverinfo="text", hovertext="<b>Gable Attic Wall</b>",
        lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
        flatshading=True, showlegend=False
    ))
    # East Gable (x = length)
    fig.add_trace(go.Mesh3d(
        x=[length, length, length],
        y=[0, y_mid, width],
        z=[height, height + (y_mid * math.tan(pitch_rad)), height],
        i=[0], j=[1], k=[2],
        color=roof_color, opacity=0.90, name="Attic Gable",
        hoverinfo="text", hovertext="<b>Gable Attic Wall</b>",
        lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
        flatshading=True, showlegend=False
    ))

    # Extra: Snow Cap on Roof (Leh / Cold)
    if "snow_cap" in extras:
        snow_zs = [z + 0.05 for z in zs]
        snow_zn = [z + 0.05 for z in zn]
        snow_hover = "<b>❄️ Snow Pack Layer</b><br>Natural additional roof insulation (R-value ~ 1.0 m²K/W)"
        fig.add_trace(go.Mesh3d(
            x=xs, y=ys, z=snow_zs, i=i_s, j=j_s, k=k_s,
            color="#f8fafc", opacity=0.92, name="Snow Cap (Winter Pack)",
            hoverinfo="text", hovertext=snow_hover,
            lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
            flatshading=True, showlegend=True
        ))
        fig.add_trace(go.Mesh3d(
            x=xn, y=yn, z=snow_zn, i=i_s, j=j_s, k=k_s,
            color="#f8fafc", opacity=0.92, name="Snow Cap",
            hoverinfo="text", hovertext=snow_hover,
            lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
            flatshading=True, showlegend=False
        ))

    # Extra: Ridge Vent (Chennai / Hot-Humid)
    if "ridge_vent" in extras:
        rv_w = 0.35
        _add_box_mesh(
            fig, x_min, y_mid - rv_w/2, z_ridge + 0.08, (x_max - x_min), rv_w, 0.15,
            "#7c2d12", "Ridge Ventilation Cap",
            "<b>💨 Continuous Ridge Vent</b><br>Exhausts rising indoor heat via thermal buoyancy stack effect.",
            showlegend=True
        )


def _add_flat_roof(
    fig: go.Figure,
    length: float, width: float, height: float,
    overhang: float, roof_color: str, roof_name: str,
    extras: List[str]
):
    """
    Builds a realistic 3D flat roof with overhangs and perimeter parapet walls.
    """
    x_min, x_max = -overhang, length + overhang
    y_min, y_max = -overhang, width + overhang
    slab_th = 0.18

    # Main Flat Slab
    hover_roof = f"<b>🏠 {roof_name}</b><br>Overhang: {overhang:.2f} m | High-Thermal Mass Concrete Deck"
    _add_box_mesh(
        fig, x_min, y_min, height, (x_max - x_min), (y_max - y_min), slab_th,
        roof_color, "Roof Deck", hover_roof, showlegend=True
    )

    # Parapet Border Walls
    if "parapet" in extras:
        pw_h = 0.35
        pw_th = 0.15
        p_col = "#c28b52" if "reflective_roof" in extras else roof_color
        # South parapet
        _add_box_mesh(fig, x_min, y_min, height + slab_th, (x_max - x_min), pw_th, pw_h, p_col, "Parapet", "Parapet Wall")
        # North parapet
        _add_box_mesh(fig, x_min, y_max - pw_th, height + slab_th, (x_max - x_min), pw_th, pw_h, p_col, "Parapet", "Parapet Wall")
        # West parapet
        _add_box_mesh(fig, x_min, y_min, height + slab_th, pw_th, (y_max - y_min), pw_h, p_col, "Parapet", "Parapet Wall")
        # East parapet
        _add_box_mesh(fig, x_max - pw_th, y_min, height + slab_th, pw_th, (y_max - y_min), pw_h, p_col, "Parapet", "Parapet Wall")

    # Extra: Reflective Cool Roof Coating Layer (Jaisalmer / Hot-Dry)
    if "reflective_roof" in extras:
        _add_box_mesh(
            fig, x_min + 0.1, y_min + 0.1, height + slab_th + 0.01,
            (x_max - x_min - 0.2), (y_max - y_min - 0.2), 0.03,
            "#fafaf9", "High-Albedo Reflective Coating",
            "<b>✨ White Reflective Cool Roof Layer</b><br>Solar Reflectance Index (SRI) > 85<br>Reflects 82% of incident solar irradiance.",
            showlegend=True
        )


# ==============================================================================
# 4. MASTER 3D BUILDER FUNCTION
# ==============================================================================
def build_3d_shelter(
    climate_type: str,
    length: float,
    width: float,
    height: float,
    window_area: float,
    wall_material: str = "brick",
    insulation_mm: float = 50.0,
    glazing_name: str = "Double Clear",
    city_name: Optional[str] = None
) -> go.Figure:
    """
    Creates an authoritative, climate-adaptive, highly visual 3D model of the shelter.

    Parameters:
        climate_type (str): Key from CLIMATE_STYLE (e.g. 'cold', 'hot_dry', 'hot_humid', etc.) or city name.
        length (float): Length in meters along X axis.
        width (float): Width in meters along Y axis.
        height (float): Wall height in meters along Z axis.
        window_area (float): Total fenestration area in m².
        wall_material (str): Identifier or display name of the envelope wall material.
        insulation_mm (float): Optimal insulation thickness in millimeters.
        glazing_name (str): Glazing specification name.
        city_name (Optional[str]): City name override for title.

    Returns:
        plotly.graph_objects.Figure: Complete interactive 3D shelter visualization.
    """
    fig = go.Figure()

    # 1. Resolve Climate Key
    key = str(climate_type).strip().lower()
    if key in CITY_TO_CLIMATE:
        key = CITY_TO_CLIMATE[key]
    if key not in CLIMATE_STYLE:
        key = "composite"

    spec = CLIMATE_STYLE[key]
    pal = spec["palette"]
    extras = spec["extras"]
    display_city = (city_name or spec["city_alias"]).upper()

    # 2. Ground Plane
    g_pad = max(3.5, length * 0.4)
    gx0, gx1 = -g_pad, length + g_pad
    gy0, gy1 = -g_pad, width + g_pad
    _add_box_mesh(
        fig, gx0, gy0, -0.04, (gx1 - gx0), (gy1 - gy0), 0.04,
        pal["ground"], "Ground Plane", f"<b>🌍 Surrounding Terrain</b> ({spec['name']})", showlegend=False
    )

    # 3. Solid Envelope Walls (with Visual Thickness)
    w_th = spec["wall_visual_thickness"]
    hover_wall = (
        f"<b>🧱 Envelope Wall Assembly</b><br>"
        f"Material: {pal['wall_name']} ({wall_material})<br>"
        f"Wall Thickness: {w_th*1000:.0f} mm + {insulation_mm:.0f} mm Insulation<br>"
        f"Footprint: {length:.1f} m × {width:.1f} m × {height:.1f} m"
    )

    # South Wall (front)
    _add_box_mesh(fig, 0, 0, 0, length, w_th, height, pal["wall"], "Walls", hover_wall, showlegend=True)
    # North Wall (back)
    _add_box_mesh(fig, 0, width - w_th, 0, length, w_th, height, pal["wall"], "Walls", hover_wall)
    # West Wall (left)
    _add_box_mesh(fig, 0, w_th, 0, w_th, width - 2*w_th, height, pal["wall"], "Walls", hover_wall)
    # East Wall (right)
    _add_box_mesh(fig, length - w_th, w_th, 0, w_th, width - 2*w_th, height, pal["wall"], "Walls", hover_wall)

    # 4. Entry Door (0.9m x 2.05m with frame)
    door_w, door_h = 0.90, min(height - 0.2, 2.05)
    door_x = min(0.6, (length - door_w) * 0.2)
    hover_door = f"<b>🚪 Insulated Entry Door</b><br>Size: {door_w:.2f} m × {door_h:.2f} m<br>Weatherstripped Thermal Barrier"
    # Door Frame
    _add_box_mesh(fig, door_x - 0.05, -0.04, 0, door_w + 0.10, w_th + 0.08, door_h + 0.05, pal["frame"], "Door Frame", hover_door)
    # Door Leaf
    _add_box_mesh(fig, door_x, -0.06, 0, door_w, 0.06, door_h, pal["door"], "Entry Door", hover_door, showlegend=True)

    # 5. Fenestration Windows (Framed with cyan glazing panes)
    # Calculate fenestration dimensions based on climate allocation
    glaze_facades = spec["glazing_facades"]
    if len(glaze_facades) == 1 and "south" in glaze_facades:
        # Concentrate primarily on South facade
        south_win_area = window_area
        north_win_area = 0.0
    else:
        # Cross-ventilation distribution (e.g. 55% South, 45% North)
        south_win_area = window_area * 0.55
        north_win_area = window_area * 0.45

    # South Window Setup
    if south_win_area > 0.3:
        max_ww = length - door_x - door_w - 0.8
        win_w = max(0.8, min(max_ww, math.sqrt(south_win_area * 1.5)))
        win_h = max(0.6, min(height * 0.6, south_win_area / max(0.01, win_w)))
        win_x = door_x + door_w + 0.4
        win_z = max(0.7, (height - win_h) / 2.0)

        hover_win = f"<b>🪟 South Solar Glazing</b><br>Spec: {glazing_name}<br>Aperture Area: {win_w*win_h:.2f} m²<br>Passive Solar Gain Harvesting"
        # Window Frame
        _add_box_mesh(fig, win_x - 0.06, -0.04, win_z - 0.06, win_w + 0.12, w_th + 0.08, win_h + 0.12, pal["frame"], "Window Frame", hover_win)
        # Glazing Pane
        _add_box_mesh(fig, win_x, -0.06, win_z, win_w, 0.06, win_h, "#38bdf8", "Glazing (South)", hover_win, opacity=0.82, showlegend=True)

    # North Window Setup (Cross-Ventilation)
    if north_win_area > 0.3:
        n_win_w = max(0.8, min(length * 0.65, math.sqrt(north_win_area * 1.5)))
        n_win_h = max(0.6, min(height * 0.55, north_win_area / max(0.01, n_win_w)))
        n_win_x = (length - n_win_w) / 2.0
        n_win_z = max(0.8, (height - n_win_h) / 2.0)

        hover_n_win = f"<b>🪟 North Cross-Ventilation Window</b><br>Spec: {glazing_name}<br>Area: {n_win_w*n_win_h:.2f} m²<br>Prevents Overheating / Natural Airflow"
        # North Window Frame
        _add_box_mesh(fig, n_win_x - 0.06, width - w_th - 0.04, n_win_z - 0.06, n_win_w + 0.12, w_th + 0.08, n_win_h + 0.12, pal["frame"], "North Frame", hover_n_win)
        # North Glazing Pane
        _add_box_mesh(fig, n_win_x, width - 0.02, n_win_z, n_win_w, 0.06, n_win_h, "#22d3ee", "Glazing (North)", hover_n_win, opacity=0.82)

    # 6. Roof Assembly (Pitched or Flat)
    r_pitch = spec["roof_pitch"]
    r_overhang = spec["overhang"]
    if r_pitch > 0:
        _add_pitched_roof(
            fig, length, width, height, r_pitch, r_overhang,
            pal["roof"], pal["roof_name"], extras
        )
    else:
        _add_flat_roof(
            fig, length, width, height, r_overhang,
            pal["roof"], pal["roof_name"], extras
        )

    # 7. Climate-Specific Architectural Extras
    # Extra: Airlock Entry Vestibule (Leh / Cold)
    if "vestibule" in extras:
        v_w = 1.3
        v_d = 0.9
        v_h = min(height, 2.3)
        v_hover = "<b>❄️ Thermal Airlock Vestibule</b><br>Double-door entry buffer preventing direct cold drafts."
        _add_box_mesh(fig, door_x - 0.2, -v_d, 0, v_w, v_d, v_h, pal["wall"], "Thermal Vestibule", v_hover, showlegend=True)
        # Vestibule Sloped Roof
        _add_box_mesh(fig, door_x - 0.25, -v_d - 0.1, v_h, v_w + 0.1, v_d + 0.15, 0.12, pal["roof"], "Vestibule Roof", v_hover)

    # Extra: Front Verandah with Timber Posts (Chennai / Hot-Humid)
    if "verandah" in extras:
        v_depth = 1.2
        v_plinth_h = 0.15
        hover_v = "<b>🌿 Shaded Deep Verandah</b><br>Reduces solar thermal load on facade by over 80% while capturing breezes."
        # Raised Plinth Floor
        _add_box_mesh(fig, -0.2, -v_depth, 0, length + 0.4, v_depth, v_plinth_h, "#a16207", "Verandah Plinth", hover_v, showlegend=True)
        # 3 Structural Pillars
        pillar_x = [0.1, length / 2.0, length - 0.1]
        for px in pillar_x:
            _add_box_mesh(fig, px - 0.07, -v_depth + 0.08, v_plinth_h, 0.14, 0.14, height - v_plinth_h, "#78350f", "Verandah Pillar", "Verandah Pillar Post")

    # Extra: Trees Context (Chennai & Bengaluru)
    if "trees" in extras:
        _add_tree(fig, length + 2.2, -1.8, 0, scale=1.1)
        _add_tree(fig, -2.4, width * 0.6, 0, scale=0.9)

    # 8. Human Scale Reference Figure (1.70 m)
    _add_human_scale_figure(fig, hx=length + 0.8, hy=-1.0, hz=0.0)

    # 9. Sun Trajectory and Cardinal North Compass
    _add_sun_and_cardinal_compass(fig, length, width, height)

    # 10. Realism Layout & Lighting Configurations
    fig.update_layout(
        title=dict(
            text=f"<b>🏗️ 3D Climate-Adaptive Model — {display_city} ({spec['name']})</b>",
            font=dict(family="Inter, -apple-system, sans-serif", size=15, color="#38bdf8"),
            x=0.01,
            y=0.97
        ),
        paper_bgcolor="#1e293b",
        font=dict(family="Inter, -apple-system, sans-serif", color="#f8fafc"),
        scene=dict(
            aspectmode="data",
            camera=dict(
                eye=dict(x=1.6, y=-1.6, z=0.9),
                center=dict(x=0, y=0, z=-0.1)
            ),
            xaxis=dict(showbackground=False, visible=False),
            yaxis=dict(showbackground=False, visible=False),
            zaxis=dict(showbackground=False, visible=False),
            bgcolor="#0f172a"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.98,
            xanchor="right",
            x=1.0,
            font=dict(color="#f8fafc", size=11),
            bgcolor="rgba(15, 23, 42, 0.85)",
            bordercolor="rgba(56, 189, 248, 0.25)",
            borderwidth=1
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        height=520
    )

    return fig


if __name__ == "__main__":
    # Smoke test all 5 climates
    test_climates = ["leh", "jaisalmer", "chennai", "delhi", "bengaluru"]
    print("Testing 3D generation across all 5 climates...")
    for c in test_climates:
        f = build_3d_shelter(
            climate_type=c,
            length=4.5,
            width=3.2,
            height=2.8,
            window_area=2.5,
            wall_material="brick",
            insulation_mm=50.0,
            glazing_name="Double Clear Glazing"
        )
        print(f"[OK] {c.upper()}: {len(f.data)} 3D mesh components generated.")
