import os, base64
from functools import lru_cache
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from coordinate_mapper import MAP_CONFIG

MINIMAP_SIZE = 1024
HUMAN_COLOR  = "#00BFFF"
BOT_COLOR    = "#D6D9E0"

EVENT_COLORS  = {
    "Kill":"#FF3333","Killed":"#8B0000","BotKill":"#FF6600",
    "BotKilled":"#6B0000","KilledByStorm":"#9400D3","Loot":"#FFD700",
}
EVENT_SYMBOLS = {
    "Kill":"x","Killed":"circle-x","BotKill":"x-open",
    "BotKilled":"circle-x-open","KilledByStorm":"diamond","Loot":"star",
}
EVENT_LABELS  = {
    "Kill":"PVP Kill","Killed":"Death","BotKill":"Bot Kill",
    "BotKilled":"Killed by Bot","KilledByStorm":"Storm Death","Loot":"Loot",
}
MINIMAP_FILES = {
    "AmbroseValley":"AmbroseValley_Minimap.png",
    "GrandRift":"GrandRift_Minimap.png",
    "Lockdown":"Lockdown_Minimap.jpg",
}
MOVE_EVENTS  = {"Position","BotPosition"}
KILL_EVENTS  = {"Kill","BotKill"}
DEATH_EVENTS = {"Killed","BotKilled","KilledByStorm"}
LOOT_EVENTS  = {"Loot"}

MARKER_STYLE = {
    "human_spawn": dict(
        symbol="pentagon",
        size=15,
        color="#F15BB5",
        line=dict(width=2, color="#4A1637"),
        label="Human spawn",
        hover="Human spawn",
    ),
    "bot_spawn": dict(
        symbol="hexagon",
        size=15,
        color="#00F5D4",
        line=dict(width=2, color="#0F3D38"),
        label="Bot spawn",
        hover="Bot spawn",
    ),
    "human_death": dict(
        symbol="hourglass",
        size=14,
        color="#FF8E72",
        line=dict(width=2, color="#5B2618"),
        label="Human death",
        hover="Human death",
    ),
    "bot_death": dict(
        symbol="hourglass",
        size=14,
        color="#4CD964",
        line=dict(width=2, color="#174B24"),
        label="Bot death",
        hover="Bot death",
    ),
    "storm_death": dict(
        symbol="bowtie",
        size=15,
        color="#A855F7",
        line=dict(width=2, color="#3C1670"),
        label="Storm death",
        hover="Storm death",
    ),
    "unknown_exit": dict(
        symbol="hexagon2",
        size=12,
        color="#6A7A8A",
        line=dict(width=2, color="#C8D8E8"),
        label="Unknown exit",
        hover="Unknown exit",
    ),
}


def _resolve_marker_xy(event_row: pd.Series, move_rows: pd.DataFrame):
    px, py = event_row.get("pixel_x"), event_row.get("pixel_y")
    if pd.notna(px) and pd.notna(py):
        return float(px), float(py)

    ts_event = event_row["ts_unix"] if "ts_unix" in event_row.index else None
    if ts_event is not None and "ts_unix" in move_rows.columns and not move_rows.empty:
        before = move_rows[move_rows["ts_unix"] <= ts_event]
        if not before.empty:
            return float(before.iloc[-1]["pixel_x"]), float(before.iloc[-1]["pixel_y"])
    if not move_rows.empty:
        return float(move_rows.iloc[-1]["pixel_x"]), float(move_rows.iloc[-1]["pixel_y"])
    return None


def _death_hover_text(player_type: str, event_name: str) -> str:
    if player_type == "human":
        return {
            "Killed": "Human death - killed by player",
            "BotKilled": "Human death - killed by bot",
        }.get(event_name, "Human death")
    return {
        "Killed": "Bot death - killed by player",
        "BotKilled": "Bot death",
    }.get(event_name, "Bot death")


def _storm_hover_text(player_type: str) -> str:
    return "Storm death" if player_type == "human" else "Storm death - bot"


