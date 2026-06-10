from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.app.config import ApiSettings
from backend.app.contracts.events import make_event
from backend.app.main import create_app


class ApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(ApiSettings(capture_enabled=False))
        self.client_context = TestClient(self.app)
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)

    def test_health_reports_capture_disabled_without_camera(self) -> None:
        response = self.client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertFalse(payload["capture"]["enabled"])

    def test_catalog_exposes_profiles_and_default(self) -> None:
        response = self.client.get("/api/v1/catalog")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["default_profile_id"], "neutral")
        self.assertEqual(
            {profile["id"] for profile in payload["profiles"]},
            {"neutral", "happy", "sad", "angry"},
        )

    def test_session_can_select_profile_through_rest(self) -> None:
        created = self.client.post("/api/v1/sessions")
        session_id = created.json()["id"]

        response = self.client.patch(
            f"/api/v1/sessions/{session_id}/profile",
            json={"profile_id": "raiva"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["selected_profile"], "angry")

    def test_unknown_profile_returns_validation_error(self) -> None:
        session_id = self.client.post("/api/v1/sessions").json()["id"]

        response = self.client.patch(
            f"/api/v1/sessions/{session_id}/profile",
            json={"profile_id": "unknown"},
        )

        self.assertEqual(response.status_code, 422)

    def test_websocket_uses_versioned_profile_event(self) -> None:
        session_id = self.client.post("/api/v1/sessions").json()["id"]

        with self.client.websocket_connect(
            f"/api/v1/sessions/{session_id}/stream"
        ) as websocket:
            connected = websocket.receive_json()
            self.assertEqual(connected["type"], "session.status.v1")
            self.assertEqual(connected["schema_version"], "1.0")

            websocket.send_json(
                {
                    "schema_version": "1.0",
                    "type": "profile.select.v1",
                    "data": {"profile_id": "happy"},
                }
            )
            selected = websocket.receive_json()

        self.assertEqual(selected["type"], "profile.selected.v1")
        self.assertEqual(
            selected["data"]["session"]["selected_profile"],
            "happy",
        )

    def test_event_envelope_serializes_schema_and_data(self) -> None:
        payload = make_event(
            "music.state.v1",
            {"note_label": "C4", "active": True},
            session_id="session-test",
        ).model_dump(mode="json")

        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["session_id"], "session-test")
        self.assertEqual(payload["data"]["note_label"], "C4")


if __name__ == "__main__":
    unittest.main()
