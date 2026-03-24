"""
KAIRI-SIO-SATELITAL — Settings
Lee variables desde config/.env (local) o st.secrets / os.environ (Streamlit Cloud).
"""

import os
import sys
from pathlib import Path

# ── Intentar cargar .env local ───────────────────────────────────────
try:
    from dotenv import load_dotenv
    _ENV_PATH = Path(__file__).parent / ".env"
    if _ENV_PATH.exists():
        load_dotenv(_ENV_PATH)
except ImportError:
    pass

# ── Intentar cargar st.secrets (Streamlit Cloud) ────────────────────
try:
    import streamlit as st
    _secrets = st.secrets
    def _get(key, default=""):
        try:
            return _secrets[key]
        except:
            return os.getenv(key, default)
except Exception:
    def _get(key, default=""):
        return os.getenv(key, default)

# ── PYTHONPATH automático ────────────────────────────────────────────
_ROOT = str(Path(__file__).parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Base de datos ────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     _get("DB_HOST", "localhost"),
    "port":     int(_get("DB_PORT", "5432")),
    "dbname":   _get("DB_NAME", "kairi_sio_satelital"),
    "user":     _get("DB_USER", "postgres"),
    "password": _get("DB_PASSWORD", ""),
}

# ── Google Earth Engine ──────────────────────────────────────────────
GEE_PROJECT = _get("GEE_PROJECT", "kairi-sio-satelital")

# ── Telegram ─────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = _get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = _get("TELEGRAM_CHAT_ID", "")

# ── Cuencas ──────────────────────────────────────────────────────────
CUENCAS = {
    "Jucar": {
        "bbox":          [-2.0, 38.5, 0.5, 40.5],
        "center":        [39.5, -0.75],
        "confederacion": "CHJ",
        "area_km2":      22587,
        "prioridad":     "CRITICA",
    },
    "Segura": {
        "bbox":          [-2.5, 37.5, -0.5, 38.8],
        "center":        [38.1, -1.5],
        "confederacion": "CHS",
        "area_km2":      19025,
        "prioridad":     "CRITICA",
    },
    "Guadalquivir": {
        "bbox":          [-6.5, 37.0, -1.5, 38.5],
        "center":        [37.8, -4.0],
        "confederacion": "CHG",
        "area_km2":      57527,
        "prioridad":     "VALIDACION",
    },
}

# ── Parámetros SSI ───────────────────────────────────────────────────
SSI_PARAMS = {
    "Jucar": {
        "vv_min":  -25.0,
        "vv_max":  -5.0,
        "p95_mm":  120.0,
        "weights": {"sar": 0.45, "precip": 0.40, "ndvi": 0.15},
    },
    "Segura": {
        "vv_min":  -25.0,
        "vv_max":  -5.0,
        "p95_mm":  90.0,
        "weights": {"sar": 0.45, "precip": 0.40, "ndvi": 0.15},
    },
    "Guadalquivir": {
        "vv_min":  -25.0,
        "vv_max":  -5.0,
        "p95_mm":  150.0,
        "weights": {"sar": 0.45, "precip": 0.40, "ndvi": 0.15},
    },
}

# ── URLs SAIH ────────────────────────────────────────────────────────
SAIH_URLS = {
    "CHG": "https://www.chguadalquivir.es/saih/EmbalsesList.aspx",
    "CHJ": "https://www.chj.es/es-es/medioambiente/redesdecontrol/Paginas/embalses.aspx",
    "CHS": "https://www.chsegura.es/chs/cuenca/redesdecontrol/embalses/",
}