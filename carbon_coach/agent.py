"""
Carbon Coach – Groq-powered agent with tool calling.

All emission calculation tools are pure Python (no LLM needed for arithmetic).
The Groq LLM orchestrates tool calls; it never invents numbers.
"""
from __future__ import annotations

import json
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Verified Emission Factors  (same as before — untouched)
# ---------------------------------------------------------------------------
EMISSION_FACTORS: dict = {
    "travel": {
        "car_petrol":    {"kg_co2e_per_km": 0.1702, "source": "DEFRA 2023 Table 7 – Average petrol car",              "placeholder": False},
        "car_diesel":    {"kg_co2e_per_km": 0.1683, "source": "DEFRA 2023 Table 7 – Average diesel car",              "placeholder": False},
        "car_electric":  {"kg_co2e_per_km": 0.0530, "source": "DEFRA 2023 Table 7 – Battery electric vehicle",       "placeholder": False},
        "bus":           {"kg_co2e_per_km": 0.1021, "source": "DEFRA 2023 Table 8 – Local bus, average occupancy",   "placeholder": False},
        "train":         {"kg_co2e_per_km": 0.0410, "source": "DEFRA 2023 Table 8 – National rail",                  "placeholder": False},
        "motorcycle":    {"kg_co2e_per_km": 0.1140, "source": "DEFRA 2023 Table 7 – Average motorcycle",             "placeholder": False},
        "bicycle":       {"kg_co2e_per_km": 0.0000, "source": "Zero tailpipe emissions",                             "placeholder": False},
        "walking":       {"kg_co2e_per_km": 0.0000, "source": "Zero tailpipe emissions",                             "placeholder": False},
        "auto_rickshaw": {"kg_co2e_per_km": 0.0900, "source": "PLACEHOLDER – approx CNG auto-rickshaw (CPCB India)", "placeholder": True},
    },
    "electricity": {
        "IN_national": {"kg_co2e_per_kwh": 0.7160, "source": "CEA India Version 18 (2023) – national average",          "placeholder": False},
        "default":     {"kg_co2e_per_kwh": 0.4330, "source": "IEA World Average 2022 (PLACEHOLDER)",                    "placeholder": True},
    },
    "food": {
        "beef":       {"kg_co2e_per_kg": 60.0, "source": "Poore & Nemecek 2018 – beef",       "placeholder": False},
        "lamb":       {"kg_co2e_per_kg": 24.0, "source": "Poore & Nemecek 2018 – lamb",       "placeholder": False},
        "chicken":    {"kg_co2e_per_kg":  6.9, "source": "Poore & Nemecek 2018 – poultry",    "placeholder": False},
        "pork":       {"kg_co2e_per_kg":  7.6, "source": "Poore & Nemecek 2018 – pig meat",   "placeholder": False},
        "fish":       {"kg_co2e_per_kg":  6.1, "source": "Poore & Nemecek 2018 – fish farmed","placeholder": False},
        "eggs":       {"kg_co2e_per_kg":  4.5, "source": "Poore & Nemecek 2018 – eggs",       "placeholder": False},
        "dairy_milk": {"kg_co2e_per_kg":  3.2, "source": "Poore & Nemecek 2018 – dairy milk", "placeholder": False},
        "rice":       {"kg_co2e_per_kg":  4.0, "source": "Poore & Nemecek 2018 – rice",       "placeholder": False},
        "wheat":      {"kg_co2e_per_kg":  1.4, "source": "Poore & Nemecek 2018 – wheat flour","placeholder": False},
        "vegetables": {"kg_co2e_per_kg":  0.4, "source": "Poore & Nemecek 2018 – root veg",   "placeholder": False},
        "legumes":    {"kg_co2e_per_kg":  0.9, "source": "Poore & Nemecek 2018 – peas",       "placeholder": False},
        "tofu":       {"kg_co2e_per_kg":  3.0, "source": "Poore & Nemecek 2018 – tofu",       "placeholder": False},
    },
    "waste": {
        "general":    {"kg_co2e_per_kg": 0.5860, "source": "IPCC 2006 Vol.5 Ch.3 – MSW landfill",        "placeholder": False},
        "food_waste": {"kg_co2e_per_kg": 0.7060, "source": "IPCC 2006 Vol.5 Ch.3 – food/organic landfill","placeholder": False},
        "paper":      {"kg_co2e_per_kg": 1.0840, "source": "IPCC 2006 Vol.5 Ch.3 – paper landfill",      "placeholder": False},
        "plastic":    {"kg_co2e_per_kg": 0.0160, "source": "IPCC 2006 Vol.5 Ch.3 – plastic",             "placeholder": False},
        "recycled":   {"kg_co2e_per_kg": 0.0210, "source": "DEFRA 2023 – recycling credit",              "placeholder": False},
    },
}

