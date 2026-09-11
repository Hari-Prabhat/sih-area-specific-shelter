# ThermoShelter AI — Final Engineering & UI Consistency Audit

**Date:** 2026-09-11  
**Branch:** `integration-react-final`  
**Evaluation Scope:** End-to-end audit of user input propagation, physics authority, 3D visualization mechanics, 2D architectural drafting, Bayesian optimization state, and physical sanity checks for SIH 2026 / DRDO demonstration.

---

## 1. Executive Summary

ThermoShelter AI is operating with a single authoritative physical source of truth in Python (`services/` and `backend/`). The legacy client-side thermal engine has been eliminated (`thermalEngine.ts` is deleted), and all thermal simulation and Bayesian multi-objective optimization traffic routes through FastAPI endpoints (`/api/simulation/run`, `/api/optimization/run`). 297 Python unit/integration tests pass and the React production build succeeds with zero errors.

However, a strict consistency and visual audit reveals specific geometric, visual, and architectural gaps that undermine physical credibility for high-stakes defense/engineering demonstration:
1. **Critical 3D Pitched Roof Disconnect:** In `ShelterModel3D.tsx`, rectangular pitched roofs are modeled using two independent rotated boxes without gables or sealed ridge alignment. At varying pitch angles or dimensions, the roof planes disconnect from wall plates, creating visible gaps, floating geometry, and open triangular voids at the gable ends.
2. **Opening Plausibility & Door Sizing in 3D:** Door geometry is fixed at $1.0\text{ m} \times 2.1\text{ m}$ regardless of the user's `doorArea` input ($0.5\text{ m}^2$ to $6.0\text{ m}^2$). Window geometry uses arbitrary placement without architectural frames or wall cutouts.
3. **Non-Rectangular Shape Inconsistencies:** The UI presents `cylindrical`, `dome`, and `pyramid` options, but parameter inputs (`length`, `width`, `roofAngle`) are rectangular-specific. In 3D, cylindrical and dome shapes synthesize radius as $r = \sqrt{L \cdot W / \pi}$, ignoring roof pitch, while the backend canonical model treats `roof_pitch_deg` as a global property.
4. **Orientation Inversion in 3D Scene:** The 3D scene applies rotation to the compass rose rather than orienting the shelter relative to a fixed geographic North coordinate frame, creating confusion about solar-facing apertures.
5. **Blueprint Shape Generality:** The 2D Engineering Blueprint assumes rectangular geometry with a pitched/flat roof and does not adapt its projection or elevations when cylindrical, dome, or pyramid shapes are selected.

---

## 2. Inconsistency Breakdown Across System Pipeline

### A. User Input → Canonical ShelterDesign → Simulation
- **Window Glazing & Door Area:** The user can specify `doorArea` and `windowGlazing` ('single', 'double', 'triple'). `api.ts` maps glazing correctly to `'single_clear'`, `'double_clear'`, or `'triple_low_e'`. However, `doorArea` is currently omitted from `buildCanonicalSimulationPayload()` in `api.ts` (it only passes `length`, `width`, `height`, `wall_material`, `wall_thickness_m`, `insulation_thickness_m`, `window_area`, `glazing`, `orientation`, `pitch_angle_deg`, `ach`, `occupants`). While Python canonical `ShelterDesign` supports `door_area_m2`, the API payload builder omits it, causing doors to default to $2.0\text{ m}^2$.
- **Roof Type vs Pitch Angle:** In `api.ts`, `roof_type` is hardcoded to `'flat'` even when `roofAngle > 0`. The backend compensates by using `pitch_angle_deg`, but the contract should explicitly set `roof_type: pitch_angle_deg > 0 ? 'pitched' : 'flat'`.

