# ⚡ PowerGlide: The Definitive CLI Encyclopedia

A high-fidelity, granular reference for every command, flag, and sub-app in the PowerGlide ecosystem.

---

## 🛠️ Global Options
*System-level flags available at the root level.*

- `--help` : Show the top-level help menu.
- `--install-completion` : Installs shell completion for your current terminal (PowerShell/Bash/Zsh). Makes typing commands much faster with `Tab`.
- `--show-completion` : Displays the completion script for manual configuration.

---

## 🚀 Root-Level Commands
*Standalone utilities for quick access.*

### `import`
**Usage:** `powerglide import [FILE] [OPTIONS]`  
Parse shorthand logs from a file or interactive paste mode.
- `[FILE]` : (Optional) Path to a `.txt` file.
- `--type`, `-t` : `gym` or `water` (Default: `gym`).
- `--dry-run` : Show the parsed table without saving to the DB.

### `format`
**Usage:** `powerglide format`  
Prints the reference card for the **Shorthand Syntax**. Essential for learning how to write logs that `import` can read.

### `rpe`
**Usage:** `powerglide rpe`  
Displays the **Modified Borg CR-10 Scale** (1–10).

### `seed`
**Usage:** `powerglide seed [OPTIONS]`  
Initializes the database with 800+ exercises.
- `--force` : Drops and re-seeds all data.

### `history`
**Usage:** `powerglide history [OPTIONS]`  
A unified view of recent activity.
- `--limit`, `-n` : Number of sessions to show (Default: 5).

### `constraint`
**Usage:** `powerglide constraint [ACTION] [NAME] [OPTIONS]`
- `[ACTION]` : `add`, `end`, `delete`, or `list`.
- `[NAME]` : Name of the constraint.
- `--start` : Start date (YYYY-MM-DD).
- `--end` : End date (YYYY-MM-DD).
- `--desc` : Detailed notes.

### `stats`
**Usage:** `powerglide stats [EXERCISE]`  
The Command-Center view.
- `[EXERCISE]` : (Optional) Exercise name for **C1 Correlation (r)** calculation.

### `dashboard`
**Usage:** `powerglide dashboard`  
Launches the Streamlit scientific dashboard.

---

## 🏋️ Gym App (`gym`)
*Commands for the weight room.*

### `gym log`
- `[EXERCISE]` : Name (fuzzy matched).
- `[WEIGHT]` : Kg lifted.
- `[SETS_REPS]` : e.g., `4x8`, `8,8,6`, `50x8,60x8`, or time-based `3x60s`, `10kg x 60s`, `60s,45s`.
- `--rpe`, `-r` : 1–10 effort.
- `--tags`, `-t` : e.g., `paused,beltless`.
- `--date`, `-d` : `DD/MM/YY` or `YYYY-MM-DD`.

### `gym history`
- `--limit`, `-n` : Number of sessions.
- `--exercise`, `-e` : Filter by exercise name.

### `gym delete`
- `--session`, `-s` : Delete an entire session by ID.
- `--set` : Delete a single set by ID.
- `--all` : Delete all gym data.

---

## 🌊 Water App (`water`)
*Commands for on-water C1 performance.*

### `water log`
- `[DISTANCE]` : Meters.
- `[TIME]` : `M:SS` or `M:SS.ms`.
- `--spm` : Average strokes per minute.
- `--rpe`, `-r` : Piece RPE (1-10).
- `--wind` : `headwind`, `tailwind`, `crosswind`, `none`.
- `--condition` : `calm`, `choppy`, `wavy`.
- `--leg-drive-rpe` : Rate your leg drive (0–10).
- `--date`, `-d` : Date (DD/MM/YY or YYYY-MM-DD).
- `--notes` : Piece-specific notes.

### `water history`
- `--limit`, `-n` : Number of sessions.

### `water delete`
- `--session`, `-s` : Delete a water session by ID.
- `--piece` : Delete a single piece by ID.
- `--all` : Delete all water data.

---

## ⚖️ Body App (`body`)
*Weight and composition tracking.*

### `body log`
- `--weight`, `-w` : Total weight (kg).
- `--bf` : Body Fat %.
- `--mm` : Muscle Mass (kg).
- `--water` : Body Water %.
- `--visceral` : Visceral fat level.
- `--bmr` : Kcal.
- `--date`, `-d` : Measurement date.
- `--notes` : Custom notes.

### `body history`
- `--limit`, `-n` : Number of records.

### `body delete`
- `--id`, `-i` : Delete a specific record by ID.

---

## 🧠 Explain App (`explain`)
*The "Glass Box" math module.*

### `explain 1rm`
- `--weight`, `-w` : Weight lifted.
- `--reps`, `-r` : Reps.

### `explain acwr`
- No flags. Breaks down current workload risk.

### `explain fatigue`
- `--muscle`, `-m` : Target muscle group.
- `--hours`, `-h` : Lookback window (Default: 72).

### `explain workout`
- `--id` : Session ID.

---

## 🔧 Management App (`manage`)
*System and Data management.*

### `manage export`
- `--format`, `-f` : `json` or `csv`.
- `--output`, `-o` : Output directory.

---

> **Tip:** Inside the interactive shell (`powerglide` with no args), you don't need to type the "powerglide" prefix. Just type `gym log ...` or `stats`.
