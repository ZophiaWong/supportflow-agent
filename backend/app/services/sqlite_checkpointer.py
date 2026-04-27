from __future__ import annotations

import random
from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    WRITES_IDX_MAP,
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    SerializerProtocol,
    get_checkpoint_id,
    get_checkpoint_metadata,
)

from app.services.sqlite_store import connect


class SqliteSaver(BaseCheckpointSaver[str]):
    """Small SQLite LangGraph checkpointer for local durable demo runs."""

    def __init__(self, *, serde: SerializerProtocol | None = None) -> None:
        super().__init__(serde=serde)

    def _load_blobs(
        self, thread_id: str, checkpoint_ns: str, versions: ChannelVersions
    ) -> dict[str, Any]:
        channel_values: dict[str, Any] = {}
        with connect() as connection:
            for channel, version in versions.items():
                row = connection.execute(
                    """
                    SELECT value_type, value_blob
                    FROM langgraph_blobs
                    WHERE thread_id = ?
                      AND checkpoint_ns = ?
                      AND channel = ?
                      AND version = ?
                    """,
                    (thread_id, checkpoint_ns, channel, str(version)),
                ).fetchone()
                if row is None or row["value_type"] == "empty":
                    continue
                channel_values[channel] = self.serde.loads_typed(
                    (row["value_type"], bytes(row["value_blob"]))
                )
        return channel_values

    def _checkpoint_tuple_from_row(self, row: Any, config: RunnableConfig) -> CheckpointTuple:
        thread_id = row["thread_id"]
        checkpoint_ns = row["checkpoint_ns"]
        checkpoint_id = row["checkpoint_id"]
        checkpoint: Checkpoint = self.serde.loads_typed(
            (row["checkpoint_type"], bytes(row["checkpoint_blob"]))
        )
        metadata = self.serde.loads_typed(
            (row["metadata_type"], bytes(row["metadata_blob"]))
        )

        with connect() as connection:
            writes = connection.execute(
                """
                SELECT task_id, channel, value_type, value_blob
                FROM langgraph_writes
                WHERE thread_id = ?
                  AND checkpoint_ns = ?
                  AND checkpoint_id = ?
                ORDER BY task_id, idx
                """,
                (thread_id, checkpoint_ns, checkpoint_id),
            ).fetchall()

        return CheckpointTuple(
            config=config,
            checkpoint={
                **checkpoint,
                "channel_values": self._load_blobs(
                    thread_id, checkpoint_ns, checkpoint["channel_versions"]
                ),
            },
            metadata=metadata,
            pending_writes=[
                (
                    write["task_id"],
                    write["channel"],
                    self.serde.loads_typed(
                        (write["value_type"], bytes(write["value_blob"]))
                    ),
                )
                for write in writes
            ],
            parent_config=(
                {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": row["parent_checkpoint_id"],
                    }
                }
                if row["parent_checkpoint_id"]
                else None
            ),
        )

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        thread_id: str = config["configurable"]["thread_id"]
        checkpoint_ns: str = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = get_checkpoint_id(config)

        with connect() as connection:
            if checkpoint_id:
                row = connection.execute(
                    """
                    SELECT *
                    FROM langgraph_checkpoints
                    WHERE thread_id = ?
                      AND checkpoint_ns = ?
                      AND checkpoint_id = ?
                    """,
                    (thread_id, checkpoint_ns, checkpoint_id),
                ).fetchone()
                if row is None:
                    return None
                return self._checkpoint_tuple_from_row(row, config)

            row = connection.execute(
                """
                SELECT *
                FROM langgraph_checkpoints
                WHERE thread_id = ?
                  AND checkpoint_ns = ?
                ORDER BY checkpoint_id DESC
                LIMIT 1
                """,
                (thread_id, checkpoint_ns),
            ).fetchone()

        if row is None:
            return None

        return self._checkpoint_tuple_from_row(
            row,
            {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": row["checkpoint_id"],
                }
            },
        )

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        params: list[Any] = []
        clauses: list[str] = []

        if config:
            clauses.append("thread_id = ?")
            params.append(config["configurable"]["thread_id"])
            if "checkpoint_ns" in config["configurable"]:
                clauses.append("checkpoint_ns = ?")
                params.append(config["configurable"].get("checkpoint_ns", ""))
            if checkpoint_id := get_checkpoint_id(config):
                clauses.append("checkpoint_id = ?")
                params.append(checkpoint_id)

        if before and (before_checkpoint_id := get_checkpoint_id(before)):
            clauses.append("checkpoint_id < ?")
            params.append(before_checkpoint_id)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        limit_sql = "LIMIT ?" if limit is not None else ""
        if limit is not None:
            params.append(limit)

        with connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM langgraph_checkpoints
                {where_sql}
                ORDER BY checkpoint_id DESC
                {limit_sql}
                """,
                params,
            ).fetchall()

        for row in rows:
            metadata = self.serde.loads_typed(
                (row["metadata_type"], bytes(row["metadata_blob"]))
            )
            if filter and not all(
                query_value == metadata.get(query_key)
                for query_key, query_value in filter.items()
            ):
                continue
            yield self._checkpoint_tuple_from_row(
                row,
                {
                    "configurable": {
                        "thread_id": row["thread_id"],
                        "checkpoint_ns": row["checkpoint_ns"],
                        "checkpoint_id": row["checkpoint_id"],
                    }
                },
            )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        checkpoint_copy = checkpoint.copy()
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        values: dict[str, Any] = checkpoint_copy.pop("channel_values")  # type: ignore[misc]

        with connect() as connection:
            for channel, version in new_versions.items():
                value_type, value_blob = (
                    self.serde.dumps_typed(values[channel])
                    if channel in values
                    else ("empty", b"")
                )
                connection.execute(
                    """
                    INSERT OR REPLACE INTO langgraph_blobs (
                        thread_id, checkpoint_ns, channel, version, value_type, value_blob
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        thread_id,
                        checkpoint_ns,
                        channel,
                        str(version),
                        value_type,
                        value_blob,
                    ),
                )

            checkpoint_type, checkpoint_blob = self.serde.dumps_typed(checkpoint_copy)
            metadata_type, metadata_blob = self.serde.dumps_typed(
                get_checkpoint_metadata(config, metadata)
            )
            connection.execute(
                """
                INSERT OR REPLACE INTO langgraph_checkpoints (
                    thread_id,
                    checkpoint_ns,
                    checkpoint_id,
                    checkpoint_type,
                    checkpoint_blob,
                    metadata_type,
                    metadata_blob,
                    parent_checkpoint_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    checkpoint_ns,
                    checkpoint["id"],
                    checkpoint_type,
                    checkpoint_blob,
                    metadata_type,
                    metadata_blob,
                    config["configurable"].get("checkpoint_id"),
                ),
            )
            connection.commit()

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"]["checkpoint_id"]

        with connect() as connection:
            for idx, (channel, value) in enumerate(writes):
                write_idx = WRITES_IDX_MAP.get(channel, idx)
                if write_idx >= 0:
                    existing = connection.execute(
                        """
                        SELECT 1
                        FROM langgraph_writes
                        WHERE thread_id = ?
                          AND checkpoint_ns = ?
                          AND checkpoint_id = ?
                          AND task_id = ?
                          AND idx = ?
                        """,
                        (thread_id, checkpoint_ns, checkpoint_id, task_id, write_idx),
                    ).fetchone()
                    if existing is not None:
                        continue

                value_type, value_blob = self.serde.dumps_typed(value)
                connection.execute(
                    """
                    INSERT OR REPLACE INTO langgraph_writes (
                        thread_id,
                        checkpoint_ns,
                        checkpoint_id,
                        task_id,
                        idx,
                        channel,
                        value_type,
                        value_blob,
                        task_path
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        thread_id,
                        checkpoint_ns,
                        checkpoint_id,
                        task_id,
                        write_idx,
                        channel,
                        value_type,
                        value_blob,
                        task_path,
                    ),
                )
            connection.commit()

    def delete_thread(self, thread_id: str) -> None:
        with connect() as connection:
            connection.execute("DELETE FROM langgraph_writes WHERE thread_id = ?", (thread_id,))
            connection.execute("DELETE FROM langgraph_blobs WHERE thread_id = ?", (thread_id,))
            connection.execute(
                "DELETE FROM langgraph_checkpoints WHERE thread_id = ?", (thread_id,)
            )
            connection.commit()

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        return self.get_tuple(config)

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return self.put(config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        return self.put_writes(config, writes, task_id, task_path)

    async def adelete_thread(self, thread_id: str) -> None:
        return self.delete_thread(thread_id)

    def get_next_version(self, current: str | None, channel: None) -> str:
        if current is None:
            current_v = 0
        elif isinstance(current, int):
            current_v = current
        else:
            current_v = int(str(current).split(".")[0])
        next_v = current_v + 1
        next_h = random.random()
        return f"{next_v:032}.{next_h:016}"
