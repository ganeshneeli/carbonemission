"""
Automated tests for Carbon Coach emission tools (Groq edition).
All calculation tools are pure Python — no API key needed.
"""
from __future__ import annotations

import pytest

from carbon_coach.agent import (
    EMISSION_FACTORS,
    calculate_electricity_emissions,
    calculate_food_emissions,
    calculate_travel_emissions,
    calculate_waste_emissions,
    get_reduction_suggestions,
    get_summary,
    log_activity,
)


# ---------------------------------------------------------------------------
# Travel
# ---------------------------------------------------------------------------
class TestTravelEmissions:
    def test_bus_12km(self):
        r = calculate_travel_emissions("bus", 12.0)
        assert "error" not in r
        assert r["emissions_kg_co2e"] == pytest.approx(1.2252, rel=1e-4)
        assert "DEFRA" in r["source"]

    def test_car_petrol_50km(self):
        r = calculate_travel_emissions("car_petrol", 50.0)
        assert r["emissions_kg_co2e"] == pytest.approx(8.51, rel=1e-4)

    def test_train_100km(self):
        r = calculate_travel_emissions("train", 100.0)
        assert r["emissions_kg_co2e"] == pytest.approx(4.10, rel=1e-4)

    def test_bicycle_zero(self):
        assert calculate_travel_emissions("bicycle", 25.0)["emissions_kg_co2e"] == 0.0

    def test_walking_zero(self):
        assert calculate_travel_emissions("walking", 5.0)["emissions_kg_co2e"] == 0.0

    def test_zero_distance(self):
        r = calculate_travel_emissions("bus", 0.0)
        assert "error" not in r
        assert r["emissions_kg_co2e"] == 0.0

    def test_negative_distance(self):
        assert "error" in calculate_travel_emissions("bus", -5.0)

    def test_unknown_mode(self):
        r = calculate_travel_emissions("spaceship", 10.0)
        assert "error" in r

    def test_mode_normalisation(self):
        assert "error" not in calculate_travel_emissions("Car_Petrol", 10.0)

    def test_all_modes(self):
        for mode in EMISSION_FACTORS["travel"]:
            r = calculate_travel_emissions(mode, 1.0)
            assert "error" not in r, f"Error for mode={mode}"
            assert r["emissions_kg_co2e"] >= 0.0


# ---------------------------------------------------------------------------
# Electricity
# ---------------------------------------------------------------------------
class TestElectricityEmissions:
    def test_india_5kwh(self):
        r = calculate_electricity_emissions(5.0, grid="IN_national")
        assert r["emissions_kg_co2e"] == pytest.approx(3.58, rel=1e-4)
        assert "CEA" in r["source"]

    def test_default_grid_placeholder(self):
        r = calculate_electricity_emissions(10.0, grid="default")
        expected = round(10.0 * EMISSION_FACTORS["electricity"]["default"]["kg_co2e_per_kwh"], 4)
        assert r["emissions_kg_co2e"] == pytest.approx(expected, rel=1e-4)
        assert r["placeholder"] is True

    def test_zero_kwh(self):
        assert calculate_electricity_emissions(0.0)["emissions_kg_co2e"] == 0.0

    def test_negative_kwh(self):
        assert "error" in calculate_electricity_emissions(-1.0)

    def test_unknown_grid(self):
        assert "error" in calculate_electricity_emissions(5.0, grid="MARS")


# ---------------------------------------------------------------------------
# Food
# ---------------------------------------------------------------------------
class TestFoodEmissions:
    def test_beef_200g(self):
        r = calculate_food_emissions("beef", 0.2)
        assert r["emissions_kg_co2e"] == pytest.approx(12.0, rel=1e-4)
        assert "Poore" in r["source"]

    def test_rice_1kg(self):
        assert calculate_food_emissions("rice", 1.0)["emissions_kg_co2e"] == pytest.approx(4.0, rel=1e-4)

    def test_zero_quantity(self):
        assert calculate_food_emissions("vegetables", 0.0)["emissions_kg_co2e"] == 0.0

    def test_negative_quantity(self):
        assert "error" in calculate_food_emissions("chicken", -0.5)

    def test_unknown_food(self):
        assert "error" in calculate_food_emissions("unicorn_steak", 1.0)

    def test_all_food_types(self):
        for food in EMISSION_FACTORS["food"]:
            r = calculate_food_emissions(food, 1.0)
            assert "error" not in r


# ---------------------------------------------------------------------------
# Waste
# ---------------------------------------------------------------------------
class TestWasteEmissions:
    def test_paper_2kg(self):
        r = calculate_waste_emissions("paper", 2.0)
        assert r["emissions_kg_co2e"] == pytest.approx(2.168, rel=1e-4)

    def test_recycled_less_than_general(self):
        r_gen = calculate_waste_emissions("general", 1.0)
        r_rec = calculate_waste_emissions("recycled", 1.0)
        assert r_rec["emissions_kg_co2e"] < r_gen["emissions_kg_co2e"]

    def test_negative_quantity(self):
        assert "error" in calculate_waste_emissions("general", -1.0)

    def test_unknown_waste(self):
        assert "error" in calculate_waste_emissions("nuclear_waste", 1.0)


