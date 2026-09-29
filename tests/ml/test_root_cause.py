from app.retrieval.cross_source_store import (
    CrossSourceEvidenceStore
)

from app.analysis.root_cause import (
    RootCauseAnalyzer
)


def main():

    store = CrossSourceEvidenceStore(
        "data/incidents"
    )

    store.build()

    query = (
        "What caused the payment service "
        "database failure?"
    )

    evidence = store.search(
        query,
        top_k=8
    )

    analyzer = RootCauseAnalyzer()

    result = analyzer.analyze(
        evidence
    )

    print("\n" + "=" * 70)
    print("TRACEAI DETERMINISTIC ROOT CAUSE ANALYSIS")
    print("=" * 70)

    print("\nROOT CAUSE:")
    print(result["root_cause"])

    print("\nEXPLANATION:")
    print(result["explanation"])

    print("\nSUPPORT SCORE:")
    print(
        f"{result['support_score']:.2f}"
    )

    print("\nCONFIDENCE:")
    print(result["confidence"])

    print("\nSUPPORTING EVIDENCE:")

    for item in result["evidence"]:

        print(
            f"- [{item['source_file']}:"
            f"{item['location']}] "
            f"{item['text']}"
        )

    print("\n" + "-" * 70)

    print(
        "Observed Evidence : "
        f"{result.get('observed_evidence', 0)}"
    )

    print(
        "Code Evidence      : "
        f"{result.get('code_evidence', 0)}"
    )

    print(
        "Stacktrace Evidence: "
        f"{result.get('stacktrace_evidence', 0)}"
    )

    print(
        "Supporting Sources : "
        f"{result.get('supporting_sources', 0)}"
    )

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()