"""SQLite-backed immutable audit logger with hash chaining."""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4


AuditAction = Literal["SUBMITTED", "ALLOCATED", "EXECUTED", "COMPLETED", "FAILED"]
GENESIS_CHAIN_HASH = "0" * 64


class AuditLogger:
    """Appends tamper-evident audit events to a local SQLite database."""

    def __init__(self, db_path: str = "audit.db") -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    workflow_name TEXT NOT NULL,
                    target_node_id TEXT NULL,
                    chain_hash TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _get_last_chain_hash(self) -> str:
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT chain_hash
                FROM audit_events
                ORDER BY rowid DESC
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            return GENESIS_CHAIN_HASH
        return row[0]

    @staticmethod
    def _compute_chain_hash(
        previous_hash: str,
        event_id: str,
        timestamp: str,
        action: AuditAction,
        workflow_name: str,
        target_node_id: str | None,
    ) -> str:
        payload = "|".join(
            [
                previous_hash,
                event_id,
                timestamp,
                action,
                workflow_name,
                target_node_id or "",
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def append_event(
        self,
        action: AuditAction,
        workflow_name: str,
        target_node_id: str | None = None,
    ) -> str:
        """
        Append an immutable audit event and return the event_id.

        The event's chain_hash is SHA-256(previous_chain_hash + event_data).
        """
        event_id = str(uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        previous_hash = self._get_last_chain_hash()
        chain_hash = self._compute_chain_hash(
            previous_hash=previous_hash,
            event_id=event_id,
            timestamp=timestamp,
            action=action,
            workflow_name=workflow_name,
            target_node_id=target_node_id,
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_events (
                    event_id,
                    timestamp,
                    action,
                    workflow_name,
                    target_node_id,
                    chain_hash
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, timestamp, action, workflow_name, target_node_id, chain_hash),
            )
            conn.commit()

        return event_id
