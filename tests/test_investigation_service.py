import pytest

from app.services.investigation_service import InvestigationService


class FakeHistory:
    def __init__(self, database_path=None):
        self.records = {}

    def save_investigation(self, record):
        self.records[record["investigation_id"]] = record

    def get_investigation(self, investigation_id):
        return self.records.get(investigation_id)

    def list_investigations(self, limit=None):
        records = list(self.records.values())

        if limit is not None:
            records = records[:limit]

        return records

    def delete_investigation(self, investigation_id):
        if investigation_id in self.records:
            del self.records[investigation_id]
            return True

        return False

    def close(self):
        pass


class FakeStore:
    incidents = [
        {"incident_id": "incident_001"},
        {"incident_id": "incident_002"},
        {"incident_id": "incident_003"},
    ]


class FakeInvestigator:
    def __init__(self):
        self.store = FakeStore()

    def investigate(self, query, top_k, incident_id):
        return {
            "query": query,
            "incident_id": incident_id,
            "root_cause": {
                "root_cause": "Connection pool exhaustion",
                "confidence": "HIGH",
                "support_score": 1.0,
            },
            "root_cause_confidence": "HIGH",
            "root_cause_details": {
                "root_cause": "Connection pool exhaustion",
                "confidence": "HIGH",
                "support_score": 1.0,
            },
            "analysis": (
                "The database connection pool was exhausted. "
                "[incident_001.log:line 4]"
            ),
            "evidence": [],
            "historical_incidents": [],
            "context": "",
            "citation_repair": {},
            "citation_verification": {
                "citation_coverage": 1.0,
            },
            "claim_verification": {
                "claim_coverage": None,
            },
            "groundedness": {
                "score": 1.0,
            },
            "evidence_confidence": {
                "score": 1.0,
            },
        }


@pytest.fixture
def service():
    service = object.__new__(InvestigationService)

    service.investigator = FakeInvestigator()
    service.history = FakeHistory()

    return service


def test_list_incidents(service):
    incidents = service.list_incidents()

    assert incidents == [
        "incident_001",
        "incident_002",
        "incident_003",
    ]


def test_incident_exists(service):
    assert service.incident_exists("incident_001") is True
    assert service.incident_exists("does_not_exist") is False


def test_empty_query_rejected(service):
    with pytest.raises(
        ValueError,
        match="Investigation query cannot be empty",
    ):
        service.investigate(
            query="   ",
            incident_id="incident_001",
        )


def test_empty_incident_rejected(service):
    with pytest.raises(
        ValueError,
        match="Incident ID cannot be empty",
    ):
        service.investigate(
            query="Why did it fail?",
            incident_id="   ",
        )


def test_unknown_incident_rejected(service):
    with pytest.raises(
        ValueError,
        match="was not found",
    ):
        service.investigate(
            query="Why did it fail?",
            incident_id="unknown",
        )


def test_invalid_top_k_rejected(service):
    with pytest.raises(
        ValueError,
        match="top_k must be between 1 and 50",
    ):
        service.investigate(
            query="Why did it fail?",
            incident_id="incident_001",
            top_k=0,
        )


def test_investigation_runs_and_persists(service):
    result = service.investigate(
        query="Why did the database connection fail?",
        incident_id="incident_001",
        top_k=8,
    )

    assert result["incident_id"] == "incident_001"

    assert result["root_cause"]["root_cause"] == (
        "Connection pool exhaustion"
    )

    assert "investigation_id" in result

    investigation_id = result["investigation_id"]

    stored = service.get_investigation(investigation_id)

    assert stored is not None
    assert stored["investigation_id"] == investigation_id
    assert stored["incident_id"] == "incident_001"
    assert stored["root_cause"] == "Connection pool exhaustion"
    assert stored["confidence"] == "HIGH"
    assert stored["confidence_score"] == 1.0


def test_list_investigations(service):
    service.investigate(
        query="Why did it fail?",
        incident_id="incident_001",
    )

    service.investigate(
        query="What caused the error?",
        incident_id="incident_002",
    )

    history = service.list_investigations(limit=10)

    assert len(history) == 2


def test_delete_investigation(service):
    result = service.investigate(
        query="Why did it fail?",
        incident_id="incident_001",
    )

    investigation_id = result["investigation_id"]

    assert service.get_investigation(investigation_id) is not None

    deleted = service.delete_investigation(investigation_id)

    assert deleted is True
    assert service.get_investigation(investigation_id) is None


def test_delete_missing_investigation(service):
    deleted = service.delete_investigation(
        "does-not-exist"
    )

    assert deleted is False