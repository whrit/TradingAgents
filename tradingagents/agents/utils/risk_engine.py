from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import NormalDist
from typing import Dict, Any, Optional, Sequence

import numpy as np
import pandas as pd
from io import StringIO

from tradingagents.dataflows.interface import route_to_vendor


def _clean_price_csv(csv_string: str) -> pd.DataFrame:
    if not csv_string:
        raise ValueError("Empty price data")

    rows = [
        line for line in csv_string.splitlines() if line and not line.startswith("#")
    ]
    if not rows:
        raise ValueError("Price data missing rows")

    df = pd.read_csv(StringIO("\n".join(rows)))
    if "Date" not in df.columns:
        df["Date"] = df.index
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date", drop=False)
    return df


@dataclass
class RiskInputs:
    ticker: str
    end_date: str
    lookback_days: int = 120
    benchmark: str = "SPY"
    sector: Optional[str] = None
    confidence_levels: Sequence[float] = (0.95, 0.99)
    portfolio_value: float = 1_000_000.0
    position_notional: float = 100_000.0
    risk_budget_pct: float = 0.02
    adv_window: int = 20
    trading_days: int = 252


class RiskEngine:
    def generate(self, inputs: RiskInputs) -> Dict[str, Any]:
        asset = self._load_price_history(inputs.ticker, inputs)
        benchmark = (
            self._load_price_history(inputs.benchmark, inputs)
            if inputs.benchmark
            else None
        )
        sector = (
            self._load_price_history(inputs.sector, inputs)
            if inputs.sector
            else None
        )

        returns = asset["Close"].pct_change().dropna()
        if returns.empty:
            raise ValueError("Insufficient return history for risk calculation")

        bench_returns = (
            benchmark["Close"].pct_change().dropna() if benchmark is not None else None
        )
        sector_returns = (
            sector["Close"].pct_change().dropna() if sector is not None else None
        )

        hist = self._historical_var(returns, inputs.confidence_levels)
        parametric = self._parametric_var(returns, inputs.confidence_levels)

        annualized_vol = float(returns.std(ddof=0) * np.sqrt(inputs.trading_days))
        drawdown, dd_days = self._max_drawdown(returns)
        beta_bench = self._beta(returns, bench_returns)
        beta_sector = self._beta(returns, sector_returns)
        corr_metrics = self._correlation_snapshot(returns, bench_returns)
        atr = self._atr(asset)
        liquidity = self._liquidity_snapshot(asset, inputs)

        stress = self._stress_tests(
            beta_bench,
            beta_sector,
            annualized_vol,
            inputs.position_notional,
            liquidity["days_to_exit"],
        )

        sizing = self._position_sizing(hist, inputs)
        risk_limits = self._risk_limits(hist, inputs, sizing)

        report = {
            "meta": {
                "ticker": inputs.ticker,
                "end_date": inputs.end_date,
                "lookback_days": inputs.lookback_days,
                "data_points": len(returns),
                "last_price": float(asset["Close"].iloc[-1]),
            },
            "var": {"historical": hist, "parametric": parametric},
            "volatility": {
                "annualized": annualized_vol,
                "daily": float(returns.std(ddof=0)),
            },
            "drawdown": {"max_pct": drawdown, "duration_days": dd_days},
            "beta": {
                "vs_benchmark": beta_bench,
                "vs_sector": beta_sector,
            },
            "correlation": corr_metrics,
            "liquidity": liquidity,
            "stress": stress,
            "position_sizing": sizing,
            "stops": self._stop_levels(atr, inputs),
            "risk_limits": risk_limits,
        }
        return report

    def _load_price_history(self, symbol: str, inputs: RiskInputs) -> pd.DataFrame:
        if not symbol:
            raise ValueError("Symbol is required for risk calculations")
        end_dt = datetime.strptime(inputs.end_date, "%Y-%m-%d")
        start_dt = end_dt - timedelta(days=inputs.lookback_days + 5)
        csv = route_to_vendor(
            "get_stock_data", symbol, start_dt.strftime("%Y-%m-%d"), inputs.end_date
        )
        df = _clean_price_csv(csv)
        df = df.loc[df.index <= end_dt]
        cutoff = end_dt - timedelta(days=inputs.lookback_days + 1)
        df = df.loc[df.index >= cutoff]
        min_required = max(5, min(inputs.lookback_days + 1, 60))
        if len(df) < min_required:
            raise ValueError(f"Insufficient price history for {symbol}")
        return df

    def _historical_var(
        self, returns: pd.Series, levels: Sequence[float]
    ) -> Dict[str, Dict[str, float]]:
        results: Dict[str, Dict[str, float]] = {}
        for level in levels:
            quantile = float(np.quantile(returns, 1 - level))
            mask = returns <= quantile
            es = float(returns[mask].mean()) if mask.any() else quantile
            ci = self._confidence_interval(returns, quantile)
            results[f"{level:.2f}"] = {
                "value": quantile,
                "expected_shortfall": es,
                "confidence_interval": ci,
            }
        return results

    def _parametric_var(
        self, returns: pd.Series, levels: Sequence[float]
    ) -> Dict[str, Dict[str, float]]:
        mu = returns.mean()
        sigma = returns.std(ddof=0)
        dist = NormalDist(mu, sigma if sigma > 0 else 1e-9)
        results: Dict[str, Dict[str, float]] = {}
        for level in levels:
            cutoff = float(dist.inv_cdf(1 - level))
            ci = self._confidence_interval(returns, cutoff)
            results[f"{level:.2f}"] = {"value": cutoff, "confidence_interval": ci}
        return results

    def _confidence_interval(
        self, returns: pd.Series, statistic: float
    ) -> Dict[str, float]:
        std_err = returns.std(ddof=0) / np.sqrt(len(returns))
        half_width = 1.96 * std_err
        return {
            "lower": float(statistic - half_width),
            "upper": float(statistic + half_width),
        }

    def _max_drawdown(self, returns: pd.Series) -> tuple[float, int]:
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = cumulative / running_max - 1
        if drawdown.empty:
            return 0.0, 0
        trough = drawdown.idxmin()
        max_drawdown = float(drawdown.min())
        peak = cumulative.loc[:trough].idxmax()
        duration = (trough - peak).days if peak is not None else 0
        return max_drawdown, int(duration)

    def _beta(self, returns: pd.Series, bench_returns: Optional[pd.Series]) -> float:
        if bench_returns is None:
            return float("nan")
        df = pd.concat([returns, bench_returns], axis=1).dropna()
        if len(df) < 2:
            return float("nan")
        cov = np.cov(df.iloc[:, 0], df.iloc[:, 1], ddof=0)
        var_bench = np.var(df.iloc[:, 1], ddof=0)
        if var_bench == 0:
            return float("nan")
        return float(cov[0, 1] / var_bench)

    def _correlation_snapshot(
        self, returns: pd.Series, bench_returns: Optional[pd.Series]
    ) -> Dict[str, float]:
        if bench_returns is None:
            return {"rolling_30d": float("nan"), "full_period": float("nan"), "break_probability": 1.0}

        aligned = pd.concat([returns, bench_returns], axis=1).dropna()
        if aligned.empty:
            return {"rolling_30d": float("nan"), "full_period": float("nan"), "break_probability": 1.0}

        window = min(30, len(aligned))
        rolling = aligned.iloc[:, 0].rolling(window).corr(aligned.iloc[:, 1])
        latest = rolling.dropna().iloc[-1] if not rolling.dropna().empty else float("nan")
        full_period = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
        if rolling.dropna().std() == 0 or np.isnan(latest):
            break_prob = 1.0
        else:
            z = abs(latest - rolling.dropna().mean()) / rolling.dropna().std()
            break_prob = float(2 * (1 - NormalDist().cdf(min(z, 10))))

        return {
            "rolling_30d": float(latest),
            "full_period": float(full_period),
            "break_probability": break_prob,
        }

    def _atr(self, df: pd.DataFrame) -> float:
        highs = df["High"].astype(float)
        lows = df["Low"].astype(float)
        closes = df["Close"].astype(float)
        prev_closes = closes.shift(1)
        tr = pd.concat(
            [
                highs - lows,
                (highs - prev_closes).abs(),
                (lows - prev_closes).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr = tr.rolling(window=14, min_periods=1).mean().iloc[-1]
        return float(atr)

    def _liquidity_snapshot(
        self, df: pd.DataFrame, inputs: RiskInputs
    ) -> Dict[str, float]:
        window = min(inputs.adv_window, len(df))
        dollar_vol = (df["Close"].astype(float) * df["Volume"].astype(float))
        adv = float(dollar_vol.tail(window).mean())
        exit_rate = max(adv * 0.2, 1.0)
        days_to_exit = inputs.position_notional / exit_rate
        return {
            "adv_dollars": adv,
            "days_to_exit": float(days_to_exit),
        }

    def _stress_tests(
        self,
        beta_bench: float,
        beta_sector: float,
        annualized_vol: float,
        position_notional: float,
        days_to_exit: float,
    ) -> Dict[str, float]:
        beta_bench = beta_bench if not np.isnan(beta_bench) else 1.0
        beta_sector = beta_sector if not np.isnan(beta_sector) else beta_bench
        market_crash = beta_bench * -0.20
        sector_rotation = beta_sector * -0.10
        vol_cost = position_notional * min(0.05, annualized_vol * 0.1)
        return {
            "market_crash_pct": float(market_crash),
            "sector_rotation_pct": float(sector_rotation),
            "vol_spike_cost": float(vol_cost),
            "liquidity_days": float(days_to_exit),
        }

    def _position_sizing(self, hist: Dict[str, Dict[str, float]], inputs: RiskInputs) -> Dict[str, float]:
        key = next(iter(hist))
        var = abs(hist[key]["value"])
        risk_budget = inputs.portfolio_value * inputs.risk_budget_pct
        per_unit = max(var, 1e-6)
        max_position = min(inputs.portfolio_value, risk_budget / per_unit)
        optimal = min(inputs.position_notional, max_position * 0.6)
        minimum = optimal * 0.25
        return {
            "max_position": float(max_position),
            "optimal_position": float(optimal),
            "minimum_position": float(minimum),
        }

    def _risk_limits(
        self,
        hist: Dict[str, Dict[str, float]],
        inputs: RiskInputs,
        sizing: Dict[str, float],
    ) -> Sequence[Dict[str, Any]]:
        var_current = abs(hist[next(iter(hist))]["value"])
        gross_exposure = inputs.position_notional / inputs.portfolio_value
        concentration = sizing["optimal_position"] / inputs.portfolio_value
        limits = [
            self._limit_row("VaR", var_current, inputs.risk_budget_pct),
            self._limit_row("Gross Exposure", gross_exposure, 0.25),
            self._limit_row("Concentration", concentration, 0.15),
        ]
        return limits

    def _limit_row(self, metric: str, current: float, limit: float) -> Dict[str, Any]:
        status = "OK"
        if current > limit * 1.1:
            status = "BREACH"
        elif current > limit:
            status = "WARNING"
        return {
            "metric": metric,
            "current": float(current),
            "limit": float(limit),
            "status": status,
        }

    def _stop_levels(self, atr: float, inputs: RiskInputs) -> Dict[str, Any]:
        return {
            "atr_stop": float(atr * 3),
            "time_stop_days": max(5, min(20, inputs.lookback_days // 3)),
            "fundamental_trigger": f"Exit if {inputs.ticker} EPS revisions fall below -5% vs consensus.",
        }
