"""
KAIRI-SIO-SATELITAL — Alert Thresholds
Lógica de detección dual de riesgo DANA.

Modo A (saturación progresiva): SSI > 85% + precip_prevista > 40mm
Modo B (DANA seco):             precip_24h > 60mm + SSI < 50%

Validado retroactivamente contra DANA Valencia oct 2024.
"""

from dataclasses import dataclass


# ── Umbrales configurables ───────────────────────────────────────────
THRESHOLDS = {
    # Modo A — saturación progresiva
    "MODO_A": {
        "ssi_critico":       85.0,
        "ssi_alto":          70.0,
        "ssi_moderado":      50.0,
        "precip_alerta_mm":  40.0,   # precipitación prevista 6h para escalar
    },
    # Modo B — DANA seco (evento convectivo explosivo)
    "MODO_B": {
        "precip_24h_critico": 60.0,  # mm en 24h para activar Modo B
        "ssi_max_seco":       50.0,  # SSI debe estar por debajo (suelo seco)
        "precip_24h_alto":    40.0,
    },
    # TTT — tiempo al umbral
    "TTT": {
        "critico_horas":  6.0,
        "urgente_horas":  12.0,
        "alerta_horas":   24.0,
        "vigilancia_horas": 72.0,
    },
}


@dataclass
class AlertResult:
    """Resultado de evaluación de riesgo para una cuenca."""
    cuenca:        str
    alert_level:   str          # VERDE / AMARILLO / NARANJA / ROJO
    risk_score:    float        # 0-100
    modo:          str          # MODO_A / MODO_B / NORMAL
    ssi_score:     float
    precip_24h:    float
    ttt_hours:     float | None
    mensaje:       str
    accion:        str


def evaluate_risk(
    cuenca: str,
    ssi_score: float,
    precip_24h_mm: float,
    precip_prevista_6h_mm: float = 0.0,
    ttt_hours: float | None = None,
) -> AlertResult:
    """
    Evalúa el nivel de riesgo para una cuenca con lógica dual.

    Parámetros
    ----------
    cuenca               : nombre de la cuenca
    ssi_score            : SSI actual [0-100]
    precip_24h_mm        : precipitación acumulada últimas 24h (mm)
    precip_prevista_6h_mm: precipitación prevista próximas 6h (mm)
    ttt_hours            : tiempo al umbral del embalse (horas), None si N/D

    Retorna AlertResult con nivel, modo, mensaje y acción recomendada.
    """
    th_a = THRESHOLDS["MODO_A"]
    th_b = THRESHOLDS["MODO_B"]
    th_t = THRESHOLDS["TTT"]

    # ── Modo B — DANA seco (prioridad máxima) ───────────────────────
    # Suelo seco + lluvia extrema concentrada = escorrentía casi total
    if (precip_24h_mm >= th_b["precip_24h_critico"] and
            ssi_score < th_b["ssi_max_seco"]):
        return AlertResult(
            cuenca=cuenca,
            alert_level="ROJO",
            risk_score=95.0,
            modo="MODO_B",
            ssi_score=ssi_score,
            precip_24h=precip_24h_mm,
            ttt_hours=ttt_hours,
            mensaje=(f"⚠️ DANA SECO DETECTADO — {precip_24h_mm}mm/24h sobre "
                     f"suelo seco (SSI={ssi_score}%). Escorrentía máxima."),
            accion="Alerta inmediata. Notificar autoridades. Evacuar zonas bajas.",
        )

    if (precip_24h_mm >= th_b["precip_24h_alto"] and
            ssi_score < th_b["ssi_max_seco"]):
        return AlertResult(
            cuenca=cuenca,
            alert_level="NARANJA",
            risk_score=75.0,
            modo="MODO_B",
            ssi_score=ssi_score,
            precip_24h=precip_24h_mm,
            ttt_hours=ttt_hours,
            mensaje=(f"🌧 Lluvia intensa sobre suelo seco — {precip_24h_mm}mm/24h, "
                     f"SSI={ssi_score}%. Riesgo de escorrentía elevada."),
            accion="Monitoreo intensivo. Preparar protocolo de alerta.",
        )

    # ── Modo A — saturación progresiva ──────────────────────────────
    if ssi_score >= th_a["ssi_critico"]:
        # Escalar a ROJO si además hay precipitación prevista o TTT crítico
        ttt_critico = ttt_hours is not None and ttt_hours < th_t["critico_horas"]
        precip_activa = precip_prevista_6h_mm >= th_a["precip_alerta_mm"]

        if ttt_critico or precip_activa:
            return AlertResult(
                cuenca=cuenca,
                alert_level="ROJO",
                risk_score=98.0,
                modo="MODO_A",
                ssi_score=ssi_score,
                precip_24h=precip_24h_mm,
                ttt_hours=ttt_hours,
                mensaje=(f"🔴 EMERGENCIA — Suelo saturado (SSI={ssi_score}%) + "
                         f"precipitación activa. TTT={ttt_hours}h."),
                accion="Alerta inmediata. Notificar autoridades. Evacuar zonas bajas.",
            )
        return AlertResult(
            cuenca=cuenca,
            alert_level="NARANJA",
            risk_score=88.0,
            modo="MODO_A",
            ssi_score=ssi_score,
            precip_24h=precip_24h_mm,
            ttt_hours=ttt_hours,
            mensaje=f"🟠 ALERTA — Suelo en saturación crítica (SSI={ssi_score}%).",
            accion="Notificación técnica. Activar dashboard. Vigilancia continua.",
        )

    if ssi_score >= th_a["ssi_alto"]:
        return AlertResult(
            cuenca=cuenca,
            alert_level="NARANJA",
            risk_score=72.0,
            modo="MODO_A",
            ssi_score=ssi_score,
            precip_24h=precip_24h_mm,
            ttt_hours=ttt_hours,
            mensaje=f"🟠 ALERTA — SSI elevado ({ssi_score}%). Riesgo moderado-alto.",
            accion="Reporte técnico. Monitoreo cada 6h.",
        )

    if ssi_score >= th_a["ssi_moderado"]:
        return AlertResult(
            cuenca=cuenca,
            alert_level="AMARILLO",
            risk_score=52.0,
            modo="MODO_A",
            ssi_score=ssi_score,
            precip_24h=precip_24h_mm,
            ttt_hours=ttt_hours,
            mensaje=f"🟡 VIGILANCIA — SSI moderado ({ssi_score}%).",
            accion="Reporte diario automático.",
        )

    # ── Normal ───────────────────────────────────────────────────────
    return AlertResult(
        cuenca=cuenca,
        alert_level="VERDE",
        risk_score=ssi_score,
        modo="NORMAL",
        ssi_score=ssi_score,
        precip_24h=precip_24h_mm,
        ttt_hours=ttt_hours,
        mensaje=f"🟢 NORMAL — SSI={ssi_score}%. Sin riesgo inmediato.",
        accion="Monitoreo pasivo.",
    )


def should_send_alert(result: AlertResult) -> bool:
    """Retorna True si el nivel requiere notificación activa."""
    return result.alert_level in ("NARANJA", "ROJO")