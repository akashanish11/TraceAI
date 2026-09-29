from app.retrieval.causal_signals import (
    CausalSignals
)


def main():

    detector = CausalSignals()

    examples = [
        "Payment transaction failed",
        "Unable to acquire database connection",
        "Connection pool exhausted",
        "ConnectionPoolExhaustedError: No available database connections",
        "Retrying payment request",
    ]

    print("\n" + "=" * 60)
    print("TRACEAI CAUSAL SIGNALS")
    print("=" * 60)

    for text in examples:

        result = detector.calculate(
            text
        )

        print("\nText:")
        print(text)

        print(
            f"Root Cause Signal : "
            f"{result['root_cause']:.2f}"
        )

        print(
            f"Failure Signal    : "
            f"{result['failure']:.2f}"
        )

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()