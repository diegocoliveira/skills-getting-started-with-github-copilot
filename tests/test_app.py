"""Tests for the main API endpoints"""



class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_activities_contains_expected_activities(self, client):
        """Test that GET /activities contains expected activities"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Team",
            "Basketball Club",
            "Art Club",
            "Drama Society",
            "Math Olympiad",
            "Science Club"
        ]
        
        for activity in expected_activities:
            assert activity in data
    
    def test_activity_structure(self, client):
        """Test that each activity has the expected structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up newstudent@mergington.edu for Chess Club" in response.json()["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup adds participant to the activity"""
        email = "newstudent@mergington.edu"
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_email(self, client):
        """Test that duplicate signup returns 400"""
        email = "duplicate@mergington.edu"
        
        # First signup
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Second signup (duplicate)
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_full_activity(self, client):
        """Test signup when activity is full returns 400"""
        # Get activity with smallest max_participants
        response = client.get("/activities")
        activities = response.json()
        
        # Fill up Chess Club (max 12 participants)
        current_participants = len(activities["Chess Club"]["participants"])
        max_participants = activities["Chess Club"]["max_participants"]
        
        # Add participants until full
        for i in range(max_participants - current_participants):
            client.post(
                "/activities/Chess Club/signup",
                params={"email": f"student{i}@mergington.edu"}
            )
        
        # Try to add one more
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "overflow@mergington.edu"}
        )
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]


class TestRemoveParticipant:
    """Tests for the DELETE /activities/{activity_name}/remove endpoint"""
    
    def test_remove_participant_successful(self, client):
        """Test successful removal of a participant"""
        # First add a participant
        email = "toremove@mergington.edu"
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Then remove them
        response = client.delete(
            "/activities/Chess Club/remove",
            params={"email": email}
        )
        assert response.status_code == 200
        assert f"Removed {email} from Chess Club" in response.json()["message"]
    
    def test_remove_participant_verifies_removal(self, client):
        """Test that removal actually removes the participant"""
        # Add a participant
        email = "toremove@mergington.edu"
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Remove them
        client.delete(
            "/activities/Chess Club/remove",
            params={"email": email}
        )
        
        # Verify they're gone
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Chess Club"]["participants"]
    
    def test_remove_nonexistent_activity(self, client):
        """Test removal from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/remove",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_remove_non_participant(self, client):
        """Test removal of non-participant returns 404"""
        response = client.delete(
            "/activities/Chess Club/remove",
            params={"email": "notsignedup@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"]
    
    def test_remove_existing_participant(self, client):
        """Test removing an existing participant from initial data"""
        # Chess Club has "michael@mergington.edu" as an initial participant
        response = client.delete(
            "/activities/Chess Club/remove",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify removal
        response = client.get("/activities")
        activities = response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


class TestIntegration:
    """Integration tests for multiple operations"""
    
    def test_signup_and_remove_workflow(self, client):
        """Test complete workflow of signing up and removing a participant"""
        email = "workflow@mergington.edu"
        activity = "Programming Class"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify count increased
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 1
        
        # Remove
        response = client.delete(
            f"/activities/{activity}/remove",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify count back to initial
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count
    
    def test_multiple_signups_different_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "multitasker@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Art Club"]
        
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify participant is in all activities
        response = client.get("/activities")
        all_activities = response.json()
        
        for activity in activities_to_join:
            assert email in all_activities[activity]["participants"]
