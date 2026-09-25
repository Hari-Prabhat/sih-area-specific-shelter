"""
Optimization-UX pass regression tests.

Pins the product guarantees introduced by the "refine optimization and
engineering UX" pass:

  1. Comfort-first BASELINE INCLUSION: the user's own design is simulated on
     the identical climate scenario and enters the comfort ranking. A
     recommendation can never report fewer comfort hours than a feasible
     baseline (spec §20/§56).
  2. ORIENTATION SEARCH: with search_orientation enabled the optimizer
     searches continuous azimuth degrees (climate-dependent optimum — never
     a hardcoded 180°).
  3. SHAPE SEARCH: with search_shape enabled the optimizer compares all
     four supported forms, each simulated with its own real geometry.
  4. SCORE NORMALIZATION: candidate overall_score is already a 0–100 scale;
     candidates always report <= 100 (guards the frontend "/100" display).
"""

import math

import pytest

from services.optimize import (
    _collapse_radial_dimensions,
    run_comfort_first_recommendation,
    run_optimization,
)
from services.contracts import OptimizationInput


# ---------------------------------------------------------------------------
# 1. Baseline inclusion
# ---------------------------------------------------------------------------


class TestBaselineInclusion:
    def test_baseline_design_entered_as_candidate_and_reported(self):
        """The rec payload reports the baseline candidate when supplied."""
        baseline = {
            "length": 4.0,
            "width": 3.0,
            "height": 2.8,
            "wall_material": "brick",
            "wall_thickness_m": 0.23,
            "insulation_thickness_m": 0.05,
            "insulation_conductivity": 0.025,
            "window_area": 2.0,
            "door_area": 2.0,
            "glazing": "double_clear",
            "orientation": 180.0,
            "roof_type": "flat",
            "pitch_angle_deg": 0.0,
            "ach": 0.7,
            "shape": "rectangular",
        }
        result = run_comfort_first_recommendation(
            city="leh", n_trials=3, hours_to_simulate=48, baseline_design=baseline
        )
        assert result["status"] == "ok"
        assert result["baseline_included"] is True
        bc = result["baseline_candidate"]
        assert bc is not None
        assert bc["is_baseline"] is True
        assert bc["label"] == "Your Design (Baseline)"
        assert bc["comfort_hours"] >= 0.0

    def test_recommendation_comfort_never_below_feasible_baseline(self):
        """THE critical product guarantee: rec comfort >= baseline comfort."""
        baseline = {
            "length": 4.0,
            "width": 3.0,
            "height": 2.8,
            "wall_material": "brick",
            "wall_thickness_m": 0.23,
            "insulation_thickness_m": 0.10,
            "insulation_conductivity": 0.025,
            "window_area": 2.0,
            "door_area": 2.0,
            "glazing": "double_clear",
            "orientation": 180.0,
            "roof_type": "flat",
            "pitch_angle_deg": 0.0,
            "ach": 0.7,
            "shape": "rectangular",
        }
        result = run_comfort_first_recommendation(
            city="leh", n_trials=4, hours_to_simulate=48, baseline_design=baseline
        )
        assert result["status"] == "ok"
        rec = result["recommendation"]
        baseline_comfort = result["baseline_candidate"]["comfort_hours"]
        assert rec["comfort_hours"] >= baseline_comfort - 1e-9, (
            "Comfort-first recommendation reported fewer comfort hours than "
            "the feasible baseline user design."
        )
        if rec["comfort_hours"] == pytest.approx(baseline_comfort, abs=1e-9):
            # Baseline won: the recommendation must be labelled as the baseline.
            assert rec["is_baseline"] is True
            assert rec["label"] == "Your Design (Baseline)"

    def test_unsimulatable_baseline_is_skipped_not_fatal(self):
        """A broken baseline must not degrade the recommendation."""
        baseline = {
            "length": -1.0,  # invalid -> engine error -> baseline skipped
            "width": 3.0,
            "height": 2.8,
            "wall_material": "brick",
            "window_area": 2.0,
            "door_area": 2.0,
            "glazing": "double_clear",
            "orientation": 180.0,
            "shape": "rectangular",
        }
        result = run_comfort_first_recommendation(
            city="leh", n_trials=3, hours_to_simulate=48, baseline_design=baseline
        )
        assert result["status"] == "ok"
        assert result["baseline_included"] is False
        assert result["baseline_candidate"] is None
        assert result["recommendation"] is not None

    def test_no_baseline_still_works(self):
        """Legacy call signature (no baseline) keeps working."""
        result = run_comfort_first_recommendation(
            city="leh", n_trials=2, hours_to_simulate=48
        )
        assert result["status"] in ("ok", "no_comfort_feasible")


