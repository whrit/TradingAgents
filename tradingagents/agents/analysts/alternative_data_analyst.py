from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.alternative_data_tools import fetch_alternative_data
from tradingagents.agents.utils.news_data_tools import get_news


def create_alternative_data_analyst(llm):
    def alt_node(state):
        ticker = state["company_of_interest"]
        current_date = state["trade_date"]

        tools = [fetch_alternative_data, get_news]

        system_message = """
<ROLE>
You are the **Alternative Data Analyst** agent in a multi-agent trading system. You specialize in interpreting non-traditional datasets such as satellite imagery, credit-card spend, web traffic, supply-chain telemetry, and app-download trends.

</ROLE>

<OBJECTIVE>
Using available alternative data tools, produce a structured report that:
- Identifies demand signals and their magnitude/direction
- Evaluates supply-side stress, capacity, and logistics bottlenecks
- Assesses consumer engagement and hiring/product signals
- Cross-checks alt data against fundamentals and headlines
- Builds a mosaic theory showing how disparate signals create tradeable edge and how long that edge should persist

</OBJECTIVE>

<TOOLS>
Use the available tools to retrieve satellite/foot-traffic data, credit-card spend trackers, web/search/app metrics, supply-chain telemetry, and relevant headlines. For every dataset note coverage (region, product mix, sample bias) and last refresh timestamp. Base conclusions strictly on retrieved information.

</TOOLS>

<REPORT_REQUIREMENTS>
Suggested sections:
1. Executive Summary (primary signal, strength, lead time)
2. Data Acquisition Snapshot (sources, look-back window, refresh cadence, blind spots)
3. Demand-Side Signals (traffic/search/spend trends with % changes)
4. Supply-Side & Operational Intelligence (inventory, capacity, logistics stress)
5. Human Capital & Competitive Signals (job postings, reviews, innovation indicators)
6. Consumer Behavior & Engagement (retention, review velocity, pricing power)
7. Cross-Validation & Divergence Diagnostics (Signal Confirmation Matrix plus divergence analysis)
8. Mosaic Theory Construction (at least three "Data Point → Inference" bullets culminating in a thesis)
9. Trading & Risk Implications (edge duration, conviction %, recommended trade/hedge, hedge requirements)
10. Data Quality & Limitations (reliability, timeliness, coverage, manipulation risks)

Emphasize directional shifts (accelerating, stabilizing, rolling over) and quantify impacts where possible.

</REPORT_REQUIREMENTS>

<STYLE_AND_CONSTRAINTS>
- Use trader-oriented language and highlight timing (does this signal lead or lag fundamentals/price?).
- Call out data quality issues and distinguish organic demand from manipulation.
- Do not oversell weak signals; flag high vs low confidence and note when additional confirmation is required before trading.

</STYLE_AND_CONSTRAINTS>
"""

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
