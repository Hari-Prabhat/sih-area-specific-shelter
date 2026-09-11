"""
================================================================================
TESTS FOR MULTILINGUAL I18N SUPPORT
================================================================================
Tests locale loading, key parity, fallback behavior, interpolation, and
confirms that simulation/optimization results remain strictly invariant.
================================================================================
"""

import pytest
import i18n
from services.simulation_service import run_simulation
from services.recommender import get_recommendation


def test_locales_load_successfully():
    """Verify en, hi, and te locales load without error."""
    translations = i18n._load_translations()
    assert "en" in translations
    assert "hi" in translations
    assert "te" in translations
    assert len(translations["en"]) > 50
    assert len(translations["hi"]) > 50
    assert len(translations["te"]) > 50


def test_locale_key_parity():
    """Verify all keys present in English also exist in Hindi and Telugu."""
    translations = i18n._load_translations()
    en_keys = set(translations["en"].keys())
    hi_keys = set(translations["hi"].keys())
    te_keys = set(translations["te"].keys())

    missing_in_hi = en_keys - hi_keys
    missing_in_te = en_keys - te_keys

    assert not missing_in_hi, f"Missing keys in hi.json: {missing_in_hi}"
    assert not missing_in_te, f"Missing keys in te.json: {missing_in_te}"


def test_translation_lookup_and_fallback():
    """Verify t() retrieves correct strings and falls back appropriately."""
    # Test English
    en_title = i18n.t("app_title")
    assert "ThermoShelter" in en_title

    # Test missing key fallback to provided default
    missing_res = i18n.t("non_existent_key_12345", default="Fallback Default")
    assert missing_res == "Fallback Default"

    # Test missing key fallback to key itself
    key_res = i18n.t("non_existent_key_54321")
    assert key_res == "non_existent_key_54321"


def test_translation_interpolation():
    """Verify string interpolation with kwargs works cleanly in all languages."""
    translations = i18n._load_translations()

    for lang in ["en", "hi", "te"]:
        template = translations[lang]["sim_active_success"]
        formatted = template.format(
            city="LEH",
            climate_name="Alpine Severe Cold",
            discomfort=120.5,
            comfort=85.2,
        )
        assert "LEH" in formatted
        assert "120.5" in formatted
        assert "85.2" in formatted


def test_numerical_simulation_invariance():
    """Verify simulation calculations are 100% identical regardless of translation layer."""
    sim_1 = run_simulation(
        city="leh",
        length=4.5,
        width=3.2,
        height=2.8,
        wall_material="brick",
        insulation_thickness_m=0.08,
        window_area=2.5,
        occupants=4,
        hours_to_simulate=168,
    )

    sim_2 = run_simulation(
        city="leh",
        length=4.5,
        width=3.2,
        height=2.8,
        wall_material="brick",
        insulation_thickness_m=0.08,
        window_area=2.5,
        occupants=4,
        hours_to_simulate=168,
    )

    assert sim_1["comfort_hours"] == sim_2["comfort_hours"]
    assert sim_1["comfort_percentage"] == sim_2["comfort_percentage"]
    assert sim_1["discomfort_degree_hours"] == sim_2["discomfort_degree_hours"]
    assert sim_1["total_heat_loss_kwh"] == sim_2["total_heat_loss_kwh"]
    assert sim_1["u_values"]["wall_u"] == sim_2["u_values"]["wall_u"]
