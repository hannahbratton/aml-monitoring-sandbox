# Threshold Tuning Results

- **Run date:** 2026-10-05 10:00
- **Laundering-labeled transactions:** 5,177
- **Base rate:** 0.102% (hit rate expected from random alerts)
- **Recommendation rule:** highest hit rate that keeps at least 90% of baseline hits

**Lift** = hit rate divided by the base rate. A lift of 10 means the rule's alerts are 10 times more likely to be laundering than a random transaction.

## rapid_movement

| rapid_window_hours | rapid_min_ratio | Alerts | Hits | Hit rate | Lift | Note |
|---|---|---:|---:|---:|---:|---|
| 24 | 0.9 | 30,035 | 91 | 0.30% | 3.0 |  |
| 24 | 0.95 | 14,568 | 53 | 0.36% | 3.6 |  |
| 12 | 0.9 | 20,353 | 65 | 0.32% | 3.1 |  |
| 12 | 0.95 | 9,883 | 42 | 0.42% | 4.2 | Baseline, **Recommended** |
| 6 | 0.9 | 12,319 | 36 | 0.29% | 2.9 |  |
| 6 | 0.95 | 5,986 | 24 | 0.40% | 3.9 |  |

Recommended vs. baseline: alerts 9,883 to 9,883 (+0%), hits 42 to 42, hit rate 0.42% to 0.42%.

## dormant_reactivation

| dormant_days | dormant_min_amount | Alerts | Hits | Hit rate | Lift | Note |
|---|---|---:|---:|---:|---:|---|
| 3 | 1000 | 23,176 | 376 | 1.62% | 15.9 |  |
| 3 | 5000 | 5,101 | 215 | 4.21% | 41.3 | Baseline, **Recommended** |
| 3 | 10000 | 3,689 | 142 | 3.85% | 37.8 |  |
| 5 | 1000 | 13,030 | 218 | 1.67% | 16.4 |  |
| 5 | 5000 | 2,251 | 123 | 5.46% | 53.6 |  |
| 5 | 10000 | 1,677 | 82 | 4.89% | 48.0 |  |
| 7 | 1000 | 5,871 | 112 | 1.91% | 18.7 |  |
| 7 | 5000 | 1,000 | 69 | 6.90% | 67.7 |  |
| 7 | 10000 | 759 | 43 | 5.67% | 55.6 |  |

Recommended vs. baseline: alerts 5,101 to 5,101 (+0%), hits 215 to 215, hit rate 4.21% to 4.21%.

## Structuring

Not tuned. The baseline produced no alerts on laundering-labeled transactions because the dataset's laundering patterns are network-based rather than sub-$10,000 cash structuring. The rule is kept as a control.
