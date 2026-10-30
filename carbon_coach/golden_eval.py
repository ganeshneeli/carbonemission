"""
Golden Evaluation Suite for DevFest 2026 Hackathon: Carbon Coach.

Validates that ALL emission calculations match official IPCC, DEFRA, CEA India, and Poore & Nemecek factors
with zero hallucination and strict mathematical precision.
"""
from __future__ import annotations

import math
from typing import Any

from carbon_coach.agent import (
    calculate_travel_emissions,
    calculate_electricity_emissions,
    calculate_appliance_emissions,
    calculate_food_emissions,
    calculate_meal_emissions,
    calculate_waste_emissions,
    get_reduction_suggestions,
    log_activity,
)

GOLDEN_TEST_CASES = [
    {
        "id": "TC-01",
        "name": "Local Bus Journey (12 km)",
        "category": "Travel",
        "input_desc": "12 km by local bus",
        "function": calculate_travel_emissions,
        "kwargs": {"mode": "bus", "distance_km": 12.0},
        "expected_kg_co2e": 1.2252,
        "expected_source": "DEFRA 2023",
        "formula": "12.0 km × 0.1021 kg CO₂e/km",
    },
    {
        "id": "TC-02",
        "name": "Air Conditioner Use (4 hours)",
        "category": "Electricity",
        "input_desc": "4 hours AC (1.5 kW split)",
        "function": calculate_appliance_emissions,
        "kwargs": {"appliance": "ac", "hours": 4.0},
        "expected_kg_co2e": 4.2960,
        "expected_source": "BEE India 3-star AC average (1.5 kW) + CEA India Version 18 (2023)",
        "formula": "4.0 h × 1.5 kW = 6.0 kWh × 0.7160 kg CO₂e/kWh",
    },
    {
        "id": "TC-03",
        "name": "Poultry Food Consumption (0.2 kg chicken)",
        "category": "Food",
        "input_desc": "0.2 kg chicken",
        "function": calculate_food_emissions,
        "kwargs": {"food_type": "chicken", "quantity_kg": 0.2},
        "expected_kg_co2e": 1.3800,
        "expected_source": "Poore & Nemecek 2018",
        "formula": "0.2 kg × 6.9000 kg CO₂e/kg",
    },
    {
        "id": "TC-04",
        "name": "Direct Electricity Meter (5 kWh)",
        "category": "Electricity",
        "input_desc": "5 kWh national grid (CEA)",
        "function": calculate_electricity_emissions,
        "kwargs": {"kwh": 5.0, "grid": "IN_national"},
        "expected_kg_co2e": 3.5800,
        "expected_source": "CEA India Version 18 (2023)",
        "formula": "5.0 kWh × 0.7160 kg CO₂e/kWh",
    },
    {
        "id": "TC-05",
        "name": "Paper Waste Landfill (2 kg)",
        "category": "Waste",
        "input_desc": "2 kg paper waste to landfill",
        "function": calculate_waste_emissions,
        "kwargs": {"waste_type": "paper", "quantity_kg": 2.0},
        "expected_kg_co2e": 2.1680,
        "expected_source": "IPCC 2006",
        "formula": "2.0 kg × 1.0840 kg CO₂e/kg",
    },
    {
        "id": "TC-06",
        "name": "Petrol Car Commute (50 km)",
        "category": "Travel",
        "input_desc": "50 km average petrol car",
        "function": calculate_travel_emissions,
        "kwargs": {"mode": "car_petrol", "distance_km": 50.0},
        "expected_kg_co2e": 8.5100,
        "expected_source": "DEFRA 2023 Table 7",
        "formula": "50.0 km × 0.1702 kg CO₂e/km",
    },
    {
        "id": "TC-07",
        "name": "National Rail Transit (100 km)",
        "category": "Travel",
        "input_desc": "100 km electric train transit",
        "function": calculate_travel_emissions,
        "kwargs": {"mode": "train", "distance_km": 100.0},
        "expected_kg_co2e": 4.1000,
        "expected_source": "DEFRA 2023 Table 8",
        "formula": "100.0 km × 0.0410 kg CO₂e/km",
    },
    {
        "id": "TC-08",
        "name": "Active Mobility Walking (5 km)",
        "category": "Travel",
        "input_desc": "5 km walking (zero tailpipe)",
        "function": calculate_travel_emissions,
        "kwargs": {"mode": "walking", "distance_km": 5.0},
        "expected_kg_co2e": 0.0000,
        "expected_source": "Zero tailpipe emissions",
        "formula": "5.0 km × 0.0000 kg CO₂e/km",
    },
    {
        "id": "TC-09",
        "name": "Bicycle Commute (25 km)",
        "category": "Travel",
        "input_desc": "25 km cycling",
        "function": calculate_travel_emissions,
        "kwargs": {"mode": "bicycle", "distance_km": 25.0},
        "expected_kg_co2e": 0.0000,
        "expected_source": "Zero tailpipe emissions",
        "formula": "25.0 km × 0.0000 kg CO₂e/km",
    },
    {
        "id": "TC-10",
        "name": "Recycled Plastic Credit (10 kg)",
        "category": "Waste",
        "input_desc": "10 kg plastic sent for recycling",
        "function": calculate_waste_emissions,
        "kwargs": {"waste_type": "recycled", "quantity_kg": 10.0},
        "expected_kg_co2e": 0.2100,
        "expected_source": "DEFRA 2023",
        "formula": "10.0 kg × 0.0210 kg CO₂e/kg",
    },
    {
        "id": "TC-11",
        "name": "Negative Bounds Guard",
        "category": "Safety / Validation",
        "input_desc": "-5 km bus journey (invalid)",
        "function": calculate_travel_emissions,
        "kwargs": {"mode": "bus", "distance_km": -5.0},
        "expected_kg_co2e": None,
        "expect_error": True,
        "expected_source": "Validation guard",
        "formula": "Negative distance rejected with error",
    },
    {
        "id": "TC-12",
        "name": "Compound Hackathon Query (Bus + AC)",
        "category": "Compound Activity",
        "input_desc": "12 km bus (1.2252) + 4 hours AC (4.2960)",
        "is_compound": True,
        "expected_kg_co2e": 5.5212,
        "expected_source": "DEFRA 2023 + BEE/CEA 2023",
        "formula": "1.2252 (bus) + 4.2960 (AC) = 5.5212 kg CO₂e",
    },
]


