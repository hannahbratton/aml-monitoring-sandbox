# Detection Rules

Three rules written in SQL (SQLite) and run by `scripts/run_rules.py`. Thresholds are set in the `PARAMETERS` block of that script so they can be tuned in one place. Each alert records the rule, account, timestamp, amount, a plain-language detail, and the transaction's laundering label for evaluation.

## How to run

```
py scripts/load_db.py     # one time: loads the CSV into data/aml.db
py scripts/run_rules.py   # runs all rules, writes reports/detection_summary.md
```

## 1. Structuring

**File:** `sql/structuring.sql`

**Typology:** Splitting cash into amounts just under the $10,000 Currency Transaction Report (CTR) threshold to avoid reporting.

**Logic:** Selects US Dollar cash payments between the lower bound and $10,000, then counts how many each sending account made within a rolling window. Alerts when the count reaches the minimum.

| Parameter | Default | Meaning |
|---|---|---|
| struct_low_amount | 9,000 | Lower bound of the near-threshold band |
| struct_window_days | 7 | Rolling window length |
| struct_min_count | 2 | Payments in the window needed to alert |

**SQL technique:** window function with a time-based `RANGE` frame.

## 2. Rapid movement of funds

**File:** `sql/rapid_movement.sql`

**Typology:** Pass-through or mule activity, where an account receives funds and quickly sends most of them onward.

**Logic:** For each outgoing payment, finds the most recent incoming payment to the same account in the same currency. Alerts when the outgoing amount is close to the incoming amount and was sent within the window. Self-transfers are excluded.

| Parameter | Default | Meaning |
|---|---|---|
| rapid_window_hours | 12 | Maximum time between receiving and sending |
| rapid_min_ratio | 0.95 | Minimum share of the received amount sent out |
| rapid_max_ratio | 1.0 | Maximum share of the received amount sent out |

**SQL technique:** correlated subquery acting as an "as-of" join, supported by an index on account and time.

## 3. Dormant account reactivation

**File:** `sql/dormant_reactivation.sql`

**Typology:** An inactive account suddenly used to move a large amount, which can indicate account takeover or a purchased account.

**Logic:** Combines sent and received activity per account, measures the gap since the previous transaction, and alerts on large US Dollar transactions that follow a long gap.

| Parameter | Default | Meaning |
|---|---|---|
| dormant_days | 3 | Inactivity gap needed to count as dormant |
| dormant_min_amount | 5,000 | Minimum US Dollar amount to alert |

**SQL technique:** `UNION ALL` to combine both directions, then `LAG` to find the previous activity.

## Assumptions and limitations

- **Short date range.** The dataset covers only a few weeks, so the dormancy gap is set in days rather than the months used in practice. Real programs would use 90 days or more.
- **US Dollar only for dollar thresholds.** Structuring and dormant reactivation use US Dollar transactions only, so the dollar amounts mean the same thing in every alert. Rapid movement compares amounts within the same currency, so it covers all currencies.
- **Transaction-level alerts.** Each alert is one transaction. Production systems usually roll these up into account-level cases for investigators.
- **Baseline thresholds.** Defaults are starting points. Alert volume and hit rate are measured and tuned in the next issue.
