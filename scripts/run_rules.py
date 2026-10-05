"""
Run the SQL detection rules against data/aml.db and summarize the alerts.

Each rule lives in sql/<rule>.sql. Thresholds are set in PARAMETERS below so
they can be tuned in one place (issue: Measure alerts and tune thresholds).

Outputs:
    data/alerts.csv               all alerts (kept local; .gitignore excludes it)
    reports/detection_summary.md  alert counts per rule

Usage (from the repo root, after running scripts/load_db.py):
    py scripts/run_rules.py
"""

import argparse
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

RULES = ["structuring", "rapid_movement", "dormant_reactivation"]

PARAMETERS = {
    # Structuring: cash payments between this amount and $10,000
    "struct_low_amount": 9000,
    "struct_window_days": 7,
    "struct_min_count": 2,
    # Rapid movement: share of a received payment sent out within the window
    "rapid_window_hours": 24,
    "rapid_min_ratio": 0.9,
    "rapid_max_ratio": 1.0,
    # Dormant reactivation: inactivity gap and minimum US Dollar amount
    "dormant_days": 5,
    "dormant_min_amount": 5000,
}


def run_rule(con, rule, sql_dir):
    sql = (sql_dir / f"{rule}.sql").read_text(encoding="utf-8")
    con.executescript(sql.format(**PARAMETERS))
    return pd.read_sql(f"SELECT * FROM alerts_{rule}", con)


def summarize(alerts_by_rule, total_laundering, output_path):
    lines = [
        "# Detection Summary",
        "",
        f"- **Run date:** {datetime.now():%Y-%m-%d %H:%M}",
        f"- **Laundering-labeled transactions in dataset:** {total_laundering:,}",
        "",
        "## Alerts by rule",
        "",
        "| Rule | Alerts | Unique accounts | Alerts on laundering-labeled transactions | Hit rate |",
        "|---|---:|---:|---:|---:|",
    ]
    for rule, df in alerts_by_rule.items():
        hits = int(df["is_laundering"].sum()) if len(df) else 0
        rate = f"{hits / len(df):.2%}" if len(df) else "n/a"
        accounts = df[["bank", "account"]].drop_duplicates().shape[0]
        lines.append(f"| {rule} | {len(df):,} | {accounts:,} | {hits:,} | {rate} |")

    lines += ["", "## Parameters", "", "| Parameter | Value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in PARAMETERS.items()]
    lines += [
        "",
        "**Hit rate** = share of alerts on transactions the dataset labels as "
        "laundering. Rule logic is documented in docs/detection_rules.md.",
        "",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Run SQL detection rules.")
    parser.add_argument("--db", default="data/aml.db")
    parser.add_argument("--sql-dir", default="sql")
    parser.add_argument("--alerts", default="data/alerts.csv")
    parser.add_argument("--summary", default="reports/detection_summary.md")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"{db_path} not found. Run: py scripts/load_db.py")

    con = sqlite3.connect(db_path)
    alerts_by_rule = {}
    for rule in RULES:
        print(f"Running {rule}...", end=" ", flush=True)
        start = time.time()
        alerts_by_rule[rule] = run_rule(con, rule, Path(args.sql_dir))
        print(f"{len(alerts_by_rule[rule]):,} alerts ({time.time() - start:.0f}s)")

    total_laundering = con.execute(
        "SELECT SUM(is_laundering) FROM transactions").fetchone()[0] or 0
    con.close()

    all_alerts = pd.concat(alerts_by_rule.values(), ignore_index=True)
    Path(args.alerts).parent.mkdir(parents=True, exist_ok=True)
    all_alerts.to_csv(args.alerts, index=False)
    summarize(alerts_by_rule, total_laundering, Path(args.summary))

    print(f"\n{len(all_alerts):,} total alerts written to {args.alerts}")
    print(f"Summary written to {args.summary}")


if __name__ == "__main__":
    main()
