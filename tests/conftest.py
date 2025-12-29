"""
Pytest configuration for NaijaBet API tests
"""
import pytest


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for async tests"""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


# Configure pytest-asyncio
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test"
    )
