"""
Sentinel-2 óptico — NDVI y cobertura del suelo
================================================
Obtiene NDVI medio de Sentinel-2 SR para una cuenca via Google Earth Engine.
NDVI bajo = suelo desnudo = mayor escorrentía potencial.

Uso:
    from ingestion.sentinel2 import get_ndvi
    result = get_ndvi("jucar", "2024-10-01", "2024-10-15")
"""
import ee
from config.settings import CUENCAS


def get_ndvi(cuenca_name: str, fecha_ini: str, fecha_fin: str) -> dict:
    """
    Obtiene NDVI medio de Sentinel-2 SR para una cuenca.

    Args:
        cuenca_name: Clave de la cuenca en CUENCAS dict
        fecha_ini:   Fecha inicio YYYY-MM-DD
        fecha_fin:   Fecha fin YYYY-MM-DD

    Returns:
        dict con ndvi_mean, ndvi_std, n_images
    """
    geom = ee.Geometry.Rectangle(CUENCAS[cuenca_name]["bbox"])

    def add_ndvi(img):
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
        return img.addBands(ndvi)

    col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geom)
        .filterDate(fecha_ini, fecha_fin)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .map(add_ndvi)
        .select("NDVI")
    )

    n_images = col.size().getInfo()
    if n_images == 0:
        return {"ndvi_mean": None, "ndvi_std": None, "n_images": 0}

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
        "ndvi_mean": round(stats.get("NDVI_mean",   0) or 0, 4),
        "ndvi_std":  round(stats.get("NDVI_stdDev", 0) or 0, 4),
        "n_images":  n_images,
    }
