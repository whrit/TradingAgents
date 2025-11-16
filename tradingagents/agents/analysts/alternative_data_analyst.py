from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.alternative_data_tools import fetch_alternative_data
from tradingagents.agents.utils.news_data_tools import get_news


def create_alternative_data_analyst(llm):
    def alt_node(state):
        ticker = state["company_of_interest"]
        current_date = state["trade_date"]

        tools = [fetch_alternative_data, get_news]

        system_message = (
            "You specialize in alternative data: satellite imagery, credit-card spend trackers, "
            "web traffic, supply-chain telemetry, and app-download trends. Use the tools to "
            "collect the snapshot and cross-check it with any relevant headlines. Discuss:\n"
            "- Demand signals (e.g., store traffic, downloads, GPU queue depth)\n"
            "- Supply-side stress (utilization, inventory, logistics)\n"
            "- Consumer behavior (card spend, engagement indexes)\n"
            "- Whether alt data confirms or contradicts reported fundamentals."
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an alternative data analyst embedded within a trading pod."
                    " Tools: {tool_names}. Always call fetch_alternative_data first to gather the snapshot, "
                    "then reference get_news for corroborating anecdotes. Finish with a checklist rating "
                    "Momentum, Supply, Consumer, and Signal Quality.\n{system_message}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        ).partial(
            system_message=system_message,
            tool_names=", ".join(tool.name for tool in tools),
        )

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])
        report = ""
        if not result.tool_calls:
            report = result.content

        return {
            "messages": [result],
            "alternative_data_report": report,
        }

    return alt_node
