from pathlib import Path
import duckdb


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

DB = ROOT / "data" / "analytics.duckdb"


def find_dataset():
    """Find the first supported challenge dataset in data/.

    DATA_FILE can be used to explicitly select a file. This keeps the project
    compatible with the challenge dataset regardless of its downloaded filename.
    """
    import os
    explicit = os.getenv("DATA_FILE")
    if explicit:
        path = Path(explicit)
        if not path.is_absolute():
            path = ROOT / path
        if path.exists():
            return path
        raise SystemExit(f"DATA_FILE does not exist: {path}")

    candidates = sorted(
        p for p in (ROOT / "data").iterdir()
        if p.is_file()
        and p.name != DB.name
        and p.suffix.lower() in {".csv", ".gz", ".parquet"}
    )
    # Prefer the conventional challenge filename if present.
    for name in ("challenge_data.csv.gz", "challenge_data.csv", "challenge_data.parquet"):
        preferred = ROOT / "data" / name
        if preferred.exists():
            return preferred
    if candidates:
        return candidates[0]
    raise SystemExit(
        "No dataset found in data/. Put the ZarinPal dataset there as CSV, CSV.GZ or Parquet."
    )


DATA = find_dataset()
print(f"Dataset: {DATA}")


# ---------------------------------------------------------
# Connect
# ---------------------------------------------------------

print("Opening DuckDB...")

con = duckdb.connect(str(DB))

con.execute("PRAGMA threads=4")


# ---------------------------------------------------------
# Clean previous tables
# ---------------------------------------------------------

print("Dropping old tables...")

con.execute("DROP TABLE IF EXISTS sessions")
con.execute("DROP TABLE IF EXISTS attempts")


# ---------------------------------------------------------
# 1. Raw Attempts
# ---------------------------------------------------------

reader = f"read_parquet('{DATA.as_posix()}')" if DATA.suffix.lower() == ".parquet" else f"read_csv_auto('{DATA.as_posix()}', header=true, sample_size=-1, ignore_errors=false)"

print(f"Loading attempts from {DATA.name}...")

con.execute(
    f"""
    CREATE TABLE attempts AS
    SELECT
        CAST(session_key AS VARCHAR) AS session_key,
        CAST(try_seq AS INTEGER) AS try_seq,

        CAST(terminal_key AS VARCHAR) AS terminal_key,
        CAST(merchant_key AS VARCHAR) AS merchant_key,

        CAST(category_id AS VARCHAR) AS category_id,
        category_title,

        CAST(amount AS DOUBLE) AS amount,
        CAST(adjusted_fee AS DOUBLE) AS adjusted_fee,

        session_status,
        try_status,

        switch_response_code,
        psp_code,
        issuer_bank_code,
        payer_card_key,
        verify_type,

        CAST(init_time_ms AS DOUBLE) AS init_time_ms,
        CAST(verify_time_ms AS DOUBLE) AS verify_time_ms,

        TRY_CAST(created_at AS TIMESTAMP) AS created_at,
        TRY_CAST(try_created_at AS TIMESTAMP) AS try_created_at,
        TRY_CAST(verified_at AS TIMESTAMP) AS verified_at,
        TRY_CAST(settled_at AS TIMESTAMP) AS settled_at,
        TRY_CAST(expire_in AS TIMESTAMP) AS expire_in

    FROM {reader};
    """
)


attempt_count = con.execute(
    "SELECT COUNT(*) FROM attempts"
).fetchone()[0]

print(f"Loaded {attempt_count:,} attempts.")


# ---------------------------------------------------------
# 2. Build Session-level table
#
# Important:
#
# A session can contain multiple attempts.
#
# Therefore:
#
# CSV row != payment
#
# session_key = payment session
#
# try_seq > 0 = actual payment attempt
#
# try_seq = 0 = no actual payment attempt
# ---------------------------------------------------------

print("Building session-level table...")


