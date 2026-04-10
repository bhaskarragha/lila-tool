"""utils.py"""
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

def count_events(df, event_type):
    if "event" not in df.columns: return 0
    return int((df["event"] == event_type).sum())

def count_players(df, player_type):
    if "player_type" not in df.columns or "user_id" not in df.columns: return 0
    return int(df[df["player_type"] == player_type]["user_id"].nunique())

def get_timeline_bounds(df):
    if "ts_unix" not in df.columns or df.empty:
        return 0, 100
    series = df["ts_unix"].dropna()
    if series.empty:
        return 0, 100
    if is_datetime64_any_dtype(series):
        min_v = series.min().timestamp()
        max_v = series.max().timestamp()
        return int(min_v), int(max_v)
    return int(float(series.min())), int(float(series.max()))

def safe_sample(df, n=5000):
    return df.sample(n=n, random_state=42) if len(df) > n else df
