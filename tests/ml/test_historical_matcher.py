from app.retrieval.multi_source_loader import (
    MultiSourceLoader,
)

from app.retrieval.historical_matcher import (
    HistoricalIncidentMatcher,
)


def main():
    loader = MultiSourceLoader(
        "data/incidents"
    )

    incidents = loader.load_incidents()

    print(
        f"Loaded incidents: {len(incidents)}"
    )

    matcher = HistoricalIncidentMatcher(
        incidents
    )

    query = (
        "PaymentService cannot acquire a database "
        "connection because the connection pool is "
        "exhausted"
    )

    results = matcher.search(
        query,
        top_k=5,
    )

    print("=" * 70)
    print(
        "TRACEAI — REAL HISTORICAL INCIDENT MATCHING"
    )
    print("=" * 70)

    print("\nQuery:")
    print(query)

    print("\nSimilar incidents:")

    for index, result in enumerate(
        results,
        start=1,
    ):
        print(
            f"{index}. "
            f"{result['incident_id']} | "
            f"similarity="
            f"{result['similarity']:.3f}"
        )


if __name__ == "__main__":
    main()