con.execute(
    """
    CREATE TABLE sessions AS

    WITH ranked AS (

        SELECT
            *,

            ROW_NUMBER() OVER (
                PARTITION BY session_key
                ORDER BY
                    try_seq ASC,
                    try_created_at ASC NULLS LAST,
                    created_at ASC NULLS LAST
            ) AS attempt_rank

        FROM attempts
    ),


    first_attempt AS (

        SELECT
            session_key,

            try_status AS first_try_status,
            psp_code AS first_psp_code,
            try_seq AS first_try_seq,
            try_created_at AS first_try_created_at

        FROM ranked

        WHERE try_seq > 0

        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY session_key
            ORDER BY
                try_seq ASC,
                try_created_at ASC NULLS LAST,
                created_at ASC NULLS LAST
        ) = 1
    ),


    session_agg AS (

        SELECT

            session_key,

            MAX(merchant_key) AS merchant_key,

            MAX(category_id) AS category_id,
            MAX(category_title) AS category_title,

            MAX(amount) AS amount,
            MAX(adjusted_fee) AS adjusted_fee,

            MAX(session_status) AS session_status,

            MIN(created_at) AS created_at,

            MIN(try_created_at)
                FILTER (WHERE try_seq > 0)
                AS first_attempt_at,

            MAX(try_created_at)
                FILTER (WHERE try_seq > 0)
                AS last_attempt_at,


            COUNT(*)
                FILTER (WHERE try_seq > 0)
                AS attempt_count,


            COUNT(DISTINCT psp_code)
                FILTER (
                    WHERE
                        try_seq > 0
                        AND psp_code IS NOT NULL
                        AND psp_code <> ''
                )
                AS psp_count,


            BOOL_OR(
                try_status IN ('Verified', 'Paid')
            )
            FILTER (WHERE try_seq > 0)
            AS any_success,


            BOOL_OR(
                try_status IN ('Verified', 'Paid')
            )
            FILTER (WHERE try_seq > 0 AND try_seq > 1)
            AS later_success,


            MAX(try_status)
                FILTER (WHERE try_seq > 0)
                AS last_attempt_status,


            MAX(psp_code)
                FILTER (WHERE try_seq > 0)
                AS last_psp_code


        FROM attempts

        GROUP BY session_key
    )


    SELECT

        s.*,

        f.first_try_status,
        f.first_psp_code,
        f.first_try_seq,
        f.first_try_created_at,


        -- ---------------------------------------------
        -- First Attempt Success
        -- ---------------------------------------------

        CASE
            WHEN f.first_try_status IN ('Verified', 'Paid')
                THEN TRUE
            ELSE FALSE
        END AS first_attempt_success,


        -- ---------------------------------------------
        -- Recovered
        --
        -- First attempt failed
        -- AND a later attempt succeeded
        -- ---------------------------------------------

        CASE
            WHEN
                f.first_try_status IS NOT NULL
                AND f.first_try_status NOT IN ('Verified', 'Paid')
                AND s.later_success = TRUE
            THEN TRUE

            ELSE FALSE
        END AS recovered,


        -- ---------------------------------------------
        -- Unrecovered
        --
        -- First attempt failed
        -- AND there was no successful attempt
        -- ---------------------------------------------

        CASE
            WHEN
                f.first_try_status IS NOT NULL
                AND f.first_try_status NOT IN ('Verified', 'Paid')
                AND COALESCE(s.any_success, FALSE) = FALSE
            THEN TRUE

            ELSE FALSE
        END AS unrecovered,


        -- ---------------------------------------------
        -- Retried
        -- ---------------------------------------------

        CASE
            WHEN s.attempt_count > 1
                THEN TRUE
            ELSE FALSE
        END AS retried,


        -- ---------------------------------------------
        -- No Attempt
        --
        -- Session exists but no real payment attempt
        -- ---------------------------------------------

        CASE
            WHEN s.attempt_count = 0
                THEN TRUE
            ELSE FALSE
        END AS no_attempt,


        -- ---------------------------------------------
        -- Final Success
        -- ---------------------------------------------

        CASE
            WHEN COALESCE(s.any_success, FALSE) = TRUE
                THEN TRUE
            ELSE FALSE
        END AS final_success


    FROM session_agg s

    LEFT JOIN first_attempt f
        ON s.session_key = f.session_key;
    """
)


