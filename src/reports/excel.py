from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference, ScatterChart, Series
from openpyxl.chart.series import DataPoint
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(bold=True, color="FFFFFF")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
TITLE_FONT = Font(bold=True, size=14)

RED = PatternFill(start_color="F4B6B6", end_color="F4B6B6", fill_type="solid")
AMBER = PatternFill(start_color="FFE699", end_color="FFE699", fill_type="solid")
GREEN = PatternFill(start_color="C6E0B4", end_color="C6E0B4", fill_type="solid")

MAX_ALERTS = 50
SENSOR_CHART = ["s11", "s4", "s12", "s7", "s15", "s21"]
MAX_CYCLES = 400


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
    has_drivers = "sensores_clave" in df.columns
    labels = ["Vehículo", "Ciclos operados", "RUL predicho", "Estado", "Prioridad"]
    if has_drivers:
        labels.append("Sensores clave")
    last_col = get_column_letter(len(labels))
    _header(ws, 1, labels)
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
        if has_drivers:
            ws.cell(row=i, column=6, value=str(row.sensores_clave))
    _traffic_light(ws, "D", f"A2:{last_col}{last}")
    widths = (12, 18, 16, 12, 12, 24)
    for col, width in zip("ABCDEF", widths):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{last_col}{last}"


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
    chart.x_axis.delete = False
    chart.y_axis.delete = False
    series = chart.series[0]
    for idx, color in enumerate(("C00000", "FFC000", "70AD47")):
        point = DataPoint(idx=idx)
        point.graphicalProperties.solidFill = color
        series.dPt.append(point)
    ws.add_chart(chart, "D3")


def _build_data(ws, readings):
    """Lecturas en bruto de todos los vehículos (ordenadas por vehículo y ciclo)."""
    cols = ["vehiculo", "ciclo"] + SENSOR_CHART
    _header(ws, 1, cols)
    for r in readings[cols].itertuples(index=False):
        ws.append([int(r[0]), int(r[1])] + [float(x) for x in r[2:]])
    ws.freeze_panes = "A2"


def _build_sensors(ws, n_fleet, n_data):
    fl, dl = n_fleet + 1, n_data + 1
    ws["A1"] = "Sensores por vehículo"
    ws["A1"].font = TITLE_FONT
    ws.column_dimensions["A"].width = 28

    ws["A3"] = "Vehículo (elige uno)"
    ws["B3"] = 1
    ws["B3"].fill = INPUT_FILL
    dv = DataValidation(type="list", formula1=f"=Flota!$A$2:$A${fl}", allow_blank=False)
    ws.add_data_validation(dv)
    dv.add("B3")

    fleet = lambda col: f"Flota!${col}$2:${col}${fl}"
    ws["A4"] = "RUL predicho (ciclos)"
    ws["B4"] = f"=INDEX({fleet('C')},MATCH($B$3,{fleet('A')},0))"
    ws["A5"] = "Estado"
    ws["B5"] = f"=INDEX({fleet('D')},MATCH($B$3,{fleet('A')},0))"
    ws["A6"] = "Ciclos registrados"
    ws["B6"] = f"=COUNTIF(Datos!$A$2:$A${dl},$B$3)"
    ws["A7"] = "Primera fila en Datos (aux.)"
    ws["B7"] = f"=MATCH($B$3,Datos!$A$2:$A${dl},0)"
    for text, fill in (("ROJO", RED), ("ÁMBAR", AMBER), ("VERDE", GREEN)):
        ws.conditional_formatting.add(
            "B5", FormulaRule(formula=[f'$B$5="{text}"'], fill=fill)
        )

    # Tabla auxiliar (a la derecha) que alimenta los gráficos.
    # #N/A = ciclo inexistente, para que el gráfico no lo dibuje.
    tc, hr = 18, 3
    last = hr + MAX_CYCLES
    for j, label in enumerate(["Ciclo"] + SENSOR_CHART):
        ws.cell(row=hr, column=tc + j, value=label)
    for k in range(1, MAX_CYCLES + 1):
        r = hr + k
        ws.cell(row=r, column=tc, value=f"=IF({k}<=$B$6,{k},NA())")
        for i in range(len(SENSOR_CHART)):
            dcol = get_column_letter(3 + i)
            ws.cell(
                row=r,
                column=tc + 1 + i,
                value=(
                    f"=IF({k}<=$B$6,"
                    f"INDEX(Datos!${dcol}$2:${dcol}${dl},$B$7+{k}-1),NA())"
                ),
            )

    for i, sensor in enumerate(SENSOR_CHART):
        chart = ScatterChart()
        chart.title = f"{sensor} frente al ciclo"
        chart.legend = None
        chart.x_axis.title = "Ciclo"
        chart.x_axis.delete = False
        chart.y_axis.delete = False
        x = Reference(ws, min_col=tc, min_row=hr + 1, max_row=last)
        y = Reference(ws, min_col=tc + 1 + i, min_row=hr, max_row=last)
        series = Series(y, x, title_from_data=True)
        series.marker.symbol = "none"
        series.smooth = False
        series.graphicalProperties.line.solidFill = "1F3864"
        series.graphicalProperties.line.width = 15000
        chart.series.append(series)
        chart.height, chart.width = 7, 12
        anchor = f"{'A' if i % 2 == 0 else 'H'}{9 + 15 * (i // 2)}"
        ws.add_chart(chart, anchor)


def build_dashboard(
    df,
    path,
    red=30,
    amber=60,
    cost_unplanned=5000,
    cost_preventive=800,
    readings=None,
):
    """Genera el libro de Excel. Con 'readings' añade las hojas Sensores y Datos."""
    wb = Workbook()
    ws_summary = wb.active
    ws_summary.title = "Resumen"
    ws_fleet = wb.create_sheet("Flota")
    ws_alerts = wb.create_sheet("Alertas")
    ws_sensors = wb.create_sheet("Sensores") if readings is not None else None
    ws_params = wb.create_sheet("Parametros")
    ws_data = wb.create_sheet("Datos") if readings is not None else None

    _build_params(ws_params, red, amber, cost_unplanned, cost_preventive)
    _build_fleet(ws_fleet, df)
    _build_alerts(ws_alerts, len(df))
    _build_summary(ws_summary, len(df))
    if readings is not None:
        _build_data(ws_data, readings)
        _build_sensors(ws_sensors, len(df), len(readings))
    wb.save(path)
    return path