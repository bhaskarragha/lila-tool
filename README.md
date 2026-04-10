# 🎯 LILA BLACK — Player Journey Visualizer

**Live Demo:** `[ADD YOUR STREAMLIT URL HERE]`  
**GitHub:** `https://github.com/bhaskarragha/lila-tool`

---

## What This Is

A web-based tactical recon tool that turns raw LILA BLACK telemetry data into visual player journey maps. Built specifically for **Level Designers** — not data scientists. Select a map and match, and immediately see where players moved, where they fought, where they looted, and where they died.

---

## Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Core language |
| Streamlit | 1.28.1 | Web app framework |
| Plotly | 5.17.0 | Interactive charts and heatmaps |
| Pandas | 2.0.3 | Data filtering and manipulation |
| PyArrow | 13.0.0 | Reading parquet files |
| NumPy | 1.24.3 | Heatmap density calculations |

**Hosting:** Streamlit Cloud (free tier)

---

## ✅ No Setup Required — Data Included

**The player data and minimap images are included directly in this repository.**

You can run the tool immediately after cloning — no need to add any external files.

The repository contains:
- `player_data/` — 5 days of production gameplay data (Feb 10–14, 2026) from LILA BLACK
- `assets/minimaps/` — minimap images for all 3 maps

---

## Setup — Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/bhaskarragha/lila-tool.git
cd lila-tool
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
# or if pip not found:
python -m pip install -r requirements.txt
```

### 3. Run
```bash
python -m streamlit run app.py
```

Open `http://localhost:8501` in your browser. Data loads automatically.

---

## Folder Structure

```
lila-tool/
├── app.py                  ← Main Streamlit app — entry point
├── data_loader.py          ← Reads parquet files, cleans data, cascading filters
├── coordinate_mapper.py    ← Converts game world (x,z) → minimap pixels
├── visualization.py        ← Player path chart + heatmap chart (Plotly)
├── heatmap.py              ← Heatmap helpers
├── utils.py                ← Helper functions
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
├── ARCHITECTURE.md         ← Technical decisions and data flow
├── INSIGHTS.md             ← 3 design insights from the data
├── player_data/            ← ✅ INCLUDED — 5 days of game telemetry
│   ├── February_10/        ← 437 parquet files (.nakama-0 format)
│   ├── February_11/        ← 293 files
│   ├── February_12/        ← 268 files
│   ├── February_13/        ← 166 files
│   └── February_14/        ← 79 files (partial day)
└── assets/
    └── minimaps/           ← ✅ INCLUDED — map background images
        ├── AmbroseValley_Minimap.png
        ├── GrandRift_Minimap.png
        └── Lockdown_Minimap.jpg
```

---

## About the Data

**Source:** 5 days of production gameplay data (February 10–14, 2026) from LILA BLACK

| Metric | Value |
|---|---|
| Total files | 1,243 |
| Total event rows | ~89,000 |
| Unique players | 339 |
| Unique matches | 796 |
| Maps | AmbroseValley, GrandRift, Lockdown |

**File format:** Apache Parquet, no `.parquet` extension — files end in `.nakama-0`

**Data schema:**

| Column | Type | Description |
|---|---|---|
| `user_id` | string | UUID = human player. Pure number = bot. |
| `match_id` | string | Match identifier |
| `map_id` | string | AmbroseValley, GrandRift, or Lockdown |
| `x` | float32 | World X coordinate |
| `y` | float32 | Elevation — not used for 2D map |
| `z` | float32 | World Z coordinate |
| `ts` | timestamp | Milliseconds elapsed within the match |
| `event` | bytes | Event type — auto-decoded to string |

**8 event types:**

| Event | Meaning |
|---|---|
| `Position` | Human player movement |
| `BotPosition` | Bot movement |
| `Kill` | Human killed another human |
| `Killed` | Human was killed by another human |
| `BotKill` | Human killed a bot |
| `BotKilled` | Human was killed by a bot |
| `KilledByStorm` | Player died to the storm |
| `Loot` | Player picked up an item |

---

## How to Use the Tool

1. **Select Map** — sidebar Step 1 dropdown (AmbroseValley, GrandRift, Lockdown)
2. **Select Date** — only dates with data for your chosen map appear
3. **Select Match** — only matches from that map + date appear. Choose one or **ALL MATCHES** for the full day
4. **Timeline slider** — drag left to rewind, right to advance. Watch paths grow and shrink. Label shows `T+01:23 / T+04:12`
5. **Toggle events** — show/hide kills, deaths, loot, storm deaths from the sidebar
6. **Toggle players** — show/hide humans (solid blue) or bots (grey dashed) separately
7. **Spawn/Extract markers** — green triangle = spawn point, red square = end point
8. **Heatmaps** — enable Kill Zone, Death Zone, or Traffic Density in sidebar. Full map with colour overlay appears below

---

## Deployment — Streamlit Cloud

1. Push repo to GitHub (public)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub → click **Create app**
4. Select **Deploy a public app from GitHub**
5. Set GitHub URL to: `https://github.com/bhaskarragha/lila-tool/blob/main/app.py`
6. Click **Deploy** — live URL ready in ~2 minutes

---

## Environment Variables

None required. All data and configuration is included in the repository.
