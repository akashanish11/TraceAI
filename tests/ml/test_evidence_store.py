from app.parsers.log_parser import parse_log_file
from app.retrieval.evidence_store import EvidenceStore


def main():

    log_file = "data/incidents/incident_001.log"

    # Parse the actual incident log
    records = parse_log_file(log_file)

    # Create evidence store
    store = EvidenceStore()

    # Add parsed records
    store.add_records(records)

    query = "Why could the payment service not connect to the database?"

    print("\n" + "=" * 60)
    print("TRACEAI EVIDENCE SEARCH")
    print("=" * 60)

    print("\nQuery:")
    print(query)

    results = store.search(
        query,
        top_k=5
    )

    print("\nRelevant Evidence:\n")

    for result in results:

        print(
            f"Score      : {result['score']:.4f}"
        )

        print(
            f"Source     : {result['source_file']}"
        )

        print(
            f"Line       : {result['line_number']}"
        )

        print(
            f"Service    : {result['service']}"
        )

        print(
            f"Level      : {result['level']}"
        )

        print(
            f"Evidence   : {result['message']}"
        )

        print("-" * 60)


if __name__ == "__main__":
    main()