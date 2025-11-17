from pathlib import Path

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.reporting.html_report import generate_html_report

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create a custom config
config = DEFAULT_CONFIG.copy()
config["deep_think_llm"] = "gpt-5.1"  # Use a different model
config["quick_think_llm"] = "gpt-5-mini"  # Use a different model
config["max_debate_rounds"] = 1  # Increase debate rounds

# Configure data vendors (default uses yfinance and alpha_vantage)
config["data_vendors"] = {
    "core_stock_apis": "alpha_vantage",           # Options: yfinance, alpha_vantage, local
    "technical_indicators": "alpha_vantage",      # Options: yfinance, alpha_vantage, local
    "fundamental_data": "alpha_vantage",     # Options: openai, alpha_vantage, local
    "news_data": "google",            # Options: openai, alpha_vantage, google, local
    "options_data": "alpaca",          # Options: yfinance
}

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
symbol = "NVDA"
trade_date = "2024-05-10"
final_state, decision = ta.propagate(symbol, trade_date)
print(decision)

results_dir = Path(config["results_dir"]) / symbol / trade_date
report_dir = results_dir / "reports"
metadata = {
    "ticker": symbol,
    "analysis_date": trade_date,
    "research_depth": config.get("max_debate_rounds"),
    "llm_provider": config.get("llm_provider"),
    "deep_thinker": config.get("deep_think_llm"),
    "shallow_thinker": config.get("quick_think_llm"),
    "instrument_type": config.get("trade_instrument_type"),
}

try:
    html_path = generate_html_report(final_state, metadata, report_dir)
    if html_path:
        print(f"Saved HTML report to {html_path}")
except Exception as exc:
    print(f"Failed to generate HTML report: {exc}")

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
