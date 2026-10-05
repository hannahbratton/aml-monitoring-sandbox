"""
Data quality checks for the IBM AML HI-Small transactions dataset.

Runs schema, completeness, validity, and uniqueness checks before any
detection rules are applied, and writes a Markdown summary report.

Usage (from the repo root):
    python scripts/data_quality.py
    python scripts/data_quality.py --input data/HI-Small_Trans.csv --output reports/data_quality_report.md
"""

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

# pandas renames the second "Account" column to "Account.1" on load
EXPECTED_COLUMNS = [
    "Timestamp", "From Bank", "Account", "To Bank", "Account.1",
    "Amount Received", "Receiving Currency", "Amount Paid",
    "Payment Currency", "Payment Format", "Is Laundering",
]
AMOUNT_COLUMNS = ["Amount Received", "Amount Paid"]
TIMESTAMP_FORMAT = "%Y/%m/%d %H:%M"


def load_data(path):
    print(f"Loading {path} (this can take a minute for large files)...")
    df = pd.read_csv(path, low_memory=False)
    print(f"Loaded {len(df):,} rows and {len(df.columns)} columns.")
    return df


def parse_timestamps(series):
    parsed = pd.to_datetime(series, format=TIMESTAMP_FORMAT, errors="coerce")
    # Fall back to flexible parsing if the expected format doesn't match
    if parsed.isna().mean() > 0.5:
        parsed = pd.to_datetime(series, errors="coerce")
    return parsed


def run_checks(df):
    total = len(df)
    results = []  # (check, count, status, note)

    def add(check, count, note="", informational=False):
        if informational:
            status = "INFO"
        else:
            status = "PASS" if count == 0 else "FLAG"
        results.append((check, int(count), status, note))

    # Schema
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    unexpected = [c for c in df.columns if c not in EXPECTED_COLUMNS]
    add("Missing expected columns", len(missing), ", ".join(missing))
    add("Unexpected columns", len(unexpected), ", ".join(unexpected))

    # Completeness
    for col in df.columns:
        add(f"Nulls in '{col}'", df[col].isna().sum())

    # Uniqueness
    add("Exact duplicate rows", df.duplicated().sum())

    # Validity: amounts
    for col in AMOUNT_COLUMNS:
        if col in df.columns:
            amounts = pd.to_numeric(df[col], errors="coerce")
            add(f"Non-numeric '{col}'", (amounts.isna() & df[col].notna()).sum())
            add(f"Negative '{col}'", (amounts < 0).sum())
            add(f"Zero '{col}'", (amounts == 0).sum())

    # Validity: timestamps
    ts_range = None
    if "Timestamp" in df.columns:
        ts = parse_timestamps(df["Timestamp"])
        add("Unparseable timestamps", (ts.isna() & df["Timestamp"].notna()).sum())
        if ts.notna().any():
            ts_range = (ts.min(), ts.max())

    # Validity: label
    label_rate = None
    if "Is Laundering" in df.columns:
        labels = df["Is Laundering"]
        add("Labels other than 0/1", (~labels.isin([0, 1])).sum())
        label_rate = (labels == 1).mean()

    # Informational: patterns worth knowing, not errors
    if {"From Bank", "Account", "To Bank", "Account.1"} <= set(df.columns):
        self_transfers = (
            (df["From Bank"] == df["To Bank"]) & (df["Account"] == df["Account.1"])
        ).sum()
        add("Self-transfers (same sender and receiver)", self_transfers,
            "Expected in this dataset; review before rule design", informational=True)
    if {"Receiving Currency", "Payment Currency"} <= set(df.columns):
        add("Cross-currency transactions",
            (df["Receiving Currency"] != df["Payment Currency"]).sum(),
            "Amount Paid and Amount Received differ in currency", informational=True)

    summary = {"rows": total, "columns": len(df.columns),
               "ts_range": ts_range, "label_rate": label_rate}
    return results, summary


def write_report(results, summary, input_path, output_path):
    total = summary["rows"]
    flagged = sum(1 for r in results if r[2] == "FLAG")

    lines = [
        "# Data Quality Report",
        "",
        f"- **Source file:** `{input_path}`",
        f"- **Run date:** {datetime.now():%Y-%m-%d %H:%M}",
        f"- **Rows:** {total:,}",
        f"- **Columns:** {summary['columns']}",
    ]
    if summary["ts_range"]:
        start, end = summary["ts_range"]
        lines.append(f"- **Date range:** {start:%Y-%m-%d} to {end:%Y-%m-%d}")
    if summary["label_rate"] is not None:
        lines.append(f"- **Laundering rate:** {summary['label_rate']:.4%}")
    lines += [
        f"- **Checks flagged:** {flagged} of "
        f"{sum(1 for r in results if r[2] != 'INFO')}",
        "",
        "## Results",
        "",
        "| Check | Count | % of rows | Status | Note |",
        "|---|---:|---:|---|---|",
    ]
    for check, count, status, note in results:
        pct = f"{count / total:.2%}" if total else "n/a"
        lines.append(f"| {check} | {count:,} | {pct} | {status} | {note} |")

    lines += [
        "",
        "**Status key:** PASS = no issues found; FLAG = issues found, review "
        "before detection; INFO = expected pattern, documented for context.",
        "",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Run data quality checks.")
    parser.add_argument("--input", default="data/HI-Small_Trans.csv")
    parser.add_argument("--output", default="reports/data_quality_report.md")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"File not found: {input_path}. "
                         "See docs/dataset.md for download steps.")

    df = load_data(input_path)
    print("Columns found:", list(df.columns))
    results, summary = run_checks(df)
    output_path = Path(args.output)
    write_report(results, summary, input_path, output_path)

    flagged = [r for r in results if r[2] == "FLAG"]
    print(f"\nReport written to {output_path}")
    print(f"{len(flagged)} check(s) flagged.")
    for check, count, _, _ in flagged:
        print(f"  - {check}: {count:,}")


if __name__ == "__main__":
    main()
