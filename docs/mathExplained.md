# PowerGlide: Mathematical and Scientific Foundations

This document transparently details the reasoning behind the metrics tracked by PowerGlide. It explains the scientific rationale, the specific variables chosen, and the mathematical formulas powering the engine.

## The "Explain it Like I'm Five" Summary
When you exercise, your body experiences two things:
1. **External Load:** This is how much raw work you did (e.g., lifting 10kg 5 times, or paddling for 30 minutes). PowerGlide uses **sRPE (Session RPE × Duration)** to measure this for water and non-gym workouts, and **Volume Load (Weight × Reps)** for gym workouts.
2. **Injury Risk (ACWR):** We take your recent training load (the last 7 days) and compare it to your historical base (the last 28 days). If the ratio spikes too high too quickly, your risk of injury goes up. We calculate this automatically.

**Important Note on Biological Recovery:** Looking at a chart of your training volume (External Load) does *not* tell you how your brain and muscles actually feel (Internal Biological state). Just because a graph says you should be recovered doesn't mean your body agrees. **Always listen to your body.**

---

## 🔬 Scientific Deep Dive

### 1. Internal Load Quantification: Session-RPE (sRPE)
For activities where traditional tracking (Weight × Reps) is impossible or scientifically invalid—such as kayak sprint pieces, or isometric core training (Time Under Tension)—PowerGlide utilizes the Session-RPE (sRPE) method. 

**The Formula:**
`Session Load = Session RPE (1-10) × Duration (minutes)`

**Scientific Rationale:**
Foster et al. (2001) demonstrated that sRPE is a highly valid methodology for quantifying internal training load across various steady-state and non-steady-state endurance exercises. By decoupling the metric from arbitrary rep-equivalencies and focusing on subjective exertion multiplied by duration, we achieve a universal "currency" for physiological strain. This ensures isometric core exercises (like 60-second planks) contribute accurately to aggregate fatigue without polluting the 1RM curve.

*Citation:*
> Foster, C., Florhaug, J. A., Franklin, J., Gottschall, L., Hrovatin, L. A., Parker, S., Doleshal, P., & Dodge, C. (2001). A new approach to monitoring exercise training. *Journal of Strength and Conditioning Research*, *15*(1), 109–115.

### 2. Injury Prevention Engine: Acute:Chronic Workload Ratio (ACWR) via EWMA
To predict and mitigate injury risk, PowerGlide calculates the Acute:Chronic Workload Ratio (ACWR). Instead of standard rolling averages, we implement Exponentially Weighted Moving Averages (EWMA) to place greater mathematical decay on older training sessions, better mirroring the biological realities of tissue adaptation and fatigue dissipation.

**The Formula:**
`EWMAtoday = Loadtoday × λa + EWMAyesterday × (1 − λa)`
Where `λ` (the decay factor) is `2 / (N + 1)`, and `N` is the time constant (7 days for Acute, 28 days for Chronic).
`ACWR = Acute EWMA / Chronic EWMA`

**Scientific Rationale:**
Williams et al. (2017) highlighted that calculating ACWR using EWMA is significantly more sensitive to recent spikes in training load compared to rolling averages. EWMA accurately reflects the non-linear decaying nature of fitness and fatigue, providing a tighter correlation to acute injury risk.

*Citation:*
> Williams, S., West, S., Cross, M. J., & Stokes, K. A. (2017). Better way to determine the acute:chronic workload ratio?. *British Journal of Sports Medicine*, *51*(3), 209-210.

### 3. Maximum Strength Estimation (1RM Curve)
For dynamic gym lifts logged with strict Rep ranges, PowerGlide estimates the athlete's 1-Repetition Maximum (1RM) dynamically using standardized sports science algorithms.

**The Formulas:**
- For ≤ 10 Reps: **Brzycki Formula**
  `1RM = Weight × (36 / (37 - Reps))`
- For > 10 Reps: **Epley Formula**
  `1RM = Weight × (1 + (Reps / 30))`

**System Failsafe:** For time-based isometric sets (where `reps = 0` and `time_seconds > 0`), the 1RM calculator forces a `NULL` output. This rigorously protects the athlete's maximum strength engine from being tainted by incompatible modalities like core planks.
