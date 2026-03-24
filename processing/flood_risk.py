"""
KAIRI-SIO-SATELITAL — Flood Risk / Time To Threshold (TTT)
Estima cuántas horas faltan para que un embalse alcance su capacidad
máxima operacional dado el caudal de entrada estimado.
"""


def compute_time_to_threshold(
    nivel_actual_hm3: float,
    capacidad_hm3: float,
    precip_mm_hr: float,
    area_cuenca_km2: float,
    ssi_score: float = 0.0,
    runoff_coeff: float | None = None,
) -> dict:
    """
    Estima horas hasta que el embalse alcanza capacidad_hm3.

    Parámetros
    ----------
    nivel_actual_hm3 : nivel actual del embalse (hm³)
    capacidad_hm3    : capacidad total del embalse (hm³)
    precip_mm_hr     : precipitación estimada próxima hora (mm/hr)
    area_cuenca_km2  : área de la cuenca tributaria (km²)
    ssi_score        : SSI actual [0-100] — ajusta runoff_coeff automáticamente
    runoff_coeff     : coeficiente de escorrentía manual (sobreescribe auto-calc)

    Retorna
    -------
    dict con: ttt_hours, q_in_hm3_hr, runoff_coeff_used,
              risk_urgent (< 12h), risk_critical (< 6h)
    """
    # ── Coeficiente de escorrentía adaptativo según SSI ────────────
    if runoff_coeff is None:
        if ssi_score >= 85:
            runoff_coeff = 0.90   # suelo casi saturado — escorrentía máxima
        elif ssi_score >= 70:
            runoff_coeff = 0.75
        elif ssi_score >= 50:
            runoff_coeff = 0.60
        else:
            runoff_coeff = 0.40   # suelo seco — absorción alta

    # ── Caudal de entrada estimado ─────────────────────────────────
    # 1 mm sobre 1 km² = 0.001 hm³
    q_in_hm3_hr = precip_mm_hr * area_cuenca_km2 * 0.001 * runoff_coeff

    if q_in_hm3_hr <= 0:
        return {
            "ttt_hours":        None,
            "q_in_hm3_hr":      0.0,
            "runoff_coeff_used": runoff_coeff,
            "risk_urgent":      False,
            "risk_critical":    False,
            "message":          "Sin precipitación activa — TTT indefinido",
        }

    # ── Capacidad residual y TTT ───────────────────────────────────
    capacidad_residual_hm3 = max(capacidad_hm3 - nivel_actual_hm3, 0.0)
    ttt_hours = capacidad_residual_hm3 / q_in_hm3_hr

    return {
        "ttt_hours":         round(ttt_hours, 1),
        "q_in_hm3_hr":       round(q_in_hm3_hr, 3),
        "runoff_coeff_used":  round(runoff_coeff, 2),
        "risk_urgent":        ttt_hours < 12,
        "risk_critical":      ttt_hours < 6,
        "message":            _ttt_message(ttt_hours),
    }


def _ttt_message(ttt_hours: float) -> str:
    if ttt_hours < 6:
        return "🔴 CRÍTICO — desbordamiento en menos de 6 horas"
    elif ttt_hours < 12:
        return "🟠 URGENTE — desbordamiento en menos de 12 horas"
    elif ttt_hours < 24:
        return "🟡 ALERTA — desbordamiento en menos de 24 horas"
    elif ttt_hours < 72:
        return "🟡 VIGILANCIA — desbordamiento en menos de 72 horas"
    else:
        return "🟢 NORMAL — sin riesgo inmediato"


def enrich_ssi_with_ttt(
    ssi_records: list[dict],
    reservoir_data: dict,
    precip_mm_hr: float,
    cuenca_areas_km2: dict,
) -> list[dict]:
    """
    Enriquece registros SSI con TTT usando datos de embalse.

    Parámetros
    ----------
    ssi_records      : lista de dicts de batch_compute_ssi()
    reservoir_data   : dict {cuenca: {nivel_hm3, capacidad_hm3}}
    precip_mm_hr     : precipitación actual (mm/hr)
    cuenca_areas_km2 : dict {cuenca: area_km2}

    Retorna ssi_records con campo ttt_hours rellenado.
    """
    for rec in ssi_records:
        cuenca = rec["cuenca"]
        if cuenca not in reservoir_data:
            continue

        res = reservoir_data[cuenca]
        ttt = compute_time_to_threshold(
            nivel_actual_hm3=res["nivel_hm3"],
            capacidad_hm3=res["capacidad_hm3"],
            precip_mm_hr=precip_mm_hr,
            area_cuenca_km2=cuenca_areas_km2.get(cuenca, 10000),
            ssi_score=rec["ssi_score"],
        )
        rec["ttt_hours"] = ttt.get("ttt_hours")

    return ssi_records