"""WRDS institutional data engine.

This module wraps the official `wrds` Python client so agents can
authenticate, discover metadata, and execute resource-friendly queries
against the WRDS Postgres clusters. All helpers default to conservative
row limits to avoid transferring massive datasets accidentally – limits
can be overridden by setting ``WRDS_DEFAULT_LIMIT`` or
``WRDS_DEFAULT_TABLE_OBS`` in the environment.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import wrds


_CONNECTION: Optional[wrds.Connection] = None
_CONNECTION_LOCK = Lock()
_LIMIT_PATTERN = re.compile(r"\blimit\b", flags=re.IGNORECASE)

WRDS_VENDOR_PRODUCT_CATALOG: Dict[str, Dict[str, Any]] = {
    "wrds": {
        "vendor": "WRDS",
        "products": [
            {"product": "wrdsapps_backtest_basic", "update_frequency": "Annually", "last_updated": "March 5, 2025, 2:23 p.m."},
            {"product": "wrdsapps_backtest_plus", "update_frequency": "Annually", "last_updated": "March 5, 2025, 2:29 p.m."},
            {"product": "wrdsapps_beta", "update_frequency": "N/A", "last_updated": "None"},
            {"product": "wrdsapps_bondret", "update_frequency": "N/A", "last_updated": "Feb. 28, 2025, 10:04 a.m."},
            {"product": "wrdsapps_effrontier", "update_frequency": "N/A", "last_updated": "None"},
            {"product": "wrdsapps_eushort", "update_frequency": "N/A", "last_updated": "March 19, 2025, 12:23 p.m."},
            {"product": "wrdsapps_evtstudy_int", "update_frequency": "N/A", "last_updated": "None"},
            {"product": "wrdsapps_evtstudy_int_ciq", "update_frequency": "N/A", "last_updated": "None"},
            {"product": "wrdsapps_evtstudy_intraday", "update_frequency": "N/A", "last_updated": "None"},
            {"product": "wrdsapps_evtstudy_lr", "update_frequency": "Annually", "last_updated": "Feb. 28, 2025, 1:56 p.m."},
            {"product": "wrdsapps_evtstudy_lr_ciq", "update_frequency": "Annually", "last_updated": "Feb. 13, 2024, 12:42 p.m."},
            {"product": "wrdsapps_evtstudy_us", "update_frequency": "Annually", "last_updated": "None"},
            {"product": "wrdsapps_evtstudy_us_ciq", "update_frequency": "Annually", "last_updated": "None"},
            {"product": "wrdsapps_finratio", "update_frequency": "Annually", "last_updated": "June 23, 2025, 6:28 p.m."},
            {"product": "wrdsapps_finratio_ccm", "update_frequency": "Annually", "last_updated": "June 23, 2025, 6:29 p.m."},
            {"product": "wrdsapps_finratio_ibes", "update_frequency": "Annually", "last_updated": "June 23, 2025, 6:28 p.m."},
            {"product": "wrdsapps_finratio_ibes_ccm", "update_frequency": "Annually", "last_updated": "June 23, 2025, 6:29 p.m."},
            {"product": "wrdsapps_link_comp_eushort", "update_frequency": "N/A", "last_updated": "March 19, 2025, 12:23 p.m."},
            {"product": "wrdsapps_link_crsp_bond", "update_frequency": "Annually", "last_updated": "Feb. 26, 2025, 7:41 p.m."},
            {"product": "wrdsapps_link_crsp_factset", "update_frequency": "N/A", "last_updated": "March 6, 2025, 12:40 p.m."},
            {"product": "wrdsapps_link_crsp_ibes", "update_frequency": "Annually", "last_updated": "Feb. 19, 2025, 9:10 p.m."},
            {"product": "wrdsapps_link_crsp_taq", "update_frequency": "N/A", "last_updated": "Feb. 11, 2022, 3:46 p.m."},
            {"product": "wrdsapps_link_crsp_taqm", "update_frequency": "N/A", "last_updated": "Feb. 27, 2025, 11:41 a.m."},
            {"product": "wrdsapps_link_datastream_wscope", "update_frequency": "Quarterly", "last_updated": "Oct. 15, 2025, 12:10 p.m."},
            {"product": "wrdsapps_link_dealscan_wscope", "update_frequency": "N/A", "last_updated": "None"},
            {"product": "wrdsapps_link_supplychain", "update_frequency": "N/A", "last_updated": "April 8, 2025, 4:18 p.m."},
            {"product": "wrdsapps_patents", "update_frequency": "N/A", "last_updated": "None"},
            {"product": "wrdsapps_subsidiary", "update_frequency": "N/A", "last_updated": "May 15, 2025, 4:54 p.m."},
            {"product": "wrdsapps_windices", "update_frequency": "N/A", "last_updated": "July 2, 2025, 10:49 a.m."},
            {"product": "wrdssec_all", "update_frequency": "Weekly", "last_updated": "Nov. 14, 2025, 11:01 a.m."},
            {"product": "wrdssec_common", "update_frequency": "Weekly", "last_updated": "Nov. 14, 2025, 11:08 a.m."},
            {"product": "wrdssec_midas", "update_frequency": "Annually", "last_updated": "Feb. 27, 2025, 11:59 a.m."},
            {"product": "wrdssec_secsa", "update_frequency": "Weekly", "last_updated": "Nov. 14, 2025, 11:21 a.m."},
            {"product": "bank_premium_samp", "update_frequency": "N/A", "last_updated": "Oct. 1, 2025, 1:57 p.m."},
            {"product": "wrds_environmental_samp", "update_frequency": "N/A", "last_updated": "Aug. 18, 2025, 11:46 a.m."},
            {"product": "wrds_insiders_samp", "update_frequency": "N/A", "last_updated": "Oct. 27, 2023, 10:46 a.m."},
            {"product": "wrds_mutualfund_samp", "update_frequency": "N/A", "last_updated": "July 25, 2024, 11:35 a.m."},
            {"product": "wrds_shortvolume_samp", "update_frequency": "N/A", "last_updated": "June 3, 2025, 6:03 p.m."},
        ],
    },
    "sp_global_market_intelligence": {
        "vendor": "S&P Global Market Intelligence",
        "products": [
            {"product": "ciq_capstrct", "update_frequency": "Monthly", "last_updated": "Nov. 15, 2025, 5:46 p.m."},
            {"product": "ciq_common", "update_frequency": "Monthly", "last_updated": "Nov. 15, 2025, 3:55 a.m."},
            {"product": "ciq_keydev", "update_frequency": "Monthly", "last_updated": "Oct. 2, 2025, 12:25 p.m."},
            {"product": "ciq_pplintel", "update_frequency": "Monthly", "last_updated": "Nov. 15, 2025, 5:44 a.m."},
            {"product": "comp_bank_daily", "update_frequency": "Daily", "last_updated": "Nov. 17, 2025, 11:33 a.m."},
            {"product": "comp_execucomp", "update_frequency": "Monthly", "last_updated": "Nov. 4, 2025, 10:12 a.m."},
            {"product": "comp_filings", "update_frequency": "Legacy Data - No Longer Updated", "last_updated": "Aug. 24, 2016, 2:39 p.m."},
            {"product": "comp_global_daily", "update_frequency": "Daily", "last_updated": "Nov. 16, 2025, 2:34 p.m."},
            {"product": "comp_na_daily_all", "update_frequency": "Daily", "last_updated": "Nov. 17, 2025, 5:29 a.m."},
            {"product": "comp_segments_hist_daily", "update_frequency": "Daily", "last_updated": "Nov. 17, 2025, 1:12 p.m."},
            {"product": "ciqsamp_capstrct", "update_frequency": "N/A", "last_updated": "Oct. 13, 2025, 12:01 p.m."},
            {"product": "ciqsamp_common", "update_frequency": "N/A", "last_updated": "Oct. 13, 2025, 12:01 p.m."},
            {"product": "ciqsamp_keydev", "update_frequency": "N/A", "last_updated": "Jan. 8, 2024, 4:32 p.m."},
            {"product": "ciqsamp_pplintel", "update_frequency": "N/A", "last_updated": "Oct. 13, 2025, 12:02 p.m."},
            {"product": "ciqsamp_ratings", "update_frequency": "N/A", "last_updated": "Oct. 13, 2025, 12:03 p.m."},
            {"product": "ciqsamp_transactions", "update_frequency": "N/A", "last_updated": "Nov. 17, 2025, 11:10 a.m."},
            {"product": "ciqsamp_transcripts", "update_frequency": "N/A", "last_updated": "Oct. 5, 2023, 1:44 p.m."},
            {"product": "compsamp_all", "update_frequency": "N/A", "last_updated": "April 20, 2021, 12:09 a.m."},
            {"product": "compsamp_snapshot", "update_frequency": "N/A", "last_updated": "None"},
            {"product": "trucost_samp", "update_frequency": "N/A", "last_updated": "Nov. 20, 2023, noon"},
        ],
    },
    "lseg": {
        "vendor": "London Stock Exchange (LSEG)",
        "products": [
            {"product": "tr_13f", "update_frequency": "Quarterly", "last_updated": "Nov. 6, 2025, 2:54 p.m."},
            {"product": "tr_13f_archive", "update_frequency": "Legacy Data - No Longer Updated", "last_updated": "None"},
            {"product": "tr_common", "update_frequency": "Weekly", "last_updated": "Nov. 12, 2025, 12:32 p.m."},
            {"product": "tr_dealscan", "update_frequency": "Quarterly", "last_updated": "Aug. 13, 2025, 2:06 p.m."},
            {"product": "tr_ds_comds", "update_frequency": "Weekly", "last_updated": "Nov. 12, 2025, 12:51 p.m."},
            {"product": "tr_ds_econ", "update_frequency": "Weekly", "last_updated": "Nov. 12, 2025, 1:11 p.m."},
            {"product": "tr_ds_equities", "update_frequency": "Weekly", "last_updated": "Nov. 13, 2025, 11:39 a.m."},
            {"product": "tr_ds_fut", "update_frequency": "Weekly", "last_updated": "Nov. 12, 2025, 2 p.m."},
            {"product": "tr_esg", "update_frequency": "Quarterly", "last_updated": "Nov. 4, 2025, 12:04 a.m."},
            {"product": "tr_ibes", "update_frequency": "Quarterly", "last_updated": "Oct. 13, 2025, 11:53 p.m."},
            {"product": "tr_insiders", "update_frequency": "Quarterly", "last_updated": "Nov. 15, 2025, 7:22 a.m."},
            {"product": "tr_mutualfunds", "update_frequency": "Quarterly", "last_updated": "Nov. 6, 2025, 11:30 p.m."},
            {"product": "tr_mutualfunds_archive", "update_frequency": "Legacy Data - No Longer Updated", "last_updated": "None"},
            {"product": "tr_sdc_ma", "update_frequency": "Daily", "last_updated": "Nov. 15, 2025, 5:21 a.m."},
            {"product": "tr_sdc_ni", "update_frequency": "Daily", "last_updated": "Nov. 15, 2025, 5:30 a.m."},
            {"product": "tr_tass", "update_frequency": "Monthly", "last_updated": "Nov. 2, 2025, 7:12 a.m."},
            {"product": "tr_worldscope", "update_frequency": "Quarterly", "last_updated": "Oct. 3, 2025, 12:15 a.m."},
            {"product": "ibessamp_kpi", "update_frequency": "N/A", "last_updated": "None"},
            {"product": "trsamp_all", "update_frequency": "N/A", "last_updated": "July 21, 2021, 11:53 a.m."},
            {"product": "trsamp_db_dmi", "update_frequency": "N/A", "last_updated": "Aug. 13, 2024, 1:59 p.m."},
            {"product": "trsamp_db_wb", "update_frequency": "N/A", "last_updated": "Aug. 15, 2024, 3:03 p.m."},
            {"product": "trsamp_dscom", "update_frequency": "N/A", "last_updated": "Nov. 22, 2021, 5:19 p.m."},
            {"product": "trsamp_dsecon", "update_frequency": "N/A", "last_updated": "Nov. 22, 2021, 3:51 p.m."},
            {"product": "trsamp_ds_eq", "update_frequency": "N/A", "last_updated": "Nov. 22, 2021, 8:38 p.m."},
            {"product": "trsamp_dsfut", "update_frequency": "N/A", "last_updated": "Nov. 22, 2021, 4:51 p.m."},
            {"product": "trsamp_esg", "update_frequency": "N/A", "last_updated": "Feb. 27, 2024, 10 a.m."},
            {"product": "trsamp_sdc_ma", "update_frequency": "N/A", "last_updated": "None"},
            {"product": "trsamp_sdc_ni", "update_frequency": "N/A", "last_updated": "None"},
            {"product": "trsamp_worldscope", "update_frequency": "N/A", "last_updated": "None"},
            {"product": "tr_sdc_samples", "update_frequency": "N/A", "last_updated": "March 18, 2024, 2:08 p.m."},
        ],
    },
}


def _json_default(value: Any) -> Any:
    """Serializer for numpy/pandas objects returned by WRDS queries."""

    if isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:  # pragma: no cover - defensive
            pass
    if hasattr(value, "tolist"):
        return value.tolist()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:  # pragma: no cover - defensive
            return str(value)
    return str(value)


def _normalize_identifier(identifier: str) -> str:
    if identifier is None:
        raise ValueError("WRDS identifiers cannot be None")
    return identifier.strip().lower()


def _coerce_positive_int(value: Any, fallback: int) -> int:
    try:
        parsed = int(value)
        if parsed > 0:
            return parsed
    except (TypeError, ValueError):
        pass
    return fallback


def _default_limit() -> int:
    return _coerce_positive_int(os.getenv("WRDS_DEFAULT_LIMIT"), 200)


def _default_table_obs() -> int:
    return _coerce_positive_int(os.getenv("WRDS_DEFAULT_TABLE_OBS"), 100)


def _serialize_dataframe(frame: Any) -> tuple[list[Dict[str, Any]], int, list[str]]:
    if isinstance(frame, pd.DataFrame):
        return frame.to_dict(orient="records"), len(frame), list(frame.columns)
    if frame is None:
        return [], 0, []
    if isinstance(frame, list):
        return [dict(row) if isinstance(row, dict) else {"value": row} for row in frame], len(frame), []
    if isinstance(frame, dict):
        return [frame], 1, list(frame.keys())
    return ([{"value": frame}], 1, [])


def _apply_limit(sql: str, limit: Optional[int], enforce: bool) -> tuple[str, Optional[int]]:
    normalized = sql.strip().rstrip(";")
    if not enforce:
        return f"{normalized};", None

    effective_limit = limit or _default_limit()
    if _LIMIT_PATTERN.search(normalized):
        return f"{normalized};", None

    final_sql = f"{normalized} LIMIT {effective_limit};"
    return final_sql, effective_limit


def get_wrds_connection(
    wrds_username: Optional[str] = None,
    autoconnect: bool = True,
    **connect_kwargs: Any,
) -> wrds.Connection:
    """Return a cached WRDS connection using ENV defaults when available."""

    global _CONNECTION
    with _CONNECTION_LOCK:
        if _CONNECTION is not None:
            return _CONNECTION

        username = wrds_username or os.getenv("WRDS_USERNAME")
        password = os.getenv("WRDS_PASSWORD")
        if username:
            connect_kwargs.setdefault("wrds_username", username)

        requested_autoconnect = connect_kwargs.pop("autoconnect", autoconnect)
        manual_connect = bool(password) and requested_autoconnect
        connect_kwargs["autoconnect"] = False if manual_connect else requested_autoconnect

        connection = wrds.Connection(**connect_kwargs)
        if password:
            connection._password = password  # type: ignore[attr-defined]

        if manual_connect:
            connection.connect()
            connection.load_library_list()

        _CONNECTION = connection
        return _CONNECTION


def reset_wrds_connection() -> None:
    """Close and clear the cached WRDS connection (mainly for tests)."""

    global _CONNECTION
    with _CONNECTION_LOCK:
        if _CONNECTION is not None:
            try:
                _CONNECTION.close()
            finally:
                _CONNECTION = None


def run_wrds_query(
    sql: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    date_cols: Optional[Iterable[str]] = None,
    index_col: Optional[str | list[str]] = None,
    limit: Optional[int] = None,
    enforce_limit: bool = True,
    wrds_username: Optional[str] = None,
) -> str:
    """Execute a raw SQL query with safe defaults and serialized output."""

    sql_with_limit, applied_limit = _apply_limit(sql, limit, enforce_limit)
    conn = get_wrds_connection(wrds_username=wrds_username)
    frame = conn.raw_sql(
        sql_with_limit,
        params=params,
        date_cols=date_cols,
        index_col=index_col,
    )
    records, row_count, columns = _serialize_dataframe(frame)

    payload = {
        "provider": "wrds",
        "query": sql_with_limit.strip(),
        "row_count": row_count,
        "columns": columns,
        "limit_applied": applied_limit,
        "data": records,
    }
    return json.dumps(payload, default=_json_default)


def get_wrds_table(
    library: str,
    table: str,
    *,
    columns: Optional[List[str]] = None,
    obs: Optional[int] = None,
    offset: int = 0,
    wrds_username: Optional[str] = None,
) -> str:
    """Fetch a WRDS table via ``db.get_table`` with defaults and JSON output."""

    normalized_library = _normalize_identifier(library)
    normalized_table = _normalize_identifier(table)
    limit_obs = obs or _default_table_obs()

    conn = get_wrds_connection(wrds_username=wrds_username)
    frame = conn.get_table(
        library=normalized_library,
        table=normalized_table,
        columns=columns,
        obs=limit_obs,
        offset=offset,
    )
    records, row_count, table_columns = _serialize_dataframe(frame)
    payload = {
        "provider": "wrds",
        "library": normalized_library,
        "table": normalized_table,
        "row_count": row_count,
        "columns": table_columns,
        "obs": limit_obs,
        "offset": offset,
        "data": records,
    }
    return json.dumps(payload, default=_json_default)


def _clone_catalog_entry(key: str) -> Dict[str, Any]:
    entry = WRDS_VENDOR_PRODUCT_CATALOG[key]
    return {
        "vendor": entry["vendor"],
        "products": [dict(product) for product in entry["products"]],
    }


def list_wrds_products(vendor: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Return curated WRDS vendor/product metadata derived from WRDS docs."""

    if vendor:
        normalized = vendor.strip().lower()
        if normalized not in WRDS_VENDOR_PRODUCT_CATALOG:
            available = ", ".join(sorted(WRDS_VENDOR_PRODUCT_CATALOG))
            raise ValueError(f"Unknown WRDS vendor '{vendor}'. Choose from: {available}")
        return {normalized: _clone_catalog_entry(normalized)}

    return {key: _clone_catalog_entry(key) for key in WRDS_VENDOR_PRODUCT_CATALOG}


