import os

from app.rag.chunker import DocumentChunker


class EvidenceNormalizer:
    """
    Converts logs, stack traces, and documentation
    into a common evidence format.

    Source paths are normalized to stable filenames
    so citations remain consistent across platforms.
    """

    def __init__(self):

        self.chunker = DocumentChunker(
            max_characters=500
        )

    @staticmethod
    def normalize_source_file(
        source_file: str
    ) -> str:
        """
        Convert an absolute or relative source path
        into a stable filename.

        Example:

        data\\incidents\\incident_001.log
        ->
        incident_001.log
        """

        if not source_file:
            return "unknown"

        normalized = source_file.replace(
            "\\",
            "/"
        )

        return os.path.basename(
            normalized
        )

    def normalize(
        self,
        incident: dict
    ) -> list[dict]:

        evidence = []

        # =====================================================
        # Logs
        # =====================================================

        for record in incident["logs"]:

            evidence.append(
                {
                    "text": record["message"],
                    "source_type": "log",
                    "provenance": "observed",
                    "source_file": (
                        self.normalize_source_file(
                            record["source_file"]
                        )
                    ),
                    "location": (
                        f"line "
                        f"{record['line_number']}"
                    ),
                    "metadata": {
                        "service": record["service"],
                        "level": record["level"],
                        "timestamp": record["timestamp"],
                    },
                }
            )

        # =====================================================
        # Stack trace
        # =====================================================

        stacktrace = incident["stacktrace"]

        if stacktrace:

            evidence.append(
                {
                    "text": (
                        f"{stacktrace['exception_type']}: "
                        f"{stacktrace['exception_message']}"
                    ),
                    "source_type": "stacktrace",
                    "provenance": "observed",
                    "source_file": (
                        self.normalize_source_file(
                            stacktrace["source_file"]
                        )
                    ),
                    "location": "exception",
                    "metadata": {
                        "service": (
                            stacktrace["metadata"]
                            .get("service")
                        ),
                        "operation": (
                            stacktrace["metadata"]
                            .get("operation")
                        ),
                        "order_id": (
                            stacktrace["metadata"]
                            .get("order_id")
                        ),
                    },
                }
            )

            for frame in stacktrace["frames"]:

                evidence.append(
                    {
                        "text": (
                            f"{frame['function']}() "
                            f"in {frame['file']}:"
                            f"{frame['line']} "
                            f"executed: "
                            f"{frame['code']}"
                        ),
                        "source_type": "stacktrace",
                        "provenance": "code",
                        "source_file": (
                            self.normalize_source_file(
                                stacktrace[
                                    "source_file"
                                ]
                            )
                        ),
                        "location": (
                            f"{frame['file']}:"
                            f"{frame['line']}"
                        ),
                        "metadata": {
                            "function": (
                                frame["function"]
                            ),
                            "code": frame["code"],
                        },
                    }
                )

        # =====================================================
        # Documentation
        # =====================================================

        documentation = incident[
            "documentation"
        ]

        if documentation:

            chunks = self.chunker.chunk(
                documentation["content"]
            )

            for index, chunk in enumerate(
                chunks,
                start=1
            ):

                evidence.append(
                    {
                        "text": chunk,
                        "source_type": "documentation",
                        "provenance": (
                            "documentation"
                        ),
                        "source_file": (
                            self.normalize_source_file(
                                documentation[
                                    "source_file"
                                ]
                            )
                        ),
                        "location": (
                            f"chunk {index}"
                        ),
                        "metadata": {
                            "chunk_index": index
                        },
                    }
                )

        return evidence