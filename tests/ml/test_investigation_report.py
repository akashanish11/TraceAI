from app.rag.investigator import (
    IncidentInvestigator
)

from app.analysis.investigation_report import (
    InvestigationReport
)


def main():

    investigator = IncidentInvestigator(
        "data/incidents"
    )

    query = (
        "What caused the payment service "
        "database failure?"
    )

    investigation = investigator.investigate(
        query,
        top_k=8,
        incident_id="legacy_incident"
    )

    report_builder = InvestigationReport()

    report = report_builder.build(
        investigation
    )

    print("\n" + "=" * 70)
    print("TRACEAI FINAL INVESTIGATION REPORT")
    print("=" * 70)

    print("\nQUESTION:")
    print(report["query"])

    # =========================================================
    # ROOT CAUSE
    # =========================================================

    print("\n" + "-" * 70)
    print("ROOT CAUSE")
    print("-" * 70)

    print(
        report["root_cause"]["name"]
    )

    print(
        "\nExplanation:"
    )

    print(
        report["root_cause"]["explanation"]
    )

    print(
        "\nConfidence: "
        f"{report['root_cause']['confidence']}"
    )

    print(
        "Support Score: "
        f"{report['root_cause']['support_score']:.2f}"
    )

    # =========================================================
    # EVIDENCE SUMMARY
    # =========================================================

    print("\n" + "-" * 70)
    print("EVIDENCE SUMMARY")
    print("-" * 70)

    evidence = report[
        "evidence_summary"
    ]

    print(
        f"Observed Evidence : "
        f"{evidence['observed']}"
    )

    print(
        f"Code Evidence     : "
        f"{evidence['code']}"
    )

    print(
        f"Stacktrace        : "
        f"{evidence['stacktrace']}"
    )

    print(
        f"Supporting Sources: "
        f"{evidence['supporting_sources']}"
    )

    # =========================================================
    # GROUNDED CONFIDENCE
    # =========================================================

    print("\n" + "-" * 70)
    print("GROUNDED CONFIDENCE")
    print("-" * 70)

    grounded = report[
        "grounded_confidence"
    ]

    print(
        f"Confidence : "
        f"{grounded['label']}"
    )

    print(
        f"Score      : "
        f"{grounded['score']:.2f}"
    )

    print(
        f"Observed Root Cause : "
        f"{grounded['observed_root_cause']}"
    )

    print(
        f"Stacktrace Support  : "
        f"{grounded['stacktrace_confirmation']}"
    )

    print(
        f"Code Support        : "
        f"{grounded['code_confirmation']}"
    )

    print(
        f"Failure Support     : "
        f"{grounded['failure_confirmation']}"
    )

    # =========================================================
    # CITATION VERIFICATION
    # =========================================================

    print("\n" + "-" * 70)
    print("CITATION VERIFICATION")
    print("-" * 70)

    citations = report[
        "citation_verification"
    ]

    print(
        f"Verified : "
        f"{citations['verified']}/"
        f"{citations['total']}"
    )

    print(
        f"Coverage : "
        f"{citations['coverage']:.2%}"
    )

    print(
        f"Status   : "
        f"{'PASS' if citations['all_verified'] else 'WARNING'}"
    )

    # =========================================================
    # CLAIM VERIFICATION
    # =========================================================

    print("\n" + "-" * 70)
    print("CLAIM VERIFICATION")
    print("-" * 70)

    claims = report[
        "claim_verification"
    ]

    print(
        f"Claims Checked : "
        f"{claims['total']}"
    )

    print(
        f"Supported      : "
        f"{claims['supported']}"
    )

    print(
        f"Unsupported    : "
        f"{claims['unsupported']}"
    )

    print(
        f"Claim Coverage : "
        f"{claims['coverage']:.2%}"
    )

    if claims[
        "has_unsupported_claims"
    ]:

        print(
            "\nWARNING: Unsupported claims detected:"
        )

        for claim in claims[
            "unsupported_claims"
        ]:

            print(
                f"- {claim['claim']}"
            )

    else:

        print(
            "Status         : "
            "PASS - No unsupported risky claims"
        )

    # =========================================================
    # LLM EXPLANATION
    # =========================================================

    print("\n" + "-" * 70)
    print("LLM EXPLANATION")
    print("-" * 70)

    print(
        report["llm_analysis"]
    )

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()