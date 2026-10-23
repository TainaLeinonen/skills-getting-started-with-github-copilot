import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client():
    original_participants = {
        name: activity["participants"].copy()
        for name, activity in app_module.activities.items()
    }

    with TestClient(app_module.app) as test_client:
        yield test_client

    for name, participants in original_participants.items():
        app_module.activities[name]["participants"][:] = participants


def test_root_redirects_to_static_homepage(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_static_homepage_is_served(client):
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert "<html" in response.text.lower()


def test_get_activities_returns_all_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == app_module.activities


def test_signup_adds_student_to_activity(client):
    response = client.post(
        "/activities/Soccer%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up student@mergington.edu for Soccer Club"
    }
    assert (
        "student@mergington.edu"
        in app_module.activities["Soccer Club"]["participants"]
    )


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_student(client):
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for selected activity"
    }


def test_remove_participant_removes_student(client):
    response = client.delete(
        "/activities/Chess%20Club/participants/michael%40mergington.edu"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Removed michael@mergington.edu from Chess Club"
    }
    assert (
        "michael@mergington.edu"
        not in app_module.activities["Chess Club"]["participants"]
    )


def test_remove_participant_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Club/participants/student%40mergington.edu"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_participant_rejects_unregistered_student(client):
    response = client.delete(
        "/activities/Chess%20Club/participants/student%40mergington.edu"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
