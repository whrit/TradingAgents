from __future__ import annotations

import datetime as dt
import json
import math
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

import yfinance as yf
from markdown import markdown

from tradingagents.dataflows.interface import route_to_vendor


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title>TradingAgents Report — {ticker} ({analysis_date})</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
        :root {{
            color-scheme: dark;
            --bg: #05060a;
            --panel: #0f172a;
            --border: #1e293b;
            --accent: #3b82f6;
            --accent-faded: rgba(59,130,246,0.15);
            --muted: #94a3b8;
        }}
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            padding: 2rem;
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: radial-gradient(circle at top, rgba(59,130,246,0.18), transparent 35%), var(--bg);
            color: #e2e8f0;
        }}
        header {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        header h1 {{
            margin: 0;
            font-size: 2rem;
        }}
        .meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.75rem;
        }}
        .meta span {{
            display: block;
            font-size: 0.78rem;
            color: var(--muted);
        }}
        .meta strong {{
            font-size: 1rem;
        }}
        .meta div {{
            background: rgba(15,23,42,0.7);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 0.85rem;
        }}
        .grid {{
            display: grid;
            gap: 1.5rem;
        }}
        .grid.two {{
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }}
        .card {{
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 1.5rem;
            box-shadow: 0 20px 45px rgba(5,10,30,0.55);
        }}
        h2 {{
            margin-top: 0;
            color: #f8fafc;
            font-size: 1.4rem;
        }}
        .chart-stack canvas {{
            margin-top: 0.5rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.5rem;
            font-size: 0.9rem;
        }}
        th, td {{
            padding: 0.4rem 0.35rem;
            text-align: left;
        }}
        th {{
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            color: #d1d5db;
            border-bottom: 1px solid var(--border);
        }}
        td {{
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        .muted {{
            color: var(--muted);
            font-size: 0.9rem;
        }}
        .stats-list {{
            list-style: none;
            padding: 0;
            margin: 1rem 0 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.75rem;
        }}
        .stats-list li {{
            background: var(--accent-faded);
            border-radius: 12px;
            padding: 0.75rem;
        }}
        .stats-list span {{
            display: block;
            font-size: 0.75rem;
            color: var(--muted);
        }}
        .stats-list strong {{
            font-size: 1rem;
        }}
        .highlight-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
        }}
        .highlight {{
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 1rem;
            background: rgba(15,23,42,0.6);
        }}
        .highlight h3 {{
            margin-top: 0;
            margin-bottom: 0.35rem;
            font-size: 1rem;
        }}
        section.narratives {{
            margin-top: 2rem;
            line-height: 1.65;
        }}
        section.narratives h2 {{
            margin-bottom: 0.5rem;
        }}
        section.narratives section {{
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }}
        code {{
            background: rgba(255,255,255,0.05);
            padding: 0.15rem 0.25rem;
            border-radius: 4px;
        }}
        canvas {{
            max-width: 100%;
        }}
    </style>
