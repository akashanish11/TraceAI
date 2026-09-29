import re


class DiagnosticSignals:
    """
    Identifies diagnostically important terms
    in incident evidence.
    """

    HIGH_VALUE_PATTERNS = [
        r"\berror\b",
        r"\bexception\b",
        r"\bfailed\b",
        r"\bfailure\b",
        r"\bexhausted\b",
        r"\btimeout\b",
        r"\bunable\b",
        r"\bcritical\b",
        r"\bconnection pool\b",
        r"exhaustederror",
    ]

    def calculate(self, text: str) -> float:
        """
        Calculate a diagnostic signal score
        between 0.0 and 1.0.
        """

        text_lower = text.lower()

        matches = 0

        for pattern in self.HIGH_VALUE_PATTERNS:

            if re.search(
                pattern,
                text_lower
            ):
                matches += 1

        if matches == 0:
            return 0.0

        return min(
            matches / 3,
            1.0
        )