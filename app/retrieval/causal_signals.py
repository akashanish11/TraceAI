import re


class CausalSignals:
    """
    Detects language that strongly indicates
    a root cause or underlying failure mechanism.
    """

    ROOT_CAUSE_PATTERNS = [
        r"connection pool exhausted",
        r"exhaustederror",
        r"no available database connections",
        r"root cause",
        r"resource exhausted",
        r"out of connections",
        r"pool exhaustion",
    ]

    FAILURE_PATTERNS = [
        r"unable to acquire",
        r"connection timeout",
        r"failed",
        r"failure",
        r"exception",
    ]

    def calculate(
        self,
        text: str
    ) -> dict:

        text_lower = text.lower()

        root_matches = 0
        failure_matches = 0

        for pattern in self.ROOT_CAUSE_PATTERNS:

            if re.search(
                pattern,
                text_lower
            ):
                root_matches += 1

        for pattern in self.FAILURE_PATTERNS:

            if re.search(
                pattern,
                text_lower
            ):
                failure_matches += 1

        root_score = min(
            root_matches / 1,
            1.0
        )

        failure_score = min(
            failure_matches / 2,
            1.0
        )

        return {
            "root_cause": root_score,
            "failure": failure_score,
        }