from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.news_data_tools import get_news, get_global_news


def create_macro_economist(llm):
    def macro_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        tools = [get_global_news, get_news]

        system_message = (
            "You are a Macro Economist tasked with synthesizing policy updates, "
            "inflation prints, yield-curve shifts, and global risk sentiment. "
            "Use the available tools to gather CPI/PPI coverage, central-bank commentary, "
            "and geopolitical developments. Provide:\n"
            "1. A concise policy outlook (Fed, ECB, BOJ, PBOC where relevant).\n"
            "2. Inflation/yield diagnostics (curve shape, breakevens, term-premium).\n"
            "3. Growth proxies (ISM, PMIs, freight, or credit spreads).\n"
            "4. Implications for the target ticker's sector as of {current_date}."
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI economist working inside a multi-agent desk."
                    " You can call: {tool_names}. Use them to fetch macro news before writing."
                    " Always cite whether the macro backdrop is acting as a headwind or tailwind "
                    "for {ticker}. Summaries must end with a mini-table highlighting Policy, "
                    "Inflation, Growth, and Risk Regimes.\n{system_message}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(
            system_message=system_message,
            tool_names=", ".join(tool.name for tool in tools),
            ticker=ticker,
        )
        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""
        if not result.tool_calls:
            report = result.content

        return {
            "messages": [result],
            "macro_report": report,
        }

    return macro_node
