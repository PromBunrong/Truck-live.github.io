# utils/time_utils.py
from datetime import datetime
import pandas as pd
import pytz
import numpy as np
from typing import Dict

from config.config import LOCAL_TZ

TZ = pytz.timezone(LOCAL_TZ)


def now_local():
    """
    Return timezone-aware current time in LOCAL_TZ.
    Use this instead of datetime.now() in all waiting calculations.
    """
    return datetime.now(TZ)


def _is_mostly_numeric(series: pd.Series, threshold: float = 0.5) -> bool:
    """Heuristic: are >threshold fraction of entries numeric-like?"""
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.notna().sum() / max(1, len(series)) > threshold


def normalize_timestamp_series(series: pd.Series) -> pd.Series:
    """
    Convert a Series of timestamps (strings / numeric / datetimes) into tz-aware datetimes in LOCAL_TZ.
    Handles:
      - ISO strings with timezone info (pandas with utc=True will parse those)
      - Naive strings -> interpreted as LOCAL_TZ
      - Excel/Sheets serial numbers (floats/ints) -> converted via origin '1899-12-30'
    Returns a Series of dtype datetime64[ns, tz] (or all NaT if parsing fails).
    """
    s = series.copy()

    # If data is already datetime dtype with tz info, convert to LOCAL_TZ
    if pd.api.types.is_datetime64tz_dtype(s.dtype):
        return s.dt.tz_convert(TZ)

    # If many numeric-like values, treat them as Excel/Sheets serial dates
    if _is_mostly_numeric(s):
        numeric = pd.to_numeric(s, errors="coerce")
        parsed = pd.to_datetime(numeric, unit="d", origin="1899-12-30", errors="coerce")
        parsed = parsed.dt.tz_localize(TZ)
        return parsed

    # First attempt: parse with utc=True to catch tz-aware strings (gives tz-aware UTC)
    parsed = pd.to_datetime(s, errors="coerce", utc=True)

    # For parsed NaT items, maybe they were naive strings -> parse and then localize
    mask_nat = parsed.isna()
    if mask_nat.any():
        parsed_naive = pd.to_datetime(s[mask_nat], errors="coerce")
        # localize naive datetimes to LOCAL_TZ (interpret values as LOCAL_TZ)
        parsed_naive = parsed_naive.dt.tz_localize(TZ)
        parsed.loc[mask_nat] = parsed_naive

    # Finally convert all to LOCAL_TZ (items parsed as UTC will be converted)
    parsed = parsed.dt.tz_convert(TZ)

    return parsed


def normalize_dfs_timestamps(dfs: Dict[str, pd.DataFrame], candidate_cols=None) -> Dict[str, pd.DataFrame]:
    """
    For each DataFrame in dict `dfs`, attempt to find timestamp-like columns and normalize them to tz-aware datetimes.
    Standard targets:
      - column named 'Timestamp'
      - columns containing 'time', 'date', 'arrival', 'ts' (case-insensitive)
    You can pass `candidate_cols` (list) to force specific names.
    Returns the modified dfs (in-place modified).
    """
    if candidate_cols is None:
        candidate_cols = []

    for name, df in dfs.items():
        if df is None or df.empty:
            continue
        # lower-case column map
        cols = list(df.columns)
        lower_map = {c: c.lower() for c in cols}
        # build list of candidates from heuristics
        to_check = set()

        # explicit candidate names
        for c in candidate_cols:
            if c in df.columns:
                to_check.add(c)

        # typical names
        for c_orig, c_low in lower_map.items():
            if c_low in ['timestamp', 'time', 'arrival', 'arrival_time', 'arrival_at', 'created_at', 'updated_at', 'date', 'datetime']:
                to_check.add(c_orig)
            # contains patterns
            if any(k in c_low for k in ['time', 'date', 'arrival', 'ts', 'at']):
                to_check.add(c_orig)

        # Normalize found columns
        for col in list(to_check):
            try:
                df[col] = normalize_timestamp_series(df[col])
            except Exception:
                # If normalization fails, attempt a safe fallback conversion
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce").dt.tz_localize(TZ)
                except Exception:
                    # give up silently and leave as-is
                    pass

    return dfs
