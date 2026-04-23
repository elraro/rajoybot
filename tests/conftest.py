import os
import sys

import pytest_asyncio
from tortoise import Tortoise

# Add app directory to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from persistence import SoundRepository


@pytest_asyncio.fixture(scope="session")
async def database():
    """Create an in-memory SQLite database for testing."""
    db = SoundRepository(provider='sqlite')
    await db.init()
    yield db
    await Tortoise.close_connections()
