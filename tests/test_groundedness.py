from app.rag.groundedness import GroundednessAnalyzer


def main():
    print("=" * 70)
    print("TRACEAI — GROUNDEDNESS ANALYZER TEST")
    print("=" * 70)

    analyzer = GroundednessAnalyzer()

    evidence = [
        {
            "source_file": "incident_001.log",
            "location": "line 4",
        },
        {
            "source_file": "incident_001.stacktrace",
            "location": "exception",
        },
    ]

    # ---------------------------------------------------------
    # Test 1 — Fully grounded
    # ---------------------------------------------------------

    grounded_analysis = """
### 1. ROOT CAUSE

The connection pool was exhausted
[incident_001.log:line 4].

### 2. FAILURE CHAIN

The stacktrace reports a connection pool exception
[incident_001.stacktrace:exception].

### 3. IMPACT

Not established by available evidence.

### 4. EVIDENCE

The log confirms connection pool exhaustion
[incident_001.log:line 4].
"""

    result = analyzer.analyze(
        grounded_analysis,
        evidence,
    )

    print("\nTEST 1 — Fully grounded")
    print(result)

    assert result["status"] == "PASS"
    assert result["claim_coverage"] >= 0.90

    print("PASS")

    # ---------------------------------------------------------
    # Test 2 — Partially grounded
    # ---------------------------------------------------------

    partially_grounded = """
### 1. ROOT CAUSE

The connection pool was exhausted
[incident_001.log:line 4].

### 2. FAILURE CHAIN

The service then crashed because of a database leak.

### 3. IMPACT

Customers were unable to complete payments.
"""

    result = analyzer.analyze(
        partially_grounded,
        evidence,
    )

    print("\nTEST 2 — Partially grounded")
    print(result)

    assert result["status"] == "REVIEW"
    assert result["ungrounded_claims"] > 0

    print("PASS")

    # ---------------------------------------------------------
    # Test 3 — No grounding
    # ---------------------------------------------------------

    ungrounded = """
### 1. ROOT CAUSE

The database server crashed.

### 2. FAILURE CHAIN

The application lost all database connections.

### 3. IMPACT

The company lost revenue.
"""

    result = analyzer.analyze(
        ungrounded,
        evidence,
    )

    print("\nTEST 3 — No grounding")
    print(result)

    assert result["status"] == "REVIEW"
    assert result["claim_coverage"] == 0.0

    print("PASS")

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("GROUNDEDNESS TEST SUMMARY")
    print("=" * 70)

    print("Fully grounded analysis : PASS")
    print("Partially grounded      : PASS")
    print("Ungrounded analysis     : PASS")

    print("=" * 70)
    print("STATUS: GROUNDEDNESS ANALYZER PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()