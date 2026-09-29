from app.rag.investigator import IncidentInvestigator


def main():
    print("=" * 70)
    print("TRACEAI — LLM INVESTIGATION REGRESSION TEST")
    print("=" * 70)

    investigator = IncidentInvestigator("data/incidents")

    query = (
        "Why did the payment service fail to acquire "
        "a database connection?"
    )

    print("\nRunning investigation...\n")

    result = investigator.investigate(
        query=query,
        top_k=5,
        incident_id="legacy_incident",
    )

    # ---------------------------------------------------------
    # 1. Root cause
    # ---------------------------------------------------------

    root_cause = result["root_cause"]["root_cause"]

    print("Root Cause:")
    print(root_cause)

    assert root_cause == "Connection pool exhaustion", (
        f"Unexpected root cause: {root_cause}"
    )

    print("ROOT CAUSE TEST: PASS")

    # ---------------------------------------------------------
    # 2. Historical matching
    # ---------------------------------------------------------

    historical = result["historical_incidents"]

    print("\nHistorical Matches:")

    for match in historical:
        print(
            f"- {match['incident_id']} "
            f"(similarity={match['similarity']:.3f})"
        )

    assert len(historical) > 0, (
        "No historical incidents were returned."
    )

    assert all(
        match["incident_id"] != "legacy_incident"
        for match in historical
    ), (
        "Current incident incorrectly appeared "
        "as a historical match."
    )

    assert all(
        "incident" in match and match["incident"]
        for match in historical
    ), (
        "Historical match does not contain "
        "incident context."
    )

    print("HISTORICAL MATCHING TEST: PASS")

    # ---------------------------------------------------------
    # 3. LLM analysis
    # ---------------------------------------------------------

    analysis = result["analysis"]

    print("\nLLM Analysis:")
    print("-" * 70)
    print(analysis)
    print("-" * 70)

    assert analysis.strip(), (
        "LLM returned an empty analysis."
    )

    required_sections = [
        "### 1. ROOT CAUSE",
        "### 2. FAILURE CHAIN",
        "### 3. IMPACT",
        "### 4. EVIDENCE",
    ]

    for section in required_sections:
        assert section in analysis, (
            f"Missing required section: {section}"
        )

    print("LLM OUTPUT STRUCTURE TEST: PASS")

    # ---------------------------------------------------------
    # 4. Citation verification
    # ---------------------------------------------------------

    citation_result = result["citation_verification"]

    print("\nCitation Verification:")
    print(citation_result)

    assert citation_result["status"] == "PASS", (
        "Citation verification failed."
    )

    assert citation_result["citation_coverage"] == 1.0, (
        "Citation coverage is below 100%."
    )

    assert citation_result["has_unverified_citations"] is False, (
        "Unverified citations detected."
    )

    print("CITATION VERIFICATION TEST: PASS")

    # ---------------------------------------------------------
    # 5. Claim verification
    # ---------------------------------------------------------

    claim_result = result["claim_verification"]

    print("\nClaim Verification:")
    print(claim_result)

    assert claim_result["has_unsupported_claims"] is False, (
        "Unsupported claims detected."
    )

    print("CLAIM VERIFICATION TEST: PASS")

    # ---------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("LLM INVESTIGATION REGRESSION SUMMARY")
    print("=" * 70)

    print("Root Cause             : PASS")
    print("Historical Matching    : PASS")
    print("LLM Output Structure   : PASS")
    print("Citation Verification  : PASS")
    print("Claim Verification     : PASS")

    print("=" * 70)
    print("STATUS: LLM INVESTIGATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()