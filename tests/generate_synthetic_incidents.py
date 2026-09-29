import json
import random
from pathlib import Path


DATASET_PATH = Path(
    "data/evaluation/expanded_evaluation_dataset.json"
)

OUTPUT_DIR = Path("data/incidents")


random.seed(42)


def build_log(case: dict) -> str:
    metadata = case["metadata"]

    service = metadata["service"]
    request_id = metadata["request_id"]
    signal = metadata["log_signal"]

    return f"""2026-09-27 10:00:01 INFO  {service} - Request received for {request_id}
2026-09-27 10:00:02 INFO  {service} - Processing request
2026-09-27 10:00:03 INFO  {service} - Executing {metadata["operation"]}
2026-09-27 10:00:04 ERROR {service} - {signal}
2026-09-27 10:00:05 ERROR {service} - Request processing failed for {request_id}
2026-09-27 10:00:06 WARN  {service} - Returning failure response
"""


def build_stacktrace(case: dict) -> str:
    metadata = case["metadata"]

    service = metadata["service"]
    exception = metadata["exception"]
    message = metadata["exception_message"]
    file_name = metadata["file"]
    function = metadata["function"]
    line_number = metadata["line"]
    operation = metadata["operation"]
    user_id = metadata["user_id"]
    request_id = metadata["request_id"]

    if (
        exception.startswith("java.")
        or file_name.endswith(".java")
    ):
        return f"""Exception in thread "main" {exception}: {message}
    at com.example.{service.lower()}.{function}({file_name}:{line_number})
    at com.example.{service.lower()}.{service}Service.java:{line_number + 40}

Service: {service}
Operation: {operation}
User ID: {user_id}
Request ID: {request_id}
"""

    return f"""Traceback (most recent call last):
  File "services/{service.lower()}.py", line {line_number}, in {function}
    result = dependency_client.execute()
  File "{file_name}", line {line_number + 5}, in {function}
    raise {exception}("{message}")
{exception}: {message}

Service: {service}
Operation: {operation}
User ID: {user_id}
Request ID: {request_id}
"""


def build_documentation(case: dict) -> str:
    metadata = case["metadata"]

    service = metadata["service"]
    root_cause = case["ground_truth_root_cause"]
    signal = metadata["log_signal"]
    operation = metadata["operation"]

    return f"""# {service} Incident

## System Overview

The {service} processes application requests
through the {operation} operation.

## Failure Behavior

During the incident, the service encountered
a condition associated with:

{signal}

The failure prevented the requested operation
from completing normally.

## Diagnostic Signal

The expected diagnostic signal for this incident is:

- {signal}
- {metadata["exception"]}
- {metadata["exception_message"]}

## Relevant Component

- {service}
- {operation}
- {metadata["function"]}()

## Incident Category

{root_cause}
"""


def main():
    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        dataset = json.load(file)

    cases = dataset["cases"]

    generated = 0

    for case in cases:
        incident_id = case["incident_id"]

        incident_dir = OUTPUT_DIR / incident_id
        incident_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        log_content = build_log(case)
        stacktrace_content = build_stacktrace(case)
        documentation_content = build_documentation(case)

        with open(
            incident_dir / "incident.log",
            "w",
            encoding="utf-8",
        ) as file:
            file.write(log_content)

        with open(
            incident_dir / "incident.stacktrace",
            "w",
            encoding="utf-8",
        ) as file:
            file.write(stacktrace_content)

        with open(
            incident_dir / "incident.md",
            "w",
            encoding="utf-8",
        ) as file:
            file.write(documentation_content)

        generated += 1

    print("=" * 70)
    print("TRACEAI — SYNTHETIC INCIDENT GENERATION")
    print("=" * 70)

    print(f"Generated incidents : {generated}")
    print(f"Output directory    : {OUTPUT_DIR}")

    print("\nEach incident contains:")
    print("- incident.log")
    print("- incident.stacktrace")
    print("- incident.md")

    print("\nExisting incidents were preserved.")
    print("=" * 70)


if __name__ == "__main__":
    main()