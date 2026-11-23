import pandas as pd
from openpyxl import load_workbook

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