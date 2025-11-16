import pandas as pd
import pytest

from tradingagents.dataflows import options as options_module


class DummyTicker:
    def __init__(self, options_list, chain):
        self._options = options_list
        self._chain = chain

    @property
    def options(self):
        return self._options

    def option_chain(self, expiry):
        return self._chain


class DummyChain:
    def __init__(self):
        data = {
            "contractSymbol": ["AAPL240118C00100000"],
            "strike": [100.0],
            "lastPrice": [5.0],
            "bid": [4.9],
            "ask": [5.1],
            "volume": [100],
            "openInterest": [1000],
            "impliedVolatility": [0.3],
            "inTheMoney": [False],
        }
        self.calls = pd.DataFrame(data)
        self.puts = pd.DataFrame(data)


def test_get_options_chain_returns_json(monkeypatch):
    chain = DummyChain()
    dummy = DummyTicker(["2024-01-19"], chain)
    monkeypatch.setattr(options_module.yf, "Ticker", lambda _: dummy)

    payload = options_module.get_options_chain("AAPL")
    assert "AAPL" in payload
    assert "calls" in payload


def test_get_options_chain_handles_missing_expirations(monkeypatch):
    dummy = DummyTicker([], None)
    monkeypatch.setattr(options_module.yf, "Ticker", lambda _: dummy)

    payload = options_module.get_options_chain("AAPL")
    assert "No listed option" in payload
