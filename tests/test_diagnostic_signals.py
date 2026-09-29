from app.retrieval.diagnostic_signals import (
    DiagnosticSignals
)


def main():

    detector = DiagnosticSignals()

    examples = [
        "Payment request received",
        "Unable to acquire database connection",
        "Connection pool exhausted",
        "Connection timeout after 3000ms",
        "ConnectionPoolExhaustedError",
        "Payment transaction failed",
    ]

    print("\n" + "=" * 60)
    print("TRACEAI DIAGNOSTIC SIGNALS")
    print("=" * 60)

    for text in examples:

        score = detector.calculate(
            text
        )

        print(
            f"\nScore: {score:.2f}"
        )

        print(
            f"Text : {text}"
        )

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()