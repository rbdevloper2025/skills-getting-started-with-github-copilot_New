"""
Tests for the Mergington High School Activities API.
Uses the Arrange-Act-Assert (AAA) pattern.
"""

import copy
import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import app

client = TestClient(app, follow_redirects=False)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state after every test."""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestRoot:
    def test_redirects_to_index(self):
        # Arrange — no setup needed; default app state is sufficient

        # Act
        response = client.get("/")

        # Assert
        assert response.status_code in (301, 302, 307, 308)
        assert response.headers["location"].endswith("/static/index.html")


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_all_activities(self):
        # Arrange — no setup needed; activities are pre-populated at startup

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert len(response.json()) > 0

    def test_activity_has_required_fields(self):
        # Arrange — no setup needed

        # Act
        response = client.get("/activities")

        # Assert
        for name, details in response.json().items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)

    def test_chess_club_present(self):
        # Arrange — no setup needed

        # Act
        response = client.get("/activities")

        # Assert
        assert "Chess Club" in response.json()


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_successful_signup(self):
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]

    def test_signup_adds_participant(self):
        # Arrange
        email = "newcomer@mergington.edu"
        activity = "Chess Club"

        # Act
        client.post(f"/activities/{activity}/signup", params={"email": email})

        # Assert
        participants = client.get("/activities").json()[activity]["participants"]
        assert email in participants

    def test_signup_unknown_activity_returns_404(self):
        # Arrange
        email = "student@mergington.edu"
        activity = "Unknown Activity"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_returns_400(self):
        # Arrange — michael@mergington.edu is already enrolled in Chess Club
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_successful_unregister(self):
        # Arrange — michael@mergington.edu is pre-enrolled in Chess Club
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]

    def test_unregister_removes_participant(self):
        # Arrange — michael@mergington.edu is pre-enrolled in Chess Club
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Act
        client.delete(f"/activities/{activity}/unregister", params={"email": email})

        # Assert
        participants = client.get("/activities").json()[activity]["participants"]
        assert email not in participants

    def test_unregister_unknown_activity_returns_404(self):
        # Arrange
        email = "michael@mergington.edu"
        activity = "Unknown Activity"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_enrolled_returns_404(self):
        # Arrange
        email = "nothere@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"].lower()
