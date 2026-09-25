"""Pytest configuration and fixtures."""
import pytest
import sys
from pathlib import Path

# Add src to path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def pytest_configure(config):
    """Register asyncio mode."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async (deselect with '-m \"not asyncio\"')"
    )


@pytest.fixture
def asyncio_mode():
    """Use auto mode for pytest-asyncio."""
    return "auto"
