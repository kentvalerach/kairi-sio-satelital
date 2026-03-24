"""
KAIRI-SIO-SATELITAL — Settings
Configuración central: DB, GEE, Telegram, parámetros de cuencas y SSI.
Lee variables desde config/.env automáticamente.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ── Cargar .env ──────────────────────────────────────────────────────
_ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(_ENV_PATH)

# ── PYTHONPATH automático ────────────────────────────────────────────
# Asegura que la raíz del proyecto esté en el path sin necesitar
# $env:PYTHONPATH manualmente en cada terminal
_ROOT = str(Path(__file__).parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Base de datos ────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME", "kairi_sio_satelital"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# ── Google Earth Engine ──────────────────────────────────────────────
GEE_PROJECT = os.getenv("GEE_PROJECT", "kairi-sio-satelital")

# ── Telegram ─────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ── Cuencas: bounding boxes y metadatos ─────────────────────────────
# bbox = [lon_min, lat_min, lon_max, lat_max]
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

# ── Parámetros SSI por cuenca ────────────────────────────────────────
# vv_min/vv_max: rango backscatter SAR (dB)
# p95_mm: percentil 95 precipitación acumulada 7d histórica
# weights: pesos w1(SAR), w2(precip), w3(NDVI-inv)
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