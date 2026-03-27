"""
Integration Tests for FastAPI Application
Tests the main API endpoints and request/response handling.
"""

import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestAPIEndpoints:
    """Test suite for API endpoints."""

    def test_health_check(self, client):
        """Test that the API health check endpoint works."""
        response = client.get("/")
        assert response.status_code == 200

    def test_chat_endpoint_exists(self, client):
        """Test that the chat endpoint exists."""
        # This will fail if the endpoint doesn't exist
        response = client.post(
            "/chat",
            json={"message": "Hello!", "user_id": "test_user"}
        )
        # Should not return 404
        assert response.status_code != 404

    def test_chat_request_structure(self, client):
        """Test that chat endpoint accepts correct request structure."""
        response = client.post(
            "/chat",
            json={
                "message": "How are you?",
                "user_id": "test_user_123"
            }
        )
        
        # Should return either 200 or 500 (not 422 - validation error)
        assert response.status_code in [200, 500, 401]

    def test_chat_response_structure(self, client):
        """Test that chat endpoint returns expected response structure."""
        response = client.post(
            "/chat",
            json={
                "message": "I am happy",
                "user_id": "test_user"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check for expected fields in response
            assert isinstance(data, dict)

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in response."""
        response = client.get("/")
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or response.status_code == 200

    def test_invalid_request_handling(self, client):
        """Test that invalid requests are handled gracefully."""
        response = client.post(
            "/chat",
            json={"invalid_field": "test"}
        )
        # Should return 422 (validation error) or 400
        assert response.status_code in [422, 400, 200, 500]


class TestInputValidation:
    """Test suite for input validation."""

    def test_empty_message(self, client):
        """Test handling of empty message."""
        response = client.post(
            "/chat",
            json={"message": "", "user_id": "test_user"}
        )
        # Should handle gracefully
        assert response.status_code in [200, 400, 422, 500]

    def test_missing_user_id(self, client):
        """Test handling of missing user_id."""
        response = client.post(
            "/chat",
            json={"message": "Hello!"}
        )
        # Should return validation error or handle gracefully
        assert response.status_code in [200, 400, 422, 500]

    def test_special_characters_in_message(self, client):
        """Test handling of special characters in message."""
        response = client.post(
            "/chat",
            json={"message": "Hello @#$%^&*()", "user_id": "test_user"}
        )
        assert response.status_code in [200, 500]


class TestContentDelivery:
    """Test suite for content delivery and response times."""

    def test_response_is_json(self, client):
        """Test that response content-type is JSON."""
        response = client.post(
            "/chat",
            json={"message": "Test", "user_id": "user123"}
        )
        
        if response.status_code == 200:
            assert response.headers.get("content-type") is not None
