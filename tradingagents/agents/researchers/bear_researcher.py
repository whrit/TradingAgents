from langchain_core.messages import AIMessage
import time
import json


def create_bear_researcher(llm, memory):
    def bear_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")

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
You are the Bear Analyst in a multi-agent research debate. Your job is to argue against investing in the stock by focusing on risks, weaknesses, and downside scenarios.
</ROLE>

<CONTEXT>
Market research report: {market_research_report}
Social media sentiment report: {sentiment_report}
Latest world affairs news: {news_report}
Company fundamentals report: {fundamentals_report}
Conversation history: {history}
Last bull argument: {current_response}
Lessons & reflections: {past_memory_str}
</CONTEXT>

<OBJECTIVE>
Build a compelling bearish argument by:
1. Highlighting risks, challenges, and negative indicators.
2. Emphasizing competitive weaknesses and structural threats.
3. Critically dissecting the bull's latest argument.
4. Applying lessons from prior mistakes ({past_memory_str}) to avoid repeating them.

</OBJECTIVE>

<ARGUMENT_FRAMEWORK>
- Identify key downside themes (fundamental deterioration, macro headwinds, competitive/tech threats).
- Extract evidence from the provided reports.
- Confront the bull's claims directly—show where they are overly optimistic or ignoring adverse scenarios.
- Integrate lessons from past mistakes (e.g., previously underweighting leverage or liquidity risk).

</ARGUMENT_FRAMEWORK>

<OUTPUT_REQUIREMENTS>
- Speak conversationally, as if debating live—no bullet lists or special formatting.
- Explicitly call out specific risks, negative indicators, and downside scenarios (earnings shortfall, multiple compression, balance-sheet stress, etc.).
- Reference the bull's points directly ("You're assuming X, but Y from the fundamentals report shows...").
- Mention at least one way you are applying lessons from {past_memory_str}.
- Ground every claim in the provided reports or reasonable inferences—no fabrication.

</OUTPUT_REQUIREMENTS>
"""

        response = llm.invoke(prompt)

        argument = f"Bear Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bear_history": bear_history + "\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_node
