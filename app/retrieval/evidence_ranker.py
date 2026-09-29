from app.retrieval.diagnostic_signals import DiagnosticSignals
from app.retrieval.causal_signals import CausalSignals


class EvidenceRanker:
    """
    Evidence-aware ranking for incident investigation.

    Ranking combines:
    1. Semantic similarity
    2. Evidence provenance
    3. Log severity
    4. Diagnostic signals
    5. Root-cause signals
    6. Failure signals
    7. Root-cause-specific diagnostic signatures
    8. Generic downstream symptom penalties
    9. Stack-trace specificity
    """

    PROVENANCE_WEIGHTS = {
        "observed": 0.30,
        "code": 0.25,
        "documentation": 0.05,
        "historical": 0.15,
    }

    LEVEL_WEIGHTS = {
        "ERROR": 0.20,
        "WARN": 0.10,
        "INFO": 0.00,
        "DEBUG": 0.00,
    }

    SIGNAL_MULTIPLIERS = {
        "observed": 1.00,
        "code": 1.00,
        "documentation": 0.40,
        "historical": 0.70,
    }

    # Strong diagnostic signatures for known failure categories.
    # These are deliberately explicit so highly specific evidence
    # can outrank generic downstream failure messages.
    DIAGNOSTIC_SIGNATURES = {
        # API / request timeout
        "api_timeout": [
            ("request timeout", 0.55),
            ("requesttimeouterror", 0.65),
            ("request timed out", 0.55),
            ("timed out", 0.40),
            ("timeout after", 0.40),
            ("request timeout after", 0.50),
        ],

        # Database connection pool
        "connection_pool": [
            ("connection pool exhausted", 0.65),
            ("no available database connections", 0.70),
            ("connectionpoolexhaustederror", 0.70),
            ("pool exhaustion", 0.60),
            ("out of connections", 0.55),
        ],

        # Authentication
        "authentication": [
            ("invalid credentials", 0.60),
            ("authentication failed", 0.65),
            ("authenticationerror", 0.70),
            ("unauthorized", 0.45),
            ("invalid password", 0.55),
            ("access denied", 0.45),
        ],

        # Memory
        "memory": [
            ("outofmemoryerror", 0.90),
            ("out of memory", 0.85),
            ("java heap space", 0.85),
            ("memory allocation", 0.70),
            ("memory exhausted", 0.80),
        ],

        # Null pointer
        "null_pointer": [
            ("nullpointerexception", 0.90),
            ("null pointer exception", 0.90),
            ("object is null", 0.75),
            ("cannot invoke", 0.75),
            ("noneType", 0.65),
            ("attributeerror", 0.60),
        ],

        # Network connectivity
        "network": [
            ("network connection failed", 0.70),
            ("network connectivity", 0.65),
            ("connection refused", 0.70),
            ("connection reset", 0.65),
            ("host unreachable", 0.75),
            ("network unreachable", 0.75),
            ("socket timeout", 0.65),
            ("dns resolution failed", 0.75),
            ("name resolution failed", 0.70),
            ("connection refusederror", 0.70),
        ],

        # Storage
        "storage": [
            ("storagefullerror", 0.95),
            ("no space left on device", 0.95),
            ("disk full", 0.90),
            ("storage full", 0.90),
            ("out of disk space", 0.90),
            ("filesystem full", 0.85),
            ("file system full", 0.85),
        ],

        # Cache
        "cache": [
            ("cache connection failed", 0.75),
            ("cacheconnectionerror", 0.85),
            ("unable to connect to cache", 0.80),
            ("cache unavailable", 0.75),
            ("redis connection", 0.75),
            ("redis error", 0.75),
            ("cache server", 0.55),
        ],

        # Kafka
        "kafka": [
            ("kafka message publish failed", 0.85),
            ("kafkaproducererror", 0.90),
            ("failed to publish message", 0.80),
            ("kafka producer", 0.65),
            ("kafka error", 0.75),
            ("unable to publish", 0.70),
            ("message publish failed", 0.75),
        ],

        # Configuration
        "configuration": [
            ("missing required configuration", 0.95),
            ("missing requiredconfiguration", 0.95),
            ("configurationerror", 0.90),
            ("required configuration value is missing", 0.95),
            ("configuration value is missing", 0.90),
            ("invalid configuration", 0.85),
            ("configuration missing", 0.85),
        ],
    }

    GENERIC_FAILURE_MESSAGES = {
        "inventory request failed",
        "login request failed",
        "profile request failed",
        "recommendation request failed",
        "payment transaction failed",
        "request processing failed",
        "request failed",
        "operation failed",
    }

    def __init__(self):
        self.diagnostic_signals = DiagnosticSignals()
        self.causal_signals = CausalSignals()

    def _calculate_specific_signal_bonus(
        self,
        text_lower: str,
    ) -> float:
        """
        Calculate a bonus for highly specific diagnostic signatures.

        The strongest matching signature is used instead of blindly
        adding every matching pattern. This prevents multiple similar
        phrases in one evidence item from producing an excessive score.
        """

        matched_scores = []

        for signatures in self.DIAGNOSTIC_SIGNATURES.values():
            for phrase, weight in signatures:
                if phrase in text_lower:
                    matched_scores.append(weight)

        if not matched_scores:
            return 0.0

        return max(matched_scores)

    def rank(self, results: list[dict]) -> list[dict]:
        ranked = []

        for result in results:
            text = result.get("text", "")
            text_lower = text.lower()

            semantic_score = float(
                result.get("score", 0.0)
            )

            provenance = result.get(
                "provenance",
                "documentation",
            )

            provenance_bonus = self.PROVENANCE_WEIGHTS.get(
                provenance,
                0.0,
            )

            signal_multiplier = self.SIGNAL_MULTIPLIERS.get(
                provenance,
                0.40,
            )

            level = result.get(
                "metadata",
                {},
            ).get("level", "")

            level_bonus = self.LEVEL_WEIGHTS.get(
                level,
                0.0,
            )

            # --------------------------------------------------
            # Diagnostic signals
            # --------------------------------------------------

            raw_diagnostic_score = (
                self.diagnostic_signals.calculate(text)
            )

            diagnostic_score = (
                raw_diagnostic_score
                * signal_multiplier
            )

            # --------------------------------------------------
            # Causal signals
            # --------------------------------------------------

            causal_scores = (
                self.causal_signals.calculate(text)
            )

            raw_root_cause_score = (
                causal_scores["root_cause"]
            )

            raw_failure_score = (
                causal_scores["failure"]
            )

            root_cause_score = (
                raw_root_cause_score
                * signal_multiplier
            )

            failure_score = (
                raw_failure_score
                * signal_multiplier
            )

            # --------------------------------------------------
            # Root-cause-specific signatures
            # --------------------------------------------------

            specific_signal_bonus = (
                self._calculate_specific_signal_bonus(
                    text_lower
                )
            )

            # Documentation describes the condition but is not
            # direct observation, so reduce its specific bonus.
            if provenance == "documentation":
                specific_signal_weight = (
                    specific_signal_bonus * 0.35
                )

            elif provenance == "historical":
                specific_signal_weight = (
                    specific_signal_bonus * 0.60
                )

            else:
                specific_signal_weight = (
                    specific_signal_bonus
                )

            # --------------------------------------------------
            # Stack-trace specificity
            # --------------------------------------------------

            stacktrace_bonus = 0.0

            if result.get("source_type") == "stacktrace":
                # Any explicit exception is useful.
                if (
                    "exception" in text_lower
                    or "error" in text_lower
                ):
                    stacktrace_bonus += 0.20

                # Stacktrace evidence containing a specific
                # diagnostic signature gets an additional bonus.
                if specific_signal_bonus > 0:
                    stacktrace_bonus += 0.25

            # --------------------------------------------------
            # Generic downstream symptoms
            # --------------------------------------------------

            generic_failure_penalty = 0.0

            if text_lower.strip() in self.GENERIC_FAILURE_MESSAGES:
                generic_failure_penalty += 0.25

            if "unable to complete" in text_lower:
                generic_failure_penalty += 0.15

            if "returning failure response" in text_lower:
                generic_failure_penalty += 0.20

            if "request processing failed" in text_lower:
                generic_failure_penalty += 0.20

            # Generic failure messages should not dominate
            # highly specific diagnostic evidence.
            if (
                "failed" in text_lower
                and specific_signal_bonus == 0
            ):
                generic_failure_penalty += 0.10

            # --------------------------------------------------
            # Final score
            # --------------------------------------------------

            final_score = (
                semantic_score
                + provenance_bonus
                + level_bonus
                + (diagnostic_score * 0.30)
                + (root_cause_score * 0.55)
                + (failure_score * 0.10)
                + specific_signal_weight
                + stacktrace_bonus
                - generic_failure_penalty
            )

            # --------------------------------------------------
            # Store scoring details
            # --------------------------------------------------

            result["semantic_score"] = semantic_score
            result["provenance"] = provenance
            result["provenance_bonus"] = provenance_bonus
            result["signal_multiplier"] = signal_multiplier
            result["level_bonus"] = level_bonus
            result["diagnostic_score"] = diagnostic_score
            result["root_cause_score"] = root_cause_score
            result["failure_score"] = failure_score
            result["specific_signal_bonus"] = (
                specific_signal_bonus
            )
            result["specific_signal_weight"] = (
                specific_signal_weight
            )
            result["stacktrace_bonus"] = (
                stacktrace_bonus
            )
            result["generic_failure_penalty"] = (
                generic_failure_penalty
            )
            result["final_score"] = final_score

            ranked.append(result)

        ranked.sort(
            key=lambda item: item["final_score"],
            reverse=True,
        )

        return ranked

    def diversify(
        self,
        ranked_results: list[dict],
        top_k: int,
    ) -> list[dict]:
        """
        Select strong evidence while avoiding excessive
        repetition of the same source type.
        """

        if not ranked_results:
            return []

        selected = []
        remaining = ranked_results.copy()

        source_type_counts = {}

        while (
            remaining
            and len(selected) < top_k
        ):
            best_index = None
            best_adjusted_score = float("-inf")

            for index, item in enumerate(remaining):
                source_type = item.get(
                    "source_type",
                    "unknown",
                )

                count = source_type_counts.get(
                    source_type,
                    0,
                )

                diversity_penalty = count * 0.12

                adjusted_score = (
                    item.get("final_score", 0.0)
                    - diversity_penalty
                )

                if adjusted_score > best_adjusted_score:
                    best_adjusted_score = (
                        adjusted_score
                    )
                    best_index = index

            selected_item = remaining.pop(
                best_index
            )

            selected.append(selected_item)

            source_type = selected_item.get(
                "source_type",
                "unknown",
            )

            source_type_counts[source_type] = (
                source_type_counts.get(
                    source_type,
                    0,
                )
                + 1
            )

        return selected