"""
Unit tests for ThermoShelter AI Data Loader utility.
"""

import pytest
import pandas as pd
import data_loader

def test_load_locations_as_list():
    locs = data_loader.load_locations(as_dataframe=False)
    assert isinstance(locs, list)
    assert len(locs) >= 7
    ids = [loc["id"] for loc in locs]
    assert "leh" in ids
    assert "kargil" in ids
    assert "delhi" in ids

def test_load_locations_as_dataframe():
    df = data_loader.load_locations(as_dataframe=True)
    assert isinstance(df, pd.DataFrame)
    assert "latitude" in df.columns
    assert "altitude" in df.columns
    assert len(df) >= 7

def test_get_location_success():
    leh = data_loader.get_location("leh")
    assert leh["name"] == "Leh"
    assert leh["altitude"] == 3524.0
    assert leh["region"] == "Ladakh"

def test_get_location_not_found():
    with pytest.raises(ValueError):
        data_loader.get_location("non_existent_city")

def test_load_weather_all():
    df = data_loader.load_weather(as_dataframe=True)
    assert isinstance(df, pd.DataFrame)
    assert "ambient_temperature" in df.columns
    assert "solar_irradiance" in df.columns
    assert "wind_speed" in df.columns
    assert "relative_humidity" in df.columns
    assert "cloud_cover" in df.columns
    assert len(df) > 100

def test_load_weather_location_filter():
    df_leh = data_loader.load_weather(location_id="leh", as_dataframe=True)
    assert (df_leh["location_id"] == "leh").all()
    assert len(df_leh) == 168

def test_load_weather_as_dict_list():
    records = data_loader.load_weather(location_id="kargil", as_dataframe=False)
    assert isinstance(records, list)
    assert len(records) > 0
    assert "solar_irradiance" in records[0]

def test_load_materials_all():
    mats = data_loader.load_materials(as_dataframe=False)
    assert isinstance(mats, list)
    assert len(mats) >= 15
    ids = [m["id"] for m in mats]
    assert "mud_brick" in ids
    assert "eps_insulation" in ids
    assert "trombe_wall_mass" in ids

def test_load_materials_category_filter():
    insul = data_loader.load_materials(category="insulation", as_dataframe=False)
    for m in insul:
        assert m["category"] == "insulation"
    assert len(insul) >= 4

def test_load_materials_invalid_category():
    with pytest.raises(ValueError):
        data_loader.load_materials(category="nuclear_reactor")

def test_get_material_success():
    mud = data_loader.get_material("mud_brick")
    assert mud["id"] == "mud_brick"
    assert mud["density"]["typical_value"] == 1600.0
    assert mud["thermal_conductivity"]["typical_value"] == 0.60

def test_load_glazing():
    glazings = data_loader.load_glazing(as_dataframe=False)
    assert isinstance(glazings, list)
    assert len(glazings) >= 5
    ids = [g["id"] for g in glazings]
    assert "single_clear_4mm" in ids
    assert "double_low_e_argon_16mm" in ids

def test_get_glazing():
    g = data_loader.get_glazing("double_low_e_argon_16mm")
    assert g["U_value"]["typical_value"] == 1.20
    assert g["SHGC"]["typical_value"] == 0.55

def test_load_shelter_templates():
    templates = data_loader.load_shelter_templates(as_dataframe=False)
    assert isinstance(templates, list)
    assert len(templates) >= 4
    ids = [t["id"] for t in templates]
    assert "temporary_emergency_shelter" in ids
    assert "small_permanent_shelter" in ids
    assert "family_shelter" in ids

def test_get_single_shelter_template():
    t = data_loader.load_shelter_templates(template_id="temporary_emergency_shelter")
    assert isinstance(t, dict)
    assert t["capacity"] == 4
    assert t["default_length"] == 4.0
