"""
THERMOSHELTER AI - Recommendations & Envelope Specifications UI
===============================================================
Renders the optimal envelope specifications, multi-candidate ranked optimization
results, and explainable design rationale backed by computed numerical evidence.
"""

from typing import Any, Dict, List
import streamlit as st
import pandas as pd


from i18n import t


def render_envelope_specifications(
    rec: Dict[str, Any],
    sim_res: Dict[str, Any],
    home_type: str = "Permanent",
) -> None:
    """
    Renders the 6 technical envelope specification cards.
    """
    geo = rec["geometry"]
    mats = rec["materials"]
    u_vals = sim_res["u_values"]

    st.markdown(f"### {t('rec_sec4_title')}")
    r1, r2, r3 = st.columns(3)

    mass_str = t("card_wall_mass_high") if home_type == "Permanent" else t("card_wall_mass_light")

    with r1:
        st.markdown(
            f"""<div class='card'>
<h4>{t('card_wall_title')}</h4>
<p><b>{t('card_wall_material')}:</b> {mats['wall_material_name']}</p>
<p><b>{t('card_wall_u')}:</b> <span class='metric-badge'>{u_vals.get('wall_u', 0.50):.3f} W/m²K</span></p>
<p><b>{t('card_wall_r')}:</b> {u_vals.get('wall_r_total', 2.0):.2f} m²K/W</p>
<p><b>{t('card_wall_mass')}:</b> {mass_str}</p>
</div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class='card'>
<h4>{t('card_roof_title')}</h4>
<p><b>{t('card_roof_design')}:</b> {mats['roof_material']}</p>
<p><b>{t('card_roof_u')}:</b> <span class='metric-badge'>{u_vals.get('roof_u', 0.40):.3f} W/m²K</span></p>
<p><b>{t('card_roof_r')}:</b> {u_vals.get('roof_r_total', 2.5):.2f} m²K/W</p>
<p><b>{t('card_roof_profile')}:</b> {mats['roof_type'].title()} {t('roof_suffix')}</p>
</div>""",
            unsafe_allow_html=True,
        )

    with r2:
        st.markdown(
            f"""<div class='card'>
<h4>{t('card_ins_title')}</h4>
<p><b>{t('card_ins_type')}:</b> {mats['insulation_type']}</p>
<p><b>{t('card_ins_opt_thickness')}:</b> <span class='metric-badge'>{rec['optimal_insulation_mm']:.1f} mm</span></p>
<p><b>{t('card_ins_core_k')}:</b> {t('card_ins_core_detail')}</p>
<p><b>{t('card_ins_added_r')}:</b> {u_vals.get('wall_r_total', 2.0) - u_vals.get('wall_base_r', 0.5):.2f} m²K/W</p>
</div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class='card'>
<h4>{t('card_glazing_title')}</h4>
<p><b>{t('card_glazing_spec')}:</b> {rec.get('optimal_glazing_name', mats['glazing_type'])}</p>
<p><b>{t('card_glazing_area')}:</b> <span class='metric-badge'>{rec['optimal_window_area_m2']:.2f} m²</span></p>
<p><b>{t('card_glazing_u')}:</b> {u_vals.get('glass_u', u_vals.get('window_u', 2.80)):.2f} W/m²K</p>
<p><b>{t('card_glazing_wwr')}:</b> {(rec['optimal_window_area_m2'] / max(1.0, 2.0 * (geo['length_m'] + geo['width_m']) * geo['height_m'])) * 100.0:.1f} %</p>
</div>""",
            unsafe_allow_html=True,
        )

    with r3:
        st.markdown(
            f"""<div class='card'>
<h4>{t('card_orient_title')}</h4>
<p><b>{t('card_orient_label')}:</b> <span class='metric-badge'>{rec.get('optimal_orientation', 'south').title()} {t('card_orient_facade')}</span></p>
<p><b>{t('card_orient_strategy')}:</b> {mats['orientation_advice']}</p>
<p><b>{t('card_orient_shading')}:</b> {mats['shading_advice']}</p>
</div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class='card'>
<h4>{t('card_sizing_title')}</h4>
<p><b>{t('card_sizing_area')}:</b> {geo['floor_area_m2']:.1f} m² ({geo['length_m']:.1f}m × {geo['width_m']:.1f}m)</p>
<p><b>{t('card_sizing_height')}:</b> {geo['height_m']:.1f} m | <b>{t('card_sizing_volume')}:</b> {geo['volume_m3']:.1f} m³</p>
<p><b>{t('card_sizing_occupants')}:</b> {rec['people']} {t('persons_unit')}</p>
</div>""",
            unsafe_allow_html=True,
        )


def render_ranked_candidate_designs(ranked_designs: List[Dict[str, Any]]) -> None:
    """
    Renders top candidate configurations produced by the Bayesian optimizer.
    """
    if not ranked_designs:
        return

    st.markdown(f"### {t('ranking_title')}")
    st.caption(t("ranking_caption"))

    table_rows = []
    for d in ranked_designs:
        table_rows.append({
            t("col_rank"): d["label"],
            t("col_wall_material"): d["wall_material_name"],
            t("col_insulation_mm"): f"{d['insulation_mm']:.0f} mm",
            t("col_window_m2"): f"{d['window_area_m2']:.2f} m²",
            t("col_glazing_spec"): d["glazing_name"],
            t("col_orientation"): d["orientation"].title(),
            t("col_comfort_hours"): f"{d['comfort_hours']:.0f} h ({d['comfort_percentage']:.1f}%)",
            t("col_discomfort_dh"): f"{d['discomfort_dh']:.1f}",
            t("col_weekly_loss"): f"{d['total_heat_loss_kwh']:.1f}",
            t("col_composite_score"): f"{d['overall_score']:.1f} / 100",
        })

    st.dataframe(pd.DataFrame(table_rows), use_container_width=True)


def render_explainable_rationale(rec: Dict[str, Any]) -> None:
    """
    Renders the quantitative, physics-backed explainable recommendation box.
    """
    st.markdown(f"### {t('sec_rationale_title')}")
    st.info(rec["explanation"])
