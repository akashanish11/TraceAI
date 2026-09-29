import numpy as np


def cosine_similarity(
    vector_a,
    vector_b
) -> float:
    """
    Calculate cosine similarity between two vectors.
    """

    vector_a = np.asarray(vector_a).reshape(-1)
    vector_b = np.asarray(vector_b).reshape(-1)

    denominator = (
        np.linalg.norm(vector_a)
        * np.linalg.norm(vector_b)
    )

    if denominator == 0:
        return 0.0

    similarity = (
        np.dot(vector_a, vector_b)
        / denominator
    )

    return float(similarity)