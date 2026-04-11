# 🎯 LILA BLACK — Player Journey Visualizer

**Live Demo:** `https://lila-black-recon.streamlit.app`  
**GitHub:** `https://github.com/bhaskarragha/lila-tool`

---

## What This Is

A web-based tactical recon tool that turns raw LILA BLACK telemetry data into visual player journey maps. Built specifically for **Level Designers** — not data scientists. Select a map and match, and immediately see where players moved, where they fought, where they looted, and where they died.

---

## Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Core language |
| Streamlit | latest | Web app framework |
| Plotly | latest | Interactive charts and heatmaps |
| Pandas | latest | Data filtering and manipulation |
| PyArrow | latest | Reading parquet files |
| NumPy | latest | Heatmap density calculations |

**Hosting:** Streamlit Cloud (free tier)

---

## ✅ No Setup Required — Data Included

**The player data and minimap images are included directly in this repository.**

Clone the repo and run immediately — no external files needed.

| Included | What |
|---|---|
| `player_data/` | 5 days of production gameplay (Feb 10–14, 2026), 1,243 files, ~89,000 events |
| `assets/minimaps/` | Minimap images for AmbroseValley, GrandRift, Lockdown |

---

## Setup — Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/bhaskarragha/lila-tool.git
cd lila-tool-2
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
# or:
python -m pip install -r requirements.txt
```

### 3. Run
```bash
python -m streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Folder Structure

```
lila-tool/
├── app.py                  ← Main Streamlit app
├── data_loader.py          ← Reads + cleans parquet files, cascading filters
├── coordinate_mapper.py    ← Game world (x,z) → minimap pixels
├── visualization.py        ← Player paths + heatmap charts (Plotly)
├── heatmap.py              ← Heatmap helpers
├── utils.py                ← Helper functions
├── requirements.txt
├── README.md
├── ARCHITECTURE.md         ← Technical decisions and data flow
├── INSIGHTS.md             ← 5 design insights from the data
├── ASSUMPTIONS.md          ← Product decisions and tradeoffs
├── player_data/            ← ✅ Included
│   ├── February_10/        ← 437 parquet files (.nakama-0)
│   ├── February_11/        ← 293 files
│   ├── February_12/        ← 268 files
│   ├── February_13/        ← 166 files
│   └── February_14/        ← 79 files (partial day)
└── assets/
    └── minimaps/           ← ✅ Included
        ├── AmbroseValley_Minimap.png
        ├── GrandRift_Minimap.png
        └── Lockdown_Minimap.jpg
```

---

## About the Data

**Source:** 5 days of production gameplay from LILA BLACK (February 10–14, 2026)

| Metric | Value |
|---|---|
| Total files | 1,243 |
| Total events | ~89,000 |
| Unique players | 339 |
| Unique matches | 796 |
| Maps | AmbroseValley, GrandRift, Lockdown |

**File format:** Apache Parquet, no `.parquet` extension — files end in `.nakama-0`

**Schema:**

| Column | Type | Description |
|---|---|---|
| `user_id` | string | UUID = human. Numeric = bot. |
| `match_id` | string | Match identifier |
| `map_id` | string | AmbroseValley / GrandRift / Lockdown |
| `x` | float32 | World X coordinate |
| `y` | float32 | Elevation (not used for 2D map) |
| `z` | float32 | World Z coordinate |
| `ts` | timestamp | Milliseconds elapsed within match |
| `event` | bytes | Event type — auto-decoded by app |

**8 event types:** `Position`, `BotPosition`, `Kill`, `Killed`, `BotKill`, `BotKilled`, `KilledByStorm`, `Loot`

---

## How to Use the Tool

1. **Select Map** — sidebar Step 1 (AmbroseValley, GrandRift, Lockdown)
2. **Select Date** — only dates with data for your map appear
3. **Select Match** — only matches from that map+date appear. Use **ALL MATCHES** for full-day view
4. **Timeline scrubber** — drag left to rewind, right to advance. Shows `T+01:23 / T+04:12` format
5. **Toggle players** — show/hide humans (solid blue) or bots (grey dashed) separately
6. **Toggle events** — show/hide kills, deaths, loot, storm deaths individually
7. **Spawn/Extract markers** — pentagon = human spawn, hexagon = bot spawn, X = death point
8. **Heatmaps** — enable Kill Zone, Death Zone, Traffic, or Loot Zone from sidebar. Full map with colour density overlay (blue → green → yellow → red) appears below

---

## Documentation

| File | Contents |
|---|---|
| `ARCHITECTURE.md` | Tech decisions, data flow, coordinate mapping, tradeoffs |
| `INSIGHTS.md` | 5 design insights from the data with evidence and designer actions |
| `ASSUMPTIONS.md` | 7 product assumptions made during build with reasoning |

---

## Deployment

Hosted on Streamlit Cloud. To redeploy from this repo:

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **Create app → Deploy a public app from GitHub**
3. Set GitHub URL to: `https://github.com/bhaskarragha/lila-tool/blob/main/app.py`
4. Click **Deploy**

---

## Environment Variables

None required.
