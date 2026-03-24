"""
GPM IMERG — Precipitación en tiempo real
==========================================
Obtiene precipitación acumulada 7 días de NASA GPM IMERG V06
para una cuenca via Google Earth Engine.

Uso:
    from ingestion.gpm import get_precipitation_7d
    result = get_precipitation_7d("jucar", "2024-10-29")
"""
import ee
from datetime import datetime, timedelta
from config.settings import CUENCAS


def get_precipitation_7d(cuenca_name: str, fecha_ref: str) -> dict:
    """
    Precipitación acumulada 7 días antes de fecha_ref.

    Args:
        cuenca_name: Clave de la cuenca en CUENCAS dict
        fecha_ref:   Fecha de referencia YYYY-MM-DD

    Returns:
        dict con precip_7d_mm, precip_max_1h_mm
    """
    geom  = ee.Geometry.Rectangle(CUENCAS[cuenca_name]["bbox"])
    f_ini = (
        datetime.strptime(fecha_ref, "%Y-%m-%d") - timedelta(days=7)
    ).strftime("%Y-%m-%d")

    col = (
        ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
        .filterBounds(geom)
        .filterDate(f_ini, fecha_ref)
        .select("precipitation")
    )

    # Acumulado total
    total = (
        col.sum()
        .reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geom,
            scale=11000,
            maxPixels=1e9,
        )
        .getInfo()
    )

    # Máximo horario (para detección de eventos extremos)
    max_hr = (
        col.max()
        .reduceRegion(
            reducer=ee.Reducer.max(),
            geometry=geom,
            scale=11000,
            maxPixels=1e9,
        )
        .getInfo()
    )

    # V07 ya entrega mm directamente por período
    factor = 1.0 
    return {
        "precip_7d_mm":    round((total.get("precipitation") or 0) * factor, 2),
        "precip_max_1h_mm": round((max_hr.get("precipitation") or 0), 2),
    }
