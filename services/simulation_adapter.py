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

    @staticmethod
    def to_simulation_input(
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

        return SimulationInput(
            climate=cp,
            design=sd,
            hours_to_simulate=hours_to_simulate,
            substeps=substeps,
            initial_indoor_temp=initial_indoor_temp,
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
            glazing=d.glazing,
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

    @staticmethod
    def run_optimization_from_input(opt_input: OptimizationInput) -> OptimizationResult:
        """
        Executes Bayesian multi-objective optimization using the structured OptimizationInput contract.
        """
        from services.optimize import optimize_shelter
        return optimize_shelter(opt_input)

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

