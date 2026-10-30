# 🌱 DevFest 2026 Hackathon: Carbon Coach

> **Build an AI agent that helps people measure, understand, and reduce their carbon footprint.**  
> Powered by the **Free Groq API**, Multi-Agent Architecture (**Tracker + Coach**), Pure-Python Arithmetic ($A \times F = E$), and **Zero Made-Up Numbers**.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red.svg)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-Free%20Tier-orange.svg)](https://groq.com)
[![Golden Eval](https://img.shields.io/badge/Golden%20Eval-100%25%20Pass%20(12%2F12)-brightgreen.svg)](#-golden-eval-suite)
[![Languages](https://img.shields.io/badge/Languages-EN%20%7C%20%E0%B0%A4%E0%B1%86%E0%B0%B2%E0%B1%81%E0%B0%97%E0%B1%81%20%7C%20%E0%A4%B9%E0%A4%BF%E0%A4%A8%E0%A5%8D%E0%A4%A6%E0%A5%80-purple.svg)](#-trilingual-support)

---

## 🎯 Hackathon Problem Statement & Compliance Matrix

| Must-Have / Bonus Requirement | Carbon Coach Implementation | Status |
|---|---|---|
| **1. Conversational input** | Natural multi-sentence conversations in English, Telugu, and Hindi | ✅ Full |
| **2. Tool-based calculations** | Pure Python emission tools converting activities into exact kg CO₂e using verified factors | ✅ Full |
| **3. Session memory & trends** | Full session activity ledger, daily/session KPI cards, timeline charts, and category breakdowns | ✅ Full |
| **4. Actionable tips with savings** | Personalized reduction suggestions with exact calculated kg CO₂e savings (e.g. car $\to$ bus, AC $+1^\circ$C) | ✅ Full |
| **5. Zero made-up numbers** | Strict arithmetic formulas ($A \times F = E$) tied directly to DEFRA, CEA India, BEE, Poore & Nemecek, and IPCC | ✅ Full |
| **🚀 Bonus: Multi-Agent** | **🛠️ Tracker Agent** (ledger & tool arithmetic) + **🌿 Coach Agent** (strategic advice & campus target) | ✅ Full |
| **🚀 Bonus: Campus Mode** | Live leaderboard for Hostels (Godavari, Krishna, Kaveri, Ganga, Narmada) and Departments (CSE, ECE, ME, etc.) | ✅ Full |
| **🚀 Bonus: Golden Eval Suite** | 12 automated benchmark test cases achieving 100% mathematical precision with $\Delta < 10^{-4}$ | ✅ Full |
| **🚀 Bonus: Telugu / Hindi** | Trilingual support with native script responses, quick prompts, and structured markdown tables | ✅ Full |
| **🚀 Bonus: Cloud Run Ready** | Production-ready `Dockerfile` and automated 1-click `deploy.sh` script | ✅ Full |

---

## 🧮 Verified Emission Factors (No Hallucinations)

| Category | Item / Mode | Factor | Verified Dataset Citation |
|---|---|---|---|
| **Travel** | Local Bus | `0.1021 kg CO₂e / passenger-km` | DEFRA 2023 Table 8 – Local bus, average occupancy |
| **Travel** | Petrol Car | `0.1702 kg CO₂e / km` | DEFRA 2023 Table 7 – Average petrol car |
| **Travel** | Electric Train | `0.0410 kg CO₂e / passenger-km` | DEFRA 2023 Table 8 – National rail |
| **Travel** | Bicycle / Walking | `0.0000 kg CO₂e / km` | Zero tailpipe mobility emissions |
| **Electricity** | Indian National Grid | `0.7160 kg CO₂e / kWh` | CEA India Version 18 (2023) National Average |
| **Appliances** | Air Conditioner (1.5 kW split) | `1.5 kW × hours × 0.7160` | BEE India 3-star AC average + CEA India 2023 |
| **Appliances** | Ceiling Fan (75W) | `0.075 kW × hours × 0.7160` | BEE India ceiling fan standard + CEA India 2023 |
| **Food** | Poultry (Chicken) | `6.9000 kg CO₂e / kg` | Poore & Nemecek 2018 (poultry dataset) |
| **Food** | Beef | `60.0000 kg CO₂e / kg` | Poore & Nemecek 2018 (beef dataset) |
| **Food** | Legumes / Lentils | `0.9000 kg CO₂e / kg` | Poore & Nemecek 2018 (peas/lentils dataset) |
| **Waste** | Paper Landfill | `1.0840 kg CO₂e / kg` | IPCC 2006 Vol. 5 Ch. 3 – Paper landfill |
| **Waste** | Recycled Plastic | `0.0210 kg CO₂e / kg` | DEFRA 2023 – Recycling credit |

---

## ⚡ The Benchmark Compound Activity Query

The hackathon challenge test sentence:
> *"I travelled 12 km by bus today and used the AC for 4 hours."*

### Mathematical Execution by Tracker Agent:
1. **Bus Travel:** $12.0\text{ km} \times 0.1021\text{ kg CO}_2\text{e/km} = \mathbf{1.2252}\text{ kg CO}_2\text{e}$ *(DEFRA 2023)*
2. **AC Appliance:** $4.0\text{ h} \times 1.5\text{ kW} = 6.0\text{ kWh} \times 0.7160\text{ kg CO}_2\text{e/kWh} = \mathbf{4.2960}\text{ kg CO}_2\text{e}$ *(BEE/CEA India 2023)*
3. **Combined Emitted:** $1.2252 + 4.2960 = \mathbf{5.5212}\text{ kg CO}_2\text{e}$
4. **Coach Agent Campus Comparison:** Daily green target is $4.50\text{ kg CO}_2\text{e/day}$. This activity consumes $122.7\%$ of the daily student quota.

---

## 🚀 Quick Start (Local Setup)

```bash
# 1. Clone repository
git clone https://github.com/your-username/carbon-coach.git
cd carbon-coach

# 2. Virtual environment setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Run automated tests (56 passed)
pytest tests/ -v

# 4. Launch Streamlit UI
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 🧪 Golden Eval Suite

To run the automated 12-case verification suite directly from terminal:
```bash
python -c 'from carbon_coach.golden_eval import run_golden_eval_suite; import json; print(json.dumps(run_golden_eval_suite(), indent=2))'
```
Or open the **🧪 Golden Eval** tab inside the Streamlit web application.

---

## 🌐 Deploy to Google Cloud Run

To deploy Carbon Coach on Google Cloud Run with a live public URL:
```bash
export GCP_PROJECT_ID="your-project-id"
export GROQ_API_KEY="gsk_..."
./deploy.sh
```

---

## 👥 Judging Highlights

- **100% Accuracy:** Pure Python tools guarantee that arithmetic is immune to LLM hallucination.
- **Zero API Cost:** Runs completely on Groq's fast, free open models tier (`openai/gpt-oss-120b`, `20b`, `qwen/qwen3.8-27b`).
- **Interactive UX:** Live dynamic charts, trilingual quick prompts, prompt pre-population, and instant hostel score updates.
# carbonemission
