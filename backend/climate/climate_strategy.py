"""
THERMOSHELTER AI - Climate Strategy Engine
==========================================
Translates a ClimateProfile into an authoritative PassiveStrategy recommendation.
Preserves strict boundaries: produces qualitative architectural requirements and priority
rankings WITHOUT encroaching on dimensions, material thicknesses, or thermal simulation.
"""

from typing import List
from backend.climate.schemas import (
    ClimateProfile,
    ClimateZone,
    PassiveStrategy,
    PriorityLevel,
)


class ClimateStrategyEngine:
    """
    Generates evidence-based passive thermodynamic design strategies
    tailored to the normalized climate profile.
    """

    @classmethod
    def generate_strategy(cls, profile: ClimateProfile) -> PassiveStrategy:
        """
        Derives the passive architectural principles for the provided ClimateProfile.
        """
        zone = profile.climate.classification
        cold_ext = profile.design_extremes.cold_extreme
        hot_ext = profile.design_extremes.hot_extreme
        solar_kwh = profile.solar.annual_solar_ghi_kwh_m2 or (profile.solar.GHI * 8760.0 / 1000.0)
        avg_rh = profile.humidity.average_relative_humidity
        diurnal = profile.climate.diurnal_range_mean or 10.0
        hdd = profile.design_extremes.heating_degree_days_18c or 0.0

        rules_triggered: List[str] = []

        # ======================================================================
        # 1. EXTREME COLD (e.g. Leh, Ladakh; Kargil)
        # ======================================================================
        if zone == ClimateZone.EXTREME_COLD:
            rules_triggered.extend([
                "R_EC_01: Winter design sub-zero severe hypothermia mitigation",
                "R_EC_02: Maximize direct passive solar aperture on equator-facing facade",
                "R_EC_03: High envelope thermal resistance to arrest conduction loss",
                "R_EC_04: High thermal mass for diurnal solar absorption and night release",
                "R_EC_05: Mandatory dual-door airlock vestibule against infiltration wind drafts",
                "R_EC_06: Unconditioned perimeter thermal buffer on prevailing wind facade"
            ])
            explanation = (
                f"The climate profile indicates extreme sub-zero conditions with a winter design extreme "
                f"of {cold_ext:.1f}°C and {hdd:.0f} annual heating degree days. Conductive and infiltration heat losses "
                f"are life-threatening if unmitigated. However, the site benefits from exceptional solar insolation "
                f"({solar_kwh:.0f} kWh/m²/year) and significant diurnal swings ({diurnal:.1f}°C). "
                f"Therefore, direct solar capture is prioritized with high thermal mass for nighttime heat re-radiation. "
                f"The building envelope requires top-tier insulation priority with minimized fenestration on non-solar "
                f"facades, mandatory entrance airlocks to eliminate winter infiltration, and unconditioned buffer zones "
                f"shielding primary living spaces."
            )
            return PassiveStrategy(
                climate_mode=zone,
                primary_strategy="Solar heat capture + envelope thermal protection",
                secondary_strategies=[
                    "High thermal mass storage for nocturnal heat release",
                    "Controlled minimal ventilation with heat retention",
                    "Minimized fenestration on non-solar orientations",
                    "Airtight entrance airlock vestibule",
                    "Perimeter thermal buffer zones on windward exposures"
                ],
                solar_capture=PriorityLevel.HIGH,
                thermal_mass=PriorityLevel.HIGH,
                insulation_priority=PriorityLevel.HIGH,
                ventilation_strategy="CONTROLLED_MINIMAL_PREHEATED",
                shading_strategy="MINIMAL_WINTER_EXPOSURE",
                opening_strategy="MINIMIZED_HIGH_PERFORMANCE_SOLAR_BIAS",
                airlock=True,
                thermal_buffer=True,
                explanation=explanation,
                rules_triggered=rules_triggered
            )

        # ======================================================================
        # 2. COLD (e.g. Srinagar; Mountain Valleys)
        # ======================================================================
        elif zone == ClimateZone.COLD:
            rules_triggered.extend([
                "R_C_01: Winter heating preservation with design minimum near or below freezing",
                "R_C_02: Solar gain maximization during heating months",
                "R_C_03: Moderate thermal mass damping",
                "R_C_04: Controlled seasonal ventilation"
            ])
            explanation = (
                f"The climate profile exhibits cold mountain/valley conditions with a winter design extreme "
                f"of {cold_ext:.1f}°C and substantial heating demand ({hdd:.0f} HDD18). "
                f"Passive design prioritizes direct solar heat collection and high thermal envelope insulation. "
                f"Thermal mass is leveraged at a moderate-to-high level to store daytime gains, while controlled "
                f"ventilation and air-sealed fenestration reduce convective losses during freezing nights."
            )
            return PassiveStrategy(
                climate_mode=zone,
                primary_strategy="Direct solar gain + thermal envelope retention",
                secondary_strategies=[
                    "Envelope insulation priority",
                    "Moderate thermal mass damping",
                    "Controlled seasonal ventilation",
                    "Airtight draft-resistant envelope construction"
                ],
                solar_capture=PriorityLevel.HIGH,
                thermal_mass=PriorityLevel.MODERATE,
                insulation_priority=PriorityLevel.HIGH,
                ventilation_strategy="CONTROLLED_SEASONAL",
                shading_strategy="SEASONAL_SOLAR_ACCESS",
                opening_strategy="BUFFERED_CONTROLLED",
                airlock=False,
                thermal_buffer=True,
                explanation=explanation,
                rules_triggered=rules_triggered
            )

        # ======================================================================
        # 3. HOT DRY (e.g. Jaisalmer, Thar Desert)
        # ======================================================================
        elif zone == ClimateZone.HOT_DRY:
            rules_triggered.extend([
                "R_HD_01: Summer daytime heat deflection against peak extreme > 38°C",
                "R_HD_02: Thermal mass temperature damping across diurnal cycle",
                "R_HD_03: Nocturnal convective flush cooling using desert night air",
                "R_HD_04: Solar radiation exclusion and fixed overhang shading",
                "R_HD_05: Daytime building closure to exclude hot ambient air"
            ])
            explanation = (
                f"The climate profile indicates extreme arid desert heat peaking at {hot_ext:.1f}°C with very low "
                f"average relative humidity ({avg_rh:.1f}%). The decisive thermodynamic opportunity is the large "
                f"diurnal temperature swing of {diurnal:.1f}°C. High thermal mass walls and roofs are deployed to "
                f"flatten the daytime thermal wave, combined with rigorous night-flushing ventilation to purge absorbed heat. "
                f"Daytime direct solar heat capture is minimized, and deep shading overhangs protect all glazed openings."
            )
            return PassiveStrategy(
                climate_mode=zone,
                primary_strategy="Thermal mass damping + nocturnal flush cooling",
                secondary_strategies=[
                    "Comprehensive solar radiation exclusion and deep overhangs",
                    "Diurnal delay via high-capacitance building envelope",
                    "Nocturnal convective night purge ventilation",
                    "Daytime building envelope closure against ambient heat waves"
                ],
                solar_capture=PriorityLevel.LOW,
                thermal_mass=PriorityLevel.HIGH,
                insulation_priority=PriorityLevel.MODERATE,
                ventilation_strategy="NIGHT_FLUSH_DAY_CLOSED",
                shading_strategy="DEEP_FIXED_OVERHANGS",
                opening_strategy="SHADED_CONTROLLED_NOCTURNAL_OPERABLE",
                airlock=False,
                thermal_buffer=False,
                explanation=explanation,
                rules_triggered=rules_triggered
            )

        # ======================================================================
        # 4. HOT HUMID (e.g. Chennai, Coastal Regions)
        # ======================================================================
        elif zone == ClimateZone.HOT_HUMID:
            rules_triggered.extend([
                "R_HH_01: Continuous convective physiological cooling",
                "R_HH_02: Maximize natural cross-ventilation apertures",
                "R_HH_03: Total solar radiation exclusion on roof and fenestration",
                "R_HH_04: Minimized thermal mass to prevent nocturnal radiant heat trapping"
            ])
            explanation = (
                f"The climate profile exhibits tropical coastal warm-humid conditions characterized by sustained high "
                f"relative humidity ({avg_rh:.1f}%) and narrow diurnal temperature variations ({diurnal:.1f}°C). "
                f"Because night temperatures remain elevated, heavy thermal mass is detrimental as it traps heat. "
                f"The primary passive cooling mechanism is continuous high-velocity natural cross-ventilation to enhance "
                f"sweat evaporation and convective bodily cooling, paired with extensive roof and facade shading."
            )
            return PassiveStrategy(
                climate_mode=zone,
                primary_strategy="Continuous cross-ventilation + comprehensive solar shading",
                secondary_strategies=[
                    "Extensive roof and wall solar reflectance / shading overhangs",
                    "Low thermal mass to avoid nocturnal heat storage",
                    "Maximized operable openings aligned with prevailing coastal breezes",
                    "Moisture-tolerant, breathable envelope design"
                ],
                solar_capture=PriorityLevel.MINIMIZED,
                thermal_mass=PriorityLevel.LOW,
                insulation_priority=PriorityLevel.LOW,
                ventilation_strategy="CONTINUOUS_NATURAL_CROSS_VENTILATION",
                shading_strategy="EXTENSIVE_SOLAR_PROTECTION",
                opening_strategy="MAXIMIZED_CROSS_VENTILATION",
                airlock=False,
                thermal_buffer=False,
                explanation=explanation,
                rules_triggered=rules_triggered
            )

        # ======================================================================
        # 5. TEMPERATE (e.g. Bengaluru, Pune)
        # ======================================================================
        elif zone == ClimateZone.TEMPERATE:
            rules_triggered.extend([
                "R_T_01: Balanced seasonal comfort adaptation",
                "R_T_02: Natural daylighting and controlled passive solar gain",
                "R_T_03: Moderate thermal mass stabilization",
                "R_T_04: Operable natural ventilation"
            ])
            explanation = (
                f"The climate profile reflects benign, temperate conditions with mild winters ({cold_ext:.1f}°C), "
                f"moderate summer peaks ({hot_ext:.1f}°C), and balanced relative humidity ({avg_rh:.1f}%). "
                f"The passive strategy focuses on balanced seasonal adaptation: harnessing natural daylighting and "
                f"moderate solar gain during cooler mornings, while utilizing operable natural ventilation and moderate "
                f"thermal mass to maintain indoor comfort with minimal mechanical assistance."
            )
            return PassiveStrategy(
                climate_mode=zone,
                primary_strategy="Balanced seasonal passive adaptation + natural ventilation",
                secondary_strategies=[
                    "Daylighting optimization with diffuse solar admission",
                    "Moderate thermal mass for steady-state indoor stabilization",
                    "Operable natural ventilation for seasonal comfort",
                    "Medium-level insulation and balanced fenestration"
                ],
                solar_capture=PriorityLevel.MODERATE,
                thermal_mass=PriorityLevel.MODERATE,
                insulation_priority=PriorityLevel.MODERATE,
                ventilation_strategy="BALANCED_NATURAL_SEASONAL",
                shading_strategy="ADAPTIVE_SEASONAL_OVERHANGS",
                opening_strategy="BALANCED_OPERABLE",
                airlock=False,
                thermal_buffer=False,
                explanation=explanation,
                rules_triggered=rules_triggered
            )

        # ======================================================================
        # 6. VARIABLE / COMPOSITE (e.g. Delhi, Northern Plains)
        # ======================================================================
        else:
            rules_triggered.extend([
                "R_V_01: Bi-modal seasonal switching between winter cold wave and summer heat wave",
                "R_V_02: Winter heat capture and summer solar shading",
                "R_V_03: High thermal mass for diurnal smoothing across transitions",
                "R_V_04: Flexible / operable ventilation controls"
            ])
            explanation = (
                f"The climate profile exhibits extreme bi-modal seasonal swings spanning {hot_ext - cold_ext:.1f}°C "
                f"(winter design {cold_ext:.1f}°C up to summer peak {hot_ext:.1f}°C). "
                f"No static envelope can satisfy both extremes simultaneously. The shelter requires an adaptive "
                f"dual-mode passive strategy: high thermal mass to buffer diurnal spikes, movable or seasonal shading "
                f"to admit winter sun while blocking scorching summer irradiation, and dual-mode ventilation that seals "
                f"tight during winter nights and peak summer afternoons while opening for nocturnal summer flush."
            )
            return PassiveStrategy(
                climate_mode=zone,
                primary_strategy="Adaptive seasonal mode-switching + high thermal mass buffering",
                secondary_strategies=[
                    "Dual-mode operable ventilation (closed during winter nights & summer peaks)",
                    "Movable or flexible seasonal shading",
                    "High thermal mass to stabilize multi-season diurnal swings",
                    "Balanced high insulation envelope to resist both hot and cold conductive extremes"
                ],
                solar_capture=PriorityLevel.MODERATE,
                thermal_mass=PriorityLevel.HIGH,
                insulation_priority=PriorityLevel.HIGH,
                ventilation_strategy="ADAPTIVE_DUAL_MODE_SEASONAL",
                shading_strategy="FLEXIBLE_OPERABLE_SEASONAL",
                opening_strategy="ADAPTIVE_SEALED_SUMMER_WINTER_OPERABLE_TRANSITION",
                airlock=False,
                thermal_buffer=True,
                explanation=explanation,
                rules_triggered=rules_triggered
            )
