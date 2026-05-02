"""
KAIRI-SIO-SATELITAL — Dashboard Principal (Trilingüe ES/DE/EN)

Versión estable, sin unsafe_allow_html ni CSS custom.
- Sin slider, sin botón refrescar (causaban blanco)
- Sin <style> custom (causaba blanco al rerun)
- Sin <p>, <div> inyectados (causaban blanco al rerun)
- Solo componentes nativos de Streamlit
- Histórico fijo a 90 días, refresca cache cada 5 min
"""

import streamlit as st
from streamlit_folium import st_folium
from datetime import datetime

from config.settings import CUENCAS
from database.queries import get_latest_ssi, get_ssi_history
from dashboard.map_component import build_risk_map
from dashboard.charts import build_ssi_timeseries, build_risk_gauge, build_components_bar

st.set_page_config(
    page_title="KAIRI-SIO-SATELITAL",
    page_icon="🛰️",
    layout="wide",
)

# Días de histórico fijo
DIAS_HISTORICO = 90

# ════════════════════════════════════════════════════════════════════
# Traducciones
# ════════════════════════════════════════════════════════════════════

TEXTOS = {
    "ES": {
        "titulo":            "🛰️ KAIRI-SIO-SATELITAL",
        "subtitulo":         "Sistema de Alerta Temprana de Inundaciones DANA — Cuencas Mediterráneas",
        "sidebar_subtitulo": "Sistema de Alerta Temprana DANA",
        "historico_info":    f"📊 Histórico: últimos {DIAS_HISTORICO} días",
        "componentes_info":  "🔬 Componentes SSI visibles abajo",
        "cuencas_label":     "Cuencas monitorizadas:",
        "deteccion_label":   "Detección dual:",
        "modo_a":            "💧 Modo A — Saturación progresiva",
        "modo_b":            "⚡ Modo B — DANA seco + lluvia extrema",
        "auto_refresh":      "🔄 Datos refrescados automáticamente cada 5 min",
        "ultima_act":        "Última carga",
        "tab_dashboard":     "📡 Dashboard",
        "tab_historico":     "🔍 Análisis Histórico",
        "estado_actual":     "🗺️ Estado actual por cuenca",
        "panel_alertas":     "🚨 Panel de alertas",
        "sin_alertas":       "✅ Sin alertas activas",
        "ultimas_obs":       "📋 Últimas observaciones:",
        "evolucion":         "📈 Evolución histórica SSI (90 días)",
        "sin_historico":     "Sin datos históricos. Ejecuta el Análisis Histórico para poblar la DB.",
        "detalle":           "🔬 Detalle por cuenca",
        "sin_datos":         "sin datos",
        "metodologia":       "📖 Metodología",
        "ttt_label":         "TTT",
        "error_mapa":        "⚠️ No se pudo renderizar el mapa",
        "error_grafico":     "⚠️ No se pudo renderizar el gráfico",
        "error_historico":   "⚠️ Error en el análisis histórico",
        "nivel_labels": {
            "BAJO":"BAJO","MODERADO":"MODERADO","ALTO":"ALTO","CRITICO":"CRÍTICO","SIN_DATOS":"SIN DATOS",
        },
        "metodologia_texto": """
**SSI** = 0.45·SAR_norm + 0.40·Precip_norm + 0.15·NDVI_inv_norm

| Fuente | Peso | Descripción |
|--------|------|-------------|
| Sentinel-1 SAR | 45% | Backscatter VV — humedad superficial |
| GPM IMERG V07  | 40% | Precipitación acumulada 7 días |
| Sentinel-2 NDVI inverso | 15% | Cobertura vegetal |

**Modo A** — SSI > 85% + precip > 40mm · **Modo B** — precip_24h > 60mm + SSI < 50%

*Kent Valera Chirinos · Dresden · 2026*
""",
    },
    "DE": {
        "titulo":            "🛰️ KAIRI-SIO-SATELITAL",
        "subtitulo":         "Frühwarnsystem für DANA-Überschwemmungen — Mediterrane Einzugsgebiete",
        "sidebar_subtitulo": "DANA-Frühwarnsystem",
        "historico_info":    f"📊 Verlauf: letzte {DIAS_HISTORICO} Tage",
        "componentes_info":  "🔬 SSI-Komponenten unten sichtbar",
        "cuencas_label":     "Überwachte Einzugsgebiete:",
        "deteccion_label":   "Doppelte Erkennung:",
        "modo_a":            "💧 Modus A — Progressive Sättigung",
        "modo_b":            "⚡ Modus B — Trockener DANA + Extremregen",
        "auto_refresh":      "🔄 Daten alle 5 Min automatisch aktualisiert",
        "ultima_act":        "Letzte Ladung",
        "tab_dashboard":     "📡 Dashboard",
        "tab_historico":     "🔍 Historische Analyse",
        "estado_actual":     "🗺️ Aktueller Status",
        "panel_alertas":     "🚨 Warnungen",
        "sin_alertas":       "✅ Keine aktiven Warnungen",
        "ultimas_obs":       "📋 Letzte Beobachtungen:",
        "evolucion":         "📈 SSI-Zeitverlauf (90 Tage)",
        "sin_historico":     "Keine Daten. Historische Analyse ausführen.",
        "detalle":           "🔬 Details",
        "sin_datos":         "keine Daten",
        "metodologia":       "📖 Methodik",
        "ttt_label":         "ZBS",
        "error_mapa":        "⚠️ Karte konnte nicht gerendert werden",
        "error_grafico":     "⚠️ Diagramm konnte nicht gerendert werden",
        "error_historico":   "⚠️ Fehler in der historischen Analyse",
        "nivel_labels": {
            "BAJO":"NIEDRIG","MODERADO":"MÄSSIG","ALTO":"HOCH","CRITICO":"KRITISCH","SIN_DATOS":"KEINE DATEN",
        },
        "metodologia_texto": """
**SSI** = 0.45·SAR_norm + 0.40·Precip_norm + 0.15·NDVI_inv_norm

| Quelle | Gewicht | Beschreibung |
|--------|---------|--------------|
| Sentinel-1 SAR | 45% | VV-Rückstreuung |
| GPM IMERG V07  | 40% | Kumulierter Niederschlag 7 Tage |
| Sentinel-2 NDVI invers | 15% | Vegetationsbedeckung |

**Modus A** — SSI > 85% + Niederschlag > 40mm · **Modus B** — Niederschlag_24h > 60mm + SSI < 50%

*Kent Valera Chirinos · Dresden · 2026*
""",
    },
    "EN": {
        "titulo":            "🛰️ KAIRI-SIO-SATELITAL",
        "subtitulo":         "DANA Flood Early Warning System — Mediterranean River Basins",
        "sidebar_subtitulo": "DANA Early Warning System",
        "historico_info":    f"📊 History: last {DIAS_HISTORICO} days",
        "componentes_info":  "🔬 SSI components shown below",
        "cuencas_label":     "Monitored basins:",
        "deteccion_label":   "Dual detection:",
        "modo_a":            "💧 Mode A — Progressive saturation",
        "modo_b":            "⚡ Mode B — Dry DANA + extreme rainfall",
        "auto_refresh":      "🔄 Data auto-refreshed every 5 min",
        "ultima_act":        "Last load",
        "tab_dashboard":     "📡 Dashboard",
        "tab_historico":     "🔍 Historical Analysis",
        "estado_actual":     "🗺️ Current status",
        "panel_alertas":     "🚨 Alert panel",
        "sin_alertas":       "✅ No active alerts",
        "ultimas_obs":       "📋 Latest observations:",
        "evolucion":         "📈 SSI historical trend (90 days)",
        "sin_historico":     "No data. Run Historical Analysis to populate the DB.",
        "detalle":           "🔬 Detail",
        "sin_datos":         "no data",
        "metodologia":       "📖 Methodology",
        "ttt_label":         "TTT",
        "error_mapa":        "⚠️ Could not render map",
        "error_grafico":     "⚠️ Could not render chart",
        "error_historico":   "⚠️ Error in historical analysis",
        "nivel_labels": {
            "BAJO":"LOW","MODERADO":"MODERATE","ALTO":"HIGH","CRITICO":"CRITICAL","SIN_DATOS":"NO DATA",
        },
        "metodologia_texto": """
**SSI** = 0.45·SAR_norm + 0.40·Precip_norm + 0.15·NDVI_inv_norm

| Source | Weight | Description |
|--------|--------|-------------|
| Sentinel-1 SAR | 45% | VV backscatter — surface moisture |
| GPM IMERG V07  | 40% | 7-day accumulated precipitation |
| Sentinel-2 NDVI inverse | 15% | Vegetation cover |

**Mode A** — SSI > 85% + precip > 40mm · **Mode B** — precip_24h > 60mm + SSI < 50%

*Kent Valera Chirinos · Dresden · 2026*
""",
    },
}

