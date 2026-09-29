from app.rag.investigator import IncidentInvestigator


def main():
    investigator = IncidentInvestigator(
        "data/incidents"
    )

    result = investigator.investigate(
        query=(
            "PaymentService cannot acquire a database "
            "connection because the connection pool is exhausted"
        ),
        top_k=8,
        incident_id="legacy_incident",
    )

    print("=" * 70)
    print("TRACEAI — INVESTIGATION + HISTORICAL MATCHING")
    print("=" * 70)

    print("\nRoot Cause:")
    print(
        result["root_cause"]["root_cause"]
    )

    print("\nHistorical Matches:")

    historical = result.get(
        "historical_incidents",
        []
    )

    if not historical:
        print("No historical matches found.")

    for index, match in enumerate(
        historical,
        start=1,
    ):
        print(
            f"{index}. "
            f"{match['incident_id']} | "
            f"similarity="
            f"{match['similarity']:.3f}"
        )


if __name__ == "__main__":
    main()