from pathlib import Path
import duckdb


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "analytics.duckdb"


if not DB.exists():
    raise SystemExit(
        "analytics.duckdb not found. Run scripts/build_db.py first."
    )


con = duckdb.connect(str(DB))

con.execute("PRAGMA threads=4")


# =========================================================
# Cleanup
# =========================================================

print("Dropping old analytical tables...")

for table in [
    "merchant_metrics",
    "merchant_daily_metrics",
    "merchant_hourly_metrics",
    "merchant_amount_metrics",
    "merchant_psp_metrics",
    "peer_metrics",
    "insights",
]:
    con.execute(f"DROP TABLE IF EXISTS {table}")


# =========================================================
# 1. Merchant Metrics
# =========================================================

print("Building merchant_metrics...")


con.execute(
    """
    CREATE TABLE merchant_metrics AS

    SELECT

        merchant_key,

        MAX(category_id) AS category_id,
        MAX(category_title) AS category_title,

        COUNT(*) AS sessions,

        COUNT(*) FILTER (
            WHERE attempt_count > 0
        ) AS attempted_sessions,

        COUNT(*) FILTER (
            WHERE no_attempt
        ) AS no_attempt_sessions,

        COUNT(*) FILTER (
            WHERE final_success
        ) AS successful_sessions,

        COUNT(*) FILTER (
            WHERE first_attempt_success
        ) AS first_success_sessions,

        COUNT(*) FILTER (
            WHERE recovered
        ) AS recovered_sessions,

        COUNT(*) FILTER (
            WHERE unrecovered
        ) AS unrecovered_sessions,

        COUNT(*) FILTER (
            WHERE retried
        ) AS retried_sessions,


        -- -------------------------------------------------
        -- Revenue
        --
        -- Only successful sessions contribute to revenue.
        -- -------------------------------------------------

        SUM(
            CASE
                WHEN final_success THEN amount
                ELSE 0
            END
        ) AS successful_volume,


        SUM(
            CASE
                WHEN final_success THEN adjusted_fee
                ELSE 0
            END
        ) AS successful_fee,


        -- -------------------------------------------------
        -- Failed opportunity
        -- -------------------------------------------------

        SUM(
            CASE
                WHEN unrecovered THEN amount
                ELSE 0
            END
        ) AS unrecovered_volume,


        SUM(
            CASE
                WHEN recovered THEN amount
                ELSE 0
            END
        ) AS recovered_volume,


        -- -------------------------------------------------
        -- Average Order Value
        -- -------------------------------------------------

        AVG(
            CASE
                WHEN final_success THEN amount
                ELSE NULL
            END
        ) AS aov,


        -- -------------------------------------------------
        -- Rates
        -- -------------------------------------------------

        COUNT(*) FILTER (
            WHERE final_success
        ) * 1.0
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE attempt_count > 0
            ),
            0
        ) AS final_success_rate,


        COUNT(*) FILTER (
            WHERE first_attempt_success
        ) * 1.0
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE attempt_count > 0
            ),
            0
        ) AS first_attempt_success_rate,


        COUNT(*) FILTER (
            WHERE recovered
        ) * 1.0
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE
                    attempt_count > 0
                    AND first_attempt_success = FALSE
            ),
            0
        ) AS recovery_rate,


        COUNT(*) FILTER (
            WHERE retried
        ) * 1.0
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE attempt_count > 0
            ),
            0
        ) AS retry_rate,


        COUNT(*) FILTER (
            WHERE no_attempt
        ) * 1.0
        /
        NULLIF(COUNT(*), 0) AS no_attempt_rate,


        -- -------------------------------------------------
        -- Data period
        -- -------------------------------------------------

        MIN(created_at) AS first_seen_at,
        MAX(created_at) AS last_seen_at

    FROM sessions

    GROUP BY merchant_key
    """
)


# =========================================================
# 2. Daily Metrics
# =========================================================

print("Building merchant_daily_metrics...")


