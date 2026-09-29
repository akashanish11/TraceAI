import json

from app.parsers.stacktrace_parser import parse_stacktrace


DATASET_PATH = "data/evaluation/expanded_evaluation_dataset.json"


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    mismatches = []

    for case in dataset["cases"]:
        incident_id = case["incident_id"]

        expected = case["relevant_evidence"][-1]

        if not expected.startswith("incident.stacktrace:"):
            continue

        if expected == "incident.stacktrace:exception":
            continue

        path = (
            f"data/incidents/"
            f"{incident_id}/incident.stacktrace"
        )

        parsed = parse_stacktrace(path)

        actual_locations = {
            f"{frame['file']}:{frame['line']}"
            for frame in parsed["frames"]
        }

        expected_location = expected.split(
            "incident.stacktrace:",
            1
        )[1]

        if expected_location not in actual_locations:
            mismatches.append(
                {
                    "incident_id": incident_id,
                    "expected": expected_location,
                    "actual": sorted(actual_locations),
                }
            )

    print("=" * 80)
    print("TRACEAI — EVIDENCE GROUND-TRUTH AUDIT")
    print("=" * 80)

    print(f"Total cases checked : {len(dataset['cases'])}")
    print(f"Mismatches          : {len(mismatches)}")

    if mismatches:
        print()
        print("MISMATCHES:")
        for item in mismatches:
            print()
            print(f"Incident : {item['incident_id']}")
            print(f"Expected : {item['expected']}")
            print(f"Actual   : {item['actual']}")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()