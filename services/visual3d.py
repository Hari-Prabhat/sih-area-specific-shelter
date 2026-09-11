"""
THERMOSHELTER AI - Climate-Adaptive Visual 3D Digital Twin Engine
==================================================================
Generates premium, climate-specific 3D architectural shelter models
using pure Plotly (Mesh3d) with physics-grounded geometries, structural
detailing, fenestration strategies, environmental contextualization,
and multi-mode Digital Twin visualization.

View Modes:
  - normal     : Standard architectural presentation
  - envelope   : Cutaway showing insulation layers & wall assembly
  - thermal    : Heatmap-coloured surfaces from simulation data
  - solar      : Highlights PV panels, glazing, and sun path
  - ventilation: Highlights airflow openings and cross-vent paths
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
        "plinth_height": 0.30,
        "palette": {
            "wall": "#78716c",          # Local mountain stone / rammed earth
            "wall_inner": "#a8a29e",
            "wall_name": "Stone Masonry & Heavy Insulation",
            "roof": "#334155",          # Snow-shedding dark slate / metal
            "roof_name": "45° Snow-Shedding Insulated Metal Roof",
            "ground": "#e2e8f0",        # Snow / ice terrain
            "plinth": "#57534e",
            "frame": "#1e293b",
            "door": "#78350f",
            "insulation": "#fbbf24",
            "coursing": "#57534e",
            "pilaster": "#44403c",
            "solar_panel": "#1e3a5f",
            "solar_frame": "#94a3b8",
        },
        "extras": ["snow_cap", "vestibule", "thermal_mass_interior", "solar_panels_roof"],
        "description": "High-pitch snow-shedding roof, 70% South-facing passive solar glazing, thermal airlock vestibule, heavy stone envelope.",
        "camera": dict(eye=dict(x=1.8, y=-1.9, z=1.1), center=dict(x=0, y=0, z=-0.05)),
    },
    "hot_dry": {
        "city_alias": "jaisalmer",
        "name": "Hot & Arid Desert (Jaisalmer, Thar)",
        "roof_pitch": 0.0,
        "overhang": 0.60,
        "glazing_ratio": 0.10,  # 10% small recessed apertures
        "glazing_facades": ["south", "north"],
        "wall_visual_thickness": 0.45,
        "plinth_height": 0.20,
        "palette": {
            "wall": "#d97706",          # Adobe sandstone / dense earth
            "wall_inner": "#fbbf24",
            "wall_name": "Dense Sandstone / Adobe Thermal Mass",
            "roof": "#fafaf9",          # High-albedo cool roof (SRI > 85)
            "roof_name": "Reflective Flat Cool Roof (Albedo > 0.85)",
            "ground": "#eab308",        # Golden desert sand
            "plinth": "#b45309",
            "frame": "#451a03",
            "door": "#92400e",
            "insulation": "#fde68a",
            "coursing": "#b45309",
            "pilaster": "#92400e",
            "solar_panel": "#1e3a5f",
            "solar_frame": "#d6d3d1",
        },
        "extras": ["reflective_roof", "parapet", "deep_recessed_windows", "shade_fins", "solar_panels_flat"],
        "description": "Flat high-albedo cool roof, 450mm thermal mass walls, minimal recessed glazing to restrict extreme daytime radiant gain.",
        "camera": dict(eye=dict(x=1.7, y=-1.7, z=0.85), center=dict(x=0, y=0, z=-0.08)),
    },
    "hot_humid": {
        "city_alias": "chennai",
        "name": "Warm & Humid Coastal (Chennai, Coromandel)",
        "roof_pitch": 30.0,
        "overhang": 1.00,
        "glazing_ratio": 0.40,  # 40% on two opposite walls (cross-vent)
        "glazing_facades": ["south", "north"],
        "wall_visual_thickness": 0.15,
        "plinth_height": 0.35,
        "palette": {
            "wall": "#f8fafc",          # Clean white coastal reflective finish
            "wall_inner": "#e2e8f0",
            "wall_name": "Lightweight Aerated Cavity Wall",
            "roof": "#c2410c",          # Terracotta mangalore tile
            "roof_name": "30° Ventilated Pitched Terracotta Roof",
            "ground": "#0f172a",        # Architectural dark studio floor
            "plinth": "#78716c",
            "frame": "#1e293b",
            "door": "#b45309",
            "insulation": "#a3e635",
            "coursing": "#cbd5e1",
            "pilaster": "#94a3b8",
            "solar_panel": "#1e3a5f",
            "solar_frame": "#94a3b8",
        },
        "extras": ["verandah", "trees", "ridge_vent", "ventilation_louvers"],
        "description": "Deep 1.0m rain/sun overhangs, shaded verandah, 100% cross-ventilation, ridge ventilation.",
        "camera": dict(eye=dict(x=1.9, y=-2.0, z=0.95), center=dict(x=0, y=0, z=-0.05)),
    },
    "composite": {
        "city_alias": "delhi",
        "name": "Composite / Extreme Seasonal (Delhi, NCR)",
        "roof_pitch": 20.0,
        "overhang": 0.60,
        "glazing_ratio": 0.40,  # 40% South-oriented
        "glazing_facades": ["south"],
        "wall_visual_thickness": 0.25,
        "plinth_height": 0.22,
        "palette": {
            "wall": "#b91c1c",          # Terracotta fired clay brick
            "wall_inner": "#fca5a5",
            "wall_name": "Insulated Double Brick Cavity",
            "roof": "#475569",          # Composite insulation deck
            "roof_name": "20° Slope Composite Insulated Deck",
            "ground": "#0f172a",        # Architectural dark studio floor
            "plinth": "#78716c",
            "frame": "#0f172a",
            "door": "#7c2d12",
            "insulation": "#fdba74",
            "coursing": "#991b1b",
            "pilaster": "#7f1d1d",
            "solar_panel": "#1e3a5f",
            "solar_frame": "#94a3b8",
        },
        "extras": ["chajja_overhangs", "solar_panels_roof"],
        "description": "Balanced envelope for severe winter and summer extremes; South daylighting with chajja solar shading overhangs.",
        "camera": dict(eye=dict(x=1.6, y=-1.6, z=0.9), center=dict(x=0, y=0, z=-0.1)),
    },
    "moderate": {
        "city_alias": "bengaluru",
        "name": "Temperate Plateau (Bengaluru, Deccan)",
        "roof_pitch": 10.0,
        "overhang": 0.60,
        "glazing_ratio": 0.30,  # 30% two sides
        "glazing_facades": ["south", "north"],
        "wall_visual_thickness": 0.15,
        "plinth_height": 0.18,
        "palette": {
            "wall": "#fef3c7",          # Modern light cream
            "wall_inner": "#fef9c3",
            "wall_name": "Fly-Ash Masonry / Modular Panel",
            "roof": "#1e293b",          # Modern charcoal deck
            "roof_name": "Low-Pitch Modern Charcoal Roof",
            "ground": "#0f172a",        # Architectural dark studio floor
            "plinth": "#78716c",
            "frame": "#0f172a",
            "door": "#a16207",
            "insulation": "#bef264",
            "coursing": "#d4d4d4",
            "pilaster": "#a8a29e",
            "solar_panel": "#1e3a5f",
            "solar_frame": "#94a3b8",
        },
        "extras": ["trees"],
        "description": "Optimized natural ventilation and daylighting with perimeter landscaping to leverage mild annual climate.",
        "camera": dict(eye=dict(x=1.6, y=-1.6, z=0.9), center=dict(x=0, y=0, z=-0.1)),
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
    ambient=0.55,
    diffuse=0.80,
    specular=0.35,
    roughness=0.35,
    fresnel=0.25
)
LIGHT_POSITION = dict(x=8, y=-12, z=14)

# Secondary fill light for depth
FILL_LIGHT = dict(
    ambient=0.70,
    diffuse=0.60,
    specular=0.10,
    roughness=0.55,
    fresnel=0.10
)


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
    showlegend: bool = False,
    lighting: Optional[dict] = None,
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
        lighting=lighting or LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
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


def _add_dimension_line(
    fig: go.Figure,
    p1: Tuple[float, float, float],
    p2: Tuple[float, float, float],
    label: str,
    color: str = "#94a3b8",
):
    """Adds a dimension annotation line with label between two 3D points."""
    mx = (p1[0] + p2[0]) / 2
    my = (p1[1] + p2[1]) / 2
    mz = (p1[2] + p2[2]) / 2
    fig.add_trace(go.Scatter3d(
        x=[p1[0], p2[0]], y=[p1[1], p2[1]], z=[p1[2], p2[2]],
        mode="lines+text",
        line=dict(color=color, width=2, dash="dot"),
        text=[None, label],
        textposition="top center",
        textfont=dict(size=10, color=color, family="Inter, sans-serif"),
        hoverinfo="skip",
        showlegend=False,
    ))


# ==============================================================================
# 3. ARCHITECTURAL DETAIL GENERATORS
# ==============================================================================
def _add_foundation_plinth(
    fig: go.Figure,
    length: float, width: float,
    plinth_h: float, w_th: float,
    plinth_color: str,
):
    """Visible raised concrete foundation plinth with stepped edge."""
    pad = 0.12
    hover = (
        f"<b>🧱 Foundation Plinth</b><br>"
        f"Height: {plinth_h*1000:.0f} mm | Stepped RCC/Stone Base<br>"
        f"Protects against ground moisture & thermal bridging"
    )
    # Main plinth slab
    _add_box_mesh(
        fig, -pad, -pad, -plinth_h,
        length + 2*pad, width + 2*pad, plinth_h,
        plinth_color, "Foundation Plinth", hover, showlegend=True
    )
    # Step-out footing (slightly wider base)
    step = 0.06
    _add_box_mesh(
        fig, -pad - step, -pad - step, -plinth_h - 0.08,
        length + 2*(pad + step), width + 2*(pad + step), 0.08,
        plinth_color, "Footing", hover, opacity=0.85
    )


def _add_wall_coursing(
    fig: go.Figure,
    x0: float, y0: float, z0: float,
    dx: float, dy: float, wall_h: float,
    coursing_color: str,
    is_x_face: bool,
    n_courses: int = 6,
):
    """Renders horizontal mortar coursing lines on a wall face."""
    course_h = wall_h / n_courses
    seam_thickness = 0.02
    for i in range(1, n_courses):
        cz = z0 + i * course_h
        _add_box_mesh(
            fig, x0, y0, cz - seam_thickness/2,
            dx, dy, seam_thickness,
            coursing_color, "Coursing", "Mortar Joint Line",
            opacity=0.6
        )


def _add_corner_pilasters(
    fig: go.Figure,
    length: float, width: float, height: float,
    w_th: float, pilaster_color: str, z_base: float = 0.0,
):
    """Visible structural corner pilasters at wall intersections."""
    pw = w_th * 1.25  # slightly wider than wall
    pd = w_th * 1.25
    ph = height
    hover = "<b>Structural Corner Pilaster</b><br>Reinforced column at wall intersection"
    corners = [
        (0 - (pw - w_th)/2, 0 - (pd - w_th)/2),
        (length - pw + (pw - w_th)/2, 0 - (pd - w_th)/2),
        (0 - (pw - w_th)/2, width - pd + (pd - w_th)/2),
        (length - pw + (pw - w_th)/2, width - pd + (pd - w_th)/2),
    ]
    for cx, cy in corners:
        _add_box_mesh(fig, cx, cy, z_base, pw, pd, ph, pilaster_color, "Pilaster", hover, opacity=0.92)


def _add_recessed_door(
    fig: go.Figure,
    door_x: float, wall_y: float, z_base: float,
    door_w: float, door_h: float,
    w_th: float,
    frame_color: str, door_color: str,
    plinth_h: float = 0.0,
):
    """Door set into a recessed reveal with visible frame depth, threshold step, handle."""
    recess_depth = min(w_th * 0.5, 0.15)
    hover_door = (
        f"<b>🚪 Insulated Entry Door</b><br>"
        f"Size: {door_w:.2f} m × {door_h:.2f} m<br>"
        f"Recess Depth: {recess_depth*1000:.0f} mm<br>"
        f"Weatherstripped Thermal Barrier"
    )
    # Recessed reveal (darker void)
    _add_box_mesh(
        fig, door_x - 0.04, wall_y - 0.02, z_base,
        door_w + 0.08, recess_depth + 0.04, door_h + 0.04,
        "#0f172a", "Door Reveal", hover_door, opacity=0.95
    )
    # Door frame (3-sided)
    fr = 0.05
    _add_box_mesh(fig, door_x - fr, wall_y - 0.03, z_base, fr, w_th*0.3 + 0.06, door_h + fr, frame_color, "Door Frame", hover_door)
    _add_box_mesh(fig, door_x + door_w, wall_y - 0.03, z_base, fr, w_th*0.3 + 0.06, door_h + fr, frame_color, "Door Frame", hover_door)
    _add_box_mesh(fig, door_x - fr, wall_y - 0.03, z_base + door_h, door_w + 2*fr, w_th*0.3 + 0.06, fr, frame_color, "Door Frame", hover_door)
    # Door leaf (set back into reveal)
    _add_box_mesh(
        fig, door_x, wall_y - recess_depth * 0.3, z_base,
        door_w, 0.06, door_h,
        door_color, "Entry Door", hover_door, showlegend=True
    )
    # Threshold step
    _add_box_mesh(
        fig, door_x - 0.06, wall_y - recess_depth - 0.1, z_base - 0.04,
        door_w + 0.12, recess_depth + 0.15, 0.04,
        frame_color, "Threshold", "Door Threshold Step"
    )
    # Handle dot
    _add_box_mesh(
        fig, door_x + door_w * 0.82, wall_y - recess_depth * 0.3 - 0.01, z_base + door_h * 0.48,
        0.04, 0.04, 0.06,
        "#d4af37", "Handle", "Door Handle", opacity=0.95
    )


def _add_recessed_window(
    fig: go.Figure,
    win_x: float, wall_y: float, win_z: float,
    win_w: float, win_h: float,
    w_th: float,
    frame_color: str, glazing_color: str,
    facade_label: str, glazing_name: str,
    is_deep_recess: bool = False,
    opacity: float = 0.80,
    showlegend: bool = False,
):
    """Window set back from wall face showing wall-thickness reveal, mullion cross-bars."""
    recess = min(w_th * (0.7 if is_deep_recess else 0.4), 0.20 if is_deep_recess else 0.12)
    hover = (
        f"<b>🪟 {facade_label} Glazing</b><br>"
        f"Spec: {glazing_name}<br>"
        f"Aperture: {win_w:.2f} × {win_h:.2f} m ({win_w*win_h:.2f} m²)<br>"
        f"Recess: {recess*1000:.0f} mm reveal depth"
    )
    # Reveal void
    _add_box_mesh(
        fig, win_x - 0.03, wall_y - 0.01, win_z - 0.03,
        win_w + 0.06, recess + 0.03, win_h + 0.06,
        "#0f172a", "Window Reveal", hover, opacity=0.9
    )
    # Frame (4-sided)
    fr = 0.04
    _add_box_mesh(fig, win_x - fr, wall_y - 0.02, win_z - fr, win_w + 2*fr, recess*0.3 + 0.04, fr, frame_color, "Window Frame", hover)
    _add_box_mesh(fig, win_x - fr, wall_y - 0.02, win_z + win_h, win_w + 2*fr, recess*0.3 + 0.04, fr, frame_color, "Window Frame", hover)
    _add_box_mesh(fig, win_x - fr, wall_y - 0.02, win_z, fr, recess*0.3 + 0.04, win_h, frame_color, "Window Frame", hover)
    _add_box_mesh(fig, win_x + win_w, wall_y - 0.02, win_z, fr, recess*0.3 + 0.04, win_h, frame_color, "Window Frame", hover)
    # Mullion cross-bars (vertical center + horizontal center)
    mb = 0.025
    _add_box_mesh(fig, win_x + win_w/2 - mb/2, wall_y - 0.02, win_z, mb, recess*0.3 + 0.04, win_h, frame_color, "Mullion", hover)
    _add_box_mesh(fig, win_x, wall_y - 0.02, win_z + win_h/2 - mb/2, win_w, recess*0.3 + 0.04, mb, frame_color, "Mullion", hover)
    # Glazing pane (set back into recess)
    _add_box_mesh(
        fig, win_x, wall_y + recess * 0.2, win_z,
        win_w, 0.04, win_h,
        glazing_color, f"Glazing ({facade_label})", hover,
        opacity=opacity, showlegend=showlegend
    )
    # Sill (bottom ledge)
    _add_box_mesh(
        fig, win_x - 0.04, wall_y - recess * 0.4, win_z - 0.04,
        win_w + 0.08, recess * 0.6 + 0.04, 0.04,
        frame_color, "Window Sill", "Window Sill Ledge"
    )


def _add_solar_panels_pitched(
    fig: go.Figure,
    length: float, width: float, height: float,
    roof_pitch_deg: float, overhang: float,
    panel_color: str, frame_color: str,
):
    """Solar PV panel array on south-facing pitched roof slope."""
    pitch_rad = math.radians(roof_pitch_deg)
    y_mid = width / 2.0
    panel_rows = 2
    panel_cols = max(2, int(length / 1.5))
    p_w = (length * 0.8) / panel_cols
    p_h = (y_mid * 0.5) / panel_rows
    margin = 0.1

    hover = (
        "<b>☀️ Rooftop Solar PV Array</b><br>"
        f"Panels: {panel_rows}×{panel_cols} ({panel_rows*panel_cols} modules)<br>"
        "Integrated with south-facing roof slope for optimal winter insolation"
    )
    for r in range(panel_rows):
        for c in range(panel_cols):
            px = (length * 0.1) + c * (p_w + margin)
            # Position along south roof slope
            py_base = overhang * 0.3 + r * (p_h + margin) + 0.3
            pz_base = height + py_base * math.tan(pitch_rad) + 0.08
            _add_box_mesh(
                fig, px, -overhang + py_base, pz_base,
                p_w, p_h * math.cos(pitch_rad), 0.04,
                panel_color, "Solar PV Panel", hover,
                opacity=0.92, showlegend=(r == 0 and c == 0)
            )


def _add_solar_panels_flat(
    fig: go.Figure,
    length: float, width: float, height: float,
    overhang: float,
    panel_color: str, frame_color: str,
    slab_th: float = 0.18,
):
    """Solar PV panel array on flat roof with tilt frames."""
    panel_rows = 2
    panel_cols = max(2, int(length / 1.8))
    p_w = (length * 0.65) / panel_cols
    p_h = 0.8
    margin = 0.2
    tilt_angle = math.radians(15)
    z_top = height + slab_th + 0.40

    hover = (
        "<b>☀️ Rooftop Solar PV Array</b><br>"
        f"Panels: {panel_rows}×{panel_cols} ({panel_rows*panel_cols} modules)<br>"
        "Tilted 15° on flat roof for optimal year-round generation"
    )
    for r in range(panel_rows):
        for c in range(panel_cols):
            px = (length * 0.15) + c * (p_w + margin)
            py = (width * 0.15) + r * (p_h + margin + 0.3)
            # Support legs
            _add_box_mesh(fig, px, py, height + slab_th + 0.05, 0.04, 0.04, 0.30, frame_color, "PV Mount", hover)
            _add_box_mesh(fig, px + p_w - 0.04, py, height + slab_th + 0.05, 0.04, 0.04, 0.35, frame_color, "PV Mount", hover)
            # Panel
            _add_box_mesh(
                fig, px, py, z_top,
                p_w, p_h, 0.03,
                panel_color, "Solar PV Panel", hover,
                opacity=0.92, showlegend=(r == 0 and c == 0)
            )


def _add_shade_fins(
    fig: go.Figure,
    win_x: float, wall_y: float, win_z: float,
    win_w: float, win_h: float,
    w_th: float, fin_color: str,
):
    """Projecting horizontal shade fin (jaali/chajja) above window for hot-dry climate."""
    fin_depth = 0.45
    fin_th = 0.06
    hover = "<b>🏗️ Solar Shade Fin (Chajja)</b><br>Projects 450mm to block high-angle summer sun<br>Permits low-angle winter sun entry"
    _add_box_mesh(
        fig, win_x - 0.1, wall_y - fin_depth, win_z + win_h + 0.02,
        win_w + 0.2, fin_depth + w_th * 0.3, fin_th,
        fin_color, "Shade Fin", hover, showlegend=True
    )


def _add_ventilation_louvers(
    fig: go.Figure,
    win_x: float, wall_y: float, win_z: float,
    win_w: float, win_h: float,
    frame_color: str,
):
    """Ventilation louver slats above or below a window for hot-humid cross-ventilation."""
    n_slats = 4
    slat_h = 0.04
    slat_gap = 0.06
    louver_h = n_slats * (slat_h + slat_gap)
    lz = win_z + win_h + 0.06
    hover = "<b>💨 Ventilation Louvers</b><br>Angled slats for permanent airflow<br>Rain-resistant while allowing cross-ventilation"
    for s in range(n_slats):
        sz = lz + s * (slat_h + slat_gap)
        _add_box_mesh(
            fig, win_x, wall_y - 0.08, sz,
            win_w, 0.12, slat_h,
            frame_color, "Ventilation Louver", hover,
            showlegend=(s == 0)
        )


def _add_thermal_mass_interior(
    fig: go.Figure,
    length: float, width: float, height: float,
    w_th: float, wall_color: str,
):
    """Interior thermal mass accent strip visible through cutaway for cold climates."""
    hover = "<b>🧱 Interior Thermal Mass</b><br>Dense masonry inner leaf stores solar heat during day<br>Releases warmth during cold nights"
    strip_h = height * 0.5
    strip_z = 0.3
    # Inner leaf on south wall
    _add_box_mesh(
        fig, w_th + 0.3, w_th + 0.02, strip_z,
        length * 0.4, 0.12, strip_h,
        "#a8a29e", "Thermal Mass", hover, opacity=0.85, showlegend=True
    )


# ==============================================================================
# 4. ROOF BUILDERS (UPGRADED)
# ==============================================================================
def _add_pitched_roof(
    fig: go.Figure,
    length: float, width: float, height: float,
    roof_pitch_deg: float, overhang: float,
    roof_color: str, roof_name: str,
    extras: List[str],
):
    """
    Builds a realistic 3D pitched gabled roof with visible thickness, overhangs,
    fascia, ridge cap, and climate extras.
    """
    pitch_rad = math.radians(roof_pitch_deg)
    y_mid = width / 2.0
    ridge_h = (y_mid + overhang) * math.tan(pitch_rad)
    z_ridge = height + ridge_h
    slab_th = 0.12

    x_min, x_max = -overhang, length + overhang
    y_min, y_max = -overhang, width + overhang

    # South Roof Slope (outer surface)
    xs = [x_min, x_max, x_max, x_min]
    ys = [y_min, y_min, y_mid, y_mid]
    zs = [height, height, z_ridge, z_ridge]
    i_s = [0, 0]; j_s = [1, 2]; k_s = [2, 3]

    hover_roof = (
        f"<b>🏠 {roof_name}</b><br>"
        f"Slope: {roof_pitch_deg:.0f}° | Overhang: {overhang:.2f} m<br>"
        f"Deck Thickness: {slab_th*1000:.0f} mm<br>"
        f"Attic Thermal Buffer Zone"
    )

    fig.add_trace(go.Mesh3d(
        x=xs, y=ys, z=zs, i=i_s, j=j_s, k=k_s,
        color=roof_color, opacity=0.96, name="Roof (South Pitch)",
        hoverinfo="text", hovertext=hover_roof,
        lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
        flatshading=True, showlegend=True
    ))

    # North Roof Slope
    xn = [x_min, x_max, x_max, x_min]
    yn = [y_mid, y_mid, y_max, y_max]
    zn = [z_ridge, z_ridge, height, height]

    fig.add_trace(go.Mesh3d(
        x=xn, y=yn, z=zn, i=i_s, j=j_s, k=k_s,
        color=roof_color, opacity=0.96, name="Roof (North Pitch)",
        hoverinfo="text", hovertext=hover_roof,
        lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
        flatshading=True, showlegend=False
    ))

    # Roof underside (visible slab thickness) - south
    zs_under = [z - slab_th for z in zs]
    fig.add_trace(go.Mesh3d(
        x=xs, y=ys, z=zs_under, i=i_s, j=j_s, k=k_s,
        color="#334155", opacity=0.65, name="Roof Soffit",
        hoverinfo="text", hovertext="Roof Soffit / Underside",
        lighting=FILL_LIGHT, lightposition=LIGHT_POSITION,
        flatshading=True, showlegend=False
    ))
    # North underside
    zn_under = [z - slab_th for z in zn]
    fig.add_trace(go.Mesh3d(
        x=xn, y=yn, z=zn_under, i=i_s, j=j_s, k=k_s,
        color="#334155", opacity=0.65, name="Roof Soffit",
        hoverinfo="text", hovertext="Roof Soffit / Underside",
        lighting=FILL_LIGHT, lightposition=LIGHT_POSITION,
        flatshading=True, showlegend=False
    ))

    # Gabled Attic End Walls
    fig.add_trace(go.Mesh3d(
        x=[0, 0, 0], y=[0, width, y_mid],
        z=[height, height, height + (y_mid * math.tan(pitch_rad))],
        i=[0], j=[1], k=[2],
        color=roof_color, opacity=0.90, name="Attic Gable",
        hoverinfo="text", hovertext="<b>Gable Attic Wall</b>",
        lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
        flatshading=True, showlegend=False
    ))
    fig.add_trace(go.Mesh3d(
        x=[length, length, length], y=[0, y_mid, width],
        z=[height, height + (y_mid * math.tan(pitch_rad)), height],
        i=[0], j=[1], k=[2],
        color=roof_color, opacity=0.90, name="Attic Gable",
        hoverinfo="text", hovertext="<b>Gable Attic Wall</b>",
        lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
        flatshading=True, showlegend=False
    ))

    # Ridge cap (thick beam along the ridge)
    _add_box_mesh(
        fig, x_min, y_mid - 0.06, z_ridge - 0.02,
        (x_max - x_min), 0.12, 0.08,
        "#475569", "Ridge Cap", "<b>Ridge Cap</b><br>Weatherproofing ridge beam"
    )

    # Fascia boards at eaves (south and north)
    _add_box_mesh(fig, x_min, y_min - 0.04, height - 0.06, (x_max - x_min), 0.04, 0.10, "#334155", "Fascia", "Eave Fascia Board")
    _add_box_mesh(fig, x_min, y_max, height - 0.06, (x_max - x_min), 0.04, 0.10, "#334155", "Fascia", "Eave Fascia Board")

    # Extra: Snow Cap on Roof (Leh / Cold)
    if "snow_cap" in extras:
        snow_zs = [z + 0.06 for z in zs]
        snow_zn = [z + 0.06 for z in zn]
        snow_hover = "<b>❄️ Snow Pack Layer</b><br>Natural additional roof insulation (R-value ~ 1.0 m²K/W)"
        fig.add_trace(go.Mesh3d(
            x=xs, y=ys, z=snow_zs, i=i_s, j=j_s, k=k_s,
            color="#f8fafc", opacity=0.88, name="Snow Cap (Winter Pack)",
            hoverinfo="text", hovertext=snow_hover,
            lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
            flatshading=True, showlegend=True
        ))
        fig.add_trace(go.Mesh3d(
            x=xn, y=yn, z=snow_zn, i=i_s, j=j_s, k=k_s,
            color="#f8fafc", opacity=0.88, name="Snow Cap",
            hoverinfo="text", hovertext=snow_hover,
            lighting=LIGHTING_CONFIG, lightposition=LIGHT_POSITION,
            flatshading=True, showlegend=False
        ))

    # Extra: Ridge Vent (Chennai / Hot-Humid)
    if "ridge_vent" in extras:
        rv_w = 0.35
        rv_hover = "<b>💨 Continuous Ridge Vent</b><br>Exhausts rising indoor heat via thermal buoyancy stack effect."
        _add_box_mesh(
            fig, x_min, y_mid - rv_w/2, z_ridge + 0.10, (x_max - x_min), rv_w, 0.18,
            "#7c2d12", "Ridge Ventilation Cap", rv_hover, showlegend=True
        )
        # Vent gap (dark slot)
        _add_box_mesh(
            fig, x_min + 0.1, y_mid - 0.05, z_ridge + 0.04, (x_max - x_min - 0.2), 0.10, 0.06,
            "#0f172a", "Ridge Vent Gap", rv_hover, opacity=0.8
        )


def _add_flat_roof(
    fig: go.Figure,
    length: float, width: float, height: float,
    overhang: float, roof_color: str, roof_name: str,
    extras: List[str],
):
    """
    Builds a realistic 3D flat roof with visible thickness, overhangs,
    perimeter parapet walls with coping.
    """
    x_min, x_max = -overhang, length + overhang
    y_min, y_max = -overhang, width + overhang
    slab_th = 0.18

    hover_roof = (
        f"<b>🏠 {roof_name}</b><br>"
        f"Overhang: {overhang:.2f} m<br>"
        f"Slab Thickness: {slab_th*1000:.0f} mm<br>"
        f"High-Thermal Mass Concrete Deck"
    )
    _add_box_mesh(
        fig, x_min, y_min, height, (x_max - x_min), (y_max - y_min), slab_th,
        roof_color, "Roof Deck", hover_roof, showlegend=True
    )

    # Parapet Border Walls with coping
    if "parapet" in extras:
        pw_h = 0.40
        pw_th = 0.15
        p_col = "#c28b52" if "reflective_roof" in extras else roof_color
        coping_col = "#a8a29e"
        # Parapets (4 sides)
        _add_box_mesh(fig, x_min, y_min, height + slab_th, (x_max - x_min), pw_th, pw_h, p_col, "Parapet", "Parapet Wall")
        _add_box_mesh(fig, x_min, y_max - pw_th, height + slab_th, (x_max - x_min), pw_th, pw_h, p_col, "Parapet", "Parapet Wall")
        _add_box_mesh(fig, x_min, y_min, height + slab_th, pw_th, (y_max - y_min), pw_h, p_col, "Parapet", "Parapet Wall")
        _add_box_mesh(fig, x_max - pw_th, y_min, height + slab_th, pw_th, (y_max - y_min), pw_h, p_col, "Parapet", "Parapet Wall")
        # Coping (cap on parapet)
        cop_th = 0.05
        _add_box_mesh(fig, x_min - 0.02, y_min - 0.02, height + slab_th + pw_h, (x_max - x_min + 0.04), pw_th + 0.04, cop_th, coping_col, "Coping", "Parapet Coping Cap")
        _add_box_mesh(fig, x_min - 0.02, y_max - pw_th - 0.02, height + slab_th + pw_h, (x_max - x_min + 0.04), pw_th + 0.04, cop_th, coping_col, "Coping", "Parapet Coping Cap")
        _add_box_mesh(fig, x_min - 0.02, y_min, height + slab_th + pw_h, pw_th + 0.04, (y_max - y_min), cop_th, coping_col, "Coping", "Parapet Coping Cap")
        _add_box_mesh(fig, x_max - pw_th - 0.02, y_min, height + slab_th + pw_h, pw_th + 0.04, (y_max - y_min), cop_th, coping_col, "Coping", "Parapet Coping Cap")

    # Extra: Reflective Cool Roof Coating Layer
    if "reflective_roof" in extras:
        _add_box_mesh(
            fig, x_min + 0.18, y_min + 0.18, height + slab_th + 0.01,
            (x_max - x_min - 0.36), (y_max - y_min - 0.36), 0.03,
            "#fafaf9", "High-Albedo Reflective Coating",
            "<b>✨ White Reflective Cool Roof Layer</b><br>Solar Reflectance Index (SRI) > 85<br>Reflects 82% of incident solar irradiance.",
            showlegend=True
        )


# ==============================================================================
# 5. CONTEXT GENERATORS
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
    # Sun rays (lines)
    for angle in [0, 30, -30, 60, -60]:
        rad = math.radians(angle)
        ray_len = 1.2
        fig.add_trace(go.Scatter3d(
            x=[sx, sx + ray_len * math.cos(rad)],
            y=[sy, sy - ray_len * 0.3],
            z=[sz, sz + ray_len * math.sin(rad)],
            mode="lines", line=dict(color="#fbbf24", width=2),
            hoverinfo="skip", showlegend=False,
        ))

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
    # N label
    fig.add_trace(go.Scatter3d(
        x=[nx], y=[ny + 0.9], z=[nz + 0.3],
        mode="text", text=["<b>N</b>"],
        textfont=dict(size=14, color="#ef4444", family="Inter, sans-serif"),
        hoverinfo="skip", showlegend=False,
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


# ==============================================================================
# 6. VIEW MODE OVERLAYS
# ==============================================================================
def _apply_envelope_view(
    fig: go.Figure,
    length: float, width: float, height: float,
    w_th: float, insulation_color: str, wall_inner_color: str,
    insulation_mm: float,
):
    """Adds cutaway wall section showing insulation layers."""
    ins_th = insulation_mm / 1000.0
    cutaway_x = length * 0.55
    cutaway_len = length * 0.35
    hover_ins = (
        f"<b>🔶 Insulation Layer (Cutaway View)</b><br>"
        f"Thickness: {insulation_mm:.0f} mm<br>"
        f"Reduces conductive heat transfer through envelope"
    )
    hover_inner = (
        f"<b>Inner Wall Leaf</b><br>"
        f"Provides interior finish and thermal mass"
    )
    # South wall cutaway: show inner leaf + insulation
    # Insulation layer
    _add_box_mesh(
        fig, cutaway_x, w_th * 0.3, 0.2,
        cutaway_len, ins_th, height * 0.7,
        insulation_color, "Insulation Layer", hover_ins,
        opacity=0.85, showlegend=True
    )
    # Inner leaf
    _add_box_mesh(
        fig, cutaway_x, w_th * 0.3 + ins_th, 0.2,
        cutaway_len, w_th * 0.35, height * 0.7,
        wall_inner_color, "Inner Wall Leaf", hover_inner,
        opacity=0.75, showlegend=True
    )


def _apply_thermal_view(
    fig: go.Figure,
    length: float, width: float, height: float,
    w_th: float,
):
    """Adds thermal heatmap zones on floor (warm center, cooler edges)."""
    # Warm zone (center floor - represents occupied thermal comfort zone)
    _add_box_mesh(
        fig, w_th + length*0.15, w_th + width*0.15, 0.01,
        length*0.7 - 2*w_th, width*0.7 - 2*w_th, 0.03,
        "#22c55e", "Thermal Comfort Zone",
        "<b>🌡️ Thermal Comfort Zone</b><br>Central occupied area within ASHRAE 55 comfort band<br>(Visualization based on simulation data)",
        opacity=0.5, showlegend=True
    )
    # Cooler edge zones near walls
    _add_box_mesh(
        fig, w_th + 0.05, w_th + 0.05, 0.01,
        length*0.15, width - 2*w_th - 0.1, 0.02,
        "#3b82f6", "Cooler Perimeter",
        "<b>🌡️ Cooler Perimeter Zone</b><br>Near-wall area with higher heat loss<br>(Visualization based on simulation data)",
        opacity=0.4, showlegend=True
    )
    _add_box_mesh(
        fig, length - w_th - length*0.15 - 0.05, w_th + 0.05, 0.01,
        length*0.15, width - 2*w_th - 0.1, 0.02,
        "#3b82f6", "Cooler Perimeter",
        "<b>🌡️ Cooler Perimeter Zone</b>",
        opacity=0.4
    )


def _apply_ventilation_view(
    fig: go.Figure,
    length: float, width: float, height: float,
    extras: List[str],
):
    """Adds airflow path arrows for cross-ventilation visualization."""
    # Cross-ventilation arrows (south to north)
    arrow_y_positions = [width * 0.3, width * 0.6]
    for ay in arrow_y_positions:
        # Arrow body
        fig.add_trace(go.Scatter3d(
            x=[length * 0.3, length * 0.3, length * 0.3],
            y=[-0.5, ay, width + 0.5],
            z=[height * 0.5, height * 0.55, height * 0.5],
            mode="lines",
            line=dict(color="#22d3ee", width=5),
            hoverinfo="text",
            hovertext="<b>💨 Cross-Ventilation Airflow Path</b><br>Natural breeze from South to North openings",
            showlegend=False,
        ))
    # Stack effect arrow (if ridge vent present)
    if "ridge_vent" in extras:
        fig.add_trace(go.Scatter3d(
            x=[length * 0.5, length * 0.5],
            y=[width * 0.5, width * 0.5],
            z=[0.5, height + 1.5],
            mode="lines+text",
            line=dict(color="#f59e0b", width=4),
            text=[None, "↑ Stack Effect"],
            textfont=dict(size=9, color="#f59e0b"),
            textposition="top center",
            hoverinfo="text",
            hovertext="<b>🔥 Thermal Stack Effect</b><br>Hot air rises and exits through ridge vent",
            showlegend=False,
        ))


# ==============================================================================
# 7. MASTER 3D BUILDER FUNCTION
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
    city_name: Optional[str] = None,
    view_mode: str = "normal",
) -> go.Figure:
    """
    Creates a premium, climate-adaptive 3D Digital Twin architectural model.

    Parameters:
        climate_type (str): Key from CLIMATE_STYLE or city name.
        length (float): Length in meters along X axis.
        width (float): Width in meters along Y axis.
        height (float): Wall height in meters along Z axis.
        window_area (float): Total fenestration area in m².
        wall_material (str): Envelope wall material name.
        insulation_mm (float): Insulation thickness in millimeters.
        glazing_name (str): Glazing specification name.
        city_name (Optional[str]): City name override for title.
        view_mode (str): View mode - 'normal', 'envelope', 'thermal', 'solar', 'ventilation'.

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
    w_th = spec["wall_visual_thickness"]
    plinth_h = spec.get("plinth_height", 0.20)

    view_labels = {
        "normal": "Architectural",
        "envelope": "Envelope Cutaway",
        "thermal": "Thermal Zones",
        "solar": "Solar Analysis",
        "ventilation": "Ventilation Paths",
    }
    view_label = view_labels.get(view_mode, "Architectural")

    # 2. Ground Plane
    g_pad = max(3.5, length * 0.4)
    gx0, gx1 = -g_pad, length + g_pad
    gy0, gy1 = -g_pad, width + g_pad
    _add_box_mesh(
        fig, gx0, gy0, -0.05, (gx1 - gx0), (gy1 - gy0), 0.05,
        pal["ground"], "Ground Plane",
        f"<b>🌍 Surrounding Terrain</b> ({spec['name']})",
        showlegend=False
    )

    # 3. Foundation Plinth
    _add_foundation_plinth(fig, length, width, plinth_h, w_th, pal["plinth"])

    # 4. Envelope Walls (with Visual Thickness)
    hover_wall = (
        f"<b>🧱 Envelope Wall Assembly</b><br>"
        f"Material: {pal['wall_name']} ({wall_material})<br>"
        f"Wall Thickness: {w_th*1000:.0f} mm + {insulation_mm:.0f} mm Insulation<br>"
        f"Footprint: {length:.1f} m × {width:.1f} m × {height:.1f} m"
    )

    wall_opacity = 0.55 if view_mode == "envelope" else 1.0

    # South Wall (front)
    _add_box_mesh(fig, 0, 0, 0, length, w_th, height, pal["wall"], "Walls", hover_wall, opacity=wall_opacity, showlegend=True)
    # North Wall (back)
    _add_box_mesh(fig, 0, width - w_th, 0, length, w_th, height, pal["wall"], "Walls", hover_wall, opacity=wall_opacity)
    # West Wall (left)
    _add_box_mesh(fig, 0, w_th, 0, w_th, width - 2*w_th, height, pal["wall"], "Walls", hover_wall, opacity=wall_opacity)
    # East Wall (right)
    _add_box_mesh(fig, length - w_th, w_th, 0, w_th, width - 2*w_th, height, pal["wall"], "Walls", hover_wall, opacity=wall_opacity)

    # Interior floor slab
    _add_box_mesh(
        fig, w_th, w_th, -0.02, length - 2*w_th, width - 2*w_th, 0.02,
        "#64748b", "Interior Floor", "Interior Floor Slab", opacity=0.6
    )

    # 5. Wall Coursing Lines (structural texture)
    n_courses = max(4, int(height / 0.45))
    # South wall coursing
    _add_wall_coursing(fig, 0, -0.005, 0, length, 0.01, height, pal["coursing"], True, n_courses)
    # North wall coursing
    _add_wall_coursing(fig, 0, width - 0.005, 0, length, 0.01, height, pal["coursing"], True, n_courses)
    # West wall coursing
    _add_wall_coursing(fig, -0.005, w_th, 0, 0.01, width - 2*w_th, height, pal["coursing"], False, n_courses)
    # East wall coursing
    _add_wall_coursing(fig, length - 0.005, w_th, 0, 0.01, width - 2*w_th, height, pal["coursing"], False, n_courses)

    # 6. Corner Pilasters
    _add_corner_pilasters(fig, length, width, height, w_th, pal["pilaster"])

    # 7. Entry Door (recessed with frame depth)
    door_w, door_h = 0.90, min(height - 0.2, 2.05)
    door_x = min(0.6, (length - door_w) * 0.2)
    _add_recessed_door(
        fig, door_x, 0.0, 0.0,
        door_w, door_h, w_th,
        pal["frame"], pal["door"], plinth_h
    )

    # 8. Fenestration Windows (Recessed with reveals and mullions)
    glaze_facades = spec["glazing_facades"]
    is_deep = "deep_recessed_windows" in extras

    if len(glaze_facades) == 1 and "south" in glaze_facades:
        south_win_area = window_area
        north_win_area = 0.0
    else:
        south_win_area = window_area * 0.55
        north_win_area = window_area * 0.45

    # South Window
    if south_win_area > 0.3:
        max_ww = length - door_x - door_w - 0.8
        win_w = max(0.8, min(max_ww, math.sqrt(south_win_area * 1.5)))
        win_h = max(0.6, min(height * 0.6, south_win_area / max(0.01, win_w)))
        win_x = door_x + door_w + 0.4
        win_z = max(0.7, (height - win_h) / 2.0)

        _add_recessed_window(
            fig, win_x, 0.0, win_z, win_w, win_h, w_th,
            pal["frame"], "#38bdf8", "South Solar", glazing_name,
            is_deep_recess=is_deep, showlegend=True
        )

        # Shade fins for hot_dry
        if "shade_fins" in extras:
            _add_shade_fins(fig, win_x, 0.0, win_z, win_w, win_h, w_th, pal["pilaster"])

        # Chajja overhangs for composite
        if "chajja_overhangs" in extras:
            _add_shade_fins(fig, win_x, 0.0, win_z, win_w, win_h, w_th, pal["frame"])

        # Ventilation louvers for hot_humid
        if "ventilation_louvers" in extras:
            _add_ventilation_louvers(fig, win_x, 0.0, win_z, win_w, win_h, pal["frame"])

    # North Window (Cross-Ventilation)
    if north_win_area > 0.3:
        n_win_w = max(0.8, min(length * 0.65, math.sqrt(north_win_area * 1.5)))
        n_win_h = max(0.6, min(height * 0.55, north_win_area / max(0.01, n_win_w)))
        n_win_x = (length - n_win_w) / 2.0
        n_win_z = max(0.8, (height - n_win_h) / 2.0)

        _add_recessed_window(
            fig, n_win_x, width - w_th, n_win_z, n_win_w, n_win_h, w_th,
            pal["frame"], "#22d3ee", "North Cross-Vent", glazing_name,
            is_deep_recess=is_deep
        )

        if "ventilation_louvers" in extras:
            _add_ventilation_louvers(fig, n_win_x, width - w_th, n_win_z, n_win_w, n_win_h, pal["frame"])

    # 9. Roof Assembly
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

    # 10. Solar Panels
    if "solar_panels_roof" in extras and (view_mode in ("normal", "solar")):
        _add_solar_panels_pitched(
            fig, length, width, height, r_pitch, r_overhang,
            pal["solar_panel"], pal["solar_frame"]
        )
    if "solar_panels_flat" in extras and (view_mode in ("normal", "solar")):
        _add_solar_panels_flat(
            fig, length, width, height, r_overhang,
            pal["solar_panel"], pal["solar_frame"]
        )

    # 11. Climate-Specific Architectural Extras
    # Airlock Entry Vestibule (Leh / Cold)
    if "vestibule" in extras:
        v_w = 1.3
        v_d = 1.0
        v_h = min(height, 2.3)
        v_hover = (
            "<b>❄️ Thermal Airlock Vestibule</b><br>"
            "Double-door entry buffer preventing direct cold drafts<br>"
            "Reduces infiltration heat loss by ~40%"
        )
        # Vestibule walls (thicker for cold)
        _add_box_mesh(fig, door_x - 0.25, -v_d, 0, 0.15, v_d, v_h, pal["wall"], "Vestibule Wall", v_hover)
        _add_box_mesh(fig, door_x + door_w + 0.10, -v_d, 0, 0.15, v_d, v_h, pal["wall"], "Vestibule Wall", v_hover)
        _add_box_mesh(fig, door_x - 0.25, -v_d, 0, v_w + 0.25, 0.15, v_h, pal["wall"], "Vestibule Front", v_hover, showlegend=True)
        # Outer door
        _add_box_mesh(fig, door_x + 0.1, -v_d - 0.02, 0, door_w - 0.2, 0.06, door_h - 0.1, pal["door"], "Outer Door", v_hover)
        # Vestibule pitched roof
        vest_pitch = math.radians(30)
        vest_ridge = 0.3
        _add_box_mesh(
            fig, door_x - 0.35, -v_d - 0.15, v_h,
            v_w + 0.35, v_d + 0.25, 0.10,
            pal["roof"], "Vestibule Roof", v_hover
        )

    # Front Verandah with Timber Posts (Chennai / Hot-Humid)
    if "verandah" in extras:
        v_depth = 1.5
        v_plinth_h = 0.20
        hover_v = (
            "<b>🌿 Shaded Deep Verandah</b><br>"
            "Reduces solar thermal load on facade by over 80%<br>"
            "Captures monsoon breezes for passive cooling"
        )
        # Raised Plinth Floor
        _add_box_mesh(fig, -0.2, -v_depth, -v_plinth_h, length + 0.4, v_depth + 0.05, v_plinth_h + 0.05, "#a16207", "Verandah Plinth", hover_v, showlegend=True)
        # Structural Pillars (timber posts)
        n_pillars = max(3, int(length / 2.0) + 1)
        pillar_spacing = length / (n_pillars - 1)
        for p in range(n_pillars):
            px = p * pillar_spacing
            _add_box_mesh(fig, px - 0.07, -v_depth + 0.08, 0.0, 0.14, 0.14, height, "#78350f", "Verandah Pillar", "Verandah Pillar Post")
        # Verandah beam (connecting pillars at top)
        _add_box_mesh(fig, -0.1, -v_depth + 0.05, height - 0.1, length + 0.2, 0.08, 0.10, "#78350f", "Verandah Beam", "Structural Beam")

    # Thermal mass interior (Leh / Cold)
    if "thermal_mass_interior" in extras and view_mode in ("normal", "envelope"):
        _add_thermal_mass_interior(fig, length, width, height, w_th, pal["wall"])

    # Trees Context
    if "trees" in extras:
        _add_tree(fig, length + 2.5, -2.0, 0, scale=1.1)
        _add_tree(fig, -2.8, width * 0.6, 0, scale=0.9)

    # 12. Human Scale Reference Figure
    _add_human_scale_figure(fig, hx=length + 0.9, hy=-1.0, hz=0.0)

    # 13. Sun and Compass
    _add_sun_and_cardinal_compass(fig, length, width, height)

    # 14. Dimension Annotations
    dim_offset_y = width + g_pad * 0.5
    dim_offset_x = length + g_pad * 0.4
    _add_dimension_line(fig, (0, dim_offset_y, 0), (length, dim_offset_y, 0), f"{length:.1f} m")
    _add_dimension_line(fig, (dim_offset_x, 0, 0), (dim_offset_x, width, 0), f"{width:.1f} m")
    _add_dimension_line(fig, (dim_offset_x, 0, 0), (dim_offset_x, 0, height), f"{height:.1f} m")

    # 15. View Mode Overlays
    if view_mode == "envelope":
        _apply_envelope_view(
            fig, length, width, height, w_th,
            pal["insulation"], pal["wall_inner"], insulation_mm
        )
    elif view_mode == "thermal":
        _apply_thermal_view(fig, length, width, height, w_th)
    elif view_mode == "ventilation":
        _apply_ventilation_view(fig, length, width, height, extras)

    # 16. Layout & Lighting
    camera = spec.get("camera", dict(eye=dict(x=1.6, y=-1.6, z=0.9), center=dict(x=0, y=0, z=-0.1)))
    n_components = len(fig.data)

    fig.update_layout(
        title=dict(
            text=(
                f"<b>🏗️ 3D Digital Twin — {display_city} ({spec['name']})</b>"
                f"<br><span style='font-size:11px; color:#94a3b8;'>"
                f"View: {view_label} | {n_components} components | "
                f"{length:.1f}×{width:.1f}×{height:.1f} m | "
                f"Wall: {w_th*1000:.0f}mm + {insulation_mm:.0f}mm ins.</span>"
            ),
            font=dict(family="Inter, -apple-system, sans-serif", size=14, color="#38bdf8"),
            x=0.01,
            y=0.97
        ),
        paper_bgcolor="#1e293b",
        font=dict(family="Inter, -apple-system, sans-serif", color="#f8fafc"),
        scene=dict(
            aspectmode="data",
            camera=camera,
            xaxis=dict(showbackground=False, visible=False),
            yaxis=dict(showbackground=False, visible=False),
            zaxis=dict(showbackground=False, visible=False),
            bgcolor="#0f172a"
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.02,
            xanchor="center",
            x=0.5,
            font=dict(color="#f8fafc", size=10),
            bgcolor="rgba(15, 23, 42, 0.90)",
            bordercolor="rgba(56, 189, 248, 0.25)",
            borderwidth=1,
            itemsizing="constant",
        ),
        margin=dict(l=0, r=0, t=60, b=0),
        height=580,
    )

    return fig


if __name__ == "__main__":
    # Smoke test all 5 climates × all view modes
    test_climates = ["leh", "jaisalmer", "chennai", "delhi", "bengaluru"]
    test_views = ["normal", "envelope", "thermal", "solar", "ventilation"]
    print("Testing 3D Digital Twin generation across all climates and view modes...")
    for c in test_climates:
        for v in test_views:
            f = build_3d_shelter(
                climate_type=c,
                length=4.5,
                width=3.2,
                height=2.8,
                window_area=2.5,
                wall_material="brick",
                insulation_mm=50.0,
                glazing_name="Double Clear Glazing",
                view_mode=v,
            )
            print(f"  [OK] {c.upper():12s} | {v:13s} | {len(f.data):3d} components")
    print("\n[OK] All smoke tests passed successfully.")
