"""
Build the before/after results charts for the README.

Runs each detection rule twice against data/aml.db: once with the original
baseline thresholds and once with the tuned thresholds currently set in
scripts/run_rules.py. Writes:

    reports/before_after.md                 comparison table
    reports/figures/alerts_by_rule.png      alert volume, before vs. after
    reports/figures/hit_rate_by_rule.png    hit rate vs. the base rate
    reports/figures/summary.png             headline numbers

Usage (from the repo root):
    py -m pip install matplotlib
    py scripts/build_dashboard.py
Expect about 5 minutes on the full dataset.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from run_rules import PARAMETERS as TUNED, RULES  # noqa: E402

# Original thresholds before tuning (issue #5)
BASELINE = {
    "struct_low_amount": 9000, "struct_window_days": 7, "struct_min_count": 2,
    "rapid_window_hours": 24, "rapid_min_ratio": 0.9, "rapid_max_ratio": 1.0,
    "dormant_days": 5, "dormant_min_amount": 5000,
}

LABELS = {
    "structuring": "Structuring",
    "rapid_movement": "Rapid movement",
    "dormant_reactivation": "Dormant reactivation",
}

# Colors: baseline is a neutral gray so the tuned result carries the emphasis
SURFACE = "#ffffff"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"
BEFORE = "#b5b3ad"
AFTER = "#2a78d6"


def evaluate(con, sql_dir, params):
    results = {}
    for rule in RULES:
        sql = (sql_dir / f"{rule}.sql").read_text(encoding="utf-8")
        con.executescript(sql.format(**params))
        alerts, hits = con.execute(
            f"SELECT COUNT(*), COALESCE(SUM(is_laundering), 0) FROM alerts_{rule}"
        ).fetchone()
        results[rule] = {"alerts": alerts, "hits": hits,
                         "rate": hits / alerts if alerts else 0.0}
        print(f"  {LABELS[rule]}: {alerts:,} alerts, {hits:,} hits")
    return results


def style_axes(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=TEXT_SECONDARY, length=0, labelsize=10)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def paired_bars(before, after, rules, value_fmt, title, subtitle, xlabel,
                output, reference=None):
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    style_axes(ax)

    height, gap = 0.34, 0.04
    positions = list(range(len(rules)))[::-1]
    max_value = max(max(before), max(after), reference or 0)
    for y, b, a in zip(positions, before, after):
        ax.barh(y + (height + gap) / 2, b, height=height, color=BEFORE)
        ax.barh(y - (height + gap) / 2, a, height=height, color=AFTER)
        for value, offset in ((b, (height + gap) / 2), (a, -(height + gap) / 2)):
            # Keep labels clear of the dashed reference line
            label_x = max(value, reference or 0) + max_value * 0.01
            ax.text(label_x, y + offset, value_fmt(value),
                    va="center", ha="left", fontsize=9, color=TEXT_PRIMARY)

    if reference is not None:
        ax.axvline(reference, color=TEXT_SECONDARY, linewidth=1,
                   linestyle=(0, (4, 3)))
        ax.text(reference, len(rules) - 0.45,
                f"  Base rate {value_fmt(reference)}",
                fontsize=9, color=TEXT_SECONDARY, va="center")

    ax.set_yticks(positions)
    ax.set_yticklabels([LABELS[r] for r in rules], color=TEXT_PRIMARY,
                       fontsize=10)
    ax.set_xlim(0, max_value * 1.18)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: value_fmt(v)))
    ax.set_xlabel(xlabel, color=TEXT_SECONDARY, fontsize=9)

    fig.text(0.01, 0.97, title, fontsize=13, fontweight="bold",
             color=TEXT_PRIMARY, va="top")
    fig.text(0.01, 0.905, subtitle, fontsize=9.5, color=TEXT_SECONDARY,
             va="top")
    handles = [plt.Rectangle((0, 0), 1, 1, color=BEFORE),
               plt.Rectangle((0, 0), 1, 1, color=AFTER)]
    fig.legend(handles, ["Before tuning", "After tuning"], loc="upper right",
               bbox_to_anchor=(0.99, 0.985), frameon=False, ncol=2,
               fontsize=9, labelcolor=TEXT_PRIMARY)
    fig.subplots_adjust(left=0.2, right=0.97, top=0.8, bottom=0.14)
    fig.savefig(output, facecolor=SURFACE)
    plt.close(fig)


def summary_figure(totals, output):
    fig = plt.figure(figsize=(9, 2.4), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    tiles = [
        ("Total alerts", totals["alerts_before"], totals["alerts_after"]),
        ("Laundering-labeled alerts", totals["hits_before"],
         totals["hits_after"]),
    ]
    for i, (label, before, after) in enumerate(tiles):
        x = 0.03 + i * 0.5
        change = (after - before) / before if before else 0
        fig.text(x, 0.82, label, fontsize=10.5, color=TEXT_SECONDARY)
        fig.text(x, 0.42, f"{change:+.0%}", fontsize=34, fontweight="bold",
                 color=TEXT_PRIMARY)
        fig.text(x, 0.16, f"{before:,} before  →  {after:,} after",
                 fontsize=10, color=TEXT_SECONDARY)
    fig.savefig(output, facecolor=SURFACE)
    plt.close(fig)


def write_table(before, after, base_rate, output):
    lines = [
        "# Before and After Tuning",
        "",
        f"Base rate (share of all transactions labeled laundering): "
        f"{base_rate:.3%}",
        "",
        "| Rule | Alerts before | Alerts after | Hits before | Hits after "
        "| Hit rate before | Hit rate after |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for rule in RULES:
        b, a = before[rule], after[rule]
        lines.append(
            f"| {LABELS[rule]} | {b['alerts']:,} | {a['alerts']:,} "
            f"| {b['hits']:,} | {a['hits']:,} | {b['rate']:.2%} | {a['rate']:.2%} |")
    tb = sum(v["alerts"] for v in before.values())
    ta = sum(v["alerts"] for v in after.values())
    hb = sum(v["hits"] for v in before.values())
    ha = sum(v["hits"] for v in after.values())
    lines.append(f"| **Total** | **{tb:,}** | **{ta:,}** | **{hb:,}** "
                 f"| **{ha:,}** | | |")
    lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")
    return {"alerts_before": tb, "alerts_after": ta,
            "hits_before": hb, "hits_after": ha}


def main():
    parser = argparse.ArgumentParser(description="Build results charts.")
    parser.add_argument("--db", default="data/aml.db")
    parser.add_argument("--sql-dir", default="sql")
    parser.add_argument("--reports", default="reports")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"{db_path} not found. Run: py scripts/load_db.py")
    reports = Path(args.reports)
    figures = reports / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(db_path)
    total, laundering = con.execute(
        "SELECT COUNT(*), SUM(is_laundering) FROM transactions").fetchone()
    base_rate = (laundering or 0) / total
    print("Running rules with baseline thresholds...")
    before = evaluate(con, Path(args.sql_dir), BASELINE)
    print("Running rules with tuned thresholds...")
    after = evaluate(con, Path(args.sql_dir), TUNED)
    con.close()

    totals = write_table(before, after, base_rate, reports / "before_after.md")

    paired_bars(
        [before[r]["alerts"] for r in RULES],
        [after[r]["alerts"] for r in RULES],
        RULES, lambda v: f"{v:,.0f}",
        "Alert volume by rule",
        f"Total alerts {totals['alerts_before']:,} before tuning, "
        f"{totals['alerts_after']:,} after",
        "Alerts", figures / "alerts_by_rule.png")

    paired_bars(
        [before[r]["rate"] * 100 for r in RULES],
        [after[r]["rate"] * 100 for r in RULES],
        RULES, lambda v: f"{v:.2f}%",
        "Hit rate by rule",
        "Share of alerts on laundering-labeled transactions; "
        "the dashed line is the rate for random alerts",
        "Hit rate", figures / "hit_rate_by_rule.png",
        reference=base_rate * 100)

    summary_figure(totals, figures / "summary.png")

    print(f"\nTable written to {reports / 'before_after.md'}")
    print(f"Charts written to {figures}")


if __name__ == "__main__":
    main()
