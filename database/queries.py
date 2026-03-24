"""
KAIRI-SIO-SATELITAL — Database Queries
Funciones INSERT / SELECT para las 4 tablas del schema.
"""

from datetime import date
from database.connection import get_conn, release_conn


# ════════════════════════════════════════════════════════════════════
# satellite_obs
# ════════════════════════════════════════════════════════════════════

def insert_satellite_obs(data: dict) -> int:
    """
    Inserta una observación satelital. Usa ON CONFLICT DO UPDATE
    para actualizar si ya existe (cuenca, obs_date).

    data = {
        cuenca, obs_date, vv_mean_db, vv_std_db,
        precip_7d_mm, precip_max_1h, ndvi_mean, ndvi_std, n_sar_images
    }
    Retorna el id insertado/actualizado.
    """
    sql = """
        INSERT INTO satellite_obs
            (cuenca, obs_date, vv_mean_db, vv_std_db,
             precip_7d_mm, precip_max_1h, ndvi_mean, ndvi_std, n_sar_images)
        VALUES
            (%(cuenca)s, %(obs_date)s, %(vv_mean_db)s, %(vv_std_db)s,
             %(precip_7d_mm)s, %(precip_max_1h)s, %(ndvi_mean)s,
             %(ndvi_std)s, %(n_sar_images)s)
        ON CONFLICT (cuenca, obs_date) DO UPDATE SET
            vv_mean_db    = EXCLUDED.vv_mean_db,
            vv_std_db     = EXCLUDED.vv_std_db,
            precip_7d_mm  = EXCLUDED.precip_7d_mm,
            precip_max_1h = EXCLUDED.precip_max_1h,
            ndvi_mean     = EXCLUDED.ndvi_mean,
            ndvi_std      = EXCLUDED.ndvi_std,
            n_sar_images  = EXCLUDED.n_sar_images,
            created_at    = NOW()
        RETURNING id;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, data)
            row_id = cur.fetchone()[0]
            conn.commit()
            return row_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_conn(conn)


def get_latest_satellite_obs(cuenca: str) -> dict | None:
    """Retorna la observación satelital más reciente para una cuenca."""
    sql = """
        SELECT cuenca, obs_date, vv_mean_db, vv_std_db,
               precip_7d_mm, precip_max_1h, ndvi_mean, ndvi_std, n_sar_images
        FROM satellite_obs
        WHERE cuenca = %s
        ORDER BY obs_date DESC
        LIMIT 1;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (cuenca,))
            row = cur.fetchone()
            if not row:
                return None
            cols = ["cuenca", "obs_date", "vv_mean_db", "vv_std_db",
                    "precip_7d_mm", "precip_max_1h", "ndvi_mean", "ndvi_std", "n_sar_images"]
            return dict(zip(cols, row))
    finally:
        release_conn(conn)


# ════════════════════════════════════════════════════════════════════
# ssi_scores
# ════════════════════════════════════════════════════════════════════

def insert_ssi_score(data: dict) -> int:
    """
    Inserta un SSI calculado. Upsert por (cuenca, obs_date).

    data = {
        cuenca, obs_date, ssi_score, sar_norm, precip_norm,
        ndvi_inv_norm, risk_level, ttt_hours
    }
    """
    sql = """
        INSERT INTO ssi_scores
            (cuenca, obs_date, ssi_score, sar_norm, precip_norm,
             ndvi_inv_norm, risk_level, ttt_hours)
        VALUES
            (%(cuenca)s, %(obs_date)s, %(ssi_score)s, %(sar_norm)s,
             %(precip_norm)s, %(ndvi_inv_norm)s, %(risk_level)s, %(ttt_hours)s)
        ON CONFLICT (cuenca, obs_date) DO UPDATE SET
            ssi_score     = EXCLUDED.ssi_score,
            sar_norm      = EXCLUDED.sar_norm,
            precip_norm   = EXCLUDED.precip_norm,
            ndvi_inv_norm = EXCLUDED.ndvi_inv_norm,
            risk_level    = EXCLUDED.risk_level,
            ttt_hours     = EXCLUDED.ttt_hours,
            created_at    = NOW()
        RETURNING id;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, data)
            row_id = cur.fetchone()[0]
            conn.commit()
            return row_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_conn(conn)


def get_latest_ssi(cuenca: str) -> dict | None:
    """Retorna el SSI más reciente para una cuenca (usado por el dashboard)."""
    sql = """
        SELECT cuenca, obs_date, ssi_score, sar_norm, precip_norm,
               ndvi_inv_norm, risk_level, ttt_hours
        FROM ssi_scores
        WHERE cuenca = %s
        ORDER BY obs_date DESC
        LIMIT 1;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (cuenca,))
            row = cur.fetchone()
            if not row:
                return None
            cols = ["cuenca", "obs_date", "ssi_score", "sar_norm", "precip_norm",
                    "ndvi_inv_norm", "risk_level", "ttt_hours"]
            return dict(zip(cols, row))
    finally:
        release_conn(conn)


def get_ssi_history(cuenca: str, days: int = 90) -> list[dict]:
    """Retorna histórico SSI de los últimos N días (para gráficos dashboard)."""
    sql = """
        SELECT obs_date, ssi_score, risk_level
        FROM ssi_scores
        WHERE cuenca = %s
          AND obs_date >= CURRENT_DATE - INTERVAL '%s days'
        ORDER BY obs_date ASC;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (cuenca, days))
            rows = cur.fetchall()
            cols = ["obs_date", "ssi_score", "risk_level"]
            return [dict(zip(cols, row)) for row in rows]
    finally:
        release_conn(conn)


# ════════════════════════════════════════════════════════════════════
# reservoir_levels
# ════════════════════════════════════════════════════════════════════

def insert_reservoir_level(data: dict) -> int:
    """
    Inserta nivel de embalse. Upsert por (embalse, obs_timestamp).

    data = {
        cuenca, embalse, obs_timestamp, nivel_hm3,
        capacidad_hm3, pct_llenado
    }
    """
    sql = """
        INSERT INTO reservoir_levels
            (cuenca, embalse, obs_timestamp, nivel_hm3,
             capacidad_hm3, pct_llenado)
        VALUES
            (%(cuenca)s, %(embalse)s, %(obs_timestamp)s, %(nivel_hm3)s,
             %(capacidad_hm3)s, %(pct_llenado)s)
        ON CONFLICT (embalse, obs_timestamp) DO UPDATE SET
            nivel_hm3     = EXCLUDED.nivel_hm3,
            capacidad_hm3 = EXCLUDED.capacidad_hm3,
            pct_llenado   = EXCLUDED.pct_llenado
        RETURNING id;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, data)
            row_id = cur.fetchone()[0]
            conn.commit()
            return row_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_conn(conn)


# ════════════════════════════════════════════════════════════════════
# alert_log
# ════════════════════════════════════════════════════════════════════

def insert_alert_log(data: dict) -> int:
    """
    Registra una alerta disparada.

    data = {
        cuenca, alert_level, ssi_score, ttt_hours, channel
    }
    """
    sql = """
        INSERT INTO alert_log
            (cuenca, alert_level, ssi_score, ttt_hours, channel)
        VALUES
            (%(cuenca)s, %(alert_level)s, %(ssi_score)s,
             %(ttt_hours)s, %(channel)s)
        RETURNING id;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, data)
            row_id = cur.fetchone()[0]
            conn.commit()
            return row_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_conn(conn)