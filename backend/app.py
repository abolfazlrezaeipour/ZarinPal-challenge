from pathlib import Path
from typing import Optional, Any
import json
import os
from datetime import date, datetime
from decimal import Decimal

import duckdb
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from dotenv import load_dotenv

load_dotenv(
    os.path.join(
        os.path.dirname(__file__),
        ".env"
    ),
    override=True
)
# =========================================================
# Environment / paths
# =========================================================

BACKEND_DIR = Path(__file__).resolve().parent
ROOT = BACKEND_DIR.parent

# Load backend/.env first, then project/.env if it exists.
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(ROOT / ".env")

DB_PATH = Path(
    os.getenv("ZP_DB_PATH", "../data/analytics.duckdb")
)

if not DB_PATH.is_absolute():
    DB_PATH = (BACKEND_DIR / DB_PATH).resolve()


# =========================================================
# App
# =========================================================

app = FastAPI(
    title="ZarinPal Insight API",
    version="2.0.0",
    description="Evidence-backed analytical API for ZarinPal merchants",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Models
# =========================================================

class AskRequest(BaseModel):
    question: str


# =========================================================
# Serialization helpers
# =========================================================

def json_safe(value: Any):
    """Convert DuckDB/Python values to JSON-safe values."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def json_text(value: Any) -> str:
    return json.dumps(
        json_safe(value),
        ensure_ascii=False,
        indent=2,
    )


# =========================================================
# Database
# =========================================================

def ensure_database():
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail=f"DuckDB database not found: {DB_PATH}",
        )


def query(sql: str, params=None):
    ensure_database()

    con = duckdb.connect(str(DB_PATH), read_only=True)

    try:
        result = con.execute(sql, params or [])
        columns = [d[0] for d in result.description]
        rows = result.fetchall()

        return [
            json_safe(dict(zip(columns, row)))
            for row in rows
        ]
    finally:
        con.close()


def query_one(sql: str, params=None):
    rows = query(sql, params)
    return rows[0] if rows else None


def table_exists(table_name: str) -> bool:
    ensure_database()

    row = query_one(
        """
        SELECT COUNT(*) AS n
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_name = ?
        """,
        [table_name],
    )

    return bool(row and row["n"])


def table_columns(table_name: str):
    if not table_exists(table_name):
        return []

    rows = query(
        f'DESCRIBE "{table_name}"'
    )

    return [r["column_name"] for r in rows]


# =========================================================
# Root / health
# =========================================================

@app.get("/")
def root():
    return {
        "name": "ZarinPal Insight API",
        "version": "2.0.0",
        "status": "ok",
        "database": str(DB_PATH),
    }


@app.get("/api/health")
def health():
    ensure_database()

    merchants_count = (
        query_one("SELECT COUNT(*) AS n FROM merchant_metrics")
        if table_exists("merchant_metrics")
        else {"n": 0}
    )

    return {
        "status": "ok",
        "database": str(DB_PATH),
        "database_exists": DB_PATH.exists(),
        "merchants": int(merchants_count["n"] or 0),
        "llm_sdk_installed": OpenAI is not None,
        "llm_provider": "AvalAI",
        "llm_base_url": os.getenv(
            "OPENAI_BASE_URL",
            "https://api.avalai.ir/v1",
        ),
        "llm_model": os.getenv(
            "OPENAI_MODEL",
            "gpt-5.5",
        ),
        "api_key_configured": bool(
            os.getenv("AVALAI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        ),
    }


# =========================================================
# Merchants
# =========================================================

@app.get("/api/merchants")
def merchants(
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
):
    if search:
        return query(
            """
            SELECT
                merchant_key,
                sessions,
                successful_sessions,
                final_success_rate,
                successful_volume,
                aov
            FROM merchant_metrics
            WHERE merchant_key ILIKE ?
            ORDER BY successful_volume DESC
            LIMIT ?
            """,
            [f"%{search}%", limit],
        )

    return query(
        """
        SELECT
            merchant_key,
            sessions,
            successful_sessions,
            final_success_rate,
            successful_volume,
            aov
        FROM merchant_metrics
        ORDER BY successful_volume DESC
        LIMIT ?
        """,
        [limit],
    )


# =========================================================
# Merchant overview
# =========================================================

@app.get("/api/merchants/{merchant_id}/overview")
def merchant_overview(merchant_id: str):
    merchant = query_one(
        """
        SELECT *
        FROM merchant_metrics
        WHERE merchant_key = ?
        """,
        [merchant_id],
    )

    if not merchant:
        raise HTTPException(
            status_code=404,
            detail="Merchant not found",
        )

    peer = query_one(
        """
        SELECT *
        FROM peer_metrics
        WHERE merchant_key = ?
        """,
        [merchant_id],
    ) if table_exists("peer_metrics") else None

    return {
        "merchant": merchant,
        "peer": peer,
    }


# =========================================================
# Merchant insights
# =========================================================

@app.get("/api/merchants/{merchant_id}/insights")
def merchant_insights(
    merchant_id: str,
    severity: Optional[str] = None,
):
    params = [merchant_id]

    sql = """
        SELECT *
        FROM insight_evidence
        WHERE merchant_key = ?
    """

    if severity:
        sql += " AND severity = ?"
        params.append(severity)

    sql += """
        ORDER BY
            CASE severity
                WHEN 'critical' THEN 1
                WHEN 'warning' THEN 2
                WHEN 'info' THEN 3
                ELSE 4
            END,
            metric_value DESC NULLS LAST
    """

    return query(sql, params)


# =========================================================
# Daily metrics
# =========================================================

@app.get("/api/merchants/{merchant_id}/daily")
def merchant_daily(
    merchant_id: str,
    limit: int = Query(default=180, ge=1, le=1000),
):
    # SELECT * is intentional: the project DB calls the lost amount
    # "lost_volume", not "unrecovered_volume".
    return query(
        """
        SELECT *
        FROM merchant_daily_metrics
        WHERE merchant_key = ?
        ORDER BY metric_date
        LIMIT ?
        """,
        [merchant_id, limit],
    )


# =========================================================
# Hourly metrics
# =========================================================

@app.get("/api/merchants/{merchant_id}/hourly")
def merchant_hourly(merchant_id: str):
    # The real schema uses hour_of_day.
    return query(
        """
        SELECT *
        FROM merchant_hourly_metrics
        WHERE merchant_key = ?
        ORDER BY hour_of_day
        """,
        [merchant_id],
    )


# =========================================================
# Amount distribution
# =========================================================

@app.get("/api/merchants/{merchant_id}/amounts")
def merchant_amounts(merchant_id: str):
    return query(
        """
        SELECT *
        FROM merchant_amount_metrics
        WHERE merchant_key = ?
        ORDER BY amount_bucket
        """,
        [merchant_id],
    )


# =========================================================
# PSP performance
# =========================================================

@app.get("/api/merchants/{merchant_id}/psps")
def merchant_psps(merchant_id: str):
    # The real metric table uses success_rate, not final_success_rate.
    return query(
        """
        SELECT *
        FROM merchant_psp_metrics
        WHERE merchant_key = ?
        ORDER BY success_rate DESC NULLS LAST
        """,
        [merchant_id],
    )


# =========================================================
# Insight detail
# =========================================================

@app.get("/api/insights/{merchant_id}/{insight_type}")
def insight_detail(
    merchant_id: str,
    insight_type: str,
):
    insight = query_one(
        """
        SELECT *
        FROM insight_evidence
        WHERE merchant_key = ?
          AND insight_type = ?
        ORDER BY
            CASE severity
                WHEN 'critical' THEN 1
                WHEN 'warning' THEN 2
                ELSE 3
            END
        LIMIT 1
        """,
        [merchant_id, insight_type],
    )

    if not insight:
        raise HTTPException(
            status_code=404,
            detail="Insight not found",
        )

    methodology = query_one(
        """
        SELECT *
        FROM insight_methodology
        WHERE insight_type = ?
        """,
        [insight_type],
    )

    return {
        "insight": insight,
        "methodology": methodology,
    }


# =========================================================
# Evidence sessions
# =========================================================

@app.get("/api/insights/{merchant_id}/{insight_type}/sessions")
def insight_sessions(
    merchant_id: str,
    insight_type: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    base_columns = """
        session_key,
        merchant_key,
        amount,
        attempt_count,
        session_status,
        first_try_status,
        last_attempt_status,
        first_attempt_at,
        last_attempt_at,
        created_at,
        final_success,
        recovered,
        unrecovered,
        retried,
        no_attempt
    """

    if insight_type == "RECOVERY_OPPORTUNITY":
        condition = "AND unrecovered = TRUE"
        order_by = "amount DESC"

    elif insight_type == "NO_ATTEMPT":
        condition = "AND no_attempt = TRUE"
        order_by = "amount DESC"

    elif insight_type == "HIGH_RETRY":
        condition = "AND retried = TRUE"
        order_by = "attempt_count DESC, amount DESC"

    else:
        condition = ""
        order_by = "created_at DESC"

    return query(
        f"""
        SELECT {base_columns}
        FROM sessions
        WHERE merchant_key = ?
        {condition}
        ORDER BY {order_by}
        LIMIT ? OFFSET ?
        """,
        [merchant_id, limit, offset],
    )


# =========================================================
# Session detail
# =========================================================

@app.get("/api/sessions/{session_key}")
def session_detail(session_key: str):
    session = query_one(
        """
        SELECT *
        FROM sessions
        WHERE session_key = ?
        """,
        [session_key],
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    attempts = query(
        """
        SELECT *
        FROM attempts
        WHERE session_key = ?
        ORDER BY try_seq
        """,
        [session_key],
    )

    return {
        "session": session,
        "attempts": attempts,
    }


# =========================================================
# Peer comparison
# =========================================================

@app.get("/api/merchants/{merchant_id}/peers")
def merchant_peers(merchant_id: str):
    merchant = query_one(
        """
        SELECT category_id
        FROM merchant_metrics
        WHERE merchant_key = ?
        """,
        [merchant_id],
    )

    if not merchant:
        raise HTTPException(
            status_code=404,
            detail="Merchant not found",
        )

    return query(
        """
        SELECT
            m.merchant_key,
            m.sessions,
            m.successful_volume,
            m.aov,
            m.final_success_rate,
            p.success_rate_percentile,
            p.volume_percentile,
            p.aov_percentile
        FROM merchant_metrics m
        LEFT JOIN peer_metrics p
            ON m.merchant_key = p.merchant_key
        WHERE m.category_id = ?
        ORDER BY m.final_success_rate DESC NULLS LAST
        LIMIT 50
        """,
        [merchant["category_id"]],
    )


# =========================================================
# Global stats
# =========================================================

@app.get("/api/stats")
def stats():
    return query_one(
        """
        SELECT
            COUNT(*) AS merchants,
            SUM(sessions) AS sessions,
            SUM(attempted_sessions) AS attempted_sessions,
            SUM(no_attempt_sessions) AS no_attempt_sessions,
            SUM(successful_sessions) AS successful_sessions,
            SUM(recovered_sessions) AS recovered_sessions,
            SUM(unrecovered_sessions) AS unrecovered_sessions,
            SUM(retried_sessions) AS retried_sessions,
            SUM(successful_volume) AS successful_volume,
            SUM(unrecovered_volume) AS unrecovered_volume
        FROM merchant_metrics
        """
    )


# =========================================================
# Customer analytics
# =========================================================

@app.get("/api/merchants/{merchant_id}/customers")
def merchant_customers(merchant_id: str):
    rows = query(
        """
        WITH c AS (
            SELECT
                payer_card_key,
                COUNT(DISTINCT session_key) AS orders,
                SUM(
                    CASE
                        WHEN try_status IN ('Verified', 'Paid')
                        THEN amount
                        ELSE 0
                    END
                ) AS spend,
                MIN(created_at) AS first_seen,
                MAX(created_at) AS last_seen
            FROM attempts
            WHERE merchant_key = ?
              AND payer_card_key IS NOT NULL
              AND payer_card_key <> ''
            GROUP BY payer_card_key
        )
        SELECT
            COUNT(*) AS customers,
            COUNT(*) FILTER (WHERE orders > 1) AS repeat_customers,
            AVG(orders) AS avg_orders,
            SUM(spend) AS customer_spend,
            COUNT(*) FILTER (WHERE orders >= 5) AS vip,
            COUNT(*) FILTER (WHERE orders BETWEEN 2 AND 4) AS loyal,
            COUNT(*) FILTER (WHERE orders = 1) AS new_customers
        FROM c
        """,
        [merchant_id],
    )

    r = rows[0] if rows else {}

    customers = int(r.get("customers") or 0)
    repeat = int(r.get("repeat_customers") or 0)

    return {
        **r,
        "customers": customers,
        "repeat_customers": repeat,
        "repeat_rate": (repeat / customers * 100) if customers else 0,
        "avg_orders": float(r.get("avg_orders") or 0),
        "vip": int(r.get("vip") or 0),
        "loyal": int(r.get("loyal") or 0),
        "new_customers": int(r.get("new_customers") or 0),
    }


# =========================================================
# Transaction/session explorer
# =========================================================

@app.get("/api/merchants/{merchant_id}/sessions")
def merchant_sessions(
    merchant_id: str,
    search: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    params = [merchant_id]
    where = "WHERE merchant_key = ?"

    if search:
        where += " AND CAST(session_key AS VARCHAR) ILIKE ?"
        params.append(f"%{search}%")

    if status in {
        "success",
        "failed",
        "recovered",
        "retry",
        "no_attempt",
    }:
        mapping = {
            "success": "final_success = TRUE",
            "failed": "unrecovered = TRUE",
            "recovered": "recovered = TRUE",
            "retry": "retried = TRUE",
            "no_attempt": "no_attempt = TRUE",
        }

        where += " AND " + mapping[status]

    count = query_one(
        f"SELECT COUNT(*) AS total FROM sessions {where}",
        params,
    )

    rows = query(
        f"""
        SELECT
            session_key,
            amount,
            attempt_count,
            session_status,
            first_try_status,
            last_attempt_status,
            first_attempt_at,
            last_attempt_at,
            created_at,
            final_success,
            recovered,
            unrecovered,
            retried,
            no_attempt,
            last_psp_code
        FROM sessions
        {where}
        ORDER BY created_at DESC NULLS LAST
        LIMIT ? OFFSET ?
        """,
        params + [limit, offset],
    )

    return {
        "items": rows,
        "total": int(count["total"] if count else 0),
        "limit": limit,
        "offset": offset,
    }


# =========================================================
# Calendar analytics
# =========================================================

@app.get("/api/merchants/{merchant_id}/calendar")
def merchant_calendar(merchant_id: str):
    return query(
        """
        SELECT
            EXTRACT(DOW FROM created_at) AS weekday,
            EXTRACT(MONTH FROM created_at) AS month,
            COUNT(*) AS sessions,
            COUNT(*) FILTER (WHERE final_success)
                AS successful_sessions,
            SUM(
                CASE WHEN final_success THEN amount ELSE 0 END
            ) AS successful_volume,
            SUM(
                CASE WHEN unrecovered THEN amount ELSE 0 END
            ) AS lost_volume,
            AVG(
                CASE WHEN final_success THEN amount END
            ) AS aov,
            COUNT(*) FILTER (WHERE final_success) * 1.0 /
                NULLIF(
                    COUNT(*) FILTER (WHERE attempt_count > 0),
                    0
                ) AS success_rate
        FROM sessions
        WHERE merchant_key = ?
          AND created_at IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 2, 1
        """,
        [merchant_id],
    )

# =========================================================
# Seasonality analytics
# =========================================================

@app.get("/api/merchants/{merchant_id}/seasonality")
def merchant_seasonality(merchant_id: str):

    rows = query(
        """
        SELECT
            EXTRACT(MONTH FROM created_at)::INTEGER AS month,

            COUNT(*) AS sessions,

            COUNT(*) FILTER (
                WHERE final_success
            ) AS successful_sessions,

            SUM(
                CASE
                    WHEN final_success
                    THEN amount
                    ELSE 0
                END
            ) AS successful_volume,

            COUNT(*) FILTER (
                WHERE final_success
            ) * 1.0 /
            NULLIF(
                COUNT(*) FILTER (
                    WHERE attempt_count > 0
                ),
                0
            ) AS success_rate

        FROM sessions

        WHERE merchant_key = ?
        AND created_at IS NOT NULL

        GROUP BY 1

        ORDER BY 1
        """,
        [merchant_id],
    )


    weekday = query(
        """
        SELECT

            EXTRACT(DOW FROM created_at)::INTEGER AS weekday,

            COUNT(*) AS sessions,

            COUNT(*) FILTER(
                WHERE final_success
            ) AS successful_sessions,


            SUM(
                CASE
                    WHEN final_success
                    THEN amount
                    ELSE 0
                END
            ) AS successful_volume,


            COUNT(*) FILTER(
                WHERE final_success
            ) * 1.0 /
            NULLIF(
                COUNT(*) FILTER(
                    WHERE attempt_count > 0
                ),
                0
            ) AS success_rate


        FROM sessions

        WHERE merchant_key = ?
        AND created_at IS NOT NULL


        GROUP BY 1

        ORDER BY 1

        """,
        [merchant_id],
    )


    return {
        "monthly": rows,
        "weekday": weekday
    }
# =========================================================
# Health score
# =========================================================

@app.get("/api/merchants/{merchant_id}/health-score")
def merchant_health(merchant_id: str):
    m = query_one(
        "SELECT * FROM merchant_metrics WHERE merchant_key = ?",
        [merchant_id],
    )

    p = query_one(
        "SELECT * FROM peer_metrics WHERE merchant_key = ?",
        [merchant_id],
    )

    if not m:
        raise HTTPException(
            status_code=404,
            detail="Merchant not found",
        )

    success = float(m.get("final_success_rate") or 0)
    recovery = float(m.get("recovery_rate") or 0)
    retry = float(m.get("retry_rate") or 0)
    no_attempt = float(m.get("no_attempt_rate") or 0)

    score = max(
        0,
        min(
            100,
            success * 70
            + recovery * 10
            + max(0, 1 - retry) * 10
            + max(0, 1 - no_attempt) * 10,
        ),
    )

    return {
        "score": round(score, 1),
        "status": (
            "عالی"
            if score >= 85
            else "خوب"
            if score >= 70
            else "نیازمند توجه"
        ),
        "success_rate": success,
        "recovery_rate": recovery,
        "retry_rate": retry,
        "no_attempt_rate": no_attempt,
        "percentile": float(
            (p or {}).get("success_rate_percentile") or 0
        ) * 100,
    }


# =========================================================
# LLM context
# =========================================================
def build_llm_context(merchant_id: str):
    """
    Build a safe, JSON-serializable context for the LLM.
    The merchant_metrics table is the primary source.
    Optional tables are loaded independently so one broken query
    does not destroy the whole context.
    """

    merchant = query_one(
        """
        SELECT *
        FROM merchant_metrics
        WHERE merchant_key=?
        """,
        [merchant_id],
    )

    if not merchant:
        raise HTTPException(
            status_code=404,
            detail=f"Merchant not found: {merchant_id}",
        )

    # ---------------------------------------------------------
    # Health
    # ---------------------------------------------------------

    health = {
        "success_rate": merchant.get("final_success_rate"),
        "first_attempt_success_rate": merchant.get(
            "first_attempt_success_rate"
        ),
        "recovery_rate": merchant.get("recovery_rate"),
        "retry_rate": merchant.get("retry_rate"),
        "no_attempt_rate": merchant.get("no_attempt_rate"),
    }

    # ---------------------------------------------------------
    # Peer
    # ---------------------------------------------------------

    try:
        peer = query_one(
            """
            SELECT *
            FROM peer_metrics
            WHERE merchant_key=?
            """,
            [merchant_id],
        ) or {}
    except Exception:
        peer = {}

    # ---------------------------------------------------------
    # Daily
    # ---------------------------------------------------------

    try:
        daily = query(
            """
            SELECT
                metric_date,
                sessions,
                successful_sessions,
                successful_volume,
                recovered_sessions,
                unrecovered_sessions,
                lost_volume
            FROM merchant_daily_metrics
            WHERE merchant_key=?
            ORDER BY metric_date DESC
            LIMIT 30
            """,
            [merchant_id],
        )
    except Exception:
        daily = []

    # ---------------------------------------------------------
    # Hourly
    # ---------------------------------------------------------

    try:
        hourly = query(
            """
            SELECT
                hour_of_day,
                sessions,
                successful_sessions,
                successful_volume,
                success_rate
            FROM merchant_hourly_metrics
            WHERE merchant_key=?
            ORDER BY hour_of_day
            """,
            [merchant_id],
        )
    except Exception:
        hourly = []

    # ---------------------------------------------------------
    # PSP
    # ---------------------------------------------------------

    try:
        psps = query(
            """
            SELECT
                psp_code,
                sessions,
                successful_sessions,
                final_success_rate,
                successful_volume
            FROM merchant_psp_metrics
            WHERE merchant_key=?
            ORDER BY sessions DESC
            """,
            [merchant_id],
        )
    except Exception:
        psps = []

    # ---------------------------------------------------------
    # Customers
    # ---------------------------------------------------------

    try:
        customers = query_one(
            """
            WITH c AS (
                SELECT
                    payer_card_key,
                    COUNT(DISTINCT session_key) AS orders,

                    SUM(
                        CASE
                            WHEN try_status IN ('Verified', 'Paid')
                            THEN amount
                            ELSE 0
                        END
                    ) AS spend

                FROM attempts

                WHERE merchant_key=?
                  AND payer_card_key IS NOT NULL
                  AND payer_card_key<>''

                GROUP BY payer_card_key
            )

            SELECT
                COUNT(*) AS customers,

                COUNT(*) FILTER (
                    WHERE orders > 1
                ) AS repeat_customers,

                AVG(orders) AS avg_orders,

                SUM(spend) AS customer_spend,

                COUNT(*) FILTER (
                    WHERE orders >= 5
                ) AS vip,

                COUNT(*) FILTER (
                    WHERE orders BETWEEN 2 AND 4
                ) AS loyal,

                COUNT(*) FILTER (
                    WHERE orders = 1
                ) AS new_customers

            FROM c
            """,
            [merchant_id],
        ) or {}
    except Exception:
        customers = {}

    # ---------------------------------------------------------
    # Insights
    # ---------------------------------------------------------

    try:
        insights = query(
            """
            SELECT
                insight_type,
                severity,
                title,
                summary,
                recommendation,
                metric_name,
                metric_value

            FROM insight_evidence

            WHERE merchant_key=?

            ORDER BY
                CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'warning' THEN 2
                    ELSE 3
                END,
                metric_value DESC NULLS LAST

            LIMIT 10
            """,
            [merchant_id],
        )
    except Exception:
        insights = []

    # ---------------------------------------------------------
    # Seasonality
    # ---------------------------------------------------------

    try:
        seasonality = query(
            """
            SELECT
                EXTRACT(
                    MONTH FROM created_at
                )::INTEGER AS month,

                COUNT(*) AS sessions,

                COUNT(*) FILTER (
                    WHERE final_success
                ) AS successful_sessions,

                SUM(
                    CASE
                        WHEN final_success
                        THEN amount
                        ELSE 0
                    END
                ) AS successful_volume,

                SUM(
                    CASE
                        WHEN unrecovered
                        THEN amount
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

            WHERE merchant_key=?
              AND created_at IS NOT NULL

            GROUP BY 1
            ORDER BY 1
            """,
            [merchant_id],
        )
    except Exception:
        seasonality = []

    # ---------------------------------------------------------
    # Final context
    # ---------------------------------------------------------

    return {
        "merchant": merchant,
        "health": health,
        "peer": peer,
        "daily_last_30_days": daily,
        "hourly": hourly,
        "psps": psps,
        "customers": customers,
        "insights": insights,
        "seasonality_monthly": seasonality,
    }
# =========================================================
# AvalAI / OpenAI-compatible client
# =========================================================

def get_llm_client():
    if OpenAI is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "OpenAI SDK is not installed. "
                "Run: python -m pip install openai"
            ),
        )

    api_key = (
        os.getenv("AVALAI_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )

    base_url = (
        os.getenv("OPENAI_BASE_URL")
        or "https://api.avalai.ir/v1"
    ).strip()

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "AVALAI_API_KEY is not configured. "
                "Put it in backend/.env"
            ),
        )

    return OpenAI(
        api_key=api_key.strip(),
        base_url=base_url,
        timeout=60.0,
        max_retries=1,
    )


def call_llm(
    client: OpenAI,
    model: str,
    instructions: str,
    prompt: str,
):
    """
    AvalAI is OpenAI-compatible.
    Use chat.completions here because this is the endpoint
    already verified by the project environment.
    """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": instructions,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    if not response.choices:
        return ""

    message = response.choices[0].message
    return (message.content or "").strip()


# =========================================================
# AI Assistant - POST
# =========================================================

@app.post("/api/merchants/{merchant_id}/ask")
def merchant_ask(
    merchant_id: str,
    body: AskRequest,
):
    question = body.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question is required",
        )

    # 1. Build evidence from DuckDB first.
    context = build_llm_context(merchant_id)

    # 2. Read AvalAI configuration.
    model = os.getenv(
        "OPENAI_MODEL",
        "gpt-5.5",
    ).strip()

    if not model:
        model = "gpt-5.5"

    client = get_llm_client()

    instructions = """
تو ZarinPal Merchant Analyst هستی؛ دستیار تحلیلی داشبورد پذیرندگان زرین‌پال.

قواعد قطعی:
1. پاسخ را فارسی بده، مگر کاربر زبان دیگری بخواهد.
2. فقط از DATABASE CONTEXT استفاده کن.
3. هیچ عدد، درصد، تاریخ، علت، روند، عملکرد PSP یا benchmark را حدس نزن.
4. اگر داده کافی نیست، صریح بگو داده کافی برای پاسخ قطعی وجود ندارد.
5. بین correlation و causation تفاوت بگذار.
6. برای اعداد مهم، مقدار واقعی دیتابیس را ذکر کن.
7. مبلغ‌ها ریال هستند مگر اینکه خود داده خلاف آن را نشان دهد.
8. نرخ‌های decimal مثل 0.73 را به صورت 73٪ نمایش بده.
9. پیشنهاد عملی فقط وقتی بده که از داده پشتیبانی شود.
10. پاسخ را کوتاه و مدیریتی نگه دار.
11. در پایان بخشی با عنوان «شواهد» اضافه کن و 2 تا 5 metric/table
    استفاده‌شده را نام ببر.
12. اگر کاربر فقط گفت «سلام»، فقط سلام و یک جمله کوتاه پاسخ بده
    و از ساختن تحلیل غیرضروری خودداری کن.
"""

    prompt = f"""
MERCHANT_ID:
{merchant_id}

DATABASE_CONTEXT:
{json_text(context)}

USER_QUESTION:
{question}
"""

    try:
        answer = call_llm(
            client=client,
            model=model,
            instructions=instructions,
            prompt=prompt,
        )

        if not answer:
            answer = "مدل پاسخ متنی برنگرداند."

    except Exception as exc:
        error_text = str(exc)
        lower = error_text.lower()

        if (
            "401" in error_text
            or "invalid_api_key" in lower
            or "incorrect api key" in lower
        ):
            detail = (
                "کلید AvalAI معتبر نیست یا هنوز فعال نشده است. "
                "AVALAI_API_KEY در backend/.env را بررسی کنید."
            )

        elif (
            "429" in error_text
            or "quota" in lower
            or "credit" in lower
            or "balance" in lower
        ):
            detail = (
                "درخواست به AvalAI رسید، اما اعتبار حساب کافی نیست. "
                "موجودی AvalAI را شارژ کنید."
            )

        elif (
            "model" in lower
            and (
                "not found" in lower
                or "does not exist" in lower
                or "model_not_found" in lower
            )
        ):
            detail = (
                f"مدل «{model}» توسط AvalAI در دسترس نیست. "
                "مقدار OPENAI_MODEL را به یکی از مدل‌های فعال حساب AvalAI تغییر دهید."
            )

        else:
            detail = f"AvalAI request failed: {error_text}"

        raise HTTPException(
            status_code=502,
            detail=detail,
        )

    return {
        "answer": answer,
        "model": model,
        "provider": "AvalAI",
        "llm_ready": True,
        "evidence": {
    "merchant": context.get("merchant", {}),
    "health": context.get("health", {}),
    "peer": context.get("peer", {}),
    "insights": context.get("insights", []),
},
    }


# =========================================================
# AI Assistant - GET (used by current frontend)
# =========================================================

@app.get("/api/merchants/{merchant_id}/ask")
def merchant_ask_get(
    merchant_id: str,
    q: str = Query(..., min_length=1),
):
    return merchant_ask(
        merchant_id,
        AskRequest(question=q),
    )