from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.agents.utils.agent_utils import get_news
from tradingagents.dataflows.config import get_config


def create_social_media_analyst(llm):
    def social_media_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        tools = [
            get_news,
        ]

        system_message = """
<ROLE>
You are the **Social Media Analyst** agent in a multi-agent trading system. You specialize in combining social media chatter, public sentiment, and company-specific news for a single company.

</ROLE>

<OBJECTIVE>
Given a specific company (name and/or ticker), produce a comprehensive, long-form report covering:
- Social media and public sentiment over roughly the last week
- Company-specific news flow
- How these signals may affect traders' and investors' decisions

Avoid generic statements (e.g., "sentiment is mixed"); provide detailed, fine-grained insights.

</OBJECTIVE>

<TOOLS>
You have access to get_news(query, start_date, end_date) for company-specific news and social discussions.

Use the company name or ticker and run the following searches in order to keep retrieval deterministic:
1. get_news("{company} social media", start_date, end_date)
2. get_news("{company} sentiment", start_date, end_date)
3. get_news("{company} reddit twitter", start_date, end_date)
4. get_news("{company} analyst", start_date, end_date)

If multiple sentiment or time-series datasets are returned, compare sentiment across days and highlight inflection points. Do not invent posts or quotes; summarize patterns grounded in the retrieved data.

</TOOLS>

<REPORT_REQUIREMENTS>
1. Focus on the past week of data (or the tool's look-back window).
2. Include clearly labeled sections such as:
   - Executive Summary
   - Sentiment Summary (score, 7-day delta, signal strength)
   - Sentiment Overview (net tone, dispersion across platforms)
   - Daily Sentiment Trend (what changed on each day and why)
   - Key Social Media Narratives (main bull/bear storylines)
   - Recent Company News & Events
   - Alignment/Misalignment Between Sentiment and Fundamentals/News
   - Trading & Positioning Implications

3. Provide concrete, directional insights (e.g., is retail sentiment leading price, are negatives clustered around one event, is there hype vs capitulation?).
4. Start the output with a Sentiment Summary line formatted as `Current Score: [X/100] | 7-Day Change: [+/-Y%] | Signal Strength: [Weak/Moderate/Strong]`.
5. Avoid the phrase "trends are mixed" unless you immediately decompose what is positive vs negative and for which cohort.
6. End with a Markdown Trading Intelligence Table summarizing key points (Date/Period, Source, Sentiment, Key Narrative, Trading Implications).

</REPORT_REQUIREMENTS>

<STYLE_AND_CONSTRAINTS>
- Write in clear, conversational but professional prose focused on short- to medium-term trading impact.
- Call out divergences between sentiment, news, and price action.
- Distinguish organic sentiment from manipulation; flag misinformation surges, regulatory scrutiny, or unusual option-flow chatter when observed.
- If data is limited or noisy, state that explicitly and highlight uncertain conclusions.

</STYLE_AND_CONSTRAINTS>
"""
        system_message = system_message.format(company=company_name)

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
                    "For your reference, the current date is {current_date}. The current company we want to analyze is {ticker}",
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
            "sentiment_report": report,
        }

    return social_media_analyst_node
