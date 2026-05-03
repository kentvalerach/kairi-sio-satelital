"""
KAIRI-SIO-SATELITAL — Dashboard final
Versión basada en streamlit_test5 (que funciona estable en Streamlit Cloud).
- Selector idioma + plotly + tabs + folium + historical
- Textos completos en ES/DE/EN
- Panel de alertas con st.error/st.warning/st.success nativos
- Sin unsafe_allow_html, sin CSS custom, sin slider, sin botón refrescar
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
from dashboard.charts import build_ssi_timeseries, build_risk_gauge, build_components_bar
from dashboard.map_component import build_risk_map

st.set_page_config(page_title="KAIRI-SIO-SATELITAL", layout="wide")

DIAS_HISTORICO = 90

# ════════════════════════════════════════════════════════════════════
# Traducciones — solo strings, sin HTML
# ════════════════════════════════════════════════════════════════════

TXT = {
    "ES": {
        "titulo":          "🛰️ KAIRI-SIO-SATELITAL",
        "subtitulo":       "Sistema de Alerta Temprana DANA — Cuencas Mediterráneas",
        "tab1":            "📡 Dashboard",
        "tab2":            "🔍 Análisis Histórico",
        "metricas":        "Estado por cuenca",
        "mapa":            "🗺️ Mapa de riesgo",
        "alertas":         "🚨 Panel de alertas",
        "sin_alertas":     "✅ Sin alertas activas",
        "ultimas_obs":     "📋 Últimas observaciones",
        "evolucion":       "📈 Evolución histórica SSI (90 días)",
        "sin_historico":   "Sin datos históricos.",
        "detalle":         "🔬 Detalle por cuenca",
        "sin_datos":       "sin datos",
        "metodologia":     "📖 Metodología",
        "ttt":             "TTT",
        "info_lateral":    f"📊 Histórico: últimos {DIAS_HISTORICO} días",
        "auto_refresh":    "🔄 Refresco automático cada 5 min",
        "ultima_carga":    "Última carga",
        "cuencas_label":   "Cuencas monitorizadas:",
        "deteccion":       "Detección dual:",
        "modo_a":          "💧 Modo A — Saturación progresiva",
        "modo_b":          "⚡ Modo B — DANA seco + lluvia extrema",
        "niveles": {"BAJO":"BAJO","MODERADO":"MODERADO","ALTO":"ALTO","CRITICO":"CRÍTICO","SIN_DATOS":"SIN DATOS"},
        "metodologia_md": """
**SSI** = 0.45·SAR_norm + 0.40·Precip_norm + 0.15·NDVI_inv_norm

| Fuente | Peso | Descripción |
|--------|------|-------------|
| Sentinel-1 SAR | 45% | Backscatter VV — humedad superficial |
| GPM IMERG V07 | 40% | Precipitación acumulada 7 días |
| Sentinel-2 NDVI inverso | 15% | Cobertura vegetal |

**Modo A** — SSI > 85% + precip > 40mm
**Modo B** — precip_24h > 60mm + SSI < 50%

*Kent Valera Chirinos · Dresden · 2026*
""",
    },
    "DE": {
        "titulo":          "🛰️ KAIRI-SIO-SATELITAL",
        "subtitulo":       "DANA-Frühwarnsystem — Mediterrane Einzugsgebiete",
        "tab1":            "📡 Übersicht",
        "tab2":            "🔍 Historische Analyse",
        "metricas":        "Status nach Einzugsgebiet",
        "mapa":            "🗺️ Risikokarte",
        "alertas":         "🚨 Warnungen",
        "sin_alertas":     "✅ Keine aktiven Warnungen",
        "ultimas_obs":     "📋 Letzte Beobachtungen",
        "evolucion":       "📈 SSI-Zeitverlauf (90 Tage)",
        "sin_historico":   "Keine historischen Daten.",
        "detalle":         "🔬 Details pro Einzugsgebiet",
        "sin_datos":       "keine Daten",
        "metodologia":     "📖 Methodik",
        "ttt":             "ZBS",
        "info_lateral":    f"📊 Verlauf: letzte {DIAS_HISTORICO} Tage",
        "auto_refresh":    "🔄 Automatische Aktualisierung alle 5 Min",
        "ultima_carga":    "Letzte Ladung",
        "cuencas_label":   "Überwachte Einzugsgebiete:",
        "deteccion":       "Doppelte Erkennung:",
        "modo_a":          "💧 Modus A — Progressive Sättigung",
        "modo_b":          "⚡ Modus B — Trockener DANA + Extremregen",
        "niveles": {"BAJO":"NIEDRIG","MODERADO":"MÄSSIG","ALTO":"HOCH","CRITICO":"KRITISCH","SIN_DATOS":"KEINE DATEN"},
        "metodologia_md": """
