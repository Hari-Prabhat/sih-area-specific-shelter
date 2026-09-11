"""
THERMOSHELTER AI - Simulation Adapter
======================================
Transforms upstream contracts (ClimateProfile from Member 1, ShelterDesign from Member 2)
into unified SimulationInput objects and connects them to the simulation engine,
returning standardized SimulationResult contracts.

Architecture:
  ClimateProfile (M1) + ShelterDesign (M2)
          ↓
  SimulationAdapter.to_simulation_input()
          ↓
    SimulationInput
          ↓
  SimulationAdapter.run_simulation_from_input()
          ↓
    SimulationResult (M3 -> M4/5)
"""

from typing import Any, Dict, Optional, Union
from services.contracts import (
    ClimateProfile,
    ShelterDesign,
    SimulationEnvelopeParameters,
    SimulationInput,
    SimulationResult,
    OptimizationInput,
    OptimizationResult,
    adapt_to_climate_profile,
    adapt_to_shelter_design,
    adapt_simulation_result,
    adapt_to_optimization_input,
    adapt_optimization_result,
)
from services.simulation_service import run_simulation


class SimulationAdapter:
    """
    Focused data transformation adapter bridging upstream Member 1 & 2 contracts
    to Member 3's simulation execution pipeline.
    """

    @classmethod
    def extract_envelope_parameters(cls, design: ShelterDesign) -> SimulationEnvelopeParameters:
        """
        Extracts lumped multi-layer thermal envelope parameters from canonical ShelterDesign.
        """
        p = design.to_simulation_parameters()
        return SimulationEnvelopeParameters(
            wall_u_value=p["wall_u_value"],
            roof_u_value=p["roof_u_value"],
            floor_u_value=p["floor_u_value"],
            window_u_value=p["window_u_value"],
            window_shgc=p["window_shgc"],
            window_area_m2=p["window_area_m2"],
            gross_wall_area_m2=p["gross_wall_area_m2"],
            roof_area_m2=p["roof_area_m2"],
            floor_area_m2=p["floor_area_m2"],
            volume_m3=p["volume_m3"],
            effective_thermal_capacity_j_k=p["effective_thermal_capacity_j_k"],
            orientation_deg=p["orientation_deg"],
            ach=p["ach"],
            occupants=p["occupants"],
            heat_per_person=p["heat_per_person"],
            roof_type=p["roof_type"],
            pitch_angle_deg=p["pitch_angle_deg"],
        )

    @classmethod
    def to_simulation_input(
        cls,
        climate: Union[ClimateProfile, Dict[str, Any]],
        design: Union[ShelterDesign, Dict[str, Any]],
        hours_to_simulate: int = 168,
        substeps: int = 60,
        initial_indoor_temp: float = 20.0,
    ) -> SimulationInput:
        """
        Adapts ClimateProfile and ShelterDesign into a validated SimulationInput.

        Parameters:
            climate: Validated ClimateProfile object or equivalent dictionary.
            design: Validated ShelterDesign object or equivalent dictionary.
            hours_to_simulate: Number of hours to simulate (default: 168).
            substeps: Integration substeps per hour (default: 60).
            initial_indoor_temp: Initial indoor temperature in °C (default: 20.0).

        Returns:
            SimulationInput: Fully validated simulation input configuration.
        """
        cp = adapt_to_climate_profile(climate)
        sd = adapt_to_shelter_design(design)
        env_params = cls.extract_envelope_parameters(sd)

        return SimulationInput(
            climate=cp,
            design=sd,
            hours_to_simulate=hours_to_simulate,
            substeps=substeps,
            initial_indoor_temp=initial_indoor_temp,
            envelope_parameters=env_params,
        )

    @staticmethod
    def run_simulation_from_input(sim_input: SimulationInput) -> SimulationResult:
        """
        Executes thermal simulation from a structured SimulationInput contract.
        Maps all parameters to the simulation engine and wraps the output in SimulationResult.

        Parameters:
            sim_input (SimulationInput): Validated simulation input contract.

        Returns:
            SimulationResult: Validated, typed simulation output contract.
        """
        if not isinstance(sim_input, SimulationInput):
            raise TypeError(f"Expected SimulationInput, got {type(sim_input)}")

        c = sim_input.climate
        d = sim_input.design

        glaze_val = d.glazing.id if hasattr(d.glazing, "id") else str(d.glazing)
        if "low_e" in glaze_val.lower() and "argon" in glaze_val.lower():
            glaze_str = "double_low_e"
        elif "double_clear" in glaze_val.lower():
            glaze_str = "double_clear"
        elif "single" in glaze_val.lower():
            glaze_str = "single_clear"
        elif "triple" in glaze_val.lower():
            glaze_str = "triple_low_e"
        else:
            glaze_str = glaze_val

        # Execute using the authoritative simulation service
        raw_res = run_simulation(
            city=c.city,
            length=d.length,
            width=d.width,
            height=d.height,
            wall_material=d.wall_material,
            wall_thickness_m=d.wall_thickness_m,
            insulation_thickness_m=d.insulation_thickness_m,
            insulation_conductivity=d.insulation_conductivity,
            window_area=d.window_area,
            glazing=glaze_str,
            orientation=d.orientation,
            roof_type=d.roof_type,
            pitch_angle_deg=d.pitch_angle_deg,
            shelter_model=d.shelter_model,
            roof_thickness_m=d.roof_thickness_m,
            roof_conductivity=d.roof_conductivity,
            roof_insulation_m=d.roof_insulation_m,
            shgc=d.shgc,
            ach=d.ach,
            occupants=d.occupants,
            heat_per_person=d.heat_per_person,
            initial_indoor_temp=sim_input.initial_indoor_temp,
            hours_to_simulate=sim_input.hours_to_simulate,
            substeps=sim_input.substeps,
            hourly_temperatures=c.hourly_temperature,
            hourly_direct_solar=c.hourly_direct_solar,
            hourly_diffuse_solar=c.hourly_diffuse_solar,
        )

        if "error" in raw_res:
            raise ValueError(f"Simulation execution failed: {raw_res['error']}")

        return adapt_simulation_result(raw_res)

    @classmethod
    def run_from_contracts(
        cls,
        climate: Union[ClimateProfile, Dict[str, Any]],
        design: Union[ShelterDesign, Dict[str, Any]],
        hours_to_simulate: int = 168,
        substeps: int = 60,
        initial_indoor_temp: float = 20.0,
    ) -> SimulationResult:
        """
        Convenience end-to-end entrypoint: converts contracts directly to SimulationResult.
        """
        sim_in = cls.to_simulation_input(
            climate=climate,
            design=design,
            hours_to_simulate=hours_to_simulate,
            substeps=substeps,
            initial_indoor_temp=initial_indoor_temp,
        )
        return cls.run_simulation_from_input(sim_in)