def _collect_endpoint_markers(df: pd.DataFrame, timeline_pct: float) -> dict:
    out = {"human_death": [], "bot_death": [], "storm_death": [], "unknown_exit": []}
    if df.empty or "user_id" not in df.columns or "event" not in df.columns:
        return out

    at_timeline_end = timeline_pct >= 0.999
    for _, grp in df.groupby("user_id", sort=False):
        ptype = grp["player_type"].iloc[0] if "player_type" in grp.columns else "unknown"
        if ptype not in {"human", "bot"}:
            continue

        g = grp.sort_values("ts_unix") if "ts_unix" in grp.columns else grp
        moves = g[g["event"].isin(MOVE_EVENTS)]
        deaths = g[g["event"].isin(DEATH_EVENTS)]

        if deaths.empty:
            if ptype != "human" or not at_timeline_end or moves.empty:
                continue
            xy = _resolve_marker_xy(moves.iloc[-1], moves)
            if xy is not None:
                out["unknown_exit"].append(xy)
            continue

        death = deaths.iloc[-1]
        evt = str(death["event"])
        if evt not in DEATH_EVENTS:
            continue
        xy = _resolve_marker_xy(death, moves)
        if xy is None:
            continue

        if evt == "KilledByStorm":
            out["storm_death"].append((xy[0], xy[1], ptype))
            continue

        bucket = "human_death" if ptype == "human" else "bot_death"
        out[bucket].append((xy[0], xy[1], evt, ptype))
    return out


def _add_endpoint_traces(fig, buckets: dict, event_toggles: dict, show_start_end: bool) -> None:
    if not show_start_end:
        return

    for bucket in ("human_death", "bot_death", "storm_death"):
        pts = buckets[bucket]
        if not pts:
            continue
        cfg = MARKER_STYLE[bucket]
        xs, ys, hovers = [], [], []
        for pt in pts:
            if bucket == "storm_death":
                x, y, player_type = pt
                if not event_toggles.get("KilledByStorm", True):
                    continue
                xs.append(x)
                ys.append(y)
                hovers.append(_storm_hover_text(player_type))
                continue

            x, y, evt, player_type = pt
            if not event_toggles.get(evt, True):
                continue
            xs.append(x)
            ys.append(y)
            hovers.append(_death_hover_text(player_type, evt))
        if not xs:
            continue
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers",
                marker=dict(
                    symbol=cfg["symbol"],
                    size=cfg["size"],
                    color=cfg["color"],
                    line=cfg["line"],
                ),
                showlegend=False,
                hovertemplate="%{text}<extra></extra>",
                text=hovers,
            )
        )

    unknown_pts = buckets["unknown_exit"]
    if unknown_pts:
        cfg = MARKER_STYLE["unknown_exit"]
        xs, ys = zip(*unknown_pts)
        fig.add_trace(
            go.Scatter(
                x=list(xs),
                y=list(ys),
                mode="markers",
                marker=dict(
                    symbol=cfg["symbol"],
                    size=cfg["size"],
                    color=cfg["color"],
                    line=cfg["line"],
                ),
                showlegend=False,
                hovertemplate=f"{cfg['hover']}<extra></extra>",
            )
        )


def _timeline_seconds(series: pd.Series) -> pd.Series:
    s = series.copy()
    if pd.api.types.is_datetime64_any_dtype(s):
        return s.view("int64").div(10**9)
    return pd.to_numeric(s, errors="coerce")


def _smooth_heatmap(grid: np.ndarray, passes: int = 2) -> np.ndarray:
    if grid.size == 0:
        return grid
    g = np.nan_to_num(grid, nan=0.0).astype(float)
    for _ in range(max(1, passes)):
        p = np.pad(g, ((1, 1), (1, 1)), mode="edge")
        g = (
            p[1:-1, 1:-1] * 0.40
            + (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) * 0.12
            + (p[:-2, :-2] + p[:-2, 2:] + p[2:, :-2] + p[2:, 2:]) * 0.03
        )
    g[g <= 0] = np.nan
    return g


