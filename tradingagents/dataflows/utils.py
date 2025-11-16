import os
import json
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime
from typing import Annotated, Optional, Dict, Any

SavePathType = Annotated[str, "File path to save data. If None, data is not saved."]

def save_output(data: pd.DataFrame, tag: str, save_path: SavePathType = None) -> None:
    if save_path:
        data.to_csv(save_path)
        print(f"{tag} saved to {save_path}")


def get_current_date():
    return date.today().strftime("%Y-%m-%d")


def decorate_all_methods(decorator):
    def class_decorator(cls):
        for attr_name, attr_value in cls.__dict__.items():
            if callable(attr_value):
                setattr(cls, attr_name, decorator(attr_value))
        return cls

    return class_decorator


def get_next_weekday(date):

    if not isinstance(date, datetime):
        date = datetime.strptime(date, "%Y-%m-%d")

    if date.weekday() >= 5:
        days_to_add = 7 - date.weekday()
        next_weekday = date + timedelta(days=days_to_add)
        return next_weekday
    else:
        return date


def _canonicalize_column(name: str) -> str:
    cleaned = name.strip().lower().replace(" ", "_")
    mapping = {
        "adj_close": "adjusted_close",
        "adjclose": "adjusted_close",
        "close_adj": "adjusted_close",
    }
    return mapping.get(cleaned, cleaned)


def _json_default(value: Any):
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def build_price_payload(
    symbol: str,
    start_date: str,
    end_date: str,
    source: str,
    df: pd.DataFrame,
    date_column: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Serialize price history DataFrame to a normalized JSON payload."""
    symbol = (symbol or "").upper()
    if not symbol:
        raise ValueError("symbol is required for price payloads")

    normalized = df.copy()
    if date_column and date_column in normalized.columns:
        normalized = normalized.rename(columns={date_column: "date"})
    elif "date" in normalized.columns:
        pass
    elif "Date" in normalized.columns:
        normalized = normalized.rename(columns={"Date": "date"})
    else:
        normalized = normalized.reset_index().rename(columns={"index": "date"})

    if "date" not in normalized.columns:
        raise ValueError("Price dataframe missing a date column")

    normalized["date"] = pd.to_datetime(normalized["date"]).dt.strftime("%Y-%m-%d")
    rename_map = {col: _canonicalize_column(col) for col in normalized.columns}
    normalized = normalized.rename(columns=rename_map)
    normalized = normalized.sort_values("date")

    payload: Dict[str, Any] = {
        "symbol": symbol,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "source": source,
        "records": normalized.to_dict(orient="records"),
    }
    if metadata:
        payload["meta"] = metadata
    return json.dumps(payload, default=_json_default)