</head>
<body>
    <header>
        <div>
            <h1>{ticker} — Strategy Review</h1>
            <p class="muted">Analysis date {analysis_date} • Generated {generated_at}</p>
        </div>
        <div class="meta">
            <div><span>Research Depth</span><strong>{research_depth}</strong></div>
            <div><span>LLM Provider</span><strong>{llm_provider}</strong></div>
            <div><span>Instrument Preference</span><strong>{instrument_choice}</strong></div>
            <div><span>Trade Summary</span><strong>{trade_summary}</strong></div>
        </div>
    </header>

    <section class="grid two">
        <article class="card">
            <h2>Price Action & Volatility</h2>
            {price_stats_html}
            <div class="chart-stack">
                <canvas id="priceChart" height="200"></canvas>
                <canvas id="volumeChart" height="120"></canvas>
            </div>
        </article>
        <article class="card">
            <h2>Options & Volatility Snapshot</h2>
            {options_metrics_html}
            <div class="chart-stack">
                <canvas id="optionsChart" height="200"></canvas>
                <canvas id="optionIvChart" height="140"></canvas>
            </div>
            {options_summary_html}
            {options_table_html}
        </article>
    </section>

    <section class="grid two" style="margin-top:1.5rem;">
        <article class="card">
            <h2>Payoff Scenarios</h2>
            <canvas id="payoffChart" height="200"></canvas>
            <p class="muted">{payoff_summary}</p>
        </article>
        <article class="card">
            <h2>Risk, Stress & Limits</h2>
            {risk_tables_html}
        </article>
    </section>

    <section class="card" style="margin-top:1.5rem;">
        <h2>Highlights & Narratives</h2>
        {news_highlights_html}
    </section>

    <section class="card" style="margin-top:1.5rem;">
        <h2>Cost Summary</h2>
        {cost_html}
    </section>

    <section class="narratives">
        {sections_html}
    </section>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const priceLabels = {price_chart_labels};
        const priceValues = {price_chart_prices};
        const volumeLabels = {volume_chart_labels};
        const volumeValues = {volume_chart_values};
        const priceCanvas = document.getElementById("priceChart");
        if (priceLabels.length && priceValues.length) {{
            new Chart(priceCanvas, {{
                type: "line",
                data: {{
                    labels: priceLabels,
                    datasets: [{{
                        label: "Close",
                        data: priceValues,
                        borderColor: "{chart_accent}",
                        backgroundColor: "{chart_accent_faded}",
                        fill: true,
                        tension: 0.25,
                        pointRadius: 0,
                    }}],
                }},
                options: {{
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        x: {{ ticks: {{ color: "#9ca3af" }} }},
                        y: {{ ticks: {{ color: "#9ca3af" }} }},
                    }},
                }},
            }});
        }} else {{
            const placeholder = document.createElement("p");
            placeholder.className = "muted";
            placeholder.textContent = "Price data unavailable.";
            priceCanvas.replaceWith(placeholder);
        }}

        const volumeCanvas = document.getElementById("volumeChart");
        if (volumeCanvas && volumeLabels.length && volumeValues.length) {{
            new Chart(volumeCanvas, {{
                type: "bar",
                data: {{
                    labels: volumeLabels,
                    datasets: [{{
                        label: "Volume",
                        data: volumeValues,
                        backgroundColor: "rgba(99,102,241,0.4)",
                        borderRadius: 4,
                    }}],
                }},
                options: {{
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        x: {{ display: false }},
                        y: {{ ticks: {{ color: "#9ca3af" }} }},
                    }},
                }},
            }});
        }} else if (volumeCanvas) {{ volumeCanvas.remove(); }}

        const optionStrikes = {options_chart_labels};
        const callOpenInterest = {options_chart_calls};
        const putOpenInterest = {options_chart_puts};
        const optionIvLabels = {option_iv_labels};
        const optionIvCalls = {option_iv_calls};
        const optionIvPuts = {option_iv_puts};
        const optionCanvas = document.getElementById("optionsChart");
        if (optionStrikes.length && (callOpenInterest.length || putOpenInterest.length)) {{
            new Chart(optionCanvas, {{
                type: "bar",
                data: {{
                    labels: optionStrikes,
                    datasets: [
                        {{
                            label: "Calls OI",
                            data: callOpenInterest,
                            backgroundColor: "{chart_accent}",
                        }},
                        {{
                            label: "Puts OI",
                            data: putOpenInterest,
                            backgroundColor: "#f97316",
                        }},
                    ],
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        x: {{ ticks: {{ color: "#9ca3af" }} }},
                        y: {{ ticks: {{ color: "#9ca3af" }} }},
                    }},
                }},
            }});
        }} else {{
            const placeholder = document.createElement("p");
            placeholder.className = "muted";
            placeholder.textContent = "Options snapshot unavailable.";
            optionCanvas.replaceWith(placeholder);
        }}

        const optionIvCanvas = document.getElementById("optionIvChart");
        if (optionIvCanvas && optionIvLabels.length && (optionIvCalls.length || optionIvPuts.length)) {{
            new Chart(optionIvCanvas, {{
                type: "line",
                data: {{
                    labels: optionIvLabels,
                    datasets: [
                        {{ label: "Call IV", data: optionIvCalls, borderColor: "#f472b6", tension: 0.3 }},
                        {{ label: "Put IV", data: optionIvPuts, borderColor: "#14b8a6", tension: 0.3 }},
                    ],
                }},
                options: {{
                    scales: {{
                        x: {{ ticks: {{ color: "#9ca3af" }} }},
                        y: {{ ticks: {{ color: "#9ca3af" }} }},
                    }},
                }},
            }});
        }} else if (optionIvCanvas) {{ optionIvCanvas.remove(); }}

        const payoffLabels = {payoff_labels};
        const payoffValues = {payoff_values};
        const payoffCanvas = document.getElementById("payoffChart");
        if (payoffLabels.length && payoffValues.length) {{
            new Chart(payoffCanvas, {{
                type: "line",
                data: {{
                    labels: payoffLabels,
                    datasets: [{{
                        label: "Scenario P&L",
                        data: payoffValues,
                        borderColor: "#10b981",
                        backgroundColor: "rgba(16,185,129,0.2)",
                        fill: true,
                        tension: 0.15,
                    }}],
                }},
                options: {{
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        x: {{ ticks: {{ color: "#9ca3af" }} }},
                        y: {{ ticks: {{ color: "#9ca3af" }} }},
                    }},
                }},
            }});
        }} else {{
            const placeholder = document.createElement("p");
            placeholder.className = "muted";
            placeholder.textContent = "No executable trade available.";
            payoffCanvas.replaceWith(placeholder);
        }}
    </script>
