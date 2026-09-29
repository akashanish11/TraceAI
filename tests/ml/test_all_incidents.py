from app.rag.investigator import IncidentInvestigator


def main():
    investigator = IncidentInvestigator("data/incidents")

    tests = [
        ("legacy_incident", "What caused the payment service database failure?"),
        ("incident_002", "What caused the order service failure?"),
        ("incident_003", "What caused the authentication failure?"),
        ("incident_004", "What caused the recommendation service failure?"),
        ("incident_005", "What caused the user profile failure?"),
    ]

    expected = {
        "legacy_incident": "Connection pool exhaustion",
        "incident_002": "API request timeout",
        "incident_003": "Authentication failure",
        "incident_004": "Memory exhaustion",
        "incident_005": "Null pointer failure",
    }

    print("\n" + "=" * 70)
    print("TRACEAI — MULTI-INCIDENT REGRESSION TEST")
    print("=" * 70)

    passed = 0

    for incident_id, query in tests:
        print("\n" + "-" * 70)
        print(f"INCIDENT: {incident_id}")

        result = investigator.investigate(
            query,
            top_k=8,
            incident_id=incident_id,
        )

        root_cause = result["root_cause"]["root_cause"]
        confidence = result["root_cause"]["confidence"]
        support_score = result["root_cause"]["support_score"]

        expected_root_cause = expected[incident_id]

        status = "PASS" if root_cause == expected_root_cause else "FAIL"

        if status == "PASS":
            passed += 1

        print(f"Expected   : {expected_root_cause}")
        print(f"Predicted  : {root_cause}")
        print(f"Confidence : {confidence}")
        print(f"Support    : {support_score:.2f}")
        print(f"Status     : {status}")

        print("\nTop Evidence:")
        for index, item in enumerate(result["evidence"][:5], start=1):
            print(
                f"{index}. "
                f"{item['source_file']} "
                f"{item['location']} "
                f"=> {item['text'][:100]}"
            )

    print("\n" + "=" * 70)
    print("REGRESSION TEST SUMMARY")
    print("=" * 70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {len(tests) - passed}/{len(tests)}")

    if passed == len(tests):
        print("STATUS: ALL INCIDENTS PASSED")
    else:
        print("STATUS: SOME INCIDENTS FAILED")


if __name__ == "__main__":
    main()