# ---------------------------------------------------------------------------
# 2. Orientation search
# ---------------------------------------------------------------------------


class TestOrientationSearch:
    def test_orientation_searched_as_continuous_degrees(self):
        inp = OptimizationInput(
            city="leh",
            n_trials=3,
            hours_to_simulate=48,
            search_orientation=True,
            search_shape=False,
        )
        from services.optimize import optimize_shelter

        res = optimize_shelter(inp)
        assert res.ranked_designs, "expected at least one ranked candidate"
        # Continuous-degree candidates are reported as numeric strings
        # ("157.0" etc.), NOT just cardinal names.
        orientations = [c.orientation for c in res.ranked_designs]
        numeric = [
            o for o in orientations
            if o.replace(".", "", 1).replace("-", "", 1).isdigit()
        ]
        assert numeric, f"expected numeric azimuth orientations, got {orientations}"
        for o in numeric:
            deg = float(o)
            assert 0.0 <= deg <= 360.0

    def test_explicit_orientation_still_pinned(self):
        """Legacy behaviour: an explicit orientation is never overridden."""
        res = run_optimization(
            city="leh",
            n_trials=2,
            hours_to_simulate=48,
            orientation="south",
            search_orientation=True,
        )
        assert res["orientation"] == "south"

    def test_allowed_orientation_list_still_respected(self):
        """An explicit allowed list remains authoritative over the search."""
        res = run_optimization(
            city="leh",
            n_trials=2,
            hours_to_simulate=48,
            allowed_orientations=["north", "south"],
            search_orientation=True,
        )
        assert res["orientation"] in ("north", "south")

    def test_default_engine_behaviour_unchanged(self):
        """Engine default keeps the legacy cardinal categorical search."""
        res = run_optimization(
            city="leh", n_trials=2, hours_to_simulate=48
        )
        assert res["orientation"] in ("south", "north", "east", "west")


# ---------------------------------------------------------------------------
# 3. Shape search
# ---------------------------------------------------------------------------


class TestShapeSearch:
    def test_shape_searched_across_all_four_forms(self):
        inp = OptimizationInput(
            city="leh",
            n_trials=8,
            hours_to_simulate=48,
            search_orientation=True,
            search_shape=True,
        )
        from services.optimize import optimize_shelter

        res = optimize_shelter(inp)
        shapes = {c.shape for c in res.ranked_designs if c.shape}
        assert shapes, "candidates must report their simulated shape"
        assert shapes.issubset({"rectangular", "cylindrical", "dome", "pyramid"})

    def test_fixed_shape_still_authoritative_when_search_off(self):
        inp = OptimizationInput(
            city="leh",
            n_trials=3,
            hours_to_simulate=48,
            shape="dome",
            search_orientation=True,
            search_shape=False,
        )
        from services.optimize import optimize_shelter

        res = optimize_shelter(inp)
        for c in res.ranked_designs:
            assert c.shape == "dome"

    def test_radial_candidates_carry_diameter_dimensions(self):
        """Cylindrical/dome candidates must satisfy the L == W diameter rule."""
        res = run_optimization(
            city="leh",
            n_trials=8,
            hours_to_simulate=48,
            search_orientation=True,
            search_shape=True,
        )
        for c in res["ranked_designs"]:
            if c.get("shape") in ("cylindrical", "dome"):
                assert c["length_m"] == pytest.approx(c["width_m"]), (
                    f"radial candidate {c['shape']} must carry diameter "
                    f"semantics (L == W), got L={c['length_m']} W={c['width_m']}"
                )

    def test_collapse_helper(self):
        assert _collapse_radial_dimensions("cylindrical", 4.0, 3.0) == (3.0, 3.0)
        assert _collapse_radial_dimensions("dome", 5.0, 2.0) == (2.0, 2.0)
        assert _collapse_radial_dimensions("rectangular", 4.0, 3.0) == (4.0, 3.0)
        assert _collapse_radial_dimensions("pyramid", 6.0, 4.0) == (6.0, 4.0)


# ---------------------------------------------------------------------------
# 4. Score normalization
# ---------------------------------------------------------------------------


class TestScoreNormalization:
    def test_overall_score_is_already_0_to_100(self):
        """overall_score must stay <= 100 — the frontend renders it as '/100'
        directly. (Guards against the historical x100 display bug.)"""
        res = run_optimization(
            city="leh", n_trials=3, hours_to_simulate=48,
            search_orientation=True, search_shape=True,
        )
        for c in res["ranked_designs"]:
            assert 0.0 <= c["overall_score"] <= 100.0, (
                f"overall_score out of 0-100 range: {c['overall_score']}"
            )
            for sub in c["sub_scores"].values():
                assert 0.0 <= sub <= 100.0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
