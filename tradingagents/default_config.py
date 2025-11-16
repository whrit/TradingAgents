import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": "/Users/yluo/Documents/Code/ScAI/FR1-data",
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "gpt-5.1",
    "quick_think_llm": "gpt-5-mini",
    "backend_url": "https://api.openai.com/v1",
    "cost_currency": os.getenv("COST_CURRENCY", "USD"),
    "model_pricing": {
        # USD cost per 1K tokens for each provider/model combination.
        "gpt-5.1": {"input_cost_per_1k_tokens": 0.00125, "output_cost_per_1k_tokens": 0.01},
        "gpt-5-mini": {"input_cost_per_1k_tokens": 0.00025, "output_cost_per_1k_tokens": 0.002},
        "claude-3-5-sonnet-20241022": {"input_cost_per_1k_tokens": 0.015, "output_cost_per_1k_tokens": 0.075},
        "claude-3-5-haiku-20241022": {"input_cost_per_1k_tokens": 0.0015, "output_cost_per_1k_tokens": 0.005},
        "gemini-2.5-flash-preview-05-20": {"input_cost_per_1k_tokens": 0.0025, "output_cost_per_1k_tokens": 0.0075},
    },
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Embedding defaults
    "embedding_provider": "voyage",
    "embedding_model": "voyage-finance-2",
    "embedding_output_dimension": None,
    "embedding_max_tokens": int(os.getenv("EMBEDDING_MAX_TOKENS", "7000")),
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "alpha_vantage",       # Options: yfinance, alpha_vantage, local
        "technical_indicators": "alpha_vantage",  # Options: yfinance, alpha_vantage, local
        "fundamental_data": "alpha_vantage", # Options: openai, alpha_vantage, local
        "news_data": "alpha_vantage",        # Options: openai, alpha_vantage, google, local
        "options_data": "yfinance",          # Options: yfinance
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
        # Example: "get_news": "openai",               # Override category default
    },
    # Broker configuration for trade execution
    "trading_broker": "alpaca",  # Currently only "alpaca" is supported
    "broker_mode": "paper",      # "paper" for paper trading, "live" for live trading
    "auto_execute_trades": False,  # Explicit opt-in before any automated execution
    "default_trade_quantity": 1,   # Shares to trade when automation is enabled
    "default_order_type": "market",
    "default_time_in_force": "day",
    "default_limit_price": None,
    "trade_size_multiplier": float(os.getenv("TRADE_SIZE_MULTIPLIER", "1.0")),
    "trade_instrument_type": os.getenv("TRADE_INSTRUMENT_TYPE", "shares"),
    "restricted_tickers": [],
    "max_position_size": 1000,
    # Risk engine defaults
    "risk_portfolio_value": float(os.getenv("RISK_PORTFOLIO_VALUE", "1000000")),
    "risk_position_notional": float(os.getenv("RISK_POSITION_NOTIONAL", "100000")),
    "risk_budget_pct": float(os.getenv("RISK_BUDGET_PCT", "0.02")),
    "risk_benchmark": os.getenv("RISK_BENCHMARK", "SPY"),
    "risk_sector_etf": os.getenv("RISK_SECTOR_ETF", ""),
    "risk_lookback_days": int(os.getenv("RISK_LOOKBACK_DAYS", "120")),
    "risk_primary_confidence": float(os.getenv("RISK_PRIMARY_CONFIDENCE", "0.95")),
    "risk_secondary_confidence": float(os.getenv("RISK_SECONDARY_CONFIDENCE", "0.99")),
    # Alpaca credentials (loaded from environment variables)
    "alpaca_paper_api_key": os.getenv("ALPACA_PAPER_API_KEY"),
    "alpaca_paper_secret_key": os.getenv("ALPACA_PAPER_SECRET_KEY"),
    "alpaca_live_api_key": os.getenv("ALPACA_LIVE_API_KEY"),
    "alpaca_live_secret_key": os.getenv("ALPACA_LIVE_SECRET_KEY"),
}
