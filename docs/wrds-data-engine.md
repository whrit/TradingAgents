# WRDS Data Engine

TradingAgents can now talk directly to WRDS' 50+ institutional datasets via the
official `wrds` Python client. This document consolidates the WRDS quickstart
notes and explains how to drive the new data engine from the agent router.

## Prerequisites

1. **Dedicated WRDS account** – IPAuth / day-pass credentials are not supported.
2. **Python environment** – WRDS recommends installing the Anaconda distribution
   so you can manage research packages (pandas, numpy, matplotlib, psycopg2,
   etc.) without conflicting with your OS Python.
3. **`wrds` module** – already listed in `pyproject.toml` and
   `requirements.txt`, but you can install manually with `pip install wrds`.
4. **`.pgpass` file** – stores your WRDS username/password so the connector can
   auto-authenticate. WRDS ships a helper: `db.create_pgpass_file()`.

### Creating `.pgpass`

```python
from tradingagents.dataflows import wrds_data

# Prompts once for WRDS credentials and writes ~/.pgpass (or pgpass.conf on Windows)
wrds_data.ensure_wrds_pgpass()
```

Behind the scenes this runs `wrds.Connection(...).create_pgpass_file()` so you
do not need to type your password every time.

## Environment Variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `WRDS_USERNAME` | Passed to `wrds.Connection` if set | Prompted by `wrds` |
| `WRDS_PASSWORD` | Used to authenticate + seed `.pgpass` automatically | Prompted by `wrds` |
| `WRDS_DEFAULT_LIMIT` | Max rows for raw SQL when no `LIMIT` clause exists | `200` |
| `WRDS_DEFAULT_TABLE_OBS` | Default `obs` argument for `db.get_table` | `100` |

Adjust these in `.env` if you routinely need bigger extracts.

## Router Methods

The interface exposes a dedicated `institutional_data` vendor category routed to
WRDS. You can call these tools from any agent via `route_to_vendor()`:

```python
from tradingagents.dataflows.interface import route_to_vendor

# Discover datasets
libraries = route_to_vendor("list_wrds_libraries")
tables = route_to_vendor("list_wrds_tables", "djones")
metadata = route_to_vendor("describe_wrds_table", "djones", "djdaily")

# Pull a bounded table snapshot (uses db.get_table)
table_payload = route_to_vendor(
    "get_wrds_table",
    "comp",
    "funda",
    ["gvkey", "datadate", "at", "lt"],
    50,   # obs override (optional)
    0,    # offset
)

# Run arbitrary SQL with automatic LIMITs and JSON serialization
query_payload = route_to_vendor(
    "run_wrds_query",
    "SELECT date, dji FROM djones.djdaily WHERE date >= '2024-01-01'",
    params=None,
    date_cols=["date"],
    limit=25,
)

# Inspect curated vendor/product coverage sourced from WRDS documentation
catalog = route_to_vendor("list_wrds_products")
wrds_products = catalog["wrds"]["products"]
sp_global_products = catalog["sp_global_market_intelligence"]["products"]
```

`run_wrds_query` and `get_wrds_table` respond with JSON strings that include
metadata (column list, row count, limit used) plus the serialized rows. Metadata
helpers (`list_*`, `describe_*`) return native Python lists/dicts for easy prompt
composition.

## Notes

- WRDS caps each user at five concurrent connections. The data engine caches a
  single connection and reuses it; call `wrds_data.reset_wrds_connection()` if
  you need to force a reconnect (primarily for testing).
- Use small limits while prototyping and expand only once the SQL is correct –
  many WRDS libraries (TAQ, CRSP, IBES) can return millions of rows quickly.
- The helper automatically appends a `LIMIT` clause (default 200 rows) to raw
  SQL unless it already finds a `LIMIT` statement. Set `enforce_limit=False` if
  you need the full result set.
- Date columns can be parsed by passing the `date_cols` parameter directly to
  `run_wrds_query`; the wrapper forwards it to `wrds.Connection.raw_sql`.
- `list_wrds_products(vendor=None)` returns a curated catalog of WRDS, S&P
  Global Market Intelligence, and LSEG data sources (update frequency + last
  refresh) so analysts can choose the right dataset during prompts.

Refer to the upstream WRDS documentation for deeper coverage of the Python
client (metadata explorers, parameterized SQL examples, and suggestions for
using Jupyter or Spyder inside the Anaconda environment).
