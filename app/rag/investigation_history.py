import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class InvestigationHistory:
    """
    SQLite-backed persistence layer for TraceAI investigations.

    This class is intentionally independent from IncidentInvestigator.
    It stores completed investigation results and provides basic
    CRUD operations for investigation history.
    """

    def __init__(self, db_path: str | Path = "data/traceai.db"):
        self.db_path = Path(db_path)

        # Create parent directory when using a normal project path.
        if self.db_path.parent:
            self.db_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self.connection = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
        )

        self.connection.row_factory = sqlite3.Row

        self._create_tables()

    # ------------------------------------------------------------------
    # Database initialization
    # ------------------------------------------------------------------

    def _create_tables(self) -> None:
        """Create the investigation history table if it does not exist."""

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS investigations (
                investigation_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                query TEXT NOT NULL,
                root_cause TEXT,
                confidence TEXT,
                confidence_score REAL,
                analysis TEXT,
                groundedness_score REAL,
                citation_coverage REAL,
                claim_coverage REAL,
                created_at TEXT NOT NULL
            )
            """
        )

        self.connection.commit()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save_investigation(
        self,
        investigation: Dict[str, Any],
    ) -> bool:
        """
        Save an investigation.

        Returns:
            True when the investigation is successfully stored.
        """

        investigation_id = investigation.get(
            "investigation_id"
        )

        incident_id = investigation.get(
            "incident_id"
        )

        query = investigation.get(
            "query"
        )

        if not investigation_id:
            raise ValueError(
                "investigation_id is required"
            )

        if not incident_id:
            raise ValueError(
                "incident_id is required"
            )

        if not query:
            raise ValueError(
                "query is required"
            )

        created_at = investigation.get(
            "created_at"
        )

        if not created_at:
            created_at = datetime.now(
                timezone.utc
            ).isoformat()

        self.connection.execute(
            """
            INSERT OR REPLACE INTO investigations (
                investigation_id,
                incident_id,
                query,
                root_cause,
                confidence,
                confidence_score,
                analysis,
                groundedness_score,
                citation_coverage,
                claim_coverage,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                investigation_id,
                incident_id,
                query,
                investigation.get(
                    "root_cause"
                ),
                investigation.get(
                    "confidence"
                ),
                investigation.get(
                    "confidence_score"
                ),
                investigation.get(
                    "analysis"
                ),
                investigation.get(
                    "groundedness_score"
                ),
                investigation.get(
                    "citation_coverage"
                ),
                investigation.get(
                    "claim_coverage"
                ),
                created_at,
            ),
        )

        self.connection.commit()

        return True

    # ------------------------------------------------------------------
    # Get one
    # ------------------------------------------------------------------

    def get_investigation(
        self,
        investigation_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a single investigation by ID."""

        cursor = self.connection.execute(
            """
            SELECT *
            FROM investigations
            WHERE investigation_id = ?
            """,
            (investigation_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def list_investigations(
        self,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return investigations ordered from newest to oldest.

        Args:
            limit:
                Optional maximum number of investigations.
        """

        if limit is not None:
            cursor = self.connection.execute(
                """
                SELECT *
                FROM investigations
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT *
                FROM investigations
                ORDER BY created_at DESC
                """
            )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_investigation(
        self,
        investigation_id: str,
    ) -> bool:
        """Delete an investigation by ID."""

        cursor = self.connection.execute(
            """
            DELETE FROM investigations
            WHERE investigation_id = ?
            """,
            (investigation_id,),
        )

        self.connection.commit()

        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Count
    # ------------------------------------------------------------------

    def count(self) -> int:
        """Return the total number of stored investigations."""

        cursor = self.connection.execute(
            """
            SELECT COUNT(*)
            FROM investigations
            """
        )

        return cursor.fetchone()[0]

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the SQLite connection."""

        if self.connection:
            self.connection.close()

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.close()