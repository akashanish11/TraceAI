from app.retrieval.cross_source_store import CrossSourceEvidenceStore
from app.retrieval.confidence import EvidenceConfidence
from app.retrieval.multi_source_loader import MultiSourceLoader
from app.retrieval.historical_matcher import HistoricalIncidentMatcher
from app.retrieval.embeddings import EmbeddingModel

from app.analysis.root_cause import RootCauseAnalyzer

from app.rag.context_builder import RAGContextBuilder
from app.rag.investigation_prompt import build_investigation_prompt
from app.rag.ollama_client import OllamaClient
from app.rag.citation_verifier import CitationVerifier
from app.rag.claim_verifier import ClaimVerifier
from app.rag.groundedness import GroundednessAnalyzer
from app.rag.citation_repair import CitationRepairer


class IncidentInvestigator:
    """
    End-to-end incident investigation pipeline.

    Pipeline:
        Query
          ↓
        Evidence Retrieval
          ↓
        Root Cause Analysis
          ↓
        Historical Incident Matching
          ↓
        RAG Context Construction
          ↓
        Local LLM Analysis
          ↓
        Citation Repair
          ↓
        Citation Verification
          ↓
        Claim Verification
          ↓
        Groundedness / Claim Coverage
          ↓
        Evidence Confidence
          ↓
        Investigation Result
    """

    def __init__(
        self,
        incident_directory: str,
    ):
        self.incident_directory = (
            incident_directory
        )

        # -----------------------------------------------------
        # Shared embedding model
        # -----------------------------------------------------

        self.embedding_model = (
            EmbeddingModel()
        )

        # -----------------------------------------------------
        # Evidence retrieval
        # -----------------------------------------------------

        self.store = CrossSourceEvidenceStore(
            incident_directory,
            embedding_model=self.embedding_model,
        )

        # -----------------------------------------------------
        # Analysis components
        # -----------------------------------------------------

        self.root_cause_analyzer = (
            RootCauseAnalyzer()
        )

        self.context_builder = (
            RAGContextBuilder()
        )

        self.llm = OllamaClient()

        # -----------------------------------------------------
        # Verification
        # -----------------------------------------------------

        self.citation_verifier = (
            CitationVerifier()
        )

        self.claim_verifier = (
            ClaimVerifier()
        )

        self.groundedness_analyzer = (
            GroundednessAnalyzer()
        )

        # -----------------------------------------------------
        # Citation repair
        #
        # This layer repairs invalid LLM citations by matching
        # the claim against CURRENT retrieved evidence only.
        # -----------------------------------------------------

        self.citation_repairer = (
            CitationRepairer(
                minimum_similarity=0.45,
            )
        )

        # -----------------------------------------------------
        # Deterministic confidence
        # -----------------------------------------------------

        self.confidence_calculator = (
            EvidenceConfidence()
        )

        # -----------------------------------------------------
        # Build evidence index
        # -----------------------------------------------------

        self.store.build()

        # -----------------------------------------------------
        # Historical incident matcher
        # -----------------------------------------------------

        loader = MultiSourceLoader(
            incident_directory
        )

        incidents = loader.load_incidents()

        self.historical_matcher = (
            HistoricalIncidentMatcher(
                incidents,
                embedding_model=self.embedding_model,
            )
        )

    # =========================================================
    # HISTORICAL INCIDENTS
    # =========================================================

    def _find_historical_incidents(
        self,
        query: str,
        incident_id: str | None = None,
        top_k: int = 3,
    ) -> list[dict]:

        results = self.historical_matcher.search(
            query=query,
            top_k=top_k + 1,
            similarity_threshold=0.45,
        )

        historical_results = []

        for result in results:

            matched_incident_id = result.get(
                "incident_id"
            )

            # Never return the current incident as a
            # historical match.
            if (
                incident_id is not None
                and matched_incident_id == incident_id
            ):
                continue

            historical_results.append(
                {
                    "incident_id": (
                        matched_incident_id
                    ),
                    "similarity": result[
                        "similarity"
                    ],
                    "incident": result.get(
                        "incident",
                        {},
                    ),
                }
            )

            if (
                len(historical_results)
                >= top_k
            ):
                break

        return historical_results

    # =========================================================
    # INVESTIGATION
    # =========================================================

    def investigate(
        self,
        query: str,
        top_k: int = 8,
        incident_id: str | None = None,
    ) -> dict:

        # -----------------------------------------------------
        # 1. Retrieve current evidence
        # -----------------------------------------------------

        evidence = self.store.search(
            query=query,
            top_k=top_k,
            incident_id=incident_id,
        )

        # -----------------------------------------------------
        # 2. Historical incident matching
        # -----------------------------------------------------

        historical_incidents = (
            self._find_historical_incidents(
                query=query,
                incident_id=incident_id,
                top_k=3,
            )
        )

        # -----------------------------------------------------
        # No evidence
        # -----------------------------------------------------

        if not evidence:

            return {
                "query": query,
                "incident_id": incident_id,
                "root_cause": None,
                "root_cause_confidence": "LOW",
                "evidence": [],
                "historical_incidents": (
                    historical_incidents
                ),
                "analysis": (
                    "No relevant evidence was "
                    "retrieved for this incident."
                ),
                "citation_repair": {
                    "repair_count": 0,
                    "repairs": [],
                },
                "citation_verification": {
                    "valid": False,
                    "issues": [
                        "No evidence was "
                        "available for verification."
                    ],
                },
                "claim_verification": {
                    "valid": False,
                    "issues": [
                        "No evidence was "
                        "available for verification."
                    ],
                },
                "groundedness": {
                    "score": 0.0,
                    "level": "LOW",
                    "total_claims": 0,
                    "grounded_claims": 0,
                    "ungrounded_claims": 0,
                    "claim_coverage": 0.0,
                    "citations": [],
                    "grounded_lines": [],
                    "ungrounded_lines": [],
                    "status": "FAIL",
                },
                "evidence_confidence": {
                    "score": 0.0,
                    "confidence": "LOW",
                },
            }

        # -----------------------------------------------------
        # 3. Deterministic root cause
        # -----------------------------------------------------

        root_cause = (
            self.root_cause_analyzer.analyze(
                evidence
            )
        )

        # -----------------------------------------------------
        # 4. Build RAG context
        # -----------------------------------------------------

        context = self.context_builder.build(
            query=query,
            evidence=evidence,
        )

        # -----------------------------------------------------
        # 5. Build investigation prompt
        # -----------------------------------------------------

        prompt = build_investigation_prompt(
            query=query,
            context=context,
            root_cause=root_cause,
            historical_incidents=(
                historical_incidents
            ),
        )

        # -----------------------------------------------------
        # 6. Local LLM
        # -----------------------------------------------------

        analysis = self.llm.generate(
            prompt
        )

        # -----------------------------------------------------
        # 7. Citation repair
        #
        # Important:
        # Only current retrieved evidence may be used as
        # replacement evidence.
        # -----------------------------------------------------

        citation_repair = (
            self.citation_repairer.repair(
                analysis=analysis,
                evidence=evidence,
            )
        )

        repaired_analysis = (
            citation_repair["analysis"]
        )

        # -----------------------------------------------------
        # 8. Citation verification
        #
        # Verify the REPAIRED analysis, not the raw LLM output.
        # -----------------------------------------------------

        citation_verification = (
            self.citation_verifier.verify(
                analysis=repaired_analysis,
                evidence=evidence,
            )
        )

        # -----------------------------------------------------
        # 9. Claim verification
        # -----------------------------------------------------

        claim_verification = (
            self.claim_verifier.verify(
                analysis=repaired_analysis,
                evidence=evidence,
            )
        )

        # -----------------------------------------------------
        # 10. Groundedness
        # -----------------------------------------------------

        groundedness = (
            self.groundedness_analyzer.analyze(
                analysis=repaired_analysis,
                evidence=evidence,
            )
        )

        # -----------------------------------------------------
        # 11. Evidence confidence
        # -----------------------------------------------------

        evidence_confidence = (
            self.confidence_calculator.calculate(
                evidence,
                root_cause=root_cause[
                    "root_cause"
                ],
            )
        )

        # -----------------------------------------------------
        # 12. Final result
        # -----------------------------------------------------

        return {
            "query": query,
            "incident_id": incident_id,

            "root_cause": root_cause,

            "root_cause_confidence": (
                root_cause["confidence"]
            ),

            "root_cause_details": root_cause,

            "evidence": evidence,

            "historical_incidents": (
                historical_incidents
            ),

            "context": context,

            # Return repaired analysis as the
            # user-facing analysis.
            "analysis": repaired_analysis,

            # Keep repair information visible
            # for debugging / UI.
            "citation_repair": citation_repair,

            "citation_verification": (
                citation_verification
            ),

            "claim_verification": (
                claim_verification
            ),

            "groundedness": groundedness,

            "evidence_confidence": (
                evidence_confidence
            ),
        }