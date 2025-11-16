from typing import Optional
from tradingagents.dataflows.config import get_config


def create_execution_strategist(llm):
    def execution_node(state):
        config = get_config()
        ticker = state["company_of_interest"]
        final_decision = state.get("final_trade_decision", "")
        trader_plan = state.get("trader_investment_plan", "")
        risk_summary = state.get("risk_quant_report", "")

        action = None
        decision_upper = final_decision.upper()
        if "BUY" in decision_upper:
            action = "buy"
        elif "SELL" in decision_upper:
            action = "sell"

        instruction = None
        if action:
            instruction = {
                "symbol": ticker,
                "action": action,
                "quantity": config.get("default_trade_quantity", 1),
                "order_type": config.get("default_order_type", "market"),
                "time_in_force": config.get("default_time_in_force", "day"),
                "limit_price": config.get("default_limit_price"),
            }

        context = (
            f"Ticker: {ticker}\n"
            f"Trader Plan:\n{trader_plan}\n\n"
            f"Risk Guidance:\n{risk_summary}\n\n"
            f"Proposed Instruction: {instruction or 'No trade (likely HOLD)'}"
        )

        prompt = (
            "You are an execution strategist. Using the context below, craft a routing "
            "plan describing order slicing, venue preference, and slippage expectations. "
            "If instruction is None, explain why no trade should be routed.\n\n"
            f"{context}"
        )
        response = llm.invoke([{"role": "user", "content": prompt}])
        plan_text = response.content if hasattr(response, "content") else str(response)

        return {
            "messages": [response],
            "execution_plan": plan_text,
            "proposed_trade": instruction,
        }

    return execution_node
