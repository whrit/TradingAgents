import time
import json


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        investment_debate_state = state["investment_debate_state"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""
<ROLE>
You are the Research Manager (portfolio manager and debate facilitator) in a multi-agent trading system. You adjudicate the bull vs bear debate and convert it into a clear, actionable investment stance.
</ROLE>

<CONTEXT>
Past lessons:
{past_memory_str}

Debate history:
{history}
</CONTEXT>

<OBJECTIVE>
1. Summarize the strongest bull and bear arguments.
2. Make a decisive recommendation: Buy, Sell, or Hold (Hold only if strongly justified).
3. Justify your stance using debate evidence and past lessons.
4. Translate your conclusion into a concrete investment plan for the trader.

</OBJECTIVE>

<OUTPUT_REQUIREMENTS>
Write conversationally (no markdown or bullet lists). Include:
- Brief Summary of the Debate focusing on the most important bull vs bear points.
- Recommendation stated clearly with supporting rationale.
- Rationale & Lessons explaining how past mistakes influenced your decision.
- Investment Plan covering direction, sizing logic, time horizon, catalysts, and triggers for reassessment.

Be decisive and ensure the trader can act on your conclusion.

</OUTPUT_REQUIREMENTS>
"""
        response = llm.invoke(prompt)

        new_investment_debate_state = {
            "judge_decision": response.content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": response.content,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response.content,
        }

    return research_manager_node
