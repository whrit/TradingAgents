from typing import Optional
import datetime
import json
import math
import typer
import uuid
from pathlib import Path
from functools import wraps
from statistics import fmean
from rich.console import Console, Group
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live
from rich.columns import Columns
from rich.markdown import Markdown
from rich.layout import Layout
from rich.text import Text
from rich.live import Live
from rich.table import Table
from collections import deque
import time
from rich.tree import Tree
from rich import box
from rich.align import Align
from rich.rule import Rule
import yfinance as yf

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.brokers.interface import route_to_broker
from tradingagents.dataflows.interface import route_to_vendor
from cli.models import AnalystType
from cli.utils import *
from cli.html_report import generate_html_report

console = Console()

TEAM_STRUCTURE = {
    "Analyst Team": [
        "Macro Economist",
        "Market Analyst",
        "Social Analyst",
        "News Analyst",
        "Fundamentals Analyst",
        "Alternative Data Analyst",
    ],
    "Research Team": ["Bull Researcher", "Bear Researcher", "Research Manager"],
    "Trading Team": ["Trader", "Risk Quant Analyst"],
    "Risk Management": ["Risky Analyst", "Neutral Analyst", "Safe Analyst"],
    "Portfolio & Execution": [
        "Portfolio Manager",
        "Execution Strategist",
        "Compliance Officer",
    ],
}

app = typer.Typer(
    name="TradingAgents",
    help="TradingAgents CLI: Multi-Agents LLM Financial Trading Framework",
    add_completion=True,  # Enable shell completion
)


# Create a deque to store recent messages with a maximum length
class MessageBuffer:
    def __init__(self, max_length=100):
        self.messages = deque(maxlen=max_length)
        self.tool_calls = deque(maxlen=max_length)
        self.current_report = None
        self.final_report = None  # Store the complete final report
        self.agent_status = {
            # Analyst Team
            "Macro Economist": "pending",
            "Market Analyst": "pending",
            "Social Analyst": "pending",
            "News Analyst": "pending",
            "Fundamentals Analyst": "pending",
            "Alternative Data Analyst": "pending",
            # Research Team
            "Bull Researcher": "pending",
            "Bear Researcher": "pending",
            "Research Manager": "pending",
            # Trading Team
            "Trader": "pending",
            "Risk Quant Analyst": "pending",
            # Risk Management Team
            "Risky Analyst": "pending",
            "Neutral Analyst": "pending",
            "Safe Analyst": "pending",
            # Portfolio Management Team
            "Portfolio Manager": "pending",
            "Execution Strategist": "pending",
            "Compliance Officer": "pending",
        }
        self.current_agent = None
        self.report_sections = {
            "macro_report": None,
            "market_report": None,
            "sentiment_report": None,
            "news_report": None,
            "fundamentals_report": None,
            "alternative_data_report": None,
            "investment_plan": None,
            "trader_investment_plan": None,
            "risk_quant_report": None,
            "final_trade_decision": None,
            "execution_plan": None,
            "compliance_report": None,
        }
        self.ticker = None
        self.live_metrics = {
            "costs": None,
            "positions": [],
            "positions_error": None,
            "pnl": {},
            "account_error": None,
            "account": None,
            "market": None,
            "market_error": None,
            "trade_size_multiplier": 1.0,
            "instrument_type": "shares",
        }

    def add_message(self, message_type, content):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.messages.append((timestamp, message_type, content))

    def add_tool_call(self, tool_name, args):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.tool_calls.append((timestamp, tool_name, args))

    def update_agent_status(self, agent, status):
        if agent in self.agent_status:
            self.agent_status[agent] = status
            self.current_agent = agent

    def update_report_section(self, section_name, content):
        if section_name in self.report_sections:
            self.report_sections[section_name] = content
            self._update_current_report()

    def set_ticker(self, ticker: str):
        self.ticker = ticker

    def update_cost_summary(self, summary):
        self.live_metrics["costs"] = summary

    def update_positions_snapshot(self, snapshot):
        self.live_metrics["positions"] = snapshot.get("positions", [])
        self.live_metrics["positions_error"] = snapshot.get("error")
        pnl = snapshot.get("pnl")
        if pnl is not None:
            self.live_metrics["pnl"] = pnl

    def update_account_snapshot(self, snapshot):
        self.live_metrics["account"] = snapshot.get("account")
        self.live_metrics["account_error"] = snapshot.get("error")

    def update_market_snapshot(self, snapshot):
        self.live_metrics["market"] = snapshot.get("market")
        self.live_metrics["market_error"] = snapshot.get("error")

    def set_trade_preferences(self, multiplier: float, instrument: str):
        self.live_metrics["trade_size_multiplier"] = multiplier
        self.live_metrics["instrument_type"] = instrument

    def _update_current_report(self):
        # For the panel display, only show the most recently updated section
        latest_section = None
        latest_content = None

        # Find the most recently updated section
        for section, content in self.report_sections.items():
            if content is not None:
                latest_section = section
                latest_content = content
               
        if latest_section and latest_content:
            # Format the current section for display
            section_titles = {
                "macro_report": "Macro Outlook",
                "market_report": "Market Analysis",
                "sentiment_report": "Social Sentiment",
                "news_report": "News Analysis",
                "fundamentals_report": "Fundamentals Analysis",
                "alternative_data_report": "Alternative Data",
                "investment_plan": "Research Team Decision",
                "trader_investment_plan": "Trading Team Plan",
                "risk_quant_report": "Risk Quant Summary",
                "final_trade_decision": "Portfolio Management Decision",
                "execution_plan": "Execution Strategy",
                "compliance_report": "Compliance Summary",
            }
            self.current_report = (
                f"### {section_titles[latest_section]}\n{latest_content}"
            )

        # Update the final complete report
        self._update_final_report()

    def _update_final_report(self):
        report_parts = []

        # Analyst Team Reports
        analyst_sections = [
            "macro_report",
            "market_report",
            "sentiment_report",
            "news_report",
            "fundamentals_report",
            "alternative_data_report",
        ]
        if any(self.report_sections[section] for section in analyst_sections):
            report_parts.append("## Analyst Team Reports")
            if self.report_sections["macro_report"]:
                report_parts.append(
                    f"### Macro Economist\n{self.report_sections['macro_report']}"
                )
            if self.report_sections["market_report"]:
                report_parts.append(
                    f"### Market Analysis\n{self.report_sections['market_report']}"
                )
            if self.report_sections["sentiment_report"]:
                report_parts.append(
                    f"### Social Sentiment\n{self.report_sections['sentiment_report']}"
                )
            if self.report_sections["news_report"]:
                report_parts.append(
                    f"### News Analysis\n{self.report_sections['news_report']}"
                )
            if self.report_sections["fundamentals_report"]:
                report_parts.append(
                    f"### Fundamentals Analysis\n{self.report_sections['fundamentals_report']}"
                )
            if self.report_sections["alternative_data_report"]:
                report_parts.append(
                    f"### Alternative Data\n{self.report_sections['alternative_data_report']}"
                )

        # Research Team Reports
        if self.report_sections["investment_plan"]:
            report_parts.append("## Research Team Decision")
            report_parts.append(f"{self.report_sections['investment_plan']}")

        # Trading Team Reports
        if self.report_sections["trader_investment_plan"]:
            report_parts.append("## Trading Team Plan")
            report_parts.append(f"{self.report_sections['trader_investment_plan']}")
        if self.report_sections["risk_quant_report"]:
            report_parts.append("## Risk Quant Summary")
            report_parts.append(f"{self.report_sections['risk_quant_report']}")

        # Portfolio Management Decision
        if self.report_sections["final_trade_decision"]:
            report_parts.append("## Portfolio Management Decision")
            report_parts.append(f"{self.report_sections['final_trade_decision']}")
        if self.report_sections["execution_plan"]:
            report_parts.append("## Execution Strategy")
            report_parts.append(f"{self.report_sections['execution_plan']}")
        if self.report_sections["compliance_report"]:
            report_parts.append("## Compliance Summary")
            report_parts.append(f"{self.report_sections['compliance_report']}")

        self.final_report = "\n\n".join(report_parts) if report_parts else None


message_buffer = MessageBuffer()


def create_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    layout["main"].split_column(
        Layout(name="upper", ratio=3), Layout(name="analysis", ratio=5)
    )
    layout["upper"].split_row(
        Layout(name="progress", ratio=2),
        Layout(name="messages", ratio=3),
        Layout(name="dashboard", ratio=2),
    )
    return layout


def format_currency(value):
    if value is None:
        return "—"
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def format_percent(value):
    if value is None:
        return "—"
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return "—"


