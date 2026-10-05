-- Rule: Dormant account reactivation
-- An account with no activity (sent or received) for a set number of days
-- suddenly moves a large amount. Limited to US Dollar amounts so the
-- dollar threshold is meaningful.
-- Parameters: {dormant_days}, {dormant_min_amount}

DROP TABLE IF EXISTS alerts_dormant_reactivation;

CREATE TABLE alerts_dormant_reactivation AS
WITH activity AS (
    SELECT from_bank AS bank, from_account AS account, ts, ts_text,
           amount_paid AS amount, payment_currency AS currency,
           'sent' AS direction, is_laundering
    FROM transactions
    UNION ALL
    SELECT to_bank, to_account, ts, ts_text,
           amount_received, receiving_currency,
           'received', is_laundering
    FROM transactions
),
with_gap AS (
    SELECT
        *,
        LAG(ts) OVER (PARTITION BY bank, account ORDER BY ts) AS prev_ts
    FROM activity
)
SELECT
    'dormant_reactivation' AS rule,
    bank,
    account,
    ts_text  AS alert_ts,
    amount,
    currency,
    printf('%.1f', (ts - prev_ts) / 86400.0) || ' days inactive, then '
        || direction AS detail,
    is_laundering
FROM with_gap
WHERE prev_ts IS NOT NULL
  AND ts - prev_ts >= {dormant_days} * 86400
  AND currency = 'US Dollar'
  AND amount >= {dormant_min_amount};