@lru_cache(maxsize=8)
def _load_bg(map_name):
    assets = os.path.join(os.path.dirname(__file__), "assets", "minimaps")
    fname  = MINIMAP_FILES.get(map_name, f"{map_name}_Minimap.png")
    path   = os.path.join(assets, fname)
    if not os.path.exists(path):
        return None, None, fname
    ext  = fname.rsplit(".",1)[-1].lower()
    mime = "image/jpeg" if ext in ("jpg","jpeg") else "image/png"
    with open(path,"rb") as f:
        return base64.b64encode(f.read()).decode(), mime, fname


def _add_coord_mapper_layer(fig, map_name: str) -> None:
    """Invisible heatmap so hovering empty map shows pixel + world coords (matches coordinate_mapper)."""
    cfg = MAP_CONFIG.get(map_name, {"scale": 1000, "origin_x": -500, "origin_z": -500})
    scale, ox, oz = cfg["scale"], cfg["origin_x"], cfg["origin_z"]
    n = 80
    edges = np.linspace(0, MINIMAP_SIZE, n + 1)
    cx = (edges[:-1] + edges[1:]) / 2.0
    cy = (edges[:-1] + edges[1:]) / 2.0
    px, py = np.meshgrid(cx, cy)
    u = px / MINIMAP_SIZE
    v = 1.0 - (py / MINIMAP_SIZE)
    world_x = u * scale + ox
    world_z = v * scale + oz
    customdata = np.stack([world_x, world_z], axis=-1)
    z = np.zeros((n, n))
    fig.add_trace(
        go.Heatmap(
            x=cx,
            y=cy,
            z=z,
            customdata=customdata,
            opacity=0,
            showscale=False,
            showlegend=False,
            name="",
            hovertemplate=(
                "<b>COORD MAPPER</b><br>"
                "PIXEL &nbsp; x=%{x:.0f} &nbsp; y=%{y:.0f}<br>"
                "WORLD &nbsp; x=%{customdata[0]:.1f} &nbsp; z=%{customdata[1]:.1f}"
                "<extra></extra>"
            ),
            colorscale=[[0.0, "rgba(0,0,0,0)"], [1.0, "rgba(0,0,0,0)"]],
            zmin=0,
            zmax=1,
            zsmooth=False,
        )
    )


def _add_bg_image(fig, map_name, opacity=0.85):
    enc, mime, fname = _load_bg(map_name)
    if enc:
        fig.add_layout_image(dict(
            source=f"data:{mime};base64,{enc}",
            xref="x", yref="y", x=0, y=0,
            sizex=MINIMAP_SIZE, sizey=MINIMAP_SIZE,
            sizing="stretch", opacity=opacity, layer="below",
        ))
    else:
        fig.add_shape(type="rect", x0=0, y0=0, x1=MINIMAP_SIZE, y1=MINIMAP_SIZE,
                      fillcolor="#1e3a5f", line=dict(color="#4a90d9", width=2))
        fig.add_annotation(x=MINIMAP_SIZE/2, y=MINIMAP_SIZE/2,
                           text=f"Add {fname} to assets/minimaps/",
                           font=dict(size=13, color="#aaa"), showarrow=False)


def _base_layout(height=760):
    return dict(
        xaxis=dict(range=[0,MINIMAP_SIZE], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[MINIMAP_SIZE,0], showgrid=False, zeroline=False, visible=False,
                   scaleanchor="x", scaleratio=1),
        plot_bgcolor="#030508",
        paper_bgcolor="#030508",
        font=dict(color="#c8ffc8"),
        margin=dict(l=0, r=120, t=10, b=0),
        height=height,
        legend=dict(bgcolor="rgba(0,0,0,0.7)", bordercolor="#00ff64",
                    borderwidth=1, font=dict(size=11, color="#c8ffc8"), x=1.01, y=1),
    )


