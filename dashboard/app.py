"""
KAIRI-SIO-SATELITAL — Dashboard Principal (Trilingüe ES/DE/EN)
Sistema de Alerta Temprana de Inundaciones DANA
Cuencas mediterráneas: Júcar, Segura, Guadalquivir
"""
import sys
import os

# Permitir imports desde la raíz del proyecto
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
from streamlit_folium import st_folium
from datetime import datetime

from config.settings import CUENCAS
from database.queries import get_latest_ssi, get_ssi_history
from dashboard.map_component import build_risk_map
from dashboard.charts import build_ssi_timeseries, build_risk_gauge, build_components_bar

# ── Configuración página ─────────────────────────────────────────────
st.set_page_config(
    page_title="KAIRI-SIO-SATELITAL",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-title {
        font-size: 1.8rem; font-weight: 700;
        color: #1E3A5F; margin-bottom: 0;
    }
    .subtitle { font-size: 0.9rem; color: #666; margin-bottom: 1rem; }
    .alert-box-rojo    { background:#fdedec; border-left:4px solid #e74c3c;
                         padding:10px; border-radius:4px; margin:4px 0; }
    .alert-box-naranja { background:#fef5e7; border-left:4px solid #e67e22;
                         padding:10px; border-radius:4px; margin:4px 0; }
    .alert-box-verde   { background:#eafaf1; border-left:4px solid #2ecc71;
                         padding:10px; border-radius:4px; margin:4px 0; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# Traducciones / Übersetzungen / Translations
# ════════════════════════════════════════════════════════════════════

TEXTOS = {
    "ES": {
        "flag": "🇪🇸",
        "titulo":            "🛰️ KAIRI-SIO-SATELITAL",
        "subtitulo":         "Sistema de Alerta Temprana de Inundaciones DANA — Cuencas Mediterráneas",
        "sidebar_subtitulo": "*Sistema de Alerta Temprana DANA*",
        "historico_label":   "Histórico (días)",
        "componentes_label": "Mostrar componentes SSI",
        "cuencas_label":     "**Cuencas monitorizadas:**",
        "deteccion_label":   "**Detección dual:**",
        "modo_a":            "💧 **Modo A** — Saturación progresiva",
        "modo_b":            "⚡ **Modo B** — DANA seco + lluvia extrema",
        "actualizar":        "🔄 Actualizar datos",
        "ultima_act":        "Última actualización",
        "estado_actual":     "🗺️ Estado actual por cuenca",
        "panel_alertas":     "🚨 Panel de alertas",
        "sin_alertas":       "✅ Sin alertas activas",
        "ultimas_obs":       "**📋 Últimas observaciones:**",
        "evolucion":         "📈 Evolución histórica SSI",
        "sin_historico":     "Sin datos históricos suficientes. Ejecuta la validación DANA para poblar la DB.",
        "detalle":           "🔬 Detalle por cuenca",
        "sin_datos":         "sin datos",
        "metodologia":       "📖 Metodología — Cómo funciona el SSI",
        "ttt_label":         "TTT",
        "nivel_labels": {
            "BAJO": "BAJO", "MODERADO": "MODERADO",
            "ALTO": "ALTO", "CRITICO": "CRÍTICO", "SIN_DATOS": "SIN DATOS",
        },
        "metodologia_texto": """
**Soil Saturation Index (SSI)**

El SSI es un índice compuesto [0-100%] que estima la saturación del suelo
combinando tres fuentes satelitales:

| Fuente | Peso | Descripción |
|--------|------|-------------|
| Sentinel-1 SAR | 45% | Backscatter VV — humedad superficial del suelo |
| GPM IMERG V07  | 40% | Precipitación acumulada 7 días |
| Sentinel-2 NDVI inverso | 15% | Cobertura vegetal — absorción potencial |

**Sistema de detección dual:**
- **Modo A** (saturación progresiva): `SSI > 85%` + precipitación prevista `> 40mm`
- **Modo B** (DANA seco): `precip_24h > 60mm` + `SSI < 50%` → Validado contra DANA Valencia oct 2024

**Niveles:** 🟢 BAJO (<50%) · 🟡 MODERADO (50-70%) · 🟠 ALTO (70-85%) · 🔴 CRÍTICO (>85%)

*Desarrollado por Kent Valera Chirinos · Dresden, Alemania · 2026*
""",
    },
    "DE": {
        "flag": "🇩🇪",
        "titulo":            "🛰️ KAIRI-SIO-SATELITAL",
        "subtitulo":         "Frühwarnsystem für DANA-Überschwemmungen — Mediterrane Einzugsgebiete",
        "sidebar_subtitulo": "*DANA-Frühwarnsystem*",
        "historico_label":   "Verlauf (Tage)",
        "componentes_label": "SSI-Komponenten anzeigen",
        "cuencas_label":     "**Überwachte Einzugsgebiete:**",
        "deteccion_label":   "**Doppelte Erkennung:**",
        "modo_a":            "💧 **Modus A** — Progressive Sättigung",
        "modo_b":            "⚡ **Modus B** — Trockener DANA + Extremregen",
        "actualizar":        "🔄 Daten aktualisieren",
        "ultima_act":        "Letzte Aktualisierung",
        "estado_actual":     "🗺️ Aktueller Status je Einzugsgebiet",
        "panel_alertas":     "🚨 Warnungsübersicht",
        "sin_alertas":       "✅ Keine aktiven Warnungen",
        "ultimas_obs":       "**📋 Letzte Beobachtungen:**",
        "evolucion":         "📈 SSI-Zeitverlauf",
        "sin_historico":     "Nicht genügend historische Daten. DANA-Validierung ausführen.",
        "detalle":           "🔬 Details je Einzugsgebiet",
        "sin_datos":         "keine Daten",
        "metodologia":       "📖 Methodik — Wie der SSI funktioniert",
        "ttt_label":         "ZBS",
        "nivel_labels": {
            "BAJO": "NIEDRIG", "MODERADO": "MÄSSIG",
            "ALTO": "HOCH", "CRITICO": "KRITISCH", "SIN_DATOS": "KEINE DATEN",
        },
        "metodologia_texto": """
**Bodensättigungsindex (SSI)**

Der SSI ist ein zusammengesetzter Index [0-100%], der die Bodensättigung
aus drei Satellitenquellen schätzt:

| Quelle | Gewicht | Beschreibung |
|--------|---------|--------------|
| Sentinel-1 SAR | 45% | VV-Rückstreuung — Oberflächenbodenfeuchte |
| GPM IMERG V07  | 40% | Kumulierter Niederschlag 7 Tage |
| Sentinel-2 NDVI invers | 15% | Vegetationsbedeckung — Absorptionspotenzial |

**Doppeltes Erkennungssystem:**
- **Modus A** (progressive Sättigung): `SSI > 85%` + vorhergesagter Niederschlag `> 40mm`
- **Modus B** (trockener DANA): `Niederschlag_24h > 60mm` + `SSI < 50%` → Validiert gegen DANA Valencia Okt. 2024

**Warnstufen:** 🟢 NIEDRIG (<50%) · 🟡 MÄSSIG (50-70%) · 🟠 HOCH (70-85%) · 🔴 KRITISCH (>85%)

*Entwickelt von Kent Valera Chirinos · Dresden, Deutschland · 2026*
""",
    },
    "EN": {
        "flag": "🇬🇧",
        "titulo":            "🛰️ KAIRI-SIO-SATELITAL",
        "subtitulo":         "DANA Flood Early Warning System — Mediterranean River Basins",
        "sidebar_subtitulo": "*DANA Early Warning System*",
        "historico_label":   "History (days)",
        "componentes_label": "Show SSI components",
        "cuencas_label":     "**Monitored basins:**",
        "deteccion_label":   "**Dual detection:**",
        "modo_a":            "💧 **Mode A** — Progressive saturation",
        "modo_b":            "⚡ **Mode B** — Dry DANA + extreme rainfall",
        "actualizar":        "🔄 Refresh data",
        "ultima_act":        "Last update",
        "estado_actual":     "🗺️ Current status by basin",
        "panel_alertas":     "🚨 Alert panel",
        "sin_alertas":       "✅ No active alerts",
        "ultimas_obs":       "**📋 Latest observations:**",
        "evolucion":         "📈 SSI historical trend",
        "sin_historico":     "Not enough historical data. Run DANA validation to populate the DB.",
        "detalle":           "🔬 Detail by basin",
        "sin_datos":         "no data",
        "metodologia":       "📖 Methodology — How the SSI works",
        "ttt_label":         "TTT",
        "nivel_labels": {
            "BAJO": "LOW", "MODERADO": "MODERATE",
            "ALTO": "HIGH", "CRITICO": "CRITICAL", "SIN_DATOS": "NO DATA",
        },
        "metodologia_texto": """
**Soil Saturation Index (SSI)**

The SSI is a composite index [0-100%] estimating soil saturation
from three satellite sources:

| Source | Weight | Description |
|--------|--------|-------------|
| Sentinel-1 SAR | 45% | VV backscatter — surface soil moisture |
| GPM IMERG V07  | 40% | 7-day accumulated precipitation |
| Sentinel-2 NDVI inverse | 15% | Vegetation cover — absorption potential |

**Dual detection system:**
- **Mode A** (progressive saturation): `SSI > 85%` + forecast precipitation `> 40mm`
- **Mode B** (dry DANA): `precip_24h > 60mm` + `SSI < 50%` → Validated against Valencia DANA Oct 2024

**Alert levels:** 🟢 LOW (<50%) · 🟡 MODERATE (50-70%) · 🟠 HIGH (70-85%) · 🔴 CRITICAL (>85%)

*Developed by Kent Valera Chirinos · Dresden, Germany · 2026*
""",
    },
}

EMOJI_NIVEL = {
    "BAJO": "🟢", "MODERADO": "🟡",
    "ALTO": "🟠", "CRITICO": "🔴", "SIN_DATOS": "⚪",
}

# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_latest_data() -> dict:
    return {cuenca: get_latest_ssi(cuenca) for cuenca in CUENCAS}


@st.cache_data(ttl=300)
def load_history(days: int = 90) -> dict:
    return {cuenca: get_ssi_history(cuenca, days) for cuenca in CUENCAS}


# ════════════════════════════════════════════════════════════════════
# Sidebar
# ════════════════════════════════════════════════════════════════════

with st.sidebar:
    lang_options = {
        "🇪🇸 Español": "ES",
        "🇩🇪 Deutsch": "DE",
        "🇬🇧 English": "EN",
    }
    lang_sel = st.selectbox("🌐 Sprache / Idioma / Language", list(lang_options.keys()))
    lang = lang_options[lang_sel]
    T = TEXTOS[lang]

    st.markdown(f"## {T['titulo']}")
    st.markdown(T["sidebar_subtitulo"])
    st.divider()

    dias_historico      = st.slider(T["historico_label"], 30, 180, 90, step=30)
    mostrar_componentes = st.checkbox(T["componentes_label"], value=True)

    st.divider()
    st.markdown(T["cuencas_label"])
    for cuenca, meta in CUENCAS.items():
        st.markdown(f"- {cuenca} ({meta['confederacion']}) — {meta['prioridad']}")

    st.divider()
    st.markdown(T["deteccion_label"])
    st.markdown(T["modo_a"])
    st.markdown(T["modo_b"])

    st.divider()
    if st.button(T["actualizar"]):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"{T['ultima_act']}: {datetime.now().strftime('%d/%m/%Y %H:%M')}")


# ════════════════════════════════════════════════════════════════════
# Cabecera
# ════════════════════════════════════════════════════════════════════

st.markdown(f'<p class="main-title">{T["titulo"]}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="subtitle">{T["subtitulo"]}</p>', unsafe_allow_html=True)

latest  = load_latest_data()
history = load_history(dias_historico)

# ════════════════════════════════════════════════════════════════════
# Fila 1 — Métricas
# ════════════════════════════════════════════════════════════════════

cols = st.columns(len(CUENCAS))
for i, (cuenca, _) in enumerate(CUENCAS.items()):
    data = latest.get(cuenca)
    with cols[i]:
        if data:
            nivel     = data["risk_level"]
            nivel_txt = T["nivel_labels"].get(nivel, nivel)
            emoji     = EMOJI_NIVEL.get(nivel, "⚪")
            ttt_val   = data.get("ttt_hours")
            delta     = f"{T['ttt_label']}: {ttt_val}h" if ttt_val else f"{T['ttt_label']}: N/D"
            st.metric(label=f"{emoji} {cuenca}", value=f"{data['ssi_score']}%",
                      delta=delta, delta_color="inverse")
            st.caption(f"{nivel_txt} · {data.get('obs_date', 'N/D')}")
        else:
            st.metric(label=f"⚪ {cuenca}", value=T["sin_datos"].upper())

st.divider()

# ════════════════════════════════════════════════════════════════════
# Fila 2 — Mapa + Alertas
# ════════════════════════════════════════════════════════════════════

col_mapa, col_alertas = st.columns([2, 1])

with col_mapa:
    st.subheader(T["estado_actual"])
    st_folium(build_risk_map(latest), width=700, height=420, returned_objects=[])

with col_alertas:
    st.subheader(T["panel_alertas"])
    alertas_activas = [
        (c, d) for c, d in latest.items()
        if d and d.get("risk_level") in ("ALTO", "CRITICO")
    ]
    if alertas_activas:
        for cuenca, data in alertas_activas:
            nivel     = data["risk_level"]
            nivel_txt = T["nivel_labels"].get(nivel, nivel)
            css       = "alert-box-rojo" if nivel == "CRITICO" else "alert-box-naranja"
            ttt_val   = data.get("ttt_hours")
            ttt_str   = f"{T['ttt_label']}: {ttt_val}h" if ttt_val else ""
            st.markdown(
                f'<div class="{css}"><b>{EMOJI_NIVEL[nivel]} {cuenca}</b><br>'
                f'SSI: {data["ssi_score"]}% | {nivel_txt}<br>{ttt_str}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            f'<div class="alert-box-verde">{T["sin_alertas"]}</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown(T["ultimas_obs"])
    for cuenca, data in latest.items():
        if data:
            emoji     = EMOJI_NIVEL.get(data["risk_level"], "⚪")
            nivel_txt = T["nivel_labels"].get(data["risk_level"], data["risk_level"])
            st.markdown(f"{emoji} **{cuenca}** — {data['obs_date']} · SSI {data['ssi_score']}%")

st.divider()

# ════════════════════════════════════════════════════════════════════
# Fila 3 — Serie temporal
# ════════════════════════════════════════════════════════════════════

st.subheader(T["evolucion"])
if any(len(v) > 0 for v in history.values()):
    st.plotly_chart(build_ssi_timeseries(history), use_container_width=True)
else:
    st.info(T["sin_historico"])

st.divider()

# ════════════════════════════════════════════════════════════════════
# Fila 4 — Gauges + Componentes
# ════════════════════════════════════════════════════════════════════

if mostrar_componentes:
    st.subheader(T["detalle"])
    cols2 = st.columns(len(CUENCAS))
    for i, (cuenca, _) in enumerate(CUENCAS.items()):
        data = latest.get(cuenca)
        with cols2[i]:
            if data:
                st.plotly_chart(build_risk_gauge(data["ssi_score"], cuenca), use_container_width=True)
                st.plotly_chart(build_components_bar(data, cuenca), use_container_width=True)
            else:
                st.info(f"{cuenca}: {T['sin_datos']}")

st.divider()

# ════════════════════════════════════════════════════════════════════
# Footer
# ════════════════════════════════════════════════════════════════════

with st.expander(T["metodologia"]):
    st.markdown(T["metodologia_texto"])
