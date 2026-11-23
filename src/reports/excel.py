from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(bold=True, color="FFFFFF")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
TITLE_FONT = Font(bold=True, size=14)

RED = PatternFill(start_color="F4B6B6", end_color="F4B6B6", fill_type="solid")
AMBER = PatternFill(start_color="FFE699", end_color="FFE699", fill_type="solid")
GREEN = PatternFill(start_color="C6E0B4", end_color="C6E0B4", fill_type="solid")

MAX_ALERTS = 20


def _header(ws, row, labels):
    for col, label in enumerate(labels, start=1):
        cell = ws.cell(row=row, column=col, value=label)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")


def _traffic_light(ws, status_col, cell_range):
    for text, fill in (("ROJO", RED), ("ÁMBAR", AMBER), ("VERDE", GREEN)):
        ws.conditional_formatting.add(
            cell_range,
            FormulaRule(formula=[f'${status_col}2="{text}"'], fill=fill),
        )


def _build_params(ws, red, amber, cost_unplanned, cost_preventive):
    ws["A1"] = "Parámetros (edita las celdas amarillas)"
    ws["A1"].font = TITLE_FONT
    rows = [
        ("Umbral rojo: RUL menor que (ciclos)", red),
        ("Umbral ámbar: RUL menor que (ciclos)", amber),
        ("Coste de parada no planificada (€)", cost_unplanned),
        ("Coste de mantenimiento preventivo (€)", cost_preventive),
    ]
    for i, (label, value) in enumerate(rows, start=3):
        ws.cell(row=i, column=1, value=label)
        cell = ws.cell(row=i, column=2, value=value)
        cell.fill = INPUT_FILL
    ws.column_dimensions["A"].width = 42
    ws.column_dimensions["B"].width = 14


def _build_fleet(ws, df):
    n = len(df)
    last = n + 1
    _header(ws, 1, ["Vehículo", "Ciclos operados", "RUL predicho", "Estado", "Prioridad"])
    for i, row in enumerate(df.itertuples(index=False), start=2):
        ws.cell(row=i, column=1, value=int(row.vehiculo))
        ws.cell(row=i, column=2, value=int(row.ciclos_operados))
        ws.cell(row=i, column=3, value=float(row.rul_pred))
        ws.cell(
            row=i,
            column=4,
            value=(
                f'=IF(C{i}<Parametros!$B$3,"ROJO",'
                f'IF(C{i}<Parametros!$B$4,"ÁMBAR","VERDE"))'
            ),
        )
        # Ranking de menor a mayor RUL; el COUNTIF desempata
        ws.cell(
            row=i,
            column=5,
            value=f"=RANK(C{i},$C$2:$C${last},1)+COUNTIF($C$2:C{i},C{i})-1",
        )
    _traffic_light(ws, "D", f"A2:E{last}")
    for col, width in zip("ABCDE", (12, 18, 16, 12, 12)):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:E{last}"


def _build_alerts(ws, n):
    last = n + 1
    rng = lambda col: f"Flota!${col}$2:${col}${last}"
    _header(ws, 1, ["Orden", "Vehículo", "RUL predicho", "Estado"])
    for k in range(1, min(n, MAX_ALERTS) + 1):
        r = k + 1
        pos = f"MATCH($A{r},{rng('E')},0)"
        ws.cell(row=r, column=1, value=k)
        ws.cell(
            row=r,
            column=3,
            value=(
                f'=IFERROR(IF(INDEX({rng("C")},{pos})<Parametros!$B$4,'
                f'INDEX({rng("C")},{pos}),""),"")'
            ),
        )
        ws.cell(row=r, column=2, value=f'=IF(C{r}="","",INDEX({rng("A")},{pos}))')
        ws.cell(row=r, column=4, value=f'=IF(C{r}="","",INDEX({rng("D")},{pos}))')
    _traffic_light(ws, "D", f"A2:D{min(n, MAX_ALERTS) + 1}")
    for col, width in zip("ABCD", (10, 12, 16, 12)):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"


def _build_summary(ws, n):
    last = n + 1
    ws["A1"] = "Resumen de la flota"
    ws["A1"].font = TITLE_FONT
    kpis = [
        ("Vehículos en la flota", f"=COUNTA(Flota!A2:A{last})", None),
        ("En alerta roja", f'=COUNTIF(Flota!D2:D{last},"ROJO")', None),
        ("En alerta ámbar", f'=COUNTIF(Flota!D2:D{last},"ÁMBAR")', None),
        ("Estado verde", f'=COUNTIF(Flota!D2:D{last},"VERDE")', None),
        ("% en alerta roja", "=IF(B3=0,0,B4/B3)", "0.0%"),
        ("RUL medio de la flota (ciclos)", f"=AVERAGE(Flota!C2:C{last})", "0.0"),
        (
            "Coste evitado estimado (€)",
            "=B4*(Parametros!B5-Parametros!B6)",
            "#,##0",
        ),
    ]
    for i, (label, formula, fmt) in enumerate(kpis, start=3):
        ws.cell(row=i, column=1, value=label)
        cell = ws.cell(row=i, column=2, value=formula)
        if fmt:
            cell.number_format = fmt
        cell.font = Font(bold=True)
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 14

    chart = BarChart()
    chart.title = "Vehículos por estado"
    chart.legend = None
    chart.add_data(Reference(ws, min_col=2, min_row=4, max_row=6))
    chart.set_categories(Reference(ws, min_col=1, min_row=4, max_row=6))
    chart.height, chart.width = 7, 12
    ws.add_chart(chart, "D3")


def build_dashboard(
    df, path, red=30, amber=60, cost_unplanned=5000, cost_preventive=800
):
    """Genera el libro de Excel del dashboard a partir de las predicciones."""
    wb = Workbook()
    ws_summary = wb.active
    ws_summary.title = "Resumen"
    ws_fleet = wb.create_sheet("Flota")
    ws_alerts = wb.create_sheet("Alertas")
    ws_params = wb.create_sheet("Parametros")

    _build_params(ws_params, red, amber, cost_unplanned, cost_preventive)
    _build_fleet(ws_fleet, df)
    _build_alerts(ws_alerts, len(df))
    _build_summary(ws_summary, len(df))
    wb.save(path)
    return path