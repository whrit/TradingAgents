from tradingagents.graph.conditional_logic import ConditionalLogic


class DummyMessage:
    def __init__(self, has_tool_calls: bool):
        self.tool_calls = ["tool"] if has_tool_calls else []


def _state_with_message(has_tool_calls: bool):
    return {"messages": [DummyMessage(has_tool_calls)]}


def test_should_continue_market_matches_node_names():
    logic = ConditionalLogic()
    assert (
        logic.should_continue_market(_state_with_message(False))
        == "Msg Clear Market Analyst"
    )
    assert logic.should_continue_market(_state_with_message(True)) == "tools_market"


def test_should_continue_social_matches_node_names():
    logic = ConditionalLogic()
    assert (
        logic.should_continue_social(_state_with_message(False))
        == "Msg Clear Social Analyst"
    )
    assert logic.should_continue_social(_state_with_message(True)) == "tools_social"


def test_should_continue_news_matches_node_names():
    logic = ConditionalLogic()
    assert (
        logic.should_continue_news(_state_with_message(False))
        == "Msg Clear News Analyst"
    )
    assert logic.should_continue_news(_state_with_message(True)) == "tools_news"


def test_should_continue_fundamentals_matches_node_names():
    logic = ConditionalLogic()
    assert (
        logic.should_continue_fundamentals(_state_with_message(False))
        == "Msg Clear Fundamentals Analyst"
    )
    assert (
        logic.should_continue_fundamentals(_state_with_message(True))
        == "tools_fundamentals"
    )
