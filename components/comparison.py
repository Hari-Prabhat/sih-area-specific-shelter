"""
THERMOSHELTER AI - Comparative Benchmarking & Archetype Evaluation
==================================================================
Provides real, calculated comparative analytics between:
  1. Conventional Baseline vs AI-Optimized Shelter.
  2. Multiple Geometric Archetypes (under identical floor area).
"""

from typing import Any, Dict, List
import streamlit as st
import pandas as pd

from components.charts import plot_baseline_vs_optimized
from services.simulation_service import run_simulation, SHELTER_MODELS
from services.recommender import get_recommendation


from i18n import t


def render_baseline_vs_optimized_view(
    comp_city: str,
    comp_people: int,
    comp_home_type: str,
    is_dark: bool = True,
) -> None:
    """
    Renders Baseline vs AI-Optimized comparative study with dynamic calculations.
    """
    st.subheader(t("comp_studio_title"))
    st.caption(t("comp_studio_caption"))

    # 1. Run or retrieve baseline and optimized results
    # Use session_state to cache simulation so it loads immediately
    cache_key = f"comp_{comp_city}_{comp_people}_{comp_home_type}"
    
    if cache_key not in st.session_state:
        with st.spinner(t("comp_spinner", city=comp_city.upper())):
            rec_comp = get_recommendation(
                city=comp_city,
                people=comp_people,
                home_type=comp_home_type,
                n_trials=35,
            )
            geo_c = rec_comp["geometry"]
            mats_c = rec_comp["materials"]

            # Baseline: Uninsulated masonry for permanent, uninsulated thin panel for temporary
            base_mat = "brick" if comp_home_type == "Permanent" else "wood"
            sim_baseline = run_simulation(
                city=comp_city,
                length=geo_c["length_m"],
                width=geo_c["width_m"],
                height=geo_c["height_m"],
                wall_material=base_mat,
                insulation_thickness_m=0.0,
                window_area=2.0,
                glazing="single_clear",
                orientation="south",
                occupants=comp_people,
                hours_to_simulate=168,
            )

            sim_opt = rec_comp["simulation_result"]

            st.session_state[cache_key] = {
                "baseline": sim_baseline,
                "optimized": sim_opt,
                "rec": rec_comp,
            }

    data = st.session_state[cache_key]
    s_base = data["baseline"]
    s_opt = data["optimized"]
    r_info = data["rec"]

    # Comparative Delta Metrics (Calculated Dynamically)
    st.markdown(f"### {t('comp_impact_title')}")
    d1, d2, d3, d4 = st.columns(4)

    base_dh = s_base["discomfort_degree_hours"]
    opt_dh = s_opt["discomfort_degree_hours"]
    dh_reduction = ((base_dh - opt_dh) / max(0.01, base_dh)) * 100.0

    base_loss = s_base["total_heat_loss_kwh"]
    opt_loss = s_opt["total_heat_loss_kwh"]
    loss_reduction = ((base_loss - opt_loss) / max(0.01, base_loss)) * 100.0

    comfort_hrs_delta = s_opt["comfort_hours"] - s_base["comfort_hours"]
    comfort_pct_delta = s_opt["comfort_percentage"] - s_base["comfort_percentage"]

    d1.metric(
        t("metric_comfort_hours"),
        f"{s_opt['comfort_hours']:.0f} h / 168 h",
        delta=t("comp_delta_baseline", val=comfort_hrs_delta),
    )
    d2.metric(
        t("metric_comfort_pct"),
        f"{s_opt['comfort_percentage']:.1f} %",
        delta=f"{comfort_pct_delta:+.1f} %",
    )
    d3.metric(
        t("spec_discomfort"),
        f"{opt_dh:.1f} °C·h",
        delta=t("comp_delta_discomfort", val=dh_reduction),
        delta_color="inverse",
    )
    d4.metric(
        t("metric_total_loss"),
        f"{opt_loss:.1f} kWh",
        delta=t("comp_delta_loss", val=loss_reduction),
        delta_color="inverse",
    )

    st.markdown("---")

    # Overlaid Temperature Response Curves
    st.markdown(f"### {t('comp_curves_title')}")
    st.plotly_chart(
        plot_baseline_vs_optimized(s_base, s_opt, is_dark=is_dark),
        use_container_width=True,
    )

    # Detailed Side-by-Side Specifications Comparison Table
    st.markdown(f"### {t('comp_specs_title')}")
    base_wall_name = t("base_wall_perm") if comp_home_type == "Permanent" else t("base_wall_temp")
    comp_df = pd.DataFrame({
        t("comp_col_spec_param"): [
            t("spec_wall_assembly"),
            t("spec_insulation"),
            t("spec_wall_u"),
            t("spec_roof_u"),
            t("spec_glazing"),
            t("spec_fenestration"),
            t("spec_orientation"),
            t("spec_comfort_hours"),
            t("spec_discomfort"),
            t("spec_weekly_loss"),
        ],
        t("comp_col_baseline"): [
            base_wall_name,
            t("uninsulated_label"),
            f"{s_base['u_values']['wall_u']:.3f} W/m²K",
            f"{s_base['u_values']['roof_u']:.3f} W/m²K",
            t("single_glaze_label"),
            "2.00 m²",
            f"South {t('card_orient_facade')}",
            f"{s_base['comfort_hours']:.0f} / 168 h ({s_base['comfort_percentage']:.1f}%)",
            f"{s_base['discomfort_degree_hours']:.1f} °C·h",
            f"{s_base['total_heat_loss_kwh']:.1f} kWh",
        ],
        t("comp_col_optimized"): [
            r_info.get("optimal_wall_material", "brick").title() + t("puf_layer_suffix"),
            f"{r_info['optimal_insulation_mm']:.0f}" + t("puf_core_suffix"),
            f"{s_opt['u_values']['wall_u']:.3f} W/m²K",
            f"{s_opt['u_values']['roof_u']:.3f} W/m²K",
            r_info.get("optimal_glazing_name", "Double Clear"),
            f"{r_info['optimal_window_area_m2']:.2f} m²",
            f"{r_info.get('optimal_orientation', 'south').title()} {t('card_orient_facade')}",
            f"{s_opt['comfort_hours']:.0f} / 168 h ({s_opt['comfort_percentage']:.1f}%)",
            f"{s_opt['discomfort_degree_hours']:.1f} °C·h",
            f"{s_opt['total_heat_loss_kwh']:.1f} kWh",
        ],
    })
    st.dataframe(comp_df, use_container_width=True)
