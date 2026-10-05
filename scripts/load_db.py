"""
Load the IBM AML HI-Small CSV into a local SQLite database for SQL-based
detection rules.

Creates data/aml.db with one table, `transactions`, using snake_case column
names and timestamps stored as Unix epoch seconds (`ts`) so time windows can
be expressed in seconds inside SQL.

Usage (from the repo root):
    py scripts/load_db.py
"""

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

COLUMN_NAMES = [
    "ts_text", "from_bank", "from_account", "to_bank", "to_account",
    "amount_received", "receiving_currency", "amount_paid",
    "payment_currency", "payment_format", "is_laundering",
]
TIMESTAMP_FORMAT = "%Y/%m/%d %H:%M"
CHUNK_SIZE = 500_000


def main():
    parser = argparse.ArgumentParser(description="Load CSV into SQLite.")
    parser.add_argument("--input", default="data/HI-Small_Trans.csv")
    parser.add_argument("--db", default="data/aml.db")
    args = parser.parse_args()

    input_path, db_path = Path(args.input), Path(args.db)
    if not input_path.exists():
        raise SystemExit(f"File not found: {input_path}. "
                         "See docs/dataset.md for download steps.")
    if db_path.exists():
        db_path.unlink()  # rebuild from scratch so reruns are repeatable

    con = sqlite3.connect(db_path)
    print(f"Loading {input_path} into {db_path} in chunks...")
    loaded = 0
    for chunk in pd.read_csv(
        input_path, header=0, names=COLUMN_NAMES, chunksize=CHUNK_SIZE,
        dtype={"from_account": "string", "to_account": "string"},
    ):
        parsed = pd.to_datetime(chunk["ts_text"], format=TIMESTAMP_FORMAT)
        epoch_seconds = (parsed - pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")
        chunk.insert(0, "ts", epoch_seconds.astype("int64"))
        chunk.to_sql("transactions", con, if_exists="append", index=False)
        loaded += len(chunk)
        print(f"  {loaded:,} rows loaded")

    print("Creating indexes...")
    con.executescript("""
        CREATE INDEX idx_from ON transactions (from_bank, from_account, ts);
        CREATE INDEX idx_to   ON transactions (to_bank, to_account, ts);
    """)
    start, end = con.execute(
        "SELECT datetime(MIN(ts), 'unixepoch'), datetime(MAX(ts), 'unixepoch') "
        "FROM transactions").fetchone()
    con.close()
    print(f"\nDone: {loaded:,} rows. Date range: {start} to {end}")


if __name__ == "__main__":
    main()