class OptimizationAdapter:
    """
    Focused data transformation adapter bridging upstream contracts and bounds
    to Member 3's Bayesian design optimization pipeline.
    """

    @staticmethod
    def to_optimization_input(
        city_or_config: Union[str, Dict[str, Any], OptimizationInput],
        home_type: str = "Permanent",
        length: float = 4.0,
        width: float = 3.0,
        height: float = 2.8,
        occupants: int = 2,
        n_trials: int = 40,
        **kwargs: Any,
    ) -> OptimizationInput:
        """
        Creates a validated OptimizationInput contract from keyword arguments or a dictionary.
        """
        if isinstance(city_or_config, OptimizationInput):
            return city_or_config
        elif isinstance(city_or_config, dict):
            return adapt_to_optimization_input(city_or_config)
        else:
            payload = {
                "city": city_or_config,
                "home_type": home_type,
                "length": length,
                "width": width,
                "height": height,
                "occupants": occupants,
                "n_trials": n_trials,
                **kwargs,
            }
            return adapt_to_optimization_input(payload)

    @classmethod
    def from_shelter_design(
        cls,
        design: Union[ShelterDesign, Dict[str, Any]],
        city_or_climate: Union[str, ClimateProfile, Dict[str, Any]] = "leh",
        home_type: Optional[str] = None,
        n_trials: int = 40,
        **kwargs: Any,
    ) -> OptimizationInput:
        """
        Creates a validated OptimizationInput contract from a canonical ShelterDesign digital twin.
        """
        sd = adapt_to_shelter_design(design)

        if isinstance(city_or_climate, ClimateProfile):
            city_str = city_or_climate.city
        elif isinstance(city_or_climate, dict):
            city_str = str(city_or_climate.get("city", "leh"))
        elif isinstance(city_or_climate, str):
            city_str = city_or_climate.strip().lower()
        else:
            city_str = "leh"

        ht = home_type
        if not ht:
            if hasattr(sd, "shelter_type") and sd.shelter_type:
                ht = "Temporary" if str(sd.shelter_type).lower().startswith("temp") else "Permanent"
            elif hasattr(sd, "requirements") and sd.requirements.permanence:
                ht = "Temporary" if str(sd.requirements.permanence).lower().startswith("temp") else "Permanent"
            else:
                ht = "Permanent"

        glaze_raw = kwargs.get("glazing")
        if not glaze_raw:
            if hasattr(sd, "glazing") and hasattr(sd.glazing, "id"):
                glaze_raw = sd.glazing.id
            elif hasattr(sd, "glazing") and isinstance(sd.glazing, str):
                glaze_raw = sd.glazing
            else:
                glaze_raw = "double_clear"

        orient_raw = kwargs.get("orientation")
        if not orient_raw:
            orient_raw = str(sd.orientation)

        payload = {
            "city": city_str,
            "home_type": ht,
            "length": sd.length,
            "width": sd.width,
            "height": sd.height,
            "wall_material": kwargs.get("wall_material", sd.wall_material),
            "glazing": glaze_raw,
            "orientation": orient_raw,
            "occupants": kwargs.get("occupants", sd.occupants),
            "min_insulation_m": kwargs.get("min_insulation_m", 0.0),
            "max_insulation_m": kwargs.get("max_insulation_m", 0.20),
            "min_window_area": kwargs.get("min_window_area", 0.5),
            "max_window_area": kwargs.get("max_window_area", None),
            "allowed_wall_materials": kwargs.get("allowed_wall_materials"),
            "allowed_glazings": kwargs.get("allowed_glazings"),
            "allowed_orientations": kwargs.get("allowed_orientations"),
            "n_trials": n_trials,
            "substeps": kwargs.get("substeps", 15),
            "hours_to_simulate": kwargs.get("hours_to_simulate", 168),
            "weights": kwargs.get("weights"),
        }

        return adapt_to_optimization_input(payload)

    @classmethod
    def candidate_to_shelter_design(
        cls,
        candidate: OptimizationCandidate,
        base_design: Optional[Union[ShelterDesign, Dict[str, Any]]] = None,
    ) -> ShelterDesign:
        """
        Converts an OptimizationCandidate into a fully validated canonical ShelterDesign.
        Preserves base geometry dimensions and requirements while applying optimized parameters.
        """
        return candidate.to_shelter_design(base_design=base_design)

    @staticmethod
    def run_optimization_from_input(opt_input: OptimizationInput) -> OptimizationResult:
        """
        Executes Bayesian multi-objective optimization using the structured OptimizationInput contract.
        """
        from services.optimize import optimize_shelter
        return optimize_shelter(opt_input)

    @classmethod
    def run_optimization_for_shelter(
        cls,
        design: Union[ShelterDesign, Dict[str, Any]],
        city_or_climate: Union[str, ClimateProfile, Dict[str, Any]] = "leh",
        n_trials: int = 40,
        **kwargs: Any,
    ) -> OptimizationResult:
        """
        Executes end-to-end optimization starting from canonical ShelterDesign digital twin.
        """
        opt_in = cls.from_shelter_design(
            design=design,
            city_or_climate=city_or_climate,
            n_trials=n_trials,
            **kwargs,
        )
        return cls.run_optimization_from_input(opt_in)

    @classmethod
    def run_from_specs(
        cls,
        city: str,
        home_type: str = "Permanent",
        length: float = 4.0,
        width: float = 3.0,
        height: float = 2.8,
        n_trials: int = 40,
        **kwargs: Any,
    ) -> OptimizationResult:
        """
        Convenience end-to-end optimization entrypoint.
        """
        opt_in = cls.to_optimization_input(
            city_or_config=city,
            home_type=home_type,
            length=length,
            width=width,
            height=height,
            n_trials=n_trials,
            **kwargs,
        )
        return cls.run_optimization_from_input(opt_in)


