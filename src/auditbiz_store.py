from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "var" / "auditbizia" / "auditbizia.sqlite3"


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class AuditBizStore:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS audit_sessions (
                    id TEXT PRIMARY KEY,
                    sector_id TEXT NOT NULL,
                    current_step TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS audit_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES audit_sessions(id)
                );
                CREATE TABLE IF NOT EXISTS audit_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    field TEXT NOT NULL,
                    value TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    validated INTEGER NOT NULL DEFAULT 0,
                    step TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES audit_sessions(id)
                );
                CREATE TABLE IF NOT EXISTS audit_hypotheses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    hypothesis TEXT NOT NULL,
                    basis_json TEXT NOT NULL DEFAULT '[]',
                    confidence REAL NOT NULL,
                    requires_validation INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES audit_sessions(id)
                );
                CREATE TABLE IF NOT EXISTS audit_questions_asked (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    step TEXT NOT NULL,
                    question TEXT NOT NULL,
                    outcome TEXT NOT NULL DEFAULT 'asked',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES audit_sessions(id)
                );
                CREATE TABLE IF NOT EXISTS audit_question_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES audit_sessions(id)
                );
                """
            )

    def create_session(self, *, sector_id: str = "generic_tpe", current_step: str = "conversation_preferences", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        sid = f"auditbiz-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:8]}"
        now = utc_now()
        metadata = metadata or {}
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO audit_sessions(id, sector_id, current_step, status, created_at, updated_at, metadata_json) VALUES (?, ?, ?, 'active', ?, ?, ?)",
                (sid, sector_id, current_step, now, now, json.dumps(metadata, ensure_ascii=False)),
            )
        return self.get_session(sid)  # type: ignore[return-value]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM audit_sessions WHERE id = ?", (session_id,)).fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "sector_id": row["sector_id"],
                "current_step": row["current_step"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
                "messages": [dict(r) for r in conn.execute("SELECT role, text, created_at FROM audit_messages WHERE session_id = ? ORDER BY id", (session_id,))],
                "facts": [self._fact_row(r) for r in conn.execute("SELECT * FROM audit_facts WHERE session_id = ? ORDER BY id", (session_id,))],
                "hypotheses": [self._hypothesis_row(r) for r in conn.execute("SELECT * FROM audit_hypotheses WHERE session_id = ? ORDER BY id", (session_id,))],
                "questions_asked": [self._question_row(r) for r in conn.execute("SELECT * FROM audit_questions_asked WHERE session_id = ? ORDER BY id", (session_id,))],
                "feedback": [dict(r) for r in conn.execute("SELECT question_id, signal, details, created_at FROM audit_question_feedback WHERE session_id = ? ORDER BY id", (session_id,))],
            }

    def add_message(self, session_id: str, *, role: str, text: str) -> None:
        if role not in {"client", "omar", "system"}:
            raise ValueError("invalid message role")
        text = str(text or "").strip()
        if not text:
            raise ValueError("message text required")
        now = utc_now()
        with self.connect() as conn:
            conn.execute("INSERT INTO audit_messages(session_id, role, text, created_at) VALUES (?, ?, ?, ?)", (session_id, role, text, now))
            conn.execute("UPDATE audit_sessions SET updated_at = ? WHERE id = ?", (now, session_id))

    def add_fact(self, session_id: str, *, field: str, value: str, source: str, confidence: float, step: str, validated: bool = False) -> int:
        if not 0 <= float(confidence) <= 1:
            raise ValueError("confidence must be between 0 and 1")
        now = utc_now()
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO audit_facts(session_id, field, value, source, confidence, validated, step, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, field, value, source, float(confidence), 1 if validated else 0, step, now),
            )
            conn.execute("UPDATE audit_sessions SET updated_at = ? WHERE id = ?", (now, session_id))
            if cur.lastrowid is None:
                raise RuntimeError("sqlite insert did not return lastrowid")
            return int(cur.lastrowid)

    def add_hypothesis(self, session_id: str, *, hypothesis: str, basis: list[str] | None = None, confidence: float = 0.5, requires_validation: bool = True) -> int:
        if not 0 <= float(confidence) <= 1:
            raise ValueError("confidence must be between 0 and 1")
        now = utc_now()
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO audit_hypotheses(session_id, hypothesis, basis_json, confidence, requires_validation, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, hypothesis, json.dumps(basis or [], ensure_ascii=False), float(confidence), 1 if requires_validation else 0, now),
            )
            conn.execute("UPDATE audit_sessions SET updated_at = ? WHERE id = ?", (now, session_id))
            if cur.lastrowid is None:
                raise RuntimeError("sqlite insert did not return lastrowid")
            return int(cur.lastrowid)

    def record_question(self, session_id: str, *, question_id: str, step: str, question: str, outcome: str = "asked", metadata: dict[str, Any] | None = None) -> int:
        now = utc_now()
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO audit_questions_asked(session_id, question_id, step, question, outcome, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, question_id, step, question, outcome, json.dumps(metadata or {}, ensure_ascii=False), now),
            )
            conn.execute("UPDATE audit_sessions SET updated_at = ? WHERE id = ?", (now, session_id))
            if cur.lastrowid is None:
                raise RuntimeError("sqlite insert did not return lastrowid")
            return int(cur.lastrowid)

    def record_feedback(self, session_id: str, *, question_id: str, signal: str, details: str = "") -> int:
        allowed = {"answered", "skipped", "unclear", "too_deep", "useful", "why_requested", "corrected"}
        if signal not in allowed:
            raise ValueError(f"invalid feedback signal: {signal}")
        now = utc_now()
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO audit_question_feedback(session_id, question_id, signal, details, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, question_id, signal, details, now),
            )
            conn.execute("UPDATE audit_sessions SET updated_at = ? WHERE id = ?", (now, session_id))
            if cur.lastrowid is None:
                raise RuntimeError("sqlite insert did not return lastrowid")
            return int(cur.lastrowid)

    def set_step(self, session_id: str, step: str) -> None:
        now = utc_now()
        with self.connect() as conn:
            conn.execute("UPDATE audit_sessions SET current_step = ?, updated_at = ? WHERE id = ?", (step, now, session_id))

    @staticmethod
    def _fact_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "field": row["field"],
            "value": row["value"],
            "source": row["source"],
            "confidence": row["confidence"],
            "validated": bool(row["validated"]),
            "step": row["step"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _hypothesis_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "hypothesis": row["hypothesis"],
            "basis": json.loads(row["basis_json"] or "[]"),
            "confidence": row["confidence"],
            "requires_validation": bool(row["requires_validation"]),
            "created_at": row["created_at"],
        }

    @staticmethod
    def _question_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "question_id": row["question_id"],
            "step": row["step"],
            "question": row["question"],
            "outcome": row["outcome"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
            "created_at": row["created_at"],
        }
