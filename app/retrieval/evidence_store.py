from typing import Any

from app.retrieval.vector_store import VectorStore


class EvidenceStore:
    """
    Converts parsed incident records into searchable evidence
    while preserving source metadata.
    """

    def __init__(self):
        self.vector_store = VectorStore()
        self.metadata: list[dict[str, Any]] = []

    def add_records(self, records: list[dict[str, Any]]):
        """
        Add structured log records to the vector store.
        """

        documents = []

        for record in records:

            text = (
                f"{record['level']} "
                f"{record['service']} "
                f"{record['message']}"
            )

            documents.append(text)

            self.metadata.append({
                "text": text,
                "message": record["message"],
                "source_file": record["source_file"],
                "line_number": record["line_number"],
                "service": record["service"],
                "level": record["level"],
                "timestamp": record["timestamp"],
            })

        self.vector_store.add_documents(documents)

    def search(
        self,
        query: str,
        top_k: int = 3
    ) -> list[dict[str, Any]]:
        """
        Search incident evidence and return metadata.
        """

        results = self.vector_store.search(
            query,
            top_k
        )

        enriched_results = []

        for result in results:

            document = result["document"]

            matching_metadata = next(
                (
                    item
                    for item in self.metadata
                    if item["text"] == document
                ),
                None
            )

            if matching_metadata:

                enriched_results.append({
                    **matching_metadata,
                    "score": result["score"]
                })

        return enriched_results