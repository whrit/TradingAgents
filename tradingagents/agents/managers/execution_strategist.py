import json
from typing import Optional
from tradingagents.dataflows.config import get_config
from tradingagents.dataflows.interface import route_to_vendor


def _load_options_snapshot(ticker: str, limit: int = 5):
    try:
        raw = route_to_vendor("get_options_data", ticker, None, limit)
        return json.loads(raw)
    except Exception:
        return None


def _select_option_contract(snapshot, action: str):
    if not snapshot:
        return None
    option_type = "call" if action == "buy" else "put"
    contracts = snapshot.get("calls" if option_type == "call" else "puts", [])
    return (option_type, contracts[0]) if contracts else None


def _build_option_instruction(ticker: str, base_instruction: dict, snapshot):
    selection = _select_option_contract(snapshot, base_instruction.get("action", "buy"))
    if not selection:
        return None, ""
    option_type, contract = selection
    premium = contract.get("ask") or contract.get("lastPrice")
    if premium is None:
        return None, ""

    quantity = max(1, int(round(base_instruction.get("quantity", 1))))
    derivative_details = {
        "option_type": option_type,
        "strike": contract.get("strike"),
        "premium": float(premium),
        "contract_symbol": contract.get("contractSymbol"),
        "implied_vol": contract.get("impliedVolatility"),
        "expiry": snapshot.get("expiry"),
        "multiplier": 100,
    }

    instruction = {
        "symbol": contract.get("contractSymbol"),
        "underlying_symbol": ticker,
        "action": base_instruction.get("action"),
        "quantity": quantity,
        "order_type": "limit",
        "time_in_force": base_instruction.get("time_in_force", "day"),
        "limit_price": float(premium),
        "instrument_type": base_instruction.get("instrument_type", "options"),
        "asset_type": "option",
        "derivative_details": derivative_details,
        "option_strategy": f"Single {option_type.title()} ({snapshot.get('expiry', 'n/a')})",
    }
    summary = (
        f"{instruction['symbol']} strike {derivative_details['strike']} premium {premium} "
        f"({option_type}, exp {snapshot.get('expiry', 'n/a')})"
    )
    return instruction, summary


def create_execution_strategist(llm):
    def execution_node(state):
        config = get_config()
        ticker = state["company_of_interest"]
        final_decision = state.get("final_trade_decision", "")
        trader_plan = state.get("trader_investment_plan", "")
        risk_summary = state.get("risk_quant_report", "")
        risk_metrics_json = state.get("risk_metrics_json", "")

        action = None
        decision_upper = final_decision.upper()
        if "BUY" in decision_upper:
            action = "buy"
        elif "SELL" in decision_upper:
            action = "sell"

        instruction = None
        trade_multiplier = float(config.get("trade_size_multiplier", 1.0))
        instrument_type = config.get("trade_instrument_type", "shares")

        if action:
            instruction = {
                "symbol": ticker,
                "action": action,
                "quantity": config.get("default_trade_quantity", 1) * trade_multiplier,
                "order_type": config.get("default_order_type", "market"),
                "time_in_force": config.get("default_time_in_force", "day"),
                "limit_price": config.get("default_limit_price"),
                "instrument_type": instrument_type,
                "asset_type": "equity",
            }

        options_context = ""
        options_snapshot = None
        if instruction and instrument_type != "shares":
            options_snapshot = _load_options_snapshot(ticker)
            option_instruction = None
            summary_text = ""
            if options_snapshot:
                option_instruction, summary_text = _build_option_instruction(
                    ticker, instruction, options_snapshot
                )
            if option_instruction:
                instruction = option_instruction
            options_context = (
                "\nOptions Snapshot:\n"
                f"{summary_text or json.dumps(options_snapshot or {}, indent=2)}\n"
            )

        context = (
            f"Ticker: {ticker}\n"
            f"Trader Plan:\n{trader_plan}\n\n"
            f"Risk Guidance:\n{risk_summary}\n\n"
            f"Risk Metrics JSON:\n{risk_metrics_json}\n\n"
            f"Instrument Type: {instrument_type}\n"
            f"Proposed Instruction: {instruction or 'No trade (likely HOLD)'}"
            f"{options_context}"
        )

        prompt = f"""
<ROLE>
You are the Execution Strategist in a multi-agent trading system. You convert trade instructions and context into a concrete execution and routing plan.
</ROLE>

<CONTEXT>
{context}
</CONTEXT>

<OBJECTIVE>
1. If there is a valid trade instruction, design a detailed execution strategy covering order slicing, venue selection, slippage expectations, and contingency rules.
2. If no trade should be routed, clearly explain why (e.g., instruction absent, compliance block, risk override).

</OBJECTIVE>

<OUTPUT_REQUIREMENTS>
Write concise, professional prose. If a trade should be executed, cover:
1. Order Slicing – how to break the order by time/size and how speed relates to urgency/alpha decay.
2. Venue Preference – which venues/types to prioritize or avoid, with reasons.
3. Slippage Expectations & Controls – expected slippage vs benchmark and tactics to manage it (passive vs aggressive, limit vs market, pegging strategies, etc.).
4. Contingency / Adaptation Rules – how to adapt to volatility spikes, liquidity droughts, or news events (pause, slow, accelerate). 

If no trade should be routed, explicitly state that no execution is recommended and provide the key reason.

</OUTPUT_REQUIREMENTS>
"""
        response = llm.invoke([{"role": "user", "content": prompt}])
        plan_text = response.content if hasattr(response, "content") else str(response)

        return {
            "messages": [response],
            "execution_plan": plan_text,
            "proposed_trade": instruction,
            "options_snapshot": options_snapshot,
        }

    return execution_node
