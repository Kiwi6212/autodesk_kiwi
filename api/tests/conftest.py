"""Pytest fixtures for API testing."""

import os
import sys

# Add api directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment BEFORE any imports
os.environ["DATABASE_URL"] = "sqlite:///./test_data.db"
os.environ["DEBUG"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

# Clear any cached settings
from config import get_settings
get_settings.cache_clear()

from main import app
from db import engine


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create fresh database tables for each test."""
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)
    # Clean up test database file
    if os.path.exists("./test_data.db"):
        try:
            os.remove("./test_data.db")
        except:
            pass


@pytest.fixture(scope="function")
def client():
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_task():
    """Sample task data for testing."""
    return {
        "title": "Test Task",
        "description": "A test task description",
        "priority": "normal",
    }


@pytest.fixture
def sample_task_high_priority():
    """Sample high priority task data."""
    return {
        "title": "Urgent Task",
        "description": "This is urgent",
        "priority": "high",
    }


@pytest.fixture
def sample_task_with_due_date():
    """Sample task with due date."""
    return {
        "title": "Task with deadline",
        "priority": "normal",
        "due_date": "2025-12-31T23:59:59",
    }


@pytest.fixture
def sample_task_with_tags():
    """Sample task with tags."""
    return {
        "title": "Tagged Task",
        "priority": "normal",
        "tags": "urgent, project",
    }


@pytest.fixture
def sample_task_recurring():
    """Sample recurring task."""
    return {
        "title": "Daily Standup",
        "priority": "normal",
        "recurrence": "daily",
    }
