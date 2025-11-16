from tradingagents.dataflows.config import get_config


def create_compliance_officer(llm):
    def compliance_node(state):
        config = get_config()
        ticker = state["company_of_interest"]
        trade = state.get("proposed_trade")

        restrictions = {t.upper() for t in config.get("restricted_tickers", [])}
        max_size = config.get("max_position_size")
        issues = []
        risk_summary = state.get("risk_quant_report", "")
        risk_metrics_json = state.get("risk_metrics_json", "")

        if ticker.upper() in restrictions:
            issues.append(f"{ticker.upper()} is on the restricted list.")

        if trade:
            qty = trade.get("quantity", 0)
            if max_size and qty > max_size:
                issues.append(
                    f"Requested quantity {qty} exceeds max position size {max_size}."
                )
        else:
            issues.append("No executable trade instruction was provided.")

        status = "APPROVED" if not issues else "BLOCKED"
        notes = "\n".join(f"- {issue}" for issue in issues) or "- No compliance flags."

        prompt = (
            f"""
<ROLE>
You are the Compliance Officer in a multi-agent trading system. Summarize whether a proposed trade is permissible and why, in plain language suitable for audit logging.
</ROLE>

<CONTEXT>
Ticker: {ticker}
Instruction: {trade}
Status: {status}
Issues:
{notes}
Risk Quant Summary:
{risk_summary}
Risk Metrics JSON:
{risk_metrics_json}
</CONTEXT>

<OBJECTIVE>
Produce a single brief paragraph that states the final status and the key reasons driving the decision.
</OBJECTIVE>

<OUTPUT_REQUIREMENTS>
- Mention the ticker, the high-level trade instruction (buy vs sell, approximate intent), the decision status, and the main reasons drawn from the issues above (e.g., restricted list, position limits, or "no issues found").
- Keep the tone neutral, professional, and factual. Do not speculate beyond the provided notes.

</OUTPUT_REQUIREMENTS>
"""
        )
        response = llm.invoke([{"role": "user", "content": prompt}])
        summary = response.content if hasattr(response, "content") else str(response)

        return {
            "messages": [response],
            "compliance_report": summary,
            "compliance_status": status,
        }

    return compliance_node
