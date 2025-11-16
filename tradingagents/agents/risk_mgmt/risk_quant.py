from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.risk_tools import calculate_portfolio_risk


def create_risk_quant(llm):
    def risk_quant_node(state):
        ticker = state["company_of_interest"]
        trade_date = state["trade_date"]
        tools = [calculate_portfolio_risk]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a quantitative risk analyst producing VaR/ES guidance and hedge ideas."
                    " Always call the risk tool to pull the latest metrics, then translate them into"
                    " actionable guardrails: target gross exposure, hedge ratios, and stop levels."
                    " Summaries must include a short bullet list covering VaR, tail risk, hedge idea, "
                    "and recommended risk capital usage.",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        ).partial(tool_names=", ".join(tool.name for tool in tools))

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])
        report = ""
        if not result.tool_calls:
            report = result.content

        return {
            "messages": [result],
            "risk_quant_report": report,
        }

    return risk_quant_node
