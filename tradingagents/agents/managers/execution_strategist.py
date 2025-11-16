from typing import Optional
from tradingagents.dataflows.config import get_config


def create_execution_strategist(llm):
    def execution_node(state):
        config = get_config()
        ticker = state["company_of_interest"]
        final_decision = state.get("final_trade_decision", "")
        trader_plan = state.get("trader_investment_plan", "")
        risk_summary = state.get("risk_quant_report", "")
        risk_metrics_json = state.get("risk_metrics_json", "")

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
            f"Risk Metrics JSON:\n{risk_metrics_json}\n\n"
            f"Proposed Instruction: {instruction or 'No trade (likely HOLD)'}"
        )

        prompt = f"""
<ROLE>
You are the Execution Strategist in a multi-agent trading system. You convert trade instructions and context into a concrete execution and routing plan.
</ROLE>

<CONTEXT>
{context}
</CONTEXT>

<OBJECTIVE>
1. If there is a valid trade instruction, design a detailed execution strategy covering order slicing, venue selection, slippage expectations, and contingency rules.
2. If no trade should be routed, clearly explain why (e.g., instruction absent, compliance block, risk override).

</OBJECTIVE>

<OUTPUT_REQUIREMENTS>
Write concise, professional prose. If a trade should be executed, cover:
1. Order Slicing – how to break the order by time/size and how speed relates to urgency/alpha decay.
2. Venue Preference – which venues/types to prioritize or avoid, with reasons.
3. Slippage Expectations & Controls – expected slippage vs benchmark and tactics to manage it (passive vs aggressive, limit vs market, pegging strategies, etc.).
4. Contingency / Adaptation Rules – how to adapt to volatility spikes, liquidity droughts, or news events (pause, slow, accelerate). 

If no trade should be routed, explicitly state that no execution is recommended and provide the key reason.

</OUTPUT_REQUIREMENTS>
"""
        response = llm.invoke([{"role": "user", "content": prompt}])
        plan_text = response.content if hasattr(response, "content") else str(response)

        return {
            "messages": [response],
            "execution_plan": plan_text,
            "proposed_trade": instruction,
        }

    return execution_node