session_count = con.execute(
    "SELECT COUNT(*) FROM sessions"
).fetchone()[0]

print(f"Built {session_count:,} sessions.")


# ---------------------------------------------------------
# 3. Indexes
# ---------------------------------------------------------

print("Creating indexes...")


con.execute(
    """
    CREATE INDEX IF NOT EXISTS idx_sessions_merchant
    ON sessions(merchant_key);
    """
)


con.execute(
    """
    CREATE INDEX IF NOT EXISTS idx_sessions_category
    ON sessions(category_id);
    """
)


con.execute(
    """
    CREATE INDEX IF NOT EXISTS idx_sessions_created_at
    ON sessions(created_at);
    """
)


con.execute(
    """
    CREATE INDEX IF NOT EXISTS idx_attempts_session
    ON attempts(session_key);
    """
)


# ---------------------------------------------------------
# 4. Validation
# ---------------------------------------------------------

print("")
print("Running validation...")
print("")


stats = con.execute(
    """
    SELECT

        COUNT(*) AS sessions,

        COUNT(*) FILTER (
            WHERE attempt_count > 0
        ) AS attempted_sessions,

        COUNT(*) FILTER (
            WHERE no_attempt = TRUE
        ) AS no_attempt_sessions,

        COUNT(*) FILTER (
            WHERE first_attempt_success = TRUE
        ) AS first_attempt_success_sessions,

        COUNT(*) FILTER (
            WHERE final_success = TRUE
        ) AS final_success_sessions,

        COUNT(*) FILTER (
            WHERE recovered = TRUE
        ) AS recovered_sessions,

        COUNT(*) FILTER (
            WHERE unrecovered = TRUE
        ) AS unrecovered_sessions,

        COUNT(*) FILTER (
            WHERE retried = TRUE
        ) AS retried_sessions

    FROM sessions
    """
).fetchone()


(
    total_sessions,
    attempted_sessions,
    no_attempt_sessions,
    first_success,
    final_success,
    recovered,
    unrecovered,
    retried,
) = stats


print(f"Total sessions:              {total_sessions:,}")
print(f"Attempted sessions:          {attempted_sessions:,}")
print(f"No-attempt sessions:         {no_attempt_sessions:,}")
print(f"First-attempt success:       {first_success:,}")
print(f"Final success:               {final_success:,}")
print(f"Recovered sessions:          {recovered:,}")
print(f"Unrecovered sessions:        {unrecovered:,}")
print(f"Retried sessions:            {retried:,}")


# ---------------------------------------------------------
# 5. Derived rates
# ---------------------------------------------------------

print("")
print("Derived rates:")
print("")


def pct(value, denominator):
    if denominator == 0:
        return 0.0

    return value / denominator * 100


print(
    f"Attempt coverage:            "
    f"{pct(attempted_sessions, total_sessions):.2f}%"
)


print(
    f"No-attempt rate:             "
    f"{pct(no_attempt_sessions, total_sessions):.2f}%"
)


print(
    f"First-attempt success:       "
    f"{pct(first_success, attempted_sessions):.2f}%"
)


print(
    f"Final success:               "
    f"{pct(final_success, attempted_sessions):.2f}%"
)


print(
    f"Retry rate:                  "
    f"{pct(retried, attempted_sessions):.2f}%"
)


failed_first = attempted_sessions - first_success

print(
    f"Recovery rate:               "
    f"{pct(recovered, failed_first):.2f}%"
    if failed_first > 0
    else "Recovery rate:               0.00%"
)


# ---------------------------------------------------------
# 6. Database summary
# ---------------------------------------------------------

print("")
print("--------------------------------------------")
print("Database successfully created.")
print(f"Location: {DB}")
print("--------------------------------------------")
print("")


con.close()