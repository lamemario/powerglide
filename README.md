# ⚡ PowerGlide

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Science: Peer-Reviewed](https://img.shields.io/badge/Science-Validated-green.svg)](#scientific-foundation)
[![Tests: Passing](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](#automated-testing)

> **Local-first hybrid CLI/GUI performance tracker for Sprint Paddlers.**

PowerGlide is a specialised tool designed for varsity-level canoeing athletes. It bridges the gap between messy mobile notes and high-level sports science analytics, providing injury prevention modeling (ACWR) and strength-to-speed correlation tracking without ever leaving your local machine. *To be honest, I built this for myself after tearing my hamstring. 2 Grade 2 tears, mate. I wasn't even aware that I was that fatigued. So that got me thinking about having some research-backed metrics to keep track of training load so that I could prevent myself from over-training and getting injured. This is truly a tracker made for myself, haha.*

---

## 🚀 Highlights

- **⌨️ Keyboard-Centric:** A sophisticated interactive shell (REPL) with context-aware prompts.
- **📝 Smart Parser:** Import workouts directly from formatted notes using regex-based shorthand.
- **🔬 Scientific Core:** Validated 1RM estimations and injury risk monitoring (ACWR via EWMA).
- **📊 Local Analytics:** Real-time terminal stats (`powerglide stats`) and an interactive Streamlit dashboard.
- **🛶 C1 Specific:** Biomechanically mapped to C1 paddling (Top Arm Push, Bottom Arm Pull, Trunk Rotation).

---

## 📦 Quick Start

### 1. Installation
```bash
# Clone the repository
cd "Gym Tracking App"

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows

# Install in editable mode
pip install -e .
```

### 2. Initialise
```bash
# Seed the exercise database (800+ exercises + C1 enrichment)
powerglide seed
```

### 3. Run
```bash
# Enter the interactive PowerGlide shell
powerglide
```

---

## 📝 The "Secret Sauce": Shorthand Parser

PowerGlide is designed for the real-world workflow: **Log on your phone, Paste at home.**

**Format Example:**
```text
21/02/26 60min @7

Barbell Bench Press [feet up]
60 x 8, 50 x 8,8,8 @8

Lat Pulldown [wide grip]
63x8, 58.9x8, 58.9x8, 58.9x8

Dead Bug
0 x 10,10,10

Plank
3x60s
```

**How to Import:**
1. Run `powerglide`
2. Type `import`
3. Paste your notes and type `END`
4. **Done.** Fuzzy matching automatically resolves "Bench" to "Barbell Bench Press - Medium Grip".

---

## 🏛️ Scientific Foundation

PowerGlide's math is not generic; it is built on primary source literature found in the `Research Papers/` directory.

---

## 🔍 The "Transparency Layer": Explain Command

PowerGlide includes a dedicated `explain` command group to provide a step-by-step breakdown of the math and sports science behind your data.

- **`explain 1rm`**: See the specific formula (Brzycki vs Epley) and math used for a set.
- **`explain acwr`**: Breakdown the $\lambda$ decay constants and see how your current ratio maps to the literature.
- **`explain fatigue`**: List every set that contributed to a muscle's 72h fatigue score, including the weighted coefficients.
- **`explain workout`**: See the internal vs external load calculations for a specific session.

*Try typing `explain acwr` inside the PowerGlide shell for a live demonstration.*

---

### 1. Injury Prevention (ACWR)
Uses **Exponentially Weighted Moving Averages (EWMA)** to calculate the Acute:Chronic Workload Ratio. This tracks your *External Load* and tissue strain.
- **Formula:** $\lambda = 2 / (N + 1)$
- **Optimal Zone:** 0.8 – 1.3 ( Qin et al. 2025 )
- **Danger Zone:** > 1.5 (High risk of non-contact injury)

### 2. Time-Based Core/TUT vs 1RM Engine
To keep your maximum strength metrics medically pure, time-based exercises (like Planks logged as `60s`) calculate their volume via sRPE, completely bypassing the Brzycki/Epley 1RM estimator to prevent false regressions.
- **1–10 Reps:** Brzycki Formula — $Weight \times \frac{36}{37 - Reps}$
- **>10 Reps:** Epley Formula — $Weight \times (1 + \frac{Reps}{30})$

### 3. ACWR vs 72-Hour Fatigue vs Biological Recovery
PowerGlide measures *External Load* (the physical work done).
- **ACWR:** Tracks tissue tolerance and injury vulnerability.
- **72-Hour Fatigue Map:** Tracks the raw volume distribution across specific muscle groups over 3 days.

**CRITICAL CAVEAT:** The 72-Hour Fatigue Map is *not* a biological recovery metric. Just because the graph says a muscle group has low volume does not mean your Central Nervous System (CNS) is recovered. **Always listen to your body.** Your internal readiness to train is subjective, and should be gauged via Session RPE, Heart Rate Variability (HRV), and personal feeling. PowerGlide's external metrics are a *supplement* to your internal biological compass, never a replacement.

---

## 🛠️ Command Reference

| Command | Sub-Context | Purpose |
| :--- | :--- | :--- |
| `stats` | Root | Instant view of ACWR, 72h Fatigue, and C1 Correlations. |
| `explain` | Root | Mathematical transparency (1RM, ACWR, Fatigue, Workout). |
| `import` | Root | Paste mode for bulk workout entry. |
| `dashboard` | Root | Launch the Plotly/Streamlit visual analytics. |
| `log` | `gym`/`water` | Quick entry for a single exercise or piece. |
| `history` | `gym`/`water` | View recent sessions with calculated e1RM/Splits. |
| `constraint` | `manage` | Track injuries (e.g., "hamstring tear") to contextualise stats. |
| `export` | `manage` | Export history to CSV or JSON for external analysis. |

---

## 📂 Architecture

```text
powerglide/
├── core/             # Mathematical engines and parsers
├── database/         # SQLite models, migrations, and seeder
├── cli/              # Typer commands and interactive shell
├── dashboard/        # Streamlit UI and Plotly charts
└── tests/            # Automated Pytest suite
```

### Automated Testing
PowerGlide maintains a strict testing protocol. Run tests with:
```bash
pytest tests/
```

---

## ⚙️ Configuration

Tune the system to your training style in `powerglide.toml`:
```toml
[acwr]
acute_window = 7
chronic_window = 28
optimal_max = 1.3
caution_max = 1.5
```

---

## 📚 References
- **Qin et al. (2025):** "Acute to chronic workload ratio (ACWR) for predicting sports injury risk."
- **LeSuer et al. (1997):** "The Accuracy of Prediction Equations for Estimating 1-RM Performance."
- **Crisafulli et al. (2025):** "Power–Load Relationship of Bench Press and Prone Bench Pull in International Medal-Winning Canoeists."
