# Architecture Document
## LILA BLACK — Player Journey Visualizer

---

## What I Built and Why

**Stack: Python + Streamlit + Plotly + Pandas + PyArrow + NumPy**

**Why Streamlit?**
Streamlit converts Python scripts into interactive web apps with zero frontend code. For a PM building a Level Designer tool under a 5-day deadline, this was the right call:
- A working, deployable web app from a single Python file
- No HTML, CSS, JavaScript, or API layer required
- Deploys to Streamlit Cloud from a GitHub repo in under 2 minutes
- Code is readable English — any team member can maintain it without engineering support

**Why Plotly?**
Plotly produces interactive charts natively (hover, zoom, toggle legend items). `go.Scattergl` (WebGL-accelerated scatter) handles hundreds of path segments without frame drops. `go.Heatmap` overlays density grids directly on the minimap image coordinate system. No other Python charting library supports all three of these requirements out of the box.

**Why Parquet + PyArrow?**
The data arrives in parquet format. PyArrow reads it directly from disk with no database, ETL pipeline, or infrastructure overhead. 89,000 rows fit in memory and load in under 3 seconds.

---

## Data Flow

```
player_data/
  February_10/ ... February_14/
  (1,243 files ending in .nakama-0 — valid parquet, no extension)
        │
        ▼
  data_loader.py
  ┌────────────────────────────────────────────┐
  │ 1. PyArrow reads each file → DataFrame     │
  │ 2. event bytes decoded:                    │
  │      b'Kill' → 'Kill'                      │
  │ 3. user_id classified:                     │
  │      UUID format → player_type = human     │
  │      numeric     → player_type = bot       │
  │ 4. ts (milliseconds) converted:            │
  │      ts_unix = ts_ms / 1000.0              │
  │      (elapsed seconds within the match)    │
  │ 5. match_id: .nakama-0 suffix stripped     │
  │ 6. date_folder column added per file       │
  └────────────────────────────────────────────┘
        │
        ▼  (cascading sidebar filters applied)
  apply_filters(map_id, date_folder, match_id)
        │
        ▼
  coordinate_mapper.py
  ┌────────────────────────────────────────────┐
  │ Vectorised world (x,z) → pixel (px, py)    │
  │ using per-map scale + origin config        │
  │ No .apply() — pure Pandas column math      │
  └────────────────────────────────────────────┘
        │
        ▼
  safe_sample() — cap at 5,000 rows if needed
        │
        ▼
  visualization.py
  ┌────────────────────────────────────────────┐
  │ build_minimap_figure()                     │
  │  - Timeline filter: ts_unix ≤ cutoff       │
  │  - Minimap PNG as layout image background  │
  │  - Human paths: go.Scattergl (WebGL fast)  │
  │  - Bot paths: go.Scatter dashed            │
  │  - Spawn markers: pentagon (human) /       │
  │    hexagon (bot) at first position         │
  │  - End markers: per player type at last    │
  │    recorded position                       │
  │  - Event markers: kill/death/loot/storm    │
  │                                            │
  │ build_heatmap_figure()                     │
  │  - Minimap PNG as background               │
  │  - np.histogram2d → density grid           │
  │  - Custom gaussian-style smoothing passes  │
  │  - go.Heatmap overlay with rgba colorscale │
  │  - Supports: kill, death, traffic, loot    │
  └────────────────────────────────────────────┘
        │
        ▼
  app.py (Streamlit UI)
  ┌────────────────────────────────────────────┐
  │ Sidebar: cascading filters                 │
  │   Map → Date (filtered) → Match (filtered) │
  │ Timeline scrubber → timeline_pct (0–1.0)   │
  │ Main area: minimap figure                  │
  │ Below: heatmap panels (if enabled)         │
  └────────────────────────────────────────────┘
```

---

## Coordinate Mapping — Step by Step

The game world uses a large float coordinate space (e.g. -500 to +500). The minimap image is 1024×1024 pixels. The conversion normalises world coordinates to pixel space in three steps.

**Step 1: Subtract the map origin**
Each map has a known world position that corresponds to pixel (0,0) — the top-left corner of the minimap.

```python
u = (x - origin_x) / scale
v = (z - origin_z) / scale
```

This produces a normalised value in the 0–1 range.

**Step 2: Scale to pixel dimensions**
```python
pixel_x = u * 1024
pixel_y = (1 - v) * 1024
```

**Step 3: Flip the Y axis**
Game engines use Z increasing "northward" (upward on minimap). PNG images use Y increasing downward. Subtracting v from 1 flips the axis so path overlays align correctly with the image.

**Map configurations (from the data README):**

