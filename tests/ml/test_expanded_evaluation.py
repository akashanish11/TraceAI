import json
from collections import defaultdict

from app.rag.investigator import IncidentInvestigator


DATASET_PATH = "data/evaluation/expanded_evaluation_dataset.json"


def normalize(text: str) -> str:
    return text.replace("\\", "/").strip().lower()


def evidence_key(item: dict) -> str:
    source_file = normalize(item.get("source_file", ""))
    location = normalize(item.get("location", ""))

    if location:
        return f"{source_file}:{location}"

    return source_file


def get_retrieved_evidence_keys(results: list[dict], top_k: int = 5) -> set[str]:
    return {
        evidence_key(item)
        for item in results[:top_k]
    }


def calculate_metrics(
    retrieved: list[dict],
    relevant_evidence: list[str],
    top_k: int = 5,
) -> tuple[float, float, float]:
    relevant = {
        normalize(item)
        for item in relevant_evidence
    }

    retrieved_top = retrieved[:top_k]

    retrieved_keys = [
        evidence_key(item)
        for item in retrieved_top
    ]

    relevant_retrieved = [
        key for key in retrieved_keys
        if key in relevant
    ]

    precision = (
        len(set(relevant_retrieved)) / top_k
        if top_k > 0
        else 0.0
    )

    recall = (
        len(set(relevant_retrieved)) / len(relevant)
        if relevant
        else 0.0
    )

    reciprocal_rank = 0.0

    for rank, key in enumerate(retrieved_keys, start=1):
        if key in relevant:
            reciprocal_rank = 1.0 / rank
            break

    return precision, recall, reciprocal_rank


def main():
    print("=" * 80)
    print("TRACEAI — EXPANDED 50-CASE EVALUATION")
    print("=" * 80)

    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    cases = dataset["cases"]

    print(f"Dataset cases : {len(cases)}")
    print(f"Categories    : {dataset['categories']}")
    print(f"Seed          : {dataset['seed']}")
    print()

    investigator = IncidentInvestigator( incident_directory="data/incidents")

    total = len(cases)

    root_cause_correct = 0
    precision_scores = []
    recall_scores = []
    reciprocal_rank_scores = []

    category_metrics = defaultdict(
        lambda: {
            "total": 0,
            "correct": 0,
            "precision": [],
            "recall": [],
            "mrr": [],
        }
    )

    failures = []

    for index, case in enumerate(cases, start=1):
        incident_id = case["incident_id"]
        query = case["query"]
        expected_root_cause = case["ground_truth_root_cause"]
        relevant_evidence = case["relevant_evidence"]
        category = case["ground_truth_root_cause"]

        print(
            f"[{index:02d}/{total}] "
            f"{incident_id} | {category}"
        )

        result = investigator.investigate(
            query=query,
            top_k=8,
            incident_id=incident_id,
        )

        predicted_root_cause = result["root_cause"]["root_cause"]

        precision, recall, reciprocal_rank = calculate_metrics(
            result["evidence"],
            relevant_evidence,
            top_k=5,
        )

        root_correct = (
            predicted_root_cause.strip().lower()
            == expected_root_cause.strip().lower()
        )

        if root_correct:
            root_cause_correct += 1

        precision_scores.append(precision)
        recall_scores.append(recall)
        reciprocal_rank_scores.append(reciprocal_rank)

        category_metrics[category]["total"] += 1
        category_metrics[category]["precision"].append(precision)
        category_metrics[category]["recall"].append(recall)
        category_metrics[category]["mrr"].append(reciprocal_rank)

        if root_correct:
            category_metrics[category]["correct"] += 1

        status = "PASS" if root_correct else "FAIL"

        print(
            f"      {status} | "
            f"Expected: {expected_root_cause} | "
            f"Predicted: {predicted_root_cause} | "
            f"P@5={precision:.3f} "
            f"R@5={recall:.3f} "
            f"RR={reciprocal_rank:.3f}"
        )

        if not root_correct:
            failures.append(
                {
                    "incident_id": incident_id,
                    "category": category,
                    "expected": expected_root_cause,
                    "predicted": predicted_root_cause,
                }
            )

    root_cause_accuracy = root_cause_correct / total

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

    mean_mrr = (
        sum(reciprocal_rank_scores) / len(reciprocal_rank_scores)
        if reciprocal_rank_scores
        else 0.0
    )

    print()
    print("=" * 80)
    print("OVERALL RESULTS")
    print("=" * 80)

    print(f"Test Cases          : {total}")
    print(f"Root Cause Accuracy : {root_cause_accuracy:.2%}")
    print(f"Mean Precision@5    : {mean_precision:.3f}")
    print(f"Mean Recall@5       : {mean_recall:.3f}")
    print(f"MRR                 : {mean_mrr:.3f}")

    print()
    print("=" * 80)
    print("RESULTS BY CATEGORY")
    print("=" * 80)

    for category in sorted(category_metrics):
        metrics = category_metrics[category]

        accuracy = metrics["correct"] / metrics["total"]

        precision = sum(metrics["precision"]) / len(
            metrics["precision"]
        )

        recall = sum(metrics["recall"]) / len(
            metrics["recall"]
        )

        mrr = sum(metrics["mrr"]) / len(
            metrics["mrr"]
        )

        print(
            f"{category:<30} "
            f"Accuracy={accuracy:.2%} "
            f"P@5={precision:.3f} "
            f"R@5={recall:.3f} "
            f"MRR={mrr:.3f}"
        )

    if failures:
        print()
        print("=" * 80)
        print("ROOT-CAUSE FAILURES")
        print("=" * 80)

        for failure in failures:
            print(
                f"{failure['incident_id']} | "
                f"{failure['category']} | "
                f"Expected={failure['expected']} | "
                f"Predicted={failure['predicted']}"
            )

    print()
    print("=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()