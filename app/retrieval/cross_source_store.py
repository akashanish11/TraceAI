from app.retrieval.embeddings import EmbeddingModel
from app.retrieval.evidence_normalizer import EvidenceNormalizer
from app.retrieval.multi_source_loader import MultiSourceLoader
from app.retrieval.similarity import cosine_similarity
from app.retrieval.evidence_ranker import EvidenceRanker


class CrossSourceEvidenceStore:
    """
    Semantic evidence retrieval across multiple incidents.

    Each incident can contain:
    - application logs
    - stack traces
    - documentation

    Evidence is normalized into a common representation,
    embedded, and ranked using semantic similarity plus
    deterministic diagnostic signals.
    """

    def __init__(
        self,
        incident_directory: str,
        embedding_model: EmbeddingModel | None = None,
    ):
        self.incident_directory = incident_directory

        # Reuse an existing embedding model when supplied.
        # This allows the investigator to share one model
        # between evidence retrieval and historical matching.
        self.embedding_model = (
            embedding_model
            if embedding_model is not None
            else EmbeddingModel()
        )

        self.normalizer = EvidenceNormalizer()
        self.ranker = EvidenceRanker()

        self.evidence = []
        self.embeddings = None
        self.incidents = []

    def build(self):
        """
        Load and index evidence from ALL incidents.
        """

        loader = MultiSourceLoader(self.incident_directory)

        self.incidents = loader.load_incidents()

        if not self.incidents:
            raise RuntimeError(
                "No incidents with evidence were found."
            )

        self.evidence = []

        for incident in self.incidents:
            incident_evidence = self.normalizer.normalize(
                incident
            )

            for item in incident_evidence:
                item["incident_id"] = incident["incident_id"]

            self.evidence.extend(incident_evidence)

        if not self.evidence:
            raise RuntimeError(
                "Incidents were found, but no evidence was extracted."
            )

        texts = [
            item["text"]
            for item in self.evidence
        ]

        self.embeddings = self.embedding_model.encode(texts)

        print(
            f"Indexed {len(self.evidence)} evidence items "
            f"from {len(self.incidents)} incident(s)."
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        incident_id: str | None = None,
    ) -> list[dict]:
        """
        Search across all indexed incidents.

        If incident_id is provided, restrict retrieval
        to that specific incident.
        """

        if self.embeddings is None:
            raise RuntimeError(
                "Evidence store has not been built. "
                "Call build() first."
            )

        query_embedding = self.embedding_model.encode(
            [query]
        )[0]

        scores = []

        for index, embedding in enumerate(self.embeddings):
            item = self.evidence[index]

            if (
                incident_id is not None
                and item.get("incident_id") != incident_id
            ):
                continue

            score = cosine_similarity(
                query_embedding,
                embedding
            )

            scores.append((score, index))

        scores.sort(
            key=lambda item: item[0],
            reverse=True
        )

        if not scores:
            return []

        # Retrieve a larger candidate pool before applying
        # deterministic diagnostic ranking and diversification.
        candidate_k = min(
            len(scores),
            max(top_k * 6, 50)
        )

        candidates = []

        for score, index in scores[:candidate_k]:
            item = self.evidence[index].copy()

            item["score"] = float(score)

            candidates.append(item)

        # Apply deterministic evidence ranking.
        ranked_results = self.ranker.rank(
            candidates
        )

        # Reduce duplicate or overly similar evidence sources.
        diversified_results = self.ranker.diversify(
            ranked_results,
            top_k=top_k,
        )

        return diversified_results