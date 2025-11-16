import time
import json


def create_risk_manager(llm, memory):
    def risk_manager_node(state) -> dict:

        company_name = state["company_of_interest"]

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        market_research_report = state["market_report"]
        news_report = state["news_report"]
        fundamentals_report = state["news_report"]
        sentiment_report = state["sentiment_report"]
        trader_plan = state["investment_plan"]
        risk_summary = state.get("risk_quant_report", "")
        risk_metrics_json = state.get("risk_metrics_json", "")

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""
<ROLE>
You are the Risk Manager (risk management judge and debate facilitator) in a multi-agent trading system. You adjudicate a debate between Risky, Neutral, and Safe/Conservative analysts and convert it into a clear risk-adjusted trading recommendation.
</ROLE>

<CONTEXT>
Trader plan:
{trader_plan}

Past lessons:
{past_memory_str}

Risk debate history:
{history}

Risk Quant Summary:
{risk_summary}

Structured Risk Metrics JSON:
{risk_metrics_json}
</CONTEXT>

<OBJECTIVE>
1. Evaluate the Risky, Neutral, and Safe perspectives.
2. Make a single actionable recommendation: Buy, Sell, or Hold (Hold only if strongly justified).
3. Use past mistakes to avoid repeating poor risk decisions.
4. Refine the trader's plan to better balance reward and risk.

</OBJECTIVE>

<OUTPUT_REQUIREMENTS>
Write plain prose (no special formatting) that covers:
1. Summary of Key Risk Arguments – what each analyst emphasized and why it matters now.
2. Recommendation (Buy/Sell/Hold) stated explicitly and early, with justification.
3. Rationale anchored in debate evidence and lessons from {past_memory_str}.
4. Refined Trader Plan – detail adjustments to position size/gross exposure, hedging, time horizon, review checkpoints, and risk limits.

Be decisive and focus on actionable risk management rather than theory.

</OUTPUT_REQUIREMENTS>
"""

        response = llm.invoke(prompt)

        new_risk_debate_state = {
            "judge_decision": response.content,
            "history": risk_debate_state["history"],
            "risky_history": risk_debate_state["risky_history"],
            "safe_history": risk_debate_state["safe_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_risky_response": risk_debate_state["current_risky_response"],
            "current_safe_response": risk_debate_state["current_safe_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": response.content,
        }

    return risk_manager_node
