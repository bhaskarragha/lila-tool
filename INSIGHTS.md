# Design Insights
## LILA BLACK — Player Journey Analysis

Five observations from 5 days of production gameplay data with evidence and actionable recommendations for level designers.

---

## Insight 1: Kill Activity Is Funnelled Into 15–20% of the Map

**What caught my eye**
Enabling the Kill Zone thermal on AmbroseValley reveals that red and orange density zones cover a small fraction of the total playable area. The remaining map shows near-zero kill interaction — not just low activity, but effectively zero — across every match analysed.

**Evidence**
- Kill heatmap shows the same hotspot zones consistently across February 10, 11, and 12 — the pattern is repeatable across days and matches, ruling out a one-off anomaly
- Storm death markers (purple diamonds) cluster at the southern boundary of AmbroseValley, confirming the one-directional storm pushes all players northward into the same narrow zone
- Traffic density shows player movement spreading across the map early in the match, then converging into the kill cluster zone as the storm closes — the storm is the funnel
- The same clustering pattern appears on GrandRift, suggesting it is a systemic design issue across maps, not specific to one

**Actionable items**
- Review storm path direction — a multi-directional or rotating storm would distribute player convergence more evenly across the map
- Add high-value loot to currently dead zones to create a genuine risk/reward decision for players willing to go off the beaten path early
- Add terrain features (cover, elevation changes) to empty zones to make them tactically viable, not just traversal space

**Metrics affected:** Match-to-match encounter variance, zone dwell time, player perception of map diversity, replayability

**Why a level designer should care**
If 80% of the map is functionally irrelevant to the average match outcome, that is wasted design and art budget. Every match plays out in the same geography — which kills replayability. Redistributing engagement across the full map is one of the highest-leverage changes available without building a new map.

---

## Insight 2: Bots and Humans Take Fundamentally Different Paths — Bot Data Misleads Heatmaps

**What caught my eye**
Toggling the human/bot path display reveals a stark pattern. Bot paths (grey dashed lines) are short, anchored to 3–4 fixed positions per map, and nearly identical across different matches. Human paths (solid blue lines) are longer, more varied, and visibly respond to the storm boundary.

**Evidence**
- `BotPosition` events on GrandRift show bots anchoring to the same pixel clusters across multiple match IDs — strong evidence of fixed patrol waypoints rather than dynamic pathfinding
- `KilledByStorm` events appear almost exclusively for human players — bots appear to have hardcoded storm avoidance, so they never make the routing mistakes humans make
- Bot movement radius per match is significantly smaller than human movement radius — bots are patrolling, not traversing
- In matches with high bot counts (>60% numeric user IDs), kill and death heatmaps shift toward bot patrol positions rather than reflecting human-vs-human combat zones

**Actionable items**
- Cross-reference bot spawn positions against the waypoint config in the game build — confirm whether bots are using outdated or placeholder patrol paths
- When using the tool for design analysis, filter to human-only paths for reliable insights. Use the "Show Humans" toggle and disable "Show Bots" to isolate real player behaviour
- Flag bot-heavy matches as lower-confidence data for balance decisions

**Metrics affected:** Reliability of heatmap data, bot vs human kill ratio per zone, playtesting signal accuracy

**Why a level designer should care**
If bots are not moving like humans, heatmaps from bot-heavy matches show AI patrol behaviour, not player behaviour. Design decisions based on this data risk optimising the map for bot routes rather than human gameplay. The tool's human/bot toggle makes this distinction visible and actionable.

---

## Insight 3: Loot Pickups Are Absent From High-Traffic Zones

**What caught my eye**
Comparing the Traffic Density heatmap against the Loot Zone heatmap reveals a mismatch. Players are moving through large sections of the map but not picking up loot there. Loot markers cluster in a small number of locations even when traffic shows players passing through many others.

**Evidence**
- On Lockdown (smallest map), loot events are almost entirely concentrated in one central building cluster — players entering from any other direction find nothing worth stopping for
- Traffic density on AmbroseValley shows player movement across the northern half of the map, but loot markers concentrate in 2–3 fixed interior locations — exterior routes generate no loot interactions
- The absence is consistent across multiple days, ruling out a sampling issue — it is structural, not random
- Storm death events cluster at the map edge, suggesting players are running from one loot cluster to the storm boundary without finding secondary loot along the way

