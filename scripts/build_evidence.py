from pathlib import Path
import duckdb


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "analytics.duckdb"


if not DB.exists():
    raise SystemExit(
        "analytics.duckdb not found. Run build_db.py and build_metrics.py first."
    )


con = duckdb.connect(str(DB))

con.execute("PRAGMA threads=4")


# =========================================================
# Cleanup
# =========================================================

print("Dropping old evidence tables...")

for table in [
    "insight_evidence",
    "insight_methodology",
]:
    con.execute(f"DROP TABLE IF EXISTS {table}")


# =========================================================
# 1. Methodology
#
# This table makes every insight explainable.
# =========================================================

print("Building insight_methodology...")


con.execute(
    """
    CREATE TABLE insight_methodology AS

    SELECT
        'RECOVERY_OPPORTUNITY' AS insight_type,

        'فرصت بازیابی' AS title,

        'مجموع مبلغ Sessionهایی که اولین تلاش ناموفق داشته‌اند و هیچ تلاش موفقی بعد از آن ثبت نشده است.'
        AS definition,

        'SUM(amount)'
        AS formula,

        'merchant_key = پذیرنده AND unrecovered = TRUE'
        AS filters,

        'فقط Sessionهای دارای حداقل یک Attempt در نظر گرفته می‌شوند. مبلغ بر اساس amount همان Session محاسبه می‌شود.'
        AS notes

    UNION ALL

    SELECT
        'FIRST_ATTEMPT_GAP',

        'شکاف موفقیت در تلاش اول',

        'نسبت Sessionهایی که اولین تلاش پرداخت آن‌ها موفق بوده است به کل Sessionهای دارای Attempt.',

        'first_attempt_success_sessions / attempted_sessions',

        'merchant_key = پذیرنده',

        'این معیار با Final Success متفاوت است؛ پرداختی که بعداً با Retry موفق شده باشد، در First Attempt Success محسوب نمی‌شود.'

    UNION ALL

    SELECT
        'PEER_SUCCESS_GAP',

        'مقایسه با هم‌صنف‌ها',

        'جایگاه نرخ موفقیت نهایی پذیرنده نسبت به سایر پذیرندگان همان دسته‌بندی.',

        'PERCENT_RANK(final_success_rate) OVER category',

        'category_id = صنف پذیرنده',

        'برای کاهش اثر پذیرندگان بسیار بزرگ از Percent Rank استفاده شده است.'

    UNION ALL

    SELECT
        'HIGH_RETRY',

        'نرخ Retry بالا',

        'نسبت Sessionهایی که بیش از یک Attempt داشته‌اند به کل Sessionهای دارای Attempt.',

        'retried_sessions / attempted_sessions',

        'merchant_key = پذیرنده',

        'Retry به معنی چند تلاش برای یک Session است و نباید به عنوان چند مشتری یا چند خرید شمرده شود.'

    UNION ALL

    SELECT
        'NO_ATTEMPT',

        'Session بدون تلاش پرداخت',

        'نسبت Sessionهایی که ایجاد شده‌اند اما هیچ Attempt واقعی برای پرداخت آن‌ها ثبت نشده است.',

        'no_attempt_sessions / sessions',

        'merchant_key = پذیرنده',

        'try_seq = 0 به تنهایی به معنی پرداخت ناموفق نیست؛ این Sessionها در تحلیل جدا نگه داشته می‌شوند.'
    """
)


# =========================================================
# 2. Evidence
#
# One row per insight / merchant.
# =========================================================

print("Building insight_evidence...")


con.execute(
    """
    CREATE TABLE insight_evidence AS

    SELECT

        i.merchant_key,

        i.insight_type,

        i.severity,

        i.title,

        i.summary,

        i.recommendation,

        i.metric_name,

        i.metric_value,

        m.sessions,

        m.attempted_sessions,

        m.no_attempt_sessions,

        m.successful_sessions,

        m.first_success_sessions,

        m.recovered_sessions,

        m.unrecovered_sessions,

        m.retried_sessions,

        m.successful_volume,

        m.recovered_volume,

        m.unrecovered_volume,

        m.aov,

        m.final_success_rate,

        m.first_attempt_success_rate,

        m.recovery_rate,

        m.retry_rate,

        m.no_attempt_rate,

        m.first_seen_at,

        m.last_seen_at,

        p.success_rate_percentile,

        p.recovery_rate_percentile,

        p.aov_percentile,

        p.volume_percentile,

        md.definition,

        md.formula,

        md.filters,

        md.notes

    FROM insights i

    LEFT JOIN merchant_metrics m
        ON i.merchant_key = m.merchant_key

    LEFT JOIN peer_metrics p
        ON i.merchant_key = p.merchant_key

    LEFT JOIN insight_methodology md
        ON i.insight_type = md.insight_type
    """
)


