import json
from typing import Annotated, Sequence

import numpy as np
from langchain_core.tools import tool

from tradingagents.agents.utils.risk_engine import RiskEngine, RiskInputs


def _to_percent(value: float) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    return f"{value:.2%}"


def _json_default(value):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value


def _format_report(report: dict) -> str:
    meta = report["meta"]
    lines = [
        f"### Risk Dashboard for {meta['ticker']} (as of {meta['end_date']})",
        f"Look-back window: {meta['lookback_days']} days | Observations: {meta['data_points']}",
        "",
        "#### VaR & Tail Risk",
    ]

    for flavor, entries in report["var"].items():
        parts = []
        for level, stats in entries.items():
            parts.append(f"{level}: {_to_percent(stats['value'])}")
        lines.append(f"- {flavor.title()}: {', '.join(parts)}")

    stress = report["stress"]
    lines.extend(
        [
            "",
            "#### Stress Tests",
            f"- Market crash (-20% beta-adjusted): {_to_percent(stress['market_crash_pct'])}",
            f"- Sector rotation (-10%): {_to_percent(stress['sector_rotation_pct'])}",
            f"- Volatility spike hedge cost: ${stress['vol_spike_cost']:,.0f}",
            f"- Liquidity days to exit: {stress['liquidity_days']:.2f}",
        ]
    )

    liquidity = report["liquidity"]
    lines.extend(
        [
            "",
            "#### Liquidity & Positioning",
            f"- ADV (USD): ${liquidity['adv_dollars']:,.0f}",
            f"- Days to exit current plan: {liquidity['days_to_exit']:.2f}",
            f"- Suggested max position: ${report['position_sizing']['max_position']:,.0f}",
            f"- Optimal position: ${report['position_sizing']['optimal_position']:,.0f}",
        ]
    )

    lines.extend(
        [
            "",
            "#### Risk Limits",
            "| Metric | Current | Limit | Status |",
            "|--------|---------|-------|--------|",
        ]
    )
    for row in report["risk_limits"]:
        metric = row["metric"]
        value = _to_percent(row["current"]) if "Exposure" in metric or metric == "VaR" else f"{row['current']:.2f}"
        limit = _to_percent(row["limit"]) if "Exposure" in metric or metric == "VaR" else f"{row['limit']:.2f}"
        lines.append(f"| {metric} | {value} | {limit} | {row['status']} |")

    lines.extend(
        [
            "",
            "```json",
            json.dumps(report, indent=2, default=_json_default),
            "```",
        ]
    )

    return "\n".join(lines)


@tool
def calculate_portfolio_risk(
    ticker: Annotated[str, "Ticker symbol"],
    end_date: Annotated[str, "Analysis end date in yyyy-mm-dd format"],
    lookback_days: Annotated[int, "How many days of history to use"] = 120,
    confidence: Annotated[float, "Primary VaR confidence level"] = 0.95,
    confidence_levels: Annotated[
        Sequence[float], "Tuple of VaR confidence levels"
    ] = (),
    benchmark: Annotated[str, "Benchmark ticker for beta/hedging"] = "SPY",
    sector: Annotated[str, "Sector ETF or None" ] = "",
    portfolio_value: Annotated[float, "Portfolio notional used for risk budgets"] = 1_000_000.0,
    position_notional: Annotated[float, "Current position size in dollars"] = 100_000.0,
    risk_budget_pct: Annotated[float, "Max VaR as % of portfolio"] = 0.02,
) -> str:
    """Return a Markdown risk dashboard plus the structured JSON metrics."""
    engine = RiskEngine()
    levels = tuple(confidence_levels) if confidence_levels else (confidence, 0.99)
    inputs = RiskInputs(
        ticker=ticker,
        end_date=end_date,
        lookback_days=lookback_days,
        confidence_levels=levels,
        benchmark=benchmark or None,
        sector=sector or None,
        portfolio_value=portfolio_value,
        position_notional=position_notional,
        risk_budget_pct=risk_budget_pct,
    )
    report = engine.generate(inputs)
    return _format_report(report)
