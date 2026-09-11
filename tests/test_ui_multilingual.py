"""
================================================================================
STREAMLIT APPTEST SUITE FOR MULTILINGUAL UI
================================================================================
Simulates user interactions, language switching (en -> hi -> te -> en),
studio navigation, and input preservation.
================================================================================
"""

import pytest
from streamlit.testing.v1 import AppTest
import i18n


import os

APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))


def test_apptest_language_switching():
    """Test switching languages on the main scientific engine and verify text updates."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    # Switch to Scientific & Bayesian Engine
    # thermoshelter_app_view selectbox
    at.selectbox(key="thermoshelter_app_view").select("🔬 Scientific & Bayesian Engine").run()
    assert not at.exception

    # Default is English
    all_markdown = " ".join([m.value for m in at.markdown])
    assert "ThermoShelter Scientific Engine" in all_markdown
    assert "1. CLIMATE" in all_markdown

    # Switch to Hindi via language selector
    at.selectbox(key="header_lang_selector").select("hi").run()
    assert not at.exception

    all_markdown_hi = " ".join([m.value for m in at.markdown])
    assert "थर्मोशेल्टर" in all_markdown_hi
    assert "1. जलवायु" in all_markdown_hi

    # Switch to Telugu via language selector
    at.selectbox(key="header_lang_selector").select("te").run()
    assert not at.exception

    all_markdown_te = " ".join([m.value for m in at.markdown])
    assert "థర్మోషెల్టర్" in all_markdown_te
    assert "1. వాతావరణం" in all_markdown_te

    # Switch back to English
    at.selectbox(key="header_lang_selector").select("en").run()
    assert not at.exception

    all_markdown_en = " ".join([m.value for m in at.markdown])
    assert "ThermoShelter Scientific Engine" in all_markdown_en
    assert "1. CLIMATE" in all_markdown_en


def test_apptest_studios_navigation_in_multilingual():
    """Test that all 5 studios render without error in Hindi and Telugu."""
    for lang in ["hi", "te"]:
        at = AppTest.from_file(APP_PATH, default_timeout=30)
        at.run()

        # Switch view
        at.selectbox(key="thermoshelter_app_view").select("🔬 Scientific & Bayesian Engine").run()
        at.selectbox(key="header_lang_selector").select(lang).run()

        # Test each feature studio
        for studio_key in [
            "studio_shelter_designer",
            "studio_baseline_vs_opt",
            "studio_material_comparison",
            "studio_multiple_models",
            "studio_sensitivity_analysis",
        ]:
            at.radio(key="feature_studio_nav").set_value(studio_key).run()
            assert not at.exception, f"Failed on studio {studio_key} in language {lang}"
