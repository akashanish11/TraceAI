import re
from difflib import SequenceMatcher


class CitationRepairer:
    """
    Repairs and completes citations in LLM-generated analysis.

    The repairer operates ONLY against the CURRENT retrieved
    evidence.

    It can:

        1. Repair an invalid citation.
        2. Add a missing citation to a factual statement.
        3. Leave a valid citation unchanged.

    It never invents a source or location.
    """

    CITATION_PATTERN = re.compile(
        r"\[([^\]:]+):([^\]]+)\]"
    )

    SECTION_PATTERN = re.compile(
        r"^###\s+\d+\.\s+(.+)$",
        re.IGNORECASE,
    )

    NON_FACTUAL_LINES = {
        "",
        "not established by available evidence.",
    }

    NON_FACTUAL_PREFIXES = (
        "###",
    )

    def __init__(
        self,
        minimum_similarity: float = 0.45,
    ):
        self.minimum_similarity = (
            minimum_similarity
        )

    # =========================================================
    # NORMALIZATION
    # =========================================================

    def _normalize(
        self,
        text: str,
    ) -> str:

        text = text.lower()

        text = re.sub(
            r"\[[^\]]+\]",
            "",
            text,
        )

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # =========================================================
    # SIMILARITY
    # =========================================================

    def _similarity(
        self,
        claim: str,
        evidence_text: str,
    ) -> float:

        claim_normalized = (
            self._normalize(claim)
        )

        evidence_normalized = (
            self._normalize(evidence_text)
        )

        if not claim_normalized:
            return 0.0

        if not evidence_normalized:
            return 0.0

        # Exact phrase containment.
        if (
            claim_normalized
            in evidence_normalized
        ):
            return 1.0

        if (
            evidence_normalized
            in claim_normalized
        ):
            return 0.95

        # Sequence similarity.
        sequence_score = (
            SequenceMatcher(
                None,
                claim_normalized,
                evidence_normalized,
            ).ratio()
        )

        # Token overlap.
        claim_tokens = set(
            claim_normalized.split()
        )

        evidence_tokens = set(
            evidence_normalized.split()
        )

        if not claim_tokens:
            token_score = 0.0
        else:
            token_score = (
                len(
                    claim_tokens
                    & evidence_tokens
                )
                / len(claim_tokens)
            )

        return max(
            sequence_score,
            token_score,
        )

    # =========================================================
    # EVIDENCE INDEX
    # =========================================================

    def _build_evidence_index(
        self,
        evidence: list[dict],
    ) -> dict[str, dict]:

        index = {}

        for item in evidence:

            source_file = item.get(
                "source_file"
            )

            location = item.get(
                "location"
            )

            if (
                not source_file
                or not location
            ):
                continue

            citation = (
                f"[{source_file}:"
                f"{location}]"
            )

            index[citation] = item

        return index

    # =========================================================
    # BEST EVIDENCE
    # =========================================================

    def _find_best_evidence(
        self,
        claim: str,
        evidence: list[dict],
    ):

        best_item = None
        best_score = 0.0

        for item in evidence:

            evidence_text = item.get(
                "text",
                "",
            )

            score = self._similarity(
                claim,
                evidence_text,
            )

            if score > best_score:

                best_score = score
                best_item = item

        if (
            best_item is None
            or best_score
            < self.minimum_similarity
        ):
            return None, best_score

        return best_item, best_score

    # =========================================================
    # LINE CLASSIFICATION
    # =========================================================

    def _is_section_heading(
        self,
        line: str,
    ) -> bool:

        stripped = line.strip()

        if not stripped:
            return True

        if stripped.startswith(
            self.NON_FACTUAL_PREFIXES
        ):
            return True

        return bool(
            self.SECTION_PATTERN.match(
                stripped
            )
        )

    def _is_non_factual_line(
        self,
        line: str,
    ) -> bool:

        stripped = line.strip()

        if not stripped:
            return True

        lowered = stripped.lower()

        if lowered in self.NON_FACTUAL_LINES:
            return True

        if self._is_section_heading(
            stripped
        ):
            return True

        return False

    def _contains_citation(
        self,
        line: str,
    ) -> bool:

        return bool(
            self.CITATION_PATTERN.search(
                line
            )
        )

    # =========================================================
    # CLAIM EXTRACTION
    # =========================================================

    def _claim_without_citations(
        self,
        line: str,
    ) -> str:

        claim = (
            self.CITATION_PATTERN.sub(
                "",
                line,
            )
        )

        claim = claim.strip(
            " :-–—"
        )

        # Remove list numbering such as:
        # 1. Connection pool exhausted
        claim = re.sub(
            r"^\d+\.\s*",
            "",
            claim,
        )

        # Remove markdown bullet.
        claim = re.sub(
            r"^[-*]\s*",
            "",
            claim,
        )

        return claim.strip()

    # =========================================================
    # REPAIR ONE CITATION
    # =========================================================

    def _repair_invalid_citation(
        self,
        line: str,
        original_citation: str,
        evidence: list[dict],
    ):

        claim = (
            self._claim_without_citations(
                line
            )
        )

        if not claim:
            return None

        best_item, similarity = (
            self._find_best_evidence(
                claim,
                evidence,
            )
        )

        if best_item is None:
            return None

        source_file = best_item.get(
            "source_file"
        )

        location = best_item.get(
            "location"
        )

        if (
            not source_file
            or not location
        ):
            return None

        replacement = (
            f"[{source_file}:"
            f"{location}]"
        )

        return {
            "replacement": replacement,
            "similarity": similarity,
            "evidence": best_item.get(
                "text",
                "",
            ),
        }

    # =========================================================
    # ADD MISSING CITATION
    # =========================================================

    def _add_missing_citation(
        self,
        line: str,
        evidence: list[dict],
    ):

        if self._is_non_factual_line(
            line
        ):
            return None

        claim = (
            self._claim_without_citations(
                line
            )
        )

        if not claim:
            return None

        # -----------------------------------------------------
        # Conservative threshold for adding citations.
        #
        # We require stronger evidence than for repairing a
        # citation because we are adding information that the
        # LLM omitted.
        # -----------------------------------------------------

        best_item, similarity = (
            self._find_best_evidence(
                claim,
                evidence,
            )
        )

        if (
            best_item is None
            or similarity < 0.55
        ):
            return None

        source_file = best_item.get(
            "source_file"
        )

        location = best_item.get(
            "location"
        )

        if (
            not source_file
            or not location
        ):
            return None

        citation = (
            f"[{source_file}:"
            f"{location}]"
        )

        return {
            "citation": citation,
            "similarity": similarity,
            "evidence": best_item.get(
                "text",
                "",
            ),
        }

    # =========================================================
    # REPAIR ANALYSIS
    # =========================================================

    def repair(
        self,
        analysis: str,
        evidence: list[dict],
    ) -> dict:

        if not analysis.strip():

            return {
                "analysis": analysis,
                "repairs": [],
                "repair_count": 0,
            }

        evidence_index = (
            self._build_evidence_index(
                evidence
            )
        )

        lines = analysis.splitlines()

        repaired_lines = []

        repairs = []

        for line_number, line in enumerate(
            lines,
            start=1,
        ):

            # -------------------------------------------------
            # Normalize malformed citation brackets emitted by
            # the local LLM.
            #
            # Example:
            #   [upload_test.log:line 3]]
            #
            # becomes:
            #   [upload_test.log:line 3]
            #
            # This happens before citation extraction so the
            # cleaned analysis is also used by verification
            # and persistence.
            # -------------------------------------------------

            line = re.sub(
                r"(\[[^\]\r\n]+:[^\]\r\n]+\])\]+",
                r"\1",
                line,
            )

            # -------------------------------------------------
            # Ignore headings / empty lines.
            # -------------------------------------------------

            if self._is_non_factual_line(
                line
            ):

                repaired_lines.append(
                    line
                )

                continue

            # -------------------------------------------------
            # Case 1:
            # Line already contains citations.
            # -------------------------------------------------

            citations = (
                self.CITATION_PATTERN.findall(
                    line
                )
            )

            if citations:

                repaired_line = line

                for source_file, location in citations:

                    original_citation = (
                        f"[{source_file}:"
                        f"{location}]"
                    )

                    # -----------------------------------------
                    # Valid citation.
                    # -----------------------------------------

                    if (
                        original_citation
                        in evidence_index
                    ):
                        continue

                    # -----------------------------------------
                    # Invalid citation.
                    # -----------------------------------------

                    repair = (
                        self._repair_invalid_citation(
                            line=line,
                            original_citation=(
                                original_citation
                            ),
                            evidence=evidence,
                        )
                    )

                    if repair is None:
                        continue

                    replacement = repair[
                        "replacement"
                    ]

                    repaired_line = (
                        repaired_line.replace(
                            original_citation,
                            replacement,
                            1,
                        )
                    )

                    repairs.append(
                        {
                            "type": (
                                "invalid_citation_repair"
                            ),
                            "line_number": (
                                line_number
                            ),
                            "original": (
                                original_citation
                            ),
                            "replacement": (
                                replacement
                            ),
                            "similarity": round(
                                repair[
                                    "similarity"
                                ],
                                3,
                            ),
                            "evidence": (
                                repair[
                                    "evidence"
                                ]
                            ),
                        }
                    )

                repaired_lines.append(
                    repaired_line
                )

                continue

            # -------------------------------------------------
            # Case 2:
            # Factual line has no citation.
            # -------------------------------------------------

            missing = (
                self._add_missing_citation(
                    line=line,
                    evidence=evidence,
                )
            )

            if missing is None:

                repaired_lines.append(
                    line
                )

                continue

            citation = missing[
                "citation"
            ]

            repaired_line = (
                f"{line.rstrip()} "
                f"{citation}"
            )

            repaired_lines.append(
                repaired_line
            )

            repairs.append(
                {
                    "type": (
                        "missing_citation_added"
                    ),
                    "line_number": (
                        line_number
                    ),
                    "original": None,
                    "replacement": citation,
                    "similarity": round(
                        missing[
                            "similarity"
                        ],
                        3,
                    ),
                    "evidence": (
                        missing[
                            "evidence"
                        ]
                    ),
                }
            )

        repaired_analysis = "\n".join(
            repaired_lines
        )

        return {
            "analysis": repaired_analysis,
            "repairs": repairs,
            "repair_count": len(
                repairs
            ),
        }