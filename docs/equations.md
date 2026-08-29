# 📐 ThermoShelter AI — Central Mathematical & Thermal Formula Engine

This document outlines the mathematical equations, thermodynamic models, variable definitions, standard SI units, and scientific assumptions implemented in the centralized formula engine (`services/formulas.py`).

---

## 1. Geometry Equations (`services/geometry.py`)

### 1.1 Net Floor Area
$$A_{\text{floor}} = L \times W$$
* **Variables**: $L$ = Internal shelter length ($\text{m}$), $W$ = Internal shelter width ($\text{m}$)
* **Units**: $\text{m}^2$
* **Assumptions**: Rectangular floor plan geometry.

### 1.2 Enclosed Volume
$$V = L \times W \times H$$
* **Variables**: $H$ = Mean internal ceiling height ($\text{m}$)
* **Units**: $\text{m}^3$
* **Assumptions**: Enclosed air mass volume calculation.

### 1.3 Gross Vertical Wall Surface Area
$$A_{\text{wall,gross}} = 2(L + W)H$$
* **Units**: $\text{m}^2$

### 1.4 Net Opaque Wall Area
$$A_{\text{wall,net}} = A_{\text{wall,gross}} - \sum A_{\text{windows}} - \sum A_{\text{doors}}$$
* **Units**: $\text{m}^2$
* **Constraint**: $A_{\text{wall,net}} \ge 0$.

---

## 2. Thermal Resistance ($R$-Value) (`services/thermal.py`)

### 2.1 Single Homogeneous Layer
$$R_i = \frac{L_i}{k_i}$$
* **Variables**: $L_i$ = Layer thickness ($\text{m}$), $k_i$ = Material thermal conductivity ($\text{W}/(\text{m}\cdot\text{K})$)
* **Units**: $\text{m}^2\cdot\text{K}/\text{W}$
* **Assumptions**: 1D steady-state Fourier conduction across planar layer.

### 2.2 Multi-Layer Composite Assembly
$$R_{\text{total}} = R_{\text{inside}} + \sum_{i=1}^{n} \frac{L_i}{k_i} + R_{\text{outside}}$$
* **Variables**: $R_{\text{inside}}$ = Interior surface air film resistance ($\text{m}^2\cdot\text{K}/\text{W}$), $R_{\text{outside}}$ = Exterior surface film resistance ($\text{m}^2\cdot\text{K}/\text{W}$)
* **Units**: $\text{m}^2\cdot\text{K}/\text{W}$
* **Standard Reference**: ISO 6946 / IS 3792 (Vertical wall defaults: $R_{\text{in}} = 0.13$, $R_{\text{out}} = 0.04$).

---

## 3. Overall Thermal Transmittance ($U$-Value)

$$U = \frac{1}{R_{\text{total}}}$$
* **Units**: $\text{W}/(\text{m}^2\cdot\text{K})$

---

## 4. Conductive Heat Transfer

$$\dot{Q}_{\text{conduction}} = U \cdot A \cdot (T_{\text{in}} - T_{\text{out}})$$
* **Variables**: $U$ = Assembly U-value ($\text{W}/(\text{m}^2\cdot\text{K})$), $A$ = Net surface area ($\text{m}^2$), $T_{\text{in}}$ = Indoor temperature ($^\circ\text{C}$), $T_{\text{out}}$ = Outdoor ambient temperature ($^\circ\text{C}$)
* **Units**: Watts ($\text{W}$)
* **Sign Convention**: Positive ($+$) denotes heat lost from shelter to environment.

---

## 5. Solar Radiation & Absorbed Surface Gain (`services/solar.py`)

$$\dot{Q}_{\text{solar,opaque}} = I_{\text{solar}} \cdot A \cdot \alpha \cdot F_{\text{orientation}}$$
* **Variables**: $I_{\text{solar}}$ = Incident solar irradiance ($\text{W}/\text{m}^2$), $\alpha$ = Surface solar absorptivity ($0.0 - 1.0$), $F_{\text{orientation}}$ = Geometric orientation factor ($0.0 - 1.0$)
* **Units**: Watts ($\text{W}$)

---

## 6. Glazing Solar Heat Gain

$$\dot{Q}_{\text{solar,glazing}} = I_{\text{solar}} \cdot A_{\text{window}} \cdot \text{SHGC} \cdot F_{\text{shading}}$$
* **Variables**: $\text{SHGC}$ = Solar Heat Gain Coefficient of window assembly ($0.0 - 1.0$), $F_{\text{shading}}$ = Frame/shading reduction factor ($0.0 - 1.0$)
* **Units**: Watts ($\text{W}$)
* **Assumptions**: Standard lumped ASHRAE fenestration heat gain model.

---

## 7. Ventilation & Infiltration (`services/ventilation.py`)

