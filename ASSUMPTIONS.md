# Assumptions Document
## LILA BLACK — Player Journey Visualizer

This document records every assumption and product decision made during the build, including why each decision was made and what alternative was considered.

---

## Assumption 1: Spawn and Extract Markers Are Essential for Readability

**The problem**
Without any reference point, a player path is just a line floating on the map. You can see where the player went, but you cannot tell where they started or where they ended up. For a level designer trying to understand routing decisions, this is nearly useless — did the player start from the north or the south? Did they extract or die?

**The decision**
We added distinct markers for every player path:
- **Human spawn:** Pink pentagon at the first recorded position
- **Bot spawn:** Teal hexagon at the first recorded position
- **Human death/extract:** Red circle-X at the last recorded position
- **Bot death:** Orange marker at the last recorded position
- **Storm death:** Purple diamond — specific to storm kills

**Why different shapes for humans vs bots?**
Using colour alone is not enough when paths overlap. Pentagon vs hexagon gives a secondary visual cue that works even when markers overlap on a busy map.

**What we considered instead**
A simple numbered label per player. Rejected because it becomes unreadable when 20+ players are shown simultaneously.

---

## Assumption 2: Loot Heatmap Is a Required Fourth Layer

**The problem**
The assignment specified kill zones, death zones, and traffic heatmaps. After building those three, the tool felt incomplete for an extraction shooter context. Loot is the primary driver of player routing in an extraction game — where players go first is almost entirely determined by loot spawn locations.

**The decision**
We added a fourth heatmap: **Loot Zone Heat**. This shows density of `Loot` events — where players are actually picking up items. This is distinct from traffic (where players walk) and gives designers a direct view of which loot spawns are being used and which are being ignored.

**Why this matters**
A designer can compare the Traffic heatmap against the Loot heatmap. If players are moving through an area but not looting there, it means loot spawns in that zone are either missing or too low quality to be worth stopping for. This is an actionable insight the original three heatmaps cannot provide alone.

**What we considered instead**
Overlaying loot events as scatter points on the traffic map. Rejected because it created visual clutter when combined with movement paths and event markers.

---

## Assumption 3: Heatmaps Must Be Separate — Not Overlaid

**The problem**
During development, we attempted to render kill, death, traffic, and loot heatmaps simultaneously on the same map chart. The result was visually unreadable — overlapping colour gradients produced a muddy brown-green blend that conveyed no useful information.

**The decision**
Each heatmap is rendered as a separate, full-size chart below the main player path map. The designer enables one or more heatmaps from the sidebar and each appears as its own panel side by side, each with the full minimap image as its background.

**The tradeoff**
A designer cannot see heatmap data and player paths at the same time in a single view. However, for level design analysis, reviewing heatmaps is typically a separate workflow from reviewing individual player journeys — the separation keeps each view clean and readable.

**What we considered instead**
A tab system (tab 1: paths, tab 2: heatmaps). Rejected because Streamlit tabs require a full page reload on each switch, which re-runs the entire data pipeline and feels slow.

---

## Assumption 4: Manual Timeline Scrubber Is Better Than Auto-Playback

**The problem**
The original design called for automatic match playback — a play button that would advance the timeline at real speed, re-rendering the map every second. We built and tested this approach.

**What went wrong**
Auto-playback requires Streamlit to re-render the Plotly chart every second. Each re-render reads and re-processes the filtered dataframe, recalculates pixel coordinates, and rebuilds the entire figure. On a dataset of 5,000+ rows, this took 1.5–3 seconds per frame. The result was a choppy, laggy animation that was worse than useless for understanding match progression.

**The decision**
We replaced auto-playback with a **manual scrubber slider**. The designer drags the slider to any point in the match and the map updates to show exactly that moment. This gives full control — pause on any moment, compare two specific timestamps, move at your own pace.

**Why this is actually better for the use case**
Level designers are not watching matches for entertainment. They are looking for specific patterns — "where does the fight start?", "at what point do players stop looting and start moving toward extraction?" A manual scrubber lets them jump directly to the moment of interest.

**What we considered instead**
Pre-computing animation frames as a Plotly figure with frames and a built-in play button. This works well for small datasets but with 89,000 rows, pre-computing all frames would take 30–60 seconds on load, making the tool unusable.

---

## Assumption 5: Cascading Filters Prevent "No Data Found" Errors

**The problem**
Initial versions showed all maps, all dates, and all matches in three independent dropdowns. Users frequently selected combinations with no data — for example, a date when a particular map was not in rotation. This produced an empty map with a confusing warning.

**The decision**
Filters are cascading:
1. Select a map → date dropdown shows only dates that have data for that map
2. Select a date → match dropdown shows only matches from that exact map + date combination
3. **"ALL MATCHES"** at the top of the match dropdown shows the full day's activity combined

