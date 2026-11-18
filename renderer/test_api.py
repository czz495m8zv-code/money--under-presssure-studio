import os
import unittest
from fastapi.testclient import TestClient

os.environ["STUDIO_API_TOKEN"] = "test-token"

from renderer.api import app


class RenderApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer test-token"}

    def test_health_is_public(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_render_requires_token(self):
        response = self.client.post("/v1/renders", json={"title": "Test"})
        self.assertEqual(response.status_code, 401)

    def test_create_render_returns_job_id(self):
        response = self.client.post(
            "/v1/renders",
            headers=self.headers,
            json={
                "title": "Test finance video",
                "subtitle": "A test subtitle",
                "duration_seconds": 5,
                "fps": 24,
                "chart": [{"label": "2024", "value": 50}]
            }
        )
        self.assertEqual(response.status_code, 202)
        self.assertIn("job_id", response.json())
        self.assertEqual(response.json()["status"], "queued")

    def test_rejects_invalid_duration(self):
        response = self.client.post(
            "/v1/renders",
            headers=self.headers,
            json={"title": "Invalid", "duration_seconds": 1000}
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
