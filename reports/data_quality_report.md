# Data Quality Report

- **Source file:** `data\HI-Small_Trans.csv`
- **Run date:** 2026-10-04 22:55
- **Rows:** 5,078,345
- **Columns:** 11
- **Date range:** 2022-09-01 to 2022-09-18
- **Laundering rate:** 0.1019%
- **Checks flagged:** 1 of 22

## Results

| Check | Count | % of rows | Status | Note |
|---|---:|---:|---|---|
| Missing expected columns | 0 | 0.00% | PASS |  |
| Unexpected columns | 0 | 0.00% | PASS |  |
| Nulls in 'Timestamp' | 0 | 0.00% | PASS |  |
| Nulls in 'From Bank' | 0 | 0.00% | PASS |  |
| Nulls in 'Account' | 0 | 0.00% | PASS |  |
| Nulls in 'To Bank' | 0 | 0.00% | PASS |  |
| Nulls in 'Account.1' | 0 | 0.00% | PASS |  |
| Nulls in 'Amount Received' | 0 | 0.00% | PASS |  |
| Nulls in 'Receiving Currency' | 0 | 0.00% | PASS |  |
| Nulls in 'Amount Paid' | 0 | 0.00% | PASS |  |
| Nulls in 'Payment Currency' | 0 | 0.00% | PASS |  |
| Nulls in 'Payment Format' | 0 | 0.00% | PASS |  |
| Nulls in 'Is Laundering' | 0 | 0.00% | PASS |  |
| Exact duplicate rows | 9 | 0.00% | FLAG |  |
| Non-numeric 'Amount Received' | 0 | 0.00% | PASS |  |
| Negative 'Amount Received' | 0 | 0.00% | PASS |  |
| Zero 'Amount Received' | 0 | 0.00% | PASS |  |
| Non-numeric 'Amount Paid' | 0 | 0.00% | PASS |  |
| Negative 'Amount Paid' | 0 | 0.00% | PASS |  |
| Zero 'Amount Paid' | 0 | 0.00% | PASS |  |
| Unparseable timestamps | 0 | 0.00% | PASS |  |
| Labels other than 0/1 | 0 | 0.00% | PASS |  |
| Self-transfers (same sender and receiver) | 591,212 | 11.64% | INFO | Expected in this dataset; review before rule design |
| Cross-currency transactions | 72,170 | 1.42% | INFO | Amount Paid and Amount Received differ in currency |

**Status key:** PASS = no issues found; FLAG = issues found, review before detection; INFO = expected pattern, documented for context.