def render_live_cost_panel():
    summary = message_buffer.live_metrics.get("costs")
    currency = (summary or {}).get("currency", "USD")
    table = Table(box=box.SIMPLE_HEAD, show_header=False, expand=True)
    table.add_row(f"Currency: [bold]{currency}[/bold]")
    trade_mult = message_buffer.live_metrics.get("trade_size_multiplier", 1.0)
    instrument = message_buffer.live_metrics.get("instrument_type") or "shares"
    instrument_label = instrument.replace("_", " ").title()
    table.add_row(f"Trade Size: x{trade_mult}")
    table.add_row(f"Instrument: {instrument_label}")
    if summary:
        total = summary.get("total_cost", 0.0)
        calls = summary.get("total_calls", 0)
        table.add_row(f"Run Cost: [bold]{total:,.4f} {currency}[/bold]")
        table.add_row(f"LLM Calls: {calls:,}")
        table.add_row("")
        mini = Table(
            title="Top Models",
            box=box.MINIMAL_DOUBLE_HEAD,
            expand=True,
            show_header=True,
        )
        mini.add_column("Model", style="cyan")
        mini.add_column("Cost", justify="right")
        models = (summary.get("models") or {}).items()
        for model, stats in sorted(
            models, key=lambda item: item[1].get("cost", 0), reverse=True
        )[:3]:
            mini.add_row(model, f"{stats.get('cost', 0):,.4f}")
        if not models:
            mini.add_row("—", "0.0000")
        table.add_row(mini)
    else:
        table.add_row("[dim]Waiting for token usage...[/dim]")

    return Panel(table, title="Live Cost Tracker", border_style="yellow", padding=(1, 1))


def render_positions_panel():
    metrics = message_buffer.live_metrics
    positions = metrics.get("positions") or []
    positions_table = Table(
        title="Positions",
        box=box.MINIMAL,
        show_header=True,
        expand=True,
    )
    positions_table.add_column("Symbol", style="cyan", justify="center")
    positions_table.add_column("Qty", justify="right")
    positions_table.add_column("Price", justify="right")
    positions_table.add_column("P&L", justify="right")
    if positions:
        for pos in positions[:5]:
            pnl = pos.get("pnl")
            pnl_color = "green" if pnl is not None and pnl >= 0 else "red"
            pnl_str = (
                f"[{pnl_color}]{format_currency(pnl)}[/{pnl_color}]"
                if pnl is not None
                else "—"
            )
            positions_table.add_row(
                pos.get("symbol", "—"),
                pos.get("qty", "—"),
                format_currency(pos.get("price")),
                pnl_str,
            )
    else:
        error = metrics.get("positions_error")
        positions_table.add_row(
            "—", "—", "—", error or "No open positions"
        )

    pnl_data = metrics.get("pnl") or {}
    pnl_table = Table(box=box.MINIMAL, show_header=False, expand=True)
    pnl_table.add_row("Unrealized:", format_currency(pnl_data.get("unrealized")))
    pnl_table.add_row("Positions:", str(pnl_data.get("count") or len(positions)))

    account = metrics.get("account") or {}
    account_table = Table(box=box.MINIMAL, show_header=False, expand=True)
    if account:
        account_table.add_row("Cash:", format_currency(account.get("cash")))
        account_table.add_row("Equity:", format_currency(account.get("equity")))
        account_table.add_row(
            "Buying Power:", format_currency(account.get("buying_power"))
        )
        if status := account.get("status"):
            account_table.add_row("Status:", status)
    else:
        error = metrics.get("account_error")
        account_table.add_row("Account:", error or "Unavailable")

    content = Group(positions_table, pnl_table, account_table)
    return Panel(content, title="Portfolio Snapshot", border_style="cyan", padding=(1, 1))


def render_market_panel():
    snapshot = message_buffer.live_metrics.get("market")
    table = Table(box=box.SIMPLE_HEAD, show_header=False, expand=True)
    if snapshot:
        table.add_row("Symbol:", snapshot.get("symbol", "—"))
        table.add_row("Price:", format_currency(snapshot.get("price")))
        change = snapshot.get("change")
        pct = snapshot.get("percent_change")
        if change is not None:
            color = "green" if change >= 0 else "red"
            pct_str = f"{pct:+.2f}%" if pct is not None else ""
            table.add_row(
                "Change:",
                f"[{color}]{change:+.2f}[/{color}] {pct_str}",
            )
        table.add_row("Open:", format_currency(snapshot.get("open")))
        table.add_row("High / Low:", f"{format_currency(snapshot.get('high'))} / {format_currency(snapshot.get('low'))}")
        volume = snapshot.get("volume")
        if volume is not None:
            table.add_row("Volume:", f"{volume:,.0f}")
        if snapshot.get("five_day_change") is not None:
            table.add_row(
                "5D Change:",
                f"{snapshot['five_day_change']:+.2f}%",
            )
        if snapshot.get("timestamp"):
            table.add_row(
                "Last Update:",
                snapshot["timestamp"],
            )
    else:
        error = message_buffer.live_metrics.get("market_error") or "Waiting for market data..."
        table.add_row(error)

    return Panel(table, title="Market Movement", border_style="magenta", padding=(1, 1))


def _make_bar(value: float, max_value: float, width: int = 20) -> str:
    if max_value <= 0:
        return ""
    ratio = min(1.0, max(0.0, value / max_value))
    blocks = max(1, int(ratio * width))
    return "▇" * blocks


SPARKLINE_BLOCKS = "▁▂▃▄▅▆▇█"


def _sparkline(points):
    values = [float(p) for p in points if p is not None]
    if not values:
        return "n/a"
    minimum = min(values)
    maximum = max(values)
    if math.isclose(maximum, minimum):
        return "─" * len(values)
    span = maximum - minimum
    chars = []
    for value in values:
        normalized = (value - minimum) / span
        index = int(round(normalized * (len(SPARKLINE_BLOCKS) - 1)))
        index = max(0, min(index, len(SPARKLINE_BLOCKS) - 1))
        chars.append(SPARKLINE_BLOCKS[index])
    return "".join(chars)


def _pct_change(series, window):
    if series is None or len(series) <= window:
        return None
    earlier = float(series.iloc[-window - 1])
    latest = float(series.iloc[-1])
    if earlier == 0:
        return None
    return ((latest / earlier) - 1) * 100


def build_price_visuals(ticker: str):
    try:
        hist = yf.Ticker(ticker).history(period="1mo", interval="1d")
    except Exception as exc:  # pragma: no cover - network
        message = f"Failed to load price history: {exc}"
        return Panel(message, title="Price Action", border_style="red"), None

    if hist is None or hist.empty:
        return Panel("No price history available.", title="Price Action", border_style="red"), None

    closes = hist["Close"].dropna()
    latest_price = float(closes.iloc[-1]) if not closes.empty else None
    trend = closes.tail(20)
    spark = _sparkline(trend.tolist())

    spark_panel = Panel(
        Align.center(Text(spark, style="bold green")),
        title="30-Day Trend",
        border_style="green",
    )

    stats = Table(box=box.MINIMAL, show_header=False, expand=True)
    stats.add_row("Last Close", format_currency(latest_price))
    stats.add_row("1D", format_percent(_pct_change(closes, 1)))
    stats.add_row("5D", format_percent(_pct_change(closes, 5)))
    stats.add_row("1M", format_percent(_pct_change(closes, len(closes) - 1)))

    returns = closes.pct_change().dropna()
    realized_vol = None
    if not returns.empty:
        realized_vol = returns.std() * math.sqrt(252) * 100

    vol_table = Table(box=box.MINIMAL, show_header=False, expand=True)
    vol_table.add_row("Realized Vol (ann.)", format_percent(realized_vol))
    vol_table.add_row("Observations", str(len(closes)))

    combined = Columns([stats, vol_table], equal=True, expand=True)
    body = Group(spark_panel, combined)
    return Panel(body, title=f"Price Action — {ticker.upper()}", border_style="cyan"), latest_price


def _summarize_option_rows(rows, title):
    table = Table(title=title, box=box.SIMPLE_HEAD, expand=True)
    table.add_column("Contract", style="cyan")
    table.add_column("Strike", justify="right")
    table.add_column("Last", justify="right")
    table.add_column("IV", justify="right")
    table.add_column("OI", justify="right")
    for row in rows[:3]:
        iv = row.get("impliedVolatility")
        iv_pct = format_percent((iv or 0) * 100 if iv and iv > 1 else (iv or 0) * 100)
        table.add_row(
            str(row.get("contractSymbol", "—")),
            f"{row.get('strike', 0):,.2f}",
            f"{row.get('lastPrice', 0):,.2f}",
            iv_pct,
            f"{int(row.get('openInterest', 0)):,}",
        )
    if not rows:
        table.add_row("—", "—", "—", "—", "—")
    return table


