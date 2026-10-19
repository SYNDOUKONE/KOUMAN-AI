"""Test du montage de l'interface Web de démonstration."""

from __future__ import annotations


def test_ui_serves_html(api):
    _, client = api
    r = client.get("/ui/")
    assert r.status_code == 200
    assert "KOUMAN AI" in r.text
    assert "style.css" in r.text


def test_root_redirects_to_ui(api):
    _, client = api
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (307, 200)
