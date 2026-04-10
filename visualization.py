import os, base64
from functools import lru_cache
import numpy as np
import pandas as pd
import plotly.graph_objects as go

MINIMAP_SIZE = 1024
HUMAN_COLOR  = "#00BFFF"
BOT_COLOR    = "#888888"

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
        start_x, start_y, end_x, end_y = [], [], [], []

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
                start_x.append(grp["pixel_x"].iloc[0])
                start_y.append(grp["pixel_y"].iloc[0])
                if len(grp) > 1:
                    end_x.append(grp["pixel_x"].iloc[-1])
                    end_y.append(grp["pixel_y"].iloc[-1])

        if human_x:
            fig.add_trace(go.Scattergl(
                x=human_x, y=human_y, mode="lines",
                line=dict(color=HUMAN_COLOR, width=2),
                name="Human", legendgroup="human", showlegend=True,
                opacity=0.8, hoverinfo="skip",
            ))
        if bot_x:
            # Keep bot paths dashed for readability (single SVG trace).
            fig.add_trace(go.Scatter(
                x=bot_x, y=bot_y, mode="lines",
                line=dict(color=BOT_COLOR, width=1, dash="dash"),
                name="Bot", legendgroup="bot", showlegend=True,
                opacity=0.8, hoverinfo="skip",
            ))
        if show_start_end and start_x:
            fig.add_trace(go.Scattergl(
                x=start_x, y=start_y, mode="markers",
                marker=dict(symbol="triangle-up", size=14, color="#00FF88",
                            line=dict(width=2, color="#003300")),
                showlegend=False, hoverinfo="skip",
            ))
        if show_start_end and end_x:
            fig.add_trace(go.Scattergl(
                x=end_x, y=end_y, mode="markers",
                marker=dict(symbol="square", size=12, color="#FF2222",
                            line=dict(width=2, color="#330000")),
                showlegend=False, hoverinfo="skip",
            ))

    # Legend entries for spawn/end
    if show_start_end:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
            marker=dict(symbol="triangle-up", size=12, color="#00FF88"),
            name="▲ Spawn", showlegend=True))
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
            marker=dict(symbol="square", size=11, color="#FF2222"),
            name="■ End", showlegend=True))

    # Event markers
    action_df = df[~df["event"].isin(MOVE_EVENTS)] if "event" in df.columns else pd.DataFrame()
    for etype, color in EVENT_COLORS.items():
        if not event_toggles.get(etype, True): continue
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

    fig.update_layout(**_base_layout(760))
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

    if not subset.empty and "pixel_x" in subset.columns and len(subset) >= 3:
        bins = 90 if heatmap_type in {"kill", "death"} else 60
        x = subset["pixel_x"].values
        y = subset["pixel_y"].values
        h, xedges, yedges = np.histogram2d(
            x, y, bins=bins,
            range=[[0, MINIMAP_SIZE], [0, MINIMAP_SIZE]]
        )
        h = h.T
        if heatmap_type in {"kill", "death"}:
            h = _smooth_heatmap(h, passes=3)
        else:
            h = np.where(h == 0, np.nan, h)
        xc = (xedges[:-1] + xedges[1:]) / 2
        yc = (yedges[:-1] + yedges[1:]) / 2

        # colorbar with NO titlefont — uses title dict instead
        fig.add_trace(go.Heatmap(
            z=h, x=xc, y=yc,
            colorscale=colorscale,
            opacity=0.60 if heatmap_type in {"kill", "death"} else 0.68,
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