def list_wrds_libraries(wrds_username: Optional[str] = None) -> list[str]:
    """Return a sorted list of WRDS libraries available to the account."""

    conn = get_wrds_connection(wrds_username=wrds_username)
    libraries = conn.list_libraries()
    unique = sorted({lib.strip().lower() for lib in libraries})
    return unique


def list_wrds_tables(library: str, wrds_username: Optional[str] = None) -> list[str]:
    """Return sorted, deduplicated table names for a given library."""

    normalized_library = _normalize_identifier(library)
    conn = get_wrds_connection(wrds_username=wrds_username)
    tables = conn.list_tables(normalized_library)
    unique = sorted({tbl.strip().lower() for tbl in tables})
    return unique


def describe_wrds_table(
    library: str,
    table: str,
    wrds_username: Optional[str] = None,
) -> Dict[str, Any]:
    """Return column metadata for the requested library.table pair."""

    normalized_library = _normalize_identifier(library)
    normalized_table = _normalize_identifier(table)
    conn = get_wrds_connection(wrds_username=wrds_username)
    metadata = conn.describe_table(library=normalized_library, table=normalized_table)

    if isinstance(metadata, pd.DataFrame):
        columns: list[Dict[str, Any]] = metadata.to_dict(orient="records")
    elif isinstance(metadata, list):
        columns = [dict(row) if isinstance(row, dict) else {"value": row} for row in metadata]
    elif isinstance(metadata, dict):
        columns = [metadata]
    else:  # pragma: no cover - defensive
        columns = [{"value": str(metadata)}]

    return {
        "provider": "wrds",
        "library": normalized_library,
        "table": normalized_table,
        "columns": columns,
    }


def ensure_wrds_pgpass(wrds_username: Optional[str] = None) -> Path:
    """Call ``create_pgpass_file`` and return the expected pgpass path."""

    conn = get_wrds_connection(wrds_username=wrds_username)
    conn.create_pgpass_file()
    return _pgpass_path()


def _pgpass_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home())) / "postgresql"
        return base / "pgpass.conf"
    return Path.home() / ".pgpass"
