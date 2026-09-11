"""
================================================================================
THERMOSHELTER AI — Internationalization (i18n) Engine
================================================================================
Provides centralized, robust multi-language localization for:
  - English (en, default)
  - Hindi (hi, हिन्दी)
  - Telugu (te, తెలుగు)

Persists chosen language in Streamlit session_state without resetting inputs.
Falls back safely to English and original keys if any translation key is missing.
================================================================================
"""

import json
import os
from typing import Any, Dict, Optional
import streamlit as st

SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "hi": "हिन्दी (Hindi)",
    "te": "తెలుగు (Telugu)",
}

DEFAULT_LANGUAGE = "en"
SESSION_KEY = "thermoshelter_language"

_LOCALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")
_TRANSLATIONS: Dict[str, Dict[str, str]] = {}


def _load_translations() -> Dict[str, Dict[str, str]]:
    """Loads all JSON translation files from the locales directory into memory."""
    global _TRANSLATIONS
    if _TRANSLATIONS:
        return _TRANSLATIONS

    for lang in SUPPORTED_LANGUAGES.keys():
        file_path = os.path.join(_LOCALES_DIR, f"{lang}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    _TRANSLATIONS[lang] = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load locale file {file_path}: {e}")
                _TRANSLATIONS[lang] = {}
        else:
            _TRANSLATIONS[lang] = {}

    return _TRANSLATIONS


def get_current_language() -> str:
    """Returns the current active language code from session state."""
    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = DEFAULT_LANGUAGE
    return st.session_state.get(SESSION_KEY, DEFAULT_LANGUAGE)


def set_language(lang_code: str) -> None:
    """Sets the active language code in session state."""
    if lang_code in SUPPORTED_LANGUAGES:
        st.session_state[SESSION_KEY] = lang_code


def t(key: str, default: Optional[str] = None, lang: Optional[str] = None, **kwargs: Any) -> str:
    """
    Translates a key into the currently selected language (or specified lang).
    Falls back to English if missing, then to `default` or `key`.
    Supports keyword interpolation using str.format(**kwargs).
    """
    translations = _load_translations()
    current_lang = lang if lang and lang in SUPPORTED_LANGUAGES else get_current_language()

    # 1. Try current language
    val = translations.get(current_lang, {}).get(key)

    # 2. Fall back to English
    if val is None:
        val = translations.get(DEFAULT_LANGUAGE, {}).get(key)

    # 3. Fall back to supplied default or key itself
    if val is None:
        val = default if default is not None else key

    # Interpolate format variables if provided
    if kwargs and isinstance(val, str):
        try:
            return val.format(**kwargs)
        except Exception:
            return val

    return val


def _on_language_change(widget_key: str) -> None:
    val = st.session_state.get(widget_key)
    if val in SUPPORTED_LANGUAGES:
        st.session_state[SESSION_KEY] = val
        for other_key in ["header_lang_selector", "sidebar_lang_selector"]:
            if other_key != widget_key:
                st.session_state[other_key] = val


def render_language_selector(key: str = "lang_select", label_visibility: str = "collapsed") -> str:
    """
    Renders a compact, styled language selectbox.
    Returns the selected language code.
    """
    current = get_current_language()
    lang_codes = list(SUPPORTED_LANGUAGES.keys())

    if key not in st.session_state or st.session_state[key] not in SUPPORTED_LANGUAGES:
        st.session_state[key] = current

    current_idx = lang_codes.index(st.session_state[key]) if st.session_state[key] in lang_codes else 0

    selected = st.selectbox(
        label=t("language_selector_label", default="🌐 Language"),
        options=lang_codes,
        index=current_idx,
        format_func=lambda code: SUPPORTED_LANGUAGES.get(code, code),
        key=key,
        on_change=_on_language_change,
        args=(key,),
        label_visibility=label_visibility,
    )

    if selected != current:
        st.session_state[SESSION_KEY] = selected

    return selected
