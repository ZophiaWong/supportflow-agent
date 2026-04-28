from __future__ import annotations

import sqlite3
from pathlib import Path
from os import environ

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "supportflow.sqlite3"


def get_database_path() -> Path:
    configured_path = environ.get("SUPPORTFLOW_DB_PATH")
    if configured_path:
        return Path(configured_path).expanduser().resolve()
    return DEFAULT_DB_PATH


def connect() -> sqlite3.Connection:
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    initialize_schema(connection)
    return connection


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS pending_reviews (
            thread_id TEXT PRIMARY KEY,
            ticket_id TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS run_events (
            event_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            ticket_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_run_events_thread_created
            ON run_events(thread_id, created_at, event_id);

        CREATE TABLE IF NOT EXISTS run_trace_events (
            trace_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            ticket_id TEXT NOT NULL,
            node_name TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT NOT NULL,
            status TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_run_trace_events_thread_started
            ON run_trace_events(thread_id, started_at, trace_id);

        CREATE TABLE IF NOT EXISTS support_actions (
            action_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            ticket_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            status TEXT NOT NULL,
            idempotency_key TEXT NOT NULL UNIQUE,
            requires_review INTEGER NOT NULL,
            reason TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_support_actions_thread_updated
            ON support_actions(thread_id, updated_at, action_id);

        CREATE TABLE IF NOT EXISTS langgraph_checkpoints (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL,
            checkpoint_id TEXT NOT NULL,
            checkpoint_type TEXT NOT NULL,
            checkpoint_blob BLOB NOT NULL,
            metadata_type TEXT NOT NULL,
            metadata_blob BLOB NOT NULL,
            parent_checkpoint_id TEXT,
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
        );

        CREATE TABLE IF NOT EXISTS langgraph_writes (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL,
            checkpoint_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            idx INTEGER NOT NULL,
            channel TEXT NOT NULL,
            value_type TEXT NOT NULL,
            value_blob BLOB NOT NULL,
            task_path TEXT NOT NULL DEFAULT '',
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
        );

        CREATE TABLE IF NOT EXISTS langgraph_blobs (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL,
            channel TEXT NOT NULL,
            version TEXT NOT NULL,
            value_type TEXT NOT NULL,
            value_blob BLOB NOT NULL,
            PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
        );
        """
    )
    connection.commit()


def clear_runtime_tables() -> None:
    with connect() as connection:
        connection.executescript(
            """
            DELETE FROM pending_reviews;
            DELETE FROM run_events;
            DELETE FROM run_trace_events;
            DELETE FROM support_actions;
            DELETE FROM langgraph_writes;
            DELETE FROM langgraph_blobs;
            DELETE FROM langgraph_checkpoints;
            """
        )
        connection.commit()
