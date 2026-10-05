# Detection Summary

- **Run date:** 2026-10-04 23:22
- **Laundering-labeled transactions in dataset:** 5,177

## Alerts by rule

| Rule | Alerts | Unique accounts | Alerts on laundering-labeled transactions | Hit rate |
|---|---:|---:|---:|---:|
| structuring | 1,005 | 146 | 0 | 0.00% |
| rapid_movement | 30,035 | 11,561 | 91 | 0.30% |
| dormant_reactivation | 2,251 | 2,251 | 123 | 5.46% |

## Parameters

| Parameter | Value |
|---|---|
| struct_low_amount | 9000 |
| struct_window_days | 7 |
| struct_min_count | 2 |
| rapid_window_hours | 24 |
| rapid_min_ratio | 0.9 |
| rapid_max_ratio | 1.0 |
| dormant_days | 5 |
| dormant_min_amount | 5000 |

**Hit rate** = share of alerts on transactions the dataset labels as laundering. Rule logic is documented in docs/detection_rules.md.
