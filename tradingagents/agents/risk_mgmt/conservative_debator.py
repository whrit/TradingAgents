from langchain_core.messages import AIMessage
import time
import json


def create_safe_debator(llm):
    def safe_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        safe_history = risk_debate_state.get("safe_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        risk_summary = state.get("risk_quant_report", "")
        risk_metrics_json = state.get("risk_metrics_json", "")

        trader_decision = state["trader_investment_plan"]

        prompt = f"""
<ROLE>
You are the Safe/Conservative Risk Analyst in a three-way risk debate. Your primary goal is to protect capital, minimize volatility, and ensure long-term stability.
</ROLE>

<CONTEXT>
Trader's decision: {trader_decision}
Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest World Affairs Report: {news_report}
Company Fundamentals Report: {fundamentals_report}
Risk Quant Summary: {risk_summary}
Risk Metrics JSON:
{risk_metrics_json}
Conversation history: {history}
Risky arguments: {current_risky_response}
Neutral arguments: {current_neutral_response}
</CONTEXT>

<OBJECTIVE>
1. Critically examine the trader's decision for sources of undue risk.
2. Counter the Risky and Neutral views where they underweight downside.
3. Propose safer, lower-volatility adjustments or alternatives.
4. If other viewpoints are missing, present your own conservative stance without inventing their arguments.

</OBJECTIVE>

<OUTPUT_REQUIREMENTS>
- Speak conversationally (no special formatting).
- Highlight specific threats and potential loss scenarios.
- Critique Risky and Neutral positions when present, pointing out ignored drawdowns or correlation risks.
- Offer a clear conservative adjustment grounded in the provided reports.

</OUTPUT_REQUIREMENTS>
"""
        response = llm.invoke(prompt)

        argument = f"Safe Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": safe_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Safe",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return safe_node
