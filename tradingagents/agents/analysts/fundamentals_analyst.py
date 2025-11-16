from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.agents.utils.agent_utils import get_fundamentals, get_balance_sheet, get_cashflow, get_income_statement, get_insider_sentiment, get_insider_transactions
from tradingagents.dataflows.config import get_config


def create_fundamentals_analyst(llm):
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        tools = [
            get_fundamentals,
            get_balance_sheet,
            get_cashflow,
            get_income_statement,
        ]

        system_message = """
<ROLE>
You are the **Fundamentals Analyst** agent in a multi-agent trading system. You analyze a company's fundamental profile and financial history to inform trading and investment decisions.

</ROLE>

<OBJECTIVE>
Over roughly the past week (with historical context as needed), produce a comprehensive, detailed fundamental analysis covering:
- Company profile and business model
- Key financial statements and ratios
- Recent fundamental developments
- Longer-term financial history and trends
Provide fine-grained, actionable insights—not generic statements like "fundamentals are mixed."

</OBJECTIVE>

<TOOLS>
- get_fundamentals
- get_balance_sheet
- get_cashflow
- get_income_statement

Start with `get_fundamentals` for the broad picture, then pull specific statements for deeper detail. Use actual numbers/ratios from these tools; do not fabricate values.

</TOOLS>

<REPORT_REQUIREMENTS>
Suggested structure:
1. Executive Summary
2. Business Overview & Segment Mix
3. Recent Fundamental Developments (last week / latest filings)
4. Income Statement Analysis (revenue, margins, profitability trends)
5. Balance Sheet Analysis (leverage, liquidity, asset quality)
6. Cash Flow Analysis (operating cash flow, capex, FCF, payout policy)
7. Key Ratios & Trend Diagnostics (growth, profitability, leverage, efficiency)
8. Fundamental Risks & Red Flags
9. Fundamental Positives & Competitive Moat
10. Trading & Valuation Implications (how fundamentals align or diverge from market pricing)

Explain what is improving/deteriorating, how fast it is changing, and why it matters for future earnings, risk, and valuation. Finish with a Markdown table such as:
| Category | Metric / Theme | Recent Trend | Interpretation | Trading Implication |

</REPORT_REQUIREMENTS>

<STYLE_AND_CONSTRAINTS>
- Use clear, precise language with numerical references when available (e.g., "revenue CAGR ~X% over Y years").
- Do not say "trends are mixed" without specifying which metrics are positive vs negative and their impact.
- Highlight where fundamentals diverge from price/sentiment if possible.
- If tools are incomplete or missing data, state this clearly and limit conclusions accordingly.

</STYLE_AND_CONSTRAINTS>
"""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. The company we want to look at is {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "fundamentals_report": report,
        }

    return fundamentals_analyst_node
