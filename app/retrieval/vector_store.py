import faiss
import numpy as np

from app.retrieval.embeddings import EmbeddingModel


class VectorStore:
    """
    Local FAISS vector store for TraceAI evidence.
    """

    def __init__(self):
        self.embedding_model = EmbeddingModel()

        self.index = None
        self.documents = []

    def add_documents(self, documents: list[str]):
        """
        Convert documents into embeddings and add them
        to the FAISS index.
        """

        if not documents:
            return

        embeddings = self.embedding_model.encode(documents)

        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )

        dimension = embeddings.shape[1]

        # Create FAISS index on first insertion
        if self.index is None:
            self.index = faiss.IndexFlatIP(dimension)

        self.index.add(embeddings)

        self.documents.extend(documents)

    def search(
        self,
        query: str,
        top_k: int = 3
    ) -> list[dict]:
        """
        Search the vector store using semantic similarity.
        """

        if self.index is None:
            return []

        query_embedding = self.embedding_model.encode(
            [query]
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype="float32"
        )

        scores, indices = self.index.search(
            query_embedding,
            min(top_k, len(self.documents))
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0]
        ):

            if index == -1:
                continue

            results.append({
                "document": self.documents[index],
                "score": float(score)
            })

        return results