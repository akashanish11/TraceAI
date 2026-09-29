from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api.main as api_main
from app.rag.investigation_history import InvestigationHistory


client = TestClient(api_main.app)


class FakeService:
    def __init__(self):
        self.incidents = [
            "legacy_incident",
            "synthetic_001",
            "synthetic_002",
        ]

        self.investigations = {}

    def list_incidents(self):
        return self.incidents

    def incident_exists(self, incident_id):
        return incident_id in self.incidents

    def investigate(
        self,
        query,
        incident_id,
        top_k=8,
    ):
        if not query.strip():
            raise ValueError(
                "Investigation query cannot be empty."
            )

        if not incident_id.strip():
            raise ValueError(
                "Incident ID cannot be empty."
            )

        if not self.incident_exists(incident_id):
            raise ValueError(
                f"Incident '{incident_id}' was not found."
            )

        if not 1 <= top_k <= 50:
            raise ValueError(
                "top_k must be between 1 and 50."
            )

        investigation_id = (
            f"{incident_id}-test001"
        )

        result = {
            "investigation_id": investigation_id,
            "incident_id": incident_id,
            "query": query,
            "root_cause": {
                "root_cause": (
                    "Connection pool exhaustion"
                ),
                "confidence": "HIGH",
                "support_score": 1.0,
                "explanation": (
                    "The database connection pool "
                    "was exhausted."
                ),
            },
            "root_cause_confidence": "HIGH",
            "root_cause_details": {
                "root_cause": (
                    "Connection pool exhaustion"
                ),
                "confidence": "HIGH",
                "support_score": 1.0,
                "explanation": (
                    "The database connection pool "
                    "was exhausted."
                ),
            },
            "analysis": (
                "The database connection pool "
                "was exhausted. "
                "[incident.log:line 4]"
            ),
            "evidence": [
                {
                    "text": (
                        "Connection pool exhausted"
                    ),
                    "source_type": "log",
                    "provenance": "observed",
                    "source_file": "incident.log",
                    "location": "line 4",
                    "metadata": {},
                }
            ],
            "citation_verification": {
                "citation_coverage": 1.0,
                "status": "PASS",
            },
            "groundedness": {
                "score": 1.0,
                "level": "HIGH",
            },
            "claim_verification": {
                "claim_coverage": None,
                "status": "PASS",
            },
        }

        self.investigations[investigation_id] = {
            "investigation_id": investigation_id,
            "incident_id": incident_id,
            "query": query,
            "root_cause": (
                "Connection pool exhaustion"
            ),
            "confidence": "HIGH",
            "confidence_score": 1.0,
            "analysis": result["analysis"],
            "groundedness_score": 1.0,
            "citation_coverage": 1.0,
            "claim_coverage": None,
            "created_at": (
                "2026-09-29T00:00:00+00:00"
            ),
        }

        return result

    def list_investigations(self, limit=25):
        records = list(
            self.investigations.values()
        )

        return records[:limit]

    def get_investigation(
        self,
        investigation_id,
    ):
        return self.investigations.get(
            investigation_id
        )

    def delete_investigation(
        self,
        investigation_id,
    ):
        if investigation_id not in self.investigations:
            return False

        del self.investigations[
            investigation_id
        ]

        return True


@pytest.fixture
def fake_service(monkeypatch):
    service = FakeService()

    monkeypatch.setattr(
        api_main,
        "get_service",
        lambda: service,
    )

    return service


def test_api_v1_health():
    response = client.get(
        "/api/v1/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "traceai-api"
    assert data["version"] == "v1"


def test_api_v1_incidents(fake_service):
    response = client.get(
        "/api/v1/incidents"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 3

    assert data["incidents"] == [
        "legacy_incident",
        "synthetic_001",
        "synthetic_002",
    ]


def test_api_v1_investigation_crud(
    fake_service,
):
    payload = {
        "incident_id": "legacy_incident",
        "query": (
            "Why did the payment fail?"
        ),
        "top_k": 8,
    }

    response = client.post(
        "/api/v1/investigations",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["incident_id"] == (
        "legacy_incident"
    )

    assert data["root_cause"]["name"] == (
        "Connection pool exhaustion"
    )

    assert data["root_cause"]["confidence"] == (
        "HIGH"
    )

    assert data["verification"][
        "citation_coverage"
    ] == 1.0

    investigation_id = data[
        "investigation_id"
    ]

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation_id}"
    )

    assert response.status_code == 200

    history = response.json()

    assert history["investigation_id"] == (
        investigation_id
    )

    response = client.get(
        "/api/v1/investigations"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 1

    response = client.delete(
        f"/api/v1/investigations/"
        f"{investigation_id}"
    )

    assert response.status_code == 200

    assert response.json()["status"] == (
        "deleted"
    )

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation_id}"
    )

    assert response.status_code == 404


def test_api_v1_investigation_invalid_incident(
    fake_service,
):
    payload = {
        "incident_id": "does_not_exist",
        "query": "Why did it fail?",
        "top_k": 8,
    }

    response = client.post(
        "/api/v1/investigations",
        json=payload,
    )

    assert response.status_code == 400

    assert "was not found" in (
        response.json()["detail"]
    )


def test_api_v1_investigation_validation(
    fake_service,
):
    payload = {
        "incident_id": "legacy_incident",
        "query": "Why did it fail?",
        "top_k": 0,
    }

    response = client.post(
        "/api/v1/investigations",
        json=payload,
    )

    assert response.status_code == 422


def test_api_v1_history_limit(
    fake_service,
):
    for index in range(5):
        fake_service.investigate(
            query=f"Question {index}",
            incident_id="legacy_incident",
            top_k=8,
        )

        # Make IDs unique for this test fixture.
        old_id = (
            "legacy_incident-test001"
        )

        record = fake_service.investigations.pop(
            old_id
        )

        new_id = (
            f"legacy_incident-test{index:03d}"
        )

        record["investigation_id"] = new_id

        fake_service.investigations[
            new_id
        ] = record

    response = client.get(
        "/api/v1/investigations?limit=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 2
    assert len(data["investigations"]) == 2


def test_api_v1_history_not_found(
    fake_service,
):
    response = client.get(
        "/api/v1/investigations/"
        "does-not-exist"
    )

    assert response.status_code == 404


def test_api_v1_delete_not_found(
    fake_service,
):
    response = client.delete(
        "/api/v1/investigations/"
        "does-not-exist"
    )

    assert response.status_code == 404