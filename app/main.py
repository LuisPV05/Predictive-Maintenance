from functools import lru_cache
from io import BytesIO
from pathlib import Path

from fastapi.responses import FileResponse, Response

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile

from src.data.load import COLUMNS
from src.reports.excel import build_dashboard
from src.reports.fleet import load_artifacts, predict_fleet, predict_from_raw

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
STATIC = Path(__file__).parent / "static"

app = FastAPI(title="Predictive Maintenance API", version="0.1.0")


def classify(rul, red, amber):
    if rul < red:
        return "ROJO"
    if rul < amber:
        return "ÁMBAR"
    return "VERDE"


@lru_cache
def artifacts():
    return load_artifacts()


def default_fleet():
    return predict_fleet()


def to_records(df, red, amber):
    out = df.copy()
    out["estado"] = out["rul_pred"].apply(lambda r: classify(r, red, amber))
    return out.sort_values("rul_pred").to_dict(orient="records")

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/fleet")
def fleet(red: float = 30, amber: float = 60):
    return to_records(default_fleet(), red, amber)


@app.post("/fleet/upload")
async def fleet_upload(
    file: UploadFile = File(...), red: float = 30, amber: float = 60
):
    try:
        raw = pd.read_csv(file.file, sep=r"\s+", header=None, names=COLUMNS)
    except Exception:
        raise HTTPException(400, "No se pudo leer el archivo")
    if raw.empty or raw.isna().any().any():
        raise HTTPException(400, f"Se esperan {len(COLUMNS)} columnas sin cabecera")
    model, scaler = artifacts()
    return to_records(predict_from_raw(raw, model, scaler), red, amber)


@app.get("/report")
def report(
    red: float = 30,
    amber: float = 60,
    cost_unplanned: float = 5000,
    cost_preventive: float = 800,
):
    buf = BytesIO()
    build_dashboard(
        default_fleet(),
        buf,
        red=red,
        amber=amber,
        cost_unplanned=cost_unplanned,
        cost_preventive=cost_preventive,
    )
    return Response(
        content=buf.getvalue(),
        media_type=XLSX,
        headers={"Content-Disposition": 'attachment; filename="dashboard_flota.xlsx"'},
    )