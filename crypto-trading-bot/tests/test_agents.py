"""
Tests for Recommendation Agents
Agent: QA + Testing Team
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.base_agent import BaseRecommendationAgent, AgentRecommendation
from agents.technical_analysis import TechnicalAnalysisAgent
from agents.fundamental_analysis import FundamentalAnalysisAgent
from agents.sentiment_analysis import SentimentAnalysisAgent
from agents.risk_assessment import RiskAssessmentAgent
from agents.thesis_synthesis import ThesisSynthesisAgent
from agents.agent_runner import AgentRunner


class MockAgent(BaseRecommendationAgent):
    """Mock agent for testing."""

    def __init__(self):
        super().__init__("mock-model", "MockAgent")

    def build_prompt(self, asset, market_data=None, **kwargs):
        return "Mock prompt"

    def parse_output(self, raw_output, asset):
        return AgentRecommendation(
            agent_name="MockAgent",
            asset=asset,
            recommendation="WAIT",
            confidence="Medium",
            warnings="None",
            raw_output=raw_output,
            timestamp="2026-01-01T00:00:00Z",
            model_used="mock-model",
        )


def test_base_agent_call_ollama():
    agent = MockAgent()
    with patch.object(agent, '_call_ollama', return_value="Mock output"):
        result = agent.run("BTC/USD")
        assert result.agent_name == "MockAgent"
        assert result.asset == "BTC/USD"
        assert result.recommendation == "WAIT"


def test_technical_agent_prompt_building():
    agent = TechnicalAnalysisAgent()
    prompt = agent.build_prompt("BTC/USD", current_price=50000, recent_data="Some data")
    assert "BTC/USD" in prompt
    assert "50000" in prompt
    assert "Technical recommendation" in prompt


def test_technical_agent_parsing():
    agent = TechnicalAnalysisAgent()
    raw = """
Technical recommendation: BUY zone
Confidence: High
Warnings: None
"""
    result = agent.parse_output(raw, "BTC/USD")
    assert result.recommendation == "BUY zone"
    assert result.confidence == "High"
    assert result.agent_name == "Candles"


def test_fundamental_agent_prompt_building():
    agent = FundamentalAnalysisAgent()
    prompt = agent.build_prompt("ETH/USD")
    assert "ETH/USD" in prompt
    assert "Fundamental recommendation" in prompt


def test_sentiment_agent_prompt_building():
    agent = SentimentAnalysisAgent()
    prompt = agent.build_prompt("SOL/USD")
    assert "SOL/USD" in prompt
    assert "Sentiment recommendation" in prompt


def test_risk_agent_prompt_building():
    agent = RiskAssessmentAgent()
    prompt = agent.build_prompt("BTC/USD", portfolio_value=10000, current_position_value=0)
    assert "BTC/USD" in prompt
    assert "Recommended action" in prompt
    assert "10000" in prompt


def test_thesis_agent_prompt_building():
    agent = ThesisSynthesisAgent()
    prompt = agent.build_prompt(
        "BTC/USD",
        technical_recommendation="Tech: BUY",
        fundamental_recommendation="Fund: BULLISH",
        sentiment_recommendation="Sent: NEUTRAL",
        risk_recommendation="Risk: Proceed",
    )
    assert "BTC/USD" in prompt
    assert "Tech: BUY" in prompt
    assert "Final recommendation" in prompt


def test_agent_runner_structure():
    runner = AgentRunner()
    assert runner.technical.agent_name == "Candles"
    assert runner.fundamental.agent_name == "Ledger"
    assert runner.sentiment.agent_name == "Pulse"
    assert runner.risk.agent_name == "Shield"
    assert runner.thesis.agent_name == "Compass"


def test_agent_runner_with_mocks():
    runner = AgentRunner()

    # Mock all agents
    mock_rec = AgentRecommendation(
        agent_name="Mock",
        asset="BTC/USD",
        recommendation="WAIT",
        confidence="Medium",
        warnings="None",
        raw_output="Mock output",
        timestamp="2026-01-01T00:00:00Z",
        model_used="mock",
    )

    with patch.object(runner.technical, 'run', return_value=mock_rec):
        with patch.object(runner.fundamental, 'run', return_value=mock_rec):
            with patch.object(runner.sentiment, 'run', return_value=mock_rec):
                with patch.object(runner.risk, 'run', return_value=mock_rec):
                    with patch.object(runner.thesis, 'run', return_value=mock_rec):
                        result = runner.run_pipeline("BTC/USD", current_price=50000)

    assert result["asset"] == "BTC/USD"
    assert result["all_agents_succeeded"] is True
    assert len(result["errors"]) == 0
    assert result["technical"].recommendation == "WAIT"
    assert result["thesis"].recommendation == "WAIT"
