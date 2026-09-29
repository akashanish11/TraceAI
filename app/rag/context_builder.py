class RAGContextBuilder:

    def __init__(
        self,
        max_evidence: int = 6,
        max_text_length: int = 250
    ):
        self.max_evidence = max_evidence
        self.max_text_length = max_text_length

    def build(
        self,
        query: str,
        evidence: list[dict]
    ) -> str:

        sections = []

        sections.append(
            f"USER QUESTION:\n{query}"
        )

        sections.append(
            "\nRETRIEVED EVIDENCE:"
        )

        selected_evidence = evidence[:self.max_evidence]

        for index, item in enumerate(
            selected_evidence,
            start=1
        ):

            source_type = item.get(
                "source_type",
                "unknown"
            )

            provenance = item.get(
                "provenance",
                "unknown"
            )

            source_file = item.get(
                "source_file",
                "unknown"
            )

            location = item.get(
                "location",
                "unknown"
            )

            text = item.get("text", "")

            if len(text) > self.max_text_length:
                text = (
                    text[:self.max_text_length]
                    .rstrip()
                    + "..."
                )

            citation = (
                f"[{source_file}:{location}]"
            )

            sections.append(
                f"""
[EVIDENCE {index}]
Type: {source_type}
Provenance: {provenance}
Citation: {citation}
Content: {text}
"""
            )

        sections.append(
            """
GROUNDING RULES:

1. Use ONLY the supplied evidence.
2. Do not invent facts or outcomes.
3. Prefer observed and code evidence.
4. Documentation is supporting context only.
5. Every factual claim must have an exact citation.
6. Only use citations present in the evidence.
7. If something is unsupported, say:
   "Not established by available evidence."
8. Do not infer recovery, failure of retries,
   customer impact, revenue loss, downtime,
   security impact, or data loss unless directly
   supported by evidence.
"""
        )

        return "\n".join(sections)