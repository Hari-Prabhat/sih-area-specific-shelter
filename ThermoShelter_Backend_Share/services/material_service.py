import json
import os
from functools import lru_cache
from typing import Any, Dict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATERIALS_FILE = os.path.join(BASE_DIR, "data", "materials", "materials.json")


def _extract_val(v: Any, default: float = 1.0) -> float:
    if isinstance(v, dict):
        return float(v.get("typical_value", default))
    if isinstance(v, (int, float)):
        return float(v)
    return default


@lru_cache(maxsize=1)
def load_all_materials() -> Dict[str, Dict[str, Any]]:
    """
    Returns normalized material database keyed by material ID and common aliases.
    """
    if not os.path.exists(MATERIALS_FILE):
        return {}

    with open(MATERIALS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    materials: Dict[str, Dict[str, Any]] = {}

    if isinstance(raw, list):
        for m in raw:
            mat_id = m.get("id", "").strip().lower()
            if not mat_id:
                continue
            normalized = {
                "id": mat_id,
                "name": m.get("name", mat_id.title()),
                "category": m.get("category", "wall"),
                "thermal_conductivity": _extract_val(m.get("thermal_conductivity"), 0.72),
                "density": _extract_val(m.get("density"), 1800.0),
                "specific_heat": _extract_val(m.get("specific_heat"), 900.0),
                "emissivity": _extract_val(m.get("emissivity"), 0.90),
                "solar_absorptivity": _extract_val(m.get("solar_absorptivity"), 0.70),
                "cost_estimate": _extract_val(m.get("cost_estimate"), 50.0),
                "source": m.get("source", ""),
                "notes": m.get("notes", ""),
            }
            materials[mat_id] = normalized

        # Common shorthand aliases for backward compatibility
        aliases = {
            "brick": "fired_clay_brick",
            "concrete": "concrete_standard",
            "puf_insulation": "polyurethane_foam",
            "eps_insulation": "eps_insulation",
            "xps_insulation": "xps_insulation",
            "stone": "stone_granite",
            "mud": "mud_brick",
            "adobe": "mud_brick",
            "wood": "wood_timber_pine",
        }
        for alias, target_id in aliases.items():
            if target_id in materials and alias not in materials:
                alias_entry = dict(materials[target_id])
                alias_entry["id"] = alias
                materials[alias] = alias_entry

    elif isinstance(raw, dict):
        materials = raw

    return materials


def get_material(material_name: str) -> Dict[str, Any]:
    """
    Return properties for one material by ID or alias.
    """
    materials = load_all_materials()
    key = str(material_name).strip().lower()
    if key in materials:
        return materials[key]
    return {"error": f"Material '{material_name}' not found."}


if __name__ == "__main__":
    brick = get_material("brick")
    print(f"Brick conductivity: {brick['thermal_conductivity']} W/mK")
    all_mats = load_all_materials()
    print(f"Total materials loaded: {len(all_mats)}")