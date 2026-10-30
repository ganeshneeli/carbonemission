"""
Campus Leaderboard & Benchmarking Module for DevFest 2026 Hackathon: Carbon Coach.

Enables students and faculty to compare hostels and departments, track per-capita daily emissions,
and earn eco-badges to drive campus-wide sustainability.
"""
from __future__ import annotations

CAMPUS_BENCHMARKS = {
    "india_per_capita_daily_kg": 5.10,      # CEA / MoEFCC India average per person (~1.9 tons/year = 5.1 kg/day)
    "campus_student_daily_target_kg": 4.50, # DevFest 2026 Green Campus Goal
    "campus_average_daily_kg": 5.35,        # Current estimated campus average
}

HOSTEL_BASELINES: dict[str, dict] = {
    "Godavari Hostel": {"students": 240, "base_daily_kg": 1128.0, "icon": "🌊"},
    "Krishna Hostel":  {"students": 280, "base_daily_kg": 1394.4, "icon": "🍃"},
    "Kaveri Hostel":   {"students": 210, "base_daily_kg": 966.0,  "icon": "🌸"},
    "Ganga Hostel":    {"students": 320, "base_daily_kg": 1824.0, "icon": "⚡"},
    "Narmada Hostel":  {"students": 260, "base_daily_kg": 1326.0, "icon": "🌿"},
}

DEPARTMENT_BASELINES: dict[str, dict] = {
    "Computer Science & Engg (CSE)":     {"members": 450, "base_daily_kg": 2115.0, "icon": "💻"},
    "Electronics & Comm (ECE)":           {"members": 380, "base_daily_kg": 1938.0, "icon": "📡"},
    "Mechanical Engineering (ME)":        {"members": 340, "base_daily_kg": 1972.0, "icon": "⚙️"},
    "Civil Engineering (CE)":             {"members": 290, "base_daily_kg": 1421.0, "icon": "🏗️"},
    "Electrical & Electronics (EEE)":     {"members": 310, "base_daily_kg": 1581.0, "icon": "⚡"},
}

ECO_BADGES = [
    ("🥇 Eco-Champion",   "#10b981", 4.60),  # < 4.60 kg/student
    ("🥈 Green Pioneer",  "#06b6d4", 5.00),  # < 5.00 kg/student
    ("🥉 Conscious Unit", "#f59e0b", 5.50),  # < 5.50 kg/student
    ("⚠️ High Carbon",    "#ef4444", 999.0), # >= 5.50 kg/student
]


def _assign_badge(per_capita: float) -> tuple[str, str]:
    for name, color, threshold in ECO_BADGES:
        if per_capita <= threshold:
            return name, color
    return "⚠️ High Carbon", "#ef4444"


def get_campus_leaderboard(
    entity_type: str = "hostel",
    selected_entity: str | None = None,
    user_session_emissions: float = 0.0,
) -> dict:
    """
    Generate ranked leaderboard for hostels or departments.
    Incorporates the user's logged emissions into their selected entity.
    """
    is_hostel = entity_type.lower() == "hostel"
    baselines = HOSTEL_BASELINES if is_hostel else DEPARTMENT_BASELINES
    count_key = "students" if is_hostel else "members"

    entries = []
    for name, data in baselines.items():
        total_kg = data["base_daily_kg"]
        if selected_entity and name.lower() == selected_entity.lower():
            total_kg += user_session_emissions

        members = data[count_key]
        per_capita = round(total_kg / members, 3)
        badge_name, badge_color = _assign_badge(per_capita)

        # Difference against campus target
        target_diff_pct = round(((per_capita - CAMPUS_BENCHMARKS["campus_student_daily_target_kg"]) / CAMPUS_BENCHMARKS["campus_student_daily_target_kg"]) * 100, 1)

        entries.append({
            "name": name,
            "icon": data["icon"],
            "members": members,
            "total_emissions_kg": round(total_kg, 2),
            "per_capita_daily_kg": per_capita,
            "badge": badge_name,
            "badge_color": badge_color,
            "target_diff_pct": target_diff_pct,
            "is_user_entity": bool(selected_entity and name.lower() == selected_entity.lower()),
        })

    # Sort ascending by per_capita_daily_kg (lowest emission is top rank 1)
    entries.sort(key=lambda x: x["per_capita_daily_kg"])
    for rank, entry in enumerate(entries, 1):
        entry["rank"] = rank

    user_entry = next((e for e in entries if e["is_user_entity"]), None)
    return {
        "entity_type": entity_type,
        "selected_entity": selected_entity,
        "campus_average_per_capita": CAMPUS_BENCHMARKS["campus_average_daily_kg"],
        "target_per_capita": CAMPUS_BENCHMARKS["campus_student_daily_target_kg"],
        "user_entry": user_entry,
        "rankings": entries,
    }


def compare_user_to_campus(user_daily_emissions: float) -> dict:
    """Compare a single user's daily emission total against national and campus averages."""
    campus_avg = CAMPUS_BENCHMARKS["campus_average_daily_kg"]
    target = CAMPUS_BENCHMARKS["campus_student_daily_target_kg"]
    india_avg = CAMPUS_BENCHMARKS["india_per_capita_daily_kg"]

    diff_campus_pct = round(((user_daily_emissions - campus_avg) / campus_avg) * 100, 1) if campus_avg else 0.0
    status = "lower" if user_daily_emissions <= campus_avg else "higher"

    return {
        "user_daily_kg": round(user_daily_emissions, 4),
        "campus_avg_kg": campus_avg,
        "india_avg_kg": india_avg,
        "target_kg": target,
        "diff_campus_pct": abs(diff_campus_pct),
        "status": status,
        "meets_target": user_daily_emissions <= target,
    }
