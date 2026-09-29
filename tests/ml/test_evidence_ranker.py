from app.retrieval.cross_source_store import (
    CrossSourceEvidenceStore
)

from app.retrieval.evidence_ranker import (
    EvidenceRanker
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

    ranker = EvidenceRanker()

    ranked_results = ranker.rank(
        results
    )

    print("\n" + "=" * 60)
    print("TRACEAI EVIDENCE-AWARE RANKING")
    print("=" * 60)

    print("\nQuery:")
    print(query)

    print("\nRanked Evidence:\n")

    for index, result in enumerate(
        ranked_results,
        start=1
    ):

        print(
            f"Rank       : {index}"
        )

        print(
            f"Semantic   : "
            f"{result['semantic_score']:.4f}"
        )

        print(
            f"Diagnostic : "
            f"{result['diagnostic_score']:.4f}"
        )

        print(
            f"Type       : "
            f"{result['source_type']}"
        )

        print(
            f"Source     : "
            f"{result['source_file']}"
        )

        print(
            f"Location   : "
            f"{result['location']}"
        )

        print(
            f"Evidence   : "
            f"{result['text'][:200]}"
        )

        print("-" * 60)


if __name__ == "__main__":
    main()
    