**Actionable items**
- Cross-reference loot event pixel positions against the loot spawn table in the game config — confirm which spawns are generating pickups vs which exist but are never touched
- Add or upgrade loot quality along high-traffic routes that show zero loot interactions — players will stop if there is something worth picking up
- On Lockdown specifically, distribute loot spawns across at least 3 distinct clusters to break the "everyone converges on centre" pattern

**Metrics affected:** Average loot collected per match, time-to-first-loot, zone dwell time, player routing diversity

**Why a level designer should care**
Loot placement is the primary driver of player routing. If loot only exists in one or two locations, every player goes there — which directly causes the kill funnel problem in Insight 1. Fixing loot distribution is upstream of fixing engagement distribution. These two problems are connected, and loot is the lever to pull first.

---

## Insight 4: Storm Deaths Reveal a Timing and Boundary Perception Problem

**What caught my eye**
Storm death markers (purple diamonds) cluster in a distinctive band just inside what players appear to believe is the safe zone boundary. Players are not dying at the extreme edge of the map — they are dying in areas they should theoretically be able to reach safely.

**Evidence**
- Using the timeline scrubber to advance to the 60–80% point of a match, storm deaths appear in a concentrated band rather than being scattered — suggesting a specific phase of the match when players misjudge the storm
- The band of storm deaths is consistent across multiple matches on AmbroseValley — same approximate pixel zone repeatedly
- Human players account for the overwhelming majority of storm deaths (bots appear storm-aware) — this is a human perception problem, not a pathfinding one
- Loot events immediately preceding storm death events (visible by scrubbing back 30 seconds) show players stopping to loot in zones that become storm-affected shortly after — players are being caught looting in dangerous areas

**Actionable items**
- Review the storm warning system — is the visual/audio cue appearing far enough in advance of actual damage?
- Check whether the storm damage boundary is lagging behind the visual shrink animation — players may be dying in areas that look safe but are already in the damage zone
- Consider a "storm incoming" secondary warning indicator at a wider radius than the current first warning

**Metrics affected:** Storm death rate, match completion rate, player frustration metrics, perceived fairness of storm mechanic

**Why a level designer should care**
Storm deaths that feel unfair are a major source of player frustration. If players are dying in areas they believed were safe, the issue is not player skill — it is a communication failure in the level design. The storm boundary timing and visual feedback are level design problems, not game code problems.

---

## Insight 5: Match Duration Varies Significantly — Short Matches May Indicate Early Wipe Zones

**What caught my eye**
Using the timeline scrubber on different match IDs within the same map and date reveals significant variation in match duration. Some matches have paths that span the full T+00:00 to T+04:00+ range. Others end abruptly at T+01:30 or earlier, with players' end markers (red squares) appearing in the same general area of the map.

**Evidence**
- Short matches (ending before T+02:00) show end markers clustering in 1–2 specific zones of the map — suggesting these are early fight zones where players are eliminated quickly
- Longer matches show more spatially distributed end markers, with human players reaching extraction zones in the north/northeast areas
- The timeline scrubber makes this pattern visible: at T+01:00, short matches already show 50%+ of their players with end markers placed, while long matches have most players still moving
- GrandRift shows more short-match clustering than AmbroseValley, suggesting it may have higher early-game lethality

**Actionable items**
- Map the early wipe zones against loot placement — players dying early may be converging on the same high-value loot spawn and fighting immediately on drop
- Consider whether early-game cover in the identified wipe zones would create more tactical options (flanking, repositioning) rather than immediate contact
- Use the timeline scrubber to filter to T+00:00→T+01:30 across multiple matches to build a clearer picture of opening-phase movement before making design changes

**Metrics affected:** Average match duration, early elimination rate, new player retention (early deaths are demoralising), spawn zone balance

**Why a level designer should care**
Consistent early wipe zones indicate a spawn balance problem. If players are reliably eliminated in the same area in the first 90 seconds regardless of match, the opening phase has no strategic variance. This is a solvable level design problem — spawn point distribution, early cover placement, and loot spread all influence it.
