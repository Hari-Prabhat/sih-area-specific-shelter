"""
THERMOSHELTER AI - Centralized Plotly Theme & Chart Styling Engine
==================================================================
Universal, high-contrast, theme-safe styling for Plotly figures in both
Dark and Light modes. Ensures 100% readability of titles, axes, legends,
annotations, hover labels, and tick values across desktop and mobile screens.
"""

from typing import Optional
import plotly.graph_objects as go

# ==============================================================================
# COLOR PALETTES & CONSTANTS
# ==============================================================================
FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

# Dark Theme Tokens (Deep Slate / Midnight UI)
DARK_PAPER_BG       = "#1e293b"      # Slate-800 card container background
DARK_PLOT_BG        = "#0f172a"      # Slate-900 midnight plot area
DARK_GRID_COLOR     = "rgba(148, 163, 184, 0.16)" # Subdued grid
DARK_ZEROLINE_COLOR = "rgba(148, 163, 184, 0.35)" # Visible zero line
DARK_TEXT_PRIMARY   = "#f8fafc"      # Pure white-slate for ticks and text
DARK_TEXT_MUTED     = "#94a3b8"      # Slate-400 for axis titles
DARK_ACCENT_CYAN    = "#38bdf8"      # Bright sky cyan for figure titles
DARK_LEGEND_BG      = "rgba(15, 23, 42, 0.88)"
DARK_LEGEND_BORDER  = "rgba(56, 189, 248, 0.30)"
DARK_HOVER_BG       = "#0f172a"
DARK_HOVER_BORDER   = "#38bdf8"

# Light Theme Tokens (Crisp Clean Presentation)
LIGHT_PAPER_BG       = "#ffffff"
LIGHT_PLOT_BG        = "#f8fafc"
LIGHT_GRID_COLOR     = "rgba(100, 116, 139, 0.15)"
LIGHT_ZEROLINE_COLOR = "rgba(100, 116, 139, 0.35)"
LIGHT_TEXT_PRIMARY   = "#0f172a"     # Dark slate
LIGHT_TEXT_MUTED     = "#475569"     # Medium slate
LIGHT_ACCENT_CYAN    = "#0284c7"     # Deep sky blue
LIGHT_LEGEND_BG      = "rgba(255, 255, 255, 0.92)"
LIGHT_LEGEND_BORDER  = "rgba(2, 132, 199, 0.30)"
LIGHT_HOVER_BG       = "#ffffff"
LIGHT_HOVER_BORDER   = "#0284c7"

# Standard Distinct Trace Colors
SERIES_COLORS = {
    "outdoor_temp": "#38bdf8",     # Cyan
    "indoor_temp": "#f87171",      # Salmon Coral
    "comfort_band": "rgba(34, 197, 94, 0.18)",
    "comfort_line": "#22c55e",     # Green
    "solar_irradiance": "#f59e0b", # Amber
    "solar_power": "#fbbf24",      # Yellow Amber
    "solar_gain": "#f43f5e",       # Rose Red
    "wall_loss": "#a78bfa",        # Violet
    "roof_loss": "#f472b6",        # Pink
    "floor_loss": "#c084fc",       # Purple
    "glazing_loss": "#22d3ee",     # Aqua
    "ventilation_loss": "#94a3b8",  # Slate
    "radiation_loss": "#60a5fa",    # Blue
    "net_heat_flow": "#34d399",    # Emerald
    "baseline_temp": "#ef4444",    # Crimson
    "optimized_temp": "#10b981",   # Emerald Green
}


def apply_chart_theme(
    fig: go.Figure,
    title_text: str = "",
    height: int = 400,
    show_legend: bool = True,
    is_dark: bool = True,
    margin: Optional[dict] = None,
) -> go.Figure:
    """
    Applies the authoritative theme to any Plotly Figure.
    
    Guarantees:
      - High-contrast visible text in both Dark and Light modes.
      - Styled axis titles and tick marks with clear numeric font sizing.
      - Styled hover cards with border highlights.
      - Neatly styled legends with translucent backgrounds.
    """
    if is_dark:
        paper_bg     = DARK_PAPER_BG
        plot_bg      = DARK_PLOT_BG
        text_primary = DARK_TEXT_PRIMARY
        text_muted   = DARK_TEXT_MUTED
        accent_color = DARK_ACCENT_CYAN
        grid_color   = DARK_GRID_COLOR
        zero_color   = DARK_ZEROLINE_COLOR
        leg_bg       = DARK_LEGEND_BG
        leg_border   = DARK_LEGEND_BORDER
        hov_bg       = DARK_HOVER_BG
        hov_border   = DARK_HOVER_BORDER
        hov_text     = "#ffffff"
    else:
        paper_bg     = LIGHT_PAPER_BG
        plot_bg      = LIGHT_PLOT_BG
        text_primary = LIGHT_TEXT_PRIMARY
        text_muted   = LIGHT_TEXT_MUTED
        accent_color = LIGHT_ACCENT_CYAN
        grid_color   = LIGHT_GRID_COLOR
        zero_color   = LIGHT_ZEROLINE_COLOR
        leg_bg       = LIGHT_LEGEND_BG
        leg_border   = LIGHT_LEGEND_BORDER
        hov_bg       = LIGHT_HOVER_BG
        hov_border   = LIGHT_HOVER_BORDER
        hov_text     = "#0f172a"

    default_margin = dict(l=50, r=40, t=55, b=45) if margin is None else margin

    fig.update_layout(
        title=dict(
            text=f"<b>{title_text}</b>" if title_text else "",
            font=dict(family=FONT_FAMILY, size=15, color=accent_color),
            x=0.01,
            y=0.97
        ),
        paper_bgcolor=paper_bg,
        plot_bgcolor=plot_bg,
        font=dict(family=FONT_FAMILY, color=text_primary, size=12),
        hoverlabel=dict(
            bgcolor=hov_bg,
            font_size=12,
            font_family=FONT_FAMILY,
            font_color=hov_text,
            bordercolor=hov_border
        ),
        margin=default_margin,
        height=height,
    )

    if show_legend:
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1.0,
                font=dict(color=text_primary, size=11, family=FONT_FAMILY),
                bgcolor=leg_bg,
                bordercolor=leg_border,
                borderwidth=1,
            )
        )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=grid_color,
        zeroline=False,
        tickfont=dict(color=text_primary, size=11, family=FONT_FAMILY),
        title_font=dict(color=text_muted, size=12, family=FONT_FAMILY)
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=grid_color,
        zeroline=True,
        zerolinecolor=zero_color,
        tickfont=dict(color=text_primary, size=11, family=FONT_FAMILY),
        title_font=dict(color=text_muted, size=12, family=FONT_FAMILY)
    )

    return fig
