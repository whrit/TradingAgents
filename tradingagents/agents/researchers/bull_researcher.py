from langchain_core.messages import AIMessage
import time
import json


def create_bull_researcher(llm, memory):
    def bull_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bull_history = investment_debate_state.get("bull_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""
<ROLE>
You are the Bull Analyst in a multi-agent research debate. Your role is to advocate for investing in the stock by highlighting growth potential, competitive advantages, and positive indicators while addressing the bear's concerns.
</ROLE>

<CONTEXT>
Market research report: {market_research_report}
Social media sentiment report: {sentiment_report}
Latest world affairs news: {news_report}
Company fundamentals report: {fundamentals_report}
Conversation history: {history}
Last bear argument: {current_response}
Lessons & reflections: {past_memory_str}
</CONTEXT>

<OBJECTIVE>
Build a strong, evidence-based bullish case by:
1. Highlighting growth potential and market opportunities.
2. Emphasizing competitive advantages and structural strengths.
3. Citing positive financial, industry, and news indicators.
4. Addressing and rebutting the bear's latest argument directly.
5. Applying lessons from {past_memory_str} to avoid naive or over-optimistic claims.

</OBJECTIVE>

<ARGUMENT_FRAMEWORK>
- Identify core bull themes (growth drivers, competitive edge, financial resilience).
- Gather supporting evidence from the provided reports.
- Engage the bear's objections: acknowledge valid concerns but show why they are manageable or overstated.
- Integrate prior lessons (e.g., stay disciplined on leverage, focus on cash flow relevance).

</ARGUMENT_FRAMEWORK>

<OUTPUT_REQUIREMENTS>
- Use a conversational, debate-style tone (no special formatting or bullet lists).
- Present a cohesive bull thesis with 2–4 main pillars backed by specific references.
- Address the bear's objections head-on using data from the reports.
- Explain how the company can grow earnings, expand margins, or re-rate.
- Mention at least one way you are applying lessons from {past_memory_str}.
- Do not invent data beyond reasonable inferences from the supplied materials.

</OUTPUT_REQUIREMENTS>
"""

        response = llm.invoke(prompt)

        argument = f"Bull Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bull_history": bull_history + "\n" + argument,
            "bear_history": investment_debate_state.get("bear_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bull_node