| Map | Scale | Origin X | Origin Z |
|---|---|---|---|
| AmbroseValley | 900 | -370 | -473 |
| GrandRift | 581 | -290 | -290 |
| Lockdown | 1000 | -500 | -500 |

**Implementation — fully vectorised, no `.apply()`:**
```python
cfg = MAP_CONFIG[map_name]
u = (df["x"] - cfg["origin_x"]) / cfg["scale"]
v = (df["z"] - cfg["origin_z"]) / cfg["scale"]
df["pixel_x"] = u * 1024
df["pixel_y"] = (1 - v) * 1024
```

Using `.apply()` with `result_type="expand"` causes `KeyError: 0` on Python 3.14. Vectorised math avoids this and is 10–50× faster.

---

## Timeline Scrubber — How It Works

The Streamlit slider outputs `timeline_elapsed` (seconds from 0 → match duration).

Converted to a fraction:
```python
timeline_pct = timeline_elapsed / elapsed_max  # 0.0 to 1.0
```

Inside `build_minimap_figure()`, before drawing:
```python
ts = _timeline_seconds(df["ts_unix"])
ts_min, ts_max = ts.dropna().min(), ts.dropna().max()
cutoff = ts_min + (ts_max - ts_min) * timeline_pct
df = df[ts <= cutoff].copy()
```

Only rows with `ts_unix ≤ cutoff` are drawn. Dragging left removes events from the end (rewind). Dragging right adds them back (advance).

**Why manual scrubber instead of auto-playback?**
Auto-playback requires re-rendering the Plotly chart every second. Each render re-processes the full dataframe pipeline. On 5,000+ rows this takes 1.5–3 seconds per frame, producing unusable choppy animation. The manual scrubber gives designers full control — they jump to any moment of interest without waiting for playback to reach it.

---

## Heatmap Design

Four heatmap layers, each rendered as a separate full-map panel:
- **Kill Zone** — `Kill` + `BotKill` events
- **Death Zone** — `Killed` + `BotKilled` + `KilledByStorm` events
- **Traffic** — `Position` + `BotPosition` events
- **Loot Zone** — `Loot` events (added assumption — see ASSUMPTIONS.md)

Each uses `np.histogram2d` to bin pixel coordinates into a density grid, followed by custom gaussian-style smoothing passes to produce readable blobs rather than noisy pixel grids. The minimap image renders at reduced opacity as the background, with the heatmap overlay at 60–68% opacity on top.

**Why separate panels instead of overlay?**
Overlaying multiple heatmaps on the same chart produces illegible colour mixing. Each heatmap panel is independently readable and can be compared side by side.

---

## Spawn and End Markers

Each player path shows:
- **Spawn marker** — first recorded position (pentagon for human, hexagon for bot)
- **End marker** — last recorded position (type depends on exit event: death, storm, or unknown)

Different shapes for humans vs bots ensure readability when markers overlap — colour alone is insufficient when 20+ players are displayed simultaneously.

---

## Assumptions

See `ASSUMPTIONS.md` for full detail. Summary:

| Assumption | Decision |
|---|---|
| `ts` = match-elapsed ms, not wall clock | Displayed as T+MM:SS elapsed time |
| Bot detection | Numeric user_id = bot; UUID = human |
| `y` column = elevation | Ignored for 2D minimap plotting |
| Auto-playback too slow | Replaced with manual scrubber |
| Heatmap overlay illegible | Each heatmap rendered as separate panel |
| Loot heatmap needed | Added as 4th heatmap layer |
| Spawn/end markers needed | Added with distinct shapes per player type |
| 5,000 row render cap | Random sample with fixed seed for reproducibility |

---

## Major Tradeoffs

| Decision | Chose | Gave Up | Why |
|---|---|---|---|
| Streamlit vs React | Streamlit | Full UI control | Deployable in minutes; PM can maintain it |
| Plotly vs D3 | Plotly | Custom rendering | Interactive natively; supports layout images |
| Files vs database | Parquet files | SQL query speed | 89k rows fits in memory; zero infrastructure |
| 5,000 row sample cap | Sampling | Full precision on all-day views | Browser freezes above ~10k scatter points |
| Manual scrubber vs auto-play | Manual scrubber | Cinematic playback | Auto-play too slow to re-render at acceptable frame rate |
| Separate heatmaps vs overlay | Separate panels | Single unified view | Overlaid gradients are unreadable |
| Cascading filters | Map→Date→Match | Show all options at once | Eliminates "no data found" errors entirely |
| Scattergl for human paths | WebGL rendering | Fallback compatibility | Handles hundreds of path segments without frame drops |
| 4 heatmap types | Kill/Death/Traffic/Loot | Simplicity | Loot is core to extraction shooter routing decisions |
