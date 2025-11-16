import functools
import time
import json


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        system_prompt = f"""
<ROLE>
You are the Trader agent in a multi-agent trading system. You synthesize upstream analysis (research, risk, macro, execution, compliance) into a final trade decision.
</ROLE>

<CONTEXT>
Lessons from similar situations:
{past_memory_str}
</CONTEXT>

<OBJECTIVE>
1. Analyze the available information and determine whether to Buy, Sell, or Hold the position.
2. Provide a clear justification, incorporating lessons from prior trades.
3. End with a firm decision line: FINAL TRANSACTION PROPOSAL: **BUY/SELL/HOLD**.

</OBJECTIVE>

<OUTPUT_REQUIREMENTS>
- Provide a short justification (1–3 paragraphs) in trader-friendly language explaining why your chosen action is superior right now and how past lessons influenced the decision.
- On a separate final line, output exactly: FINAL TRANSACTION PROPOSAL: **BUY** (or SELL/HOLD). Do not add any text after that line.

</OUTPUT_REQUIREMENTS>
"""

        user_context = {
            "role": "user",
            "content": (
                f"Based on the upstream analysis, here is the latest investment plan for {company_name}.\n\n"
                f"Proposed Investment Plan: {investment_plan}\n\n"
                "Use this plan and the other agent outputs to decide whether to buy, sell, or hold."
            ),
        }

        messages = [
            {"role": "system", "content": system_prompt},
            user_context,
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
