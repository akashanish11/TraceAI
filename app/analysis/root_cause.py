import re


class RootCauseAnalyzer:
    """
    Deterministically identifies a likely root cause
    from retrieved incident evidence.

    This component does not use the LLM.

    It uses explicit diagnostic patterns and
    evidence provenance to establish a
    traceable root-cause hypothesis.
    """

    ROOT_CAUSES = [
        {
            "name": "Connection pool exhaustion",
            "patterns": [
                r"connection pool exhausted",
                r"no available database connections",
                r"connectionpoolexhaustederror",
                r"pool exhaustion",
                r"out of connections",
            ],
            "explanation": (
                    "The database connection pool reached "
                    "its available connection limit, preventing "
                    "the affected service from acquiring a connection."
            ),
        },
        {
            "name": "Database connection timeout",
            "patterns": [
                r"connection timeout",
                r"database connection timed out",
                r"connection timed out",
            ],
            "explanation": (
                "The service was unable to establish or "
                "obtain a database connection within the "
                "configured timeout period."
            ),
        },
        {
            "name": "API request timeout",
            "patterns": [
                r"api timeout",
                r"request timeout",
                r"request timed out",
                r"http timeout",
            ],
            "explanation": (
                "An API request exceeded its allowed "
                "response time."
            ),
        },
        {
            "name": "Authentication failure",
            "patterns": [
                r"authentication failed",
                r"invalid credentials",
                r"unauthorized",
                r"access denied",
                r"authentication error",
            ],
            "explanation": (
                "The service failed to authenticate "
                "against a required resource."
            ),
        },
        {
            "name": "Null pointer failure",
            "patterns": [
                r"nullpointerexception",
                r"null pointer exception",
                r"none type",
                r"object is null",
            ],
            "explanation": (
                "Application code attempted to access "
                "an object or value that was null."
            ),
        },
        {
            "name": "Memory exhaustion",
            "patterns": [
                r"out of memory",
                r"memory exhausted",
                r"memoryerror",
                r"heap space",
                r"oom",
            ],
            "explanation": (
                "The application exhausted the available "
                "memory required for execution."
            ),
        },
        {
            "name": "Network connectivity failure",
            "patterns": [
                r"network unreachable",
                r"connection refused",
                r"connection reset",
                r"host unreachable",
                r"network error",
            ],
            "explanation": (
                "The service could not establish or "
                "maintain network connectivity to a "
                "required resource."
            ),
        },
        {
            "name": "Storage failure",
            "patterns": [
                r"disk full",
                r"no space left",
                r"storage exhausted",
                r"filesystem full",
            ],
            "explanation": (
                "The system lacked sufficient storage "
                "capacity to complete the operation."
            ),
        },
                {
            "name": "Cache failure",
            "patterns": [
                r"cache connection failed",
                r"cacheconnectionerror",
                r"unable to connect to cache",
                r"cache server",
                r"redis connection",
                r"redis error",
                r"cache unavailable",
            ],
            "explanation": (
                "The service was unable to connect to or "
                "access the configured cache service."
            ),
        },
        {
            "name": "Kafka failure",
            "patterns": [
                r"kafka message publish failed",
                r"kafkaproducererror",
                r"failed to publish message",
                r"kafka producer",
                r"kafka error",
                r"unable to publish",
                r"message publish failed",
            ],
            "explanation": (
                "The service failed to publish a message "
                "to the Kafka messaging system."
            ),
        },
        {
            "name": "Configuration failure",
            "patterns": [
                r"missing requiredconfiguration",
                r"missing required configuration",
                r"configurationerror",
                r"required configuration value is missing",
                r"configuration value is missing",
                r"invalid configuration",
                r"configuration missing",
            ],
            "explanation": (
                "The service could not initialize or complete "
                "the operation because a required configuration "
                "value was missing or invalid."
            ),
        },
    ]

    def analyze(
        self,
        evidence: list[dict]
    ) -> dict:

        candidates = []

        for root_cause in self.ROOT_CAUSES:

            matched_evidence = []

            for item in evidence:

                text = item.get(
                    "text",
                    ""
                ).lower()

                for pattern in root_cause[
                    "patterns"
                ]:

                    if re.search(
                        pattern,
                        text
                    ):

                        matched_evidence.append(
                            item
                        )

                        break

            if not matched_evidence:
                continue

            # ---------------------------------------------
            # Calculate deterministic support
            # ---------------------------------------------

            observed_count = sum(
                1
                for item in matched_evidence
                if item.get("provenance")
                == "observed"
            )

            code_count = sum(
                1
                for item in matched_evidence
                if item.get("provenance")
                == "code"
            )

            stacktrace_count = sum(
                1
                for item in matched_evidence
                if item.get("source_type")
                == "stacktrace"
            )

            source_files = {
                item.get("source_file")
                for item in matched_evidence
                if item.get("source_file")
            }

            support_score = (
                (observed_count * 0.30)
                + (code_count * 0.25)
                + (stacktrace_count * 0.20)
                + (len(source_files) * 0.10)
            )

            support_score = min(
                support_score,
                1.0
            )

            candidates.append(
                {
                    "root_cause": root_cause[
                        "name"
                    ],
                    "explanation": root_cause[
                        "explanation"
                    ],
                    "support_score": support_score,
                    "observed_evidence": (
                        observed_count
                    ),
                    "code_evidence": (
                        code_count
                    ),
                    "stacktrace_evidence": (
                        stacktrace_count
                    ),
                    "supporting_sources": (
                        len(source_files)
                    ),
                    "evidence": matched_evidence,
                }
            )

        # ---------------------------------------------
        # No root cause established
        # ---------------------------------------------

        if not candidates:

            return {
                "root_cause": (
                    "Not established by "
                    "available evidence."
                ),
                "explanation": (
                    "No known root-cause pattern "
                    "was sufficiently supported "
                    "by the retrieved evidence."
                ),
                "support_score": 0.0,
                "confidence": "LOW",
                "evidence": [],
            }

        # ---------------------------------------------
        # Select strongest candidate
        # ---------------------------------------------

        candidates.sort(
            key=lambda item: item[
                "support_score"
            ],
            reverse=True
        )

        best = candidates[0]

        # ---------------------------------------------
        # Determine confidence
        # ---------------------------------------------

        if best["support_score"] >= 0.75:
            confidence = "HIGH"

        elif best["support_score"] >= 0.45:
            confidence = "MEDIUM"

        else:
            confidence = "LOW"

        return {
            **best,
            "confidence": confidence,
        }