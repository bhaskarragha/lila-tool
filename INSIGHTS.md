# Design Insights
## LILA BLACK — Player Journey Analysis

Three observations from 5 days of production data that level designers should act on immediately.

---

## Insight 1: Kill Activity Is Funnelled Into 15–20% of the Map

**What caught my eye**

Enabling the Kill Zone thermal on AmbroseValley reveals that red and orange density zones cover a small fraction of the total playable area. The remaining map shows near-zero kill interaction — not just low activity, but effectively zero — across every match analysed.

**Evidence**
- Kill heatmap consistently shows the same hotspot zones across February 10, 11, and 12 — the pattern is repeatable across days and matches, not a one-off
- Storm death markers (purple diamonds on the player path map) cluster at the southern boundary of AmbroseValley, confirming that the one-directional storm pushes all players northward into the same narrow zone
- Traffic density heatmap shows player movement spreading across the map in the early match phase, then converging into the kill cluster zone as the storm closes in
- The same clustering pattern appears on GrandRift, suggesting it is a systemic design issue across maps, not specific to one

**Actionable items**
- Review storm path direction — a multi-directional or rotating storm would distribute player convergence more evenly
- Add high-value loot to currently dead zones to create a genuine risk/reward decision: "do I go off the beaten path early?"
- Add terrain features (cover, elevation changes) to empty zones to make them tactically viable, not just traversal space

**Metrics affected:** Match-to-match encounter variance, zone dwell time, player perception of map diversity

**Why a level designer should care**

If 80% of the map is functionally irrelevant to the average match outcome, that is wasted design and art budget. More critically, it means every match plays out in the same geography — which kills replayability. Redistributing engagement across the full map is one of the highest-leverage changes available without building a new map.

---

## Insight 2: Bot Paths Are Fixed — They Do Not Simulate Human Behaviour

**What caught my eye**

Toggling the human/bot path display reveals a striking pattern. Bot paths (grey dashed lines) are short, clustered around 3–4 fixed positions per map, and largely identical across different matches. Human paths (solid blue lines) are longer, more varied, and visibly respond to the storm boundary.

**Evidence**
- `BotPosition` events on GrandRift show bots anchoring to the same pixel clusters across multiple match IDs — strong evidence of fixed patrol waypoints rather than dynamic pathfinding
- `KilledByStorm` events appear almost exclusively for human players. Bots appear to have hardcoded storm avoidance, meaning they never die to the storm the way humans do
- Bot movement radius per match is significantly smaller than human movement radius — bots are not traversing the map, they are patrolling small fixed zones
- In bot-heavy matches (where >70% of `user_id` values are numeric), the kill and death heatmaps look markedly different from human-heavy matches — clusters shift toward bot patrol positions

**Actionable items**
- Cross-reference bot spawn positions against the waypoint config in the game build — confirm whether bots are using outdated or placeholder patrol paths
- Flag bot-heavy matches (>60% numeric user IDs) in the tool as lower-confidence data for design decisions
- If bots are used for load testing or playtesting, their movement data should not be weighted equally with human data when making map balance decisions

**Metrics affected:** Reliability of heatmap data in bot-heavy sessions, bot kill/death ratio per zone, accuracy of playtesting signal

**Why a level designer should care**

If bots are not moving like humans, the heatmaps from bot-heavy matches are showing bot behaviour, not player behaviour. Design decisions based on this data risk optimising the map for AI patrol routes rather than human gameplay patterns. The tool now makes this distinction visible — use it.

---

## Insight 3: Loot Events Are Absent From High-Traffic Zones

**What caught my eye**

Comparing the Traffic Density heatmap against the Loot event markers (gold stars on the player path map) reveals a mismatch. Players are moving through large sections of the map but not picking up loot there. The loot markers cluster in a small number of locations even when traffic shows players passing through many others.

**Evidence**
- On Lockdown (the smallest map), loot events are almost entirely concentrated in one central building cluster — players entering from any other direction find nothing worth stopping for
- Traffic density on AmbroseValley shows player movement across the northern half of the map, but loot markers are concentrated in 2–3 fixed interior locations — exterior routes generate no loot interactions
- The absence is consistent across multiple days, ruling out a sampling issue — it is structural, not random
- Storm death events cluster at the map edge, suggesting players are running from one loot cluster to the storm boundary without finding secondary loot along the way

**Actionable items**
- Cross-reference loot event pixel positions against the loot spawn table in the game config — confirm which spawns are actually generating pickups vs which exist in the data but are never touched
- Add or upgrade loot quality along high-traffic routes that currently show zero loot interactions — players will stop if there is something worth picking up
- On Lockdown specifically, distribute loot spawns across at least 3 distinct clusters to break the "everyone converges on centre" pattern

**Metrics affected:** Average loot collected per match, time-to-first-loot, zone dwell time, player routing diversity

**Why a level designer should care**

Loot placement is the primary driver of player routing decisions. If loot only exists in one or two locations, every player goes to those locations — which directly causes the kill funnel problem identified in Insight 1. Fixing loot distribution is upstream of fixing engagement distribution. These two problems are connected, and loot placement is the lever to pull first.