con.execute(
    """
    CREATE TABLE merchant_daily_metrics AS

    SELECT

        merchant_key,

        CAST(created_at AS DATE) AS metric_date,

        COUNT(*) AS sessions,

        COUNT(*) FILTER (
            WHERE attempt_count > 0
        ) AS attempted_sessions,

        COUNT(*) FILTER (
            WHERE final_success
        ) AS successful_sessions,

        COUNT(*) FILTER (
            WHERE recovered
        ) AS recovered_sessions,

        COUNT(*) FILTER (
            WHERE unrecovered
        ) AS unrecovered_sessions,

        SUM(
            CASE
                WHEN final_success THEN amount
                ELSE 0
            END
        ) AS successful_volume,

        SUM(
            CASE
                WHEN unrecovered THEN amount
                ELSE 0
            END
        ) AS lost_volume,

        AVG(
            CASE
                WHEN final_success THEN amount
            END
        ) AS aov,

        COUNT(*) FILTER (
            WHERE final_success
        ) * 1.0
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE attempt_count > 0
            ),
            0
        ) AS success_rate

    FROM sessions

    WHERE created_at IS NOT NULL

    GROUP BY
        merchant_key,
        CAST(created_at AS DATE)
    """
)


# =========================================================
# 3. Hourly Metrics
# =========================================================

print("Building merchant_hourly_metrics...")


con.execute(
    """
    CREATE TABLE merchant_hourly_metrics AS

    SELECT

        merchant_key,

        EXTRACT(HOUR FROM created_at) AS hour_of_day,

        COUNT(*) AS sessions,

        COUNT(*) FILTER (
            WHERE attempt_count > 0
        ) AS attempted_sessions,

        COUNT(*) FILTER (
            WHERE final_success
        ) AS successful_sessions,

        COUNT(*) FILTER (
            WHERE unrecovered
        ) AS unrecovered_sessions,

        SUM(
            CASE
                WHEN final_success THEN amount
                ELSE 0
            END
        ) AS successful_volume,

        SUM(
            CASE
                WHEN unrecovered THEN amount
                ELSE 0
            END
        ) AS lost_volume,

        COUNT(*) FILTER (
            WHERE final_success
        ) * 1.0
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE attempt_count > 0
            ),
            0
        ) AS success_rate

    FROM sessions

    WHERE created_at IS NOT NULL

    GROUP BY
        merchant_key,
        EXTRACT(HOUR FROM created_at)
    """
)


# =========================================================
# 4. Amount Buckets
# =========================================================

print("Building merchant_amount_metrics...")


con.execute(
    """
    CREATE TABLE merchant_amount_metrics AS

    WITH bucketed AS (

        SELECT

            merchant_key,

            CASE
                WHEN amount < 1000000
                    THEN '0-1M'

                WHEN amount < 5000000
                    THEN '1M-5M'

                WHEN amount < 10000000
                    THEN '5M-10M'

                WHEN amount < 50000000
                    THEN '10M-50M'

                ELSE '50M+'
            END AS amount_bucket,

            amount,
            attempt_count,
            final_success,
            first_attempt_success,
            recovered,
            unrecovered

        FROM sessions
    )

    SELECT

        merchant_key,

        amount_bucket,

        COUNT(*) AS sessions,

        COUNT(*) FILTER (
            WHERE attempt_count > 0
        ) AS attempted_sessions,

        COUNT(*) FILTER (
            WHERE final_success
        ) AS successful_sessions,

        COUNT(*) FILTER (
            WHERE recovered
        ) AS recovered_sessions,

        COUNT(*) FILTER (
            WHERE unrecovered
        ) AS unrecovered_sessions,

        SUM(
            CASE
                WHEN final_success THEN amount
                ELSE 0
            END
        ) AS successful_volume,

        SUM(
            CASE
                WHEN unrecovered THEN amount
                ELSE 0
            END
        ) AS lost_volume,

        COUNT(*) FILTER (
            WHERE final_success
        ) * 1.0
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE attempt_count > 0
            ),
            0
        ) AS success_rate

    FROM bucketed

    GROUP BY
        merchant_key,
        amount_bucket
    """
)


# =========================================================
# 5. PSP Metrics
# =========================================================

print("Building merchant_psp_metrics...")


