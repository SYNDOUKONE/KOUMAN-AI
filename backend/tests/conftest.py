"""Fixtures : une application complète avec les stubs, sans GPU ni réseau."""

from __future__ import annotations

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        translator_backend="stub",
        llm_backend="stub",
        api_keys_db=tmp_path / "keys.sqlite3",
        enabled_languages=["dyu"],
        rate_limit_per_minute=1000,
        debug_allowed=True,
        history_max_turns=2,
    )


def make_client(settings: Settings):
    app = create_app(settings)
    client = TestClient(app)
    client.__enter__()  # déclenche le lifespan (chargement des composants)
    key = app.state.key_store.create("tests")
    return app, client, key


@pytest.fixture
def api(settings):
    app, client, key = make_client(settings)
    client.headers.update({"X-API-Key": key})
    yield app, client
    client.__exit__(None, None, None)


@pytest.fixture
def api_factory(settings):
    created = []

    def _factory(**overrides):
        app, client, key = make_client(replace(settings, **overrides))
        client.headers.update({"X-API-Key": key})
        created.append(client)
        return app, client

    yield _factory
    for c in created:
        c.__exit__(None, None, None)
