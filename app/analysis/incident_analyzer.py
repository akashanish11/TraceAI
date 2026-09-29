from collections import Counter
from typing import Any


def analyze_incident(records: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze structured log records and generate
    a basic incident summary.
    """

    if not records:
        return {
            "total_events": 0,
            "error_count": 0,
            "warning_count": 0,
            "affected_services": [],
            "error_messages": [],
            "severity": "UNKNOWN",
        }

    # Count log levels
    level_counts = Counter(
        record.get("level", "UNKNOWN")
        for record in records
    )

    # Count services
    service_counts = Counter(
        record.get("service")
        for record in records
        if record.get("service")
    )

    # Extract errors
    errors = [
        record
        for record in records
        if record.get("level") == "ERROR"
    ]

    # Extract warnings
    warnings = [
        record
        for record in records
        if record.get("level") == "WARN"
    ]

    # Determine severity
    error_count = len(errors)

    if error_count >= 5:
        severity = "CRITICAL"
    elif error_count >= 3:
        severity = "HIGH"
    elif error_count >= 1:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    # Get unique affected services
    affected_services = list(service_counts.keys())

    # Extract error messages
    error_messages = [
        {
            "service": error["service"],
            "message": error["message"],
            "line_number": error["line_number"],
            "source_file": error["source_file"],
        }
        for error in errors
    ]

    return {
        "total_events": len(records),
        "error_count": error_count,
        "warning_count": len(warnings),
        "level_counts": dict(level_counts),
        "affected_services": affected_services,
        "service_counts": dict(service_counts),
        "error_messages": error_messages,
        "severity": severity,
    }