# ---------------------------------------------------------------------------
# log_activity + get_summary
# ---------------------------------------------------------------------------
class TestLogAndSummary:
    def test_log_travel(self):
        acts = []
        d = calculate_travel_emissions("bus", 12.0)
        r = log_activity(acts, "travel", d)
        assert r["status"] == "saved"
        assert len(acts) == 1

    def test_log_multiple(self):
        acts = []
        log_activity(acts, "travel", calculate_travel_emissions("bus", 12.0))
        log_activity(acts, "electricity", calculate_electricity_emissions(5.0))
        assert len(acts) == 2

    def test_summary_total_matches(self):
        acts = []
        d1 = calculate_travel_emissions("bus", 12.0)
        d2 = calculate_electricity_emissions(5.0)
        log_activity(acts, "travel", d1)
        log_activity(acts, "electricity", d2)
        summary = get_summary(acts, "today")
        expected = round(d1["emissions_kg_co2e"] + d2["emissions_kg_co2e"], 4)
        assert summary["total_kg_co2e"] == pytest.approx(expected, rel=1e-6)

    def test_category_breakdown_sums_to_total(self):
        acts = []
        log_activity(acts, "travel",      calculate_travel_emissions("car_petrol", 10))
        log_activity(acts, "food",         calculate_food_emissions("chicken", 0.5))
        log_activity(acts, "waste",        calculate_waste_emissions("paper", 1))
        summary = get_summary(acts, "today")
        cat_sum = round(sum(summary["by_category"].values()), 4)
        assert cat_sum == pytest.approx(summary["total_kg_co2e"], rel=1e-6)

    def test_empty_session(self):
        summary = get_summary([], "today")
        assert summary["total_kg_co2e"] == 0.0
        assert summary["activity_count"] == 0

    def test_invalid_period(self):
        assert "error" in get_summary([], "last_year")

    def test_invalid_category(self):
        assert "error" in log_activity([], "banking", {"emissions_kg_co2e": 1.0})

    def test_missing_emissions(self):
        assert "error" in log_activity([], "travel", {"mode": "bus"})

    def test_negative_emissions(self):
        assert "error" in log_activity([], "travel", {"emissions_kg_co2e": -1.0})

    def test_this_week_period(self):
        acts = []
        log_activity(acts, "travel", calculate_travel_emissions("train", 50))
        summary = get_summary(acts, "this_week")
        assert summary["total_kg_co2e"] > 0

    def test_session_isolation(self):
        acts1, acts2 = [], []
        log_activity(acts1, "travel", calculate_travel_emissions("bus", 10))
        assert len(acts2) == 0


# ---------------------------------------------------------------------------
# Reduction suggestions
# ---------------------------------------------------------------------------
class TestSuggestions:
    def test_car_triggers_suggestions(self):
        acts = []
        log_activity(acts, "travel", calculate_travel_emissions("car_petrol", 20))
        result = get_reduction_suggestions(acts)
        assert len(result["suggestions"]) > 0
        assert result["total_potential_saving_kg_co2e"] > 0

    def test_bus_no_suggestion(self):
        acts = []
        log_activity(acts, "travel", calculate_travel_emissions("bus", 20))
        result = get_reduction_suggestions(acts)
        # Bus is already low — no travel suggestions expected
        assert all(s["category"] != "travel" for s in result["suggestions"])

    def test_electricity_suggestion(self):
        acts = []
        log_activity(acts, "electricity", calculate_electricity_emissions(10))
        result = get_reduction_suggestions(acts)
        assert any(s["category"] == "electricity" for s in result["suggestions"])

    def test_empty_activities(self):
        result = get_reduction_suggestions([])
        assert result["suggestions"] == []


# ---------------------------------------------------------------------------
# Precision
# ---------------------------------------------------------------------------
class TestPrecision:
    def test_travel_precision(self):
        val = calculate_travel_emissions("bus", 7.777)["emissions_kg_co2e"]
        assert val == round(val, 4)

    def test_electricity_precision(self):
        val = calculate_electricity_emissions(3.333)["emissions_kg_co2e"]
        assert val == round(val, 4)


