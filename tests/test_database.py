from typing import TYPE_CHECKING

from fastapi import FastAPI
from starlette.requests import Request

from app import database

if TYPE_CHECKING:
    import pytest


class _FakeEngine:
    disposed = False

    async def dispose(self) -> None:
        self.disposed = True


def test_get_engine_reads_engine_from_app_state() -> None:
    app = FastAPI()
    fake_engine = _FakeEngine()
    app.state.engine = fake_engine
    request = Request({"type": "http", "app": app})

    assert database.get_engine(request) is fake_engine


async def test_lifespan_sets_engine_initializes_and_disposes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    fake_engine = _FakeEngine()
    initialized = False

    def _create_engine() -> _FakeEngine:
        return fake_engine

    async def _initialize_engine(engine: _FakeEngine) -> None:
        nonlocal initialized
        initialized = True
        assert engine is fake_engine

    monkeypatch.setattr(database, "create_engine", _create_engine)
    monkeypatch.setattr(database, "initialize_engine", _initialize_engine)

    async with database.lifespan(app):
        assert initialized
        assert app.state.engine is fake_engine
        assert not fake_engine.disposed

    assert fake_engine.disposed


def test_database_module_has_no_import_time_engine() -> None:
    assert not hasattr(database, "_async_engine")
    assert not hasattr(database, "_async_sessionmaker")
    assert not hasattr(database, "_get_async_session")
