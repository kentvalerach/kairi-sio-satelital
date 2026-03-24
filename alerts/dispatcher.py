"""
KAIRI-SIO-SATELITAL — Alert Dispatcher
Envía alertas por Telegram al chat personal y/o grupo.
Soporta Modo A (saturación) y Modo B (DANA seco).
"""

import requests
from datetime import datetime
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from alerts.thresholds import AlertResult, should_send_alert
from database.queries import insert_alert_log

# ── Emojis por nivel ─────────────────────────────────────────────────
EMOJI_NIVEL = {
    "VERDE":    "🟢",
    "AMARILLO": "🟡",
    "NARANJA":  "🟠",
    "ROJO":     "🔴",
}

EMOJI_MODO = {
    "MODO_A": "💧",
    "MODO_B": "⚡",
    "NORMAL": "✅",
}


def _build_message(result: AlertResult) -> str:
    """Construye el mensaje Telegram formateado en HTML."""
    emoji  = EMOJI_NIVEL[result.alert_level]
    modo   = EMOJI_MODO.get(result.modo, "")
    ts     = datetime.now().strftime("%d/%m/%Y %H:%M UTC")
    ttt    = f"{result.ttt_hours}h" if result.ttt_hours is not None else "N/D"

    modo_label = {
        "MODO_A": "Saturación progresiva",
        "MODO_B": "DANA seco — lluvia extrema",
        "NORMAL": "Normal",
    }.get(result.modo, result.modo)

    msg = (
        f"{emoji} <b>KAIRI-SIO-SATELITAL — {result.alert_level}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌊 <b>Cuenca:</b> {result.cuenca}\n"
        f"{modo} <b>Modo:</b> {modo_label}\n"
        f"📊 <b>SSI:</b> {result.ssi_score}%\n"
        f"🌧 <b>Precip 24h:</b> {result.precip_24h} mm\n"
        f"⏱ <b>TTT:</b> {ttt}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ {result.mensaje}\n"
        f"📋 <b>Acción:</b> {result.accion}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {ts}"
    )
    return msg


def send_telegram(chat_id: str, message: str) -> bool:
    """Envía un mensaje a un chat_id específico. Retorna True si OK."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":    chat_id,
        "text":       message,
        "parse_mode": "HTML",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            return True
        else:
            print(f"  ⚠ Telegram error {resp.status_code}: {resp.text[:200]}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Telegram conexión fallida: {e}")
        return False


def dispatch_alert(
    result: AlertResult,
    extra_chat_ids: list[str] | None = None,
    force: bool = False,
) -> bool:
    """
    Evalúa y envía alerta si el nivel lo requiere.

    Parámetros
    ----------
    result        : AlertResult de thresholds.evaluate_risk()
    extra_chat_ids: lista de chat_ids adicionales (ej. grupo)
    force         : enviar aunque sea VERDE/AMARILLO (para pruebas)

    Retorna True si se envió al menos una notificación.
    """
    if not force and not should_send_alert(result):
        print(f"  ℹ {result.cuenca}: {result.alert_level} — sin notificación")
        return False

    message = _build_message(result)

    # ── Destinatarios ────────────────────────────────────────────────
    chat_ids = [TELEGRAM_CHAT_ID]
    if extra_chat_ids:
        chat_ids.extend(extra_chat_ids)
    chat_ids = [c for c in chat_ids if c]

    if not chat_ids:
        print("  ⚠ No hay TELEGRAM_CHAT_ID configurado en .env")
        return False

    sent = False
    for chat_id in chat_ids:
        ok = send_telegram(chat_id, message)
        if ok:
            print(f"  ✅ Alerta enviada a chat_id={chat_id}")
            sent = True
        else:
            print(f"  ❌ Fallo envío a chat_id={chat_id}")

    # ── Registrar en DB ──────────────────────────────────────────────
    if sent:
        try:
            insert_alert_log({
                "cuenca":      result.cuenca,
                "alert_level": result.alert_level,
                "ssi_score":   result.ssi_score,
                "ttt_hours":   result.ttt_hours,
                "channel":     "telegram",
            })
        except Exception as e:
            print(f"  ⚠ Error guardando en alert_log: {e}")

    return sent


def send_test_alert(cuenca: str = "Jucar") -> bool:
    """
    Envía una alerta de prueba forzada para verificar la configuración.
    Simula una DANA seco (Modo B) sobre el Júcar con valores reales oct-2024.
    """
    from alerts.thresholds import evaluate_risk
    print(f"🧪 Enviando alerta de prueba para {cuenca}...")

    result = evaluate_risk(
        cuenca=cuenca,
        ssi_score=44.86,
        precip_24h_mm=82.6,
        precip_prevista_6h_mm=0.0,
        ttt_hours=3.2,
    )
    print(f"   Nivel calculado: {result.alert_level} ({result.modo})")
    return dispatch_alert(result, force=True)