def build_options_visuals(ticker: str, ref_price: Optional[float]):
    snapshot = None
    try:
        raw = route_to_vendor("get_options_data", ticker.upper(), None, 6)
        snapshot = json.loads(raw) if raw else {}
    except Exception as exc:  # pragma: no cover - network
        message = f"Failed to load options data: {exc}"
        return Panel(message, title="Options & Volatility", border_style="red"), snapshot

    calls = snapshot.get("calls", []) or []
    puts = snapshot.get("puts", []) or []
    if not calls and not puts:
        return Panel("Options chain unavailable.", title="Options & Volatility", border_style="red"), snapshot

    calls_table = _summarize_option_rows(calls, "Top Calls")
    puts_table = _summarize_option_rows(puts, "Top Puts")

    call_iv = [row.get("impliedVolatility") for row in calls if row.get("impliedVolatility")]
    put_iv = [row.get("impliedVolatility") for row in puts if row.get("impliedVolatility")]
    call_oi = sum(row.get("openInterest", 0) or 0 for row in calls)
    put_oi = sum(row.get("openInterest", 0) or 0 for row in puts)

    summary = Table(title="Volatility Snapshot", box=box.SIMPLE_HEAD, expand=True, show_header=False)
    summary.add_row("Expiry", snapshot.get("expiry", "—"))
    summary.add_row("Avg Call IV", format_percent((fmean(call_iv) * 100) if call_iv else None))
    summary.add_row("Avg Put IV", format_percent((fmean(put_iv) * 100) if put_iv else None))
    ratio = (call_oi / put_oi) if put_oi else None
    summary.add_row("Call/Put OI", f"{ratio:.2f}" if ratio is not None else "—")
    summary.add_row("Ref Price", format_currency(ref_price))

    visuals = Columns([calls_table, puts_table, summary], equal=True, expand=True)
    panel = Panel(visuals, title="Options & Volatility", border_style="magenta", padding=(1, 1))
    return panel, snapshot


def _infer_option_from_snapshot(snapshot, preferred_side: str):
    if not snapshot:
        return None
    option_type = "call" if preferred_side == "buy" else "put"
    collection = snapshot.get("calls" if option_type == "call" else "puts", [])
    if not collection:
        return None
    candidate = collection[0]
    return {
        "option_type": option_type,
        "strike": candidate.get("strike"),
        "premium": candidate.get("lastPrice") or candidate.get("ask") or candidate.get("bid"),
        "contract_symbol": candidate.get("contractSymbol"),
        "implied_vol": candidate.get("impliedVolatility"),
        "expiry": snapshot.get("expiry"),
        "multiplier": 100,
    }


def build_payoff_panel(final_state, ref_price: Optional[float], options_snapshot: Optional[dict]):
    trade = final_state.get("proposed_trade")
    if not trade:
        return None

    quantity = float(trade.get("quantity") or 0)
    if quantity == 0:
        return None

    action = trade.get("action", "buy").lower()
    direction = 1 if action == "buy" else -1
    instrument = trade.get("instrument_type", "shares")
    payoff_table = Table(title="Scenario PnL", box=box.SIMPLE_HEAD, expand=True)
    payoff_table.add_column("Move", justify="right")
    payoff_table.add_column("Price", justify="right")
    payoff_table.add_column("PnL", justify="right")
    steps = [-0.1, -0.05, 0.0, 0.05, 0.1]

    if instrument == "shares":
        if ref_price is None:
            return None
        for move in steps:
            scenario_price = ref_price * (1 + move)
            pnl = direction * quantity * (scenario_price - ref_price)
            payoff_table.add_row(format_percent(move * 100), format_currency(scenario_price), format_currency(pnl))
        title = "Equity Payoff"
        info = f"Qty: {quantity:.2f} shares"
    else:
        derivative = trade.get("derivative_details") or _infer_option_from_snapshot(options_snapshot, action)
        if not derivative:
            return None
        strike = derivative.get("strike")
        premium = derivative.get("premium")
        if strike is None or premium is None or ref_price is None:
            return None
        multiplier = derivative.get("multiplier", 100)
        opt_type = derivative.get("option_type", "call")
        for move in steps:
            scenario_price = ref_price * (1 + move)
            if opt_type == "call":
                intrinsic = max(0.0, scenario_price - strike)
            else:
                intrinsic = max(0.0, strike - scenario_price)
            payoff = (intrinsic - premium) * multiplier * quantity * direction
            payoff_table.add_row(format_percent(move * 100), format_currency(scenario_price), format_currency(payoff))
        title = f"Options Payoff ({opt_type.title()})"
        info = f"Contract: {derivative.get('contract_symbol', '—')} | Strike {strike:.2f} | Premium {premium:.2f}"

    return Panel(
        Group(payoff_table, Text(info, style="dim")),
        title=title,
        border_style="yellow",
        padding=(1, 1),
    )


def render_risk_visuals(final_state):
    metrics_blob = final_state.get("risk_metrics_json")
    if not metrics_blob:
        return None
    if isinstance(metrics_blob, str):
        try:
            metrics = json.loads(metrics_blob)
        except json.JSONDecodeError:
            return None
    elif isinstance(metrics_blob, dict):
        metrics = metrics_blob
    else:
        return None

    var_table = Table(title="Value at Risk", box=box.SIMPLE_HEAD, expand=True)
    var_table.add_column("Type")
    var_table.add_column("VaR (%)", justify="right")
    var_table.add_column("ES (%)", justify="right")
    hist = metrics.get("var", {}).get("historical", {})
    for cl, stats in hist.items():
        var_table.add_row(
            f"Hist {cl}",
            f"{stats.get('value', 0)*100:.2f}",
            f"{stats.get('expected_shortfall', 0)*100:.2f}",
        )
    param = metrics.get("var", {}).get("parametric", {})
    for cl, stats in param.items():
        var_table.add_row(
            f"Param {cl}",
            f"{stats.get('value', 0)*100:.2f}",
            "—",
        )

    stress_table = Table(title="Stress Tests", box=box.SIMPLE_HEAD, expand=True)
    stress_table.add_column("Scenario")
    stress_table.add_column("Impact", justify="right")
    for key, value in (metrics.get("stress") or {}).items():
        label = key.replace("_", " ").title()
        if key.endswith("_pct"):
            impact = f"{value*100:.1f}%"
        elif "cost" in key:
            impact = f"${value:,.0f}"
        else:
            impact = f"{value:.1f}"
        stress_table.add_row(label, impact)

    sizing_table = Table(title="Position Sizing", box=box.SIMPLE_HEAD, expand=True)
    sizing_table.add_column("Metric")
    sizing_table.add_column("Value", justify="right")
    sizing_table.add_column("Visual")
    sizing = metrics.get("position_sizing") or {}
    max_sizing = max(sizing.values()) if sizing else 0
    for key, value in sizing.items():
        label = key.replace("_", " ").title()
        sizing_table.add_row(label, f"${value:,.0f}", _make_bar(value, max_sizing))

    limits_table = Table(title="Risk Limits", box=box.SIMPLE_HEAD, expand=True)
    limits_table.add_column("Metric")
    limits_table.add_column("Current", justify="right")
    limits_table.add_column("Limit", justify="right")
    limits_table.add_column("Status")
    for row in metrics.get("risk_limits", []):
        status = row.get("status", "OK")
        color = {"OK": "green", "WARNING": "yellow", "BREACH": "red"}.get(status, "white")
        limits_table.add_row(
            row.get("metric", "—"),
            f"{row.get('current', 0):.3f}",
            f"{row.get('limit', 0):.3f}",
            f"[{color}]{status}[/{color}]",
        )

    visuals = Columns(
        [var_table, stress_table, sizing_table, limits_table],
        equal=True,
        expand=True,
    )
    return Panel(visuals, title="IX. Risk Visuals", border_style="cyan", padding=(1, 1))


def _prompt_optional_float(message: str, default: Optional[float] = None) -> Optional[float]:
    prompt_default = "" if default is None else str(default)
    while True:
        raw = typer.prompt(message, default=prompt_default)
        raw = raw.strip()
        if not raw:
            return default
        try:
            return float(raw.replace("%", ""))
        except ValueError:
            console.print("[red]Please enter a valid number or leave blank to skip.[/red]")


