from app.retrieval.multi_source_loader import MultiSourceLoader
from app.retrieval.evidence_normalizer import EvidenceNormalizer


def main():

    loader = MultiSourceLoader(
        "data/incidents"
    )

    incident = loader.load_incident()

    normalizer = EvidenceNormalizer()

    evidence = normalizer.normalize(incident)

    print("\n" + "=" * 60)
    print("TRACEAI NORMALIZED EVIDENCE")
    print("=" * 60)

    print(f"\nTotal evidence items: {len(evidence)}")

    for index, item in enumerate(evidence, start=1):

        print("\n" + "-" * 60)

        print(f"Evidence #{index}")
        print(f"Type     : {item['source_type']}")
        print(f"Source   : {item['source_file']}")
        print(f"Location : {item['location']}")
        print(f"Text     : {item['text'][:200]}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()