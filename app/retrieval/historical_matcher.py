from app.retrieval.embeddings import EmbeddingModel


class HistoricalIncidentMatcher:
    """
    Finds historically similar incidents from the real TraceAI
    incident corpus.

    Historical matching is kept separate from the main evidence
    ranking pipeline so it cannot change the existing benchmark.
    """

    def __init__(
        self,
        incidents: list[dict],
        embedding_model: EmbeddingModel | None = None,
    ):
        self.incidents = incidents

        self.embedding_model = (
            embedding_model
            if embedding_model is not None
            else EmbeddingModel()
        )

        self.search_records = self._build_search_records()

        self.embeddings = None

        if self.search_records:
            texts = [
                record["search_text"]
                for record in self.search_records
            ]

            self.embeddings = self.embedding_model.encode(
                texts
            )

    def _build_search_records(self) -> list[dict]:
        """
        Convert loaded incident objects into compact searchable
        representations.
        """

        records = []

        for incident in self.incidents:
            parts = []

            # --------------------------------------------------
            # Logs
            # --------------------------------------------------

            for log in incident.get("logs", []):
                message = log.get("message", "")

                if message:
                    parts.append(message)

            # --------------------------------------------------
            # Stacktrace
            # --------------------------------------------------

            stacktrace = incident.get("stacktrace")

            if stacktrace:
                exception_type = stacktrace.get(
                    "exception_type"
                )

                exception_message = stacktrace.get(
                    "exception_message"
                )

                if exception_type:
                    parts.append(exception_type)

                if exception_message:
                    parts.append(exception_message)

                metadata = stacktrace.get(
                    "metadata",
                    {}
                )

                for key in (
                    "service",
                    "operation",
                    "dependency",
                ):
                    value = metadata.get(key)

                    if value:
                        parts.append(str(value))

            # --------------------------------------------------
            # Documentation
            # --------------------------------------------------

            documentation = incident.get(
                "documentation"
            )

            if documentation:
                content = documentation.get(
                    "content",
                    ""
                )

                if content:
                    parts.append(content)

            search_text = " ".join(parts).strip()

            if not search_text:
                continue

            records.append(
                {
                    "incident_id": incident.get(
                        "incident_id"
                    ),
                    "search_text": search_text,
                    "incident": incident,
                }
            )

        return records

    def search(
        self,
        query: str,
        top_k: int = 3,
        similarity_threshold: float = 0.60,
    ) -> list[dict]:
        """
        Find the most semantically similar historical incidents.

        Parameters
        ----------
        query:
            Incident description or investigation query.

        top_k:
            Maximum number of historical incidents to return.

        similarity_threshold:
            Minimum cosine similarity required for a historical
            incident to be returned.

        Notes
        -----
        The threshold is configurable and has not yet been
        empirically calibrated against a historical-match
        evaluation dataset.
        """

        if (
            not self.search_records
            or self.embeddings is None
        ):
            return []

        query_embedding = self.embedding_model.encode(
            [query]
        )[0]

        # Because both the stored embeddings and query embedding
        # are normalized, the dot product is cosine similarity.
        scores = self.embeddings @ query_embedding

        # Sort all incidents from highest similarity to lowest.
        ranked_indices = scores.argsort()[::-1]

        results = []

        for index in ranked_indices:
            similarity = float(scores[index])

            # Scores are sorted descending, so once we fall below
            # the threshold, all remaining results will also be
            # below it.
            if similarity < similarity_threshold:
                break

            if len(results) >= top_k:
                break

            record = self.search_records[index]

            results.append(
                {
                    "incident_id": record["incident_id"],
                    "similarity": similarity,
                    "incident": record["incident"],
                }
            )

        return results