def _customize_order(trade: dict) -> dict:
    console.print("[cyan]Customize order parameters[/cyan]")
    order_type_default = trade.get("order_type", "market")
    order_type = typer.prompt(
        "Order type [market/limit/stop/stop_limit/trailing_stop]",
        default=order_type_default,
    ).strip()
    if order_type:
        trade["order_type"] = order_type.lower()

    if trade["order_type"] in {"limit", "stop_limit"}:
        trade["limit_price"] = _prompt_optional_float(
            "Limit price",
            trade.get("limit_price"),
        )

    if trade["order_type"] in {"stop", "stop_limit"}:
        trade["stop_price"] = _prompt_optional_float(
            "Stop trigger price",
            trade.get("stop_price"),
        )

    if trade["order_type"] == "trailing_stop":
        trail_raw = typer.prompt(
            "Trail amount (append % for percent)",
            default="5%",
        ).strip()
        if trail_raw.endswith("%"):
            trade["trail_percent"] = float(trail_raw[:-1])
            trade["trail_price"] = None
        else:
            trade["trail_price"] = float(trail_raw)
            trade["trail_percent"] = None

    tif_default = trade.get("time_in_force", "day").upper()
    tif = typer.prompt(
        "Time in force (DAY/GTC/OPG/CLS/IOC/FOK)",
        default=tif_default,
    ).strip()
    if tif:
        trade["time_in_force"] = tif.lower()

    order_class_default = trade.get("order_class", "simple")
    order_class_value = typer.prompt(
        "Order class (simple/bracket/oco/oto/otoco/mleg)",
        default=order_class_default,
    ).strip()
    if order_class_value:
        trade["order_class"] = order_class_value.lower()

    if typer.confirm("Attach take-profit target?", default=False):
        tp_price = _prompt_optional_float(
            "Take profit limit price",
            (trade.get("take_profit") or {}).get("limit_price"),
        )
        if tp_price is not None:
            trade["take_profit"] = {"limit_price": tp_price}

    if typer.confirm("Attach stop-loss guard?", default=False):
        stop_loss_price = _prompt_optional_float(
            "Stop loss trigger price",
            (trade.get("stop_loss_order") or {}).get("stop_price"),
        )
        limit_cap = _prompt_optional_float(
            "Optional stop-loss limit price",
            (trade.get("stop_loss_order") or {}).get("limit_price"),
        )
        if stop_loss_price is not None:
            trade["stop_loss_order"] = {
                "stop_price": stop_loss_price,
                "limit_price": limit_cap,
            }

    if typer.confirm("Generate a client_order_id for tracking?", default=True):
        trade["client_order_id"] = trade.get("client_order_id") or f"cli_{uuid.uuid4().hex[:8]}"

    return trade


def fetch_positions_snapshot():
    try:
        raw = route_to_broker("get_positions")
    except Exception as exc:  # pragma: no cover - network call
        return {"positions": [], "error": str(exc)}

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines or lines[0].lower().startswith("no open positions"):
        return {"positions": []}

    positions = []
    total_pnl = 0.0
    for line in lines:
        if not line.startswith("- "):
            continue
        # Example line: - AAPL: 10 shares @ $150.50 (P&L: $25.00)
        try:
            body = line[2:]
            symbol, rest = body.split(":", 1)
            qty_part, remainder = rest.split("shares @", 1)
            qty = qty_part.strip()
            price_part, pnl_part = remainder.split("(P&L:", 1)
            price = float(price_part.replace("$", "").strip())
            pnl_value = pnl_part.replace(")", "").replace("$", "").strip()
            pnl = float(pnl_value)
            total_pnl += pnl
            positions.append(
                {
                    "symbol": symbol.strip(),
                    "qty": qty,
                    "price": price,
                    "pnl": pnl,
                }
            )
        except ValueError:
            continue

    return {
        "positions": positions,
        "pnl": {"unrealized": total_pnl, "count": len(positions)},
    }


def fetch_account_snapshot():
    try:
        raw = route_to_broker("get_account")
    except Exception as exc:  # pragma: no cover - network call
        return {"account": None, "error": str(exc)}

    account = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip().replace("$", "").replace(",", "")
        if key == "cash":
            account["cash"] = float(value)
        elif key == "equity":
            account["equity"] = float(value)
        elif key == "buying power":
            account["buying_power"] = float(value)
        elif key == "status":
            account["status"] = value.upper()

    return {"account": account}


def fetch_market_snapshot(ticker: str):
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period="5d", interval="1d")
        if hist.empty:
            raise ValueError("No price data")
        last = hist.iloc[-1]
        prev_close = hist.iloc[-2]["Close"] if len(hist) > 1 else last["Open"]
        price = float(last["Close"])
        change = price - float(prev_close)
        percent_change = (change / float(prev_close)) * 100 if prev_close else 0.0
        five_day_change = None
        if len(hist) > 1:
            base = float(hist.iloc[0]["Close"])
            if base:
                five_day_change = ((price / base) - 1) * 100
        snapshot = {
            "symbol": ticker.upper(),
            "price": price,
            "open": float(last["Open"]),
            "high": float(last["High"]),
            "low": float(last["Low"]),
            "volume": float(last.get("Volume", 0)),
            "change": change,
            "percent_change": percent_change,
            "five_day_change": five_day_change,
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        }
        return {"market": snapshot}
    except Exception as exc:  # pragma: no cover - network dependent
        return {"market": None, "error": str(exc)}


