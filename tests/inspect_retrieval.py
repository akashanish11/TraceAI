import json

from app.rag.investigator import IncidentInvestigator


DATASET_PATH = "data/evaluation/expanded_evaluation_dataset.json"


def inspect_case(incident_id):
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    case = next(
        item
        for item in dataset["cases"]
        if item["incident_id"] == incident_id
    )

    investigator = IncidentInvestigator(
        "data/incidents"
    )

    result = investigator.investigate(
        query=case["query"],
        top_k=8,
        incident_id=incident_id,
    )

    print("=" * 80)
    print(f"INCIDENT: {incident_id}")
    print("=" * 80)

    print("\nGROUND TRUTH:")
    for item in case["relevant_evidence"]:
        print(f"- {item}")

    print("\nRETRIEVED EVIDENCE:")

    for index, item in enumerate(
        result["evidence"],
        start=1,
    ):
        print(
            f"\n{index}. "
            f"source_type={item.get('source_type')} "
            f"source_file={item.get('source_file')} "
            f"location={item.get('location')}"
        )

        print(
            f"   semantic_score="
            f"{item.get('score', 0.0):.3f}"
        )

        print(
            f"   final_score="
            f"{item.get('final_score', 0.0):.3f}"
        )

        print(
            f"   text={item.get('text')}"
        )


if __name__ == "__main__":
    inspect_case("synthetic_031")