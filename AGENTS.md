# Repository Guidelines

## Project Structure & Module Organization
TradingAgents centers on the `tradingagents/` package: `agents/` defines LLM personas, `dataflows/` houses vendor adapters (yfinance, Alpha Vantage, Alpaca), `brokers/` wraps execution clients, and `graph/` wires them together via LangGraph. `cli/` (entry `python -m cli.main`) hosts the interactive workflow. Tests mirror the runtime layout in `tests/dataflows`, `tests/brokers`, and `tests/agents`; consult `tests/QUICKSTART.md` for goals before adding a suite or fixture. The agent roster now includes Macro Economist, Alternative Data Analyst, Risk Quant, Execution Strategist, and Compliance Officer modules, so contributions should keep their prompts/data sources healthy.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` inside a Python ≥3.10 env (or follow the README conda snippet) to install dependencies.
- `python main.py` runs a minimal `TradingAgentsGraph` propagation with overrides from `default_config.py`, ideal for smoke testing new agents or debate settings.
- `python -m cli.main` launches the guided workflow for choosing tickers, research depth, and LLM backbones; keep it aligned with any new flags. After the full report renders, the CLI now summarizes the Execution Strategist plan and asks the operator to approve or deny the proposed trade before routing it.
- `python scripts/verify_alpaca_integration.py` validates Alpaca credentials and endpoints before modifying broker code.
- `pytest -v` executes the suite; narrow scope with markers (`pytest -m alpaca`, `pytest -m broker`) or append `--cov=tradingagents --cov-report=term-missing` for coverage.

## Coding Style & Naming Conventions
Adhere to PEP 8, 4-space indentation, and typed signatures for LangGraph nodes, data vendors, and broker clients. Functions stay snake_case, classes follow PascalCase (`TradingAgentsGraph`), and shared config belongs in SCREAMING_SNAKE_CASE dictionaries such as `DEFAULT_CONFIG`. Keep API lookups centralized through environment helpers or `dotenv` so secrets never surface inside agents, tools, or notebooks, and respect the automated-trading knobs (`auto_execute_trades`, `default_trade_quantity`, `default_order_type`, `default_time_in_force`) whenever wiring broker calls.

## Testing Guidelines
`pytest.ini` governs discovery (`test_*.py`, `*_test.py`) and enforces markers (`unit`, `integration`, `dataflow`, `broker`, `alpaca`, `agents`). Prefer fixtures from `tests/conftest.py` for mocked Alpaca clients, credentials, and frames, extending them instead of redefining mocks. Enable coverage (`--cov=tradingagents --cov-fail-under=90`) when altering core modules and record partial passes or expected failures in `TEST_SUMMARY.md`.

## Commit & Pull Request Guidelines
Use the repository’s imperative, scope-first tone (e.g., `Refactor Alpaca integration by removing obsolete modules`). Reference affected areas (`dataflows`, `brokers`, `cli`) and include issue links. PRs must describe config changes, attach screenshots for CLI or asset updates, and list a reproducible test plan (commands above plus vendor prerequisites).

## Security & Configuration Tips
Populate secrets via a private `.env` copied from `.env.example`, exporting `OPENAI_API_KEY`, `ALPHA_VANTAGE_API_KEY`, `VOYAGE_API_KEY` (if you opt into Voyage embeddings), and broker keys; never commit those files. The Alpaca data vendor now accepts either `ALPACA_API_KEY/SECRET` or the paper/live-specific pairs, so ensure the right combination is set before running tests. Keep vendor toggles, rate-limit tweaks, embedding provider choices, and execution defaults inside `default_config.py` or CLI prompts so reviewers can trace changes. Use `restricted_tickers` and `max_position_size` to keep the Compliance Officer deterministic. Redact Alpaca order IDs, transcripts under `memory/`, and cached CSVs from logs before committing, and only flip `auto_execute_trades` to `True` when you explicitly intend to place orders.
