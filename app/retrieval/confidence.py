class EvidenceConfidence:
    """
    Calculates grounded confidence from evidence diversity and
    root-cause-specific diagnostic signals.

    This is a deterministic heuristic, not an empirical probability.
    """

    ROOT_CAUSE_SIGNALS = {
        "connection pool exhaustion": [
            "connection pool exhausted",
            "no available database connections",
            "connectionpoolexhaustederror",
            "pool exhaustion",
            "out of connections",
            "unable to acquire database connection",
            "active connections:",
],
        "api request timeout": [
            "request timeout",
            "requesttimeouterror",
            "request timed out",
            "http timeout",
            "timed out",
        ],
        "authentication failure": [
            "authentication failed",
            "authenticationerror",
            "invalid credentials",
            "access denied",
            "unauthorized",
        ],
        "null pointer failure": [
            "nullpointerexception",
            "null pointer exception",
            "object is null",
            "cannot invoke",
        ],
        "memory exhaustion": [
            "outofmemoryerror",
            "out of memory",
            "java heap space",
            "memory exhausted",
            "memory allocation",
        ],
        "network connectivity failure": [
            "network unreachable",
            "connection refused",
            "connection reset",
            "host unreachable",
            "network error",
        ],
        "storage failure": [
            "disk full",
            "no space left",
            "storage exhausted",
            "filesystem full",
        ],
    }

    def calculate(
        self,
        evidence: list[dict],
        root_cause: str | None = None,
    ) -> dict:

        if not evidence:
            return {
                "confidence": "LOW",
                "score": 0.0,
                "observed_root_cause": False,
                "stacktrace_confirmation": False,
                "code_confirmation": False,
                "failure_confirmation": False,
                "supporting_source_count": 0,
                "diagnostic_signal_count": 0,
            }

        root_cause_key = (root_cause or "").lower()

        signals = self.ROOT_CAUSE_SIGNALS.get(
            root_cause_key,
            [],
        )

        observed_root_cause = False
        stacktrace_confirmation = False
        code_confirmation = False
        failure_confirmation = False

        diagnostic_signal_count = 0
        supporting_sources = set()

        for item in evidence:
            text = item.get("text", "").lower()
            source_type = item.get("source_type", "")
            provenance = item.get("provenance", "")

            if item.get("source_file"):
                supporting_sources.add(item["source_file"])

            # ---------------------------------------------
            # Root-cause diagnostic signal
            # ---------------------------------------------

            signal_match = False

            for signal in signals:
                if signal in text:
                    signal_match = True
                    break

            if signal_match:
                diagnostic_signal_count += 1

                if provenance == "observed":
                    observed_root_cause = True

            # ---------------------------------------------
            # Stack trace confirmation
            # ---------------------------------------------

            if source_type == "stacktrace":
                if signal_match:
                    stacktrace_confirmation = True

            # ---------------------------------------------
            # Code confirmation
            # ---------------------------------------------

            if provenance == "code":
                if signal_match:
                    code_confirmation = True

            # ---------------------------------------------
            # Failure confirmation
            # ---------------------------------------------

            failure_signals = [
                "failed",
                "failure",
                "unable",
                "exception",
                "error",
                "timeout",
                "denied",
                "exhausted",
                "nullpointer",
                "outofmemory",
            ]

            if any(signal in text for signal in failure_signals):
                failure_confirmation = True

        # ---------------------------------------------
        # Deterministic grounded score
        # ---------------------------------------------

        score = 0.0

        if observed_root_cause:
            score += 0.35

        if stacktrace_confirmation:
            score += 0.25

        if code_confirmation:
            score += 0.20

        if failure_confirmation:
            score += 0.10

        if len(supporting_sources) >= 2:
            score += 0.10

        # Multiple independent diagnostic signals provide
        # additional evidence, but do not allow the score
        # to exceed 1.0.
        if diagnostic_signal_count >= 2:
            score += 0.05

        score = min(score, 1.0)

        if score >= 0.80:
            confidence = "HIGH"
        elif score >= 0.50:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return {
            "confidence": confidence,
            "score": score,
            "observed_root_cause": observed_root_cause,
            "stacktrace_confirmation": stacktrace_confirmation,
            "code_confirmation": code_confirmation,
            "failure_confirmation": failure_confirmation,
            "supporting_source_count": len(supporting_sources),
            "diagnostic_signal_count": diagnostic_signal_count,
        }