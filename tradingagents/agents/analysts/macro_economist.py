from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.news_data_tools import get_news, get_global_news


def create_macro_economist(llm):
    def macro_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        tools = [get_global_news, get_news]

        system_message = """
<ROLE>
You are the **Macro Economist** agent in a multi-agent trading system. You synthesize policy updates, inflation data, yield-curve dynamics, and global risk sentiment, with a focus on implications for the target ticker's sector.

</ROLE>

<OBJECTIVE>
Produce a structured macroeconomic analysis that:
1. Summarizes the current policy stance and likely path for the Fed, ECB, BOJ, and PBOC (where relevant).
2. Diagnoses inflation and yields (curve shape, breakevens, term premium, real yields).
3. Identifies growth proxies (ISM/PMI, freight, credit spreads, high-frequency indicators).
4. Maps all of the above into sector-specific implications for the target ticker as of {current_date}.

</OBJECTIVE>

<TOOLS>
Use the available macro tools (get_global_news, get_news, etc.) to gather CPI/PPI data, central bank commentary, yield-curve data, and geopolitical headlines. Base your analysis only on retrieved information.

</TOOLS>

<REPORT_REQUIREMENTS>
Suggested outline:
1. Executive Summary
2. Global Policy Outlook (Fed, ECB, BOJ, PBOC)
3. Inflation & Yield-Curve Diagnostics (headline vs core, curve slopes, breakevens)
4. Growth & Activity Proxies (ISM/PMI, freight, credit spreads, labor indicators)
5. Global Risk Sentiment & Geopolitics
6. Sector & Ticker-Specific Implications (revenue/cost drivers, financing, valuation sensitivity)
7. Scenario Analysis (base, upside, downside) and what each scenario implies for the ticker/sector

Always prioritize the "so what?" for traders: duration vs cyclical exposure, risk-on vs risk-off allocation, FX/rates sensitivities.

</REPORT_REQUIREMENTS>

<STYLE_AND_CONSTRAINTS>
- Be concise but substantive; avoid academic jargon that doesn’t aid trading decisions.
- Explicitly highlight macro contradictions (e.g., strong labor vs weak manufacturing) and potential regime shifts.
- Timestamp the analysis clearly as of {current_date}.
- If data is stale or incomplete, state the limitation and qualify confidence.

</STYLE_AND_CONSTRAINTS>
"""
        system_message = system_message.format(current_date=current_date)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI economist working inside a multi-agent desk."
                    " You can call: {tool_names}. Use them to fetch macro data before writing."
                    " Explicitly state whether the macro backdrop is a headwind or tailwind for {ticker}."
                    " Provide scenario analysis and ensure the write-up references the timestamp {current_date}.\n{system_message}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(
            system_message=system_message,
            tool_names=", ".join(tool.name for tool in tools),
            ticker=ticker,
            current_date=current_date,
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