# =========================================================
# 3. Evidence sessions
#
# Detailed rows used by the UI drill-down.
# =========================================================

print("Building evidence indexes...")


con.execute(
    """
    CREATE INDEX IF NOT EXISTS idx_evidence_merchant
    ON insight_evidence(merchant_key)
    """
)

con.execute(
    """
    CREATE INDEX IF NOT EXISTS idx_evidence_type
    ON insight_evidence(insight_type)
    """
)

con.execute(
    """
    CREATE INDEX IF NOT EXISTS idx_sessions_merchant_created
    ON sessions(merchant_key, created_at)
    """
)


# =========================================================
# 4. Validation
# =========================================================

print("")
print("Evidence validation...")
print("")


count = con.execute(
    "SELECT COUNT(*) FROM insight_evidence"
).fetchone()[0]

print(f"Evidence rows: {count:,}")


method_count = con.execute(
    "SELECT COUNT(*) FROM insight_methodology"
).fetchone()[0]

print(f"Methodology rows: {method_count:,}")


# =========================================================
# 5. Traceability sanity checks
# =========================================================

print("")
print("Traceability checks...")
print("")


# Recovery opportunity
recovery_check = con.execute(
    """
    SELECT

        COUNT(*) AS merchants,

        SUM(unrecovered_volume) AS total_unrecovered_volume,

        SUM(
            CASE
                WHEN metric_name = 'unrecovered_volume'
                THEN metric_value
                ELSE 0
            END
        ) AS total_metric_value

    FROM insight_evidence

    WHERE insight_type = 'RECOVERY_OPPORTUNITY'
    """
).fetchone()


print(
    "Recovery Opportunity:",
    f"{recovery_check[0]:,} insight rows"
)


# First attempt gap
first_check = con.execute(
    """
    SELECT
        COUNT(*),
        MIN(metric_value),
        MAX(metric_value)
    FROM insight_evidence

    WHERE insight_type = 'FIRST_ATTEMPT_GAP'
    """
).fetchone()


print(
    "First Attempt Gap:",
    f"{first_check[0]:,} insight rows"
)


# Peer
peer_check = con.execute(
    """
    SELECT
        COUNT(*),
        MIN(success_rate_percentile),
        MAX(success_rate_percentile)
    FROM insight_evidence

    WHERE insight_type = 'PEER_SUCCESS_GAP'
    """
).fetchone()


print(
    "Peer Success Gap:",
    f"{peer_check[0]:,} insight rows"
)


# =========================================================
# 6. Example evidence
# =========================================================

print("")
print("Example traceable insight:")
print("")


example = con.execute(
    """
    SELECT

        merchant_key,
        insight_type,
        severity,
        metric_name,
        metric_value,
        formula,
        filters

    FROM insight_evidence

    ORDER BY
        CASE severity
            WHEN 'critical' THEN 1
            WHEN 'warning' THEN 2
            ELSE 3
        END,
        metric_value DESC NULLS LAST

    LIMIT 1
    """
).fetchone()


if example:

    (
        merchant,
        insight_type,
        severity,
        metric_name,
        value,
        formula,
        filters,
    ) = example

    print(f"Merchant:    {merchant}")
    print(f"Insight:     {insight_type}")
    print(f"Severity:    {severity}")
    print(f"Metric:      {metric_name}")
    print(f"Value:       {value}")
    print(f"Formula:     {formula}")
    print(f"Filters:     {filters}")


# =========================================================
# Finish
# =========================================================

con.close()


print("")
print("--------------------------------------------")
print("Evidence Engine completed.")
print(f"Database: {DB}")
print("--------------------------------------------")