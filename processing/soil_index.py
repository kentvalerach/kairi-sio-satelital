"""
KAIRI-SIO-SATELITAL — Soil Saturation Index (SSI)
Calcula el índice compuesto de saturación del suelo [0-100]
combinando backscatter SAR, precipitación acumulada y NDVI inverso.
"""

import numpy as np
from config.settings import SSI_PARAMS


def compute_ssi(
    cuenca_name: str,
    vv_mean: float,
    precip_7d_mm: float,
    ndvi: float,
) -> dict:
    """
    Calcula el SSI para una cuenca.

    Parámetros
    ----------
    cuenca_name  : nombre de la cuenca (debe existir en SSI_PARAMS)
    vv_mean      : backscatter VV medio Sentinel-1 (dB), ej. -12.5
    precip_7d_mm : precipitación acumulada 7 días (mm)
    ndvi         : NDVI medio Sentinel-2 [0.0 - 1.0]

    Retorna
    -------
    dict con: ssi_score, sar_norm, precip_norm, ndvi_inv_norm, risk_level
    """
    if cuenca_name not in SSI_PARAMS:
        raise ValueError(f"Cuenca '{cuenca_name}' no encontrada en SSI_PARAMS")

    params = SSI_PARAMS[cuenca_name]

    # ── Normalización SAR ──────────────────────────────────────────
    # VV_min=-25dB (seco) → 0%,  VV_max=-5dB (saturado) → 100%
    sar_norm = float(np.clip(
        (vv_mean - params["vv_min"]) / (params["vv_max"] - params["vv_min"]) * 100,
        0.0, 100.0
    ))

    # ── Normalización precipitación ────────────────────────────────
    # Capped en P95 climatológico de la cuenca
    precip_norm = float(min(precip_7d_mm / params["p95_mm"], 1.0) * 100)

    # ── NDVI inverso normalizado ───────────────────────────────────
    # Suelo desnudo (NDVI bajo) = mayor escorrentía potencial → riesgo alto
    ndvi_clamped = float(np.clip(ndvi, 0.0, 1.0))
    ndvi_inv_norm = (1.0 - ndvi_clamped) * 100.0

    # ── SSI compuesto ponderado ────────────────────────────────────
    w = params["weights"]
    ssi = (
        w["sar"]    * sar_norm +
        w["precip"] * precip_norm +
        w["ndvi"]   * ndvi_inv_norm
    )
    ssi = float(np.clip(ssi, 0.0, 100.0))

    # ── Nivel de riesgo ────────────────────────────────────────────
    if ssi >= 85:
        risk = "CRITICO"
    elif ssi >= 70:
        risk = "ALTO"
    elif ssi >= 50:
        risk = "MODERADO"
    else:
        risk = "BAJO"

    return {
        "ssi_score":     round(ssi, 2),
        "sar_norm":      round(sar_norm, 2),
        "precip_norm":   round(precip_norm, 2),
        "ndvi_inv_norm": round(ndvi_inv_norm, 2),
        "risk_level":    risk,
    }


def batch_compute_ssi(observations: list[dict]) -> list[dict]:
    """
    Calcula SSI para una lista de observaciones.

    Cada elemento debe tener: cuenca, obs_date, vv_mean_db,
    precip_7d_mm, ndvi_mean.

    Retorna lista de dicts listos para insert_ssi_score().
    """
    results = []
    for obs in observations:
        # Si faltan datos satelitales, saltar
        if obs.get("vv_mean_db") is None or obs.get("ndvi_mean") is None:
            print(f"  ⚠ Saltando {obs['cuenca']} {obs['obs_date']} — datos incompletos")
            continue

        ssi_result = compute_ssi(
            cuenca_name=obs["cuenca"],
            vv_mean=obs["vv_mean_db"],
            precip_7d_mm=obs.get("precip_7d_mm", 0.0),
            ndvi=obs["ndvi_mean"],
        )

        results.append({
            "cuenca":       obs["cuenca"],
            "obs_date":     obs["obs_date"],
            "ssi_score":    ssi_result["ssi_score"],
            "sar_norm":     ssi_result["sar_norm"],
            "precip_norm":  ssi_result["precip_norm"],
            "ndvi_inv_norm":ssi_result["ndvi_inv_norm"],
            "risk_level":   ssi_result["risk_level"],
            "ttt_hours":    None,  # se rellena en flood_risk.py
        })

    return results