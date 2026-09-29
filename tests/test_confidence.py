from app.retrieval.confidence import EvidenceConfidence


def main():

    evidence = [
        {
            "text": "Connection pool exhausted",
            "source_type": "log",
            "provenance": "observed",
            "source_file": "incident_001.log",
        },
        {
            "text": (
                "ConnectionPoolExhaustedError: "
                "No available database connections"
            ),
            "source_type": "stacktrace",
            "provenance": "observed",
            "source_file": "incident_001.stacktrace",
        },
        {
            "text": (
                "process_payment() in "
                "database/connection_pool.py:87 "
                "executed: "
                "raise ConnectionPoolExhaustedError"
            ),
            "source_type": "stacktrace",
            "provenance": "code",
            "source_file": "incident_001.stacktrace",
        },
        {
            "text": "Payment transaction failed",
            "source_type": "log",
            "provenance": "observed",
            "source_file": "incident_001.log",
        },
    ]

    confidence_calculator = EvidenceConfidence()

    result = confidence_calculator.calculate(
        evidence,
        root_cause="Connection pool exhaustion",
    )

    print("\n" + "=" * 60)
    print("TRACEAI EVIDENCE-GROUNDED CONFIDENCE")
    print("=" * 60)

    print(
        f"\nConfidence              : "
        f"{result['confidence']}"
    )

    print(
        f"Support Score           : "
        f"{result['score']:.2f}"
    )

    print(
        f"Observed Root Cause     : "
        f"{result['observed_root_cause']}"
    )

    print(
        f"Stacktrace Confirmation : "
        f"{result['stacktrace_confirmation']}"
    )

    print(
        f"Code Confirmation       : "
        f"{result['code_confirmation']}"
    )

    print(
        f"Failure Confirmation    : "
        f"{result['failure_confirmation']}"
    )

    print(
        f"Supporting Sources      : "
        f"{result['supporting_source_count']}"
    )

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()