con.execute(
    """
    CREATE TABLE merchant_psp_metrics AS

    SELECT

        merchant_key,

        last_psp_code AS psp_code,

        COUNT(*) AS sessions,

        COUNT(*) FILTER (
            WHERE final_success
        ) AS successful_sessions,

        COUNT(*) FILTER (
            WHERE unrecovered
        ) AS unrecovered_sessions,

        SUM(
            CASE
                WHEN final_success THEN amount
                ELSE 0
            END
        ) AS successful_volume,

        SUM(
            CASE
                WHEN unrecovered THEN amount
                ELSE 0
            END
        ) AS lost_volume,

        COUNT(*) FILTER (
            WHERE final_success
        ) * 1.0
        /
        NULLIF(COUNT(*), 0) AS success_rate

    FROM sessions

    WHERE
        attempt_count > 0
        AND last_psp_code IS NOT NULL
        AND last_psp_code <> ''

    GROUP BY
        merchant_key,
        last_psp_code
    """
)


# =========================================================
# 6. Peer Benchmark
#
# We use category-level peer groups.
#
# To avoid huge merchants dominating the benchmark,
# percentile-based metrics are used instead of averages
# wherever possible.
# =========================================================

print("Building peer_metrics...")


con.execute(
    """
    CREATE TABLE peer_metrics AS

    WITH base AS (

        SELECT

            m.*,

            PERCENT_RANK() OVER (
                PARTITION BY category_id
                ORDER BY final_success_rate
            ) AS success_rate_percentile,


            PERCENT_RANK() OVER (
                PARTITION BY category_id
                ORDER BY recovery_rate
            ) AS recovery_rate_percentile,


            PERCENT_RANK() OVER (
                PARTITION BY category_id
                ORDER BY aov
            ) AS aov_percentile,


            PERCENT_RANK() OVER (
                PARTITION BY category_id
                ORDER BY successful_volume
            ) AS volume_percentile

        FROM merchant_metrics m
    )

    SELECT *

    FROM base
    """
)


# =========================================================
# 7. Insights
# =========================================================

print("Building insights...")