# ---------------------------------------------------------------------------
# Food & Agent Dispatch Tests
# ---------------------------------------------------------------------------
class TestFoodChickenAndAgent:
    def test_chicken_200g(self):
        r = calculate_food_emissions("chicken", 0.2)
        assert "error" not in r
        assert r["emissions_kg_co2e"] == pytest.approx(1.38, rel=1e-4)
        assert "Poore & Nemecek" in r["source"]

    def test_coach_init_default_model(self):
        from carbon_coach.agent import GroqCarbonCoach
        coach = GroqCarbonCoach(api_key="gsk_dummy_test_key")
        assert coach.model == GroqCarbonCoach.DEFAULT_MODEL
        assert coach.MODEL == GroqCarbonCoach.DEFAULT_MODEL
        assert len(coach.activities) == 0

    def test_coach_dispatch_food(self):
        from carbon_coach.agent import GroqCarbonCoach
        coach = GroqCarbonCoach(api_key="gsk_dummy_test_key")
        res = coach._dispatch("calculate_food_emissions", '{"food_type": "chicken", "quantity_kg": 0.2}')
        assert res["emissions_kg_co2e"] == pytest.approx(1.38, rel=1e-4)
        assert len(coach.activities) == 1
        assert coach.activities[0]["category"] == "food"

    def test_fallback_tool_execution(self):
        from carbon_coach.agent import GroqCarbonCoach
        coach = GroqCarbonCoach(api_key="gsk_dummy_test_key")
        # Test fallback directly (when API tool calling is not supported)
        ans = coach._chat_without_native_tools("0.2 kg chicken", user_turn_idx=1)
        assert len(coach.activities) == 1
        assert coach.activities[0]["category"] == "food"
        assert coach.activities[0]["details"]["emissions_kg_co2e"] == pytest.approx(1.38, rel=1e-4)
        assert "1.38" in ans or "chicken" in ans.lower()


# ---------------------------------------------------------------------------
# Appliances & Meals
# ---------------------------------------------------------------------------
class TestAppliancesAndMeals:
    def test_ac_4hours(self):
        from carbon_coach.agent import calculate_appliance_emissions
        r = calculate_appliance_emissions("ac", 4.0)
        assert "error" not in r
        assert r["kwh"] == pytest.approx(6.0, rel=1e-4)
        assert r["emissions_kg_co2e"] == pytest.approx(4.296, rel=1e-4)
        assert "BEE India" in r["source"]

    def test_fan_8hours(self):
        from carbon_coach.agent import calculate_appliance_emissions
        r = calculate_appliance_emissions("fan", 8.0)
        assert "error" not in r
        # 8h * 0.075 kW = 0.6 kWh * 0.7160 = 0.4296
        assert r["kwh"] == pytest.approx(0.6, rel=1e-4)
        assert r["emissions_kg_co2e"] == pytest.approx(0.4296, rel=1e-4)

    def test_unknown_appliance(self):
        from carbon_coach.agent import calculate_appliance_emissions
        r = calculate_appliance_emissions("laser_cannon", 2.0)
        assert "error" in r

    def test_negative_hours(self):
        from carbon_coach.agent import calculate_appliance_emissions
        r = calculate_appliance_emissions("ac", -1.0)
        assert "error" in r

    def test_chicken_meal(self):
        from carbon_coach.agent import calculate_meal_emissions
        r = calculate_meal_emissions("chicken_meal", 2)
        assert "error" not in r
        assert r["emissions_kg_co2e"] == pytest.approx(3.70, rel=1e-4)

    def test_unknown_meal(self):
        from carbon_coach.agent import calculate_meal_emissions
        r = calculate_meal_emissions("alien_soup", 1)
        assert "error" in r


# ---------------------------------------------------------------------------
# Compound Activity Extraction & Multi-Agent
# ---------------------------------------------------------------------------
class TestCompoundExtractionAndMultiAgent:
    def test_hackathon_prompt_compound(self):
        from carbon_coach.agent import extract_activities_from_text
        prompt = "I travelled 12 km by bus today and used the AC for 4 hours."
        items = extract_activities_from_text(prompt)
        assert len(items) == 2
        categories = [cat for cat, _ in items]
        assert "travel" in categories
        assert "electricity" in categories

        bus_item = next(res for cat, res in items if cat == "travel")
        assert bus_item["emissions_kg_co2e"] == pytest.approx(1.2252, rel=1e-4)

        ac_item = next(res for cat, res in items if cat == "electricity")
        assert ac_item["emissions_kg_co2e"] == pytest.approx(4.2960, rel=1e-4)

    def test_tracker_and_coach_agents(self):
        from carbon_coach.agent import TrackerAgent, CoachAgent, calculate_travel_emissions
        acts = []
        tracker = TrackerAgent(acts)
        coach = CoachAgent(acts)

        r = calculate_travel_emissions("bus", 20.0)
        tracker.verify_and_log("travel", r)
        assert len(acts) == 1

        summary = tracker.get_summary("today")
        assert summary["total_kg_co2e"] == pytest.approx(2.042, rel=1e-4)

        bmark = coach.campus_benchmark(summary["total_kg_co2e"])
        assert bmark["meets_target"] is True


# ---------------------------------------------------------------------------
# Campus & Golden Eval Tests
# ---------------------------------------------------------------------------
class TestCampusAndGoldenEval:
    def test_campus_leaderboard(self):
        from carbon_coach.campus import get_campus_leaderboard
        board = get_campus_leaderboard("hostel", "Godavari Hostel", user_session_emissions=5.0)
        assert "rankings" in board
        assert len(board["rankings"]) == 5
        assert board["user_entry"]["name"] == "Godavari Hostel"
        assert board["rankings"][0]["rank"] == 1

    def test_golden_eval_suite_100_percent(self):
        from carbon_coach.golden_eval import run_golden_eval_suite
        res = run_golden_eval_suite()
        assert res["all_passed"] is True
        assert res["passed_cases"] == 12
        assert res["total_cases"] == 12
        assert res["accuracy_pct"] == 100.0

