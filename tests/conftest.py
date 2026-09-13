"""
Pytest configuration for NaijaBet API tests
"""
import pytest


# Configure pytest-asyncio
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test"
    )
