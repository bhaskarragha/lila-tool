"""coordinate_mapper.py - vectorized, no apply(), no KeyError"""

import pandas as pd

MAP_CONFIG = {
    "AmbroseValley": {"scale": 900,  "origin_x": -370, "origin_z": -473},
    "GrandRift":     {"scale": 581,  "origin_x": -290, "origin_z": -290},
    "Lockdown":      {"scale": 1000, "origin_x": -500, "origin_z": -500},
}
MINIMAP_SIZE = 1024


def add_pixel_coords(df: pd.DataFrame, map_name: str) -> pd.DataFrame:
    if "x" not in df.columns or "z" not in df.columns:
        df = df.copy()
        df["pixel_x"] = 0.0
        df["pixel_y"] = 0.0
        return df
    cfg = MAP_CONFIG.get(map_name, {"scale": 1000, "origin_x": -500, "origin_z": -500})
    df = df.copy()
    u = (df["x"] - cfg["origin_x"]) / cfg["scale"]
    v = (df["z"] - cfg["origin_z"]) / cfg["scale"]
    df["pixel_x"] = u * MINIMAP_SIZE
    df["pixel_y"] = (1 - v) * MINIMAP_SIZE
    return df
