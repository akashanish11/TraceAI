from app.retrieval.vector_store import VectorStore


def main():

    store = VectorStore()

    documents = [
        "Database connection pool exhausted",
        "Payment transaction failed because the database connection was unavailable",
        "User authentication completed successfully",
        "Kafka consumer stopped processing messages",
        "The application server restarted successfully",
        "Football match scheduled for tomorrow"
    ]

    print("\nAdding documents to FAISS...")

    store.add_documents(documents)

    print("Documents added successfully.")

    query = "Why was the payment unable to connect to the database?"

    print("\nQuery:")
    print(query)

    print("\nTop relevant evidence:")

    results = store.search(
        query,
        top_k=3
    )

    for result in results:

        print(
            f"{result['score']:.4f} "
            f"→ {result['document']}"
        )


if __name__ == "__main__":
    main()