import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.ingest.load_csv import load_csv, clean_data
from scripts.analyze.analyze_data import analyze
from scripts.report.generate_summary import save_summary
from scripts.report.generate_dashboard import save_dashboard
from scripts.report.generate_pdf import save_pdf


def run_pipeline(input_file, comparison_file=None, output_dir=None, date_col=None, value_cols=None):
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"[ERR] File not found: {input_path}")
        sys.exit(1)

    if output_dir is None:
        output_dir = Path("reports")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    date_stamp = datetime.now().strftime("%Y-%m-%d")
    stem = input_path.stem

    print(f"[1/4] Loading CSV: {input_path.name}...")
    df, metadata = load_csv(input_file)
    print(f"       Rows: {metadata['rows']}, Cols: {metadata['columns']}")

    df, cleaning_log = clean_data(df)
    print(f"       Cleaning: {len(cleaning_log)} operations")

    comparison_df = None
    if comparison_file:
        comp_path = Path(comparison_file)
        if comp_path.exists():
            print(f"[2/4] Loading comparison CSV: {comp_path.name}...")
            comparison_df, _ = load_csv(str(comp_path))
        else:
            print(f"[WARN] Comparison file not found: {comp_path}, skipping")

    print(f"[2/4] Analyzing data...")
    result = analyze(df, metadata, comparison_df=comparison_df, date_column=date_col, value_columns=value_cols)

    summary_file = output_dir / f"{date_stamp}_{stem}_summary.md"
    print(f"[3/5] Generating summary: {summary_file}")
    save_summary(result, str(summary_file))

    dashboard_file = output_dir / f"{date_stamp}_{stem}_dashboard.html"
    print(f"[4/5] Generating dashboard: {dashboard_file}")
    save_dashboard(result, str(dashboard_file))

    pdf_file = output_dir / f"{date_stamp}_{stem}_report.pdf"
    print(f"[5/5] Generating PDF: {pdf_file}")
    save_pdf(result, str(pdf_file))

    print(f"\n[DONE] Reports saved to: {output_dir}")
    print(f"  - Summary:   {summary_file}")
    print(f"  - Dashboard: {dashboard_file}")
    print(f"  - PDF:       {pdf_file}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Умная диагностика — анализ табличных данных (CSV)"
    )
    parser.add_argument("input", help="Путь к CSV-файлу")
    parser.add_argument("--compare", help="CSV-файл для сравнения (опционально)")
    parser.add_argument("-o", "--output", help="Папка для отчётов (по умолчанию reports/)")
    parser.add_argument("--date-col", help="Название столбца с датами")
    parser.add_argument("--value-cols", nargs="*", help="Столбцы для детального анализа")

    args = parser.parse_args()
    run_pipeline(
        args.input,
        comparison_file=args.compare,
        output_dir=args.output,
        date_col=args.date_col,
        value_cols=args.value_cols,
    )


if __name__ == "__main__":
    main()
