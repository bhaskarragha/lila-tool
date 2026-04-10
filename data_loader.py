import os, re
import pandas as pd
import pyarrow.parquet as pq

DATA_DIR = os.path.join(os.path.dirname(__file__), "player_data")
DATE_FOLDERS = ["February_10","February_11","February_12","February_13","February_14"]
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)

def load_folder(folder_name, max_files=150):
    path = os.path.join(DATA_DIR, folder_name)
    if not os.path.exists(path): return pd.DataFrame()
    frames = []
    for fn in list(os.listdir(path))[:max_files]:
        try:
            df = pq.read_table(os.path.join(path, fn)).to_pandas()
            df["date_folder"] = folder_name
            frames.append(df)
        except: continue
    if not frames: return pd.DataFrame()
    return _clean(pd.concat(frames, ignore_index=True))

def load_all_data(max_files_per_folder=150):
    frames = []
    for f in DATE_FOLDERS:
        df = load_folder(f, max_files_per_folder)
        if not df.empty: frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def _clean(df):
    if "event" in df.columns:
        df["event"] = df["event"].apply(lambda v: v.decode("utf-8") if isinstance(v,(bytes,bytearray)) else str(v))
    if "user_id" in df.columns:
        def classify(uid):
            s = str(uid).strip()
            if _UUID_RE.match(s): return "human"
            if s.isdigit(): return "bot"
            return "unknown"
        df["player_type"] = df["user_id"].apply(classify)
    else:
        df["player_type"] = "unknown"
    if "ts" in df.columns:
        ts_numeric = pd.to_numeric(df["ts"], errors="coerce")
        if ts_numeric.notna().any():
            # Telemetry `ts` is elapsed milliseconds in match.
            # Keep a stable elapsed-seconds axis for timeline replay.
            df["ts_unix"] = ts_numeric.div(1000.0)
            df["ts"] = pd.to_datetime(ts_numeric, unit="ms", errors="coerce")
        else:
            df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
            df["ts_unix"] = df["ts"].view("int64").div(10**9)
    if "match_id" in df.columns:
        df["match_id"] = df["match_id"].str.replace(r"\.nakama-0$","",regex=True)
    return df

def get_maps(df):
    if "map_id" not in df.columns: return []
    return sorted(df["map_id"].dropna().unique().tolist())

def get_dates_for_map(df, map_name):
    if "map_id" not in df.columns or "date_folder" not in df.columns: return []
    return sorted(df[df["map_id"]==map_name]["date_folder"].dropna().unique().tolist())

def get_matches_for_map_date(df, map_name, date_folder):
    if "map_id" not in df.columns or "match_id" not in df.columns: return []
    mask = (df["map_id"]==map_name) & (df["date_folder"]==date_folder)
    return sorted(df[mask]["match_id"].dropna().unique().tolist())

def apply_filters(df, selected_map, selected_date, selected_match):
    SKIP = {"All","ALL MATCHES","— SELECT MAP —","— SELECT DATE —","— SELECT DATE FIRST —","— SELECT MAP FIRST —",None,""}
    if selected_map not in SKIP and "map_id" in df.columns:
        df = df[df["map_id"]==selected_map]
    if selected_date not in SKIP and "date_folder" in df.columns:
        df = df[df["date_folder"]==selected_date]
    if selected_match not in SKIP and "match_id" in df.columns:
        df = df[df["match_id"]==selected_match]
    return df