def build_minimap_figure(df, map_name, show_humans=True, show_bots=True,
                          event_toggles=None, timeline_pct=1.0, show_start_end=True):
    if event_toggles is None:
        event_toggles = {e: True for e in EVENT_COLORS}

    fig = go.Figure()

    # Apply timeline cut — THIS IS THE SLIDER LOGIC
    if "ts_unix" in df.columns and timeline_pct < 1.0:
        ts = _timeline_seconds(df["ts_unix"])
        ts_valid = ts.dropna()
        if not ts_valid.empty:
            ts_min = ts_valid.min()
            ts_max = ts_valid.max()
            if ts_max > ts_min:
                cutoff = ts_min + (ts_max - ts_min) * timeline_pct
                mask = ts <= cutoff
                df = df[mask.fillna(False)].copy()

    _add_bg_image(fig, map_name, opacity=0.88)

    # Player paths
    move_df = df[df["event"].isin(MOVE_EVENTS)] if "event" in df.columns else df
    if "ts_unix" in move_df.columns and "user_id" in move_df.columns and not move_df.empty:
        move_df = move_df.sort_values(["user_id", "ts_unix"])
    if "user_id" in move_df.columns and not move_df.empty:
        human_x, human_y = [], []
        bot_x, bot_y = [], []
        human_start_x, human_start_y = [], []
        bot_start_x, bot_start_y = [], []

        for _, grp in move_df.groupby("user_id", sort=False):
            ptype = grp["player_type"].iloc[0] if "player_type" in grp.columns else "unknown"
            if ptype == "human":
                if not show_humans:
                    continue
                human_x.extend(grp["pixel_x"].tolist())
                human_x.append(None)
                human_y.extend(grp["pixel_y"].tolist())
                human_y.append(None)
            elif ptype == "bot":
                if not show_bots:
                    continue
                bot_x.extend(grp["pixel_x"].tolist())
                bot_x.append(None)
                bot_y.extend(grp["pixel_y"].tolist())
                bot_y.append(None)
            else:
                continue

            if show_start_end and len(grp) >= 1:
                if ptype == "human":
                    human_start_x.append(grp["pixel_x"].iloc[0])
                    human_start_y.append(grp["pixel_y"].iloc[0])
                elif ptype == "bot":
                    bot_start_x.append(grp["pixel_x"].iloc[0])
                    bot_start_y.append(grp["pixel_y"].iloc[0])

        if human_x:
            # SVG Scatter (not GL) so the coord-mapper heatmap beneath receives hovers on empty map.
            fig.add_trace(go.Scatter(
                x=human_x, y=human_y, mode="lines",
                line=dict(color=HUMAN_COLOR, width=2),
                name="Human", legendgroup="human", showlegend=True,
                opacity=0.8, hoverinfo="skip",
            ))
        if bot_x:
            # Keep bot paths dashed for readability (single SVG trace).
            fig.add_trace(go.Scatter(
                x=bot_x, y=bot_y, mode="lines",
                line=dict(color=BOT_COLOR, width=1.8, dash="dash"),
                name="Bot", legendgroup="bot", showlegend=True,
                opacity=0.95, hoverinfo="skip",
            ))
        if show_start_end and human_start_x:
            fig.add_trace(go.Scatter(
                x=human_start_x, y=human_start_y, mode="markers",
                marker=dict(
                    symbol=MARKER_STYLE["human_spawn"]["symbol"],
                    size=MARKER_STYLE["human_spawn"]["size"],
                    color=MARKER_STYLE["human_spawn"]["color"],
                    line=MARKER_STYLE["human_spawn"]["line"],
                ),
                showlegend=False, hoverinfo="skip",
            ))
        if show_start_end and bot_start_x:
            fig.add_trace(go.Scatter(
                x=bot_start_x, y=bot_start_y, mode="markers",
                marker=dict(
                    symbol=MARKER_STYLE["bot_spawn"]["symbol"],
                    size=MARKER_STYLE["bot_spawn"]["size"],
                    color=MARKER_STYLE["bot_spawn"]["color"],
                    line=MARKER_STYLE["bot_spawn"]["line"],
                ),
                showlegend=False, hoverinfo="skip",
            ))

    # Above paths (still below event markers) so mapper hovers work on lines too.
    _add_coord_mapper_layer(fig, map_name)

    # Legend for path-state markers
    if show_start_end:
        for marker_key in ("human_spawn", "bot_spawn", "human_death", "bot_death", "storm_death", "unknown_exit"):
            cfg = MARKER_STYLE[marker_key]
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode="markers",
                marker=dict(
                    symbol=cfg["symbol"],
                    size=cfg["size"],
                    color=cfg["color"],
                    line=cfg["line"],
                ),
                name=cfg["label"],
                showlegend=True, hoverinfo="skip",
            ))

    # Event markers (death rows are rendered as journey-end markers instead)
    action_df = df[~df["event"].isin(MOVE_EVENTS)] if "event" in df.columns else pd.DataFrame()
    for etype, color in EVENT_COLORS.items():
        if etype in DEATH_EVENTS or not event_toggles.get(etype, True):
            continue
        sub = action_df[action_df["event"] == etype] if not action_df.empty else pd.DataFrame()
        if sub.empty: continue
        fig.add_trace(go.Scatter(
            x=sub["pixel_x"], y=sub["pixel_y"], mode="markers",
            marker=dict(symbol=EVENT_SYMBOLS[etype], color=color, size=11,
                        line=dict(width=1.5, color="#000000")),
            name=EVENT_LABELS[etype], legendgroup=f"ev_{etype}",
            showlegend=True,
            hovertemplate=f"<b>{etype}</b><extra></extra>",
        ))

    endpoint_buckets = _collect_endpoint_markers(df, timeline_pct)
    _add_endpoint_traces(fig, endpoint_buckets, event_toggles, show_start_end)

    layout = _base_layout(760)
    layout["margin"] = dict(l=0, r=120, t=52, b=0)
    layout["hovermode"] = "closest"
    layout["hoverlabel"] = dict(
        bgcolor="rgba(12,16,32,0.94)",
        bordercolor="rgba(114,255,216,0.55)",
        font=dict(size=11, color="#e8fff8", family="Share Tech Mono, monospace"),
    )
    layout["annotations"] = [
        dict(
            text="⌖ COORD MAPPER - hover map",
            xref="paper",
            yref="paper",
            x=1.0,
            y=1.02,
            xanchor="right",
            yanchor="bottom",
            showarrow=False,
            font=dict(size=11, color="#72ffd8", family="Share Tech Mono, monospace"),
        )
    ]
    fig.update_layout(**layout)
    fig.update_xaxes(
        showspikes=True,
        spikecolor="rgba(114,255,216,0.55)",
        spikesnap="cursor",
        spikemode="across",
        spikethickness=1,
    )
    fig.update_yaxes(
        showspikes=True,
        spikecolor="rgba(114,255,216,0.55)",
        spikesnap="cursor",
        spikemode="across",
        spikethickness=1,
    )
    return fig