</body>
</html>
"""

AGENT_SECTIONS = [
    ("Macro Economist", "macro_report"),
    ("Market Analyst", "market_report"),
    ("Social Analyst", "sentiment_report"),
    ("News Analyst", "news_report"),
    ("Fundamentals Analyst", "fundamentals_report"),
    ("Alternative Data Analyst", "alternative_data_report"),
    ("Research Manager Decision", "investment_plan"),
    ("Trader", "trader_investment_plan"),
    ("Risk Quant Analyst", "risk_quant_report"),
    ("Portfolio Manager", "final_trade_decision"),
    ("Execution Strategist", "execution_plan"),
    ("Compliance Officer", "compliance_report"),
]


def generate_html_report(
    final_state: Dict[str, Any],
    metadata: Optional[Dict[str, Any]],
    report_dir: Path,
) -> Optional[Path]:
    """
    Build a standalone HTML report that mirrors the CLI experience with charts and tables.
    """
    metadata = metadata or {}

    ticker = (
        metadata.get("ticker")
        or final_state.get("company_of_interest")
        or "UNKNOWN"
    ).upper()
    analysis_date = metadata.get("analysis_date") or final_state.get("trade_date")
    analysis_date = (analysis_date or dt.date.today().isoformat()).replace("/", "-")

    price_data = _collect_price_data(ticker)
    options_data = _collect_options_data(ticker)
    payoff_data = _build_payoff_dataset(
        final_state,
        price_data.get("latest_price"),
        options_data.get("snapshot"),
    )
    risk_metrics = _extract_risk_metrics(final_state.get("risk_metrics_json"))

    price_chart_labels = json.dumps(price_data.get("labels") or [])
    price_chart_prices = json.dumps(price_data.get("prices") or [])
    volume_chart_labels = json.dumps(price_data.get("volume_labels") or [])
    volume_chart_values = json.dumps(price_data.get("volume_values") or [])
    options_chart_labels = json.dumps(options_data.get("chart_strikes") or [])
    options_chart_calls = json.dumps(options_data.get("chart_calls") or [])
    options_chart_puts = json.dumps(options_data.get("chart_puts") or [])
    option_iv_labels = json.dumps(options_data.get("iv_labels") or [])
    option_iv_calls = json.dumps(options_data.get("iv_calls") or [])
    option_iv_puts = json.dumps(options_data.get("iv_puts") or [])
    payoff_labels = json.dumps((payoff_data or {}).get("labels") or [])
    payoff_values = json.dumps((payoff_data or {}).get("values") or [])

    html_output = HTML_TEMPLATE.format(
        ticker=escape(ticker),
        analysis_date=escape(analysis_date),
        generated_at=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        research_depth=metadata.get("research_depth", "n/a"),
        llm_provider=escape(
            f"{(metadata.get('llm_provider') or '').upper()} | "
            f"{metadata.get('deep_thinker') or 'deep'} / "
            f"{metadata.get('shallow_thinker') or 'quick'}"
        ),
        instrument_choice=escape(
            (metadata.get("instrument_type") or "shares").replace("_", " ").title()
        ),
        trade_summary=escape(_summarize_trade(final_state)),
        price_stats_html=_render_price_stats(price_data),
        options_metrics_html=_render_options_metrics(options_data),
        options_summary_html=_render_options_summary(options_data),
        options_table_html=_render_options_tables(options_data),
        news_highlights_html=_render_highlights(final_state),
        payoff_summary=escape(
            (payoff_data or {}).get("details", "No executable trade available.")
        ),
        risk_tables_html=_render_risk_tables(risk_metrics),
        cost_html=_render_cost_table(final_state.get("cost_statistics")),
        sections_html=_render_agent_sections(final_state),
        price_chart_labels=price_chart_labels,
        price_chart_prices=price_chart_prices,
        volume_chart_labels=volume_chart_labels,
        volume_chart_values=volume_chart_values,
        options_chart_labels=options_chart_labels,
        options_chart_calls=options_chart_calls,
        options_chart_puts=options_chart_puts,
        option_iv_labels=option_iv_labels,
        option_iv_calls=option_iv_calls,
        option_iv_puts=option_iv_puts,
        payoff_labels=payoff_labels,
        payoff_values=payoff_values,
        chart_accent="#3b82f6",
        chart_accent_faded="rgba(59,130,246,0.18)",
    )

    report_dir.mkdir(parents=True, exist_ok=True)
    output_path = report_dir / f"{ticker}_{analysis_date}_report.html"
    output_path.write_text(html_output, encoding="utf-8")
    return output_path


def _collect_price_data(ticker: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    try:
        hist = yf.Ticker(ticker).history(period="3mo", interval="1d")
    except Exception:
        return data

    closes = hist.get("Close")
    if closes is None or closes.dropna().empty:
        return data

    closes = closes.dropna()
    data["labels"] = [idx.strftime("%Y-%m-%d") for idx in closes.index]
    data["prices"] = [round(float(value), 2) for value in closes]
    data["latest_price"] = round(float(closes.iloc[-1]), 2)
    volumes = hist.get("Volume")
    if volumes is not None and not volumes.dropna().empty:
        vol = volumes.dropna()
        data["volume_labels"] = [idx.strftime("%Y-%m-%d") for idx in vol.index]
        data["volume_values"] = [int(v) for v in vol]
        data["avg_volume"] = int(vol.mean())
    else:
        data["volume_labels"] = []
        data["volume_values"] = []

    one_month_window = min(len(closes) - 1, 21)
    data["changes"] = {
        "1D": _calc_pct_move(closes, 1),
        "5D": _calc_pct_move(closes, 5),
        "1M": _calc_pct_move(closes, one_month_window if one_month_window > 0 else 0),
    }

    returns = closes.pct_change().dropna()
    if not returns.empty:
        data["volatility"] = float(returns.std() * math.sqrt(252) * 100)
    if len(closes) > 1:
        prev = float(closes.iloc[-2])
        change = data["latest_price"] - prev
        data["daily_change"] = change
        data["daily_change_pct"] = ((data["latest_price"] / prev) - 1) * 100 if prev else None
    data["period_high"] = float(closes.max())
    data["period_low"] = float(closes.min())
    return data


def _calc_pct_move(series, window: int) -> Optional[float]:
    if window <= 0 or len(series) <= window:
        return None
    prev = float(series.iloc[-window - 1])
    latest = float(series.iloc[-1])
    if prev == 0:
        return None
    return ((latest / prev) - 1) * 100


def _collect_options_data(ticker: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {"snapshot": {}}
    try:
        raw = route_to_vendor("get_options_data", ticker.upper(), None, 6)
        snapshot = json.loads(raw) if raw else {}
    except Exception:
        return data

    data["snapshot"] = snapshot or {}
    calls = snapshot.get("calls") or []
    puts = snapshot.get("puts") or []
    simplified_calls = _simplify_option_rows(calls)
    simplified_puts = _simplify_option_rows(puts)

    data["calls"] = simplified_calls
    data["puts"] = simplified_puts
    data["expiry"] = snapshot.get("expiry")
    data["call_oi"] = sum(row.get("oi", 0) or 0 for row in simplified_calls)
    data["put_oi"] = sum(row.get("oi", 0) or 0 for row in simplified_puts)

    call_iv = [row.get("iv") for row in simplified_calls if row.get("iv") is not None]
    put_iv = [row.get("iv") for row in simplified_puts if row.get("iv") is not None]
    data["avg_call_iv"] = float(sum(call_iv) / len(call_iv)) if call_iv else None
    data["avg_put_iv"] = float(sum(put_iv) / len(put_iv)) if put_iv else None
    data["call_put_ratio"] = (
        float(data["call_oi"]) / float(data["put_oi"]) if data["put_oi"] else None
    )

    chart_series = _build_option_chart_series(simplified_calls, simplified_puts)
    data.update(chart_series)
    return data


def _simplify_option_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    simplified = []
    for row in rows[:5]:
        strike = row.get("strike")
        last = row.get("lastPrice") or row.get("ask") or row.get("bid")
        iv = row.get("impliedVolatility")
        simplified.append(
            {
                "contract": row.get("contractSymbol", "—"),
                "strike": float(strike) if strike is not None else None,
                "last": float(last) if last is not None else None,
                "iv": float(iv) * 100 if iv is not None else None,
                "oi": int(row.get("openInterest") or 0),
            }
        )
    return simplified


def _build_option_chart_series(calls, puts):
    strikes: Dict[float, Dict[str, float]] = {}
    for row in calls:
        strike = row.get("strike")
        if strike is None:
            continue
        strikes.setdefault(strike, {})["call"] = row.get("oi", 0)
        if row.get("iv") is not None:
            strikes[strike]["call_iv"] = row.get("iv")
    for row in puts:
        strike = row.get("strike")
        if strike is None:
            continue
        strikes.setdefault(strike, {})["put"] = row.get("oi", 0)
        if row.get("iv") is not None:
            strikes[strike]["put_iv"] = row.get("iv")

    sorted_strikes = sorted(strikes.keys())
    return {
        "chart_strikes": [f"{strike:.0f}" for strike in sorted_strikes],
        "chart_calls": [strikes[strike].get("call", 0) for strike in sorted_strikes],
        "chart_puts": [strikes[strike].get("put", 0) for strike in sorted_strikes],
        "iv_labels": [f"{strike:.0f}" for strike in sorted_strikes],
        "iv_calls": [strikes[strike].get("call_iv") or 0 for strike in sorted_strikes],
        "iv_puts": [strikes[strike].get("put_iv") or 0 for strike in sorted_strikes],
    }


def _build_payoff_dataset(final_state, ref_price, snapshot):
    trade = final_state.get("proposed_trade")
    if not trade:
        return None

    quantity = float(trade.get("quantity") or 0)
    if quantity <= 0:
        return None

    action = (trade.get("action") or "buy").lower()
    direction = 1 if action == "buy" else -1
    instrument = (trade.get("instrument_type") or "shares").lower()
    steps = [-0.1, -0.05, 0.0, 0.05, 0.1]

    if instrument == "shares":
        if not ref_price:
            return None
        labels, values = [], []
        for move in steps:
            scenario_price = ref_price * (1 + move)
            pnl = direction * quantity * (scenario_price - ref_price)
            labels.append(f"{move * 100:+.0f}%")
            values.append(round(pnl, 2))
        details = f"{action.upper()} {quantity:.0f} shares @ ${ref_price:,.2f}"
        return {"labels": labels, "values": values, "details": details}

    derivative = trade.get("derivative_details") or _infer_option_from_snapshot(
        snapshot, action
    )
    if not derivative:
        return None
    strike = derivative.get("strike")
    premium = derivative.get("premium")
    if strike is None or premium is None or ref_price is None:
        return None

    opt_type = derivative.get("option_type", "call")
    multiplier = derivative.get("multiplier", 100)
    labels, values = [], []
    for move in steps:
        scenario_price = ref_price * (1 + move)
        if opt_type == "call":
            intrinsic = max(0.0, scenario_price - strike)
        else:
            intrinsic = max(0.0, strike - scenario_price)
        payoff = (intrinsic - premium) * multiplier * quantity * direction
        labels.append(f"{move * 100:+.0f}%")
        values.append(round(payoff, 2))
    details = (
        f"{opt_type.title()} {quantity:.0f}x {strike:.2f} strike "
        f"premium {premium:.2f}"
    )
    return {"labels": labels, "values": values, "details": details}


def _infer_option_from_snapshot(snapshot, preferred_side: str):
    if not snapshot:
        return None
    collection = snapshot.get("calls" if preferred_side == "buy" else "puts") or []
    if not collection:
        return None
    candidate = collection[0]
    return {
        "option_type": "call" if preferred_side == "buy" else "put",
        "strike": candidate.get("strike"),
        "premium": candidate.get("lastPrice")
        or candidate.get("ask")
        or candidate.get("bid"),
        "multiplier": 100,
    }


def _extract_risk_metrics(blob) -> Dict[str, Any]:
    if not blob:
        return {}
    if isinstance(blob, str):
        try:
            metrics = json.loads(blob)
        except json.JSONDecodeError:
            return {}
    elif isinstance(blob, dict):
        metrics = blob
    else:
        return {}

    var_rows = []
    for source, entries in (metrics.get("var") or {}).items():
        for conf, stats in (entries or {}).items():
            var_rows.append(
                {
                    "label": f"{source.title()} {conf}",
                    "var": (stats or {}).get("value"),
                    "es": (stats or {}).get("expected_shortfall"),
                }
            )

    stress_rows = []
    for key, value in (metrics.get("stress") or {}).items():
        label = key.replace("_", " ").title()
        stress_rows.append(
            {
                "label": label,
                "value": value,
                "is_pct": key.endswith("_pct"),
                "is_cost": "cost" in key,
            }
        )

    sizing_rows = []
    sizing = metrics.get("position_sizing") or {}
    if sizing:
        max_value = max(sizing.values())
        for key, value in sizing.items():
            sizing_rows.append(
                {
                    "label": key.replace("_", " ").title(),
                    "value": value,
                    "ratio": value / max_value if max_value else 0,
                }
            )

    limits_rows = metrics.get("risk_limits") or []

    return {
        "var": var_rows,
        "stress": stress_rows,
        "sizing": sizing_rows,
        "limits": limits_rows,
    }


def _render_price_stats(data: Dict[str, Any]) -> str:
    if not data:
        return "<p class='muted'>Price history unavailable.</p>"
    change = data.get("daily_change")
    change_pct = data.get("daily_change_pct")
    rows = [
        f"<li><span>Last Close</span><strong>{_format_currency(data.get('latest_price'))}</strong></li>",
        f"<li><span>Daily Change</span><strong>{_format_currency(change)} ({_format_percent(change_pct)})</strong></li>",
        f"<li><span>5D Return</span><strong>{_format_percent((data.get('changes') or {}).get('5D'))}</strong></li>",
        f"<li><span>Monthly Range</span><strong>{_format_currency(data.get('period_low'))} → {_format_currency(data.get('period_high'))}</strong></li>",
        f"<li><span>Avg Volume</span><strong>{_format_number(data.get('avg_volume'))}</strong></li>",
        f"<li><span>Realized Vol (ann.)</span><strong>{_format_percent(data.get('volatility'))}</strong></li>",
    ]
    return f"<ul class='stats-list'>{''.join(rows)}</ul>"


def _render_options_metrics(data: Dict[str, Any]) -> str:
    if not data:
        return "<p class='muted'>Options data unavailable.</p>"
    rows = [
        ("Next Expiry", data.get("expiry") or "—"),
        ("Call/Put OI", f"{data.get('call_put_ratio'):.2f}" if data.get("call_put_ratio") else "—"),
        ("Avg Call IV", _format_percent(data.get("avg_call_iv"))),
        ("Avg Put IV", _format_percent(data.get("avg_put_iv"))),
        ("Total Call OI", _format_number(data.get("call_oi"))),
        ("Total Put OI", _format_number(data.get("put_oi"))),
    ]
    items = [f"<li><span>{escape(label)}</span><strong>{value}</strong></li>" for label, value in rows]
    return f"<ul class='stats-list'>{''.join(items)}</ul>"


def _render_options_summary(data: Dict[str, Any]) -> str:
    if not data.get("calls") and not data.get("puts"):
        return "<p class='muted'>Options snapshot unavailable.</p>"
    summary = [
        ("Expiry", data.get("expiry") or "n/a"),
        ("Avg Call IV", _format_percent(data.get("avg_call_iv"))),
        ("Avg Put IV", _format_percent(data.get("avg_put_iv"))),
        ("Call OI", f"{data.get('call_oi', 0):,}"),
        ("Put OI", f"{data.get('put_oi', 0):,}"),
        ("Call/Put OI", f"{data.get('call_put_ratio'):.2f}" if data.get("call_put_ratio") else "—"),
    ]
    blocks = "".join(
        f"<div><span>{escape(label)}</span><strong>{escape(str(value))}</strong></div>"
        for label, value in summary
    )
    return f"<div class='meta' style='margin-bottom:0.75rem;'>{blocks}</div>"


def _render_options_tables(data: Dict[str, Any]) -> str:
    if not data.get("calls") and not data.get("puts"):
        return ""
    tables = []
    if data.get("calls"):
        tables.append(_build_option_table("Top Calls", data["calls"]))
    if data.get("puts"):
        tables.append(_build_option_table("Top Puts", data["puts"]))
    return f"<div class='grid two'>{''.join(tables)}</div>"


def _build_option_table(title: str, rows: List[Dict[str, Any]]) -> str:
    header = (
        "<table>"
        "<thead><tr><th>Contract</th><th>Strike</th><th>Last</th><th>IV</th><th>OI</th></tr></thead>"
        "<tbody>"
    )
    body = ""
    for row in rows:
        body += (
            "<tr>"
            f"<td>{escape(str(row.get('contract', '—')))}</td>"
            f"<td>{_format_currency(row.get('strike'))}</td>"
            f"<td>{_format_currency(row.get('last'))}</td>"
            f"<td>{_format_percent(row.get('iv'))}</td>"
            f"<td>{int(row.get('oi', 0)):,}</td>"
            "</tr>"
        )
    footer = "</tbody></table>"
    return f"<div><h3>{escape(title)}</h3>{header}{body}{footer}</div>"


def _render_risk_tables(metrics: Dict[str, Any]) -> str:
    if not metrics:
        return "<p class='muted'>Risk metrics unavailable.</p>"
    tables = []
    if metrics.get("var"):
        rows = []
        for row in metrics["var"]:
            var_value = row.get("var")
            es_value = row.get("es")
            rows.append(
                "<tr>"
                f"<td>{escape(row['label'])}</td>"
                f"<td>{_format_percent(var_value * 100 if var_value is not None else None)}</td>"
                f"<td>{_format_percent(es_value * 100 if es_value is not None else None)}</td>"
                "</tr>"
            )
        table = (
            "<div>"
            "<h3>Value at Risk</h3>"
            "<table><thead><tr><th>Type</th><th>VaR</th><th>ES</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            "</div>"
        )
        tables.append(table)
    if metrics.get("stress"):
        rows = []
        for row in metrics["stress"]:
            value = row.get("value")
            if row.get("is_pct"):
                display = _format_percent(value * 100 if value is not None else None)
            elif row.get("is_cost"):
                display = _format_currency(value)
            else:
                display = _format_number(value)
            rows.append(
                f"<tr><td>{escape(row['label'])}</td><td>{display}</td></tr>"
            )
        table = (
            "<div>"
            "<h3>Stress Tests</h3>"
            "<table><thead><tr><th>Scenario</th><th>Impact</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            "</div>"
        )
        tables.append(table)
    if metrics.get("sizing"):
        rows = "".join(
            f"<tr><td>{escape(row['label'])}</td>"
            f"<td>{_format_currency(row.get('value'))}</td>"
            f"<td><div style='background:rgba(248,113,113,0.2);border-radius:6px;height:6px;'>"
            f"<div style='background:#f43f5e;width:{row.get('ratio',0)*100:.0f}%;height:6px;border-radius:6px;'></div>"
            "</div></td></tr>"
            for row in metrics["sizing"]
        )
        table = (
            "<div>"
            "<h3>Position Sizing</h3>"
            "<table><thead><tr><th>Metric</th><th>Value</th><th>Utilization</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
            "</div>"
        )
        tables.append(table)
    if metrics.get("limits"):
        rows = "".join(
            f"<tr><td>{escape(row.get('metric', 'Metric'))}</td>"
            f"<td>{_format_number(row.get('current'))}</td>"
            f"<td>{_format_number(row.get('limit'))}</td>"
            f"<td>{escape(row.get('status', 'OK'))}</td></tr>"
            for row in metrics["limits"]
        )
        table = (
            "<div>"
            "<h3>Risk Limits</h3>"
            "<table><thead><tr><th>Metric</th><th>Current</th><th>Limit</th><th>Status</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
            "</div>"
        )
        tables.append(table)
    return f"<div class='grid risk'>{''.join(tables)}</div>"


def _render_cost_table(stats: Optional[Dict[str, Any]]) -> str:
    if not stats:
        return "<p class='muted'>Cost data unavailable.</p>"
    currency = stats.get("currency", "USD")
    summary = (
        f"<p>Total Cost: <strong>{stats.get('total_cost', 0.0):,.4f} {currency}</strong> "
        f"• LLM Calls: {stats.get('total_calls', 0)} "
        f"• Tokens: {stats.get('total_input_tokens', 0):,} in / "
        f"{stats.get('total_output_tokens', 0):,} out</p>"
    )
    models_table = _dict_to_table(
        "Model Usage",
        stats.get("models"),
        ("Model", "Calls", "Cost"),
        lambda name, entry: (
            escape(name),
            f"{entry.get('calls', 0):,}",
            f"{entry.get('cost', 0.0):,.4f}",
        ),
    )
    sections_table = _dict_to_table(
        "Pipeline Sections",
        stats.get("sections"),
        ("Section", "Calls", "Cost"),
        lambda name, entry: (
            escape(name),
            f"{entry.get('calls', 0):,}",
            f"{entry.get('cost', 0.0):,.4f}",
        ),
    )
    tables = f"<div class='grid two'>{models_table}{sections_table}</div>"
    return summary + tables


def _dict_to_table(title, data, headers, row_builder):
    if not data:
        return f"<div><h3>{escape(title)}</h3><p class='muted'>No data.</p></div>"
    rows = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row_builder(name, entry)) + "</tr>"
        for name, entry in sorted(data.items())
    )
    header_html = "".join(f"<th>{escape(h)}</th>" for h in headers)
    return (
        f"<div><h3>{escape(title)}</h3>"
        f"<table><thead><tr>{header_html}</tr></thead><tbody>{rows}</tbody></table></div>"
    )


def _render_agent_sections(final_state: Dict[str, Any]) -> str:
    blocks = []
    for title, key in AGENT_SECTIONS:
        block = _markdown_block(title, final_state.get(key))
        if block:
            blocks.append(block)

    research_state = final_state.get("investment_debate_state") or {}
    research_content = []
    if research_state.get("bull_history"):
        research_content.append(f"### Bull Researcher\n{research_state['bull_history']}")
    if research_state.get("bear_history"):
        research_content.append(f"### Bear Researcher\n{research_state['bear_history']}")
    if research_state.get("judge_decision"):
        research_content.append(
            f"### Research Manager Decision\n{research_state['judge_decision']}"
        )
    if research_content:
        blocks.append(
            _markdown_block("Investment Debate Transcript", "\n\n".join(research_content))
        )

    risk_state = final_state.get("risk_debate_state") or {}
    risk_content = []
    if risk_state.get("risky_history"):
        risk_content.append(f"### Risky Analyst\n{risk_state['risky_history']}")
    if risk_state.get("safe_history"):
        risk_content.append(f"### Safe Analyst\n{risk_state['safe_history']}")
    if risk_state.get("neutral_history"):
        risk_content.append(f"### Neutral Analyst\n{risk_state['neutral_history']}")
    if risk_state.get("judge_decision"):
        risk_content.append(
            f"### Portfolio Manager\n{risk_state['judge_decision']}"
        )
    if risk_content:
        blocks.append(
            _markdown_block("Risk Debate Transcript", "\n\n".join(risk_content))
        )

    if not blocks:
        return "<p class='muted'>Agent narratives unavailable.</p>"
    return "".join(blocks)


def _render_highlights(final_state: Dict[str, Any]) -> str:
    sections = [
        ("Macro Outlook", final_state.get("macro_report")),
        ("Market Analysis", final_state.get("market_report")),
        ("News Summary", final_state.get("news_report")),
        ("Sentiment", final_state.get("sentiment_report")),
    ]
    cards = []
    for title, content in sections:
        snippet = _summarize_text(content)
        if not snippet:
            continue
        cards.append(
            f"<div class='highlight'><h3>{escape(title)}</h3><p class='muted'>{snippet}</p></div>"
        )
    if not cards:
        return "<p class='muted'>Narrative snippets unavailable for this run.</p>"
    return f"<div class='highlight-grid'>{''.join(cards)}</div>"


def _markdown_block(title: str, content: Optional[str]) -> str:
    if not content:
        return ""
    rendered = markdown(content, extensions=["extra", "sane_lists"]) if content else ""
    return f"<section><h2>{escape(title)}</h2>{rendered}</section>"


def _summarize_trade(final_state: Dict[str, Any]) -> str:
    trade = final_state.get("proposed_trade")
    if not trade:
        return "No trade proposed"
    action = (trade.get("action") or "hold").upper()
    qty = trade.get("quantity")
    instrument = (trade.get("instrument_type") or "shares").replace("_", " ").title()
    symbol = trade.get("symbol") or trade.get("underlying_symbol") or "—"

    return f"{action} {qty} {instrument} in {symbol}"


def _summarize_text(content: Optional[str], limit: int = 320) -> str:
    if not content:
        return ""
    text = " ".join(content.strip().split())
    if not text:
        return ""
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "…"
    return escape(text)


def _format_currency(value) -> str:
    if value is None:
        return "—"
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"


def _format_percent(value) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return "—"


def _format_number(value) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"
