from pathlib import Path
import tempfile

from app.rag.investigator import IncidentInvestigator
from app.rag.investigation_history import InvestigationHistory


def main():
    print("=" * 70)
    print("TRACEAI — REAL INVESTIGATION PERSISTENCE TEST")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "traceai_test.db"

        # ---------------------------------------------------------
        # 1. Run the real TraceAI investigation
        # ---------------------------------------------------------
        investigator = IncidentInvestigator(
            "data/incidents"
        )

        result = investigator.investigate(
            query=(
                "Why could the payment service not "
                "acquire a database connection?"
            ),
            top_k=8,
            incident_id="legacy_incident",
        )

        # ---------------------------------------------------------
        # 2. Extract REAL production result fields
        # ---------------------------------------------------------
        root_cause = result["root_cause"]

        root_cause_name = root_cause["root_cause"]

        confidence = root_cause.get(
            "confidence",
            "UNKNOWN",
        )

        confidence_score = root_cause.get(
            "support_score",
            0.0,
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

        groundedness_score = groundedness.get(
            "score",
            0.0,
        )

        citation_coverage = citation_verification.get(
            "citation_coverage",
            0.0,
        )

        claim_coverage = claim_verification.get(
            "claim_coverage"
        )

        # ---------------------------------------------------------
        # 3. Build persistence record
        # ---------------------------------------------------------
        investigation = {
            "investigation_id": "integration-test-001",
            "incident_id": "legacy_incident",
            "query": (
                "Why could the payment service not "
                "acquire a database connection?"
            ),
            "root_cause": root_cause_name,
            "confidence": confidence,
            "confidence_score": confidence_score,
            "analysis": result.get(
                "analysis",
                "",
            ),
            "groundedness_score": groundedness_score,
            "citation_coverage": citation_coverage,
            "claim_coverage": claim_coverage,
        }

        # ---------------------------------------------------------
        # 4. Persist the real result
        # ---------------------------------------------------------
        history = InvestigationHistory(
            db_path
        )

        saved = history.save_investigation(
            investigation
        )

        assert saved is True

        print("\nPASS: Real investigation saved")

        # ---------------------------------------------------------
        # 5. Retrieve it
        # ---------------------------------------------------------
        stored = history.get_investigation(
            "integration-test-001"
        )

        assert stored is not None

        assert (
            stored["incident_id"]
            == "legacy_incident"
        )

        assert (
            stored["root_cause"]
            == "Connection pool exhaustion"
        )

        assert (
            stored["confidence"]
            == "HIGH"
        )

        assert (
            stored["confidence_score"]
            == 1.0
        )

        assert (
            stored["groundedness_score"]
            == 1.0
        )

        assert (
            stored["citation_coverage"]
            == 1.0
        )

        assert (
            stored["claim_coverage"]
            is None
        )

        print("PASS: Real investigation retrieved")

        # ---------------------------------------------------------
        # 6. Verify history
        # ---------------------------------------------------------
        records = history.list_investigations()

        assert len(records) == 1

        print(
            "PASS: Real investigation appears in history"
        )

        # ---------------------------------------------------------
        # 7. Print persisted values
        # ---------------------------------------------------------
        print("\nStored Investigation:")
        print(
            f"Investigation ID : "
            f"{stored['investigation_id']}"
        )
        print(
            f"Incident ID      : "
            f"{stored['incident_id']}"
        )
        print(
            f"Root Cause       : "
            f"{stored['root_cause']}"
        )
        print(
            f"Confidence       : "
            f"{stored['confidence']}"
        )
        print(
            f"Support Score    : "
            f"{stored['confidence_score']}"
        )
        print(
            f"Groundedness     : "
            f"{stored['groundedness_score']}"
        )
        print(
            f"Citation Coverage: "
            f"{stored['citation_coverage']}"
        )
        print(
            f"Claim Coverage   : "
            f"{stored['claim_coverage']}"
        )

        history.close()

    print("\n" + "=" * 70)
    print(
        "REAL INVESTIGATION PERSISTENCE TEST PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()