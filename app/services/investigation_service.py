from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from app.rag.investigation_history import InvestigationHistory


class InvestigationService:
    """
    Application service responsible for orchestrating incident
    investigations and persistence.

    This layer is shared by Streamlit and FastAPI so that both
    interfaces use the same business logic.
    """

    def __init__(
        self,
        incident_directory="data/incidents",
        history_database="data/traceai.db",
    ):
        self.incident_directory = Path(incident_directory)

        # Lazy import keeps this module importable in environments
        # where the ML stack cannot currently initialize.
        from app.rag.investigator import IncidentInvestigator

        self.investigator = IncidentInvestigator(
            str(self.incident_directory)
        )

        self.history = InvestigationHistory(
            history_database
        )

    def list_incidents(self):
        """
        Return all available incident IDs.
        """

        return sorted(
            incident.get("incident_id")
            for incident in self.investigator.store.incidents
            if incident.get("incident_id")
        )

    def incident_exists(self, incident_id):
        """
        Check whether an incident exists.
        """

        return any(
            incident.get("incident_id") == incident_id
            for incident in self.investigator.store.incidents
        )

    def investigate(
        self,
        query,
        incident_id,
        top_k=8,
    ):
        """
        Run an investigation and persist the result.
        """

        query = query.strip()
        incident_id = incident_id.strip()

        if not query:
            raise ValueError(
                "Investigation query cannot be empty."
            )

        if not incident_id:
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

        result = self.investigator.investigate(
            query=query,
            top_k=top_k,
            incident_id=incident_id,
        )

        investigation_id = (
            f"{incident_id}-{uuid4().hex[:12]}"
        )

        history_record = self._build_history_record(
            result=result,
            investigation_id=investigation_id,
        )

        self.history.save_investigation(
            history_record
        )

        result["investigation_id"] = investigation_id

        return result

    def list_investigations(self, limit=25):
        """
        Return persisted investigation history.
        """

        if not 1 <= limit <= 100:
            raise ValueError(
                "limit must be between 1 and 100."
            )

        return self.history.list_investigations(
            limit=limit
        )

    def get_investigation(self, investigation_id):
        """
        Retrieve one persisted investigation.
        """

        return self.history.get_investigation(
            investigation_id
        )

    def delete_investigation(self, investigation_id):
        """
        Delete one persisted investigation.
        """

        return self.history.delete_investigation(
            investigation_id
        )

    @staticmethod
    def _build_history_record(
        result,
        investigation_id,
    ):
        """
        Convert an IncidentInvestigator result into
        the SQLite persistence schema.
        """

        root_cause = result.get(
            "root_cause_details",
            result.get("root_cause", {}),
        )

        groundedness = result.get(
            "groundedness",
            {},
        )

        citation_verification = result.get(
            "citation_verification",
            {},
        )

        claim_verification = result.get(
            "claim_verification",
            {},
        )

        return {
            "investigation_id": investigation_id,
            "incident_id": result.get(
                "incident_id",
                "unknown",
            ),
            "query": result.get(
                "query",
                "",
            ),
            "root_cause": root_cause.get(
                "root_cause",
                "Unknown",
            ),
            "confidence": root_cause.get(
                "confidence",
                result.get(
                    "root_cause_confidence",
                    "LOW",
                ),
            ),
            "confidence_score": root_cause.get(
                "support_score",
                0.0,
            ),
            "analysis": result.get(
                "analysis",
                "",
            ),
            "groundedness_score": groundedness.get(
                "score",
                0.0,
            ),
            "citation_coverage": citation_verification.get(
                "citation_coverage",
                0.0,
            ),
            "claim_coverage": claim_verification.get(
                "claim_coverage"
            ),
        }

    def close(self):
        """
        Close the persistence layer.
        """

        self.history.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.close()


@lru_cache(maxsize=1)
def get_investigation_service():
    """
    Return a cached application service instance.

    The service is intentionally long-lived because
    IncidentInvestigator builds the embedding index during
    initialization.
    """

    return InvestigationService()