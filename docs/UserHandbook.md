# PowerGlide: The Comprehensive User Handbook

Welcome to PowerGlide! If you are new to sports science or just want to know exactly how to use this tool to navigate your training and prevent injuries, this handbook is for you.

PowerGlide is a "local-first" command-line application. This means you interact with it by typing commands into your terminal, and all your data stays private on your computer.

This guide will walk you through exactly **what you can do**, **what you will see**, **what the information means**, and **what actions you should take** based on that information.

---

## 1. Getting Data In: How to Log Your Training

PowerGlide tracks three main areas of your athletic life: **Gym** (strength training), **Water** (canoe/kayak paddling), and **Body** (weight and composition).

### The Primary Workflow: The `import` Command
Instead of tapping buttons on a mobile app after every set, you should write your workout notes in a simple text file or notepad app on your phone, and paste them into PowerGlide later.

**What you do:**
Type `powerglide import` in your terminal.
Paste your text block (e.g., `Bench Press 60x8, 50x8,8,8`). Press `Ctrl+Z` (Windows) or `Ctrl+D` (Mac/Linux) and then `Enter`.

**What you will see:**
The system will output a neat table showing how it parsed your notes into Exercises, Weights, Reps (or Time), and Tags. It will also show any errors (like unrecognized formats). If successful, it will say `[OK] Saved gym session`.

<pre style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; font-family: Consolas, monospace; line-height: 1.4;">
<span style="color: gray;">> powerglide import</span>
                Session: 2026-03-06                
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ <span style="color: cyan;">Exercise</span>            ┃ <span style="color: yellow;">Tags</span>  ┃ <span style="color: lime;">Sets</span>              ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
┃ Barbell Bench Press ┃ feet  ┃ <span style="color: lime;">60.0kg x 8</span> <span style="color: gray;">@8</span>     ┃
┃ Dead Bug            ┃ -     ┃ <span style="color: lime;">0kg x 10, 0kg x 10</span>┃
└─────────────────────┴───────┴───────────────────┘
  <span style="color: lime;">[OK]</span> Saved gym session 2026-03-06 (3 sets).
</pre>

**What it means:**
The system has permanently stored your session. It has automatically calculated your estimated 1-Rep Max (1RM) for weight lifts, and the Volume Load (Weight × Reps) for your muscles.

### Quick Logging: The `log` Commands
If you just did a single exercise and want to log it quickly without entering "paste mode".

**What you do:**
Type `powerglide gym log "Plank" 0 3x60s` or `powerglide water log 500 1:55 --rpe 8`.

**What you will see:**
A green success message confirming the sets or metric pieces were added to today's session.

---

## 2. Reading the Dashboard: `powerglide stats`

The `stats` command is your daily Command Center. Before you train, you should run this command.

**What you do:**
Type `powerglide stats` (or `powerglide stats "Bench Press"` to see specific exercise correlations).

### Area A: The ACWR (Acute:Chronic Workload Ratio)
**What you will see:**
A colored box displaying your latest ACWR ratio (e.g., `1.15`), a zone status (e.g., `optimal`, `danger`), and an explanation of your Acute (last 7 days) and Chronic (last 28 days) loads.

<pre style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; font-family: Consolas, monospace; line-height: 1.4;">
<span style="color: lime;">╭─────────────────────── ACWR ────────────────────────╮</span>
<span style="color: lime;">│</span> <span style="color: white; font-weight: bold;">Latest ACWR</span>  <span style="color: lime; font-weight: bold;">1.15</span>  (optimal)                        <span style="color: lime;">│</span>
<span style="color: lime;">│</span> Date: 2026-03-06  |  Acute: 620.5  | Chronic: 540.2 <span style="color: lime;">│</span>
<span style="color: lime;">╰─────────────────────────────────────────────────────╯</span>
</pre>

*   **Green (Optimal):** Usually between 0.8 and 1.3.
*   **Yellow/Orange (Caution):** Getting close to 1.5.
*   **Red (Danger):** Above 1.5.

**What it means internally:**
This is your **Injury Risk** gauge. It measures the total physical work you've done recently compared to what your body is historically used to.
*   If your Acute load spikes way higher than your Chronic base, your tissue vulnerability goes way up.

**What you should do about it:**
*   **If Green:** Proceed with your planned training. Your body is adapted to the current workload.
*   **If Orange/Red:** **Back off.** Even if you feel "good," your tendons and structural tissues are under extreme, unadapted stress. You have a mathematically higher risk of a non-contact injury (like a tear or strain). Reduce your volume or intensity today.

### Area B: 72-Hour Fatigue Map
**What you will see:**
A bar chart listing your top 5 most fatigued muscle groups over the last 3 days, accompanied by a "weighted volume" number.

<pre style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; font-family: Consolas, monospace; line-height: 1.4;">
<span style="color: dodgerblue;">╭─────────────────── Fatigue (72h) ───────────────────╮</span>
<span style="color: dodgerblue;">│</span> <span style="color: white; font-weight: bold;">72-Hour Load by Muscle Group</span>                        <span style="color: dodgerblue;">│</span>
<span style="color: dodgerblue;">│</span>                                                     <span style="color: dodgerblue;">│</span>
<span style="color: dodgerblue;">│</span>   Pectoralis Major <span style="color: #F0E6BD;">██████████████</span><span style="color: #8C8C9A;">░░░░░░░░</span> <span style="color: #A0E0A0;">2450</span>      <span style="color: dodgerblue;">│</span>
<span style="color: dodgerblue;">│</span>   Triceps Brachii  <span style="color: #F0E6BD;">████████</span><span style="color: #8C8C9A;">░░░░░░░░░░░░░░</span> <span style="color: #A0E0A0;">1420</span>      <span style="color: dodgerblue;">│</span>
<span style="color: dodgerblue;">│</span>   Deltoids         <span style="color: #F0E6BD;">█████</span><span style="color: #8C8C9A;">░░░░░░░░░░░░░░░░░</span> <span style="color: #A0E0A0;">850</span>       <span style="color: dodgerblue;">│</span>
<span style="color: dodgerblue;">╰─────────────────────────────────────────────────────╯</span>
</pre>