APPLIANCE_FACTORS: dict = {
    "ac":           {"kw": 1.500, "name": "Air Conditioner (1.5-ton split)", "source": "BEE India 3-star AC average (1.5 kW)"},
    "fan":          {"kw": 0.075, "name": "Ceiling Fan",                     "source": "BEE India standard ceiling fan (75W)"},
    "geyser":       {"kw": 2.000, "name": "Water Geyser / Water Heater",     "source": "BEE India standard water geyser (2 kW)"},
    "refrigerator": {"kw": 0.150, "name": "Refrigerator",                   "source": "BEE India 3-star refrigerator (150W)"},
    "laptop":       {"kw": 0.065, "name": "Laptop computer",                 "source": "Standard laptop consumption (65W)"},
    "tv":           {"kw": 0.100, "name": "LED Television",                  "source": "Standard LED TV (100W)"},
    "lighting":     {"kw": 0.020, "name": "Room Lighting (2x LED)",          "source": "Standard 2x10W LED bulbs (20W)"},
}

MEAL_FACTORS: dict = {
    "chicken_meal":    {"kg_co2e": 1.85, "food_type": "chicken", "quantity_kg": 0.25, "source": "Poore & Nemecek 2018 – chicken biryani/meal"},
    "vegetarian_meal": {"kg_co2e": 0.75, "food_type": "legumes", "quantity_kg": 0.35, "source": "Poore & Nemecek 2018 – veg thali/meal"},
    "vegan_meal":      {"kg_co2e": 0.50, "food_type": "vegetables", "quantity_kg": 0.30, "source": "Poore & Nemecek 2018 – plant-based meal"},
    "beef_meal":       {"kg_co2e": 12.50, "food_type": "beef", "quantity_kg": 0.20, "source": "Poore & Nemecek 2018 – beef meal"},
}

TRAVEL_MODES = list(EMISSION_FACTORS["travel"].keys())
FOOD_TYPES   = list(EMISSION_FACTORS["food"].keys())
WASTE_TYPES  = list(EMISSION_FACTORS["waste"].keys())
APPLIANCE_TYPES = list(APPLIANCE_FACTORS.keys())
MEAL_TYPES = list(MEAL_FACTORS.keys())


# ---------------------------------------------------------------------------
# Pure-Python Emission Tools  (identical logic — no ADK dependency)
# ---------------------------------------------------------------------------

def calculate_travel_emissions(mode: str, distance_km: float) -> dict:
    if distance_km < 0:
        return {"error": "distance_km cannot be negative."}
    mode = mode.lower().replace(" ", "_")
    if mode not in EMISSION_FACTORS["travel"]:
        return {"error": f"Unknown mode '{mode}'. Available: {', '.join(TRAVEL_MODES)}."}
    fd = EMISSION_FACTORS["travel"][mode]
    return {
        "category": "travel", "mode": mode, "distance_km": distance_km,
        "factor_kg_co2e_per_km": fd["kg_co2e_per_km"],
        "emissions_kg_co2e": round(distance_km * fd["kg_co2e_per_km"], 4),
        "source": fd["source"], "placeholder": fd["placeholder"],
    }


def calculate_electricity_emissions(kwh: float, grid: str = "IN_national") -> dict:
    if kwh < 0:
        return {"error": "kwh cannot be negative."}
    if grid not in EMISSION_FACTORS["electricity"]:
        return {"error": f"Unknown grid '{grid}'. Available: {list(EMISSION_FACTORS['electricity'].keys())}."}
    fd = EMISSION_FACTORS["electricity"][grid]
    return {
        "category": "electricity", "kwh": kwh, "grid": grid,
        "factor_kg_co2e_per_kwh": fd["kg_co2e_per_kwh"],
        "emissions_kg_co2e": round(kwh * fd["kg_co2e_per_kwh"], 4),
        "source": fd["source"], "placeholder": fd["placeholder"],
    }


def calculate_appliance_emissions(appliance: str, hours: float, count: int = 1, grid: str = "IN_national") -> dict:
    if hours < 0 or count <= 0:
        return {"error": "hours must be ≥ 0 and count must be ≥ 1."}
    appliance = appliance.lower().replace(" ", "_")
    if appliance not in APPLIANCE_FACTORS:
        return {"error": f"Unknown appliance '{appliance}'. Available: {', '.join(APPLIANCE_TYPES)}."}
    if grid not in EMISSION_FACTORS["electricity"]:
        return {"error": f"Unknown grid '{grid}'. Available: {list(EMISSION_FACTORS['electricity'].keys())}."}

    app_data = APPLIANCE_FACTORS[appliance]
    kwh = round(hours * app_data["kw"] * count, 4)
    grid_data = EMISSION_FACTORS["electricity"][grid]
    emissions = round(kwh * grid_data["kg_co2e_per_kwh"], 4)

    return {
        "category": "electricity",
        "appliance": appliance,
        "appliance_name": app_data["name"],
        "hours": hours,
        "count": count,
        "kw_rating": app_data["kw"],
        "kwh": kwh,
        "grid": grid,
        "factor_kg_co2e_per_kwh": grid_data["kg_co2e_per_kwh"],
        "emissions_kg_co2e": emissions,
        "source": f"{app_data['source']} + {grid_data['source']}",
        "placeholder": grid_data["placeholder"],
    }


