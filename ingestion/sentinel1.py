"""
Sentinel-1 SAR — Humedad del suelo
====================================
Obtiene backscatter VV de Sentinel-1 para una cuenca via Google Earth Engine.
El coeficiente VV es proxy de humedad superficial del suelo (0-5 cm).

Uso:
    from ingestion.sentinel1 import get_sar_backscatter
    result = get_sar_backscatter("jucar", "2024-10-01", "2024-10-07")
"""
import ee
from config.settings import CUENCAS, GEE_PROJECT

# ee.Initialize se llama una vez en config/settings.py


def get_sar_backscatter(cuenca_name: str, fecha_ini: str, fecha_fin: str) -> dict:
    """
    Obtiene media de backscatter VV Sentinel-1 para una cuenca.

    Args:
        cuenca_name: Clave de la cuenca en CUENCAS dict (ej: 'jucar')
        fecha_ini:   Fecha inicio YYYY-MM-DD
        fecha_fin:   Fecha fin YYYY-MM-DD

    Returns:
        dict con VV_mean (dB), VV_std (dB), n_images
    """
    geom = ee.Geometry.Rectangle(CUENCAS[cuenca_name]["bbox"])

    col = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(geom)
        .filterDate(fecha_ini, fecha_fin)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .select("VV")
    )

    n_images = col.size().getInfo()
    if n_images == 0:
        return {"VV_mean": None, "VV_std": None, "n_images": 0}

    stats = (
        col.mean()
        .reduceRegion(
            reducer=ee.Reducer.mean().combine(
                ee.Reducer.stdDev(), sharedInputs=True
            ),
            geometry=geom,
            scale=100,
            maxPixels=1e9,
        )
        .getInfo()
    )

    return {
        "VV_mean":  round(stats.get("VV_mean",   0) or 0, 4),
        "VV_std":   round(stats.get("VV_stdDev", 0) or 0, 4),
        "n_images": n_images,
    }
