import json
import re
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.risk_tools import calculate_portfolio_risk
from tradingagents.dataflows.config import get_config


JSON_PATTERN = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def _extract_metrics(dashboard: str) -> dict:
    match = JSON_PATTERN.search(dashboard)
    if not match:
        raise ValueError("Risk dashboard missing JSON payload")
    return json.loads(match.group(1))


def create_risk_quant(llm):
    def risk_quant_node(state):
        config = get_config()
        ticker = state["company_of_interest"]
        trade_date = state.get("trade_date") or datetime.utcnow().strftime("%Y-%m-%d")
        lookback_days = int(config.get("risk_lookback_days", 120))
        benchmark = config.get("risk_benchmark", "SPY")
        sector = config.get("risk_sector_etf", "")
        portfolio_value = float(config.get("risk_portfolio_value", 1_000_000.0))
        position_notional = float(config.get("risk_position_notional", 100_000.0))
        risk_budget_pct = float(config.get("risk_budget_pct", 0.02))
        primary_conf = float(config.get("risk_primary_confidence", 0.95))
        secondary_conf = float(config.get("risk_secondary_confidence", 0.99))

        risk_dashboard = calculate_portfolio_risk.invoke(
            {
                "ticker": ticker,
                "end_date": trade_date,
                "lookback_days": lookback_days,
                "confidence": primary_conf,
                "confidence_levels": (primary_conf, secondary_conf),
                "benchmark": benchmark,
                "sector": sector or "",
                "portfolio_value": portfolio_value,
                "position_notional": position_notional,
                "risk_budget_pct": risk_budget_pct,
            }
        )

        metrics = _extract_metrics(risk_dashboard)
        metrics_json = json.dumps(metrics)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are the Risk Quant in a multi-agent trading system. "
                    "Use ONLY the structured metrics provided below to craft a precise risk briefing. "
                    "Your response must include: (1) A concise narrative (2 short paragraphs) describing the risk profile, "
                    "(2) A Markdown 'Risk Metrics Summary' bullet list covering VaR (95/99), Expected Shortfall, annualized vol, and max drawdown, "
                    "(3) A stress-test table summarizing market crash, sector rotation, volatility spike cost, and liquidity days, "
                    "(4) Concrete guardrails (target gross/net exposure, hedge idea, stop/ drawdown levels) referencing the metrics, and "
                    "(5) A final bullet list with exactly these items: VaR, Tail risk, Hedge recommendation, Risk capital usage. "
                    "Populate every figure directly from the JSON and flag 'N/A' when data is missing. Do NOT restate the raw JSON block."
                    "\n\nRISK_METRICS_JSON:\n{risk_metrics_json}\n\nRAW_DASHBOARD (reference only):\n{risk_dashboard}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        chain = prompt | llm
        result = chain.invoke(
            {
                "messages": state["messages"],
                "risk_metrics_json": metrics_json,
                "risk_dashboard": risk_dashboard,
            }
        )

        report_body = result.content if hasattr(result, "content") else str(result)
        combined_report = f"{report_body}\n\n---\nRAW RISK DASHBOARD\n{risk_dashboard}"

        return {
            "messages": [result],
            "risk_quant_report": combined_report,
        }

    return risk_quant_node