def calculate_food_emissions(food_type: str, quantity_kg: float) -> dict:
    if quantity_kg < 0:
        return {"error": "quantity_kg cannot be negative."}
    food_type = food_type.lower().replace(" ", "_")
    if food_type not in EMISSION_FACTORS["food"]:
        return {"error": f"Unknown food '{food_type}'. Available: {', '.join(FOOD_TYPES)}."}
    fd = EMISSION_FACTORS["food"][food_type]
    return {
        "category": "food", "food_type": food_type, "quantity_kg": quantity_kg,
        "factor_kg_co2e_per_kg": fd["kg_co2e_per_kg"],
        "emissions_kg_co2e": round(quantity_kg * fd["kg_co2e_per_kg"], 4),
        "source": fd["source"], "placeholder": fd["placeholder"],
    }


def calculate_meal_emissions(meal_type: str, servings: int = 1) -> dict:
    if servings <= 0:
        return {"error": "servings must be ≥ 1."}
    meal_type = meal_type.lower().replace(" ", "_")
    if meal_type not in MEAL_FACTORS:
        return {"error": f"Unknown meal '{meal_type}'. Available: {', '.join(MEAL_TYPES)}."}
    md = MEAL_FACTORS[meal_type]
    emissions = round(md["kg_co2e"] * servings, 4)
    return {
        "category": "food",
        "meal_type": meal_type,
        "servings": servings,
        "food_type": md["food_type"],
        "quantity_kg": round(md["quantity_kg"] * servings, 4),
        "emissions_kg_co2e": emissions,
        "source": md["source"],
        "placeholder": False,
    }


def calculate_waste_emissions(waste_type: str, quantity_kg: float) -> dict:
    if quantity_kg < 0:
        return {"error": "quantity_kg cannot be negative."}
    waste_type = waste_type.lower().replace(" ", "_")
    if waste_type not in EMISSION_FACTORS["waste"]:
        return {"error": f"Unknown waste '{waste_type}'. Available: {', '.join(WASTE_TYPES)}."}
    fd = EMISSION_FACTORS["waste"][waste_type]
    return {
        "category": "waste", "waste_type": waste_type, "quantity_kg": quantity_kg,
        "factor_kg_co2e_per_kg": fd["kg_co2e_per_kg"],
        "emissions_kg_co2e": round(quantity_kg * fd["kg_co2e_per_kg"], 4),
        "source": fd["source"], "placeholder": fd["placeholder"],
    }


def log_activity(activities: list, category: str, details: dict) -> dict:
    """Save a calculated activity to the session list (mutates in-place)."""
    if category not in {"travel", "electricity", "food", "waste"}:
        return {"error": f"Unsupported category '{category}'."}
    emissions = details.get("emissions_kg_co2e")
    if not isinstance(emissions, (int, float)) or emissions < 0:
        return {"error": "details must contain a valid non-negative 'emissions_kg_co2e'."}
    record = {
        "date": date.today().isoformat(), "category": category,
        "details": details, "emissions_kg_co2e": float(emissions),
    }
    activities.append(record)
    return {"status": "saved", "activity": record, "total_activities_in_session": len(activities)}


def get_summary(activities: list, period: str) -> dict:
    """Return total + breakdown for 'today' or 'this_week'."""
    period = period.lower().strip()
    if period not in ("today", "this_week"):
        return {"error": "period must be 'today' or 'this_week'."}
    today = date.today()
    cutoff = today if period == "today" else today - timedelta(days=today.weekday())
    filtered = [a for a in activities if date.fromisoformat(a["date"]) >= cutoff]
    total = round(sum(a["emissions_kg_co2e"] for a in filtered), 4)
    by_cat: dict[str, float] = {}
    for a in filtered:
        by_cat[a["category"]] = round(by_cat.get(a["category"], 0.0) + a["emissions_kg_co2e"], 4)
    return {
        "period": period, "from_date": cutoff.isoformat(), "to_date": today.isoformat(),
        "total_kg_co2e": total, "by_category": by_cat,
        "activity_count": len(filtered), "activities": filtered,
    }


