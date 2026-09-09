# ThermoShelter AI — Subsystem Mock Data Layer (Member 2)

## Purpose & Scope
This directory contains independent, self-contained mock and baseline dataset objects for:
- `ShelterRequirements`
- `ShelterGeometry`
- `MaterialAssembly`
- `PassiveStrategy`
- `ShelterDesign`

These files enable **Member 2** (Parametric Geometry, Material & Envelope, Passive Systems), **Member 3** (Thermal Digital Twin & Optimization), and **Member 4** (3D & 2D Blueprint generation) to develop and test their systems completely independently without waiting on each other's live modules.

## Files
1. `mock_shelter_requirements.json` — Sample occupant and architectural program requirements.
2. `mock_shelter_geometry.json` — Pre-calculated compact rectangular geometry with openings and multi-zone layout.
3. `mock_material_assembly.json` — Multilayer wall, roof, and floor composite assemblies with ISO 6946 R-values and U-values.
4. `mock_passive_strategy.json` — Structured list of active passive design strategies (cold region, hot dry).
5. `mock_shelter_design_leh.json` — Complete canonical `ShelterDesign` digital twin for extreme cold climate (Leh/Ladakh hero benchmark).
6. `mock_shelter_design_hot_dry.json` — Complete canonical `ShelterDesign` digital twin for hot-dry desert climate (Jaisalmer benchmark).

## Usage
To load any mock file programmatically in Python:

```python
import json
from services.shelter.models import ShelterDesign, ShelterRequirements, ShelterGeometry

# Load complete design
with open("data/mock/mock_shelter_design_leh.json", "r") as f:
    design = ShelterDesign.from_json(f.read())

print(f"Loaded: {design.name}, Wall U-value: {design.wall_assembly.u_value} W/m²K")
```
