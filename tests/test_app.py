"""
Pytest tests for the FastAPI backend.

Uses Arrange-Act-Assert structure and isolates the in-memory activity state
between tests with an autouse fixture.
"""

from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities_state():
    """Restore the in-memory activities state before each test."""
    original_state = deepcopy(activities)
    yield
    activities.clear()
    activities.update(deepcopy(original_state))


@pytest.fixture
def client():
    """Provide a TestClient for the FastAPI app."""
    return TestClient(app)


class TestActivities:
    """Activity endpoint tests using the Arrange-Act-Assert pattern."""

    def test_get_activities_returns_activity_list(self, client):
        # Arrange
        expected_activity = "Chess Club"

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        payload = response.json()
        assert expected_activity in payload
        assert isinstance(payload[expected_activity]["participants"], list)
        assert payload[expected_activity]["description"] == "Learn strategies and compete in chess tournaments"

    def test_signup_for_activity_adds_participant(self, client):
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        encoded_activity = quote(activity_name, safe="")

        # Act
        response = client.post(
            f"/activities/{encoded_activity}/signup",
            params={"email": new_email},
        )

        # Assert
        assert response.status_code == 200
        assert new_email in activities[activity_name]["participants"]
        assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"

    def test_signup_duplicate_participant_returns_400(self, client):
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        encoded_activity = quote(activity_name, safe="")

        # Act
        response = client.post(
            f"/activities/{encoded_activity}/signup",
            params={"email": existing_email},
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_unregister_participant_removes_user(self, client):
        # Arrange
        activity_name = "Tennis Club"
        email_to_remove = "mia@mergington.edu"
        encoded_activity = quote(activity_name, safe="")

        # Act
        response = client.delete(
            f"/activities/{encoded_activity}/participants",
            params={"email": email_to_remove},
        )

        # Assert
        assert response.status_code == 200
        assert email_to_remove not in activities[activity_name]["participants"]
        assert response.json()["message"] == f"Removed {email_to_remove} from {activity_name}"

    def test_unregister_missing_participant_returns_404(self, client):
        # Arrange
        activity_name = "Debate Club"
        missing_email = "missing@mergington.edu"
        encoded_activity = quote(activity_name, safe="")

        # Act
        response = client.delete(
            f"/activities/{encoded_activity}/participants",
            params={"email": missing_email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found for this activity"
