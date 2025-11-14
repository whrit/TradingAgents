"""
Alpaca Configuration Module

Manages configuration, credentials, and environment settings for Alpaca API.
"""

import os
from typing import Optional, Dict
from dataclasses import dataclass, field


class ConfigurationError(Exception):
    """Raised when configuration is invalid or incomplete."""
    pass


@dataclass
class AlpacaConfig:
    """
    Configuration class for Alpaca API integration.

    Attributes:
        api_key: Alpaca API key
        secret_key: Alpaca secret key
        paper_trading: Whether to use paper trading environment
        base_url: Base URL for API requests
        data_url: Base URL for data API requests
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
    """

    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    paper_trading: bool = True
    base_url: Optional[str] = None
    data_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3

    # URLs for different environments
    PAPER_BASE_URL: str = field(default='https://paper-api.alpaca.markets', init=False, repr=False)
    LIVE_BASE_URL: str = field(default='https://api.alpaca.markets', init=False, repr=False)
    DATA_URL: str = field(default='https://data.alpaca.markets', init=False, repr=False)

    def __post_init__(self):
        """Initialize configuration after dataclass initialization."""
        # Load from environment if not explicitly provided
        if self.api_key is None:
            self.api_key = os.getenv('ALPACA_API_KEY')
        if self.secret_key is None:
            self.secret_key = os.getenv('ALPACA_SECRET_KEY')

        # Set base URL based on trading mode if not explicitly provided
        if self.base_url is None:
            env_url = os.getenv('ALPACA_BASE_URL')
            if env_url:
                self.base_url = env_url
                self.paper_trading = 'paper' in env_url.lower()
            else:
                self.base_url = self.PAPER_BASE_URL if self.paper_trading else self.LIVE_BASE_URL

        # Set data URL
        if self.data_url is None:
            self.data_url = os.getenv('ALPACA_DATA_URL', self.DATA_URL)

        # Validate configuration
        self._validate_required_fields()

    def _validate_required_fields(self):
        """Validate that required configuration fields are present."""
        if not self.api_key:
            raise ConfigurationError("API key is required. Set ALPACA_API_KEY environment variable or pass api_key parameter.")
        if not self.secret_key:
            raise ConfigurationError("Secret key is required. Set ALPACA_SECRET_KEY environment variable or pass secret_key parameter.")

    def validate(self) -> bool:
        """
        Validate the configuration.

        Returns:
            bool: True if configuration is valid

        Raises:
            ConfigurationError: If configuration is invalid
        """
        self._validate_required_fields()

        if self.timeout <= 0:
            raise ConfigurationError("Timeout must be positive")
        if self.max_retries < 0:
            raise ConfigurationError("Max retries cannot be negative")

        return True

    @classmethod
    def from_env_file(cls, env_file: str = '.env') -> 'AlpacaConfig':
        """
        Create configuration from .env file.

        Args:
            env_file: Path to .env file

        Returns:
            AlpacaConfig: Configuration instance
        """
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            # python-dotenv not installed, skip loading
            pass

        return cls()

    def to_dict(self, mask_secrets: bool = True) -> Dict[str, any]:
        """
        Convert configuration to dictionary.

        Args:
            mask_secrets: Whether to mask secret values

        Returns:
            dict: Configuration as dictionary
        """
        config_dict = {
            'api_key': self.api_key if not mask_secrets else '***masked***',
            'paper_trading': self.paper_trading,
            'base_url': self.base_url,
            'data_url': self.data_url,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
        }
        return config_dict

    @property
    def is_paper_trading(self) -> bool:
        """Check if paper trading mode is enabled."""
        return self.paper_trading

    def __repr__(self) -> str:
        """String representation with masked secrets."""
        return (
            f"AlpacaConfig(api_key='***', paper_trading={self.paper_trading}, "
            f"base_url='{self.base_url}', timeout={self.timeout})"
        )
