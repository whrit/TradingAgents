"""
Unit tests for Alpaca configuration module.

Tests configuration loading, validation, and environment management.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.alpaca.config import AlpacaConfig, ConfigurationError


class TestAlpacaConfig:
    """Test suite for AlpacaConfig class."""

    def test_init_with_env_variables(self):
        """Test configuration initialization from environment variables."""
        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'test_key',
            'ALPACA_SECRET_KEY': 'test_secret',
            'ALPACA_BASE_URL': 'https://paper-api.alpaca.markets'
        }):
            config = AlpacaConfig()
            assert config.api_key == 'test_key'
            assert config.secret_key == 'test_secret'
            assert config.base_url == 'https://paper-api.alpaca.markets'
            assert config.is_paper_trading is True

    def test_init_with_explicit_credentials(self):
        """Test configuration with explicitly provided credentials."""
        config = AlpacaConfig(
            api_key='explicit_key',
            secret_key='explicit_secret',
            paper_trading=False
        )
        assert config.api_key == 'explicit_key'
        assert config.secret_key == 'explicit_secret'
        assert config.is_paper_trading is False
        assert config.base_url == 'https://api.alpaca.markets'

    def test_missing_credentials_raises_error(self):
        """Test that missing credentials raise ConfigurationError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError, match="API key is required"):
                AlpacaConfig()

    def test_validate_credentials(self):
        """Test credential validation."""
        config = AlpacaConfig(api_key='key', secret_key='secret')
        assert config.validate() is True

    def test_paper_trading_url_selection(self):
        """Test correct URL selection for paper trading."""
        config = AlpacaConfig(api_key='key', secret_key='secret', paper_trading=True)
        assert 'paper-api' in config.base_url

    def test_live_trading_url_selection(self):
        """Test correct URL selection for live trading."""
        config = AlpacaConfig(api_key='key', secret_key='secret', paper_trading=False)
        assert 'paper-api' not in config.base_url

    def test_from_env_file(self):
        """Test loading configuration from .env file."""
        with patch('src.alpaca.config.load_dotenv') as mock_load:
            with patch.dict(os.environ, {
                'ALPACA_API_KEY': 'env_key',
                'ALPACA_SECRET_KEY': 'env_secret'
            }):
                config = AlpacaConfig.from_env_file('.env')
                mock_load.assert_called_once()
                assert config.api_key == 'env_key'

    def test_to_dict(self):
        """Test configuration serialization to dictionary."""
        config = AlpacaConfig(api_key='key', secret_key='secret')
        config_dict = config.to_dict()
        assert 'api_key' in config_dict
        assert 'secret_key' not in config_dict  # Should be masked
        assert 'base_url' in config_dict

    def test_timeout_configuration(self):
        """Test timeout configuration."""
        config = AlpacaConfig(api_key='key', secret_key='secret', timeout=60)
        assert config.timeout == 60

    def test_retry_configuration(self):
        """Test retry configuration."""
        config = AlpacaConfig(api_key='key', secret_key='secret', max_retries=5)
        assert config.max_retries == 5
