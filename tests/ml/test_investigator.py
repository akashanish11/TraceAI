from app.rag.investigator import (
    IncidentInvestigator
)


def main():

    investigator = IncidentInvestigator(
        "data/incidents"
    )

    query = (
        "What caused the payment service "
        "database failure?"
    )

    result = investigator.investigate(
        query,
        top_k=8
    )

    print("\n" + "=" * 70)
    print("TRACEAI ROOT CAUSE INVESTIGATION")
    print("=" * 70)

    print("\nQUESTION:")
    print(result["query"])

    print("\n" + "-" * 70)
    print("AI INVESTIGATION")
    print("-" * 70)

    print(result["analysis"])

    # ---------------------------------------------------------
    # Citation verification
    # ---------------------------------------------------------

    print("\n" + "-" * 70)
    print("CITATION VERIFICATION")
    print("-" * 70)

    verification = result[
        "citation_verification"
    ]

    print(
        f"Total Citations    : "
        f"{verification['total_citations']}"
    )

    print(
        f"Verified Citations : "
        f"{verification['verified_citations']}"
    )

    print(
        f"Citation Coverage  : "
        f"{verification['citation_coverage']:.2%}"
    )

    if verification[
        "has_unverified_citations"
    ]:
        print(
            "Status             : "
            "WARNING - Unverified citations found"
        )
    else:
        print(
            "Status             : "
            "PASS - All citations verified"
        )

    # ---------------------------------------------------------
    # Deterministic evidence confidence
    # ---------------------------------------------------------

    print("\n" + "-" * 70)
    print("TRACEAI GROUNDED CONFIDENCE")
    print("-" * 70)

    confidence = result[
        "evidence_confidence"
    ]

    print(
        f"Grounded Confidence : "
        f"{confidence['confidence']}"
    )

    print(
        f"Support Score       : "
        f"{confidence['score']:.2f}"
    )

    print(
        f"Observed Root Cause : "
        f"{confidence['observed_root_cause']}"
    )

    print(
        f"Stacktrace Support  : "
        f"{confidence['stacktrace_confirmation']}"
    )

    print(
        f"Code Support        : "
        f"{confidence['code_confirmation']}"
    )

    print(
        f"Failure Support     : "
        f"{confidence['failure_confirmation']}"
    )

    print(
        f"Supporting Sources  : "
        f"{confidence['supporting_source_count']}"
    )

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()