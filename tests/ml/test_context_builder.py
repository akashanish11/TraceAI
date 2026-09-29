from app.retrieval.cross_source_store import (
    CrossSourceEvidenceStore
)

from app.rag.context_builder import (
    RAGContextBuilder
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
        top_k=6
    )

    builder = RAGContextBuilder()

    context = builder.build(
        query,
        evidence
    )

    print("\n" + "=" * 60)
    print("TRACEAI RAG CONTEXT")
    print("=" * 60)

    print(context)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()