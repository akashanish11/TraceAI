from app.retrieval.cross_source_store import (
    CrossSourceEvidenceStore
)

from app.rag.claim_verifier import (
    ClaimVerifier
)


def main():

    store = CrossSourceEvidenceStore(
        "data/incidents"
    )

    store.build()

    query = (
        "What caused the payment service "
        "database failure?"
    )

    evidence = store.search(
        query,
        top_k=8
    )

    # ---------------------------------------------------------
    # Simulated LLM output containing one unsupported claim
    # ---------------------------------------------------------

    analysis = """
The connection pool exhaustion caused the
payment transaction failure.

The payment service retried the request.

The failure was temporary and the system
successfully recovered.

There was no evidence of revenue loss.
"""

    verifier = ClaimVerifier()

    result = verifier.verify(
        analysis,
        evidence
    )

    print("\n" + "=" * 70)
    print("TRACEAI CLAIM VERIFICATION")
    print("=" * 70)

    print(
        f"\nClaims Checked : "
        f"{result['total_claims']}"
    )

    print(
        f"Supported      : "
        f"{result['supported_count']}"
    )

    print(
        f"Unsupported    : "
        f"{result['unsupported_count']}"
    )

    print(
        f"Claim Coverage : "
        f"{result['claim_coverage']:.2%}"
    )

    print("\n" + "-" * 70)

    if result[
        "has_unsupported_claims"
    ]:

        print(
            "UNSUPPORTED CLAIMS:"
        )

        for claim in result[
            "unsupported_claims"
        ]:

            print(
                f"- {claim['claim']}"
            )

            print(
                f"  Type: "
                f"{claim['claim_type']}"
            )

    else:

        print(
            "All detected claims are "
            "supported by available evidence."
        )

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()