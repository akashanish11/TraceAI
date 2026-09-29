from pathlib import Path
import re


LOG_PATTERN = re.compile(
    r"(?P<timestamp>\S+\s+\S+)\s+"
    r"(?P<level>INFO|WARN|ERROR|DEBUG)\s+"
    r"(?P<service>\S+)\s+-\s+"
    r"(?P<message>.*)"
)


def parse_log_file(file_path: str) -> list[dict]:
    """
    Parse a log file into structured log records.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {file_path}")

    records = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):

            line = line.strip()

            if not line:
                continue

            match = LOG_PATTERN.match(line)

            if match:
                record = match.groupdict()
                record["line_number"] = line_number
                record["source_file"] = path.name

                records.append(record)

            else:
                records.append({
                    "timestamp": None,
                    "level": "UNKNOWN",
                    "service": None,
                    "message": line,
                    "line_number": line_number,
                    "source_file": path.name
                })

    return records