con.execute(
    """
    CREATE TABLE insights AS

    WITH m AS (

        SELECT
            *
        FROM peer_metrics
    )

    -- -----------------------------------------------------
    -- Insight 1: Low first-attempt success
    -- -----------------------------------------------------

    SELECT

        merchant_key,

        'FIRST_ATTEMPT_GAP' AS insight_type,

        CASE
            WHEN first_attempt_success_rate < 0.40
                THEN 'critical'

            WHEN first_attempt_success_rate < 0.50
                THEN 'warning'

            ELSE 'info'
        END AS severity,


        'نرخ موفقیت تلاش اول پایین است' AS title,


        CONCAT(
            'تنها ',
            ROUND(first_attempt_success_rate * 100, 1),
            '٪ از پرداخت‌ها در اولین تلاش موفق شده‌اند.'
        ) AS summary,


        'بررسی مسیر پرداخت، PSP و خطاهای تلاش اول' AS recommendation,


        first_attempt_success_rate AS metric_value,


        'first_attempt_success_rate' AS metric_name,


        'merchant_metrics' AS source_table,


        merchant_key AS source_key


    FROM m

    WHERE
        attempted_sessions >= 100
        AND first_attempt_success_rate < 0.50


    UNION ALL


    -- -----------------------------------------------------
    -- Insight 2: Recovery opportunity
    -- -----------------------------------------------------

    SELECT

        merchant_key,

        'RECOVERY_OPPORTUNITY' AS insight_type,

        CASE
            WHEN unrecovered_volume >= 1000000000
                THEN 'critical'

            WHEN unrecovered_volume >= 250000000
                THEN 'warning'

            ELSE 'info'
        END AS severity,


        'بخشی از فروش در پرداخت ناموفق از دست می‌رود' AS title,


        CONCAT(
            'حدود ',
            ROUND(unrecovered_volume / 1000000, 1),
            ' میلیون ریال در Sessionهای بازیابی‌نشده قرار دارد.'
        ) AS summary,


        'روی Retry و مسیر بازیابی پرداخت‌های ناموفق تمرکز کنید.' AS recommendation,


        unrecovered_volume AS metric_value,


        'unrecovered_volume' AS metric_name,


        'merchant_metrics' AS source_table,


        merchant_key AS source_key


    FROM m

    WHERE
        attempted_sessions >= 100
        AND unrecovered_volume > 0


    UNION ALL


    -- -----------------------------------------------------
    -- Insight 3: Peer gap
    -- -----------------------------------------------------

    SELECT

        merchant_key,

        'PEER_SUCCESS_GAP' AS insight_type,

        CASE
            WHEN success_rate_percentile < 0.25
                THEN 'critical'

            WHEN success_rate_percentile < 0.50
                THEN 'warning'

            ELSE 'info'
        END AS severity,


        'عملکرد موفقیت پرداخت پایین‌تر از بخشی از هم‌صنف‌هاست' AS title,


        CONCAT(
            'این پذیرنده در صدک ',
            ROUND(success_rate_percentile * 100, 0),
            ' گروه هم‌صنف خود قرار دارد.'
        ) AS summary,


        'بررسی PSP، ساعت‌های کم‌عملکرد و مبالغ دارای افت موفقیت' AS recommendation,


        success_rate_percentile AS metric_value,


        'success_rate_percentile' AS metric_name,


        'peer_metrics' AS source_table,


        merchant_key AS source_key


    FROM m

    WHERE
        attempted_sessions >= 100
        AND success_rate_percentile < 0.50


    UNION ALL


    -- -----------------------------------------------------
    -- Insight 4: High retry
    -- -----------------------------------------------------

    SELECT

        merchant_key,

        'HIGH_RETRY' AS insight_type,

        'warning' AS severity,


        'تعداد قابل توجهی از پرداخت‌ها نیاز به تلاش مجدد دارند' AS title,


        CONCAT(
            'نرخ Retry برابر ',
            ROUND(retry_rate * 100, 1),
            '٪ است.'
        ) AS summary,


        'مسیر خطا و علت Retryهای متوالی را بررسی کنید.' AS recommendation,


        retry_rate AS metric_value,


        'retry_rate' AS metric_name,


        'merchant_metrics' AS source_table,


        merchant_key AS source_key


    FROM m

    WHERE
        attempted_sessions >= 100
        AND retry_rate >= 0.10


    UNION ALL


    -- -----------------------------------------------------
    -- Insight 5: No attempt
    -- -----------------------------------------------------

    SELECT

        merchant_key,

        'NO_ATTEMPT' AS insight_type,

        'info' AS severity,


        'بخشی از درخواست‌های پرداخت اصلاً به تلاش پرداخت نرسیده‌اند' AS title,


        CONCAT(
            ROUND(no_attempt_rate * 100, 1),
            '٪ از Sessionها بدون Attempt ثبت شده‌اند.'
        ) AS summary,


        'مسیر ایجاد درخواست پرداخت و نرخ تبدیل آن به Attempt را بررسی کنید.' AS recommendation,


        no_attempt_rate AS metric_value,


        'no_attempt_rate' AS metric_name,


        'merchant_metrics' AS source_table,


        merchant_key AS source_key


    FROM m

    WHERE
        sessions >= 100
        AND no_attempt_rate >= 0.10
    """
)


# =========================================================
# 8. Validation
# =========================================================

print("")
print("Running metrics validation...")
print("")


for table in [
    "merchant_metrics",
    "merchant_daily_metrics",
    "merchant_hourly_metrics",
    "merchant_amount_metrics",
    "merchant_psp_metrics",
    "peer_metrics",
    "insights",
]:

    count = con.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(f"{table:30} {count:,}")


# =========================================================
# Top Insights
# =========================================================

print("")
print("Top insight counts:")
print("")


rows = con.execute(
    """
    SELECT

        insight_type,

        severity,

        COUNT(*) AS merchants

    FROM insights

    GROUP BY
        insight_type,
        severity

    ORDER BY
        merchants DESC
    """
).fetchall()


for insight_type, severity, merchants in rows:

    print(
        f"{insight_type:28} "
        f"{severity:10} "
        f"{merchants:,}"
    )


# =========================================================
# Finish
# =========================================================

con.close()


print("")
print("--------------------------------------------")
print("Metrics & Insight Engine completed.")
print(f"Database: {DB}")
print("--------------------------------------------")