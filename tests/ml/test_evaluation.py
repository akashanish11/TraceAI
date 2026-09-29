import json
from pathlib import Path

from app.rag.investigator import IncidentInvestigator


DATASET_PATH = Path("data/evaluation/evaluation_dataset.json")


def normalize(value: str) -> str:
    return value.replace("\\", "/").strip().lower()


def evidence_key(item: dict) -> str:
    return normalize(
        f"{item.get('source_file', '')}:{item.get('location', '')}"
    )


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    retrieved_k = retrieved[:k]

    if not retrieved_k:
        return 0.0

    relevant_count = sum(
        1 for item in retrieved_k
        if item in relevant
    )

    return relevant_count / len(retrieved_k)


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0

    retrieved_k = retrieved[:k]

    relevant_count = sum(
        1 for item in retrieved_k
        if item in relevant
    )

    return relevant_count / len(relevant)


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for index, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / index

    return 0.0


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    investigator = IncidentInvestigator("data/incidents")

    root_cause_correct = 0

    precision_scores = []
    recall_scores = []
    reciprocal_ranks = []

    print("\n" + "=" * 75)
    print("TRACEAI — EVALUATION")
    print("=" * 75)

    for case in dataset:
        incident_id = case["incident_id"]
        query = case["query"]
        ground_truth = case["ground_truth_root_cause"]

        relevant_evidence = {
            normalize(item)
            for item in case["relevant_evidence"]
        }

        print("\n" + "-" * 75)
        print(f"INCIDENT: {incident_id}")
        print(f"QUERY   : {query}")

        result = investigator.investigate(
            query,
            top_k=8,
            incident_id=incident_id,
        )

        predicted_root_cause = result["root_cause"]["root_cause"]

        retrieved_evidence = [
            evidence_key(item)
            for item in result["evidence"]
        ]

        root_cause_match = (
            predicted_root_cause.strip().lower()
            == ground_truth.strip().lower()
        )

        if root_cause_match:
            root_cause_correct += 1

        p_at_5 = precision_at_k(
            retrieved_evidence,
            relevant_evidence,
            5,
        )

        r_at_5 = recall_at_k(
            retrieved_evidence,
            relevant_evidence,
            5,
        )

        rr = reciprocal_rank(
            retrieved_evidence,
            relevant_evidence,
        )

        precision_scores.append(p_at_5)
        recall_scores.append(r_at_5)
        reciprocal_ranks.append(rr)

        print(f"Expected Root Cause : {ground_truth}")
        print(f"Predicted Root Cause: {predicted_root_cause}")
        print(
            f"Root Cause Status   : "
            f"{'PASS' if root_cause_match else 'FAIL'}"
        )

        print(f"Precision@5         : {p_at_5:.3f}")
        print(f"Recall@5            : {r_at_5:.3f}")
        print(f"Reciprocal Rank     : {rr:.3f}")

    total_cases = len(dataset)

    root_cause_accuracy = (
        root_cause_correct / total_cases
        if total_cases
        else 0.0
    )

    mean_precision = (
        sum(precision_scores) / len(precision_scores)
        if precision_scores
        else 0.0
    )

    mean_recall = (
        sum(recall_scores) / len(recall_scores)
        if recall_scores
        else 0.0
    )

    mean_reciprocal_rank = (
        sum(reciprocal_ranks) / len(reciprocal_ranks)
        if reciprocal_ranks
        else 0.0
    )

    print("\n" + "=" * 75)
    print("FINAL EVALUATION RESULTS")
    print("=" * 75)

    print(f"Test Cases          : {total_cases}")
    print(
        f"Root Cause Accuracy : "
        f"{root_cause_accuracy:.2%}"
    )
    print(
        f"Mean Precision@5    : "
        f"{mean_precision:.3f}"
    )
    print(
        f"Mean Recall@5       : "
        f"{mean_recall:.3f}"
    )
    print(
        f"MRR                 : "
        f"{mean_reciprocal_rank:.3f}"
    )

    print("\n" + "=" * 75)


if __name__ == "__main__":
    main()