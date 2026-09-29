from pathlib import Path

from app.parsers.log_parser import parse_log_file
from app.parsers.stacktrace_parser import parse_stacktrace


class MultiSourceLoader:
    """
    Loads evidence from one or multiple incident directories.

    Supported structures:

    Multi-incident:
        data/incidents/
            incident_001/
                incident.log
                incident.stacktrace
                incident.md

            incident_002/
                incident.log
                incident.stacktrace
                incident.md

    Legacy flat structure:
        data/incidents/
            incident_001.log
            incident_001.stacktrace
            incident_001.md

    Both structures can coexist.
    """

    def __init__(self, incident_directory: str):
        self.incident_directory = Path(incident_directory)

    def _load_directory(self, directory: Path) -> dict:
        result = {
            "incident_id": directory.name,
            "logs": [],
            "stacktrace": None,
            "documentation": None,
        }

        log_files = sorted(directory.glob("*.log"))

        for log_file in log_files:
            records = parse_log_file(str(log_file))
            result["logs"].extend(records)

        stacktrace_files = sorted(
            directory.glob("*.stacktrace")
        )

        if stacktrace_files:
            result["stacktrace"] = parse_stacktrace(
                str(stacktrace_files[0])
            )

        documentation_files = sorted(
            directory.glob("*.md")
        )

        if documentation_files:
            documentation_file = documentation_files[0]

            with open(
                documentation_file,
                "r",
                encoding="utf-8"
            ) as file:
                documentation = file.read()

            result["documentation"] = {
                "source_file": str(documentation_file),
                "content": documentation,
            }

        return result

    def _has_evidence(self, incident: dict) -> bool:
        return (
            bool(incident["logs"])
            or incident["stacktrace"] is not None
            or incident["documentation"] is not None
        )

    def _load_legacy_flat_incident(self) -> dict | None:
        """
        Load the original flat incident structure if it exists.
        """

        if not self.incident_directory.exists():
            return None

        log_files = sorted(
            self.incident_directory.glob("*.log")
        )

        stacktrace_files = sorted(
            self.incident_directory.glob("*.stacktrace")
        )

        documentation_files = sorted(
            self.incident_directory.glob("*.md")
        )

        if not (
            log_files
            or stacktrace_files
            or documentation_files
        ):
            return None

        result = {
            "incident_id": "legacy_incident",
            "logs": [],
            "stacktrace": None,
            "documentation": None,
        }

        for log_file in log_files:
            records = parse_log_file(str(log_file))
            result["logs"].extend(records)

        if stacktrace_files:
            result["stacktrace"] = parse_stacktrace(
                str(stacktrace_files[0])
            )

        if documentation_files:
            documentation_file = documentation_files[0]

            with open(
                documentation_file,
                "r",
                encoding="utf-8"
            ) as file:
                documentation = file.read()

            result["documentation"] = {
                "source_file": str(documentation_file),
                "content": documentation,
            }

        if self._has_evidence(result):
            return result

        return None

    def load_incidents(self) -> list[dict]:
        """
        Load ALL available incidents.

        Supports both legacy flat incidents and
        directory-based incidents simultaneously.
        """

        incidents = []

        if not self.incident_directory.exists():
            return incidents

        # --------------------------------------------------
        # 1. Load legacy flat incident if present
        # --------------------------------------------------

        legacy_incident = self._load_legacy_flat_incident()

        if legacy_incident:
            incidents.append(legacy_incident)

        # --------------------------------------------------
        # 2. Load directory-based incidents
        # --------------------------------------------------

        subdirectories = sorted(
            directory
            for directory in self.incident_directory.iterdir()
            if directory.is_dir()
        )

        for directory in subdirectories:
            incident = self._load_directory(directory)

            if self._has_evidence(incident):
                incidents.append(incident)

        return incidents

    def load_incident(self) -> dict:
        """
        Backward-compatible method.

        Returns the first available incident.
        """

        incidents = self.load_incidents()

        if not incidents:
            return {
                "incident_id": None,
                "logs": [],
                "stacktrace": None,
                "documentation": None,
            }

        return incidents[0]