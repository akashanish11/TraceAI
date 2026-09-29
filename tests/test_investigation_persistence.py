from pathlib import Path
import tempfile

from app.rag.investigation_history import InvestigationHistory


def main():
    print("=" * 70)
    print("TRACEAI — INVESTIGATION PERSISTENCE TEST")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "traceai_test.db"

        history = InvestigationHistory(db_path)

        # ---------------------------------------------------------
        # 1. Database initialization
        # ---------------------------------------------------------
        assert db_path.exists(), "Database file was not created"
        print("\nPASS: SQLite database created")

        # ---------------------------------------------------------
        # 2. Save investigation
        # ---------------------------------------------------------
        investigation = {
            "investigation_id": "test-investigation-001",
            "incident_id": "legacy_incident",
            "query": (
                "Why did the payment service fail "
                "to acquire a database connection?"
            ),
            "root_cause": "Connection pool exhaustion",
            "confidence": "HIGH",
            "confidence_score": 0.95,
            "analysis": (
                "The payment service could not acquire a database "
                "connection because the connection pool was exhausted."
            ),
            "groundedness_score": 1.0,
            "citation_coverage": 1.0,
            "claim_coverage": None,
        }

        saved = history.save_investigation(investigation)

        assert saved is True
        print("PASS: Investigation saved")

        # ---------------------------------------------------------
        # 3. Retrieve investigation by ID
        # ---------------------------------------------------------
        retrieved = history.get_investigation(
            "test-investigation-001"
        )

        assert retrieved is not None
        assert (
            retrieved["investigation_id"]
            == "test-investigation-001"
        )
        assert (
            retrieved["root_cause"]
            == "Connection pool exhaustion"
        )
        assert retrieved["confidence_score"] == 0.95

        print("PASS: Investigation retrieved")

        # ---------------------------------------------------------
        # 4. List investigation history
        # ---------------------------------------------------------
        investigations = history.list_investigations()

        assert len(investigations) == 1
        assert (
            investigations[0]["investigation_id"]
            == "test-investigation-001"
        )

        print("PASS: Investigation history listed")

        # ---------------------------------------------------------
        # 5. Save second investigation
        # ---------------------------------------------------------
        second = {
            "investigation_id": "test-investigation-002",
            "incident_id": "synthetic_004",
            "query": "Why did the service fail?",
            "root_cause": "Connection pool exhaustion",
            "confidence": "MEDIUM",
            "confidence_score": 0.65,
            "analysis": "Database connections were exhausted.",
            "groundedness_score": 0.90,
            "citation_coverage": 1.0,
            "claim_coverage": None,
        }

        assert history.save_investigation(second) is True

        investigations = history.list_investigations()

        assert len(investigations) == 2

        print("PASS: Multiple investigations stored")

        # ---------------------------------------------------------
        # 6. Delete investigation
        # ---------------------------------------------------------
        deleted = history.delete_investigation(
            "test-investigation-001"
        )

        assert deleted is True

        assert (
            history.get_investigation(
                "test-investigation-001"
            )
            is None
        )

        assert len(history.list_investigations()) == 1

        print("PASS: Investigation deleted")

        # ---------------------------------------------------------
        # Final
        # ---------------------------------------------------------
        history.close()

    print("\n" + "=" * 70)
    print("ALL INVESTIGATION PERSISTENCE TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()