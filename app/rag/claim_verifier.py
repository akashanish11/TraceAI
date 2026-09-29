import re


class ClaimVerifier:
    """
    Performs lightweight deterministic verification of
    potentially risky claims in an LLM-generated
    investigation.

    This is a heuristic guardrail, not semantic proof.

    The verifier checks whether risky outcome, impact,
    recovery, and system-state claims are supported
    by the retrieved evidence.
    """

    RISKY_PATTERNS = [
        {
            "pattern": r"\btemporary\b",
            "name": "temporary failure",
            "required_signals": [
                "resolved",
                "recovered",
                "recovery",
                "restored",
            ],
        },
        {
            "pattern": r"\bresolved\b",
            "name": "issue resolved",
            "required_signals": [
                "resolved",
                "recovered",
                "recovery",
                "restored",
            ],
        },
        {
            "pattern": r"\bsuccessfully recovered\b",
            "name": "successful recovery",
            "required_signals": [
                "successfully recovered",
                "recovered successfully",
                "recovery successful",
                "restored successfully",
            ],
        },
        {
            "pattern": r"\bunsuccessful\b",
            "name": "unsuccessful outcome",
            "required_signals": [
                "unsuccessful",
                "failed",
                "failure",
                "unable",
            ],
        },
        {
            "pattern": r"\bsuccessful(?:ly)?\b",
            "name": "successful outcome",
            "required_signals": [
                "successful",
                "successfully",
            ],
        },
        {
            "pattern": r"\bfailed to recover\b",
            "name": "failed recovery",
            "required_signals": [
                "failed to recover",
                "recovery failed",
                "could not recover",
            ],
        },
        {
            "pattern": r"\bpersisted\b",
            "name": "persistent failure",
            "required_signals": [
                "persisted",
                "continued",
                "still failing",
                "remained",
            ],
        },
        {
            "pattern": r"\bcontinued\b",
            "name": "continued failure",
            "required_signals": [
                "continued",
                "still failing",
                "persisted",
            ],
        },
        {
            "pattern": r"\bstopped\b",
            "name": "stopped system behavior",
            "required_signals": [
                "stopped",
                "shutdown",
                "terminated",
            ],
        },
        {
            "pattern": r"\bcompleted successfully\b",
            "name": "successful completion",
            "required_signals": [
                "completed successfully",
                "successfully completed",
            ],
        },
        {
            "pattern": r"\bcustomer impact\b",
            "name": "customer impact",
            "required_signals": [
                "customer",
                "user impact",
                "users affected",
            ],
        },
        {
            "pattern": r"\brevenue loss\b",
            "name": "revenue loss",
            "required_signals": [
                "revenue loss",
                "financial loss",
                "lost revenue",
            ],
        },
        {
            "pattern": r"\bdata loss\b",
            "name": "data loss",
            "required_signals": [
                "data loss",
                "data was lost",
                "lost data",
            ],
        },
        {
            "pattern": r"\bsecurity impact\b",
            "name": "security impact",
            "required_signals": [
                "security impact",
                "security breach",
                "unauthorized access",
            ],
        },
    ]

    NEGATION_PATTERNS = [
        r"\bno evidence of\b",
        r"\bno indication of\b",
        r"\bnot established\b",
        r"\bnot observed\b",
        r"\bnot supported\b",
        r"\bunknown\b",
        r"\bnone established\b",
        r"\bnot confirmed\b",
        r"\bnot demonstrated\b",
    ]

    def verify(
        self,
        analysis: str,
        evidence: list[dict],
    ) -> dict:

        evidence_text = " ".join(
            item.get("text", "")
            for item in evidence
        ).lower()

        lines = [
            line.strip()
            for line in analysis.splitlines()
            if line.strip()
        ]

        normalized_text = " ".join(lines)

        claims = []

        for rule in self.RISKY_PATTERNS:

            matches = re.finditer(
                rule["pattern"],
                normalized_text,
                re.IGNORECASE,
            )

            for match in matches:

                start = normalized_text.rfind(
                    ".",
                    0,
                    match.start(),
                )

                end = normalized_text.find(
                    ".",
                    match.end(),
                )

                if start == -1:
                    start = 0
                else:
                    start += 1

                if end == -1:
                    end = len(normalized_text)

                claim_text = (
                    normalized_text[start:end]
                    .strip()
                )

                is_negated = any(
                    re.search(
                        pattern,
                        claim_text,
                        re.IGNORECASE,
                    )
                    for pattern in self.NEGATION_PATTERNS
                )

                if is_negated:
                    continue

                supported = any(
                    signal.lower() in evidence_text
                    for signal in rule["required_signals"]
                )

                claims.append(
                    {
                        "claim": claim_text,
                        "claim_type": rule["name"],
                        "supported": supported,
                    }
                )

        supported_claims = [
            claim
            for claim in claims
            if claim["supported"]
        ]

        unsupported_claims = [
            claim
            for claim in claims
            if not claim["supported"]
        ]

        total_claims = len(claims)

        # --------------------------------------------------------
        # IMPORTANT:
        # Zero risky claims is NOT 100% claim coverage.
        #
        # It means there were no risky claims to verify.
        # --------------------------------------------------------

        if total_claims > 0:
            coverage = (
                len(supported_claims) / total_claims
            )
        else:
            coverage = None

        return {
            "claims": claims,
            "supported_claims": supported_claims,
            "unsupported_claims": unsupported_claims,

            # Number of risky claims actually inspected.
            "total_claims": total_claims,
            "checked_claims": total_claims,

            "supported_count": len(
                supported_claims
            ),

            "unsupported_count": len(
                unsupported_claims
            ),

            # None means:
            # "No risky claims were present to evaluate."
            "claim_coverage": (
                round(coverage, 3)
                if coverage is not None
                else None
            ),

            "has_unsupported_claims": (
                len(unsupported_claims) > 0
            ),

            # Explicit semantic status.
            "status": (
                "PASS"
                if len(unsupported_claims) == 0
                else "REVIEW"
            ),

            "verification_note": (
                "No risky claims detected."
                if total_claims == 0
                else (
                    f"{len(supported_claims)} of "
                    f"{total_claims} risky claims "
                    "were supported by available evidence."
                )
            ),
        }