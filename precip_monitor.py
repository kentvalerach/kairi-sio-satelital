"""
KAIRI-SIO-SATELITAL — Monitor de Precipitación Horario
Consulta GPM IMERG V07 cada hora para las 3 cuencas.
Detecta eventos Modo B (DANA seco: precip_24h > 60mm + SSI < 50%)
y dispara alerta Telegram si se supera el umbral.

Uso:
    python precip_monitor.py              # una ejecución
    python precip_monitor.py --loop       # bucle infinito cada 1h
    python precip_monitor.py --test       # simula DANA Valencia

Scheduler Windows: cada 1 hora via Task Scheduler → run_precip_monitor.bat
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ee
import time
import argparse
import logging
from datetime import datetime, timedelta, date

from config.settings import GEE_PROJECT, CUENCAS
from database.queries import get_latest_ssi, insert_alert_log
from alerts.thresholds import evaluate_risk
from alerts.dispatcher import dispatch_alert

# ── Logging ──────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/precip_monitor.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("precip_monitor")

# ── Umbrales Modo B ───────────────────────────────────────────────────
PRECIP_24H_CRITICO = 60.0   # mm — activa alerta ROJO Modo B
PRECIP_24H_ALTO    = 40.0   # mm — activa alerta NARANJA Modo B
INTERVALO_HORAS    = 1      # frecuencia del monitor


def get_precip_24h(cuenca: str) -> dict:
    """
    Consulta GPM IMERG V07 — precipitación acumulada últimas 24h.
    Ligero: solo reducción espacial sobre la cuenca, ~2KB de red.
    """
    bbox  = CUENCAS[cuenca]["bbox"]
    geom  = ee.Geometry.Rectangle(bbox)
    ahora = datetime.utcnow()
    f_ini = (ahora - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
    f_fin = ahora.strftime("%Y-%m-%dT%H:%M:%S")

    col = (ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
           .filterBounds(geom)
           .filterDate(f_ini, f_fin)
           .select("precipitation"))

    n = col.size().getInfo()
    if n == 0:
        return {"precip_24h_mm": 0.0, "n_images": 0, "timestamp": ahora}

    # Acumulado espacial medio sobre la cuenca
    total = col.sum().reduceRegion(
        ee.Reducer.mean(), geom, 11000, maxPixels=1e9
    ).getInfo()

    # Máximo horario (para detectar picos extremos)
    maximo = col.max().reduceRegion(
        ee.Reducer.max(), geom, 11000, maxPixels=1e9
    ).getInfo()

    return {
        "precip_24h_mm":  round(total.get("precipitation") or 0, 2),
        "precip_max_1h":  round(maximo.get("precipitation") or 0, 2),
        "n_images":       n,
        "timestamp":      ahora,
    }


def check_cuenca(cuenca: str) -> dict:
    """
    Verifica una cuenca: obtiene precipitación 24h y SSI más reciente,
    evalúa riesgo y dispara alerta si necesario.
    """
    # Precipitación en tiempo real
    precip = get_precip_24h(cuenca)
    precip_24h = precip["precip_24h_mm"]

    # SSI más reciente desde DB (puede tener hasta 6 días de antigüedad)
    latest_ssi = get_latest_ssi(cuenca)
    ssi_score  = latest_ssi["ssi_score"] if latest_ssi else 50.0  # fallback neutro

    # Evaluar riesgo con lógica dual
    result = evaluate_risk(
        cuenca=cuenca,
        ssi_score=ssi_score,
        precip_24h_mm=precip_24h,
        precip_prevista_6h_mm=precip["precip_max_1h"],
    )

    log.info(
        f"{cuenca}: precip_24h={precip_24h}mm | "
        f"SSI={ssi_score}% | {result.alert_level} ({result.modo})"
    )

    # Disparar alerta si nivel NARANJA o ROJO
    if result.alert_level in ("NARANJA", "ROJO"):
        log.warning(f"🚨 ALERTA {result.alert_level} — {cuenca} — {result.mensaje}")
        dispatch_alert(result)

    return {
        "cuenca":       cuenca,
        "precip_24h":   precip_24h,
        "ssi_score":    ssi_score,
        "alert_level":  result.alert_level,
        "modo":         result.modo,
        "timestamp":    precip["timestamp"].isoformat(),
    }


def run_once() -> list[dict]:
    """Una pasada completa por las 3 cuencas."""
    log.info("=" * 50)
    log.info("Monitor precipitación — inicio de ciclo")
    log.info("=" * 50)

    ee.Initialize(project=GEE_PROJECT)
    resultados = []

    for cuenca in CUENCAS:
        try:
            r = check_cuenca(cuenca)
            resultados.append(r)
        except Exception as e:
            log.error(f"{cuenca}: ERROR — {e}")

    # Resumen del ciclo
    log.info("-" * 50)
    for r in resultados:
        log.info(
            f"  {r['cuenca']:<15} "
            f"precip={r['precip_24h']:>6.1f}mm | "
            f"SSI={r['ssi_score']:>5.1f}% | "
            f"{r['alert_level']} ({r['modo']})"
        )
    log.info(f"Ciclo completado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    return resultados


def run_loop(intervalo_horas: int = 1):
    """Bucle infinito — ejecuta run_once() cada N horas."""
    log.info(f"Monitor iniciado — ciclo cada {intervalo_horas}h")
    while True:
        try:
            run_once()
        except Exception as e:
            log.error(f"Error en ciclo: {e}")
        log.info(f"Próximo ciclo en {intervalo_horas}h...")
        time.sleep(intervalo_horas * 3600)


def run_test():
    """
    Simula condiciones DANA Valencia 29-oct-2024.
    No consulta GEE — usa valores reales conocidos.
    """
    log.info("🧪 TEST — Simulando DANA Valencia 29-oct-2024")
    from alerts.thresholds import evaluate_risk
    from alerts.dispatcher import dispatch_alert

    test_cases = [
        {"cuenca": "Jucar",        "precip_24h": 82.6, "ssi": 44.86},
        {"cuenca": "Segura",       "precip_24h": 45.2, "ssi": 38.10},
        {"cuenca": "Guadalquivir", "precip_24h": 28.4, "ssi": 65.31},
    ]

    for tc in test_cases:
        result = evaluate_risk(
            cuenca=tc["cuenca"],
            ssi_score=tc["ssi"],
            precip_24h_mm=tc["precip_24h"],
        )
        log.info(
            f"  {tc['cuenca']}: precip={tc['precip_24h']}mm | "
            f"SSI={tc['ssi']}% → {result.alert_level} ({result.modo})"
        )
        if result.alert_level in ("NARANJA", "ROJO"):
            dispatch_alert(result, force=True)

    log.info("Test completado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KAIRI-SIO Monitor de Precipitación")
    parser.add_argument("--loop",     action="store_true", help="Bucle infinito cada 1h")
    parser.add_argument("--test",     action="store_true", help="Simular DANA Valencia")
    parser.add_argument("--intervalo",type=int, default=1,  help="Horas entre ciclos (default: 1)")
    args = parser.parse_args()

    if args.test:
        run_test()
    elif args.loop:
        run_loop(args.intervalo)
    else:
        run_once()