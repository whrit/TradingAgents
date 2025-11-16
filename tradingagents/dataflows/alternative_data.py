"""
Synthetic alternative data snapshots used by the Alternative Data Analyst.

These values emulate web-traffic scores, satellite utilization, and
credit-card spend trends so that the agent can reason about
non-traditional signals without calling external services.
"""

from datetime import datetime
from textwrap import dedent


ALT_DATA = {
    "AAPL": {
        "as_of": "2025-01-15",
        "web_traffic_index": 118,
        "foot_traffic_delta": 0.07,
        "supply_chain_utilization": 0.82,
        "app_store_downloads": 1.05,
        "card_spend_shift": 0.04,
    },
    "NVDA": {
        "as_of": "2025-01-15",
        "web_traffic_index": 162,
        "foot_traffic_delta": 0.05,
        "supply_chain_utilization": 0.94,
        "data_center_power_usage": 0.11,
        "cloud_gpu_queue": "elevated",
    },
    "MSFT": {
        "as_of": "2025-01-15",
        "web_traffic_index": 132,
        "enterprise_usage_growth": 0.09,
        "azure_capacity": 0.88,
        "copilot_adoption_rate": 0.12,
        "card_spend_shift": 0.03,
    },
}


def get_alternative_data_snapshot(ticker: str) -> str:
    """Return a formatted alternative-data snapshot for the provided ticker."""

    entry = ALT_DATA.get(ticker.upper())
    if not entry:
        return dedent(
            f"""
            No curated alternative data snapshot is available for {ticker.upper()}.
            Reference satellite imagery, credit-card spend trackers, and web-scraped app telemetry
            to infer demand patterns, and explicitly note any assumptions you make.
            """
        ).strip()

    as_of = entry.get("as_of", datetime.utcnow().strftime("%Y-%m-%d"))
    bullet_points = []
    for key, value in entry.items():
        if key == "as_of":
            continue
        label = key.replace("_", " ").title()
        if isinstance(value, float):
            if abs(value) < 1:
                formatted = f"{value * 100:.1f}%"
            else:
                formatted = f"{value:.2f}"
        else:
            formatted = str(value)
        bullet_points.append(f"- {label}: {formatted}")

    summary = "\n".join(bullet_points)
    return dedent(
        f"""
        ### Alternative Data Snapshot ({ticker.upper()}) – as of {as_of}
        {summary}

        Interpret the signals above relative to year-over-year run rates and
        highlight whether they reinforce or contradict traditional financial metrics.
        """
    ).strip()
