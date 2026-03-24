"""
KAIRI-SIO-SATELITAL — Pipeline Runner
Ingesta completa: GEE → SSI → PostgreSQL para las 3 cuencas.
Ejecutar manualmente o via Windows Task Scheduler cada 6 dias.

Uso:
    python pipeline_runner.py              # todas las cuencas, hoy
    python pipeline_runner.py --cuenca Jucar
    python pipeline_runner.py --dias 30    # ultimos 30 dias
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import ee
from datetime import date, timedelta, datetime

from config.settings import GEE_PROJECT, CUENCAS, SSI_PARAMS
from processing.soil_index import compute_ssi
from database.queries import insert_satellite_obs, insert_ssi_score, get_latest_ssi

# ── Inicializar GEE ──────────────────────────────────────────────────
ee.Initialize(project=GEE_PROJECT)


def get_sar(cuenca: str, f_ini: str, f_fin: str) -> dict:
    bbox = CUENCAS[cuenca]["bbox"]
    geom = ee.Geometry.Rectangle(bbox)
    col  = (ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(geom).filterDate(f_ini, f_fin)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .select("VV"))
    n = col.size().getInfo()
    if n == 0:
        return {"vv_mean": None, "vv_std": None, "n_images": 0}
    stats = col.mean().reduceRegion(
        ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
        geom, 100, maxPixels=1e9
    ).getInfo()
    return {
        "vv_mean":  round(stats.get("VV_mean", 0), 4),
        "vv_std":   round(stats.get("VV_stdDev", 0), 4),
        "n_images": n,
    }


def get_gpm(cuenca: str, fecha_ref: str) -> dict:
    bbox  = CUENCAS[cuenca]["bbox"]
    geom  = ee.Geometry.Rectangle(bbox)
    f_ini = (datetime.strptime(fecha_ref, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
    col   = (ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
             .filterBounds(geom).filterDate(f_ini, fecha_ref)
             .select("precipitation"))
    total = col.sum().reduceRegion(ee.Reducer.mean(), geom, 11000, maxPixels=1e9).getInfo()
    maxv  = col.max().reduceRegion(ee.Reducer.max(),  geom, 11000, maxPixels=1e9).getInfo()
    return {
        "precip_7d_mm":  round(total.get("precipitation") or 0, 2),
        "precip_max_1h": round(maxv.get("precipitation")  or 0, 2),
    }


def get_ndvi(cuenca: str, f_ini: str, f_fin: str) -> dict:
    bbox = CUENCAS[cuenca]["bbox"]
    geom = ee.Geometry.Rectangle(bbox)
    col  = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geom).filterDate(f_ini, f_fin)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
            .map(lambda img: img.normalizedDifference(["B8", "B4"]).rename("NDVI")))
    n = col.size().getInfo()
    if n == 0:
        return {"ndvi_mean": 0.3, "ndvi_std": 0.05}
    stats = col.mean().reduceRegion(
        ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
        geom, 100, maxPixels=1e9
    ).getInfo()
    return {
        "ndvi_mean": round(stats.get("NDVI_mean")   or 0.3,  4),
        "ndvi_std":  round(stats.get("NDVI_stdDev") or 0.05, 4),
    }


def run_pipeline_cuenca(cuenca: str, fecha_ini: date, fecha_fin: date) -> list[dict]:
    """
    Corre el pipeline completo para una cuenca en un rango de fechas.
    Intervalo: cada 6 dias (revisita Sentinel-1).
    Retorna lista de resultados SSI guardados.
    """
    print(f"\n  {'='*50}")
    print(f"  Cuenca: {cuenca} | {fecha_ini} → {fecha_fin}")
    print(f"  {'='*50}")

    resultados = []
    fecha = fecha_ini

    while fecha <= fecha_fin:
        f_str     = fecha.strftime("%Y-%m-%d")
        f_fin_str = (fecha + timedelta(days=6)).strftime("%Y-%m-%d")

        print(f"\n  📅 {f_str}...")

        try:
            # ── Ingesta GEE ──────────────────────────────────────
            print(f"     🛰  SAR...", end=" ", flush=True)
            sar = get_sar(cuenca, f_str, f_fin_str)
            print(f"VV={sar['vv_mean']} dB ({sar['n_images']} imgs)")

            print(f"     🌧  GPM...", end=" ", flush=True)
            gpm = get_gpm(cuenca, f_str)
            print(f"7d={gpm['precip_7d_mm']} mm")

            print(f"     🌿  NDVI...", end=" ", flush=True)
            ndvi = get_ndvi(cuenca, f_str, f_fin_str)
            print(f"NDVI={ndvi['ndvi_mean']}")

            if sar["vv_mean"] is None:
                print(f"     ⚠ Sin imágenes SAR — saltando")
                fecha += timedelta(days=6)
                continue

            # ── Guardar observación satelital ────────────────────
            insert_satellite_obs({
                "cuenca":        cuenca,
                "obs_date":      fecha,
                "vv_mean_db":    sar["vv_mean"],
                "vv_std_db":     sar["vv_std"],
                "precip_7d_mm":  gpm["precip_7d_mm"],
                "precip_max_1h": gpm["precip_max_1h"],
                "ndvi_mean":     ndvi["ndvi_mean"],
                "ndvi_std":      ndvi["ndvi_std"],
                "n_sar_images":  sar["n_images"],
            })

            # ── Calcular SSI ─────────────────────────────────────
            ssi = compute_ssi(
                cuenca_name=cuenca,
                vv_mean=sar["vv_mean"],
                precip_7d_mm=gpm["precip_7d_mm"],
                ndvi=ndvi["ndvi_mean"],
            )

            insert_ssi_score({
                "cuenca":        cuenca,
                "obs_date":      fecha,
                "ssi_score":     ssi["ssi_score"],
                "sar_norm":      ssi["sar_norm"],
                "precip_norm":   ssi["precip_norm"],
                "ndvi_inv_norm": ssi["ndvi_inv_norm"],
                "risk_level":    ssi["risk_level"],
                "ttt_hours":     None,
            })

            print(f"     ✅ SSI={ssi['ssi_score']}% | {ssi['risk_level']}")
            resultados.append({"fecha": fecha, "cuenca": cuenca, **ssi})

        except Exception as e:
            print(f"     ❌ Error: {e}")

        fecha += timedelta(days=6)

    return resultados


def run_all(cuencas: list[str], dias: int = 30):
    """
    Corre el pipeline para todas las cuencas indicadas.
    Por defecto los últimos 30 días.
    """
    fecha_fin = date.today()
    fecha_ini = fecha_fin - timedelta(days=dias)

    print("=" * 60)
    print(f"  KAIRI-SIO-SATELITAL — Pipeline Runner")
    print(f"  Período: {fecha_ini} → {fecha_fin} ({dias} días)")
    print(f"  Cuencas: {', '.join(cuencas)}")
    print("=" * 60)

    todos = []
    for cuenca in cuencas:
        resultados = run_pipeline_cuenca(cuenca, fecha_ini, fecha_fin)
        todos.extend(resultados)

    # ── Resumen final ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  RESUMEN FINAL")
    print("=" * 60)
    for cuenca in cuencas:
        latest = get_latest_ssi(cuenca)
        if latest:
            print(f"  {cuenca}: SSI={latest['ssi_score']}% | {latest['risk_level']} | {latest['obs_date']}")
        else:
            print(f"  {cuenca}: sin datos")

    print(f"\n  Total observaciones procesadas: {len(todos)}")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    return todos


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KAIRI-SIO-SATELITAL Pipeline Runner")
    parser.add_argument("--cuenca", type=str, default=None,
                        help="Cuenca específica (Jucar, Segura, Guadalquivir)")
    parser.add_argument("--dias",   type=int, default=30,
                        help="Número de días hacia atrás (default: 30)")
    args = parser.parse_args()

    cuencas = [args.cuenca] if args.cuenca else list(CUENCAS.keys())
    run_all(cuencas, args.dias)