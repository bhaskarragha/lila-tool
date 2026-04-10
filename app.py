import streamlit as st
import pandas as pd

from data_loader import load_all_data, apply_filters, get_maps, get_dates_for_map, get_matches_for_map_date
from coordinate_mapper import add_pixel_coords
from visualization import build_minimap_figure, build_heatmap_figure
from utils import count_events, count_players, get_timeline_bounds, safe_sample

st.set_page_config(page_title="LILA BLACK", page_icon="🎯", layout="wide")


def _fmt_clock(total_seconds: int) -> str:
    mins = max(0, int(total_seconds)) // 60
    secs = max(0, int(total_seconds)) % 60
    return f"T+{mins:02d}:{secs:02d}"


def _module_header(icon_svg: str, title: str) -> None:
    st.markdown(
        f'<div class="mod"><span class="badge">{icon_svg}</span><span>{title}</span></div>',
        unsafe_allow_html=True,
    )

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@500;700&family=Share+Tech+Mono&family=Teko:wght@600;700&display=swap');
.stApp {
  background: radial-gradient(1200px 700px at 60% -100px, rgba(112,219,255,0.10), transparent 60%), #090a12;
  background-image:
    linear-gradient(180deg, rgba(20,26,52,0.28) 0%, rgba(10,10,20,0.94) 100%),
    repeating-linear-gradient(0deg,transparent,transparent 44px,rgba(215,255,47,0.018) 44px,rgba(215,255,47,0.018) 45px),
    repeating-linear-gradient(90deg,transparent,transparent 44px,rgba(114,255,216,0.018) 44px,rgba(114,255,216,0.018) 45px);
  color:#f3f5f7; font-family:'Rajdhani','Share Tech Mono',monospace;
}
.block-container {
  padding-top: 64px !important;
  padding-bottom: 16px !important;
  padding-left: 16px !important;
  padding-right: 16px !important;
  max-width: 100% !important;
}
[data-testid="stSidebar"] {
  background:
    linear-gradient(180deg,rgba(18,22,40,0.96) 0%, rgba(12,14,28,0.98) 100%),
    repeating-linear-gradient(0deg, transparent, transparent 28px, rgba(114,255,216,0.03) 28px, rgba(114,255,216,0.03) 29px);
  border-right:1px solid rgba(114,255,216,0.28);
}
[data-testid="stSidebarCollapseButton"] { display:none !important; }
[data-testid="collapsedControl"] { display:none !important; }
[data-testid="stSidebar"] * { font-family:'Rajdhani','Share Tech Mono',monospace !important; }
.stSidebar > div:first-child {
  padding-top: 3.8rem;
}
.sec { font-size:9px; font-weight:700; letter-spacing:0.2em; text-transform:uppercase;
  color:#d9ff34; margin:16px 0 6px 0; padding-bottom:4px;
  border-bottom:1px solid rgba(217,255,52,0.30); text-shadow:0 0 8px rgba(217,255,52,0.34);
  background: linear-gradient(90deg, rgba(217,255,52,0.12), rgba(114,255,216,0.02));
  border-radius: 8px;
  padding: 6px 8px;
}
.mod {
  display:flex; align-items:center; gap:8px;
  font-family:Orbitron, monospace;
  font-size:10px; letter-spacing:.12em; text-transform:uppercase;
  color:#e7edff;
  border:1px solid rgba(114,255,216,0.30);
  border-radius:8px;
  padding:7px 9px;
  margin:14px 0 8px 0;
  background:linear-gradient(90deg, rgba(114,255,216,0.16), rgba(114,255,216,0.03));
}
.mod .badge {
  width:18px; height:18px; display:inline-flex; align-items:center; justify-content:center;
  border-radius:6px;
  border:1px solid rgba(114,255,216,0.44);
  color:#72ffd8; font-size:11px; font-weight:700;
  background:rgba(114,255,216,0.10);
}
[data-testid="stSidebar"] .mod .badge svg {
  width:12px;
  height:12px;
  stroke:#72ffd8;
  fill:none;
  stroke-width:1.8;
}
[data-testid="stMetric"] { background:linear-gradient(180deg,#161c34 0%, #10162a 100%); border:1px solid rgba(114,255,216,0.24);
  border-top:2px solid #d7ff2f; border-radius:10px; padding:8px 10px;
  box-shadow:0 8px 20px rgba(0,0,0,0.28), 0 0 0 1px rgba(114,255,216,0.07) inset; }
[data-testid="stMetricLabel"] { color:rgba(114,255,216,0.90) !important; font-size:10px !important; letter-spacing:.08em; }
[data-testid="stMetricValue"] { color:#f7ffbf !important; font-family:'Orbitron',monospace !important; }
[data-testid="stMetricLabel"] p,
[data-testid="stMetricValue"] div {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
[data-testid="stMetricDelta"] {
  font-size: 10px !important;
  color: #d7ff2f !important;
  letter-spacing: .08em !important;
}
h1,h2,h3,h4 { font-family:'Orbitron',monospace !important; color:#d7ff2f !important; }
hr { border-color:rgba(114,255,216,0.16) !important; }
.stCheckbox label { color:#f0f2f5 !important; font-size:12px; }
[data-testid="stExpander"] { border:1px solid rgba(114,255,216,0.22) !important; background:#13182b !important; border-radius:8px !important; }
[data-testid="stExpander"] summary {
  font-family:'Orbitron', monospace !important;
  font-size: 12px !important;
  letter-spacing: .06em;
}
.legend-item { display:flex; align-items:center; gap:8px; margin:3px 0; font-size:11px; color:#eef1f5; }
.ldot { width:12px; height:12px; border-radius:50%; display:inline-block; flex-shrink:0; }
div[data-baseweb="select"] > div {
  background:#171d34; border:1px solid rgba(114,255,216,0.32); border-radius:8px;
}
div[data-baseweb="select"] * { color:#f4f6f8 !important; }
div[data-baseweb="select"] svg { color:#72ffd8 !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div {
  min-height: 36px;
}
div[data-baseweb="slider"] [role="slider"] {
  background:#d7ff2f !important; border:2px solid #344606 !important;
  box-shadow:0 0 0 2px rgba(217,255,52,0.26), 0 0 14px rgba(217,255,52,0.48);
}
div[data-baseweb="slider"] > div > div > div {
  background:linear-gradient(90deg,#72ffd8 0%,#9eff5f 50%,#d7ff2f 100%) !important;
}
.stButton > button {
  width:100%;
  background:linear-gradient(180deg,#242b45 0%,#1a2138 100%);
  border:1px solid rgba(114,255,216,0.35);
  color:#e6fff8;
  border-radius:8px;
  font-family:'Orbitron',monospace;
  font-size:10px;
  letter-spacing:.08em;
}
.stButton > button:hover {
  border-color:#d7ff2f;
  color:#faffd6;
  box-shadow:0 0 12px rgba(217,255,52,0.30);
}
[data-testid="stHorizontalBlock"] .stButton > button {
  min-height: 36px;
}
[data-testid="stPlotlyChart"] {
  border:1px solid rgba(255,120,220,0.22);
  border-radius:10px;
  background:rgba(24,20,35,0.58);
  box-shadow:inset 0 0 0 1px rgba(255,120,220,0.08), 0 0 22px rgba(255,120,220,0.10);
}
[data-testid="stHorizontalBlock"] {
  gap: 8px !important;
}
[data-testid="stMetric"] {
  min-height: 82px;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 8px;
  margin-bottom: 6px;
}
.kpi-card {
  background: linear-gradient(180deg,#161c34 0%, #10162a 100%);
  border: 1px solid rgba(114,255,216,0.24);
  border-top: 2px solid #d7ff2f;
  border-radius: 10px;
  padding: 8px 10px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.28), 0 0 0 1px rgba(114,255,216,0.07) inset;
  min-height: 82px;
}
.kpi-label {
  color: rgba(114,255,216,0.90);
  font-size: 10px;
  letter-spacing: .08em;
  text-transform: uppercase;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kpi-value {
  color: #f7ffbf;
  font-family: 'Orbitron', monospace;
  font-size: 28px;
  line-height: 1.05;
  margin-top: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.hero-title {
  font-family:Teko, Orbitron, monospace;
  font-size:36px;
  font-weight:700;
  color:#d7ff2f;
  text-shadow:0 0 20px rgba(114,255,216,0.35);
  margin-bottom:10px;
  letter-spacing:.03em;
  transform: skewX(-6deg);
}
.subhead {
  font-family:Orbitron, monospace;
  font-size:11px;
  letter-spacing:.11em;
  color:#72ffd8;
  margin:4px 0 8px 0;
  text-transform:uppercase;
}
.panel-shell {
  border:1px solid rgba(114,255,216,0.24);
  border-radius:12px;
  padding:10px 10px 2px 10px;
  background:linear-gradient(180deg, rgba(20,24,44,0.58) 0%, rgba(14,16,30,0.45) 100%);
  box-shadow:0 10px 26px rgba(0,0,0,0.26), inset 0 0 0 1px rgba(114,255,216,0.06);
}
[data-testid="stSidebar"] .stCheckbox {
  margin-top: 2px;
  margin-bottom: 2px;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner="[ LOADING TACTICAL DATA... ]")
def get_data():
    return load_all_data(max_files_per_folder=150)


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:Teko,Orbitron,monospace;font-size:30px;font-weight:700;color:#d7ff2f;text-align:center;padding:8px 0;text-shadow:0 0 16px rgba(114,255,216,0.38);letter-spacing:0.08em;transform:skewX(-6deg);">BLACK</div>', unsafe_allow_html=True)
    st.divider()

    raw_df = get_data()
    if raw_df.empty:
        st.error("No data in player_data/")
        st.stop()

    # CASCADING — each dropdown depends on previous
    _module_header(
        '<svg viewBox="0 0 16 16"><path d="M8 1v14M1 8h14M3 3l10 10M13 3L3 13"/></svg>',
        "Deployment",
    )
    st.markdown('<div class="sec">MAP SECTOR</div>', unsafe_allow_html=True)
    maps = get_maps(raw_df)
    selected_map = st.selectbox("Map", ["— select —"] + maps, key="map_sel")

    st.markdown('<div class="sec">DATE SHARD</div>', unsafe_allow_html=True)
    if selected_map != "— select —":
        dates = get_dates_for_map(raw_df, selected_map)
        selected_date = st.selectbox("Date", ["— select —"] + dates, key="date_sel")
    else:
        st.selectbox("Date", ["select map first"], disabled=True, key="date_dis")
        selected_date = "— select —"

    st.markdown('<div class="sec">MATCH ID</div>', unsafe_allow_html=True)
    if selected_date != "— select —" and selected_map != "— select —":
        matches = get_matches_for_map_date(raw_df, selected_map, selected_date)
        selected_match = st.selectbox("Match", ["ALL MATCHES"] + matches, key="match_sel")
    else:
        st.selectbox("Match", ["select date first"], disabled=True, key="match_dis")
        selected_match = None

    _module_header(
        '<svg viewBox="0 0 16 16"><circle cx="8" cy="8" r="5"/><circle cx="8" cy="8" r="1.6"/></svg>',
        "Operators",
    )
    st.markdown('<div class="sec">VISIBILITY</div>', unsafe_allow_html=True)
    show_humans    = st.checkbox("Show Humans", value=True)
    show_bots      = st.checkbox("Show Bots",   value=True)
    show_start_end = st.checkbox("Spawn/Extract Markers", value=True)

    _module_header(
        '<svg viewBox="0 0 16 16"><path d="M8 2l1.6 3.3L13 7l-3.4 1.7L8 12l-1.6-3.3L3 7l3.4-1.7z"/></svg>',
        "Intel",
    )
    st.markdown('<div class="sec">EVENT OVERLAYS</div>', unsafe_allow_html=True)
    event_toggles = {
        "Kill":          st.checkbox("PVP Kills 🔴",      value=True),
        "Killed":        st.checkbox("Deaths 💀",          value=True),
        "BotKill":       st.checkbox("Bot Kills 🟠",       value=True),
        "BotKilled":     st.checkbox("Killed by Bot 🟤",   value=True),
        "KilledByStorm": st.checkbox("Storm Deaths 💜",    value=True),
        "Loot":          st.checkbox("Loot ⭐",            value=True),
    }

    _module_header(
        '<svg viewBox="0 0 16 16"><rect x="2.5" y="2.5" width="11" height="11"/><path d="M5 8h6"/></svg>',
        "Thermals",
    )
    st.markdown('<div class="sec">HEAT PASSES</div>', unsafe_allow_html=True)
    show_kill_hm    = st.checkbox("Kill Zone Heat",    value=False)
    show_death_hm   = st.checkbox("Death Zone Heat",   value=False)
    show_traffic_hm = st.checkbox("Traffic Density",   value=False)
    show_loot_hm    = st.checkbox("Loot Zone Heat",    value=False)

    st.divider()
    _module_header(
        '<svg viewBox="0 0 16 16"><path d="M8 2l4.5 6L8 14 3.5 8z"/></svg>',
        "Legend",
    )
    st.markdown('<div class="sec">SYMBOL KEY</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="legend-item"><span class="ldot" style="background:#00FF88;border:2px solid #003300"></span>▲ Spawn</div>
<div class="legend-item"><span class="ldot" style="background:#FF2222;border:2px solid #330000;border-radius:2px"></span>■ Killed by human (human exit)</div>
<div class="legend-item"><span class="ldot" style="background:#CC5500;border-radius:50%"></span>● Killed by bot (human exit)</div>
<div class="legend-item"><span class="ldot" style="background:#9400D3;border-radius:2px"></span>◆ Killed by storm (human exit)</div>
<div class="legend-item"><span class="ldot" style="background:#6A7A8A;border-radius:2px"></span>Unknown exit (human)</div>
<div class="legend-item"><span class="ldot" style="background:#FF2222;border:2px solid #330000;border-radius:2px"></span>■ Bot exit</div>
<div class="legend-item"><span class="ldot" style="background:#00BFFF"></span>─ Human path</div>
<div class="legend-item"><span class="ldot" style="background:#888"></span>╌ Bot path</div>
<div class="legend-item"><span class="ldot" style="background:#FF3333;border-radius:2px"></span>✕ Kill</div>
<div class="legend-item"><span class="ldot" style="background:#8B0000;border-radius:2px"></span>⊗ Death (bot victim)</div>
<div class="legend-item"><span class="ldot" style="background:#FFD700;border-radius:2px"></span>★ Loot</div>
<div class="legend-item"><span class="ldot" style="background:#9400D3;border-radius:2px"></span>◆ Storm (events)</div>
""", unsafe_allow_html=True)


# ── MAIN ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">BLACK // PLAYER JOURNEY INTEL</div>', unsafe_allow_html=True)

# Empty state until all 3 selections made
ready = (
    selected_map not in ("— select —", None) and
    selected_date not in ("— select —", None) and
    selected_match is not None
)

if not ready:
    st.markdown("""
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:480px;
border:1px solid rgba(255,120,220,0.28);border-radius:10px;background:#161628;text-align:center;padding:40px;
background-image:repeating-linear-gradient(0deg,transparent,transparent 40px,rgba(255,120,220,0.02) 40px,rgba(255,120,220,0.02) 41px),
repeating-linear-gradient(90deg,transparent,transparent 40px,rgba(255,120,220,0.02) 40px,rgba(255,120,220,0.02) 41px);">
<div style="font-family:Orbitron,monospace;font-size:22px;font-weight:700;color:#ff83e0;
text-shadow:0 0 20px rgba(255,120,220,0.35);margin-bottom:24px;">SELECT MISSION TO DEPLOY</div>
<div style="font-size:13px;color:rgba(255,195,245,0.55);line-height:3;">
<div style="padding:8px 24px;border:1px solid rgba(255,120,220,0.22);border-radius:6px;margin:4px 0;">① SELECT MAP ZONE</div>
<div style="padding:8px 24px;border:1px solid rgba(255,120,220,0.22);border-radius:6px;margin:4px 0;">② SELECT DATE — ONLY DATES WITH THAT MAP SHOWN</div>
<div style="padding:8px 24px;border:1px solid rgba(255,120,220,0.22);border-radius:6px;margin:4px 0;">③ SELECT MATCH — OR "ALL MATCHES" FOR FULL DAY</div>
</div>
</div>""", unsafe_allow_html=True)
    st.stop()

# FILTER DATA
filtered_df = apply_filters(raw_df, selected_map, selected_date, selected_match)
filtered_df = add_pixel_coords(filtered_df, selected_map)
display_df  = safe_sample(filtered_df, n=5000)
map_df = filtered_df
if len(map_df) > 12000 and "ts_unix" in map_df.columns:
    ordered = map_df.sort_values("ts_unix")
    stride = max(1, len(ordered) // 12000)
    map_df = ordered.iloc[::stride].copy()
elif len(map_df) > 12000:
    map_df = safe_sample(map_df, n=12000)

if filtered_df.empty:
    st.warning("No data found. Try ALL MATCHES or a different date.")
    st.stop()

# STATS ROW (responsive HTML grid avoids Streamlit column clipping on small widths)
stats = [
    ("EVENTS", f"{len(filtered_df):,}"),
    ("HUMANS", str(count_players(filtered_df, "human"))),
    ("BOTS", str(count_players(filtered_df, "bot"))),
    ("KILLS", str(count_events(filtered_df, "Kill") + count_events(filtered_df, "BotKill"))),
    ("DEATHS", str(count_events(filtered_df, "Killed") + count_events(filtered_df, "BotKilled"))),
    ("STORM", str(count_events(filtered_df, "KilledByStorm"))),
]
stats_html = "".join(
    f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>'
    for label, value in stats
)
st.markdown(f'<div class="kpi-grid">{stats_html}</div>', unsafe_allow_html=True)

st.divider()

# ── TIMELINE SLIDER ───────────────────────────────────────────────────────────
st.markdown('<div class="panel-shell">', unsafe_allow_html=True)
st.markdown('<div class="subhead">MISSION TIMELINE // MANUAL SEEK</div>', unsafe_allow_html=True)

ts_min, ts_max = get_timeline_bounds(filtered_df)
elapsed_max = int(ts_max - ts_min)

if elapsed_max <= 0:
    st.caption("[ ALL EVENTS AT SAME TIMESTAMP ]")
    timeline_elapsed = 0
    timeline_pct = 1.0
else:
    scope_key = (selected_map, selected_date, selected_match, elapsed_max)
    if st.session_state.get("timeline_scope") != scope_key:
        st.session_state["timeline_scope"] = scope_key
        st.session_state["timeline_slider"] = elapsed_max
    timeline_elapsed = st.slider(
        "timeline",
        min_value=0,
        max_value=elapsed_max,
        value=int(st.session_state.get("timeline_slider", elapsed_max)),
        label_visibility="collapsed",
        key="timeline_slider",
    )
    timeline_elapsed = int(timeline_elapsed)
    pct   = int(timeline_elapsed / elapsed_max * 100)
    st.markdown(
        f'<div style="font-size:11px;color:rgba(200,255,245,0.90);font-family:Share Tech Mono,monospace;">'
        f'{_fmt_clock(timeline_elapsed)} / {_fmt_clock(elapsed_max)} &nbsp;|&nbsp; {pct}% ELAPSED'
        f'&nbsp;|&nbsp; DRAG TO SCRUB TIMELINE</div>',
        unsafe_allow_html=True,
    )
    timeline_pct = timeline_elapsed / elapsed_max

st.divider()

# ── PLAYER JOURNEY MAP ────────────────────────────────────────────────────────
st.markdown(f'<div class="subhead">PLAYER PATHS — {selected_map} — {selected_match}</div>', unsafe_allow_html=True)

fig = build_minimap_figure(
    df=map_df,
    map_name=selected_map,
    show_humans=show_humans,
    show_bots=show_bots,
    event_toggles=event_toggles,
    timeline_pct=timeline_pct,
    show_start_end=show_start_end,
)
st.plotly_chart(
    fig,
    use_container_width=True,
    key=f"minimap_{selected_map}_{selected_match}_{timeline_elapsed if elapsed_max > 0 else 'full'}",
)
st.markdown('</div>', unsafe_allow_html=True)

# ── HEATMAP SECTION ───────────────────────────────────────────────────────────
active_hm = []
if show_kill_hm:    active_hm.append(("kill",    "KILL ZONE"))
if show_death_hm:   active_hm.append(("death",   "DEATH ZONE"))
if show_traffic_hm: active_hm.append(("traffic", "TRAFFIC"))
if show_loot_hm:    active_hm.append(("loot",    "LOOT ZONE"))

if active_hm:
    st.divider()
    st.markdown('<div style="font-family:Orbitron,monospace;font-size:14px;color:#d7ff2f;letter-spacing:0.1em;margin-bottom:4px;">THERMAL ANALYSIS</div>', unsafe_allow_html=True)
    st.caption("Blue = low  →  Green = moderate  →  Yellow = high  →  Red = extreme activity")
    cols = st.columns(len(active_hm))
    for col,(htype,label) in zip(cols, active_hm):
        with col:
            st.plotly_chart(build_heatmap_figure(display_df, selected_map, htype), use_container_width=True)
else:
    st.divider()
    st.markdown('<div style="text-align:center;color:rgba(180,255,232,0.38);font-size:11px;letter-spacing:0.1em;padding:12px;">[ THERMAL SCANS OFFLINE — ENABLE IN SIDEBAR ]</div>', unsafe_allow_html=True)

with st.expander("[ HOW TO READ ]", expanded=False):
    st.markdown("""
- **▲ Green triangle** = spawn | **Human map exit** = killed by human, bot, storm, or unknown (see legend); **■** on bot paths = bot exit
- **Blue line** = human path | **Grey dashed** = bot path
- **Drag slider** left → rewind match, right → advance
- **Heatmaps** = full map image with colour density overlay (kill, death, traffic, loot). Enable in sidebar.
- **ALL MATCHES** = see full day of activity on one map
    """)

with st.expander("[ RAW TELEMETRY ]", expanded=False):
    st.dataframe(filtered_df.head(500), use_container_width=True, height=280)

st.markdown('<div style="font-size:10px;color:rgba(200,255,245,0.35);text-align:center;padding:8px;font-family:Share Tech Mono,monospace;">LILA BLACK // PLAYER JOURNEY VISUALIZATION</div>', unsafe_allow_html=True)