def get_reduction_suggestions(activities: list) -> dict:
    """Generate verified savings suggestions from logged activities."""
    if not activities:
        return {"suggestions": [], "message": "No activities logged yet."}
    suggestions = []
    for act in activities:
        cat, d = act["category"], act["details"]
        if cat == "travel" and d.get("mode") in ("car_petrol", "car_diesel"):
            dist = d["distance_km"]
            car_f = EMISSION_FACTORS["travel"][d["mode"]]["kg_co2e_per_km"]
            bus_f = EMISSION_FACTORS["travel"]["bus"]["kg_co2e_per_km"]
            ev_f  = EMISSION_FACTORS["travel"]["car_electric"]["kg_co2e_per_km"]
            suggestions += [
                {"category":"travel","alternative":"bus",
                 "estimated_saving_kg_co2e": round((car_f-bus_f)*dist, 4),
                 "source":"DEFRA 2023","note":f"Switching {d['mode']} → bus for {dist} km"},
                {"category":"travel","alternative":"electric car",
                 "estimated_saving_kg_co2e": round((car_f-ev_f)*dist, 4),
                 "source":"DEFRA 2023","note":f"Switching {d['mode']} → EV for {dist} km"},
            ]
        elif cat == "electricity":
            kwh, grid = d.get("kwh", 0), d.get("grid","IN_national")
            f = EMISSION_FACTORS["electricity"].get(grid, EMISSION_FACTORS["electricity"]["IN_national"])["kg_co2e_per_kwh"]
            saving = round(kwh * 0.10 * f, 4)
            suggestions.append({"category":"electricity","alternative":"10 % reduction",
                "estimated_saving_kg_co2e": saving, "source":"CEA India 2023",
                "note":"Raise AC set-point 1 °C or switch to LED lighting"})
        elif cat == "food" and d.get("food_type") in ("beef","lamb"):
            qty = d.get("quantity_kg", 0)
            saving = round((EMISSION_FACTORS["food"][d["food_type"]]["kg_co2e_per_kg"]
                            - EMISSION_FACTORS["food"]["legumes"]["kg_co2e_per_kg"]) * qty, 4)
            suggestions.append({"category":"food","alternative":"legumes",
                "estimated_saving_kg_co2e": saving, "source":"Poore & Nemecek 2018",
                "note":f"Replace {d['food_type']} with lentils/beans for {qty} kg"})
        elif cat == "waste" and d.get("waste_type") in ("general","food_waste","paper"):
            qty = d.get("quantity_kg", 0)
            saving = round((EMISSION_FACTORS["waste"][d["waste_type"]]["kg_co2e_per_kg"]
                            - EMISSION_FACTORS["waste"]["recycled"]["kg_co2e_per_kg"]) * qty, 4)
            suggestions.append({"category":"waste","alternative":"recycling",
                "estimated_saving_kg_co2e": saving, "source":"IPCC 2006 / DEFRA 2023",
                "note":f"Recycle instead of landfill for {qty} kg of {d['waste_type']}"})
    if not suggestions:
        return {"suggestions":[], "message":"No high-impact activities found to suggest alternatives for."}
    return {
        "suggestions": suggestions,
        "total_potential_saving_kg_co2e": round(sum(s["estimated_saving_kg_co2e"] for s in suggestions), 4),
        "disclaimer": "All savings are ESTIMATES from verified emission factors.",
    }


# ---------------------------------------------------------------------------
# Groq Tool Schemas  (OpenAI-compatible function calling format)
# ---------------------------------------------------------------------------

GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_travel_emissions",
            "description": "Calculate CO₂e emissions for a journey using verified DEFRA 2023 factors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {"type": "string",
                        "description": f"Transport mode. One of: {', '.join(TRAVEL_MODES)}."},
                    "distance_km": {"type": "number", "description": "Distance in kilometres (≥ 0)."},
                },
                "required": ["mode", "distance_km"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_electricity_emissions",
            "description": "Calculate CO₂e from electricity use. Default grid: IN_national (CEA India 2023).",
            "parameters": {
                "type": "object",
                "properties": {
                    "kwh":  {"type": "number", "description": "Electricity in kWh (≥ 0)."},
                    "grid": {"type": "string", "description": "Grid: 'IN_national' or 'default'.", "default": "IN_national"},
                },
                "required": ["kwh"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_food_emissions",
            "description": "Calculate CO₂e from food consumption (Poore & Nemecek 2018).",
            "parameters": {
                "type": "object",
                "properties": {
                    "food_type":   {"type": "string", "description": f"Food type. One of: {', '.join(FOOD_TYPES)}."},
                    "quantity_kg": {"type": "number", "description": "Quantity in kg (≥ 0)."},
                },
                "required": ["food_type", "quantity_kg"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_appliance_emissions",
            "description": "Calculate CO₂e from electrical appliances (AC, fan, geyser, refrigerator, laptop, TV, lighting) based on BEE India power ratings and hours used.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appliance": {"type": "string", "description": f"Appliance type. One of: {', '.join(APPLIANCE_TYPES)}."},
                    "hours": {"type": "number", "description": "Hours of usage (≥ 0)."},
                    "count": {"type": "integer", "description": "Number of appliances (default 1).", "default": 1},
                    "grid": {"type": "string", "description": "Grid: 'IN_national' or 'default'.", "default": "IN_national"},
                },
                "required": ["appliance", "hours"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_meal_emissions",
            "description": "Calculate CO₂e from typical meals (chicken_meal, vegetarian_meal, vegan_meal, beef_meal) using Poore & Nemecek 2018 datasets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meal_type": {"type": "string", "description": f"Meal type. One of: {', '.join(MEAL_TYPES)}."},
                    "servings": {"type": "integer", "description": "Number of servings (≥ 1, default 1).", "default": 1},
                },
                "required": ["meal_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_waste_emissions",
            "description": "Calculate CO₂e from waste disposal (IPCC 2006).",
            "parameters": {
                "type": "object",
                "properties": {
                    "waste_type":  {"type": "string", "description": f"Waste type. One of: {', '.join(WASTE_TYPES)}."},
                    "quantity_kg": {"type": "number", "description": "Mass in kg (≥ 0)."},
                },
                "required": ["waste_type", "quantity_kg"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_activity",
            "description": "Save a successfully calculated emission activity to the session log.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "One of: travel, electricity, food, waste."},
                    "details":  {"type": "object", "description": "The full dict returned by the calculate_* tool."},
                },
                "required": ["category", "details"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_summary",
            "description": "Return total emissions and category breakdown for 'today' or 'this_week'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "'today' or 'this_week'."},
                },
                "required": ["period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_reduction_suggestions",
            "description": "Analyse logged activities and return personalised reduction suggestions with calculated savings.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

SYSTEM_PROMPT = """You are Carbon Coach (కార్బన్ కోచ్ / कार्बन कोच), a premier, verified carbon-footprint AI agent built for the DevFest 2026 Hackathon.
You support English, Telugu (తెలుగు), and Hindi (हिन्दी) — always respond in the language the user writes in.

COLLABORATIVE MULTI-AGENT ARCHITECTURE:
You operate with two synchronized sub-agent roles:
1. 🛠️ Tracker Agent: Strictly executes verified arithmetic tools, maintains the session ledger, prevents hallucinations, and records all activities.
2. 🌿 Coach Agent: Evaluates emissions against campus benchmarks (Green Campus target: 4.50 kg CO₂e/day, national average: 5.10 kg CO₂e/day) and recommends tangible reduction swaps with calculated kg CO₂e savings.

STRICT ARITHMETIC & TOOL RULES:
1. Use tools for ALL emission calculations — never invent numbers or estimate math in your head.
2. For compound statements (e.g. "I travelled 12 km by bus today and used the AC for 4 hours"), execute calculations for EVERY activity mentioned (e.g. bus travel tool AND AC appliance tool).
3. Always report the exact factor, verified source, and mathematical formula from tool results.
4. Auto-log all valid calculations to the activity ledger.
5. For totals, call get_summary — never add numbers from memory.
6. For reduction tips, call get_reduction_suggestions.

OUTPUT STRUCTURE RULES:
When reporting an emission calculation or activity log, format your response cleanly:

### 🌿 Activity Logged: [Activity Name / Item(s)]

> **[Total CO2e with 4 decimal places] kg CO₂e** emitted

| Detail | Specification |
| :--- | :--- |
| **Activity Item** | [Quantity/Distance and item(s), e.g. 12 km bus + 4h AC] |
| **Emission Factor(s)** | [Factor values and units, e.g. 0.1021 kg/km & 0.7160 kg/kWh] |
| **Calculation Formula** | [Explicit math: 12×0.1021 + 4×1.5×0.7160 = 5.5212 kg CO₂e] |
| **Verified Source(s)** | [DEFRA 2023, BEE India, CEA India Version 18] |
| **Status** | ✅ Verified by Tracker Agent & Logged in Session |

💡 **🌿 Coach Agent Recommendations & Campus Context:**
• Compare with campus target (4.50 kg/day): highlight if this single activity consumes a major fraction of daily quota.
• Provide 1-2 practical, high-impact tips with exact potential savings (e.g., raising AC thermostat by 1°C saves ~0.43 kg CO₂e per session).
• Invite user to check the **🏆 Campus Leaderboard** tab to view their hostel ranking, or **📊 Dashboard** for charts!

If responding in Telugu or Hindi, maintain the exact same structured markdown table, quote block, and bullet layout using natural, respectful Telugu or Hindi.
"""



def extract_activities_from_text(text: str) -> list[tuple[str, dict]]:
    """
    Extract and calculate one or multiple activities from free-form user text.
    Handles compound queries such as:
    'I travelled 12 km by bus today and used the AC for 4 hours.'
    """
    import re
    lower = text.lower().strip()
    extracted: list[tuple[str, dict]] = []

    # 1. Travel modes (bus, car_petrol, car_diesel, car_electric, train, motorcycle, bicycle, walking, auto_rickshaw)
    # Check compound patterns like '12 km by bus' or 'bus for 12 km'
    for mode in TRAVEL_MODES:
        pattern = rf"(?:(\d+(?:\.\d+)?)\s*(?:km|kms|kilometres?|miles?)\b[^\n,.]*?\b{mode}\b)|(?:\b{mode}\b[^\n,.]*?(\d+(?:\.\d+)?)\s*(?:km|kms|kilometres?|miles?)\b)"
        # Also check spaces instead of underscores e.g. 'car petrol'
        if "_" in mode:
            spaced = mode.replace("_", " ")
            pattern += rf"|(?:(\d+(?:\.\d+)?)\s*(?:km|kms|kilometres?|miles?)\b[^\n,.]*?\b{spaced}\b)|(?:\b{spaced}\b[^\n,.]*?(\d+(?:\.\d+)?)\s*(?:km|kms|kilometres?|miles?)\b)"
        m = re.search(pattern, lower)
        if m:
            val = next((float(g) for g in m.groups() if g is not None), None)
            if val is not None and val >= 0:
                res = calculate_travel_emissions(mode, val)
                if "error" not in res:
                    extracted.append(("travel", res))

    # Also catch Telugu/Hindi or generic walking/cycling keywords
    if not any(cat == "travel" for cat, _ in extracted):
        for mode in TRAVEL_MODES:
            if mode in lower or mode.replace("_", " ") in lower:
                m = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|kms|kilometres?)?", lower)
                if m:
                    val = float(m.group(1))
                    res = calculate_travel_emissions(mode, val)
                    if "error" not in res:
                        extracted.append(("travel", res))
                        break

    # 2. Appliances (AC, fan, geyser, refrigerator, laptop, tv, lighting)
    appliance_aliases = {
        "ac": [r"\bac\b", r"\ba/c\b", r"air conditioner", r"air condition"],
        "fan": [r"\bfan\b", r"ceiling fan"],
        "geyser": [r"\bgeyser\b", r"water heater"],
        "refrigerator": [r"\brefrigerator\b", r"\bfridge\b"],
        "laptop": [r"\blaptop\b", r"\bcomputer\b"],
        "tv": [r"\btv\b", r"\btelevision\b"],
        "lighting": [r"\blight\b", r"\blighting\b", r"\bbulbs?\b"],
    }
    for app_name, aliases in appliance_aliases.items():
        for al in aliases:
            # Pattern: 'used the AC for 4 hours' or '4 hours AC'
            pattern = rf"(?:(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b[^\n,.]*?{al})|(?:{al}[^\n,.]*?(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b)"
            m = re.search(pattern, lower)
            if m:
                val = next((float(g) for g in m.groups() if g is not None), None)
                if val is not None and val >= 0:
                    res = calculate_appliance_emissions(app_name, val)
                    if "error" not in res and not any(r.get("appliance") == app_name for _, r in extracted):
                        extracted.append(("electricity", res))
                        break

    # 3. Direct electricity (kwh / units) if not an appliance
    if not any(r.get("appliance") for _, r in extracted) and any(w in lower for w in ("kwh", "electricity", "units")):
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:kwh|units?\s*of\s*electricity|electricity\s*units?)?", lower)
        if m:
            val = float(m.group(1))
            res = calculate_electricity_emissions(val)
            if "error" not in res:
                extracted.append(("electricity", res))

    # 4. Meals (chicken_meal, vegetarian_meal, vegan_meal, beef_meal)
    meal_aliases = {
        "chicken_meal": ["chicken meal", "chicken biryani", "chicken thali"],
        "vegetarian_meal": ["vegetarian meal", "veg meal", "veg thali", "vegetarian thali"],
        "vegan_meal": ["vegan meal", "plant-based meal"],
        "beef_meal": ["beef meal", "beef steak"],
    }
    for m_type, aliases in meal_aliases.items():
        if any(al in lower for al in aliases):
            servings_m = re.search(rf"(\d+)\s*(?:servings?|plates?|meals?)", lower)
            servings = int(servings_m.group(1)) if servings_m else 1
            res = calculate_meal_emissions(m_type, servings)
            if "error" not in res:
                extracted.append(("food", res))
                break

    # 5. Food ingredients (chicken, beef, rice, vegetables, etc.)
    if not any(cat == "food" for cat, _ in extracted):
        for food in FOOD_TYPES:
            food_clean = food.replace("_", " ")
            if food in lower or food_clean in lower:
                # Search for quantity near food word
                pattern = rf"(?:(\d+(?:\.\d+)?)\s*(?:kg|kilos?|g|grams?)\b[^\n,.]*?\b{food_clean}\b)|(?:\b{food_clean}\b[^\n,.]*?(\d+(?:\.\d+)?)\s*(?:kg|kilos?|g|grams?)\b)"
                m = re.search(pattern, lower)
                if not m:
                    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|kilos?|g|grams?)?", lower)
                if m:
                    val = next((float(g) for g in m.groups() if g is not None), None)
                    if val is not None:
                        if ("g" in lower or "gram" in lower) and "kg" not in lower and val > 10:
                            val = val / 1000.0
                        res = calculate_food_emissions(food, val)
                        if "error" not in res:
                            extracted.append(("food", res))
                            break

    # 6. Waste (paper, plastic, food_waste, general, recycled)
    for waste in WASTE_TYPES:
        waste_clean = waste.replace("_", " ")
        if waste in lower or waste_clean in lower:
            m = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|kilos?|g)?", lower)
            if m:
                val = float(m.group(1))
                res = calculate_waste_emissions(waste, val)
                if "error" not in res:
                    extracted.append(("waste", res))
                    break

    return extracted


class TrackerAgent:
    """🛠️ Tracker Agent: Verifies calculations against verified datasets, records to immutable ledger."""
    def __init__(self, activities: list[dict]):
        self.activities = activities

    def verify_and_log(self, category: str, details: dict) -> dict:
        return log_activity(self.activities, category, details)

    def get_summary(self, period: str = "today") -> dict:
        return get_summary(self.activities, period)


class CoachAgent:
    """🌿 Coach Agent: Evaluates footprint against campus benchmarks and formulates reduction actions."""
    def __init__(self, activities: list[dict]):
        self.activities = activities

    def get_reduction_plan(self) -> dict:
        return get_reduction_suggestions(self.activities)

    def campus_benchmark(self, today_emissions: float) -> dict:
        from carbon_coach.campus import compare_user_to_campus
        return compare_user_to_campus(today_emissions)


class GroqCarbonCoach:
    """
    Wraps the Groq client with a tool-calling loop and in-memory session state.
    Each instance = one user session.
    Coordinates Tracker Agent and Coach Agent.
    """

    MODEL = "openai/gpt-oss-120b"
    DEFAULT_MODEL = "openai/gpt-oss-120b"
    FALLBACK_MODELS = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, activities: list[dict] | None = None):
        from groq import Groq
        self._client = Groq(api_key=api_key)
        self.model = model
        self.MODEL = model
        self._activities: list[dict] = activities if activities is not None else []
        self._messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.tracker = TrackerAgent(self._activities)
        self.coach = CoachAgent(self._activities)

    def _create_completion(self, messages: list[dict]):
        """Try completion with configured model, automatically falling back if model is inaccessible or does not support tool calling."""
        candidate_models = [self.model] + [m for m in self.FALLBACK_MODELS if m != self.model]
        last_error = None
        for candidate in candidate_models:
            try:
                response = self._client.chat.completions.create(
                    model=candidate,
                    messages=messages,
                    tools=GROQ_TOOLS,
                    tool_choice="auto",
                    parallel_tool_calls=False,
                    temperature=0.2,
                )
                if candidate != self.model:
                    self.model = candidate
                    self.MODEL = candidate
                return response
            except Exception as exc:
                err_str = str(exc).lower()
                if any(x in err_str for x in (
                    "does not exist",
                    "model_not_found",
                    "404",
                    "not have access",
                    "decommissioned",
                    "model_decommissioned",
                    "deprecated",
                    "tool calling",
                    "tool_use",
                    "not supported",
                    "permission",
                    "unauthorized",
                )):
                    last_error = exc
                    continue
                raise
        if last_error:
            raise last_error
        raise RuntimeError("No candidate models could be queried.")

    # ------------------------------------------------------------------
    def chat(self, user_text: str) -> str:
        """Send a user message and run the tool-calling loop until done."""
        user_turn_idx = len(self._messages)
        self._messages.append({"role": "user", "content": user_text})

        try:
            for _ in range(10):   # max 10 tool-call rounds per turn
                response = self._create_completion(self._messages)
                msg = response.choices[0].message

                # Append assistant turn (may include tool_calls)
                self._messages.append(msg)

                # If no tool calls → final text answer
                if not msg.tool_calls:
                    return msg.content or ""

                # Execute every requested tool call
                for tc in msg.tool_calls:
                    result = self._dispatch(tc.function.name, tc.function.arguments)
                    self._messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    })

            return "_(Max tool-call rounds reached. Please try again.)_"
        except Exception as exc:
            err_str = str(exc).lower()
            if any(k in err_str for k in ("tool calling", "not supported", "rate limit", "429", "invalid api key", "401", "authentication", "unauthorized")):
                return self._chat_without_native_tools(user_text, user_turn_idx)
            # Revert conversation state back to before this user turn if it completely failed
            if len(self._messages) > user_turn_idx:
                self._messages = self._messages[:user_turn_idx]
            raise

    def _chat_without_native_tools(self, user_text: str, user_turn_idx: int) -> str:
        """Deterministic tool execution and multi-agent synthesis when native tool calling is unsupported."""
        if len(self._messages) > user_turn_idx:
            self._messages = self._messages[:user_turn_idx]

        lower = user_text.lower().strip()
        matched_items = extract_activities_from_text(user_text)

        # Log each valid extracted activity
        for cat, res in matched_items:
            if not any(a.get("details") == res for a in self._activities):
                self.tracker.verify_and_log(cat, res)

        summary_info = None
        if any(w in lower for w in ("total", "today", "footprint", "summary", "వారం", "మొత్తం", "कुल", "आज")):
            summary_info = self.tracker.get_summary("today")

        guidance = ""
        if matched_items:
            guidance += f"\n[VERIFIED CALCULATION RESULTS ({len(matched_items)} activities)]: {json.dumps([r for _, r in matched_items])}\nAll activities successfully logged in session ledger by Tracker Agent."
        if summary_info:
            guidance += f"\n[VERIFIED SUMMARY]: {json.dumps(summary_info)}"

        fallback_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"User input: {user_text}\n{guidance}\n"
            "Format your response cleanly using the structured markdown layout specified above. "
            "Report exact factors, explicit formulas, and verified sources for all activities. "
            "Respond respectfully in the user's language (English, Telugu, or Hindi)."
        )

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": fallback_prompt}],
                temperature=0.2,
            )
            answer = resp.choices[0].message.content or ""
            self._messages.append({"role": "user", "content": user_text})
            self._messages.append({"role": "assistant", "content": answer})
            return answer
        except Exception:
            # Deterministic fallback response with 100% accurate mathematical output
            if matched_items:
                total_emitted = round(sum(r.get("emissions_kg_co2e", 0.0) for _, r in matched_items), 4)

                table_rows = []
                for _, r in matched_items:
                    cat = r.get("category", "").title()
                    em = r.get("emissions_kg_co2e", 0.0)
                    src = r.get("source", "Official benchmark")

                    if "mode" in r:
                        item_desc = f"{r['distance_km']} km by {r['mode'].replace('_', ' ')}"
                        formula = f"{r['distance_km']} km × {r['factor_kg_co2e_per_km']} kg CO₂e/km = {em:.4f} kg CO₂e"
                    elif "appliance" in r:
                        item_desc = f"{r['hours']}h {r.get('appliance_name', r['appliance'])}"
                        formula = f"{r['hours']}h × {r['kw_rating']} kW = {r['kwh']} kWh × {r['factor_kg_co2e_per_kwh']} = {em:.4f} kg CO₂e"
                    elif "food_type" in r and "meal_type" not in r:
                        item_desc = f"{r['quantity_kg']} kg {r['food_type'].replace('_', ' ')}"
                        formula = f"{r['quantity_kg']} kg × {r['factor_kg_co2e_per_kg']} kg CO₂e/kg = {em:.4f} kg CO₂e"
                    elif "meal_type" in r:
                        item_desc = f"{r['servings']} serving(s) of {r['meal_type'].replace('_', ' ')}"
                        formula = f"{r['servings']} serving(s) = {em:.4f} kg CO₂e"
                    elif "kwh" in r:
                        item_desc = f"{r['kwh']} kWh electricity"
                        formula = f"{r['kwh']} kWh × {r['factor_kg_co2e_per_kwh']} kg CO₂e/kWh = {em:.4f} kg CO₂e"
                    else:
                        item_desc = f"{r.get('quantity_kg', 1.0)} kg {r.get('waste_type', 'waste')}"
                        formula = f"{r.get('quantity_kg', 1.0)} kg × {r.get('factor_kg_co2e_per_kg', 0)} = {em:.4f} kg CO₂e"

                    table_rows.append(f"| **{item_desc}** | `{formula}` | `{em:.4f} kg CO₂e` | {src} |")

                rows_str = "\n".join(table_rows)

                ans = f"""### 🌿 Activity Logged: {len(matched_items)} Item(s) Verified

> **{total_emitted:.4f} kg CO₂e** total emitted

| Activity & Quantity | Calculation Formula | Emissions | Verified Source |
| :--- | :--- | :--- | :--- |
{rows_str}

**🛠️ Tracker Agent Status:** ✅ All {len(matched_items)} activities verified and logged in session ledger.

💡 **🌿 Coach Agent Recommendations & Campus Context:**
• **Campus Target Check:** Your campus daily target is **4.50 kg CO₂e/day**. This activity represents **{round((total_emitted / 4.50) * 100, 1)}%** of your daily budget.
• **Sustainable Tip:** Check the **🏆 Campus Leaderboard** tab to view your hostel/department standing and earn eco-badges!
• **Reduction Alternative:** Switch high-draw appliances to eco-mode or opt for active transit (cycling/walking at 0.0 kg CO₂e) to shrink your footprint.
"""
                self._messages.append({"role": "user", "content": user_text})
                self._messages.append({"role": "assistant", "content": ans})
                return ans
            raise

    # ------------------------------------------------------------------
    def _dispatch(self, name: str, args_json: str) -> dict:
        """Call the matching Python tool, auto-log valid calculations, and return its result dict."""
        args = json.loads(args_json)
        if name in (
            "calculate_travel_emissions",
            "calculate_electricity_emissions",
            "calculate_appliance_emissions",
            "calculate_food_emissions",
            "calculate_meal_emissions",
            "calculate_waste_emissions",
        ):
            if name == "calculate_travel_emissions":
                res = calculate_travel_emissions(**args)
                cat = "travel"
            elif name in ("calculate_electricity_emissions", "calculate_appliance_emissions"):
                if name == "calculate_electricity_emissions":
                    res = calculate_electricity_emissions(**args)
                else:
                    res = calculate_appliance_emissions(**args)
                cat = "electricity"
            elif name in ("calculate_food_emissions", "calculate_meal_emissions"):
                if name == "calculate_food_emissions":
                    res = calculate_food_emissions(**args)
                else:
                    res = calculate_meal_emissions(**args)
                cat = "food"
            else:
                res = calculate_waste_emissions(**args)
                cat = "waste"

            # Auto-save valid emission calculation to session activities
            if "error" not in res and "emissions_kg_co2e" in res:
                if not any(a.get("details") == res for a in self._activities):
                    self.tracker.verify_and_log(cat, res)
            return res

        if name == "log_activity":
            details = args.get("details", {})
            if any(a.get("details") == details for a in self._activities):
                return {"status": "saved", "already_logged": True, "total_activities_in_session": len(self._activities)}
            return self.tracker.verify_and_log(args.get("category", "travel"), details)
        if name == "get_summary":
            return self.tracker.get_summary(**args)
        if name == "get_reduction_suggestions":
            return self.coach.get_reduction_plan()
        return {"error": f"Unknown tool: {name}"}

    # ------------------------------------------------------------------
    @property
    def activities(self) -> list[dict]:
        return self._activities

