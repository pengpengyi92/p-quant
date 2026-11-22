-- Exercise 1: full-period net return, MDD and turnover on the same path.
SELECT p.family, a.path_id, a.variant,
       ROUND(100*w.window_return, 2) AS full_return_pct,
       ROUND(100*a.max_drawdown, 2) AS max_drawdown_pct,
       ROUND(100*a.turnover_ex_open, 2) AS turnover_ex_open_pct
FROM path_audit a
JOIN paths p USING(path_id)
JOIN window_nav w USING(path_id, profile, variant)
WHERE a.profile='primary' AND w.window_id='full'
  AND a.path_id='combined-831901'
ORDER BY a.variant;

-- Exercise 2: match sector or industry buckets across variants within a seed.
WITH paired AS (
    SELECT p.family, t.path_id, t.level, t.bucket,
           t.net_pp-b.net_pp AS tiered_minus_binary_pp,
           t.commission_pp-b.commission_pp AS commission_gap_pp,
           t.slippage_pp-b.slippage_pp AS slippage_gap_pp
    FROM attribution_audit t
    JOIN attribution_audit b USING(path_id, profile, window_id, level, bucket)
    JOIN paths p USING(path_id)
    WHERE t.variant='tiered' AND b.variant='binary'
      AND t.profile='primary' AND t.window_id='full'
)
SELECT family, level, bucket, COUNT(*) AS paths,
       ROUND(AVG(tiered_minus_binary_pp), 4) AS mean_net_gap_pp,
       ROUND(AVG(commission_gap_pp), 4) AS mean_commission_gap_pp,
       ROUND(AVG(slippage_gap_pp), 4) AS mean_slippage_gap_pp
FROM paired GROUP BY family, level, bucket
ORDER BY family, level, bucket;

-- Exercise 3: independently reconstruct the commission and slippage paid at open.
SELECT fill_session,
       COUNT(*) AS fills,
       ROUND(SUM(ABS(signed_notional)), 2) AS traded_notional,
       ROUND(SUM(commission), 2) AS commission,
       ROUND(SUM(slippage), 2) AS slippage
FROM fills
WHERE path_id='gap_chain-831701' AND profile='primary' AND variant='tiered'
GROUP BY fill_session ORDER BY slippage DESC, fill_session LIMIT 5;
