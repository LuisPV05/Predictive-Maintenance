from pathlib import Path

from src.reports.excel import build_dashboard
from src.reports.fleet import load_readings, predict_fleet

OUTPUT = "reports/dashboard_flota.xlsx"


def main():
    df = predict_fleet()
    Path("reports").mkdir(exist_ok=True)
    build_dashboard(df, OUTPUT, readings=load_readings())
    print(f"Dashboard generado: {OUTPUT} ({len(df)} vehículos)")


if __name__ == "__main__":
    main()