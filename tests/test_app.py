import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


class TestRoot:
    """Tests for root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data
    
    def test_activities_have_required_fields(self, client):
        """Test that activities have all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_activities_count(self, client):
        """Test that correct number of activities are returned"""
        response = client.get("/activities")
        data = response.json()
        assert len(data) == 9


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self, client):
        """Test successful student signup"""
        response = client.post(
            "/activities/Basketball Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "signed up" in data["message"].lower()
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Basketball Team"]["participants"]
    
    def test_signup_duplicate_participant(self, client):
        """Test that duplicate signup returns error"""
        # Try to sign up someone already registered
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_multiple_signups(self, client):
        """Test multiple students can sign up for the same activity"""
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        response1 = client.post(f"/activities/Basketball Team/signup?email={email1}")
        response2 = client.post(f"/activities/Basketball Team/signup?email={email2}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both are registered
        activities_response = client.get("/activities")
        participants = activities_response.json()["Basketball Team"]["participants"]
        assert email1 in participants
        assert email2 in participants


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_successful_unregister(self, client):
        """Test successful student unregistration"""
        # First verify the participant is there
        response = client.get("/activities")
        initial_participants = response.json()["Chess Club"]["participants"]
        assert "michael@mergington.edu" in initial_participants
        
        # Unregister
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "unregistered" in data["message"].lower()
        
        # Verify participant was removed
        response = client.get("/activities")
        updated_participants = response.json()["Chess Club"]["participants"]
        assert "michael@mergington.edu" not in updated_participants
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_not_registered_participant(self, client):
        """Test unregister student who is not registered"""
        response = client.delete(
            "/activities/Basketball Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()
    
    def test_unregister_then_signup_again(self, client):
        """Test that a student can re-register after unregistering"""
        email = "testuser@mergington.edu"
        activity = "Basketball Team"
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Verify unregister
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Sign up again
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify re-signup
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]


class TestDataIntegrity:
    """Tests for data integrity and consistency"""
    
    def test_participants_list_integrity(self, client):
        """Test that participants list remains consistent"""
        # Add multiple participants
        emails = ["test1@mergington.edu", "test2@mergington.edu", "test3@mergington.edu"]
        
        for email in emails:
            response = client.post(f"/activities/Soccer Club/signup?email={email}")
            assert response.status_code == 200
        
        # Get activity and verify all are there
        response = client.get("/activities")
        participants = response.json()["Soccer Club"]["participants"]
        
        for email in emails:
            assert email in participants
        
        assert len(participants) == len(emails)
    
    def test_other_activities_unaffected_by_signup(self, client):
        """Test that signing up for one activity doesn't affect others"""
        # Get initial state
        response = client.get("/activities")
        initial_data = response.json()
        
        # Sign up for one activity
        client.post("/activities/Basketball Team/signup?email=newuser@mergington.edu")
        
        # Check other activities are unchanged
        response = client.get("/activities")
        updated_data = response.json()
        
        # Chess Club participants should be the same
        assert updated_data["Chess Club"]["participants"] == initial_data["Chess Club"]["participants"]
        assert updated_data["Art Club"]["participants"] == initial_data["Art Club"]["participants"]
    
    def test_activity_metadata_preserved(self, client):
        """Test that activity metadata is preserved after operations"""
        # Get initial data
        response = client.get("/activities")
        initial_data = response.json()["Programming Class"].copy()
        
        # Perform signup/unregister operations
        client.post("/activities/Programming Class/signup?email=test@mergington.edu")
        client.delete("/activities/Programming Class/unregister?email=test@mergington.edu")
        
        # Check metadata is unchanged
        response = client.get("/activities")
        updated_data = response.json()["Programming Class"]
        
        assert updated_data["description"] == initial_data["description"]
        assert updated_data["schedule"] == initial_data["schedule"]
        assert updated_data["max_participants"] == initial_data["max_participants"]