EMOJI_NIVEL = {"BAJO":"🟢","MODERADO":"🟡","ALTO":"🟠","CRITICO":"🔴","SIN_DATOS":"⚪"}


# ════════════════════════════════════════════════════════════════════
# Loaders cacheados
# ════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner="Cargando datos recientes...")
def load_latest_data():
    out = {}
    for c in CUENCAS:
        try:
            out[c] = get_latest_ssi(c)
        except Exception as e:
            st.warning(f"Error leyendo {c}: {e}")
            out[c] = None
    return out

@st.cache_data(ttl=300, show_spinner="Cargando histórico...")
def load_history(days=90):
    out = {}
    for c in CUENCAS:
        try:
            out[c] = get_ssi_history(c, days)
        except Exception as e:
            st.warning(f"Error leyendo histórico {c}: {e}")
            out[c] = []
    return out


# ════════════════════════════════════════════════════════════════════
# Sidebar (solo selector idioma + textos informativos)
# ════════════════════════════════════════════════════════════════════

with st.sidebar:
    lang_options = {"🇪🇸 Español":"ES","🇩🇪 Deutsch":"DE","🇬🇧 English":"EN"}
    lang = lang_options[st.selectbox("🌐 Sprache / Idioma / Language", list(lang_options.keys()))]
    T = TEXTOS[lang]

    st.markdown(f"## {T['titulo']}")
    st.markdown(T["sidebar_subtitulo"])
    st.divider()

    st.markdown(T["historico_info"])
    st.markdown(T["componentes_info"])

    st.divider()
    st.markdown(T["cuencas_label"])
    for cuenca, meta in CUENCAS.items():
        st.markdown(f"- {cuenca} ({meta['confederacion']}) — {meta['prioridad']}")

    st.divider()
    st.markdown(T["deteccion_label"])
    st.markdown(T["modo_a"])
    st.markdown(T["modo_b"])

    st.divider()
    st.caption(T["auto_refresh"])
    st.caption(f"{T['ultima_act']}: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ════════════════════════════════════════════════════════════════════
# Cabecera + Tabs (sin HTML custom)
# ════════════════════════════════════════════════════════════════════

st.title(T["titulo"])
st.caption(T["subtitulo"])

tab_dash, tab_hist = st.tabs([T["tab_dashboard"], T["tab_historico"]])

# ════════════════════════════════════════════════════════════════════
# TAB 1 — Dashboard tiempo real
# ════════════════════════════════════════════════════════════════════

with tab_dash:
    latest  = load_latest_data()
    history = load_history(DIAS_HISTORICO)

    # Métricas
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
                st.caption(f"{nivel_txt} · {data.get('obs_date','N/D')}")
            else:
                st.metric(label=f"⚪ {cuenca}", value=T["sin_datos"].upper())

    st.divider()

    # Mapa + Alertas
    col_mapa, col_alertas = st.columns([2, 1])
    with col_mapa:
        st.subheader(T["estado_actual"])
        try:
            mapa = build_risk_map(latest)
            st_folium(mapa, width=700, height=420, returned_objects=[])
        except Exception as e:
            st.error(f"{T['error_mapa']}: {e}")

    with col_alertas:
        st.subheader(T["panel_alertas"])
        alertas = [(c, d) for c, d in latest.items() if d and d.get("risk_level") in ("ALTO","CRITICO")]
        if alertas:
            for cuenca, data in alertas:
                nivel     = data["risk_level"]
                nivel_txt = T["nivel_labels"].get(nivel, nivel)
                ttt_val   = data.get("ttt_hours")
                ttt_str   = f" | TTT: {ttt_val}h" if ttt_val else ""
                # Sin HTML custom, solo st.error / st.warning nativos
                msg = f"{EMOJI_NIVEL[nivel]} **{cuenca}** — SSI: {data['ssi_score']}% | {nivel_txt}{ttt_str}"
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
                emoji     = EMOJI_NIVEL.get(data["risk_level"], "⚪")
                nivel_txt = T["nivel_labels"].get(data["risk_level"], data["risk_level"])
                st.markdown(f"{emoji} **{cuenca}** — {data['obs_date']} · SSI {data['ssi_score']}%")

    st.divider()

    # Serie temporal
    st.subheader(T["evolucion"])
    if any(len(v) > 0 for v in history.values()):
        try:
            st.plotly_chart(build_ssi_timeseries(history), use_container_width=True)
        except Exception as e:
            st.error(f"{T['error_grafico']}: {e}")
    else:
        st.info(T["sin_historico"])

    st.divider()

    # Gauges + componentes
    st.subheader(T["detalle"])
    cols2 = st.columns(len(CUENCAS))
    for i, (cuenca, _) in enumerate(CUENCAS.items()):
        data = latest.get(cuenca)
        with cols2[i]:
            if data:
                try:
                    st.plotly_chart(build_risk_gauge(data["ssi_score"], cuenca), use_container_width=True)
                except Exception as e:
                    st.error(f"{T['error_grafico']} (gauge {cuenca}): {e}")
                try:
                    st.plotly_chart(build_components_bar(data, cuenca), use_container_width=True)
                except Exception as e:
                    st.error(f"{T['error_grafico']} (componentes {cuenca}): {e}")
            else:
                st.info(f"{cuenca}: {T['sin_datos']}")

    st.divider()
    with st.expander(T["metodologia"]):
        st.markdown(T["metodologia_texto"])

# ════════════════════════════════════════════════════════════════════
# TAB 2 — Análisis Histórico
# ════════════════════════════════════════════════════════════════════

with tab_hist:
    try:
        from dashboard.historical import render_historical_tab
        render_historical_tab(lang=lang)
    except Exception as e:
        st.error(f"{T['error_historico']}: {e}")
