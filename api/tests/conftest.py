"""Pytest fixtures for API testing."""

import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session

# Set test environment before importing app
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["DEBUG"] = "false"

from main import app
from db import engine


@pytest.fixture(scope="function")
def client():
    """Create a test client with a fresh database for each test."""
    # Create all tables
    SQLModel.metadata.create_all(engine)

    with TestClient(app) as test_client:
        yield test_client

    # Drop all tables after test
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def sample_task():
    """Sample task data for testing."""
    return {
        "title": "Test Task",
        "description": "A test task description",
        "priority": "normal",
    }


@pytest.fixture(scope="function")
def sample_task_high_priority():
    """Sample high priority task data."""
    return {
        "title": "Urgent Task",
        "description": "This is urgent",
        "priority": "high",
    }


@pytest.fixture(scope="function")
def sample_task_with_due_date():
    """Sample task with due date."""
    return {
        "title": "Task with deadline",
        "priority": "normal",
        "due_date": "2025-12-31T23:59:59",
    }


@pytest.fixture(scope="function")
def sample_task_with_tags():
    """Sample task with tags."""
    return {
        "title": "Tagged Task",
        "priority": "normal",
        "tags": "urgent, project",
    }


@pytest.fixture(scope="function")
def sample_task_recurring():
    """Sample recurring task."""
    return {
        "title": "Daily Standup",
        "priority": "normal",
        "recurrence": "daily",
    }
