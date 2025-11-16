# TradingAgents/graph/setup.py

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.metrics import CostTracker

from .conditional_logic import ConditionalLogic


ANALYST_FACTORIES = {
    "macro": create_macro_economist,
    "market": create_market_analyst,
    "social": create_social_media_analyst,
    "news": create_news_analyst,
    "fundamentals": create_fundamentals_analyst,
    "alternative": create_alternative_data_analyst,
}

ANALYST_LABELS = {
    "macro": "Macro Economist",
    "market": "Market Analyst",
    "social": "Social Analyst",
    "news": "News Analyst",
    "fundamentals": "Fundamentals Analyst",
    "alternative": "Alternative Data Analyst",
}


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    def __init__(
        self,
        quick_thinking_llm: ChatOpenAI,
        deep_thinking_llm: ChatOpenAI,
        tool_nodes: Dict[str, ToolNode],
        bull_memory,
        bear_memory,
        trader_memory,
        invest_judge_memory,
        risk_manager_memory,
        conditional_logic: ConditionalLogic,
        cost_tracker: CostTracker,
    ):
        """Initialize with required components."""
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.tool_nodes = tool_nodes
        self.bull_memory = bull_memory
        self.bear_memory = bear_memory
        self.trader_memory = trader_memory
        self.invest_judge_memory = invest_judge_memory
        self.risk_manager_memory = risk_manager_memory
        self.conditional_logic = conditional_logic
        self.cost_tracker = cost_tracker

    def setup_graph(
        self, selected_analysts=["macro", "market", "social", "news", "fundamentals", "alternative"]
    ):
        """Set up and compile the agent workflow graph.

        Args:
            selected_analysts (list): List of analyst types to include. Options are:
                - "macro": Macro economist
                - "market": Market analyst
                - "social": Social media analyst
                - "news": News analyst
                - "fundamentals": Fundamentals analyst
                - "alternative": Alternative data analyst
        """
        if len(selected_analysts) == 0:
            raise ValueError("Trading Agents Graph Setup Error: no analysts selected!")

        # Create analyst nodes
        analyst_nodes: Dict[str, Dict[str, Any]] = {}
        for analyst_key in selected_analysts:
            if analyst_key not in ANALYST_FACTORIES:
                raise ValueError(f"Unknown analyst type '{analyst_key}'")
            label = ANALYST_LABELS[analyst_key]
            node_fn = ANALYST_FACTORIES[analyst_key](self.quick_thinking_llm)
            wrapped_node = self.cost_tracker.wrap_section(label, node_fn)
            analyst_nodes[analyst_key] = {
                "label": label,
                "node": wrapped_node,
                "clear": create_msg_delete(),
                "tools": self.tool_nodes.get(analyst_key),
            }

        # Create researcher and manager nodes
        bull_researcher_node = self.cost_tracker.wrap_section(
            "Bull Researcher",
            create_bull_researcher(self.quick_thinking_llm, self.bull_memory),
        )
        bear_researcher_node = self.cost_tracker.wrap_section(
            "Bear Researcher",
            create_bear_researcher(self.quick_thinking_llm, self.bear_memory),
        )
        research_manager_node = self.cost_tracker.wrap_section(
            "Research Manager",
            create_research_manager(
                self.deep_thinking_llm, self.invest_judge_memory
            ),
        )
        trader_node = self.cost_tracker.wrap_section(
            "Trader", create_trader(self.quick_thinking_llm, self.trader_memory)
        )
        risk_quant_node = self.cost_tracker.wrap_section(
            "Risk Quant Analyst", create_risk_quant(self.quick_thinking_llm)
        )

        # Create risk analysis nodes
        risky_analyst = self.cost_tracker.wrap_section(
            "Risky Analyst", create_risky_debator(self.quick_thinking_llm)
        )
        neutral_analyst = self.cost_tracker.wrap_section(
            "Neutral Analyst", create_neutral_debator(self.quick_thinking_llm)
        )
        safe_analyst = self.cost_tracker.wrap_section(
            "Safe Analyst", create_safe_debator(self.quick_thinking_llm)
        )
        risk_manager_node = self.cost_tracker.wrap_section(
            "Risk Judge",
            create_risk_manager(self.deep_thinking_llm, self.risk_manager_memory),
        )
        execution_strategist_node = self.cost_tracker.wrap_section(
            "Execution Strategist",
            create_execution_strategist(self.quick_thinking_llm),
        )
        compliance_officer_node = self.cost_tracker.wrap_section(
            "Compliance Officer",
            create_compliance_officer(self.quick_thinking_llm),
        )

        # Create workflow
        workflow = StateGraph(AgentState)

        # Add analyst nodes to the graph
        for analyst_type, meta in analyst_nodes.items():
            label = meta["label"]
            workflow.add_node(label, meta["node"])
            workflow.add_node(f"Msg Clear {label}", meta["clear"])
            if meta["tools"]:
                workflow.add_node(f"tools_{analyst_type}", meta["tools"])

        # Add other nodes
        workflow.add_node("Bull Researcher", bull_researcher_node)
        workflow.add_node("Bear Researcher", bear_researcher_node)
        workflow.add_node("Research Manager", research_manager_node)
        workflow.add_node("Trader", trader_node)
        workflow.add_node("Risk Quant Analyst", risk_quant_node)
        workflow.add_node("Risky Analyst", risky_analyst)
        workflow.add_node("Neutral Analyst", neutral_analyst)
        workflow.add_node("Safe Analyst", safe_analyst)
        workflow.add_node("Risk Judge", risk_manager_node)
        workflow.add_node("Execution Strategist", execution_strategist_node)
        workflow.add_node("Compliance Officer", compliance_officer_node)

        # Define edges
        # Start with the first analyst
        first_label = analyst_nodes[selected_analysts[0]]["label"]
        workflow.add_edge(START, first_label)

        # Connect analysts in sequence
        for i, analyst_type in enumerate(selected_analysts):
            label = analyst_nodes[analyst_type]["label"]
            current_tools = f"tools_{analyst_type}"
            current_clear = f"Msg Clear {label}"

            should_continue = getattr(
                self.conditional_logic, f"should_continue_{analyst_type}"
            )
            workflow.add_conditional_edges(
                label,
                should_continue,
                [current_tools, current_clear],
            )
            if analyst_nodes[analyst_type]["tools"]:
                workflow.add_edge(current_tools, label)

            # Connect to next analyst or to Bull Researcher if this is the last analyst
            if i < len(selected_analysts) - 1:
                next_label = analyst_nodes[selected_analysts[i + 1]]["label"]
                workflow.add_edge(current_clear, next_label)
            else:
                workflow.add_edge(current_clear, "Bull Researcher")

        # Add remaining edges
        workflow.add_conditional_edges(
            "Bull Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher": "Bull Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_edge("Research Manager", "Trader")
        workflow.add_edge("Trader", "Risk Quant Analyst")
        workflow.add_edge("Risk Quant Analyst", "Risky Analyst")
        workflow.add_conditional_edges(
            "Risky Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Safe Analyst": "Safe Analyst",
                "Risk Judge": "Risk Judge",
            },
        )
        workflow.add_conditional_edges(
            "Safe Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Neutral Analyst": "Neutral Analyst",
                "Risk Judge": "Risk Judge",
            },
        )
        workflow.add_conditional_edges(
            "Neutral Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Risky Analyst": "Risky Analyst",
                "Risk Judge": "Risk Judge",
            },
        )

        workflow.add_edge("Risk Judge", "Execution Strategist")
        workflow.add_edge("Execution Strategist", "Compliance Officer")
        workflow.add_edge("Compliance Officer", END)

        # Compile and return
        return workflow.compile()
