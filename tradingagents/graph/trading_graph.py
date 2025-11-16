# TradingAgents/graph/trading_graph.py

import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langgraph.prebuilt import ToolNode
from tradingagents.brokers.interface import route_to_broker

from tradingagents.agents import *
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.metrics import (
    CostTracker,
    CostTrackingChatAnthropic,
    CostTrackingChatGoogle,
    CostTrackingChatOpenAI,
)
from tradingagents.agents.utils.memory import FinancialSituationMemory
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from tradingagents.dataflows.config import set_config

# Import the new abstract tool methods from agent_utils
from tradingagents.agents.utils.agent_utils import (
    get_stock_data,
    get_indicators,
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_news,
    get_insider_sentiment,
    get_insider_transactions,
    get_global_news
)
from tradingagents.agents.utils.alternative_data_tools import fetch_alternative_data

from .conditional_logic import ConditionalLogic
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor

logger = logging.getLogger(__name__)


class TradingAgentsGraph:
    """Main class that orchestrates the trading agents framework."""

    def __init__(
        self,
        selected_analysts=["macro", "market", "social", "news", "fundamentals", "alternative"],
        debug=False,
        config: Dict[str, Any] = None,
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of analyst types to include
            debug: Whether to run in debug mode
            config: Configuration dictionary. If None, uses default config
        """
        self.debug = debug
        self.config = config or DEFAULT_CONFIG

        self.cost_tracker = CostTracker(
            self.config.get("model_pricing"),
            currency=self.config.get("cost_currency", "USD"),
        )

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # Initialize LLMs
        if (
            self.config["llm_provider"].lower() == "openai"
            or self.config["llm_provider"] == "ollama"
            or self.config["llm_provider"] == "openrouter"
        ):
            self.deep_thinking_llm = CostTrackingChatOpenAI(
                model=self.config["deep_think_llm"],
                base_url=self.config["backend_url"],
                cost_tracker=self.cost_tracker,
            )
            self.quick_thinking_llm = CostTrackingChatOpenAI(
                model=self.config["quick_think_llm"],
                base_url=self.config["backend_url"],
                cost_tracker=self.cost_tracker,
            )
        elif self.config["llm_provider"].lower() == "anthropic":
            self.deep_thinking_llm = CostTrackingChatAnthropic(
                model=self.config["deep_think_llm"],
                base_url=self.config["backend_url"],
                cost_tracker=self.cost_tracker,
            )
            self.quick_thinking_llm = CostTrackingChatAnthropic(
                model=self.config["quick_think_llm"],
                base_url=self.config["backend_url"],
                cost_tracker=self.cost_tracker,
            )
        elif self.config["llm_provider"].lower() == "google":
            self.deep_thinking_llm = CostTrackingChatGoogle(
                model=self.config["deep_think_llm"],
                cost_tracker=self.cost_tracker,
            )
            self.quick_thinking_llm = CostTrackingChatGoogle(
                model=self.config["quick_think_llm"],
                cost_tracker=self.cost_tracker,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config['llm_provider']}")
        
        # Initialize memories
        self.bull_memory = FinancialSituationMemory("bull_memory", self.config)
        self.bear_memory = FinancialSituationMemory("bear_memory", self.config)
        self.trader_memory = FinancialSituationMemory("trader_memory", self.config)
        self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config)
        self.risk_manager_memory = FinancialSituationMemory("risk_manager_memory", self.config)

        # Create tool nodes
        self.tool_nodes = self._create_tool_nodes()

        # Initialize components
        self.conditional_logic = ConditionalLogic()
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.tool_nodes,
            self.bull_memory,
            self.bear_memory,
            self.trader_memory,
            self.invest_judge_memory,
            self.risk_manager_memory,
            self.conditional_logic,
            self.cost_tracker,
        )

        self.propagator = Propagator()
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict
        self.last_execution_result = None

        # Set up the graph
        self.graph = self.graph_setup.setup_graph(selected_analysts)

    def _create_tool_nodes(self) -> Dict[str, ToolNode]:
        """Create tool nodes for different data sources using abstract methods."""
        return {
            "macro": ToolNode(
                [
                    get_global_news,
                    get_news,
                ]
            ),
            "market": ToolNode(
                [
                    # Core stock data tools
                    get_stock_data,
                    # Technical indicators
                    get_indicators,
                ]
            ),
            "social": ToolNode(
                [
                    # News tools for social media analysis
                    get_news,
                ]
            ),
            "news": ToolNode(
                [
                    # News and insider information
                    get_news,
                    get_global_news,
                    get_insider_sentiment,
                    get_insider_transactions,
                ]
            ),
            "fundamentals": ToolNode(
                [
                    # Fundamental analysis tools
                    get_fundamentals,
                    get_balance_sheet,
                    get_cashflow,
                    get_income_statement,
                ]
            ),
            "alternative": ToolNode(
                [
                    fetch_alternative_data,
                    get_news,
                ]
            ),
        }

    def propagate(self, company_name, trade_date):
        """Run the trading agents graph for a company on a specific date."""

        self.ticker = company_name
        self.cost_tracker.reset()

        # Initialize state
        init_agent_state = self.propagator.create_initial_state(
            company_name, trade_date
        )
        args = self.propagator.get_graph_args()

        if self.debug:
            # Debug mode with tracing
            trace = []
            for chunk in self.graph.stream(init_agent_state, **args):
                if len(chunk["messages"]) == 0:
                    pass
                else:
                    chunk["messages"][-1].pretty_print()
                    trace.append(chunk)

            final_state = trace[-1]
        else:
            # Standard mode without tracing
            final_state = self.graph.invoke(init_agent_state, **args)

        final_state["cost_statistics"] = self.cost_tracker.summary()

        # Store current state for reflection
        self.curr_state = final_state

        # Log state
        self._log_state(trade_date, final_state)

        # Return decision and processed signal
        decision = self.process_signal(final_state["final_trade_decision"])
        instruction = final_state.get("proposed_trade")
        if not instruction:
            instruction = self._build_trade_instruction(self.ticker, decision)
            final_state["proposed_trade"] = instruction
        execution = self._maybe_execute_trade(instruction)
        if execution:
            final_state["broker_execution"] = execution

        return final_state, decision

    def _log_state(self, trade_date, final_state):
        """Log the final state to a JSON file."""
        self.log_states_dict[str(trade_date)] = {
            "company_of_interest": final_state["company_of_interest"],
            "trade_date": final_state["trade_date"],
            "market_report": final_state["market_report"],
            "sentiment_report": final_state["sentiment_report"],
            "news_report": final_state["news_report"],
            "fundamentals_report": final_state["fundamentals_report"],
            "macro_report": final_state.get("macro_report"),
            "alternative_data_report": final_state.get("alternative_data_report"),
            "investment_debate_state": {
                "bull_history": final_state["investment_debate_state"]["bull_history"],
                "bear_history": final_state["investment_debate_state"]["bear_history"],
                "history": final_state["investment_debate_state"]["history"],
                "current_response": final_state["investment_debate_state"][
                    "current_response"
                ],
                "judge_decision": final_state["investment_debate_state"][
                    "judge_decision"
                ],
            },
            "trader_investment_decision": final_state["trader_investment_plan"],
            "risk_quant_report": final_state.get("risk_quant_report"),
            "risk_debate_state": {
                "risky_history": final_state["risk_debate_state"]["risky_history"],
                "safe_history": final_state["risk_debate_state"]["safe_history"],
                "neutral_history": final_state["risk_debate_state"]["neutral_history"],
                "history": final_state["risk_debate_state"]["history"],
                "judge_decision": final_state["risk_debate_state"]["judge_decision"],
            },
            "investment_plan": final_state["investment_plan"],
            "final_trade_decision": final_state["final_trade_decision"],
            "execution_plan": final_state.get("execution_plan"),
            "compliance_report": final_state.get("compliance_report"),
            "compliance_status": final_state.get("compliance_status"),
            "cost_statistics": final_state.get("cost_statistics"),
        }

        # Save to file
        directory = Path(f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/")
        directory.mkdir(parents=True, exist_ok=True)

        with open(
            f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/full_states_log_{trade_date}.json",
            "w",
        ) as f:
            json.dump(self.log_states_dict, f, indent=4)

    def reflect_and_remember(self, returns_losses):
        """Reflect on decisions and update memory based on returns."""
        self.reflector.reflect_bull_researcher(
            self.curr_state, returns_losses, self.bull_memory
        )
        self.reflector.reflect_bear_researcher(
            self.curr_state, returns_losses, self.bear_memory
        )
        self.reflector.reflect_trader(
            self.curr_state, returns_losses, self.trader_memory
        )
        self.reflector.reflect_invest_judge(
            self.curr_state, returns_losses, self.invest_judge_memory
        )
        self.reflector.reflect_risk_manager(
            self.curr_state, returns_losses, self.risk_manager_memory
        )

    def process_signal(self, full_signal):
        """Process a signal to extract the core decision."""
        return self.signal_processor.process_signal(full_signal)

    def _build_trade_instruction(self, symbol: str, decision: Optional[str]):
        normalized = (decision or "").strip().upper()
        if normalized not in {"BUY", "SELL"}:
            return None

        base_qty = self.config.get("default_trade_quantity", 1)
        multiplier = self.config.get("trade_size_multiplier", 1.0)
        quantity = base_qty * multiplier

        instruction = {
            "symbol": symbol,
            "action": "buy" if normalized == "BUY" else "sell",
            "quantity": quantity,
            "order_type": self.config.get("default_order_type", "market"),
            "time_in_force": self.config.get("default_time_in_force", "day"),
            "limit_price": self.config.get("default_limit_price"),
            "instrument_type": self.config.get("trade_instrument_type", "shares"),
        }
        return instruction

    def _maybe_execute_trade(self, instruction: Optional[Dict[str, Any]]):
        """Execute the final trade decision if automation is enabled."""
        if not instruction or not self.config.get("auto_execute_trades"):
            return None

        instrument = instruction.get(
            "instrument_type", self.config.get("trade_instrument_type", "shares")
        )
        if instrument != "shares":
            logger.info(
                "Skipping auto execution for non-share instrument type: %s", instrument
            )
            return None

        try:
            result = route_to_broker(
                "place_order",
                instruction["symbol"],
                instruction["quantity"],
                instruction["action"],
                order_type=instruction.get("order_type", "market"),
                time_in_force=instruction.get("time_in_force", "day"),
                limit_price=instruction.get("limit_price"),
            )
            self.last_execution_result = {**instruction, "result": result}
            logger.info(
                "Executed %s decision for %s",
                instruction["action"],
                instruction["symbol"],
            )
        except Exception as exc:  # pragma: no cover
            logger.exception(
                "Failed to execute %s order for %s",
                instruction["action"],
                instruction["symbol"],
            )
            self.last_execution_result = {**instruction, "error": str(exc)}

        return self.last_execution_result