### B. 3D Model (`ShelterModel3D.tsx`)
- **Pitched Roof Geometry:**
  ```tsx
  // Current implementation in RectangularShelter:
  <mesh position={[0, height + roofPeak / 2, width / 4]} rotation={[roofRad, 0, 0]}>
    <boxGeometry args={[length + 0.4, roofHyp + 0.2, 0.12]} />
  </mesh>
  ```
  - The rotation center is the box center, not the eaves plate or ridge apex. When `roofAngle` increases, the edges penetrate into the wall or separate from the ridge beam.
  - The triangular gable ends (the wall sections extending up to the ridge under the pitch) are completely absent, leaving the shelter open to the sky at both ends.
- **Door Area Representation:**
  - Hardcoded `<boxGeometry args={[1.0, 2.1, 0.08]} />` in `Door()`. Does not respond to `shelterDesign.doorArea`.
- **Window Area Representation:**
  - Front windows use dynamic sizing, but back window area is arbitrarily scaled ($0.8 \times$). No structural frames or mullions are rendered.
- **Orientation:**
  - In `ShelterScene`, `<Compass orientation={design.orientation} />` rotates the compass rose while the shelter remains static, whereas in standard architectural CAD tools, the world axes (North/South/East/West) are fixed and the building rotates to reflect its true solar azimuth.

### C. 2D Blueprint (`EngineeringBlueprint.tsx`)
- **Shape Invariance:** Only renders rectangular plans and transverse sections. If `shape === 'dome'` or `'cylindrical'`, the blueprint continues to draft a rectangular floor plan ($L \times W$) with a ridge beam.
- **Door Dimensions:** Section and elevation hardcode door graphics (`width=40, height=90`) rather than computing dimensions from `doorArea`.

### D. Optimization Workflow (`ComparativeAnalysis.tsx` & `App.tsx`)
- **Candidate Application:** `handleApplyCandidate` correctly maps `wall_material_name`, `window_area_m2`, `glazing`, `orientation`, and `insulationType`. However, it does not update `wallThickness` or `roofAngle` if the candidate had specific structural requirements.
- **Terminology:** "Pareto" claims have been replaced with "Top Optimization Candidates Ranked by Optuna", which is accurate and defensible.

---

## 3. Classification of Issues

### A. Critical Issues (Must Fix for Credible Demo)
1. **Broken 3D Pitched Roof Geometry:** The rectangular shelter roof appears as floating disconnected slabs with open gable ends. It must be reconstructed as a single watertight parametric roof system with proper gable walls, ridge junction, and eaves overhangs.
2. **Unresponsive Door Geometry in 3D:** Door area in 3D does not change when `doorArea` slider/input changes.
3. **Missing `doorArea` in Simulation Payload:** `buildCanonicalSimulationPayload()` in `api.ts` omits `door_area`, causing simulation heat loss through doors to rely on hardcoded defaults.
4. **Compass vs Building Orientation Inversion:** In the 3D scene, orientation should rotate the shelter relative to fixed geographic coordinates (South at $+Z$ / North at $-Z$).

### B. Major Issues (Affects Professional Credibility)
1. **Gable Wall Triangles Missing:** In rectangular pitched roof mode, the left and right side walls must have triangular gables extending up to `height + roofPeak`.
2. **Window Framing & Architectural Polish:** Windows currently render as flat borderless glass panes hovering near the wall; they require parametric frames and wall aperture recesses.
3. **Blueprint Non-Rectangular Fallback/Warning:** When non-rectangular shapes are selected, the blueprint should either draw the proper shape or show an explicit engineering annotation: "CAD Blueprint currently generated for Rectangular Baseline".
4. **Shape-Specific Input Disabling in Design Studio:** When `cylindrical` or `dome` is chosen, `width` and `roofAngle` sliders should be conditionally disabled or labeled as equivalent diameter/spherical dome radius.

### C. Minor Issues (Cosmetic & Polish)
1. **Roof Type Inconsistency:** Ensure `roof_type` in `buildCanonicalSimulationPayload` reflects `'pitched'` whenever `roofAngle > 0`.
2. **Annual Diurnal Projection Labeling:** Clarify in `SimulationResults.tsx` that monthly temperatures are diurnal extrapolations based on annual climate normals.
3. **Streamlit Decoupling:** Note in documentation that Streamlit is a legacy hackathon prototype and not used in the React/FastAPI runtime.