**SSI** = 0.45·SAR_norm + 0.40·Precip_norm + 0.15·NDVI_inv_norm

| Quelle | Gewicht | Beschreibung |
|--------|---------|--------------|
| Sentinel-1 SAR | 45% | VV-Rückstreuung |
| GPM IMERG V07 | 40% | Niederschlag 7 Tage |
| Sentinel-2 NDVI invers | 15% | Vegetation |

**Modus A** — SSI > 85% + Niederschlag > 40mm
**Modus B** — Niederschlag_24h > 60mm + SSI < 50%

*Kent Valera Chirinos · Dresden · 2026*
""",
    },
    "EN": {
        "titulo":          "🛰️ KAIRI-SIO-SATELITAL",
        "subtitulo":       "DANA Flood Early Warning — Mediterranean Basins",
        "tab1":            "📡 Dashboard",
        "tab2":            "🔍 Historical Analysis",
        "metricas":        "Status by basin",
        "mapa":            "🗺️ Risk map",
        "alertas":         "🚨 Alert panel",
        "sin_alertas":     "✅ No active alerts",
        "ultimas_obs":     "📋 Latest observations",
        "evolucion":       "📈 SSI historical trend (90 days)",
        "sin_historico":   "No historical data.",
        "detalle":         "🔬 Detail per basin",
        "sin_datos":       "no data",
        "metodologia":     "📖 Methodology",
        "ttt":             "TTT",
        "info_lateral":    f"📊 History: last {DIAS_HISTORICO} days",
        "auto_refresh":    "🔄 Auto-refresh every 5 min",
        "ultima_carga":    "Last load",
        "cuencas_label":   "Monitored basins:",
        "deteccion":       "Dual detection:",
        "modo_a":          "💧 Mode A — Progressive saturation",
        "modo_b":          "⚡ Mode B — Dry DANA + extreme rainfall",
        "niveles": {"BAJO":"LOW","MODERADO":"MODERATE","ALTO":"HIGH","CRITICO":"CRITICAL","SIN_DATOS":"NO DATA"},
        "metodologia_md": """
**SSI** = 0.45·SAR_norm + 0.40·Precip_norm + 0.15·NDVI_inv_norm

| Source | Weight | Description |
|--------|--------|-------------|
| Sentinel-1 SAR | 45% | VV backscatter |
| GPM IMERG V07 | 40% | 7-day precipitation |
| Sentinel-2 NDVI inverse | 15% | Vegetation |

**Mode A** — SSI > 85% + precip > 40mm
**Mode B** — precip_24h > 60mm + SSI < 50%