**The tradeoff**
Changing the map selection resets date and match selections. Slightly annoying if comparing the same date across two maps. However, it completely eliminates "no data" errors and makes the tool usable by someone unfamiliar with the dataset.

---

## Assumption 6: 5,000 Row Sample Cap for Rendering Performance

**The problem**
The full dataset contains ~89,000 event rows across 5 days. Rendering all rows as Plotly scatter traces in a browser freezes the page for 10–20 seconds and produces an unreadable hairball of overlapping lines.

**The decision**
When the filtered dataset exceeds 5,000 rows, we apply a random sample of 5,000 rows using a fixed random seed (42) for reproducibility. Individual match views typically contain 50–300 rows and are never sampled.

**Why 5,000?**
Empirically tested: 5,000 rows renders in under 2 seconds, produces visually meaningful paths, and preserves the spatial distribution of events. At 10,000 rows performance degrades noticeably. At 89,000 the browser freezes.

**The tradeoff**
"ALL MATCHES" views may miss some events due to sampling. Individual match views are always shown in full and are the recommended mode for detailed analysis.

**Is it technically possible to show all 89,000 rows?**
Yes — and there are four ways to do it, each with increasing engineering effort:

- **Option 1 — Remove the cap entirely:** One-line change. But the browser freezes for 10–20 seconds on every filter change or slider move. On Streamlit Cloud it could time out and crash.

- **Option 2 — Render as a static image:** Convert the Plotly chart to a PNG instead of an interactive chart. Handles millions of points instantly. But you lose all interactivity — no hover, no zoom, no toggling individual players on and off.

- **Option 3 — Use Deck.gl or Kepler.gl:** Purpose-built for rendering millions of geospatial points using WebGL. Would handle 89,000 rows easily. Requires more engineering effort and time, hence was avoided.

- **Option 4 — Pre-aggregate server-side with DuckDB:** Query and summarise the data before sending to the browser. Only send summary statistics, not raw rows. Handles any dataset size. Again, significantly more engineering effort, hence was avoided.

**The V2 decision**
For this build, the 5,000 row cap is a deliberate tradeoff. The tool is designed for single-match analysis where 100% of data is always shown. For full-day views, the sample is statistically representative of the overall pattern. Options 3 or 4 are the right path for a production version of this tool.

---

## Assumption 7: Unknown Exit Type for Human Players

**The problem**
In some matches, a human player's path simply ends — the last recorded position has no corresponding death event (`Killed`, `BotKilled`, or `KilledByStorm`). This means we cannot determine with certainty whether the player successfully extracted, disconnected mid-match, or experienced a data recording gap.

**The decision**
We treat these cases as **"Unknown Exit"** and mark them with a distinct neutral marker (grey circle) at the last recorded position. We do not assume extraction or death — we surface the ambiguity honestly so a designer knows the data ends there but cannot draw conclusions about how or why.

**Why not assume extraction?**
Assuming every path without a death event ended in successful extraction would overcount extraction rates and misrepresent the data. The honest approach is to flag uncertainty rather than fill it with a guess.

**What this looks like in the tool**
Unknown exit markers appear as grey circles at the end of human paths where no death event was recorded. They are visible when the "Spawn/Extract Markers" toggle is enabled in the sidebar.

---

## Assumption 8: Bot Paths That End Without an Event Are Left as-Is

**The problem**
Similar to human unknown exits, some bot paths simply stop — the last `BotPosition` event is recorded and then the file ends. There is no corresponding `BotKilled` event to explain the termination.

**The decision**
No assumption is made. The bot path line simply ends at its last recorded position. No end marker is added, no label is shown, and no conclusion is drawn. The line stops and that is all the data tells us.

**Why no marker?**
Bot behaviour in the data is already acknowledged as not fully simulating human gameplay (see INSIGHTS.md, Insight 2). Adding an "unknown exit" marker for bots would give false significance to what is likely a routine session end or server-side cleanup event. The path ending is noted; nothing more is inferred.

---

## Assumption 9: ts Column Treated as Match-Elapsed Milliseconds

**The problem**
The `ts` column in the parquet files contains timestamps that appear to start from a Unix epoch of 1970-01-21, not 2026. This is because `ts` represents milliseconds elapsed within the match, not wall-clock time.

**The decision**
We treat `ts` as elapsed milliseconds within a match session. For the timeline scrubber, we convert to elapsed seconds (`ts_unix = ts_ms / 1000`) and display as `T+MM:SS` format — minutes and seconds into the match, not a calendar date or time.

**Why this matters**
If we treated `ts` as a real wall-clock timestamp, the timeline scrubber would show dates in January 1970 and match durations would appear to be weeks long. By treating it as elapsed time, the scrubber correctly shows a match lasting e.g. `T+00:00` to `T+04:23`.

**What we considered instead**
Displaying raw millisecond values on the slider. Rejected immediately — a designer looking at a slider showing `1,852,321 ms` has no intuitive sense of where they are in the match. `T+03:05` is immediately understandable.
