# TradingAgents Context Handoff — 2025-11-16 (Codex Update)

## 1. Progress & Updates
- **Data vendor serialization overhaul**
  - All Alpha Vantage, yfinance, local cache, and Alpaca stock/bar endpoints now emit normalized JSON payloads via `build_price_payload` instead of CSV strings.
  - Added reusable helper metadata (record count, timeframe, source, optional errors) so downstream consumers (risk engine, CLI, agents) can rely on a single schema.
  - Risk engine now parses these JSON payloads directly, eliminating CSV parsing logic and preventing “insufficient price history” issues caused by malformed indexes.
- **News vendor upgrade**
  - `news_api_lite.get_news` / `get_global_news` now power all ticker and macro queries with deterministic pagination, categorization, and scoring. Empty article sets raise a ValueError so the router immediately falls back to OpenAI or Google, ensuring “fresh” data.
- **CLI visualization & payoff enhancements**
  - Added price sparklines, realized volatility stats, options/volatility tables, and options/equity payoff panels to the final CLI report.
  - Report sections renumbered to include the new “Market Visuals & Payoffs” block and risk visuals now appear as Section IX.
  - Execution Strategist now attaches enriched derivative metadata (contract symbol, strike, premium, IV) when derivatives are selected; CLI trade prompt displays this info and prompts for order customization (advanced order classes, brackets, trailing stops, custom client IDs).
- **Broker/order-routing upgrades**
  - Alpaca trading adapter now supports `order_class`, take-profit/stop-loss attachments, trailing stops, and multi-leg option orders, aligning with the latest Alpaca SDK patterns.
  - CLI trade approval screen allows interactive order customization and passes all advanced parameters through to `route_to_broker`.
- **Testing**
  - Updated Alpaca integration/unit/e2e tests plus risk-engine tests to assert against the new JSON schema; ensured fallback/error surfaces are covered.

## 2. Mission-Critical Details
- **JSON price schema**
  - Payload keys: `symbol`, `start_date`, `end_date`, `source`, optional `meta`, and `records` (list of `{date, open, high, low, close, adjusted_close?, volume}`).
  - Consumers must parse JSON before using values; CSV parsing paths are removed.
  - Metadata includes `record_count`, timeframe, and optional `error` messages (e.g., authentication failures) so fallback logic can branch accordingly.
- **Risk Engine expectations**
  - `_parse_price_payload` is now the canonical ingestion path; any vendor returning a different shape will break VaR calculations.
  - Empty datasets return an empty DataFrame with a proper Date index, avoiding false “insufficient history” errors but still allowing the engine to raise when data truly lacks enough observations.
- **Order customization flow**
  - CLI interactive prompts collect limit/stop/trailing parameters, order class, bracket legs, and client order IDs; these keys map 1:1 to Alpaca’s API.
  - Non-share instruments (options) require manual confirmation; Execution Strategist preselects a contract, but operators must verify Alpaca permissions before routing.

## 3. Key Decisions & Rationale
- **JSON-only vendor outputs** to prevent Alpha Vantage “premium CSV” gating, simplify downstream parsing, and provide structured metadata for risk tooling and CLI visuals.
- **Option auto-selection** in Execution Strategist picks the most liquid call/put to avoid analysis dead-ends when derivatives are requested; rationale: keep derivative workflows deterministic while exposing premium/implied-vol data to the CLI.
- **Explicit fallback errors** (empty news feeds, authentication failures) are surfaced in the payload meta instead of silent strings so fallback logic (and operators) can make informed decisions.
- **Order customization in CLI** chosen to reduce manual edits after proposals, ensuring trade intents recorded by agents match what the broker ultimately executes.

## 4. Outstanding Issues & Next Steps
1. **Dependent docs/tests**: Documentation (e.g., `docs/alpaca-usage-guide.md`) still references CSV outputs; update guides/snippets to reflect JSON payloads.
2. **Downstream consumers**: Any scripts or notebooks parsing `get_stock_data` CSVs must migrate to JSON; audit `docs/` samples and internal tools.
3. **Google News fallback**: Configuration now defaults to News API Lite for `news_data`. If persistent “no fresh data” warnings remain, flip `DEFAULT_CONFIG["data_vendors"]["news_data"]` to `news_api_lite,google` (or set a tool-level override) so we always have at least one public fallback.
4. **Options multi-leg support**: Current Execution Strategist only selects single-leg contracts; future work could extend `_build_option_instruction` to detect strategy requests (spreads/straddles) and populate `legs`.
5. **Visualization polish**: New CLI panels rely on yfinance & options calls per run; consider caching to reduce vendor pressure and handle failures gracefully (currently prints panel-level warnings).

## 5. Additional Notes
- Tests covering the JSON transition: 
  - `tests/agents/utils/test_risk_engine.py`
  - `tests/dataflows/test_alpaca_data.py`
  - `tests/dataflows/test_alpaca_integration.py`
  - `tests/dataflows/test_alpaca_e2e.py`
- Key modules touched: 
  - `tradingagents/dataflows/utils.py` (new helper),
  - `tradingagents/dataflows/alpha_vantage_stock.py`,
  - `tradingagents/dataflows/y_finance.py`,
  - `tradingagents/dataflows/local.py`,
  - `tradingagents/dataflows/news_api_lite.py`,
  - `tradingagents/dataflows/alpaca/data.py`,
  - `tradingagents/agents/utils/risk_engine.py`,
  - `cli/main.py`,
  - `tradingagents/agents/managers/execution_strategist.py`,
  - `tradingagents/brokers/alpaca/trading.py`.
- Ensure any newly onboarded agent understands the JSON schema and updates remaining consumers/tests before adding new vendors or risk features.
