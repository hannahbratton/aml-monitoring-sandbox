-- Rule: Structuring
-- Repeated cash payments just below the $10,000 Currency Transaction Report
-- (CTR) threshold, from the same account within a rolling window.
-- Parameters: {struct_low_amount}, {struct_window_days}, {struct_min_count}

DROP TABLE IF EXISTS alerts_structuring;

CREATE TABLE alerts_structuring AS
WITH near_threshold AS (
    SELECT *
    FROM transactions
    WHERE payment_format = 'Cash'
      AND payment_currency = 'US Dollar'
      AND amount_paid >= {struct_low_amount}
      AND amount_paid < 10000
),
windowed AS (
    SELECT
        *,
        COUNT(*) OVER (
            PARTITION BY from_bank, from_account
            ORDER BY ts
            RANGE BETWEEN {struct_window_days} * 86400 PRECEDING AND CURRENT ROW
        ) AS txns_in_window
    FROM near_threshold
)
SELECT
    'structuring'     AS rule,
    from_bank         AS bank,
    from_account      AS account,
    ts_text           AS alert_ts,
    amount_paid       AS amount,
    payment_currency  AS currency,
    txns_in_window || ' near-threshold cash payments in '
        || {struct_window_days} || ' days' AS detail,
    is_laundering
FROM windowed
WHERE txns_in_window >= {struct_min_count};
