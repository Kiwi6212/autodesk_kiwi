"""Unit tests for Meta API endpoints."""

import pytest
from fastapi import status


class TestMetaEndpoints:
    """Tests for meta information endpoints."""

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"

    def test_get_overview(self, client):
        """Test the overview endpoint."""
        response = client.get("/meta/overview")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Overview should contain quote and other info
        assert "quote" in data or "greeting" in data

    def test_get_quote(self, client):
        """Test the quote endpoint."""
        response = client.get("/meta/quote")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should have content and optionally author
        assert "content" in data
