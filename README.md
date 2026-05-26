# FastBox Delivery Simulator — Nexgensis Technologies Assignment

**Overview:**
- **Purpose:** Simulate one day of operations for the fictional delivery company FastBox (assignment for Nexgensis Technologies). The simulator assigns packages to agents, computes travel distances, and produces reports identifying the most efficient agent.

**Quick Run:**

```bash
python simulator.py data.json
```

**Files (important):**
- `simulator.py`: main program (CLI). Contains core simulation, dynamic mode, bonus features (delays, ASCII routes, plotting, mid-day join, CSV export).
- `data.json`: sample input (warehouses, agents, packages).
- `requirements.txt`: Python dependencies (matplotlib for plotting).
- `Python Assignment(Delivery System Test Cases)/`: test inputs and generated reports/plots.

**Code Structure:**
- **Functions:**
  - `euclidean(a,b)`: computes Euclidean distance.
  - `load_data(path)`: load JSON input.
  - `assign_packages(data)`: legacy batch assignment (nearest agent to each warehouse).
  - `simulate(assignments, data)`: batch simulation once assignments are fixed.
  - `simulate_dynamic(data, mid_join, max_delay, ascii_routes)`: sequential processing that supports mid-day agent joins, random delivery delays, and records per-step routes.
  - `pick_best_agent(report)`: selects the agent with lowest average distance per package.
  - `plot_routes(stats, out_path)`: creates PNG route visualization using matplotlib.
  - `save_report(report, path)`: writes JSON report to disk.

**Simulation Logic:**
1. **Input parsing:** read input JSON containing `warehouses`, `agents`, and `packages`.
2. **Assignment:** either
	- batch mode (`assign_packages`) — assign each package to the nearest agent to the warehouse, or
	- dynamic mode (`simulate_dynamic`) — process packages in order, allowing mid-day agent join and re-calculating the nearest active agent per package.
3. **Delivery simulation:** for each package, compute distances:
	- agent current position -> warehouse (d1)
	- warehouse -> destination (d2)
	- update agent position = destination
	- accumulate `total_distance` and `packages_delivered` per agent
4. **Delays (optional):** if `--random-delays N` is used, add a random delay up to N (minutes) per delivery and record it.
5. **Reporting:** compute per-agent `total_distance`, `packages_delivered`, and `efficiency = total_distance / packages_delivered` (rounded). Determine `best_agent` by lowest efficiency.
6. **Output:** write report JSON, optional ASCII route file, CSV exporting top performer, and optional PNG plot of routes.

**CLI Options (high level):**
- `--random-delays <float>`: enable random per-delivery delay (max minutes).
- `--ascii-routes`: write a human-readable `report_routes.txt` showing each agent's steps.
- `--mid-join AGENT:X,Y:AFTER`: add a new agent mid-day at coordinates (X,Y) after `AFTER` packages have been processed (e.g., `A5:10,10:3`).
- `--export-csv <path>`: export top performer stats to CSV.
- `--plot`: generate a PNG route plot next to the JSON report (requires matplotlib).
- `-o/--output`: specify output JSON filename (defaults to `report_<input>.json`).

**Example commands:**

```bash
# basic run
python simulator.py data.json

# with bonuses: delays, ascii routes, mid-join and CSV export
python simulator.py data.json --random-delays 5 --ascii-routes --mid-join A5:10,10:3 --export-csv top.csv

# generate a PNG route plot (install matplotlib first)
python simulator.py data.json --plot
```

**Output files produced:**
- `report_<input>.json` — per-agent stats plus `best_agent`.
- `report_routes.txt` — ASCII route steps (if `--ascii-routes`).
- `<report>.png` — route visualization (if `--plot`).
- `<top>.csv` — CSV with top performer (if `--export-csv`).

**Assumptions & Notes:**
- Distances use Euclidean straight-line distance.
- If ambiguous cases arise (tie distances), the first-agent encountered is chosen.
- `simulate_dynamic` is recommended when using mid-join or delays because it records per-step routes.
- The repository contains final per-test reports and plots in `Python Assignment(Delivery System Test Cases)/`.