**What it means internally:**
This tells you exactly where your physical *External Load* was distributed. If "Pectoralis Major" has a massive bar, you've done a lot of pressing volume.

**What you should do about it:**
*   Use this to guide your exercise selection. If your hamstrings are maxed out on the fatigue map, but you planned to do deadlifts today, you should swap to an upper-body or core focus to allow local tissue recovery.
*   **Crucial caveat:** This is *not* your biological energy level. A muscle might have low volume, but if your Central Nervous System (CNS) is fried (you slept poorly, you feel sluggish), **listen to your body** and rest.

### Area C: TUT Progression & C1 Correlation (If an exercise is specified)
**What you will see:**
If you type `powerglide stats "Plank"`, you will see your **Time Under Tension (TUT)** progression (Max TUT and Total TUT in seconds).
If you type `powerglide stats "Bench Press"`, you will see a **C1 Correlation (r)** score (e.g., `r = -0.75`).

**What it means internally:**
*   **TUT:** Shows if you are actually holding your isometric core exercises longer over time.
*   **C1 Correlation:** This is the holy grail for paddlers. It takes your Gym 1RM (strength) and compares it mathematically against your Water 500m split times (speed) from the same week. A highly negative number (closing in on -1.0) means *getting stronger at this lift correlates with paddling faster*. A number near 0 (or positive) means the exercise might not be translating to boat speed.

**What you should do about it:**
*   If an exercise has a strong negative correlation, keep doing it! It's making you faster.
*   If an exercise has a weak or positive correlation after months of data, consider dropping it from your program. It's causing fatigue without giving you free speed on the water.

---

## 3. Investigating the Data: `powerglide history` and `explain`

Sometimes you want to see your past workouts, or understand *why* the system gave you a certain number.

### Using `history`
**What you do:**
Type `powerglide gym history -n 10` to see your last 10 gym sessions.

**What you will see:**
Tables showing exact weights, reps/time, and a calculated `e1RM` (estimated 1-Rep Max) for dynamic lifts.

<pre style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; font-family: Consolas, monospace; line-height: 1.4;">
<span style="color: gray;">> powerglide gym history -n 1</span>
                  2026-03-06  |  ID 9                  
  <span style="color: gray;">Set ID #</span>   <span style="color: cyan;">Exercise</span>          <span style="color: lime;">Weight</span> Reps <span style="color: magenta;">e1RM</span>   <span style="color: yellow;">Tags</span> 
 ──────────────────────────────────────────────────────
  <span style="color: gray;">set_24 1</span>   <span style="color: cyan;">Barbell Bench</span>     <span style="color: lime;">60.0kg</span>    8 <span style="color: magenta;">75.0kg</span> <span style="color: yellow;">feet</span> 
  <span style="color: gray;">set_25 2</span>   <span style="color: cyan;">Barbell Bench</span>     <span style="color: lime;">50.0kg</span>    8 <span style="color: magenta;">62.5kg</span> <span style="color: yellow;">feet</span> 
  <span style="color: gray;">set_26 1</span>   <span style="color: cyan;">Plank</span>              <span style="color: lime;">0.0kg</span>  <span style="color: white;">60s</span> <span style="color: magenta;">-</span>      <span style="color: yellow;">-</span>    
</pre>

**What it means:**
You can see at a glance if your maximal strength capacity is trending up or down.

### Using `explain`
**What you do:**
Type `powerglide explain 1rm -w 100 -r 5` or `powerglide explain acwr`.

**What you will see:**
A detailed algebraic breakdown. For `1rm`, it will show exactly which formula it picked (Brzycki vs. Epley) based on the reps, and how the math concluded your max is roughly 112.5kg. For `acwr`, it shows the decay rate of your fatigue.

<pre style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; font-family: Consolas, monospace; line-height: 1.4;">
<span style="color: gray;">> powerglide explain 1rm -w 100 -r 5</span>
╭────────────────── 1RM Explanation ───────────────────╮
│ <span style="color: white; font-weight: bold;">Brzycki Formula (Reps ≤ 10)</span>                          │
│                                                      │
│ Formula: Weight × (36 / (37 - Reps))                 │
│ Calculation: 100.0kg × (36 / (37 - 5))               │
│ Result: <span style="color: lime; font-weight: bold;">112.5 kg</span>                                     │
╰──────────────────────────────────────────────────────╯
</pre>

**What it means:**
PowerGlide is a "glass box." It never hides its algorithms. If you are ever confused by a metric, `explain` reveals the sports science backing it up.

## Summary Checklist for Daily Use

1.  **Morning:** Check how you feel (Heart Rate Variability, general soreness).
2.  **Pre-Workout:** Open terminal, run `powerglide stats`.
    *   Check ACWR (Am I in the red? If so, back off).
    *   Check Fatigue Map (Which muscles need a break?).
3.  **Workout:** Train hard, take shorthand notes on your phone.
4.  **Post-Workout:** Open terminal, run `powerglide import`, paste notes.
5.  **Review:** Run `powerglide stats` again to see how your ACWR shifted based on the session you just imported.
