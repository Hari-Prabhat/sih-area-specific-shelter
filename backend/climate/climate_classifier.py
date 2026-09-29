"""
THERMOSHELTER AI - Climate Classification Engine
================================================
Centralized, explainable, physics-grounded classifier mapping meteorological metrics
into the 6 required project categories:
  - EXTREME COLD
  - COLD
  - HOT DRY
  - HOT HUMID
  - TEMPERATE
  - VARIABLE
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.climate.schemas import (
    ClimateZone,
    DataConfidence,
    DesignExtremes,
    HumidityData,
    SolarData,
    TemperatureProfile,
    WindData,
)


class ClassificationExplanation(BaseModel):
    """Diagnostic details and physical metrics triggering a classification."""
    zone: ClimateZone
    explanation: str
    primary_criteria: List[str]
    metrics_summary: Dict[str, Any]
    confidence: DataConfidence = Field(DataConfidence.HIGH)


class ClimateClassifier:
    """
    Classifies climate profiles based on thermal extremes, moisture, diurnal swings,
    and degree-day demands. Thresholds align with National Building Code (NBC) 2016,
    Bureau of Energy Efficiency (BEE) ECBC, and ASHRAE Fundamentals.
    """

    # --------------------------------------------------------------------------
    # CENTRALIZED THRESHOLDS (Documented implementation baselines)
    # --------------------------------------------------------------------------
    # Extreme Cold: severe sub-zero design extremes or severe alpine heating demand
    EXTREME_COLD_DESIGN_TEMP_MAX = -10.0   # Cold extreme <= -10°C (e.g., Leh -18.5°C)
    EXTREME_COLD_MIN_OBSERVED_MAX = -15.0  # Observed min <= -15°C
    EXTREME_COLD_HDD18_MIN = 4000.0        # Annual Heating Degree Days >= 4000

    # Hot Dry: scorching summer extremes, low humidity (<45%), high diurnal swing (>=12°C)
    HOT_DRY_SUMMER_TEMP_MIN = 38.0         # Hot extreme >= 38°C (e.g., Jaisalmer 46°C)
    HOT_DRY_RH_MAX = 45.0                  # Average RH <= 45% (arid desert)
    HOT_DRY_DIURNAL_MIN = 12.0             # Diurnal swing >= 12°C

    # Hot Humid: persistent warmth, high moisture (>=65%), narrow diurnal range
    HOT_HUMID_WINTER_MIN = 15.0            # Cold extreme >= 15°C (no heating needed)
    HOT_HUMID_SUMMER_MIN = 32.0            # Hot extreme >= 32°C
    HOT_HUMID_RH_MIN = 65.0                # Average RH >= 65% (e.g., Chennai 74%)
    HOT_HUMID_DIURNAL_MAX = 12.0           # Diurnal swing <= 12°C

    # Variable (Composite): large seasonal swing between winter cold wave and summer heat wave with seasonal moisture
    VARIABLE_SEASONAL_SWING_MIN = 30.0     # Summer max - winter min >= 30°C (e.g., Delhi 5°C to 43.5°C)
    VARIABLE_SUMMER_MIN = 38.0             # Summer extreme >= 38°C
    VARIABLE_WINTER_MAX = 10.0             # Winter extreme <= 10°C

    # Cold: mild-to-moderate freezing or cold mountain conditions
    COLD_DESIGN_TEMP_MAX = 2.0             # Cold extreme <= 2°C (e.g., Srinagar -4.0°C)
    COLD_ANNUAL_MEAN_MAX = 16.0            # Annual mean <= 16°C
    COLD_HDD18_MIN = 2200.0                # Annual Heating Degree Days >= 2200

    # Temperate: mild year-round thermal baseline
    TEMPERATE_MEAN_MIN = 17.0              # Annual mean between 17°C and 26°C
    TEMPERATE_MEAN_MAX = 26.0
    TEMPERATE_WINTER_MIN = 7.0             # Winter extreme >= 7°C
    TEMPERATE_SUMMER_MAX = 35.0            # Summer extreme <= 35°C

    @classmethod
    def classify(
        cls,
        temperature: TemperatureProfile,
        humidity: HumidityData,
        design_extremes: DesignExtremes,
        solar: Optional[SolarData] = None,
        wind: Optional[WindData] = None
    ) -> ClassificationExplanation:
        """
        Evaluates physical climate characteristics and assigns the appropriate ClimateZone.
        Returns the classification alongside a comprehensive engineering rationale.
        """
        cold_extreme = design_extremes.cold_extreme
        hot_extreme = design_extremes.hot_extreme
        annual_mean = temperature.annual_mean_temperature
        min_temp = temperature.minimum_temperature
        max_temp = temperature.maximum_temperature
        avg_rh = humidity.average_relative_humidity
        diurnal_range = temperature.diurnal_range_mean or abs(max_temp - min_temp) / 2.0
        hdd18 = design_extremes.heating_degree_days_18c or 0.0
        cdd18 = design_extremes.cooling_degree_days_18c or 0.0
        seasonal_swing = hot_extreme - cold_extreme

        criteria_triggered: List[str] = []
        metrics_summary = {
            "cold_extreme_c": cold_extreme,
            "hot_extreme_c": hot_extreme,
            "annual_mean_c": annual_mean,
            "relative_humidity_pct": avg_rh,
            "diurnal_range_c": diurnal_range,
            "seasonal_swing_c": seasonal_swing,
            "hdd18": hdd18,
            "cdd18": cdd18
        }

        # ----------------------------------------------------------------------
        # 1. TEST EXTREME COLD
        # ----------------------------------------------------------------------
        is_extreme_cold = (
            cold_extreme <= cls.EXTREME_COLD_DESIGN_TEMP_MAX
            or min_temp <= cls.EXTREME_COLD_MIN_OBSERVED_MAX
            or (hdd18 >= cls.EXTREME_COLD_HDD18_MIN and annual_mean <= 8.0)
        )
        if is_extreme_cold:
            if cold_extreme <= cls.EXTREME_COLD_DESIGN_TEMP_MAX:
                criteria_triggered.append(f"Design winter extreme ({cold_extreme:.1f}°C) <= threshold ({cls.EXTREME_COLD_DESIGN_TEMP_MAX:.1f}°C)")
            if min_temp <= cls.EXTREME_COLD_MIN_OBSERVED_MAX:
                criteria_triggered.append(f"Historical minimum temperature ({min_temp:.1f}°C) <= threshold ({cls.EXTREME_COLD_MIN_OBSERVED_MAX:.1f}°C)")
            if hdd18 >= cls.EXTREME_COLD_HDD18_MIN:
                criteria_triggered.append(f"Heating degree days HDD18 ({hdd18:.0f}) >= threshold ({cls.EXTREME_COLD_HDD18_MIN:.0f})")

            explanation = (
                f"The site exhibits severe alpine/high-altitude cold conditions with a winter design extreme "
                f"of {cold_extreme:.1f}°C and {hdd18:.0f} heating degree days. Unprotected structures face critical "
                f"hypothermia risk and extreme conductive heat loss. Solar heat gain, envelope thermal protection, "
                f"airlocks, and thermal buffer zones are mandatory."
            )
            return ClassificationExplanation(
                zone=ClimateZone.EXTREME_COLD,
                explanation=explanation,
                primary_criteria=criteria_triggered,
                metrics_summary=metrics_summary,
                confidence=DataConfidence.HIGH
            )

        # ----------------------------------------------------------------------
        # 2. TEST HOT DRY (Arid Desert)
        # ----------------------------------------------------------------------
        is_hot_dry = (
            hot_extreme >= cls.HOT_DRY_SUMMER_TEMP_MIN
            and avg_rh <= cls.HOT_DRY_RH_MAX
            and diurnal_range >= cls.HOT_DRY_DIURNAL_MIN
        )
        if is_hot_dry:
            criteria_triggered.append(f"Summer design extreme ({hot_extreme:.1f}°C) >= {cls.HOT_DRY_SUMMER_TEMP_MIN:.1f}°C")
            criteria_triggered.append(f"Average relative humidity ({avg_rh:.1f}%) <= {cls.HOT_DRY_RH_MAX:.1f}% (Arid Desert)")
            criteria_triggered.append(f"Diurnal temperature range ({diurnal_range:.1f}°C) >= {cls.HOT_DRY_DIURNAL_MIN:.1f}°C")

            explanation = (
                f"The site exhibits arid desert conditions with intense summer heat peaking at {hot_extreme:.1f}°C "
                f"and low relative humidity ({avg_rh:.1f}%). The large diurnal swing of {diurnal_range:.1f}°C enables "
                f"substantial thermal mass storage and nocturnal radiative/convective cooling."
            )
            return ClassificationExplanation(
                zone=ClimateZone.HOT_DRY,
                explanation=explanation,
                primary_criteria=criteria_triggered,
                metrics_summary=metrics_summary,
                confidence=DataConfidence.HIGH
            )

        # ----------------------------------------------------------------------
        # 3. TEST HOT HUMID (Coastal / Tropical)
        # ----------------------------------------------------------------------
        is_hot_humid = (
            cold_extreme >= cls.HOT_HUMID_WINTER_MIN
            and hot_extreme >= cls.HOT_HUMID_SUMMER_MIN
            and avg_rh >= cls.HOT_HUMID_RH_MIN
            and diurnal_range <= cls.HOT_HUMID_DIURNAL_MAX
        )
        if is_hot_humid:
            criteria_triggered.append(f"Winter design temperature ({cold_extreme:.1f}°C) >= {cls.HOT_HUMID_WINTER_MIN:.1f}°C (zero heating requirement)")
            criteria_triggered.append(f"Summer design extreme ({hot_extreme:.1f}°C) >= {cls.HOT_HUMID_SUMMER_MIN:.1f}°C")
            criteria_triggered.append(f"Average relative humidity ({avg_rh:.1f}%) >= {cls.HOT_HUMID_RH_MIN:.1f}%")

            explanation = (
                f"The site exhibits tropical warm-humid conditions with high relative humidity ({avg_rh:.1f}%) "
                f"and sustained warmth (winter low {cold_extreme:.1f}°C, summer peak {hot_extreme:.1f}°C). "
                f"Thermal mass is ineffective due to warm nights; continuous natural cross-ventilation and extensive "
                f"shading are paramount for physiological cooling."
            )
            return ClassificationExplanation(
                zone=ClimateZone.HOT_HUMID,
                explanation=explanation,
                primary_criteria=criteria_triggered,
                metrics_summary=metrics_summary,
                confidence=DataConfidence.HIGH
            )

        # ----------------------------------------------------------------------
        # 4. TEST VARIABLE / COMPOSITE (Checked for seasonal bi-modal swings)
        # ----------------------------------------------------------------------
        is_variable = (
            seasonal_swing >= cls.VARIABLE_SEASONAL_SWING_MIN
            and hot_extreme >= cls.VARIABLE_SUMMER_MIN
            and cold_extreme <= cls.VARIABLE_WINTER_MAX
        )
        if is_variable:
            criteria_triggered.append(f"Seasonal temperature swing ({seasonal_swing:.1f}°C) >= threshold ({cls.VARIABLE_SEASONAL_SWING_MIN:.1f}°C)")
            criteria_triggered.append(f"Summer design extreme ({hot_extreme:.1f}°C) >= {cls.VARIABLE_SUMMER_MIN:.1f}°C")
            criteria_triggered.append(f"Winter design extreme ({cold_extreme:.1f}°C) <= {cls.VARIABLE_WINTER_MAX:.1f}°C")

            explanation = (
                f"The site exhibits extreme bi-modal seasonal swings spanning {seasonal_swing:.1f}°C "
                f"(winter design {cold_extreme:.1f}°C to summer design {hot_extreme:.1f}°C). "
                f"A single fixed strategy is insufficient; adaptive envelope and operational mode-switching are required."
            )
            return ClassificationExplanation(
                zone=ClimateZone.VARIABLE,
                explanation=explanation,
                primary_criteria=criteria_triggered,
                metrics_summary=metrics_summary,
                confidence=DataConfidence.HIGH
            )

        # ----------------------------------------------------------------------
        # 5. TEST COLD (Non-extreme, sub-alpine)
        # ----------------------------------------------------------------------
        is_cold = (
            cold_extreme <= cls.COLD_DESIGN_TEMP_MAX
            or annual_mean <= cls.COLD_ANNUAL_MEAN_MAX
            or hdd18 >= cls.COLD_HDD18_MIN
        )
        if is_cold:
            criteria_triggered.append(f"Cold extreme ({cold_extreme:.1f}°C) <= {cls.COLD_DESIGN_TEMP_MAX:.1f}°C or annual mean ({annual_mean:.1f}°C) <= {cls.COLD_ANNUAL_MEAN_MAX:.1f}°C")
            if hdd18 >= cls.COLD_HDD18_MIN:
                criteria_triggered.append(f"Heating degree days ({hdd18:.0f}) indicates dominant winter heating load")

            explanation = (
                f"The site exhibits cold mountain or valley climate characteristics with winter design temperatures "
                f"of {cold_extreme:.1f}°C and significant heating demand ({hdd18:.0f} HDD18). Solar heat collection, "
                f"insulation, and controlled ventilation are required to maintain indoor thermal comfort."
            )
            return ClassificationExplanation(
                zone=ClimateZone.COLD,
                explanation=explanation,
                primary_criteria=criteria_triggered,
                metrics_summary=metrics_summary,
                confidence=DataConfidence.HIGH
            )

        # ----------------------------------------------------------------------
        # 6. TEST TEMPERATE (Mild baseline)
        # ----------------------------------------------------------------------
        criteria_triggered.append(f"Annual mean temperature ({annual_mean:.1f}°C) and moderate extremes fall within temperate comfort bands")
        explanation = (
            f"The site exhibits moderate, temperate conditions with mild winters ({cold_extreme:.1f}°C), "
            f"temperate summers ({hot_extreme:.1f}°C), and balanced relative humidity ({avg_rh:.1f}%). "
            f"Balanced passive solar gain, natural daylighting, and seasonal ventilation provide comfortable habitability."
        )
        return ClassificationExplanation(
            zone=ClimateZone.TEMPERATE,
            explanation=explanation,
            primary_criteria=criteria_triggered,
            metrics_summary=metrics_summary,
            confidence=DataConfidence.HIGH
        )
