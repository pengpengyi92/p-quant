PRAGMA foreign_keys = ON;

CREATE TABLE assets (
    asset TEXT PRIMARY KEY,
    sector TEXT NOT NULL,
    industry TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE paths (
    path_id TEXT PRIMARY KEY,
    family TEXT NOT NULL,
    seed INTEGER NOT NULL UNIQUE,
    input_sha256 TEXT NOT NULL,
    shock_scale REAL NOT NULL,
    clock_shift INTEGER NOT NULL
) WITHOUT ROWID;

CREATE TABLE windows (
    path_id TEXT NOT NULL REFERENCES paths,
    window_id TEXT NOT NULL,
    start_session INTEGER NOT NULL CHECK(start_session > 0),
    end_session INTEGER NOT NULL CHECK(end_session >= start_session),
    PRIMARY KEY(path_id, window_id)
) WITHOUT ROWID;

CREATE TABLE nav (
    path_id TEXT NOT NULL REFERENCES paths,
    profile TEXT NOT NULL,
    variant TEXT NOT NULL,
    session INTEGER NOT NULL CHECK(session >= 0),
    close_nav REAL NOT NULL CHECK(close_nav > 0),
    PRIMARY KEY(path_id, profile, variant, session)
) WITHOUT ROWID;

CREATE TABLE marks (
    path_id TEXT NOT NULL,
    profile TEXT NOT NULL,
    variant TEXT NOT NULL,
    session INTEGER NOT NULL,
    asset TEXT NOT NULL REFERENCES assets,
    overnight_pnl REAL NOT NULL,
    gross_pnl REAL NOT NULL,
    PRIMARY KEY(path_id, profile, variant, session, asset),
    FOREIGN KEY(path_id, profile, variant, session) REFERENCES nav
) WITHOUT ROWID;

CREATE TABLE fills (
    path_id TEXT NOT NULL,
    profile TEXT NOT NULL,
    variant TEXT NOT NULL,
    fill_session INTEGER NOT NULL,
    asset TEXT NOT NULL REFERENCES assets,
    decision_session INTEGER NOT NULL CHECK(decision_session + 1 = fill_session),
    signed_notional REAL NOT NULL,
    commission REAL NOT NULL CHECK(commission >= 0),
    slippage REAL NOT NULL CHECK(slippage >= 0),
    PRIMARY KEY(path_id, profile, variant, fill_session, asset),
    FOREIGN KEY(path_id, profile, variant, fill_session, asset) REFERENCES marks
) WITHOUT ROWID;

CREATE VIEW session_audit AS
WITH close_clock AS (
    SELECT *, LAG(close_nav) OVER w AS prior_close,
           MAX(close_nav) OVER w AS peak,
           FIRST_VALUE(close_nav) OVER w AS initial_nav
    FROM nav WINDOW w AS (
        PARTITION BY path_id, profile, variant ORDER BY session
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )
), overnight AS (
    SELECT path_id, profile, variant, session, SUM(overnight_pnl) AS gap_pnl
    FROM marks GROUP BY path_id, profile, variant, session
), execution AS (
    SELECT path_id, profile, variant, fill_session AS session,
           SUM(ABS(signed_notional)) AS gross_notional,
           SUM(commission) AS commission, SUM(slippage) AS slippage
    FROM fills GROUP BY path_id, profile, variant, fill_session
)
SELECT c.path_id, c.profile, c.variant, c.session, c.close_nav, c.initial_nav,
       c.close_nav / c.peak - 1.0 AS drawdown,
       COALESCE(e.gross_notional, 0.0)
           / (c.prior_close + COALESCE(o.gap_pnl, 0.0)) AS gross_turnover,
       COALESCE(e.commission, 0.0) AS commission,
       COALESCE(e.slippage, 0.0) AS slippage
FROM close_clock c LEFT JOIN overnight o USING(path_id, profile, variant, session)
LEFT JOIN execution e USING(path_id, profile, variant, session);

CREATE VIEW path_audit AS
SELECT path_id, profile, variant,
       MIN(drawdown) AS max_drawdown,
       SUM(CASE WHEN session > 1 THEN gross_turnover ELSE 0 END) AS turnover_ex_open,
       SUM(commission) AS commission, SUM(slippage) AS slippage
FROM session_audit
GROUP BY path_id, profile, variant;

CREATE VIEW window_nav AS
SELECT w.path_id, b.profile, b.variant, w.window_id, w.start_session, w.end_session,
       b.close_nav AS opening_nav, e.close_nav AS ending_nav,
       e.close_nav / b.close_nav - 1.0 AS window_return
FROM windows w
JOIN nav b ON b.path_id=w.path_id AND b.session=w.start_session-1
JOIN nav e ON e.path_id=w.path_id AND e.profile=b.profile AND e.variant=b.variant
          AND e.session=w.end_session;

CREATE VIEW attribution_audit AS
WITH legs AS (
    SELECT w.path_id, w.profile, w.variant, w.window_id, w.opening_nav,
           a.sector, a.industry, m.gross_pnl,
           COALESCE(f.commission, 0.0) AS commission,
           COALESCE(f.slippage, 0.0) AS slippage
    FROM window_nav w
    JOIN marks m ON m.path_id=w.path_id AND m.profile=w.profile AND m.variant=w.variant
                AND m.session BETWEEN w.start_session AND w.end_session
    JOIN assets a ON a.asset=m.asset
    LEFT JOIN fills f ON f.path_id=m.path_id AND f.profile=m.profile AND f.variant=m.variant
                     AND f.fill_session=m.session AND f.asset=m.asset
), groups AS (
    SELECT *, 'sector' AS level, sector AS bucket FROM legs
    UNION ALL
    SELECT *, 'industry' AS level, sector || ' / ' || industry AS bucket FROM legs
)
SELECT path_id, profile, variant, window_id, level, bucket,
       SUM(gross_pnl)*100.0 / opening_nav AS gross_pp,
       SUM(commission)*100.0 / opening_nav AS commission_pp,
       SUM(slippage)*100.0 / opening_nav AS slippage_pp,
       SUM(gross_pnl-commission-slippage)*100.0 / opening_nav AS net_pp
FROM groups
GROUP BY path_id, profile, variant, window_id, level, bucket;
