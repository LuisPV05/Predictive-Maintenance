import pandas as pd
from fastapi.testclient import TestClient

import app.main as main

client = TestClient(main.app)


def fake_fleet():
    return pd.DataFrame(
        {
            "vehiculo": [1, 2, 3, 4],
            "ciclos_operados": [100, 150, 200, 250],
            "rul_pred": [10.0, 45.0, 80.0, 120.0],
        }
    )


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_classify():
    assert main.classify(10, 30, 60) == "ROJO"
    assert main.classify(45, 30, 60) == "ÁMBAR"
    assert main.classify(80, 30, 60) == "VERDE"


def test_fleet_endpoint(monkeypatch):
    monkeypatch.setattr(main, "default_fleet", fake_fleet)
    data = client.get("/fleet").json()
    assert [d["estado"] for d in data] == ["ROJO", "ÁMBAR", "VERDE", "VERDE"]


def test_fleet_custom_thresholds(monkeypatch):
    monkeypatch.setattr(main, "default_fleet", fake_fleet)
    data = client.get("/fleet?red=30&amber=100").json()
    assert [d["estado"] for d in data] == ["ROJO", "ÁMBAR", "ÁMBAR", "VERDE"]


def test_report_is_xlsx(monkeypatch):
    monkeypatch.setattr(main, "default_fleet", fake_fleet)
    r = client.get("/report")
    assert r.status_code == 200
    assert r.content[:2] == b"PK"  # los .xlsx son zips

def test_index_serves_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Mantenimiento predictivo" in r.text


def test_report_accepts_costs(monkeypatch):
    monkeypatch.setattr(main, "default_fleet", fake_fleet)
    r = client.get("/report?cost_unplanned=1000&cost_preventive=100")
    assert r.status_code == 200
    assert r.content[:2] == b"PK"