from app.retrieval.cross_source_store import (
    CrossSourceEvidenceStore
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

    results = store.search(
        query,
        top_k=8
    )

    print("\n" + "=" * 60)
    print("TRACEAI CROSS-SOURCE SEARCH")
    print("=" * 60)

    print("\nQuery:")
    print(query)

    print("\nRelevant Evidence:\n")

    for result in results:

        print(
            f"Semantic Score : "
            f"{result['semantic_score']:.4f}"
        )

        print(
            f"Diagnostic     : "
            f"{result['diagnostic_score']:.4f}"
        )

        print(
            f"Root Cause     : "
            f"{result['root_cause_score']:.4f}"
        )

        print(
            f"Failure        : "
            f"{result['failure_score']:.4f}"
        )

        print(
            f"Final Score    : "
            f"{result['final_score']:.4f}"
        )

        print(
            f"Type           : "
            f"{result['source_type']}"
        )

        print(
            f"Source         : "
            f"{result['source_file']}"
        )

        print(
            f"Location       : "
            f"{result['location']}"
        )

        print(
            f"Evidence       : "
            f"{result['text'][:250]}"
        )

        print("-" * 60)


if __name__ == "__main__":
    main()