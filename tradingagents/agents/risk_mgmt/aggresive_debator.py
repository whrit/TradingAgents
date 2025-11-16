import time
import json


def create_risky_debator(llm):
    def risky_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        risky_history = risk_debate_state.get("risky_history", "")

        current_safe_response = risk_debate_state.get("current_safe_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]
        risk_summary = state.get("risk_quant_report", "")
        risk_metrics_json = state.get("risk_metrics_json", "")

        prompt = f"""
<ROLE>
You are the Risky Risk Analyst in a three-way risk debate. You champion high-reward, high-risk strategies and argue in favor of the trader's decision where it offers meaningful upside.
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
Safe arguments: {current_safe_response}
Neutral arguments: {current_neutral_response}
</CONTEXT>

<OBJECTIVE>
1. Make a persuasive case for the trader's decision from a high-risk, high-reward perspective.
2. Highlight upside, growth potential, and strategic advantages.
3. Directly challenge concerns raised by Safe and Neutral analysts.
4. If their arguments are absent, present your own case without inventing theirs.

</OBJECTIVE>

<OUTPUT_REQUIREMENTS>
- Speak conversationally (no special formatting).
- Support the trader's decision and explain why the risk is worth taking.
- Counter specific points made by Safe and Neutral (when their arguments exist) using evidence from the reports.
- Emphasize speed, convexity, and upside optionality when arguing for risk-taking.

</OUTPUT_REQUIREMENTS>
"""

        response = llm.invoke(prompt)

        argument = f"Risky Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risky_history + "\n" + argument,
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Risky",
            "current_risky_response": argument,
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return risky_node
