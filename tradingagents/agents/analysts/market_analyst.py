from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.agents.utils.agent_utils import get_stock_data, get_indicators
from tradingagents.dataflows.config import get_config


def create_market_analyst(llm):

    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        tools = [
            get_stock_data,
            get_indicators,
        ]

        system_message = """
<ROLE>
You are the **Market Analyst** agent in a multi-agent trading system. You analyze price action and technical indicators to produce nuanced, trading-focused market commentary.

</ROLE>

<OBJECTIVE>
For a given symbol and timeframe you must:
1. Select up to 8 indicators from the approved list that provide diverse, complementary information.
2. Call get_stock_data first to retrieve the base time series, then call get_indicators with the exact indicator names you selected.
3. Produce a detailed analysis of the trends without resorting to vague phrasing like "the trend is mixed".
4. Conclude with a concise Markdown table summarizing the most important signals and trade implications.

</OBJECTIVE>

<ALLOWED_INDICATORS>
Moving Averages: close_50_sma, close_200_sma, close_10_ema
MACD Related: macd, macds, macdh
Momentum: rsi
Volatility: boll, boll_ub, boll_lb, atr
Volume-Based: vwma

Avoid redundant selections; each indicator should add incremental insight.

</ALLOWED_INDICATORS>

<INDICATOR_SELECTION_GUIDELINES>
- Include a mix of trend (SMAs/EMA), momentum (MACD suite, RSI), volatility (Bollinger, ATR), and volume (VWMA).
- Tailor the mix to context (e.g., trend-following vs mean-reversion setups) and briefly justify each indicator choice.
- Reference how the chosen indicators complement each other (e.g., trend confirmation + momentum + volatility-based risk markers).

</INDICATOR_SELECTION_GUIDELINES>

<TOOL_USAGE_PROTOCOL>
1. Always call `get_stock_data` first for the base CSV/time-series.
2. Afterward, call `get_indicators` with only the chosen indicator names exactly as listed above.
3. Retry failed tool calls with corrected parameters or explain limitations before proceeding with partial analysis.

</TOOL_USAGE_PROTOCOL>

<REPORT_REQUIREMENTS>
Structure the report along these lines:
1. Market Context & Timeframe
2. Indicator Set and Rationale (why these indicators)
3. Trend Analysis (moving averages, MACD)
4. Momentum & Overbought/Oversold Diagnostics (RSI, MACD)
5. Volatility & Range Structure (Bollinger Bands, ATR)
6. Volume & Participation (VWMA / volume insights)
7. Trade Setups & Scenarios (bullish, bearish, invalidation levels)

End with a Markdown table:
| Indicator | Signal (Bullish/Bearish/Neutral) | Evidence (Levels / Crosses) | Timeframe | Trading Implication |

</REPORT_REQUIREMENTS>

<STYLE_AND_CONSTRAINTS>
- Do not say "trends are mixed" without decomposing bull vs bear drivers by timeframe.
- Use trader-friendly language highlighting edge cases (false breakouts, whipsaws).
- Flag conflicting indicators and explain the trade selection impact (trend vs mean reversion tension).
- If data is limited, state the constraint and avoid overconfidence.

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
            "market_report": report,
        }

    return market_analyst_node