### 7.1 Volumetric Airflow
$$\dot{V} = \frac{\text{ACH} \cdot V}{3600}$$
* **Variables**: $\text{ACH}$ = Air changes per hour ($1/\text{h}$), $V$ = Enclosed volume ($\text{m}^3$)
* **Units**: $\text{m}^3/\text{s}$

### 7.2 Sensible Ventilation Heat Loss
$$\dot{Q}_{\text{ventilation}} = \rho_{\text{air}} \cdot \dot{V} \cdot c_{p,\text{air}} \cdot (T_{\text{in}} - T_{\text{out}})$$
* **Variables**: $\rho_{\text{air}} = 1.225\,\text{kg}/\text{m}^3$, $c_{p,\text{air}} = 1005.0\,\text{J}/(\text{kg}\cdot\text{K})$
* **Units**: Watts ($\text{W}$)

---

## 8. Thermal Mass & Capacitance

$$C_{\text{thermal}} = \sum m_i \cdot c_{p,i} = \sum (\rho_i \cdot V_i \cdot c_{p,i})$$
$$\Delta T = \frac{Q_{\text{net}}}{C_{\text{thermal}}}$$
* **Variables**: $m_i$ = Mass ($\text{kg}$), $c_{p,i}$ = Specific heat capacity ($\text{J}/(\text{kg}\cdot\text{K})$)
* **Units**: Capacitance in $\text{J}/\text{K}$, Energy in $\text{Joules}$

---

## 9. Longwave Radiation Exchange

$$\dot{Q}_{\text{radiation}} = \epsilon \cdot \sigma \cdot A \cdot \left( T_{\text{surface,K}}^4 - T_{\text{surroundings,K}}^4 \right)$$
* **Variables**: $\epsilon$ = Longwave emissivity ($0.0 - 1.0$), $\sigma = 5.670374 \times 10^{-8}\,\text{W}/(\text{m}^2\cdot\text{K}^4)$
* **Units**: Watts ($\text{W}$)

---

## 10. Occupant Internal Heat Gain

$$\dot{Q}_{\text{internal}} = N_{\text{occupants}} \cdot q_{\text{person}}$$
* **Variables**: $N_{\text{occupants}}$ = Number of people, $q_{\text{person}} = 80.0\,\text{W}/\text{person}$ (sensible metabolic baseline)
* **Units**: Watts ($\text{W}$)

---

## 11. Net Instantaneous Energy Balance

$$\dot{Q}_{\text{net}} = \dot{Q}_{\text{solar}} + \dot{Q}_{\text{internal}} - \dot{Q}_{\text{conduction}} - \dot{Q}_{\text{ventilation}} - \dot{Q}_{\text{radiation}}$$
* **Units**: Watts ($\text{W}$)

---

## 12. Transient Forward Euler Integration

$$T_{\text{indoor}}^{t+\Delta t} = T_{\text{indoor}}^t + \frac{\dot{Q}_{\text{net}} \cdot \Delta t}{C_{\text{thermal}}}$$
* **Variables**: $\Delta t$ = Timestep in seconds ($3600.0\,\text{s}$ for hourly steps)
* **Units**: $^\circ\text{C}$

---

## 13. Thermal Comfort & Summary Metrics (`services/comfort.py`)

* **Comfort Status**:
  $$\text{Status} = \begin{cases} \text{"too\_cold"} & \text{if } T_{\text{in}} < T_{\text{min,comfort}} \\ \text{"comfortable"} & \text{if } T_{\text{min,comfort}} \le T_{\text{in}} \le T_{\text{max,comfort}} \\ \text{"too\_hot"} & \text{if } T_{\text{in}} > T_{\text{max,comfort}} \end{cases}$$
* **Comfort Percentage**:
  $$\text{Comfort \%} = \frac{\text{Comfortable Hours}}{\text{Total Hours}} \times 100$$
* **Temperature Amplitude Range**:
  $$\Delta T_{\text{swing}} = \max(T_{\text{in}}) - \min(T_{\text{in}})$$

---

## 14. Supplemental Heating Demand

$$\dot{Q}_{\text{heating}} = \begin{cases} \frac{C_{\text{thermal}} \cdot (T_{\text{target}} - T_{\text{in}})}{\Delta t} & \text{if } T_{\text{in}} < T_{\text{target}} \\ 0 & \text{otherwise} \end{cases}$$
$$E_{\text{heating,kWh}} = \sum \frac{\dot{Q}_{\text{heating}} \cdot \Delta t_{\text{hours}}}{1000}$$

---

## 15. Multi-Criteria Design Optimization Score

$$\text{Score} = w_c \cdot S_{\text{comfort}} + w_e \cdot S_{\text{energy}} + w_{hl} \cdot S_{\text{heat\_loss}} + w_s \cdot S_{\text{solar}}$$
* **Constraints**: $\sum w_i = 1.0$, $0 \le S_i \le 100$.
* **Default Weights**: Comfort ($0.40$), Energy ($0.30$), Heat Loss Retention ($0.20$), Solar Harvesting ($0.10$).
