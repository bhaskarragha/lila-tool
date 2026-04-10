# Architecture Document
## LILA BLACK — Player Journey Visualizer

---

## What I Built and Why

**Stack: Python + Streamlit + Plotly + Pandas + PyArrow + NumPy**

**Why Streamlit?**
Streamlit converts Python scripts into interactive web apps with zero frontend code. For a PM building a Level Designer tool, this was the right call:
- A working, deployable web app in a single Python file
- No HTML, CSS, JavaScript, or API layer required
- Deploys to Streamlit Cloud in 2 minutes from a GitHub push
- Code is readable English — any team member can maintain it

**Why Plotly?**
Plotly produces interactive charts natively (hover, zoom, toggle legend items). Crucially, `go.Scatter` on a fixed pixel-space axis maps perfectly onto minimap images as a background layer. `go.Heatmap` overlays density grids directly on the same coordinate system.

**Why Parquet + PyArrow?**
The data is already in parquet format. PyArrow reads it efficiently without needing a database, ETL pipeline, or any infrastructure. Files load directly from disk.

---

## Data Flow

```
player_data/
  February_10/ ... February_14/
  (files ending in .nakama-0 — valid parquet, no extension)
        │
        ▼
  data_loader.py
  ┌──────────────────────────────────────────┐
  │ 1. PyArrow reads each file to DataFrame  │
  │ 2. event bytes decoded: b'Kill' → 'Kill' │
  │ 3. user_id classified:                   │
  │      UUID format → player_type = human   │
  │      numeric     → player_type = bot     │
  │ 4. ts (milliseconds) parsed:             │
  │      ts_unix = ts_ms / 1000.0            │
  │      (elapsed seconds within match)      │
  │ 5. match_id: strip .nakama-0 suffix      │
  │ 6. date_folder column added per file     │
  └──────────────────────────────────────────┘
        │
        ▼  (cascading sidebar filters applied)
  apply_filters(map_id, date_folder, match_id)
        │
        ▼
  coordinate_mapper.py
  ┌──────────────────────────────────────────┐
  │ Vectorised world → pixel conversion      │
  │ (x, z) → (pixel_x, pixel_y)             │
  │ per-map scale + origin config            │
  └──────────────────────────────────────────┘
        │
        ▼
  safe_sample() — cap at 5,000 rows if needed
        │
        ▼
  visualization.py
  ┌──────────────────────────────────────────┐
  │ build_minimap_figure()                   │
  │  - Timeline filter: df[ts_unix ≤ cutoff] │
  │  - Minimap PNG as layout image (below)   │
  │  - Human paths: go.Scattergl (fast)      │
  │  - Bot paths: go.Scatter dashed          │
  │  - Start markers: green triangle         │
  │  - End markers: red square               │
  │  - Event markers: kill/death/loot/storm  │
  │                                          │
  │ build_heatmap_figure()                   │
  │  - Minimap PNG as background             │
  │  - np.histogram2d → density grid         │
  │  - Custom gaussian-style smoothing       │
  │  - go.Heatmap overlay with rgba colors   │
  └──────────────────────────────────────────┘
        │
        ▼
  app.py (Streamlit UI)
  ┌──────────────────────────────────────────┐
  │ Sidebar: cascading filters               │
  │   Map → Date (filtered) → Match (filtered│
  │ Timeline slider → timeline_pct (0.0–1.0) │
  │ Main area: minimap figure                │
  │ Below: heatmap section (if enabled)      │
  └──────────────────────────────────────────┘
```

---

## Coordinate Mapping — Step by Step

The game world uses a large float coordinate space (e.g. -500 to +500). The minimap image is 1024×1024 pixels. The conversion normalises world coordinates to pixel space in three steps.

**Step 1: Subtract the map origin**
Each map has a known world position that corresponds to pixel (0, 0) — the top-left corner of the minimap image.

```
u = (x - origin_x) / scale
v = (z - origin_z) / scale
```

This produces a normalised value in the 0–1 range.

