"""
KAIRI-SIO-SATELITAL — Database Connection Pool
Lee credenciales desde os.environ (Streamlit Cloud secrets)
o desde config/settings.py (local).
"""

import os
import psycopg2
import psycopg2.pool

_pool = None

def _get_config():
    """Lee DB config desde os.environ primero, luego settings.py."""
    # Streamlit Cloud inyecta secrets como variables de entorno
    host = os.environ.get("DB_HOST")
    if host:
        return {
            "host":     host,
            "port":     int(os.environ.get("DB_PORT", "5432")),
            "dbname":   os.environ.get("DB_NAME", "postgres"),
            "user":     os.environ.get("DB_USER", "postgres"),
            "password": os.environ.get("DB_PASSWORD", ""),
        }
    # Fallback local
    from config.settings import DB_CONFIG
    return DB_CONFIG

def _get_pool():
    global _pool
    if _pool is None:
        cfg = _get_config()
        _pool = psycopg2.pool.SimpleConnectionPool(
            1, 5,
            host=cfg["host"],
            port=cfg["port"],
            dbname=cfg["dbname"],
            user=cfg["user"],
            password=cfg["password"],
        )
    return _pool

def get_conn():
    return _get_pool().getconn()

def release_conn(conn):
    _get_pool().putconn(conn)

def close_pool():
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None