*Kent Valera Chirinos · Dresden · 2026*
""",
    },
}

EMOJI = {"BAJO":"🟢","MODERADO":"🟡","ALTO":"🟠","CRITICO":"🔴","SIN_DATOS":"⚪"}


# ════════════════════════════════════════════════════════════════════
# Sidebar — solo selector idioma e info estática
# ════════════════════════════════════════════════════════════════════

with st.sidebar:
    lang_options = {"🇪🇸 Español":"ES","🇩🇪 Deutsch":"DE","🇬🇧 English":"EN"}
    lang = lang_options[st.selectbox("🌐 Sprache / Idioma / Language", list(lang_options.keys()))]

T = TXT[lang]

# Resto del sidebar después de calcular T
with st.sidebar:
    st.markdown(f"## {T['titulo']}")
    st.divider()
    st.markdown(T["info_lateral"])
    st.divider()
    st.markdown(T["cuencas_label"])
    for cuenca, meta in CUENCAS.items():
        st.markdown(f"- {cuenca} ({meta['confederacion']})")
    st.divider()
    st.markdown(T["deteccion"])
    st.markdown(T["modo_a"])
    st.markdown(T["modo_b"])
    st.divider()
    st.caption(T["auto_refresh"])
    st.caption(f"{T['ultima_carga']}: {datetime.now().strftime('%d/%m/%Y %H:%M')}")


# ════════════════════════════════════════════════════════════════════
# Loaders cacheados
# ════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_latest():
    out = {}
    for c in CUENCAS:
        try:
            out[c] = get_latest_ssi(c)
        except Exception as e:
            out[c] = None
    return out

@st.cache_data(ttl=300)
def load_hist():
    out = {}
    for c in CUENCAS:
        try:
            out[c] = get_ssi_history(c, DIAS_HISTORICO)
        except Exception as e:
            out[c] = []
    return out


# ════════════════════════════════════════════════════════════════════
# Cabecera
# ════════════════════════════════════════════════════════════════════

st.title(T["titulo"])
st.caption(T["subtitulo"])

latest = load_latest()
history = load_hist()

tab_dash, tab_hist = st.tabs([T["tab1"], T["tab2"]])

# ════════════════════════════════════════════════════════════════════
# TAB 1 — Dashboard
# ════════════════════════════════════════════════════════════════════

with tab_dash:
    # Métricas
    st.subheader(T["metricas"])
    cols = st.columns(len(CUENCAS))
    for i, cuenca in enumerate(CUENCAS):
        data = latest.get(cuenca)
        with cols[i]:
            if data:
                nivel = data["risk_level"]
                emoji = EMOJI.get(nivel, "⚪")
                ttt_val = data.get("ttt_hours")
                delta = f"{T['ttt']}: {ttt_val}h" if ttt_val else f"{T['ttt']}: N/D"
                st.metric(label=f"{emoji} {cuenca}",
                          value=f"{data['ssi_score']}%",
                          delta=delta,
                          delta_color="inverse")
                st.caption(f"{T['niveles'].get(nivel, nivel)} · {data.get('obs_date','N/D')}")
            else:
                st.metric(label=f"⚪ {cuenca}", value=T["sin_datos"].upper())

    st.divider()

    # Mapa + alertas
    col_mapa, col_alertas = st.columns([2, 1])

    with col_mapa:
        st.subheader(T["mapa"])
        try:
            mapa = build_risk_map(latest)
            st_folium(mapa, width=700, height=420, returned_objects=[])
        except Exception as e:
            st.error(f"Error mapa: {e}")

    with col_alertas:
        st.subheader(T["alertas"])
        alertas = [(c, d) for c, d in latest.items() if d and d.get("risk_level") in ("ALTO", "CRITICO")]
        if alertas:
            for cuenca, data in alertas:
                nivel = data["risk_level"]
                nivel_txt = T["niveles"].get(nivel, nivel)
                ttt_val = data.get("ttt_hours")
                ttt_str = f" | TTT: {ttt_val}h" if ttt_val else ""
                msg = f"{EMOJI[nivel]} **{cuenca}** — SSI: {data['ssi_score']}% | {nivel_txt}{ttt_str}"
                if nivel == "CRITICO":
                    st.error(msg)
                else:
                    st.warning(msg)
        else:
            st.success(T["sin_alertas"])

        st.divider()
        st.markdown(T["ultimas_obs"])
        for cuenca, data in latest.items():
            if data:
                emoji = EMOJI.get(data["risk_level"], "⚪")
                st.markdown(f"{emoji} **{cuenca}** — {data['obs_date']} · SSI {data['ssi_score']}%")

    st.divider()

    # Serie temporal
    st.subheader(T["evolucion"])
    if any(len(v) > 0 for v in history.values()):
        try:
            st.plotly_chart(build_ssi_timeseries(history), use_container_width=True)
        except Exception as e:
            st.error(f"Error timeseries: {e}")
    else:
        st.info(T["sin_historico"])

    st.divider()

    # Gauges + components
    st.subheader(T["detalle"])
    cols2 = st.columns(len(CUENCAS))
    for i, cuenca in enumerate(CUENCAS):
        data = latest.get(cuenca)
        with cols2[i]:
            if data:
                try:
                    st.plotly_chart(build_risk_gauge(data["ssi_score"], cuenca),
                                    use_container_width=True)
                    st.plotly_chart(build_components_bar(data, cuenca),
                                    use_container_width=True)
                except Exception as e:
                    st.error(f"Error charts {cuenca}: {e}")
            else:
                st.info(f"{cuenca}: {T['sin_datos']}")

    st.divider()
    with st.expander(T["metodologia"]):
        st.markdown(T["metodologia_md"])

# ════════════════════════════════════════════════════════════════════
# TAB 2 — Análisis Histórico
# ════════════════════════════════════════════════════════════════════

with tab_hist:
    try:
        from dashboard.historical import render_historical_tab
        render_historical_tab(lang=lang)
    except Exception as e:
        st.error(f"Error historical: {e}")

