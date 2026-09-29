import json

from app.rag.investigator import IncidentInvestigator


DATASET_PATH = "data/evaluation/expanded_evaluation_dataset.json"

IDS = [
    f"synthetic_{i:03d}"
    for i in range(36, 51)
]


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    cases = {
        case["incident_id"]: case
        for case in dataset["cases"]
        if case["incident_id"] in IDS
    }

    investigator = IncidentInvestigator(
        "data/incidents"
    )

    passed = 0

    print("=" * 80)
    print("TRACEAI — NEW ROOT-CAUSE REGRESSION")
    print("=" * 80)

    for incident_id in IDS:
        case = cases[incident_id]

        result = investigator.investigate(
            query=case["query"],
            top_k=8,
            incident_id=incident_id,
        )

        expected = case["ground_truth_root_cause"]
        predicted = result["root_cause"]["root_cause"]

        ok = expected.lower() == predicted.lower()

        if ok:
            passed += 1

        print(
            f"{incident_id}: "
            f"{'PASS' if ok else 'FAIL'} | "
            f"Expected={expected} | "
            f"Predicted={predicted}"
        )

    print()
    print(f"Passed: {passed}/15")
    print(f"Failed: {15 - passed}/15")


if __name__ == "__main__":
    main()