---

## 4. Files Affected

| File | Component | Issues Identified |
|---|---|---|
| `thermoshelter-design-studio/src/components/ShelterModel3D.tsx` | 3D Visualization | Pitched roof geometry, gable wall ends, door sizing, window frames, world orientation rotation |
| `thermoshelter-design-studio/src/services/api.ts` | API Client | Include `door_area: design.doorArea` and dynamic `roof_type` in simulation payload |
| `thermoshelter-design-studio/src/components/ShelterDesigner.tsx` | Input Controls | Conditionally format/disable parameters when non-rectangular shape is active |
| `thermoshelter-design-studio/src/components/EngineeringBlueprint.tsx` | 2D Blueprint | Parametric door dimensioning, shape awareness |
| `tests/test_phase2_sensitivity.py` | Python Tests | Add door area and opening sensitivity assertions |

---

## 5. Proposed Fixes

### 1. Robust Parametric 3D Roof System (`ShelterModel3D.tsx`)
- Replace the two independent rotated boxes with a unified parametric roof mesh using Three.js custom `BufferGeometry` or exact trigonometry:
  - Calculate ridge coordinates: `(0, height + roofPeak, 0)` spanning from `-length/2 - overhang` to `+length/2 + overhang`.
  - Calculate eaves coordinates: `(±(width/2 + overhang), height - eaveDrop, z)`.
  - Add triangular gable end walls on left and right sides from `height` to `height + roofPeak`.
  - Ensure roof thickness is uniform and ridge meets seamlessly without open gaps.

### 2. Parametric Openings in 3D
- Compute door dimensions deterministically:
  $$\text{Door Width } W_d = 0.9\text{ m}, \quad \text{Door Height } H_d = \frac{\text{doorArea}}{W_d} \quad (\text{bounded between } 1.8\text{m and } 2.4\text{m})$$
- Render dark metallic framing around all window apertures and door leaves.

### 3. Realistic Geographic Orientation
- Fix the Compass Rose to static world space:
  - North: $-Z$ (Red arrow)
  - South: $+Z$ (Equator/Solar-facing)
  - East: $+X$
  - West: $-X$
- Rotate the shelter model itself by $\text{azimuth} - 180^\circ$ so that a South-facing shelter ($180^\circ$) faces $+Z$, directly into the winter solar trajectory.

### 4. API Client Payload Completion
- In `api.ts` (`buildCanonicalSimulationPayload`):
  - Pass `door_area: design.doorArea`.
  - Pass `roof_type: design.roofAngle > 0 ? 'pitched' : 'flat'`.

---

## 6. Tests Required

1. **Python Physical Sensitivity:**
   - Verify changing `door_area` from $1.0\text{ m}^2$ to $4.0\text{ m}^2$ increases infiltration/conduction loss proportionately.
2. **React Production Build:**
   - Execute `npm run build` to guarantee 0 TypeScript/Vite errors.
3. **Visual Geometry Verification:**
   - Test rectangular roof pitch across extremes: $0^\circ$ (flat), $15^\circ$, $30^\circ$, $45^\circ$, $60^\circ$.
   - Test shelter length $4\text{m} \to 20\text{m}$ and width $3\text{m} \to 12\text{m}$.
   - Verify roof stays firmly attached to wall plates at all pitch angles.

---

## 7. Engineering Assumptions

1. **Gable Roof Alignment:** The ridge line is oriented along the longitudinal axis ($X$-axis, length of shelter) with two symmetrical roof planes pitching down across the transverse axis ($Z$-axis, width of shelter).
2. **Opening Placement:** Primary glazed apertures (windows) and access door are placed on the principal solar facade (South, $+Z$ local coordinates).
3. **Non-Rectangular Geometries:** Shapes other than rectangular (cylinder, dome, pyramid) represent specialized mission concepts; for rectangular shelters, detailed architectural framing and ISO 6946 multi-layer layers are fully detailed.

---

**Status:** Audit Complete. Awaiting approval before proceeding to implementation.
