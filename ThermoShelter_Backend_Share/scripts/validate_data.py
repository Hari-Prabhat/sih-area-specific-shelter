"""
THERMOSHELTER AI - Data Validation Suite
========================================
Rigorously validates all climate, weather, materials, glazing,
and shelter templates against schema and physical constraints.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

class DataValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.stats = {}

    def log_error(self, filename: str, msg: str):
        self.errors.append(f"SEVERE [{filename}]: {msg}")

    def log_warning(self, filename: str, msg: str):
        self.warnings.append(f"WARNING [{filename}]: {msg}")

    def validate_locations(self) -> bool:
        file_path = DATA_DIR / "climate" / "locations.json"
        if not file_path.exists():
            self.log_error("locations.json", "File does not exist.")
            return False

        with open(file_path, "r", encoding="utf-8") as f:
            locs = json.load(f)

        req_fields = ["id", "name", "country", "region", "latitude", "longitude", "altitude", "climate_type"]
        ids = set()

        for i, loc in enumerate(locs):
            for field in req_fields:
                if field not in loc or loc[field] is None:
                    self.log_error("locations.json", f"Record #{i} missing required field '{field}'")

            loc_id = loc.get("id", "")
            if loc_id in ids:
                self.log_error("locations.json", f"Duplicate location id '{loc_id}'")
            ids.add(loc_id)

            lat = loc.get("latitude", 0.0)
            lon = loc.get("longitude", 0.0)
            alt = loc.get("altitude", -9999)

            if not (-90.0 <= lat <= 90.0):
                self.log_error("locations.json", f"Invalid latitude {lat} for {loc_id} (must be between -90 and 90)")
            if not (-180.0 <= lon <= 180.0):
                self.log_error("locations.json", f"Invalid longitude {lon} for {loc_id} (must be between -180 and 180)")
            if alt < 0.0:
                self.log_warning("locations.json", f"Altitude {alt} is sub-zero for {loc_id}")

        self.stats["locations_count"] = len(locs)
        return True

    def validate_weather(self) -> bool:
        file_path = DATA_DIR / "climate" / "weather.csv"
        if not file_path.exists():
            self.log_error("weather.csv", "File does not exist.")
            return False

        df = pd.read_csv(file_path)
        req_cols = [
            "timestamp", "location_id", "ambient_temperature",
            "solar_irradiance", "wind_speed", "relative_humidity", "cloud_cover"
        ]

        for col in req_cols:
            if col not in df.columns:
                self.log_error("weather.csv", f"Missing required column '{col}'")

        if df.empty:
            self.log_error("weather.csv", "Dataset is empty.")
            return False

        for i, row in df.iterrows():
            ts_str = str(row["timestamp"])
            try:
                datetime.fromisoformat(ts_str)
            except Exception:
                try:
                    datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    self.log_error("weather.csv", f"Row {i}: Invalid timestamp format '{ts_str}'")

            solar = float(row["solar_irradiance"])
            if solar < 0.0:
                self.log_error("weather.csv", f"Row {i}: Negative solar irradiance {solar} W/m²")
            elif solar > 1400.0:
                self.log_warning("weather.csv", f"Row {i}: Exceptionally high solar irradiance {solar} W/m²")

            wind = float(row["wind_speed"])
            if wind < 0.0:
                self.log_error("weather.csv", f"Row {i}: Negative wind speed {wind} m/s")

            rh = float(row["relative_humidity"])
            if not (0.0 <= rh <= 100.0):
                self.log_error("weather.csv", f"Row {i}: Invalid relative humidity {rh}% (must be 0-100)")

            cloud = float(row["cloud_cover"])
            if not (0.0 <= cloud <= 1.0):
                self.log_error("weather.csv", f"Row {i}: Invalid cloud cover {cloud} (must be 0.0 - 1.0)")

        self.stats["weather_rows"] = len(df)
        return True

    def validate_materials(self) -> bool:
        file_path = DATA_DIR / "materials" / "materials.json"
        if not file_path.exists():
            self.log_error("materials.json", "File does not exist.")
            return False

        with open(file_path, "r", encoding="utf-8") as f:
            mats = json.load(f)

        req_fields = [
            "id", "name", "category", "density", "thermal_conductivity",
            "specific_heat", "emissivity", "solar_absorptivity", "cost_estimate",
            "source", "notes"
        ]
        valid_cats = {"wall", "roof", "floor", "insulation", "thermal_mass"}
        ids = set()

        for i, m in enumerate(mats):
            for field in req_fields:
                if field not in m or m[field] is None:
                    self.log_error("materials.json", f"Material #{i} missing required property '{field}'")

            m_id = m.get("id", "")
            if m_id in ids:
                self.log_error("materials.json", f"Duplicate material id '{m_id}'")
            ids.add(m_id)

            cat = m.get("category", "")
            if cat not in valid_cats:
                self.log_error("materials.json", f"Material {m_id} has invalid category '{cat}'. Must be one of {valid_cats}")

            for prop in ["density", "thermal_conductivity", "specific_heat", "emissivity", "solar_absorptivity", "cost_estimate"]:
                data_obj = m.get(prop)
                if isinstance(data_obj, dict):
                    typ = data_obj.get("typical_value")
                    mn = data_obj.get("min_value")
                    mx = data_obj.get("max_value")
                    if typ is None or (typ <= 0.0 and prop != "cost_estimate"):
                        self.log_error("materials.json", f"Material {m_id}: {prop} typical_value must be > 0")
                    if mn is not None and mx is not None and mn > mx:
                        self.log_error("materials.json", f"Material {m_id}: {prop} min_value {mn} > max_value {mx}")
                elif isinstance(data_obj, (int, float)):
                    if data_obj <= 0.0 and prop != "cost_estimate":
                        self.log_error("materials.json", f"Material {m_id}: {prop} must be > 0")

        self.stats["materials_count"] = len(mats)
        return True

    def validate_glazing(self) -> bool:
        file_path = DATA_DIR / "materials" / "glazing.json"
        if not file_path.exists():
            self.log_error("glazing.json", "File does not exist.")
            return False

        with open(file_path, "r", encoding="utf-8") as f:
            glazs = json.load(f)

        req_fields = ["id", "name", "U_value", "SHGC", "thickness", "source", "notes"]
        ids = set()

        for g, gl in enumerate(glazs):
            for field in req_fields:
                if field not in gl or gl[field] is None:
                    self.log_error("glazing.json", f"Glazing #{g} missing required field '{field}'")

            g_id = gl.get("id", "")
            if g_id in ids:
                self.log_error("glazing.json", f"Duplicate glazing id '{g_id}'")
            ids.add(g_id)

            u_obj = gl.get("U_value")
            u_val = u_obj.get("typical_value") if isinstance(u_obj, dict) else u_obj
            if u_val is None or u_val <= 0.0:
                self.log_error("glazing.json", f"Glazing {g_id} U-value must be > 0")

            shgc_obj = gl.get("SHGC")
            shgc_val = shgc_obj.get("typical_value") if isinstance(shgc_obj, dict) else shgc_obj
            if shgc_val is None or not (0.0 <= shgc_val <= 1.0):
                self.log_error("glazing.json", f"Glazing {g_id} SHGC must be between 0 and 1")

            th_obj = gl.get("thickness")
            th_val = th_obj.get("typical_value") if isinstance(th_obj, dict) else th_obj
            if th_val is None or th_val <= 0.0:
                self.log_error("glazing.json", f"Glazing {g_id} thickness must be > 0 meters")

        self.stats["glazing_count"] = len(glazs)
        return True

    def validate_shelters(self) -> bool:
        file_path = DATA_DIR / "shelters" / "templates.json"
        if not file_path.exists():
            self.log_error("templates.json", "File does not exist.")
            return False

        with open(file_path, "r", encoding="utf-8") as f:
            temps = json.load(f)

        req_fields = [
            "id", "name", "capacity",
            "default_length", "default_width", "default_height",
            "shape", "description"
        ]
        ids = set()

        for t in temps:
            for field in req_fields:
                if field not in t or t[field] is None:
                    self.log_error("templates.json", f"Shelter template missing required field '{field}'")

            t_id = t.get("id", "")
            if t_id in ids:
                self.log_error("templates.json", f"Duplicate shelter id '{t_id}'")
            ids.add(t_id)

            cap = t.get("capacity", 0)
            if cap <= 0:
                self.log_error("templates.json", f"Shelter {t_id}: capacity must be > 0")

            l = t.get("default_length", 0.0)
            w = t.get("default_width", 0.0)
            h = t.get("default_height", 0.0)
            if l <= 0.0 or w <= 0.0 or h <= 0.0:
                self.log_error("templates.json", f"Shelter {t_id}: dimensions (length, width, height) must be positive")

        self.stats["shelters_count"] = len(temps)
        return True

    def run_all(self) -> bool:
        print("=" * 60)
        print("THERMOSHELTER AI - DATA VALIDATION SUITE")
        print("=" * 60)

        self.validate_locations()
        self.validate_weather()
        self.validate_materials()
        self.validate_glazing()
        self.validate_shelters()

        print("\n--- SUMMARY STATISTICS ---")
        for k, v in self.stats.items():
            print(f"  {k:25}: {v}")

        if self.warnings:
            print(f"\n[!] WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"  - {w}")

        if self.errors:
            print(f"\n[X] SEVERE ERRORS ({len(self.errors)}):")
            for e in self.errors:
                print(f"  - {e}")
            print("=" * 60)
            print("VALIDATION FAILED!")
            return False
        else:
            print("\n(+) ALL CHECKS PASSED SUCCESSFULLY. DATASETS ARE 100% COMPLIANT.")
            print("=" * 60)
            return True

if __name__ == "__main__":
    validator = DataValidator()
    success = validator.run_all()
    sys.exit(0 if success else 1)
