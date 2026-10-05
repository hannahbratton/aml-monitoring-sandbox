-- Rule: Rapid movement of funds (pass-through)
-- An account sends out most of a payment it just received, in the same
-- currency, within a short window. For each outgoing payment, the query finds
-- the most recent incoming payment to the same account (an "as-of" match).
-- Parameters: {rapid_window_hours}, {rapid_min_ratio}, {rapid_max_ratio}

DROP TABLE IF EXISTS temp.inbound;
DROP TABLE IF EXISTS alerts_rapid_movement;

-- Incoming payments, excluding self-transfers
CREATE TEMP TABLE inbound AS
SELECT to_bank AS bank, to_account AS account, receiving_currency AS currency,
       ts, ts_text, amount_received AS amount
FROM transactions
WHERE NOT (from_bank = to_bank AND from_account = to_account);

CREATE INDEX temp.idx_inbound ON inbound (bank, account, currency, ts);

CREATE TABLE alerts_rapid_movement AS
WITH outbound AS (
    SELECT from_bank AS bank, from_account AS account,
           payment_currency AS currency, ts, ts_text,
           amount_paid AS amount, is_laundering
    FROM transactions
    WHERE NOT (from_bank = to_bank AND from_account = to_account)
),
matched AS (
    SELECT
        o.*,
        (SELECT i.rowid
         FROM inbound i
         WHERE i.bank = o.bank
           AND i.account = o.account
           AND i.currency = o.currency
           AND i.ts <= o.ts
         ORDER BY i.ts DESC
         LIMIT 1) AS inbound_id
    FROM outbound o
)
SELECT
    'rapid_movement'  AS rule,
    m.bank,
    m.account,
    m.ts_text         AS alert_ts,
    m.amount,
    m.currency,
    'Received ' || printf('%.2f', i.amount) || ' at ' || i.ts_text
        || ', sent ' || printf('%.0f', 100.0 * m.amount / i.amount)
        || '% within ' || ((m.ts - i.ts) / 3600) || 'h' AS detail,
    m.is_laundering
FROM matched m
JOIN inbound i ON i.rowid = m.inbound_id
WHERE i.amount > 0
  AND m.ts - i.ts <= {rapid_window_hours} * 3600
  AND m.amount BETWEEN i.amount * {rapid_min_ratio}
                   AND i.amount * {rapid_max_ratio};
