import pandas as pd
from openpyxl import load_workbook
from src.reports.excel import SENSOR_CHART
from src.reports.excel import build_dashboard


def make_fleet():
    return pd.DataFrame(
        {
            "vehiculo": [1, 2, 3, 4],
            "ciclos_operados": [100, 150, 200, 250],
            "rul_pred": [10.0, 45.0, 80.0, 120.0],
        }
    )


def build(tmp_path):
    path = tmp_path / "test.xlsx"
    build_dashboard(make_fleet(), path)
    return load_workbook(path)


def test_workbook_has_expected_sheets(tmp_path):
    wb = build(tmp_path)
    assert wb.sheetnames == ["Resumen", "Flota", "Alertas", "Parametros"]


def test_fleet_sheet_has_one_row_per_vehicle(tmp_path):
    ws = build(tmp_path)["Flota"]
    assert ws.max_row == 1 + 4
    assert ws["C2"].value == 10.0


def test_status_is_a_formula_linked_to_parameters(tmp_path):
    ws = build(tmp_path)["Flota"]
    assert str(ws["D2"].value).startswith("=")
    assert "Parametros!$B$3" in ws["D2"].value


def test_default_parameters(tmp_path):
    ws = build(tmp_path)["Parametros"]
    assert ws["B3"].value == 30
    assert ws["B4"].value == 60

def make_readings():
    rows = {"vehiculo": [1, 1, 1, 2, 2], "ciclo": [1, 2, 3, 1, 2]}
    for s in SENSOR_CHART:
        rows[s] = [1.0, 2.0, 3.0, 4.0, 5.0]
    return pd.DataFrame(rows)


def build_with_readings(tmp_path):
    path = tmp_path / "sensors.xlsx"
    build_dashboard(make_fleet(), path, readings=make_readings())
    return load_workbook(path)


def test_sensors_sheets_added_with_readings(tmp_path):
    wb = build_with_readings(tmp_path)
    assert wb.sheetnames == [
        "Resumen", "Flota", "Alertas", "Sensores", "Parametros", "Datos"
    ]


def test_datos_has_one_row_per_reading(tmp_path):
    ws = build_with_readings(tmp_path)["Datos"]
    assert ws.max_row == 1 + 5


def test_sensors_has_selector_and_charts(tmp_path):
    ws = build_with_readings(tmp_path)["Sensores"]
    assert len(ws.data_validations.dataValidation) == 1
    assert str(ws["B4"].value).startswith("=")
    assert len(ws._charts) == len(SENSOR_CHART)