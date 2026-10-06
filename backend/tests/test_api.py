"""Tests des points d'accès, avec les stubs."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.services.llm import StubLLM


# ----------------------------------------------------------------- service
def test_health_is_public_and_reports_components(api):
    _, client = api
    client.headers.pop("X-API-Key")
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["translator"]["name"] == "stub"
    assert body["llm"] == "stub"


def test_languages_lists_enabled_flags(api):
    _, client = api
    langs = {item["code"]: item["enabled"] for item in client.get("/api/v1/languages").json()}
    assert langs == {"dyu": True, "bam": False}


def test_request_id_is_returned(api):
    _, client = api
    r = client.get("/health", headers={"X-Request-ID": "abc-123"})
    assert r.headers["X-Request-ID"] == "abc-123"


# ----------------------------------------------------------------- auth
def test_missing_key_gives_401_with_uniform_error(api):
    _, client = api
    client.headers.pop("X-API-Key")
    r = client.post("/api/v1/translate", json={"text": "Bonjour", "src": "fr", "tgt": "dyu"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "cle_invalide"


def test_revoked_key_gives_401(api):
    app, client = api
    app.state.key_store.revoke("tests")
    r = client.post("/api/v1/translate", json={"text": "Bonjour", "src": "fr", "tgt": "dyu"})
    assert r.status_code == 401


def test_rate_limit_gives_429(api_factory):
    _, client = api_factory(rate_limit_per_minute=2)
    payload = {"text": "Bonjour", "src": "fr", "tgt": "dyu"}
    codes = [client.post("/api/v1/translate", json=payload).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


# ----------------------------------------------------------------- translate
def test_translate_both_directions(api):
    _, client = api
    r = client.post("/api/v1/translate", json={"text": "Bonjour", "src": "fr", "tgt": "dyu"})
    assert r.status_code == 200
    assert r.json()["translation"] == "[stub fr→dyu] Bonjour"
    r = client.post("/api/v1/translate", json={"text": "I ni ce", "src": "dyu", "tgt": "fr"})
    assert r.json()["translation"] == "[stub dyu→fr] I ni ce"


def test_translate_rejects_disabled_and_unknown_languages(api):
    _, client = api
    r = client.post("/api/v1/translate", json={"text": "x", "src": "fr", "tgt": "bam"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "langue_desactivee"
    r = client.post("/api/v1/translate", json={"text": "x", "src": "fr", "tgt": "xx"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "langue_inconnue"


def test_translate_rejects_non_pivot_direction(api):
    _, client = api
    r = client.post("/api/v1/translate", json={"text": "x", "src": "fr", "tgt": "fr"})
    assert r.json()["error"]["code"] == "sens_invalide"


def test_validation_error_is_uniform(api):
    _, client = api
    r = client.post("/api/v1/translate", json={"src": "fr", "tgt": "dyu"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "requete_invalide"


def test_message_too_long(api_factory):
    _, client = api_factory(max_message_chars=10)
    r = client.post("/api/v1/translate", json={"text": "x" * 11, "src": "fr", "tgt": "dyu"})
    assert r.json()["error"]["code"] == "message_trop_long"


# ----------------------------------------------------------------- chat
def test_chat_pipeline_and_debug(api):
    _, client = api
    r = client.post(
        "/api/v1/chat?debug=true",
        json={"session_id": "s1", "lang": "dyu", "message": "I ni ce"},
    )
    body = r.json()
    assert r.status_code == 200
    dbg = body["debug"]
    assert dbg["fr_input"] == "[stub dyu→fr] I ni ce"
    assert dbg["fr_reply"].startswith("Réponse de test.")
    assert body["reply"] == f"[stub fr→dyu] {dbg['fr_reply']}"
    assert set(dbg["timings_ms"]) == {"mt_in", "llm", "mt_out"}


def test_debug_hidden_when_not_allowed(api_factory):
    _, client = api_factory(debug_allowed=False)
    r = client.post(
        "/api/v1/chat?debug=true", json={"session_id": "s", "lang": "dyu", "message": "I ni ce"}
    )
    assert "debug" not in r.json()


def test_history_is_french_and_truncated(api):
    app, client = api
    for i in range(3):
        client.post("/api/v1/chat", json={"session_id": "h", "lang": "dyu", "message": f"m{i}"})
    session = app.state.sessions.get("tests:h", "dyu")
    # history_max_turns=2 -> 4 messages, tous en français (sortie du traducteur vers fr)
    assert len(session.history_fr) == 4
    assert session.history_fr[0]["content"] == "[stub dyu→fr] m1"
    assert all("→dyu" not in m["content"] for m in session.history_fr)


def test_llm_receives_history(api):
    app, client = api
    seen = []

    class SpyLLM(StubLLM):
        def reply(self, history_fr, system_prompt):
            seen.append(list(history_fr))
            return super().reply(history_fr, system_prompt)

    app.state.orchestrator.llm = SpyLLM()
    for msg in ("a", "b"):
        client.post("/api/v1/chat", json={"session_id": "x", "lang": "dyu", "message": msg})
    assert len(seen[0]) == 1 and len(seen[1]) == 3
    assert seen[1][0]["content"] == "[stub dyu→fr] a"


def test_sessions_are_isolated_per_client(api):
    app, client = api
    other_key = app.state.key_store.create("autre-appli")
    client.post("/api/v1/chat", json={"session_id": "same", "lang": "dyu", "message": "a"})
    client.post(
        "/api/v1/chat",
        json={"session_id": "same", "lang": "dyu", "message": "b"},
        headers={"X-API-Key": other_key},
    )
    assert len(app.state.sessions.get("tests:same", "dyu").history_fr) == 2
    assert len(app.state.sessions.get("autre-appli:same", "dyu").history_fr) == 2


def test_fallback_when_translation_is_empty(api):
    app, client = api

    class EmptyTranslator:
        name = "vide"

        def translate(self, text, src, tgt):
            return ""

        def info(self):
            return {"name": self.name}

    app.state.orchestrator.translator = EmptyTranslator()
    r = client.post(
        "/api/v1/chat?debug=true", json={"session_id": "f", "lang": "dyu", "message": "I ni ce"}
    )
    body = r.json()
    assert body["debug"]["fallback_reason"] == "mt_in:sortie_vide"
    assert "LOCUTEUR NATIF" in body["reply"]  # le placeholder est bien visible


def test_unexpected_error_does_not_leak_details(api):
    app, client = api

    class BrokenTranslator:
        name = "casse"

        def translate(self, text, src, tgt):
            raise RuntimeError("secret interne")

    app.state.orchestrator.translator = BrokenTranslator()
    safe = TestClient(app, raise_server_exceptions=False)
    safe.headers.update(client.headers)
    r = safe.post("/api/v1/chat", json={"session_id": "e", "lang": "dyu", "message": "x"})
    assert r.status_code == 500
    assert "secret" not in r.text


# ----------------------------------------------------------------- correctifs du 01/10
def test_api_key_is_a_security_scheme_in_openapi(api):
    """Swagger doit afficher « Authorize » : la clé est un schéma de sécurité, pas un paramètre."""
    _, client = api
    spec = client.get("/openapi.json").json()
    scheme = spec["components"]["securitySchemes"]["APIKeyHeader"]
    assert scheme == {**scheme, "type": "apiKey", "in": "header", "name": "X-API-Key"}
    translate_op = spec["paths"]["/api/v1/translate"]["post"]
    assert translate_op["security"] == [{"APIKeyHeader": []}]
    assert all(p["name"] != "X-API-Key" for p in translate_op.get("parameters", []))
    assert "security" not in spec["paths"]["/health"]["get"]


def test_timings_keep_decimals(api):
    """Un stub répond en moins d'une ms : on doit voir 0.01, pas 0 arrondi à l'entier."""
    _, client = api
    r = client.post("/api/v1/translate", json={"text": "Bonjour", "src": "fr", "tgt": "dyu"})
    assert isinstance(r.json()["time_ms"], float)
    r = client.post(
        "/api/v1/chat?debug=true", json={"session_id": "t", "lang": "dyu", "message": "I ni ce"}
    )
    assert all(isinstance(v, float) for v in r.json()["debug"]["timings_ms"].values())


# ----------------------------------------------------------------- améliorations du 05/10
def test_llm_failure_gives_503_and_keeps_history_clean(api):
    """Panne du LLM : 503 uniforme, aucun détail interne, et l'échange raté n'est pas mémorisé."""
    app, client = api

    class BrokenLLM(StubLLM):
        def reply(self, history_fr, system_prompt):
            raise RuntimeError("secret interne")

    app.state.orchestrator.llm = BrokenLLM()
    r = client.post("/api/v1/chat", json={"session_id": "p", "lang": "dyu", "message": "I ni ce"})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "llm_indisponible"
    assert "secret" not in r.text
    assert app.state.sessions.get("tests:p", "dyu").history_fr == []


def test_llm_reply_is_cleaned_before_translation(api):
    app, client = api

    class MessyLLM(StubLLM):
        def reply(self, history_fr, system_prompt):
            return "**Bonjour**\n- premier point\n- deuxième point\n"

    app.state.orchestrator.llm = MessyLLM()
    r = client.post(
        "/api/v1/chat?debug=true", json={"session_id": "n", "lang": "dyu", "message": "I ni ce"}
    )
    assert r.json()["debug"]["fr_reply"] == "Bonjour. premier point. deuxième point"
    history = app.state.sessions.get("tests:n", "dyu").history_fr
    assert "\n" not in history[-1]["content"]
