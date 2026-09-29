from app.rag.citation_repair import CitationRepairer


def build_test_evidence():
    return [
        {
            "text": "Connection pool exhausted",
            "source_type": "log",
            "provenance": "observed",
            "source_file": "upload_test.log",
            "location": "line 3",
        },
        {
            "text": "Active connections: 20/20",
            "source_type": "log",
            "provenance": "observed",
            "source_file": "upload_test.log",
            "location": "line 2",
        },
        {
            "text": "Unable to acquire database connection",
            "source_type": "log",
            "provenance": "observed",
            "source_file": "upload_test.log",
            "location": "line 4",
        },
        {
            "text": "Order processing failed",
            "source_type": "log",
            "provenance": "observed",
            "source_file": "upload_test.log",
            "location": "line 5",
        },
    ]


def test_invalid_citation_repair():

    repairer = CitationRepairer()

    evidence = build_test_evidence()

    analysis = (
        "Connection pool exhausted "
        "[incident_001.log:line 4]"
    )

    result = repairer.repair(
        analysis=analysis,
        evidence=evidence,
    )

    assert result["repair_count"] == 1

    assert (
        "[upload_test.log:line 3]"
        in result["analysis"]
    )

    assert (
        "[incident_001.log:line 4]"
        not in result["analysis"]
    )

    print("PASS: invalid citation repaired")


def test_missing_citation_added():

    repairer = CitationRepairer()

    evidence = build_test_evidence()

    analysis = (
        "1. Connection pool exhausted"
    )

    result = repairer.repair(
        analysis=analysis,
        evidence=evidence,
    )

    assert result["repair_count"] == 1

    assert (
        "[upload_test.log:line 3]"
        in result["analysis"]
    )

    print("PASS: missing citation added")


def test_valid_citation_unchanged():

    repairer = CitationRepairer()

    evidence = build_test_evidence()

    analysis = (
        "Connection pool exhausted "
        "[upload_test.log:line 3]"
    )

    result = repairer.repair(
        analysis=analysis,
        evidence=evidence,
    )

    assert result["repair_count"] == 0

    assert result["analysis"] == analysis

    print("PASS: valid citation unchanged")


def test_unsupported_claim_not_repaired():

    repairer = CitationRepairer()

    evidence = build_test_evidence()

    analysis = (
        "The database server crashed"
    )

    result = repairer.repair(
        analysis=analysis,
        evidence=evidence,
    )

    assert result["repair_count"] == 0

    assert (
        result["analysis"]
        == analysis
    )

    print("PASS: unsupported claim not repaired")


def test_historical_citation_uses_current_evidence():

    repairer = CitationRepairer()

    evidence = build_test_evidence()

    analysis = (
        "Unable to acquire database connection "
        "[incident_001.log:line 5]"
    )

    result = repairer.repair(
        analysis=analysis,
        evidence=evidence,
    )

    assert result["repair_count"] == 1

    assert (
        "[upload_test.log:line 4]"
        in result["analysis"]
    )

    assert (
        "[incident_001.log:line 5]"
        not in result["analysis"]
    )

    print(
        "PASS: historical citation replaced "
        "with current evidence"
    )


def test_empty_evidence():

    repairer = CitationRepairer()

    analysis = (
        "Connection pool exhausted"
    )

    result = repairer.repair(
        analysis=analysis,
        evidence=[],
    )

    assert result["repair_count"] == 0

    assert (
        result["analysis"]
        == analysis
    )

    print("PASS: empty evidence handled")


def main():

    print("=" * 70)
    print(
        "TRACEAI — CITATION REPAIR TESTS"
    )
    print("=" * 70)

    test_invalid_citation_repair()
    test_missing_citation_added()
    test_valid_citation_unchanged()
    test_unsupported_claim_not_repaired()
    test_historical_citation_uses_current_evidence()
    test_empty_evidence()

    print("=" * 70)
    print(
        "ALL CITATION REPAIR TESTS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()