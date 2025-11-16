from tradingagents.dataflows.alternative_data import get_alternative_data_snapshot


def test_alternative_data_known_ticker():
    snapshot = get_alternative_data_snapshot("AAPL")
    assert "AAPL" in snapshot
    assert "Alternative Data Snapshot" in snapshot


def test_alternative_data_unknown_ticker():
    snapshot = get_alternative_data_snapshot("XYZ")
    assert "No curated alternative data snapshot" in snapshot
