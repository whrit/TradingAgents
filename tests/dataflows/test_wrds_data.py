import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pytest

from tradingagents.dataflows import interface as data_interface
from tradingagents.dataflows import wrds_data
from tradingagents.dataflows.interface import route_to_vendor


class StubConnection:
    def __init__(self, dataframe: pd.DataFrame | None = None):
        self.dataframe = dataframe if dataframe is not None else pd.DataFrame()
        self.raw_calls: list[Dict[str, Any]] = []
        self.table_calls: list[Dict[str, Any]] = []
        self.libraries_requested: list[str] = []
        self.tables_requested: list[str] = []
        self.pgpass_calls = 0

    def raw_sql(self, sql: str, params=None, date_cols=None, index_col=None):
        self.raw_calls.append(
            {
                "sql": sql,
                "params": params,
                "date_cols": date_cols,
                "index_col": index_col,
            }
        )
        return self.dataframe

    def get_table(self, library: str, table: str, **kwargs):
        call = {"library": library, "table": table, **kwargs}
        self.table_calls.append(call)
        return self.dataframe

    def list_libraries(self):
        return ["comp", "ibes", "crsp"]

    def list_tables(self, library: str):
        self.libraries_requested.append(library)
        return ["msf", "dsf", "stocknames"]

    def describe_table(self, library: str, table: str):
        self.tables_requested.append(f"{library}.{table}")
        return pd.DataFrame(
            [
                {"name": "gvkey", "type": "int", "label": "Company Id"},
                {"name": "permno", "type": "int", "label": "Permno"},
            ]
        )

    def create_pgpass_file(self):
        self.pgpass_calls += 1


def test_run_wrds_query_enforces_limit_and_serializes(monkeypatch):
    monkeypatch.setenv("WRDS_DEFAULT_LIMIT", "25")
    df = pd.DataFrame(
        [
            {"date": "2025-01-02", "dji": 123.45},
            {"date": "2025-01-03", "dji": 126.01},
        ]
    )
    stub = StubConnection(dataframe=df)
    monkeypatch.setattr(wrds_data, "get_wrds_connection", lambda wrds_username=None: stub)

    payload = json.loads(
        wrds_data.run_wrds_query(
            "SELECT date, dji FROM djones.djdaily",
            params={"tickers": ("IBM", "AAPL")},
            date_cols=["date"],
        )
    )

    assert "limit 25" in stub.raw_calls[0]["sql"].lower()
    assert payload["provider"] == "wrds"
    assert payload["row_count"] == 2
    assert payload["limit_applied"] == 25
    assert payload["data"][0]["dji"] == pytest.approx(123.45)
    assert stub.raw_calls[0]["params"] == {"tickers": ("IBM", "AAPL")}
    assert stub.raw_calls[0]["date_cols"] == ["date"]


def test_get_wrds_connection_uses_env_credentials(monkeypatch):
    class FakeConnection:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self._password = ""
            self.connect_calls = 0
            self.load_calls = 0

        def connect(self):
            self.connect_calls += 1

        def load_library_list(self):
            self.load_calls += 1

        def close(self):
            pass

    wrds_data.reset_wrds_connection()
    monkeypatch.setenv("WRDS_USERNAME", "wrds_user")
    monkeypatch.setenv("WRDS_PASSWORD", "wrds_secret")
    monkeypatch.setattr(wrds_data.wrds, "Connection", FakeConnection)

    conn = wrds_data.get_wrds_connection()

    assert conn.kwargs["wrds_username"] == "wrds_user"
    assert conn._password == "wrds_secret"
    assert conn.connect_calls == 1
    assert conn.load_calls == 1

    wrds_data.reset_wrds_connection()


def test_run_wrds_query_respects_existing_limit(monkeypatch):
    df = pd.DataFrame([
        {"date": "2025-01-02", "gvkey": "1000"},
    ])
    stub = StubConnection(dataframe=df)
    monkeypatch.setattr(wrds_data, "get_wrds_connection", lambda wrds_username=None: stub)

    payload = json.loads(
        wrds_data.run_wrds_query("SELECT * FROM comp.funda LIMIT 10")
    )

    sql = stub.raw_calls[0]["sql"].strip().lower()
    assert sql.endswith("limit 10;")
    assert payload["limit_applied"] is None


def test_get_wrds_table_normalizes_inputs(monkeypatch):
    monkeypatch.setenv("WRDS_DEFAULT_TABLE_OBS", "50")
    df = pd.DataFrame([
        {"gvkey": "1000", "datadate": "2024-12-31", "at": 100.0},
    ])
    stub = StubConnection(dataframe=df)
    monkeypatch.setattr(wrds_data, "get_wrds_connection", lambda wrds_username=None: stub)

    payload = json.loads(
        wrds_data.get_wrds_table("CRSP", "MSF", columns=["gvkey", "datadate"], offset=5)
    )

    call = stub.table_calls[0]
    assert call["library"] == "crsp"
    assert call["table"] == "msf"
    assert call["obs"] == 50
    assert call["offset"] == 5
    assert payload["library"] == "crsp"
    assert payload["row_count"] == 1


def test_metadata_helpers_sort_and_describe(monkeypatch):
    stub = StubConnection()
    monkeypatch.setattr(wrds_data, "get_wrds_connection", lambda wrds_username=None: stub)

    libraries = wrds_data.list_wrds_libraries()
    assert libraries == sorted(set(["comp", "ibes", "crsp"]))

    tables = wrds_data.list_wrds_tables("CRSP")
    assert stub.libraries_requested == ["crsp"]
    assert tables == sorted(set(["msf", "dsf", "stocknames"]))

    description = wrds_data.describe_wrds_table("CRSP", "MSF")
    assert stub.tables_requested == ["crsp.msf"]
    assert description["columns"][0]["name"] == "gvkey"


def test_ensure_pgpass_invokes_connection(monkeypatch):
    stub = StubConnection()
    monkeypatch.setattr(wrds_data, "get_wrds_connection", lambda wrds_username=None, autoconnect=True: stub)
    monkeypatch.setattr(wrds_data, "_pgpass_path", lambda: Path("/tmp/.pgpass"))

    pgpass_path = wrds_data.ensure_wrds_pgpass()

    assert stub.pgpass_calls == 1
    assert pgpass_path == Path("/tmp/.pgpass")


def test_route_wrds_query_via_interface(monkeypatch):
    result_payload = {"status": "ok"}

    def fake_wrds(sql, **kwargs):
        return result_payload

    monkeypatch.setitem(
        data_interface.VENDOR_METHODS.setdefault("run_wrds_query", {}),
        "wrds",
        fake_wrds,
    )

    response = route_to_vendor("run_wrds_query", "SELECT 1")
    assert response is result_payload


def test_list_wrds_products_filters_vendor():
    catalog = wrds_data.list_wrds_products()
    assert "wrds" in catalog
    assert any(
        item["product"] == "wrdsapps_finratio"
        for item in catalog["wrds"]["products"]
    )

    lseg_only = wrds_data.list_wrds_products("LSEG")
    assert list(lseg_only.keys()) == ["lseg"]
    assert any(prod["product"] == "tr_tass" for prod in lseg_only["lseg"]["products"])

    with pytest.raises(ValueError):
        wrds_data.list_wrds_products("unknown_vendor")