def build_heatmap_figure(df, map_name, heatmap_type="kill"):
    """Full map image + colour density overlay — like a football heatmap."""
    if heatmap_type == "kill":
        subset = df[df["event"].isin(KILL_EVENTS)] if "event" in df.columns else df
        colorscale = [
            [0.00, "rgba(0,0,0,0)"],
            [0.10, "rgba(0,190,255,0.55)"],
            [0.30, "rgba(0,255,170,0.70)"],
            [0.55, "rgba(210,255,0,0.78)"],
            [0.75, "rgba(255,165,0,0.86)"],
            [0.92, "rgba(255,60,0,0.92)"],
            [1.00, "rgba(255,0,120,0.98)"],
        ]
        title = "KILL ZONE THERMAL"
    elif heatmap_type == "death":
        subset = df[df["event"].isin(DEATH_EVENTS)] if "event" in df.columns else df
        colorscale = [
            [0.00, "rgba(0,0,0,0)"],
            [0.12, "rgba(0,120,255,0.52)"],
            [0.32, "rgba(120,0,255,0.68)"],
            [0.55, "rgba(210,0,200,0.80)"],
            [0.75, "rgba(255,0,120,0.90)"],
            [1.00, "rgba(255,40,40,0.98)"],
        ]
        title = "DEATH ZONE THERMAL"
    elif heatmap_type == "loot":
        subset = df[df["event"].isin(LOOT_EVENTS)] if "event" in df.columns else df
        if map_name == "Lockdown":
            colorscale = [
                [0.00, "rgba(0,0,0,0)"],
                [0.12, "rgba(255,190,0,0.24)"],
                [0.30, "rgba(255,220,0,0.46)"],
                [0.52, "rgba(255,235,80,0.76)"],
                [0.74, "rgba(255,190,0,0.90)"],
                [1.00, "rgba(255,100,0,0.96)"],
            ]
        else:
            colorscale = [
                [0.00, "rgba(0,0,0,0)"],
                [0.15, "rgba(0,150,190,0.34)"],
                [0.35, "rgba(0,255,210,0.58)"],
                [0.55, "rgba(255,215,0,0.78)"],
                [0.75, "rgba(255,180,0,0.88)"],
                [1.00, "rgba(255,100,0,0.96)"],
            ]
        title = "LOOT ZONE THERMAL"
    else:
        subset = df[df["event"].isin(MOVE_EVENTS)] if "event" in df.columns else df
        colorscale = [
            [0.00, "rgba(0,0,0,0)"],
            [0.10, "rgba(0,110,255,0.50)"],
            [0.30, "rgba(0,220,255,0.68)"],
            [0.52, "rgba(0,255,170,0.78)"],
            [0.75, "rgba(170,255,0,0.88)"],
            [1.00, "rgba(255,210,0,0.96)"],
        ]
        title = "TRAFFIC DENSITY"

    fig = go.Figure()
    # Keep map readable while still showing activity hotspots.
    _add_bg_image(fig, map_name, opacity=0.66)

    min_pts = 1 if heatmap_type == "loot" else 3
    if not subset.empty and "pixel_x" in subset.columns and len(subset) >= min_pts:
        bins = 90 if heatmap_type in {"kill", "death", "loot"} else 60
        x = subset["pixel_x"].values
        y = subset["pixel_y"].values
        h, xedges, yedges = np.histogram2d(
            x, y, bins=bins,
            range=[[0, MINIMAP_SIZE], [0, MINIMAP_SIZE]]
        )
        h = h.T
        if heatmap_type in {"kill", "death", "loot"}:
            h = _smooth_heatmap(h, passes=3)
        else:
            h = np.where(h == 0, np.nan, h)
        xc = (xedges[:-1] + xedges[1:]) / 2
        yc = (yedges[:-1] + yedges[1:]) / 2

        # colorbar with NO titlefont — uses title dict instead
        fig.add_trace(go.Heatmap(
            z=h, x=xc, y=yc,
            colorscale=colorscale,
            opacity=0.58 if heatmap_type == "loot" else (0.60 if heatmap_type in {"kill", "death"} else 0.68),
            showscale=True,
            zsmooth="best",
            colorbar=dict(
                title=dict(text="HEAT"),
                tickfont=dict(color="#00ff64", size=10),
                tickvals=[np.nanmin(h), np.nanmax(h)] if np.isfinite(np.nanmin(h)) and np.isfinite(np.nanmax(h)) else None,
                ticktext=["LOW", "HIGH"],
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor="#00ff64",
                borderwidth=1,
            ),
        ))
    else:
        fig.add_annotation(x=MINIMAP_SIZE/2, y=MINIMAP_SIZE/2,
                           text="NO DATA FOR THIS HEATMAP",
                           font=dict(size=16, color="#00ff64"), showarrow=False)

    layout = _base_layout(480)
    layout["margin"] = dict(l=0, r=60, t=40, b=0)
    layout["title"]  = dict(text=title, font=dict(size=13, color="#00ff64",
                             family="Orbitron, monospace"))
    fig.update_layout(**layout)
    return fig
