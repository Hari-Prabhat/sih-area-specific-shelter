import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATERIALS_FILE = os.path.join(BASE_DIR, "data", "materials", "materials.json")

def load_all_materials():
    """Return the full material database."""
    with open(MATERIALS_FILE, "r") as f:
        return json.load(f)

def get_material(material_name):
    """Return properties for one material."""
    materials = load_all_materials()
    if material_name in materials:
        return materials[material_name]
    return {"error": f"Material '{material_name}' not found."}

if __name__ == "__main__":
    brick = get_material("brick")
    print(f"Brick conductivity: {brick['thermal_conductivity']} W/mK")
    all_mats = load_all_materials()
    print(f"Total materials loaded: {len(all_mats)}")