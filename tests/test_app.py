"""
Tests for the Mergington High School API

Tests cover:
- Getting all activities
- Signing up for activities
- Unregistering from activities
- Error handling and validation
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to known state before each test"""
    # Store original state
    original_state = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state
    for name, activity_data in original_state.items():
        activities[name]["participants"] = activity_data["participants"]


class TestGetActivities:
    """Test the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "Baseball Team" in data
        assert "Tennis Club" in data
        assert "Programming Class" in data
    
    def test_get_activity_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Check Baseball Team structure
        baseball = data["Baseball Team"]
        assert "description" in baseball
        assert "schedule" in baseball
        assert "max_participants" in baseball
        assert "participants" in baseball
        assert isinstance(baseball["participants"], list)


class TestSignUp:
    """Test the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity(self, client, reset_activities):
        """Test successful signup for an activity"""
        activity_name = "Baseball Team"
        email = "newstudent@mergington.edu"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_already_signed_up(self, client, reset_activities):
        """Test that a student can't sign up twice for the same activity"""
        activity_name = "Baseball Team"
        email = "alex@mergington.edu"  # Already signed up
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_multiple_students(self, client, reset_activities):
        """Test that multiple different students can sign up"""
        activity_name = "Tennis Club"
        students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in students:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all students are signed up
        assert all(email in activities[activity_name]["participants"] for email in students)


class TestUnregister:
    """Test the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_from_activity(self, client, reset_activities):
        """Test successful unregistration from an activity"""
        activity_name = "Baseball Team"
        email = "alex@mergington.edu"  # Already signed up
        
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_not_signed_up(self, client, reset_activities):
        """Test that a student can't unregister if they're not signed up"""
        activity_name = "Baseball Team"
        email = "notstudent@mergington.edu"  # Not signed up
        
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_signup_and_unregister(self, client, reset_activities):
        """Test the full flow of signing up and then unregistering"""
        activity_name = "Chess Club"
        email = "chessplayer@mergington.edu"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        assert email in activities[activity_name]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        assert email not in activities[activity_name]["participants"]


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static content"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
