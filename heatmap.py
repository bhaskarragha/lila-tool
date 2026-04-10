"""
heatmap.py
----------
Kill, death, and traffic heatmaps.

Real event names:
  Kills:  'Kill', 'BotKill'
  Deaths: 'Killed', 'BotKilled', 'KilledByStorm'
  Traffic: all 'Position' and 'BotPosition' rows
"""

import plotly.graph_objects as go
import pandas as pd

MINIMAP_SIZE = 1024

KILL_EVENTS   = {"Kill", "BotKill"}
DEATH_EVENTS  = {"Killed", "BotKilled", "KilledByStorm"}
MOVE_EVENTS   = {"Position", "BotPosition"}


def build_kill_heatmap(df: pd.DataFrame) -> go.Figure:
    subset = df[df["event"].isin(KILL_EVENTS)] if "event" in df.columns else pd.DataFrame()
    return _density(subset, "🔴 Kill Heatmap", "Reds")


def build_death_heatmap(df: pd.DataFrame) -> go.Figure:
    subset = df[df["event"].isin(DEATH_EVENTS)] if "event" in df.columns else pd.DataFrame()
    return _density(subset, "💀 Death Heatmap", "YlOrRd")


def build_traffic_heatmap(df: pd.DataFrame) -> go.Figure:
    subset = df[df["event"].isin(MOVE_EVENTS)] if "event" in df.columns else df
    return _density(subset, "🚶 Traffic Heatmap", "Blues")


def _density(df: pd.DataFrame, title: str, colorscale: str) -> go.Figure:
    fig = go.Figure()

    if df.empty or "pixel_x" not in df.columns:
        fig.add_annotation(x=MINIMAP_SIZE/2, y=MINIMAP_SIZE/2,
                           text="No data for this heatmap.<br>Try adjusting filters.",
                           font=dict(size=13, color="#aaaaaa"), showarrow=False)
    else:
        fig.add_trace(go.Histogram2dContour(
            x=df["pixel_x"], y=df["pixel_y"],
            colorscale=colorscale,
            ncontours=20,
            opacity=0.8,
            contours=dict(showlines=False),
            showscale=True,
            hovertemplate="Density: %{z}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=df["pixel_x"], y=df["pixel_y"],
            mode="markers",
            marker=dict(size=2, opacity=0.15, color="#ffffff"),
            showlegend=False, hoverinfo="skip",
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#E0E0E0")),
        xaxis=dict(range=[0, MINIMAP_SIZE], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[MINIMAP_SIZE, 0], showgrid=False, zeroline=False, visible=False,
                   scaleanchor="x", scaleratio=1),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#0f0f23",
        font=dict(color="#E0E0E0"),
        margin=dict(l=0, r=0, t=40, b=0),
        height=480,
    )
    return fig