**Step 2: Scale to pixel dimensions**
```
pixel_x = u * 1024
pixel_y = (1 - v) * 1024
```

**Step 3: Flip the Y axis**
Game engines use Z increasing "northward" (upward on the minimap). PNG images use Y increasing downward. Subtracting v from 1 flips the axis so the path overlay aligns correctly with the image.

**Map configurations (from the data README):**

| Map | Scale | Origin X | Origin Z |
|---|---|---|---|
| AmbroseValley | 900 | -370 | -473 |
| GrandRift | 581 | -290 | -290 |
| Lockdown | 1000 | -500 | -500 |

**Implementation — vectorised Pandas (no `.apply()`):**
```python
cfg = MAP_CONFIG[map_name]
u = (df["x"] - cfg["origin_x"]) / cfg["scale"]
v = (df["z"] - cfg["origin_z"]) / cfg["scale"]
df["pixel_x"] = u * 1024
df["pixel_y"] = (1 - v) * 1024
```
Using `.apply()` with `result_type="expand"` causes `KeyError: 0` on Python 3.14. Vectorised math avoids this entirely and is 10–50× faster.

---

## Timeline Slider — How It Works

The Streamlit slider outputs an integer `timeline_elapsed` (seconds from match start, 0 → total duration).

This is converted to a fraction:
```python
timeline_pct = timeline_elapsed / elapsed_max   # 0.0 to 1.0
```

Inside `build_minimap_figure()`, before drawing anything:
```python
ts = _timeline_seconds(df["ts_unix"])
ts_min = ts.dropna().min()
ts_max = ts.dropna().max()
cutoff = ts_min + (ts_max - ts_min) * timeline_pct
df = df[ts <= cutoff].copy()
```

Only rows with `ts_unix ≤ cutoff` are drawn. Dragging left removes events from the end of the match (rewind). Dragging right adds them back (fast-forward). The `ts_unix` column stores elapsed seconds since the match start, not wall-clock time.

---

## Assumptions

| Situation | Assumption Made |
|---|---|
| Files have no `.parquet` extension | PyArrow reads by path — works fine |
| `ts` is match-elapsed milliseconds, not epoch time | Converted to elapsed seconds: `ts_unix = ts_ms / 1000` |
| Bot detection | Numeric `user_id` = bot; UUID format = human |
| `y` column = elevation | Ignored entirely for 2D minimap plotting |
| February 14 partial day | Loaded and treated normally; partial data is expected |
| Match ID has `.nakama-0` suffix | Stripped for display; filtering uses cleaned ID |
| Minimap image filenames | Assumed exactly as provided: `AmbroseValley_Minimap.png`, `GrandRift_Minimap.png`, `Lockdown_Minimap.jpg` |
| 5,000 row sample cap | Representative of full dataset; individual match views are not capped |

---

## Major Tradeoffs

| Decision | Chose | Gave Up | Why It's Fine |
|---|---|---|---|
| Streamlit vs React | Streamlit | Full UI control | PM can maintain it; deploys in minutes; no build pipeline |
| Plotly vs D3 | Plotly | Pixel-perfect custom rendering | Interactive out of the box; supports layout images as backgrounds |
| Parquet files vs database | Files | SQL query speed at scale | 89k rows fits in memory; no infrastructure overhead |
| 5,000 row render cap | Sampling | Full precision on all-day views | Browser freezes above ~10k scatter points; 5k is visually representative |
| No authentication | None | Access control | Internal design tool; Streamlit Cloud auth can be added later |
| Cascading sidebar filters | Map→Date→Match | Showing all options at once | Prevents "no data found" errors; guides the user to valid selections |
| Separate heatmap section | Below main map | Overlay on paths chart | Cleaner z-ordering; prevents heatmap colours obscuring path details |
| Scattergl for human paths | WebGL rendering | Fallback compatibility | Handles hundreds of path segments without frame drops |
| Custom heatmap smoothing | NumPy blur passes | Sharp per-bin accuracy | Produces readable density blobs rather than noisy pixel grids |
