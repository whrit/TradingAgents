from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from .alpha_vantage_stock import _fetch_symbol_timeseries

try:  # TA-Lib is required for on-box indicator calculations
    import talib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - handled at runtime
    talib = None  # type: ignore


SUPPORTED_INDICATORS: Dict[str, Tuple[str, str | None]] = {
    "close_50_sma": ("50 SMA", "close"),
    "close_200_sma": ("200 SMA", "close"),
    "close_10_ema": ("10 EMA", "close"),
    "macd": ("MACD", "close"),
    "macds": ("MACD Signal", "close"),
    "macdh": ("MACD Histogram", "close"),
    "rsi": ("RSI", "close"),
    "boll": ("Bollinger Middle", "close"),
    "boll_ub": ("Bollinger Upper Band", "close"),
    "boll_lb": ("Bollinger Lower Band", "close"),
    "atr": ("ATR", None),
    "vwma": ("VWMA", "close"),
}

INDICATOR_DESCRIPTIONS = {
    "close_50_sma": "50 SMA: A medium-term trend indicator. Usage: Identify trend direction and serve as dynamic support/resistance. Tips: It lags price; combine with faster indicators for timely signals.",
    "close_200_sma": "200 SMA: A long-term trend benchmark. Usage: Confirm overall market trend and identify golden/death cross setups. Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries.",
    "close_10_ema": "10 EMA: A responsive short-term average. Usage: Capture quick shifts in momentum and potential entry points. Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals.",
    "macd": "MACD: Computes momentum via differences of EMAs. Usage: Look for crossovers and divergence as signals of trend changes. Tips: Confirm with other indicators in low-volatility or sideways markets.",
    "macds": "MACD Signal: An EMA smoothing of the MACD line. Usage: Use crossovers with the MACD line to trigger trades. Tips: Should be part of a broader strategy to avoid false positives.",
    "macdh": "MACD Histogram: Shows the gap between the MACD line and its signal. Usage: Visualize momentum strength and spot divergence early. Tips: Can be volatile; complement with additional filters in fast-moving markets.",
    "rsi": "RSI: Measures momentum to flag overbought/oversold conditions. Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis.",
    "boll": "Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. Usage: Acts as a dynamic benchmark for price movement. Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals.",
    "boll_ub": "Bollinger Upper Band: Typically 2 standard deviations above the middle line. Usage: Signals potential overbought conditions and breakout zones. Tips: Confirm signals with other tools; prices may ride the band in strong trends.",
    "boll_lb": "Bollinger Lower Band: Typically 2 standard deviations below the middle line. Usage: Indicates potential oversold conditions. Tips: Use additional analysis to avoid false reversal signals.",
    "atr": "ATR: Averages true range to measure volatility. Usage: Set stop-loss levels and adjust position sizes based on current market volatility. Tips: It's a reactive measure, so use it as part of a broader risk management strategy.",
    "vwma": "VWMA: A moving average weighted by volume. Usage: Confirm trends by integrating price action with volume data. Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses.",
}


def _require_talib() -> None:
    if talib is None:  # pragma: no cover - depends on optional dependency
        raise RuntimeError(
            "TA-Lib is required to compute indicators locally. Install the 'TA-Lib' package"
            " and ensure its native dependencies are available."
        )


def _extract_window(
    dates: pd.Series,
    values: np.ndarray,
    start_dt: datetime,
    end_dt: datetime,
) -> List[Tuple[datetime, float]]:
    results: List[Tuple[datetime, float]] = []
    for date_value, raw_value in zip(dates, values):
        if raw_value is None:
            continue
        try:
            if np.isnan(raw_value):
                continue
        except TypeError:
            pass

        current_date = date_value.to_pydatetime() if hasattr(date_value, "to_pydatetime") else date_value
        if start_dt <= current_date <= end_dt:
            results.append((current_date, float(raw_value)))
    return results


def _format_output(
    indicator: str,
    rows: List[Tuple[datetime, float]],
    start_dt: datetime,
    end_dt: datetime,
) -> str:
    if not rows:
        series_block = "No data available for the specified date range."
    else:
        lines = [f"{row_dt.strftime('%Y-%m-%d')}: {value:.4f}" for row_dt, value in rows]
        series_block = "\n".join(lines)

    description = INDICATOR_DESCRIPTIONS.get(indicator, "No description available.")
    return (
        f"## {indicator.upper()} values from {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}:\n\n"
        f"{series_block}\n\n{description}"
    )


def _calculate_vwma(close: np.ndarray, volume: np.ndarray, time_period: int) -> np.ndarray:
    price_series = pd.Series(close)
    volume_series = pd.Series(volume)
    numerator = (price_series * volume_series).rolling(time_period).sum()
    denominator = volume_series.rolling(time_period).sum()
    vwma = numerator / denominator
    return vwma.to_numpy()


def get_indicator(
    symbol: str,
    indicator: str,
    curr_date: str,
    look_back_days: int,
    interval: str = "daily",
    time_period: int = 14,
    series_type: str = "close",
) -> str:
    """Return locally-computed technical indicator values for the supplied window."""

    indicator_key = indicator.lower()

    if indicator_key not in SUPPORTED_INDICATORS:
        raise ValueError(
            f"Indicator {indicator} is not supported. Please choose from: {list(SUPPORTED_INDICATORS.keys())}"
        )

    if interval != "daily":
        raise ValueError("Only daily interval calculations are supported for Alpha Vantage indicators.")

    _require_talib()

    curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_dt = curr_date_dt - relativedelta(days=look_back_days)

    price_frame = _fetch_symbol_timeseries(symbol).sort_values("date").reset_index(drop=True)
    close = price_frame["close"].to_numpy(dtype=float)
    high = price_frame["high"].to_numpy(dtype=float)
    low = price_frame["low"].to_numpy(dtype=float)
    volume = price_frame["volume"].to_numpy(dtype=float)

    values: np.ndarray

    if indicator_key == "close_50_sma":
        values = talib.SMA(close, timeperiod=50)
    elif indicator_key == "close_200_sma":
        values = talib.SMA(close, timeperiod=200)
    elif indicator_key == "close_10_ema":
        values = talib.EMA(close, timeperiod=10)
    elif indicator_key in {"macd", "macds", "macdh"}:
        macd, macds, macdh = talib.MACD(close)
        value_map = {"macd": macd, "macds": macds, "macdh": macdh}
        values = value_map[indicator_key]
    elif indicator_key == "rsi":
        values = talib.RSI(close, timeperiod=time_period)
    elif indicator_key in {"boll", "boll_ub", "boll_lb"}:
        upper, middle, lower_band = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        band_map = {"boll": middle, "boll_ub": upper, "boll_lb": lower_band}
        values = band_map[indicator_key]
    elif indicator_key == "atr":
        values = talib.ATR(high, low, close, timeperiod=time_period)
    elif indicator_key == "vwma":
        values = _calculate_vwma(close, volume, time_period)
    else:  # pragma: no cover - defensive fallback
        raise ValueError(f"Indicator {indicator} is not implemented.")

    rows = _extract_window(price_frame["date"], values, start_dt, curr_date_dt)
    return _format_output(indicator_key, rows, start_dt, curr_date_dt)
