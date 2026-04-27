from collections.abc import Generator

import pytest

from app.graph.builder import get_support_graph
from app.services.sqlite_store import clear_runtime_tables


@pytest.fixture(autouse=True)
def isolated_runtime_database(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> Generator[None, None, None]:
    monkeypatch.setenv("SUPPORTFLOW_DB_PATH", str(tmp_path / "supportflow.sqlite3"))
    get_support_graph.cache_clear()
    clear_runtime_tables()
    yield
    get_support_graph.cache_clear()
    clear_runtime_tables()
