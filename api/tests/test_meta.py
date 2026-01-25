"""Unit tests for Meta API endpoints."""

from fastapi import status


class TestMetaEndpoints:
    """Tests for meta information endpoints."""

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/meta/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_get_overview(self, client):
        """Test the overview endpoint."""
        response = client.get("/meta/overview")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "quote" in data
        assert "quote_author" in data

    def test_get_quote(self, client):
        """Test the quote endpoint."""
        response = client.get("/meta/quote")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "content" in data
        assert "author" in data