def update_display(layout, spinner_text=None):
    # Header with welcome message
    layout["header"].update(
        Panel(
            "[bold green]Welcome to TradingAgents CLI[/bold green]\n"
            "[dim]© [Tauric Research](https://github.com/TauricResearch)[/dim]",
            title="Welcome to TradingAgents",
            border_style="green",
            padding=(1, 2),
            expand=True,
        )
    )

    # Progress panel showing agent status
    progress_table = Table(
        show_header=True,
        header_style="bold magenta",
        show_footer=False,
        box=box.SIMPLE_HEAD,  # Use simple header with horizontal lines
        title=None,  # Remove the redundant Progress title
        padding=(0, 2),  # Add horizontal padding
        expand=True,  # Make table expand to fill available space
    )
    progress_table.add_column("Team", style="cyan", justify="center", width=20)
    progress_table.add_column("Agent", style="green", justify="center", width=20)
    progress_table.add_column("Status", style="yellow", justify="center", width=20)

    # Group agents by team
    for team, agents in TEAM_STRUCTURE.items():
        # Add first agent with team name
        first_agent = agents[0]
        status = message_buffer.agent_status[first_agent]
        if status == "in_progress":
            spinner = Spinner(
                "dots", text="[blue]in_progress[/blue]", style="bold cyan"
            )
            status_cell = spinner
        else:
            status_color = {
                "pending": "yellow",
                "completed": "green",
                "error": "red",
            }.get(status, "white")
            status_cell = f"[{status_color}]{status}[/{status_color}]"
        progress_table.add_row(team, first_agent, status_cell)

        # Add remaining agents in team
        for agent in agents[1:]:
            status = message_buffer.agent_status[agent]
            if status == "in_progress":
                spinner = Spinner(
                    "dots", text="[blue]in_progress[/blue]", style="bold cyan"
                )
                status_cell = spinner
            else:
                status_color = {
                    "pending": "yellow",
                    "completed": "green",
                    "error": "red",
                }.get(status, "white")
                status_cell = f"[{status_color}]{status}[/{status_color}]"
            progress_table.add_row("", agent, status_cell)

        # Add horizontal line after each team
        progress_table.add_row("─" * 20, "─" * 20, "─" * 20, style="dim")

    layout["progress"].update(
        Panel(progress_table, title="Progress", border_style="cyan", padding=(1, 2))
    )

    # Messages panel showing recent messages and tool calls
    messages_table = Table(
        show_header=True,
        header_style="bold magenta",
        show_footer=False,
        expand=True,  # Make table expand to fill available space
        box=box.MINIMAL,  # Use minimal box style for a lighter look
        show_lines=True,  # Keep horizontal lines
        padding=(0, 1),  # Add some padding between columns
    )
    messages_table.add_column("Time", style="cyan", width=8, justify="center")
    messages_table.add_column("Type", style="green", width=10, justify="center")
    messages_table.add_column(
        "Content", style="white", no_wrap=False, ratio=1
    )  # Make content column expand

    # Combine tool calls and messages
    all_messages = []

    # Add tool calls
    for timestamp, tool_name, args in message_buffer.tool_calls:
        # Truncate tool call args if too long
        if isinstance(args, str) and len(args) > 100:
            args = args[:97] + "..."
        all_messages.append((timestamp, "Tool", f"{tool_name}: {args}"))

    # Add regular messages
    for timestamp, msg_type, content in message_buffer.messages:
        # Convert content to string if it's not already
        content_str = content
        if isinstance(content, list):
            # Handle list of content blocks (Anthropic format)
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                    elif item.get('type') == 'tool_use':
                        text_parts.append(f"[Tool: {item.get('name', 'unknown')}]")
                else:
                    text_parts.append(str(item))
            content_str = ' '.join(text_parts)
        elif not isinstance(content_str, str):
            content_str = str(content)
            
        # Truncate message content if too long
        if len(content_str) > 200:
            content_str = content_str[:197] + "..."
        all_messages.append((timestamp, msg_type, content_str))

    # Sort by timestamp
    all_messages.sort(key=lambda x: x[0])

    # Calculate how many messages we can show based on available space
    # Start with a reasonable number and adjust based on content length
    max_messages = 12  # Increased from 8 to better fill the space

    # Get the last N messages that will fit in the panel
    recent_messages = all_messages[-max_messages:]

    # Add messages to table
    for timestamp, msg_type, content in recent_messages:
        # Format content with word wrapping
        wrapped_content = Text(content, overflow="fold")
        messages_table.add_row(timestamp, msg_type, wrapped_content)

    if spinner_text:
        messages_table.add_row("", "Spinner", spinner_text)

    # Add a footer to indicate if messages were truncated
    if len(all_messages) > max_messages:
        messages_table.footer = (
            f"[dim]Showing last {max_messages} of {len(all_messages)} messages[/dim]"
        )

    layout["messages"].update(
        Panel(
            messages_table,
            title="Messages & Tools",
            border_style="blue",
            padding=(1, 2),
        )
    )

    dashboard_columns = Columns(
        [
            render_live_cost_panel(),
            render_positions_panel(),
            render_market_panel(),
        ],
        equal=True,
        expand=True,
    )
    layout["dashboard"].update(
        Panel(dashboard_columns, title="Live Operations", border_style="purple", padding=(1, 1))
    )

    # Analysis panel showing current report
    if message_buffer.current_report:
        layout["analysis"].update(
            Panel(
                Markdown(message_buffer.current_report),
                title="Current Report",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        layout["analysis"].update(
            Panel(
                "[italic]Waiting for analysis report...[/italic]",
                title="Current Report",
                border_style="green",
                padding=(1, 2),
            )
        )

    # Footer with statistics
    tool_calls_count = len(message_buffer.tool_calls)
    llm_calls_count = sum(
        1 for _, msg_type, _ in message_buffer.messages if msg_type == "Reasoning"
    )
    reports_count = sum(
        1 for content in message_buffer.report_sections.values() if content is not None
    )

    stats_table = Table(show_header=False, box=None, padding=(0, 2), expand=True)
    stats_table.add_column("Stats", justify="center")
    stats_table.add_row(
        f"Tool Calls: {tool_calls_count} | LLM Calls: {llm_calls_count} | Generated Reports: {reports_count}"
    )

    layout["footer"].update(Panel(stats_table, border_style="grey50"))


def get_user_selections():
    """Get all user selections before starting the analysis display."""
    # Display ASCII art welcome message
    with open("./cli/static/welcome.txt", "r") as f:
        welcome_ascii = f.read()

    # Create welcome box content
    welcome_content = f"{welcome_ascii}\n"
    welcome_content += "[bold green]TradingAgents: Multi-Agents LLM Financial Trading Framework - CLI[/bold green]\n\n"
    welcome_content += "[bold]Workflow Steps:[/bold]\n"
    welcome_content += "I. Analyst Team → II. Research Team → III. Trader → IV. Risk Management → V. Portfolio Management\n\n"
    welcome_content += (
        "[dim]Built by [Tauric Research](https://github.com/TauricResearch)[/dim]"
    )

    # Create and center the welcome box
    welcome_box = Panel(
        welcome_content,
        border_style="green",
        padding=(1, 2),
        title="Welcome to TradingAgents",
        subtitle="Multi-Agents LLM Financial Trading Framework",
    )
    console.print(Align.center(welcome_box))
    console.print()  # Add a blank line after the welcome box

    # Create a boxed questionnaire for each step
    def create_question_box(title, prompt, default=None):
        box_content = f"[bold]{title}[/bold]\n"
        box_content += f"[dim]{prompt}[/dim]"
        if default:
            box_content += f"\n[dim]Default: {default}[/dim]"
        return Panel(box_content, border_style="blue", padding=(1, 2))

    # Step 1: Ticker symbol
    console.print(
        create_question_box(
            "Step 1: Ticker Symbol", "Enter the ticker symbol to analyze", "SPY"
        )
    )
    selected_ticker = get_ticker()

    # Step 2: Analysis date
    default_date = datetime.datetime.now().strftime("%Y-%m-%d")
    console.print(
        create_question_box(
            "Step 2: Analysis Date",
            "Enter the analysis date (YYYY-MM-DD)",
            default_date,
        )
    )
    analysis_date = get_analysis_date()

    # Step 3: Select analysts
    console.print(
        create_question_box(
            "Step 3: Analysts Team", "Select your LLM analyst agents for the analysis"
        )
    )
    selected_analysts = select_analysts()
    console.print(
        f"[green]Selected analysts:[/green] {', '.join(analyst.value for analyst in selected_analysts)}"
    )

    # Step 4: Research depth
    console.print(
        create_question_box(
            "Step 4: Research Depth", "Select your research depth level"
        )
    )
    selected_research_depth = select_research_depth()

    # Step 5: OpenAI backend
    console.print(
        create_question_box(
            "Step 5: OpenAI backend", "Select which service to talk to"
        )
    )
    selected_llm_provider, backend_url = select_llm_provider()
    
    # Step 6: Thinking agents
    console.print(
        create_question_box(
            "Step 6: Thinking Agents", "Select your thinking agents for analysis"
        )
    )
    selected_shallow_thinker = select_shallow_thinking_agent(selected_llm_provider)
    selected_deep_thinker = select_deep_thinking_agent(selected_llm_provider)

    console.print(
        create_question_box(
            "Step 7: Trade Sizing",
            "Enter a multiplier to scale the default trade quantity (e.g., 1 = default, 2 = double).",
        )
    )
    trade_multiplier = select_trade_size_multiplier()

    console.print(
        create_question_box(
            "Step 8: Instrument Preference",
            "Choose whether the Execution Strategist should target traditional shares or derivatives.",
        )
    )
    instrument_choice = select_instrument_type()

    return {
        "ticker": selected_ticker,
        "analysis_date": analysis_date,
        "analysts": selected_analysts,
        "research_depth": selected_research_depth,
        "llm_provider": selected_llm_provider.lower(),
        "backend_url": backend_url,
        "shallow_thinker": selected_shallow_thinker,
        "deep_thinker": selected_deep_thinker,
        "trade_size_multiplier": trade_multiplier,
        "instrument_type": instrument_choice,
    }


def get_ticker():
    """Get ticker symbol from user input."""
    return typer.prompt("", default="SPY")


def get_analysis_date():
    """Get the analysis date from user input."""
    while True:
        date_str = typer.prompt(
            "", default=datetime.datetime.now().strftime("%Y-%m-%d")
        )
        try:
            # Validate date format and ensure it's not in the future
            analysis_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            if analysis_date.date() > datetime.datetime.now().date():
                console.print("[red]Error: Analysis date cannot be in the future[/red]")
                continue
            return date_str
        except ValueError:
            console.print(
                "[red]Error: Invalid date format. Please use YYYY-MM-DD[/red]"
            )


def display_complete_report(final_state):
    """Display the complete analysis report with team-based panels."""
    console.print("\n[bold green]Complete Analysis Report[/bold green]\n")

    # I. Analyst Team Reports
    analyst_reports = []

    if final_state.get("macro_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["macro_report"]),
                title="Macro Economist",
                border_style="blue",
                padding=(1, 2),
            )
        )

    if final_state.get("market_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["market_report"]),
                title="Market Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    # Social Analyst Report
    if final_state.get("sentiment_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["sentiment_report"]),
                title="Social Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    # News Analyst Report
    if final_state.get("news_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["news_report"]),
                title="News Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    if final_state.get("fundamentals_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["fundamentals_report"]),
                title="Fundamentals Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )
    if final_state.get("alternative_data_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["alternative_data_report"]),
                title="Alternative Data Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    if analyst_reports:
        console.print(
            Panel(
                Columns(analyst_reports, equal=True, expand=True),
                title="I. Analyst Team Reports",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    # II. Research Team Reports
    if final_state.get("investment_debate_state"):
        research_reports = []
        debate_state = final_state["investment_debate_state"]

        # Bull Researcher Analysis
        if debate_state.get("bull_history"):
            research_reports.append(
                Panel(
                    Markdown(debate_state["bull_history"]),
                    title="Bull Researcher",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Bear Researcher Analysis
        if debate_state.get("bear_history"):
            research_reports.append(
                Panel(
                    Markdown(debate_state["bear_history"]),
                    title="Bear Researcher",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Research Manager Decision
        if debate_state.get("judge_decision"):
            research_reports.append(
                Panel(
                    Markdown(debate_state["judge_decision"]),
                    title="Research Manager",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        if research_reports:
            console.print(
                Panel(
                    Columns(research_reports, equal=True, expand=True),
                    title="II. Research Team Decision",
                    border_style="magenta",
                    padding=(1, 2),
                )
            )

    # III. Trading Team Reports
    trading_panels = []
    if final_state.get("trader_investment_plan"):
        trading_panels.append(
            Panel(
                Markdown(final_state["trader_investment_plan"]),
                title="Trader",
                border_style="blue",
                padding=(1, 2),
            )
        )
    if final_state.get("risk_quant_report"):
        trading_panels.append(
            Panel(
                Markdown(final_state["risk_quant_report"]),
                title="Risk Quant Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )
    if trading_panels:
        console.print(
            Panel(
                Columns(trading_panels, equal=True, expand=True),
                title="III. Trading & Hedging Plan",
                border_style="yellow",
                padding=(1, 2),
            )
        )

    visuals = []
    latest_price = None
    options_snapshot = None
    ticker = final_state.get("company_of_interest")
    if ticker:
        price_panel, latest_price = build_price_visuals(ticker)
        if price_panel:
            visuals.append(price_panel)
        options_panel, options_snapshot = build_options_visuals(
            ticker, latest_price
        )
        if options_panel:
            visuals.append(options_panel)
    payoff_panel = build_payoff_panel(final_state, latest_price, options_snapshot)
    if payoff_panel:
        visuals.append(payoff_panel)

    if visuals:
        console.print(
            Panel(
                Columns(visuals, equal=True, expand=True),
                title="IV. Market Visuals & Payoffs",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    # V. Risk Management Team Reports
    if final_state.get("risk_debate_state"):
        risk_reports = []
        risk_state = final_state["risk_debate_state"]

        # Aggressive (Risky) Analyst Analysis
        if risk_state.get("risky_history"):
            risk_reports.append(
                Panel(
                    Markdown(risk_state["risky_history"]),
                    title="Aggressive Analyst",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Conservative (Safe) Analyst Analysis
        if risk_state.get("safe_history"):
            risk_reports.append(
                Panel(
                    Markdown(risk_state["safe_history"]),
                    title="Conservative Analyst",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Neutral Analyst Analysis
        if risk_state.get("neutral_history"):
            risk_reports.append(
                Panel(
                    Markdown(risk_state["neutral_history"]),
                    title="Neutral Analyst",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        if risk_reports:
            console.print(
                Panel(
                    Columns(risk_reports, equal=True, expand=True),
                    title="V. Risk Management Team Decision",
                    border_style="red",
                    padding=(1, 2),
                )
            )

        # VI. Portfolio Manager Decision
        if risk_state.get("judge_decision"):
            console.print(
                Panel(
                    Panel(
                        Markdown(risk_state["judge_decision"]),
                        title="Portfolio Manager",
                        border_style="blue",
                        padding=(1, 2),
                    ),
                    title="VI. Portfolio Manager Decision",
                    border_style="green",
                    padding=(1, 2),
                )
            )

    # VII. Execution & Compliance
    exec_panels = []
    if final_state.get("execution_plan"):
        exec_panels.append(
            Panel(
                Markdown(final_state["execution_plan"]),
                title="Execution Strategist",
                border_style="blue",
                padding=(1, 2),
            )
        )
    if final_state.get("compliance_report"):
        exec_panels.append(
            Panel(
                Markdown(final_state["compliance_report"]),
                title="Compliance Officer",
                border_style="blue",
                padding=(1, 2),
            )
        )
    if exec_panels:
        console.print(
            Panel(
                Columns(exec_panels, equal=True, expand=True),
                title="VII. Execution & Compliance",
                border_style="white",
                padding=(1, 2),
            )
        )

    # VIII. Run Cost Summary
    cost_stats = final_state.get("cost_statistics")
    if cost_stats:
        currency = cost_stats.get("currency", "USD")
        total_cost = cost_stats.get("total_cost", 0.0)

        models_table = Table(
            title="Model Cost Breakdown",
            box=box.SIMPLE_HEAD,
            expand=True,
        )
        models_table.add_column("Model", style="cyan")
        models_table.add_column("Calls", justify="right")
        models_table.add_column("Input Tokens", justify="right")
        models_table.add_column("Output Tokens", justify="right")
        models_table.add_column(f"Cost ({currency})", justify="right")

        if cost_stats.get("models"):
            for model_name, stats in sorted(cost_stats["models"].items()):
                models_table.add_row(
                    model_name,
                    f"{stats.get('calls', 0):,}",
                    f"{stats.get('input_tokens', 0):,}",
                    f"{stats.get('output_tokens', 0):,}",
                    f"{stats.get('cost', 0.0):,.4f}",
                )
        else:
            models_table.add_row("—", "0", "0", "0", f"{0.0:,.4f}")

        sections_table = Table(
            title="Section Cost Breakdown",
            box=box.SIMPLE_HEAD,
            expand=True,
        )
        sections_table.add_column("Section", style="magenta")
        sections_table.add_column("Calls", justify="right")
        sections_table.add_column("Cost", justify="right")

        if cost_stats.get("sections"):
            for section, stats in sorted(cost_stats["sections"].items()):
                sections_table.add_row(
                    section,
                    f"{stats.get('calls', 0):,}",
                    f"{stats.get('cost', 0.0):,.4f}",
                )
        else:
            sections_table.add_row("—", "0", f"{0.0:,.4f}")

        console.print(
            Panel(
                Columns([models_table, sections_table], equal=True, expand=True),
                title=f"VIII. Run Cost Summary — Total {currency} {total_cost:,.4f}",
                border_style="yellow",
                padding=(1, 2),
            )
        )

    risk_panel = render_risk_visuals(final_state)
    if risk_panel:
        console.print(risk_panel)


def prompt_trade_execution(final_state, config):
    trade = final_state.get("proposed_trade")
    if not trade:
        console.print("[yellow]No executable trade was proposed.[/yellow]")
        return

    if final_state.get("compliance_status") == "BLOCKED":
        console.print(
            "[red]Compliance blocked the trade. Manual execution disabled.[/red]"
        )
        return

    if config.get("auto_execute_trades") and final_state.get("broker_execution"):
        console.print("[green]Trade already auto-executed per configuration.[/green]")
        return

    instrument = config.get("trade_instrument_type", "shares")
    instrument_label = instrument.replace("_", " ").title()
    multiplier = config.get("trade_size_multiplier", 1.0)
    asset_type = trade.get("asset_type", "equity")
    units = "contracts" if asset_type == "option" else "shares"
    symbol_display = trade.get("symbol")
    underlying = trade.get("underlying_symbol")
    derivative = trade.get("derivative_details")

    console.print(
        Panel(
            f"Trader recommends to [bold]{trade['action'].upper()}[/bold] "
            f"{trade['quantity']} {units} of {symbol_display} using "
            f"{trade.get('order_type','market').upper()} / "
            f"{trade.get('time_in_force','day').upper()}.\n"
            f"Instrument preference: [bold]{instrument_label}[/bold] (size x{multiplier}).\n"
            f"Asset type: {asset_type.title()}"
            f"{f' | Underlying: {underlying}' if underlying else ''}.\n\n"
            f"Execution notes:\n{final_state.get('execution_plan','(none)')}",
            title="Proposed Trade",
            border_style="yellow",
        )
    )

    if derivative:
        option_table = Table(box=box.MINIMAL, show_header=False, title="Option Contract")
        option_table.add_row("Contract", derivative.get("contract_symbol", "—"))
        option_table.add_row("Strike", format_currency(derivative.get("strike")))
        option_table.add_row("Premium", format_currency(derivative.get("premium")))
        option_table.add_row("Expiry", derivative.get("expiry", "—"))
        option_table.add_row("IV", format_percent((derivative.get("implied_vol") or 0) * 100))
        console.print(option_table)

    if asset_type == "option":
        console.print(
            "[yellow]Ensure your Alpaca account has options permissions before routing this order.[/yellow]"
        )

    if typer.confirm("Customize order parameters before routing?", default=False):
        trade = _customize_order(trade)

    if typer.confirm("Do you approve and want to route this trade?", default=False):
        try:
            result = route_to_broker(
                "place_order",
                trade["symbol"],
                trade["quantity"],
                trade["action"],
                order_type=trade.get("order_type", "market"),
                time_in_force=trade.get("time_in_force", "day"),
                limit_price=trade.get("limit_price"),
                stop_price=trade.get("stop_price"),
                trail_price=trade.get("trail_price"),
                trail_percent=trade.get("trail_percent"),
                asset_type=trade.get("asset_type", "equity"),
                order_class=trade.get("order_class"),
                take_profit=trade.get("take_profit"),
                stop_loss_order=trade.get("stop_loss_order"),
                legs=trade.get("legs"),
                client_order_id=trade.get("client_order_id"),
            )
            console.print(
                f"[green]Trade executed: {result}[/green]"
            )
        except Exception as exc:  # pragma: no cover
            console.print(
                f"[red]Failed to execute trade: {exc}[/red]"
            )
    else:
        console.print("[yellow]Trade skipped at user request.[/yellow]")


def update_research_team_status(status):
    """Update status for all research team members and trader."""
    research_team = ["Bull Researcher", "Bear Researcher", "Research Manager", "Trader"]
    for agent in research_team:
        message_buffer.update_agent_status(agent, status)

def extract_content_string(content):
    """Extract string content from various message formats."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Handle Anthropic's list format
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
                elif item.get('type') == 'tool_use':
                    text_parts.append(f"[Tool: {item.get('name', 'unknown')}]")
            else:
                text_parts.append(str(item))
        return ' '.join(text_parts)
    else:
        return str(content)

def run_analysis():
    # First get all user selections
    selections = get_user_selections()
    message_buffer.set_ticker(selections["ticker"])
    message_buffer.set_trade_preferences(
        selections["trade_size_multiplier"], selections["instrument_type"]
    )

    # Create config with selected research depth
    config = DEFAULT_CONFIG.copy()
    config["max_debate_rounds"] = selections["research_depth"]
    config["max_risk_discuss_rounds"] = selections["research_depth"]
    config["quick_think_llm"] = selections["shallow_thinker"]
    config["deep_think_llm"] = selections["deep_thinker"]
    config["backend_url"] = selections["backend_url"]
    config["llm_provider"] = selections["llm_provider"].lower()
    config["trade_size_multiplier"] = selections["trade_size_multiplier"]
    config["trade_instrument_type"] = selections["instrument_type"]

    # Initialize the graph
    graph = TradingAgentsGraph(
        [analyst.value for analyst in selections["analysts"]], config=config, debug=True
    )

    # Create result directory
    results_dir = Path(config["results_dir"]) / selections["ticker"] / selections["analysis_date"]
    results_dir.mkdir(parents=True, exist_ok=True)
    report_dir = results_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    log_file = results_dir / "message_tool.log"
    log_file.touch(exist_ok=True)

    def save_message_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            timestamp, message_type, content = obj.messages[-1]
            content = content.replace("\n", " ")  # Replace newlines with spaces
            with open(log_file, "a") as f:
                f.write(f"{timestamp} [{message_type}] {content}\n")
        return wrapper
    
    def save_tool_call_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            timestamp, tool_name, args = obj.tool_calls[-1]
            args_str = ", ".join(f"{k}={v}" for k, v in args.items())
            with open(log_file, "a") as f:
                f.write(f"{timestamp} [Tool Call] {tool_name}({args_str})\n")
        return wrapper

    def save_report_section_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(section_name, content):
            func(section_name, content)
            if section_name in obj.report_sections and obj.report_sections[section_name] is not None:
                content = obj.report_sections[section_name]
                if content:
                    file_name = f"{section_name}.md"
                    with open(report_dir / file_name, "w") as f:
                        f.write(content)
        return wrapper

    message_buffer.add_message = save_message_decorator(message_buffer, "add_message")
    message_buffer.add_tool_call = save_tool_call_decorator(message_buffer, "add_tool_call")
    message_buffer.update_report_section = save_report_section_decorator(message_buffer, "update_report_section")

    # Seed live dashboards before rendering
    message_buffer.update_market_snapshot(fetch_market_snapshot(selections["ticker"]))
    message_buffer.update_positions_snapshot(fetch_positions_snapshot())
    message_buffer.update_account_snapshot(fetch_account_snapshot())

    # Now start the display layout
    layout = create_layout()

    with Live(layout, refresh_per_second=4) as live:
        # Initial display
        update_display(layout)

        # Add initial messages
        message_buffer.add_message("System", f"Selected ticker: {selections['ticker']}")
        message_buffer.add_message(
            "System", f"Analysis date: {selections['analysis_date']}"
        )
        message_buffer.add_message(
            "System",
            f"Selected analysts: {', '.join(analyst.value for analyst in selections['analysts'])}",
        )
        message_buffer.add_message(
            "System",
            f"Trade size multiplier: x{selections['trade_size_multiplier']}",
        )
        message_buffer.add_message(
            "System",
            f"Instrument preference: {selections['instrument_type'].replace('_',' ').title()}",
        )
        update_display(layout)

        # Reset agent statuses
        for agent in message_buffer.agent_status:
            message_buffer.update_agent_status(agent, "pending")

        # Reset report sections
        for section in message_buffer.report_sections:
            message_buffer.report_sections[section] = None
        message_buffer.current_report = None
        message_buffer.final_report = None

        # Update agent status to in_progress for the first analyst
        analyst_display = {value: label for label, value in ANALYST_ORDER}
        first_analyst_value = selections["analysts"][0]
        first_display = analyst_display.get(
            first_analyst_value, f"{first_analyst_value.value.capitalize()} Analyst"
        )
        message_buffer.update_agent_status(first_display, "in_progress")
        update_display(layout)

        # Create spinner text
        spinner_text = (
            f"Analyzing {selections['ticker']} on {selections['analysis_date']}..."
        )
        update_display(layout, spinner_text)

        # Initialize state and get graph args
        init_agent_state = graph.propagator.create_initial_state(
            selections["ticker"], selections["analysis_date"]
        )
        args = graph.propagator.get_graph_args()

        # Stream the analysis
        trace = []
        last_market_refresh = 0
        for chunk in graph.graph.stream(init_agent_state, **args):
            if len(chunk["messages"]) > 0:
                # Get the last message from the chunk
                last_message = chunk["messages"][-1]

                # Extract message content and type
                if hasattr(last_message, "content"):
                    content = extract_content_string(last_message.content)  # Use the helper function
                    msg_type = "Reasoning"
                else:
                    content = str(last_message)
                    msg_type = "System"

                # Add message to buffer
                message_buffer.add_message(msg_type, content)                

                # If it's a tool call, add it to tool calls
                if hasattr(last_message, "tool_calls"):
                    for tool_call in last_message.tool_calls:
                        # Handle both dictionary and object tool calls
                        if isinstance(tool_call, dict):
                            message_buffer.add_tool_call(
                                tool_call["name"], tool_call["args"]
                            )
                        else:
                            message_buffer.add_tool_call(tool_call.name, tool_call.args)

                # Update reports and agent status based on chunk content
                # Analyst Team Reports
                if "macro_report" in chunk and chunk["macro_report"]:
                    message_buffer.update_report_section(
                        "macro_report", chunk["macro_report"]
                    )
                    message_buffer.update_agent_status("Macro Economist", "completed")
                    if any(a.value == "market" for a in selections["analysts"]):
                        message_buffer.update_agent_status(
                            "Market Analyst", "in_progress"
                        )

                if "market_report" in chunk and chunk["market_report"]:
                    message_buffer.update_report_section(
                        "market_report", chunk["market_report"]
                    )
                    message_buffer.update_agent_status("Market Analyst", "completed")
                    # Set next analyst to in_progress
                    if "social" in selections["analysts"]:
                        message_buffer.update_agent_status(
                            "Social Analyst", "in_progress"
                        )

                if "sentiment_report" in chunk and chunk["sentiment_report"]:
                    message_buffer.update_report_section(
                        "sentiment_report", chunk["sentiment_report"]
                    )
                    message_buffer.update_agent_status("Social Analyst", "completed")
                    # Set next analyst to in_progress
                    if "news" in selections["analysts"]:
                        message_buffer.update_agent_status(
                            "News Analyst", "in_progress"
                        )

                if "news_report" in chunk and chunk["news_report"]:
                    message_buffer.update_report_section(
                        "news_report", chunk["news_report"]
                    )
                    message_buffer.update_agent_status("News Analyst", "completed")
                    # Set next analyst to in_progress
                    if "fundamentals" in selections["analysts"]:
                        message_buffer.update_agent_status(
                            "Fundamentals Analyst", "in_progress"
                        )

                if "fundamentals_report" in chunk and chunk["fundamentals_report"]:
                    message_buffer.update_report_section(
                        "fundamentals_report", chunk["fundamentals_report"]
                    )
                    message_buffer.update_agent_status(
                        "Fundamentals Analyst", "completed"
                    )
                    # Set all research team members to in_progress
                    update_research_team_status("in_progress")

                if (
                    "alternative_data_report" in chunk
                    and chunk["alternative_data_report"]
                ):
                    message_buffer.update_report_section(
                        "alternative_data_report", chunk["alternative_data_report"]
                    )
                    message_buffer.update_agent_status(
                        "Alternative Data Analyst", "completed"
                    )
                    update_research_team_status("in_progress")

                # Research Team - Handle Investment Debate State
                if (
                    "investment_debate_state" in chunk
                    and chunk["investment_debate_state"]
                ):
                    debate_state = chunk["investment_debate_state"]

                    # Update Bull Researcher status and report
                    if "bull_history" in debate_state and debate_state["bull_history"]:
                        # Keep all research team members in progress
                        update_research_team_status("in_progress")
                        # Extract latest bull response
                        bull_responses = debate_state["bull_history"].split("\n")
                        latest_bull = bull_responses[-1] if bull_responses else ""
                        if latest_bull:
                            message_buffer.add_message("Reasoning", latest_bull)
                            # Update research report with bull's latest analysis
                            message_buffer.update_report_section(
                                "investment_plan",
                                f"### Bull Researcher Analysis\n{latest_bull}",
                            )

                    # Update Bear Researcher status and report
                    if "bear_history" in debate_state and debate_state["bear_history"]:
                        # Keep all research team members in progress
                        update_research_team_status("in_progress")
                        # Extract latest bear response
                        bear_responses = debate_state["bear_history"].split("\n")
                        latest_bear = bear_responses[-1] if bear_responses else ""
                        if latest_bear:
                            message_buffer.add_message("Reasoning", latest_bear)
                            # Update research report with bear's latest analysis
                            message_buffer.update_report_section(
                                "investment_plan",
                                f"{message_buffer.report_sections['investment_plan']}\n\n### Bear Researcher Analysis\n{latest_bear}",
                            )

                    # Update Research Manager status and final decision
                    if (
                        "judge_decision" in debate_state
                        and debate_state["judge_decision"]
                    ):
                        # Keep all research team members in progress until final decision
                        update_research_team_status("in_progress")
                        message_buffer.add_message(
                            "Reasoning",
                            f"Research Manager: {debate_state['judge_decision']}",
                        )
                        # Update research report with final decision
                        message_buffer.update_report_section(
                            "investment_plan",
                            f"{message_buffer.report_sections['investment_plan']}\n\n### Research Manager Decision\n{debate_state['judge_decision']}",
                        )
                        # Mark all research team members as completed
                        update_research_team_status("completed")
                        # Set first risk analyst to in_progress
                        message_buffer.update_agent_status(
                            "Risky Analyst", "in_progress"
                        )

                # Trading Team
                if (
                    "trader_investment_plan" in chunk
                    and chunk["trader_investment_plan"]
                ):
                    message_buffer.update_report_section(
                        "trader_investment_plan", chunk["trader_investment_plan"]
                    )
                    # Set first risk analyst to in_progress
                    message_buffer.update_agent_status("Risk Quant Analyst", "in_progress")

                if "risk_quant_report" in chunk and chunk["risk_quant_report"]:
                    message_buffer.update_report_section(
                        "risk_quant_report", chunk["risk_quant_report"]
                    )
                    message_buffer.update_agent_status("Risk Quant Analyst", "completed")
                    message_buffer.update_agent_status("Risky Analyst", "in_progress")

                # Risk Management Team - Handle Risk Debate State
                if "risk_debate_state" in chunk and chunk["risk_debate_state"]:
                    risk_state = chunk["risk_debate_state"]

                    # Update Risky Analyst status and report
                    if (
                        "current_risky_response" in risk_state
                        and risk_state["current_risky_response"]
                    ):
                        message_buffer.update_agent_status(
                            "Risky Analyst", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Risky Analyst: {risk_state['current_risky_response']}",
                        )
                        # Update risk report with risky analyst's latest analysis only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Risky Analyst Analysis\n{risk_state['current_risky_response']}",
                        )

                    # Update Safe Analyst status and report
                    if (
                        "current_safe_response" in risk_state
                        and risk_state["current_safe_response"]
                    ):
                        message_buffer.update_agent_status(
                            "Safe Analyst", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Safe Analyst: {risk_state['current_safe_response']}",
                        )
                        # Update risk report with safe analyst's latest analysis only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Safe Analyst Analysis\n{risk_state['current_safe_response']}",
                        )

                    # Update Neutral Analyst status and report
                    if (
                        "current_neutral_response" in risk_state
                        and risk_state["current_neutral_response"]
                    ):
                        message_buffer.update_agent_status(
                            "Neutral Analyst", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Neutral Analyst: {risk_state['current_neutral_response']}",
                        )
                        # Update risk report with neutral analyst's latest analysis only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Neutral Analyst Analysis\n{risk_state['current_neutral_response']}",
                        )

                    # Update Portfolio Manager status and final decision
                    if "judge_decision" in risk_state and risk_state["judge_decision"]:
                        message_buffer.update_agent_status(
                            "Portfolio Manager", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Portfolio Manager: {risk_state['judge_decision']}",
                        )
                        # Update risk report with final decision only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Portfolio Manager Decision\n{risk_state['judge_decision']}",
                        )
                        # Mark risk analysts as completed
                        message_buffer.update_agent_status("Risky Analyst", "completed")
                        message_buffer.update_agent_status("Safe Analyst", "completed")
                        message_buffer.update_agent_status(
                            "Neutral Analyst", "completed"
                        )
                        message_buffer.update_agent_status(
                            "Portfolio Manager", "completed"
                        )
                        message_buffer.update_agent_status(
                            "Execution Strategist", "in_progress"
                        )

                if "execution_plan" in chunk and chunk["execution_plan"]:
                    message_buffer.update_report_section(
                        "execution_plan", chunk["execution_plan"]
                    )
                    message_buffer.update_agent_status(
                        "Execution Strategist", "completed"
                    )
                    message_buffer.update_agent_status(
                        "Compliance Officer", "in_progress"
                    )

                if "compliance_report" in chunk and chunk["compliance_report"]:
                    message_buffer.update_report_section(
                        "compliance_report", chunk["compliance_report"]
                    )
                    message_buffer.update_agent_status(
                        "Compliance Officer", "completed"
                    )

                message_buffer.update_cost_summary(graph.cost_tracker.summary())
                now = time.time()
                if now - last_market_refresh > 30:
                    message_buffer.update_market_snapshot(
                        fetch_market_snapshot(selections["ticker"])
                    )
                    last_market_refresh = now

                # Update the display
                update_display(layout)

            trace.append(chunk)

        # Get final state and decision
        final_state = trace[-1]
        decision = graph.process_signal(final_state["final_trade_decision"])

        message_buffer.update_cost_summary(final_state.get("cost_statistics"))
        message_buffer.update_positions_snapshot(fetch_positions_snapshot())
        message_buffer.update_account_snapshot(fetch_account_snapshot())
        message_buffer.update_market_snapshot(fetch_market_snapshot(selections["ticker"]))

        # Update all agent statuses to completed
        for agent in message_buffer.agent_status:
            message_buffer.update_agent_status(agent, "completed")

        message_buffer.add_message(
            "Analysis", f"Completed analysis for {selections['analysis_date']}"
        )

        # Update final report sections
        for section in message_buffer.report_sections.keys():
            if section in final_state:
                message_buffer.update_report_section(section, final_state[section])

        # Display the complete final report
        display_complete_report(final_state)
        try:
            html_path = generate_html_report(
                final_state,
                selections,
                report_dir,
            )
            if html_path:
                console.print(
                    f"[green]Saved HTML report to {html_path}[/green]"
                )
        except Exception as exc:  # pragma: no cover - reporting helper shouldn't halt CLI
            console.print(
                f"[red]Failed to generate HTML report: {exc}[/red]"
            )

        prompt_trade_execution(final_state, config)

        update_display(layout)


@app.command()
def analyze():
    run_analysis()


if __name__ == "__main__":
    app()
