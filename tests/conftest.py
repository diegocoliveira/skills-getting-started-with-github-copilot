"""Pytest configuration and fixtures for testing"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_participants = {
        activity_name: activity["participants"].copy()
        for activity_name, activity in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for activity_name, participants in original_participants.items():
        activities[activity_name]["participants"] = participants
