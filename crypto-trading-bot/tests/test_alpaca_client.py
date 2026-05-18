"""
Tests for Alpaca Paper Trading Client
Agent: Broker Execution Team
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from broker.alpaca_client import AlpacaPaperClient, OrderResult


@pytest.fixture
def mock_env_paper():
    env = {
        "ALPACA_API_KEY": "test_key",
        "ALPACA_SECRET_KEY": "test_secret",
        "ALPACA_PAPER": "true",
        "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
    }
    with patch.dict(os.environ, env, clear=True):
        yield env


def test_paper_mode_required(mock_env_paper):
    with patch.dict(os.environ, {"ALPACA_PAPER": "false"}, clear=False):
        with pytest.raises(ValueError, match="Live trading requires CEO approval"):
            AlpacaPaperClient()


def test_api_keys_required():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="ALPACA_API_KEY"):
            AlpacaPaperClient()
