from robinhood_mcp_bridge.tools import ALLOWED_TOOLS, SUPPORTED_TOOLS


def test_supported_tools_are_stable_and_ordered():
    assert ALLOWED_TOOLS is SUPPORTED_TOOLS
    assert len(SUPPORTED_TOOLS) == 22
    assert SUPPORTED_TOOLS == tuple(sorted(SUPPORTED_TOOLS))
    assert len(set(SUPPORTED_TOOLS)) == len(SUPPORTED_TOOLS)
    assert "place_equity_order" in SUPPORTED_TOOLS
    assert "review_equity_order" in SUPPORTED_TOOLS
