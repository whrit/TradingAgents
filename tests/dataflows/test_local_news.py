from tradingagents.dataflows import local


def test_get_reddit_global_news_missing_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(local, "DATA_DIR", str(tmp_path / "missing"))

    result = local.get_reddit_global_news("2025-01-10")

    assert "No local reddit global_news dataset" in result
