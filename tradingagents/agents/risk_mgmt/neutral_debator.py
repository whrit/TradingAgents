import time
import json


def create_neutral_debator(llm):
    def neutral_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        neutral_history = risk_debate_state.get("neutral_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_safe_response = risk_debate_state.get("current_safe_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        risk_summary = state.get("risk_quant_report", "")
        risk_metrics_json = state.get("risk_metrics_json", "")

        trader_decision = state["trader_investment_plan"]

        prompt = f"""
<ROLE>
You are the Neutral Risk Analyst in a three-way risk debate. Your job is to provide a balanced, moderate risk view that weighs upside and downside and often advocates for partial or conditional risk-taking.
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
Safe arguments: {current_safe_response}
</CONTEXT>

<OBJECTIVE>
1. Challenge both the Risky and Safe analysts where they are too extreme.
2. Propose a balanced, sustainable adjustment to the trader's decision.
3. Emphasize diversification, risk management, and realistic expectations.
4. If other viewpoints are missing, present your own moderate stance without inventing their arguments.

</OBJECTIVE>

<OUTPUT_REQUIREMENTS>
- Speak conversationally, no special formatting.
- Critique both extremes where appropriate and suggest a middle-ground approach (partial sizing, staggered entries, conditional risk-taking).
- Tie recommendations back to data from the reports whenever possible.

</OUTPUT_REQUIREMENTS>
"""

        response = llm.invoke(prompt)

        argument = f"Neutral Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": neutral_history + "\n" + argument,
            "latest_speaker": "Neutral",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": argument,
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return neutral_node