def run_golden_eval_suite() -> dict[str, Any]:
    """Execute all golden eval test vectors and return full validation results."""
    results = []
    passed = 0

    for tc in GOLDEN_TEST_CASES:
        if tc.get("is_compound"):
            r1 = calculate_travel_emissions("bus", 12.0)
            r2 = calculate_appliance_emissions("ac", 4.0)
            computed = round(r1["emissions_kg_co2e"] + r2["emissions_kg_co2e"], 4)
            diff = abs(computed - tc["expected_kg_co2e"])
            is_pass = diff < 1e-4
            if is_pass:
                passed += 1
            results.append({
                "id": tc["id"],
                "name": tc["name"],
                "category": tc["category"],
                "expected": f"{tc['expected_kg_co2e']:.4f} kg CO₂e",
                "computed": f"{computed:.4f} kg CO₂e",
                "delta": f"{diff:.6f}",
                "source": tc["expected_source"],
                "formula": tc["formula"],
                "passed": is_pass,
            })
            continue

        fn = tc["function"]
        kwargs = tc["kwargs"]
        res = fn(**kwargs)

        if tc.get("expect_error"):
            is_pass = "error" in res
            if is_pass:
                passed += 1
            results.append({
                "id": tc["id"],
                "name": tc["name"],
                "category": tc["category"],
                "expected": "Error trapped",
                "computed": "Error trapped" if is_pass else "No error",
                "delta": "0.000000",
                "source": tc["expected_source"],
                "formula": tc["formula"],
                "passed": is_pass,
            })
        else:
            computed = res.get("emissions_kg_co2e", -1.0)
            diff = abs(computed - tc["expected_kg_co2e"])
            src_ok = any(s.lower() in res.get("source", "").lower() for s in ("defra", "poore", "cea", "ipcc", "bee", "zero"))
            is_pass = diff < 1e-4 and src_ok
            if is_pass:
                passed += 1
            results.append({
                "id": tc["id"],
                "name": tc["name"],
                "category": tc["category"],
                "expected": f"{tc['expected_kg_co2e']:.4f} kg CO₂e",
                "computed": f"{computed:.4f} kg CO₂e",
                "delta": f"{diff:.6f}",
                "source": res.get("source", "N/A"),
                "formula": tc["formula"],
                "passed": is_pass,
            })

    total = len(GOLDEN_TEST_CASES)
    accuracy_pct = round((passed / total) * 100, 1)

    return {
        "total_cases": total,
        "passed_cases": passed,
        "failed_cases": total - passed,
        "accuracy_pct": accuracy_pct,
        "all_passed": passed == total,
        "details": results,
    }
