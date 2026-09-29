from app.retrieval.embeddings import EmbeddingModel
from app.retrieval.similarity import cosine_similarity


def main():

    embedding_model = EmbeddingModel()

    query = "Why could the application not connect to the database?"

    documents = [
        "Database connection pool exhausted",
        "Payment transaction failed",
        "The football match was exciting"
    ]

    # Generate embeddings
    query_embedding = embedding_model.encode([query])[0]

    document_embeddings = embedding_model.encode(documents)

    # Calculate similarity
    scores = cosine_similarity(
        query_embedding,
        document_embeddings
    )

    print("\nQuery:")
    print(query)

    print("\nSimilarity Results:")

    results = list(zip(documents, scores))

    results.sort(
        key=lambda item: item[1],
        reverse=True
    )

    for document, score in results:
        print(f"{score:.4f} → {document}")


if __name__ == "__main__":
    main()