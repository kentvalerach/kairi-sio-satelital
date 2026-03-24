"""
KAIRI-SIO-SATELITAL — Database Connection Pool
psycopg2 connection pool para kairi_sio_satelital.
Usa kwargs individuales (no DSN string) para evitar UnicodeDecodeError en Windows.
"""

import psycopg2
import psycopg2.pool
from config.settings import DB_CONFIG

_pool = None

def _get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.SimpleConnectionPool(
            1, 5,
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            dbname=DB_CONFIG["dbname"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
        )
    return _pool

def get_conn():
    """Obtiene una conexión del pool."""
    return _get_pool().getconn()

def release_conn(conn):
    """Devuelve la conexión al pool."""
    _get_pool().putconn(conn)

def close_pool():
    """Cierra todas las conexiones del pool."""
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None