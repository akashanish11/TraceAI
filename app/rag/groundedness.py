import re


class GroundednessAnalyzer:
    """
    Deterministic heuristic analyzer for checking whether factual
    statements in an LLM investigation are supported by citations.

    A citation may appear:
        1. On the same line as the claim.
        2. On the immediately following line.

    This is a groundedness heuristic, not a probabilistic truth score.
    """

    CITATION_PATTERN = re.compile(
        r"\[([^\]:]+):([^\]]+)\]"
    )

    NON_FACTUAL_LINES = {
        "",
        "not established by available evidence.",
    }

    def _extract_citations(self, text: str) -> list[str]:
        """
        Extract citation tokens from a piece of text.
        """

        matches = self.CITATION_PATTERN.findall(text)

        return [
            f"[{source_file}:{location}]"
            for source_file, location in matches
        ]

    def _is_factual_line(self, line: str) -> bool:
        """
        Determine whether a line should be treated as a factual claim.
        """

        stripped = line.strip()

        if not stripped:
            return False

        lowered = stripped.lower()

        if lowered in self.NON_FACTUAL_LINES:
            return False

        if stripped.startswith("###"):
            return False

        if stripped.startswith("---"):
            return False

        # Citation-only lines are handled separately.
        if self.CITATION_PATTERN.fullmatch(stripped.rstrip(".")):
            return False

        # Ignore markdown-only formatting.
        if re.fullmatch(r"[*_`#\-\s]+", stripped):
            return False

        return True

    def _is_citation_only_line(self, line: str) -> bool:
        """
        Check whether a line contains only one or more citations.
        """

        stripped = line.strip().rstrip(".")

        if not stripped:
            return False

        citations = self._extract_citations(stripped)

        if not citations:
            return False

        remaining = self.CITATION_PATTERN.sub("", stripped)

        return not remaining.strip()

    def analyze(
        self,
        analysis: str,
        evidence: list[dict],
    ) -> dict:
        """
        Analyze factual-claim citation coverage.

        Returns:
            score
            level
            total_claims
            grounded_claims
            ungrounded_claims
            claim_coverage
            citations
            grounded_lines
            ungrounded_lines
            status
        """

        if not analysis.strip():
            return {
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
            }

        valid_citations = {
            f"[{item.get('source_file')}:{item.get('location')}]"
            for item in evidence
        }

        lines = analysis.splitlines()

        claims = []

        for index, line in enumerate(lines):
            if not self._is_factual_line(line):
                continue

            claim_text = line.strip()

            citations = self._extract_citations(line)

            # -----------------------------------------------------
            # If citations are on the same line, use them directly.
            # -----------------------------------------------------

            valid_line_citations = [
                citation
                for citation in citations
                if citation in valid_citations
            ]

            # -----------------------------------------------------
            # If the next line contains only citations, associate
            # those citations with this claim.
            # -----------------------------------------------------

            if index + 1 < len(lines):
                next_line = lines[index + 1]

                if self._is_citation_only_line(next_line):
                    next_citations = self._extract_citations(next_line)

                    valid_next_citations = [
                        citation
                        for citation in next_citations
                        if citation in valid_citations
                    ]

                    valid_line_citations.extend(valid_next_citations)

            # Remove duplicates while preserving order.
            valid_line_citations = list(
                dict.fromkeys(valid_line_citations)
            )

            claims.append(
                {
                    "line_number": index + 1,
                    "text": claim_text,
                    "citations": valid_line_citations,
                }
            )

        grounded_lines = [
            claim
            for claim in claims
            if claim["citations"]
        ]

        ungrounded_lines = [
            {
                "line_number": claim["line_number"],
                "text": claim["text"],
            }
            for claim in claims
            if not claim["citations"]
        ]

        total_claims = len(claims)
        grounded_claims = len(grounded_lines)
        ungrounded_claims = len(ungrounded_lines)

        if total_claims == 0:
            coverage = 0.0
        else:
            coverage = grounded_claims / total_claims

        if coverage >= 0.90:
            level = "HIGH"
        elif coverage >= 0.60:
            level = "MEDIUM"
        else:
            level = "LOW"

        status = "PASS" if coverage >= 0.90 else "REVIEW"

        return {
            "score": round(coverage, 3),
            "level": level,
            "total_claims": total_claims,
            "grounded_claims": grounded_claims,
            "ungrounded_claims": ungrounded_claims,
            "claim_coverage": round(coverage, 3),
            "citations": sorted(valid_citations),
            "grounded_lines": grounded_lines,
            "ungrounded_lines": ungrounded_lines,
            "status": status,
        }