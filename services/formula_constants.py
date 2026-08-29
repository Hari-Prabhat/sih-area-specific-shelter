"""
THERMOSHELTER AI - Central Formula Constants & Configurable Defaults
=====================================================================
Single source of truth for all physical constants, standard SI conversion factors,
and engineering baseline defaults used across the simulation and optimization engines.
"""

# =====================================================================
# FUNDAMENTAL PHYSICAL CONSTANTS (SI Units)
# =====================================================================

# Stefan-Boltzmann constant (W/(m²·K⁴))
# Source: CODATA 2018 recommended values
STEFAN_BOLTZMANN: float = 5.670374419e-8

# Standard density of dry air at sea level, 15°C and 101.325 kPa (kg/m³)
# Source: ISO 2533 / Standard Atmosphere
AIR_DENSITY_DEFAULT: float = 1.225

# Specific heat capacity of dry air at constant pressure, room temperature (J/(kg·K))
# Source: ASHRAE Handbook - Fundamentals (Chapter 1)
AIR_SPECIFIC_HEAT: float = 1005.0

# Number of seconds in one standard hour (s)
SECONDS_PER_HOUR: float = 3600.0

# Absolute zero temperature offset between Celsius and Kelvin (K)
# Source: BIPM SI Brochure
CELSIUS_TO_KELVIN: float = 273.15

# Joules in one kilowatt-hour (J/kWh)
JOULES_PER_KWH: float = 3.6e6


# =====================================================================
# CONFIGURABLE ENGINEERING DEFAULTS
# =====================================================================

# Default air exchange rate for emergency/field shelters (Air Changes per Hour, ACH)
# Assumption: Moderately sealed temporary field shelter envelope
DEFAULT_ACH: float = 0.5

# Lower thermal comfort limit for cold-climate / high-altitude living spaces (°C)
# Source: WHO Housing and Health Guidelines / SP 41 (S&T)
DEFAULT_COMFORT_MIN: float = 18.0

# Upper thermal comfort limit for living spaces (°C)
# Source: ASHRAE Standard 55 / NBC 2016
DEFAULT_COMFORT_MAX: float = 24.0

# Sensible metabolic heat generation per sedentary/light-activity occupant (W/person)
# Source: ISO 7730 / ASHRAE Standard 55 (approx 1.2 met for seated/resting adult)
DEFAULT_OCCUPANT_HEAT_GAIN: float = 80.0

# Interior surface film convective + radiative thermal resistance for vertical walls (m²·K/W)
# Source: ISO 6946 / IS 3792
DEFAULT_R_INSIDE_VERTICAL: float = 0.13

# Exterior surface film convective + radiative thermal resistance for vertical walls (m²·K/W)
# Source: ISO 6946 (standard 4 m/s wind exposure)
DEFAULT_R_OUTSIDE_VERTICAL: float = 0.04

# Interior surface film thermal resistance for horizontal ceiling / roof with upward heat flow (m²·K/W)
# Source: ISO 6946
DEFAULT_R_INSIDE_HORIZONTAL: float = 0.10

# Exterior surface film thermal resistance for horizontal roof (m²·K/W)
# Source: ISO 6946
DEFAULT_R_OUTSIDE_HORIZONTAL: float = 0.04
