from tradingagents.dataflows.config import get_config


def create_compliance_officer(llm):
    def compliance_node(state):
        config = get_config()
        ticker = state["company_of_interest"]
        trade = state.get("proposed_trade")

        restrictions = {t.upper() for t in config.get("restricted_tickers", [])}
        max_size = config.get("max_position_size")
        issues = []

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
            "You are a compliance officer summarizing whether the trade is permissible.\n"
            f"Ticker: {ticker}\n"
            f"Instruction: {trade}\n"
            f"Status: {status}\n"
            f"Issues:\n{notes}\n"
            "Respond with a brief paragraph explaining the decision so it can be logged."
        )
        response = llm.invoke([{"role": "user", "content": prompt}])
        summary = response.content if hasattr(response, "content") else str(response)

        return {
            "messages": [response],
            "compliance_report": summary,
            "compliance_status": status,
        }

    return compliance_node
