from robinhood_mcp_bridge import RobinhoodMCPClient, RobinhoodMCPError, SUPPORTED_TOOLS, __version__


def test_public_exports_are_available():
    assert RobinhoodMCPClient.__name__ == "RobinhoodMCPClient"
    assert RobinhoodMCPError.__name__ == "RobinhoodMCPError"
    assert isinstance(SUPPORTED_TOOLS, tuple)
    assert len(SUPPORTED_TOOLS) == 22
    assert isinstance(__version__, str)
