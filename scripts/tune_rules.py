"""
Threshold tuning for the SQL detection rules.

Runs each rule across a grid of parameter settings, measures alert volume and
how many alerts land on laundering-labeled transactions, and writes a
comparison table. The baseline is the current PARAMETERS in run_rules.py.

Selection criterion for the recommended setting: the highest hit rate among
settings that keep at least MIN_HITS_RETAINED of the baseline's hits. This
favors cutting false positives without giving up much detection.

Usage (from the repo root, after running scripts/load_db.py):
    py scripts/tune_rules.py
Expect roughly 10-15 minutes on the full dataset.
"""

import argparse
import itertools
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_rules import PARAMETERS  # noqa: E402  (baseline settings)

MIN_HITS_RETAINED = 0.9

# Settings to test for each rule. Every combination is run.
GRIDS = {
    "rapid_movement": {
        "rapid_window_hours": [24, 12, 6],
        "rapid_min_ratio": [0.9, 0.95],
    },
    "dormant_reactivation": {
        "dormant_days": [3, 5, 7],
        "dormant_min_amount": [1000, 5000, 10000],
    },
}


def evaluate(con, rule, params, sql_dir):
    sql = (sql_dir / f"{rule}.sql").read_text(encoding="utf-8")
    con.executescript(sql.format(**params))
    alerts, hits = con.execute(
        f"SELECT COUNT(*), COALESCE(SUM(is_laundering), 0) FROM alerts_{rule}"
    ).fetchone()
    return alerts, hits


def run_grid(con, rule, grid, sql_dir, base_rate):
    names = list(grid)
    rows = []
    for values in itertools.product(*(grid[n] for n in names)):
        params = {**PARAMETERS, **dict(zip(names, values))}
        start = time.time()
        alerts, hits = evaluate(con, rule, params, sql_dir)
        rate = hits / alerts if alerts else 0.0
        is_baseline = all(params[n] == PARAMETERS[n] for n in names)
        rows.append({
            "settings": {n: params[n] for n in names},
            "alerts": alerts, "hits": hits, "hit_rate": rate,
            "lift": rate / base_rate if base_rate else 0.0,
            "baseline": is_baseline,
        })
        label = ", ".join(f"{n}={params[n]}" for n in names)
        print(f"  {label}: {alerts:,} alerts, {hits:,} hits "
              f"({rate:.2%}) [{time.time() - start:.0f}s]")
    return rows


def pick_recommended(rows):
    baseline = next((r for r in rows if r["baseline"]), None)
    if baseline is None or baseline["hits"] == 0:
        return max(rows, key=lambda r: r["hit_rate"])
    eligible = [r for r in rows
                if r["hits"] >= MIN_HITS_RETAINED * baseline["hits"]]
    return max(eligible, key=lambda r: r["hit_rate"])


def write_report(results, base_rate, total_laundering, output_path):
    lines = [
        "# Threshold Tuning Results",
        "",
        f"- **Run date:** {datetime.now():%Y-%m-%d %H:%M}",
        f"- **Laundering-labeled transactions:** {total_laundering:,}",
        f"- **Base rate:** {base_rate:.3%} (hit rate expected from random alerts)",
        f"- **Recommendation rule:** highest hit rate that keeps at least "
        f"{MIN_HITS_RETAINED:.0%} of baseline hits",
        "",
        "**Lift** = hit rate divided by the base rate. A lift of 10 means the "
        "rule's alerts are 10 times more likely to be laundering than a random "
        "transaction.",
        "",
    ]
    for rule, (rows, recommended) in results.items():
        names = list(rows[0]["settings"])
        lines += [
            f"## {rule}",
            "",
            "| " + " | ".join(names)
            + " | Alerts | Hits | Hit rate | Lift | Note |",
            "|" + "---|" * len(names) + "---:|---:|---:|---:|---|",
        ]
        for r in rows:
            notes = []
            if r["baseline"]:
                notes.append("Baseline")
            if r is recommended:
                notes.append("**Recommended**")
            lines.append(
                "| " + " | ".join(str(r["settings"][n]) for n in names)
                + f" | {r['alerts']:,} | {r['hits']:,} | {r['hit_rate']:.2%}"
                + f" | {r['lift']:.1f} | {', '.join(notes)} |")

        baseline = next((r for r in rows if r["baseline"]), None)
        if baseline and baseline["alerts"]:
            change = (recommended["alerts"] - baseline["alerts"]) / baseline["alerts"]
            lines += [
                "",
                f"Recommended vs. baseline: alerts {baseline['alerts']:,} to "
                f"{recommended['alerts']:,} ({change:+.0%}), hits "
                f"{baseline['hits']:,} to {recommended['hits']:,}, hit rate "
                f"{baseline['hit_rate']:.2%} to {recommended['hit_rate']:.2%}.",
            ]
        lines.append("")

    lines += [
        "## Structuring",
        "",
        "Not tuned. The baseline produced no alerts on laundering-labeled "
        "transactions because the dataset's laundering patterns are "
        "network-based rather than sub-$10,000 cash structuring. The rule is "
        "kept as a control.",
        "",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Tune detection thresholds.")
    parser.add_argument("--db", default="data/aml.db")
    parser.add_argument("--sql-dir", default="sql")
    parser.add_argument("--output", default="reports/tuning_results.md")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"{db_path} not found. Run: py scripts/load_db.py")

    con = sqlite3.connect(db_path)
    total, total_laundering = con.execute(
        "SELECT COUNT(*), SUM(is_laundering) FROM transactions").fetchone()
    base_rate = (total_laundering or 0) / total

    results = {}
    for rule, grid in GRIDS.items():
        print(f"Tuning {rule}...")
        rows = run_grid(con, rule, grid, Path(args.sql_dir), base_rate)
        results[rule] = (rows, pick_recommended(rows))
    con.close()

    write_report(results, base_rate, total_laundering or 0, Path(args.output))
    print(f"\nResults written to {args.output}")
    print("Recommended settings (copy into PARAMETERS in scripts/run_rules.py):")
    for rule, (_, recommended) in results.items():
        for name, value in recommended["settings"].items():
            print(f'    "{name}": {value},')


if __name__ == "__main__":
    main()
