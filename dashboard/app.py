"""
KAIRI-SIO-SATELITAL — Dashboard Principal (Trilingüe ES/DE/EN)
Tabs: Dashboard en tiempo real | Análisis Histórico
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
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-title { font-size:1.8rem; font-weight:700; color:#1E3A5F; margin-bottom:0; }
    .subtitle   { font-size:0.9rem; color:#666; margin-bottom:1rem; }
    .alert-box-rojo    { background:#fdedec; border-left:4px solid #e74c3c; padding:10px; border-radius:4px; margin:4px 0; }
    .alert-box-naranja { background:#fef5e7; border-left:4px solid #e67e22; padding:10px; border-radius:4px; margin:4px 0; }
    .alert-box-verde   { background:#eafaf1; border-left:4px solid #2ecc71; padding:10px; border-radius:4px; margin:4px 0; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# Traducciones
# ════════════════════════════════════════════════════════════════════

TEXTOS = {
    "ES": {
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
        "tab_dashboard":     "📡 Dashboard",
        "tab_historico":     "🔍 Análisis Histórico",
        "estado_actual":     "🗺️ Estado actual por cuenca",
        "panel_alertas":     "🚨 Panel de alertas",
        "sin_alertas":       "✅ Sin alertas activas",
        "ultimas_obs":       "**📋 Últimas observaciones:**",
        "evolucion":         "📈 Evolución histórica SSI",
        "sin_historico":     "Sin datos históricos. Ejecuta el Análisis Histórico para poblar la DB.",
        "detalle":           "🔬 Detalle por cuenca",
        "sin_datos":         "sin datos",
        "metodologia":       "📖 Metodología",
        "ttt_label":         "TTT",
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
        "sidebar_subtitulo": "*DANA-Frühwarnsystem*",
        "historico_label":   "Verlauf (Tage)",
        "componentes_label": "SSI-Komponenten anzeigen",
        "cuencas_label":     "**Überwachte Einzugsgebiete:**",
        "deteccion_label":   "**Doppelte Erkennung:**",
        "modo_a":            "💧 **Modus A** — Progressive Sättigung",
        "modo_b":            "⚡ **Modus B** — Trockener DANA + Extremregen",
        "actualizar":        "🔄 Daten aktualisieren",
        "ultima_act":        "Letzte Aktualisierung",
        "tab_dashboard":     "📡 Dashboard",
        "tab_historico":     "🔍 Historische Analyse",
        "estado_actual":     "🗺️ Aktueller Status",
        "panel_alertas":     "🚨 Warnungen",
        "sin_alertas":       "✅ Keine aktiven Warnungen",
        "ultimas_obs":       "**📋 Letzte Beobachtungen:**",
        "evolucion":         "📈 SSI-Zeitverlauf",
        "sin_historico":     "Keine Daten. Historische Analyse ausführen.",
        "detalle":           "🔬 Details",
        "sin_datos":         "keine Daten",
        "metodologia":       "📖 Methodik",
        "ttt_label":         "ZBS",
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
        "sidebar_subtitulo": "*DANA Early Warning System*",
        "historico_label":   "History (days)",
        "componentes_label": "Show SSI components",
        "cuencas_label":     "**Monitored basins:**",
        "deteccion_label":   "**Dual detection:**",
        "modo_a":            "💧 **Mode A** — Progressive saturation",
        "modo_b":            "⚡ **Mode B** — Dry DANA + extreme rainfall",
        "actualizar":        "🔄 Refresh data",
        "ultima_act":        "Last update",
        "tab_dashboard":     "📡 Dashboard",
        "tab_historico":     "🔍 Historical Analysis",
        "estado_actual":     "🗺️ Current status",
        "panel_alertas":     "🚨 Alert panel",
        "sin_alertas":       "✅ No active alerts",
        "ultimas_obs":       "**📋 Latest observations:**",
        "evolucion":         "📈 SSI historical trend",
        "sin_historico":     "No data. Run Historical Analysis to populate the DB.",
        "detalle":           "🔬 Detail",
        "sin_datos":         "no data",
        "metodologia":       "📖 Methodology",
        "ttt_label":         "TTT",
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

@st.cache_data(ttl=300)
def load_latest_data():
    return {c: get_latest_ssi(c) for c in CUENCAS}

@st.cache_data(ttl=300)
def load_history(days=90):
    return {c: get_ssi_history(c, days) for c in CUENCAS}

# ════════════════════════════════════════════════════════════════════
# Sidebar
# ════════════════════════════════════════════════════════════════════

with st.sidebar:
    lang_options = {"🇪🇸 Español":"ES","🇩🇪 Deutsch":"DE","🇬🇧 English":"EN"}
    lang = lang_options[st.selectbox("🌐 Sprache / Idioma / Language", list(lang_options.keys()))]
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
# Cabecera + Tabs
# ════════════════════════════════════════════════════════════════════

st.markdown(f'<p class="main-title">{T["titulo"]}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="subtitle">{T["subtitulo"]}</p>', unsafe_allow_html=True)

tab_dash, tab_hist = st.tabs([T["tab_dashboard"], T["tab_historico"]])

# ════════════════════════════════════════════════════════════════════
# TAB 1 — Dashboard tiempo real
# ════════════════════════════════════════════════════════════════════

with tab_dash:
    latest  = load_latest_data()
    history = load_history(dias_historico)

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
        st_folium(build_risk_map(latest), width=700, height=420, returned_objects=[])

    with col_alertas:
        st.subheader(T["panel_alertas"])
        alertas = [(c, d) for c, d in latest.items() if d and d.get("risk_level") in ("ALTO","CRITICO")]
        if alertas:
            for cuenca, data in alertas:
                nivel     = data["risk_level"]
                nivel_txt = T["nivel_labels"].get(nivel, nivel)
                css       = "alert-box-rojo" if nivel == "CRITICO" else "alert-box-naranja"
                ttt_val   = data.get("ttt_hours")
                ttt_str   = f"{T['ttt_label']}: {ttt_val}h" if ttt_val else ""
                st.markdown(
                    f'<div class="{css}"><b>{EMOJI_NIVEL[nivel]} {cuenca}</b><br>'
                    f'SSI: {data["ssi_score"]}% | {nivel_txt}<br>{ttt_str}</div>',
                    unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-box-verde">{T["sin_alertas"]}</div>', unsafe_allow_html=True)

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
        st.plotly_chart(build_ssi_timeseries(history), use_container_width=True)
    else:
        st.info(T["sin_historico"])

    st.divider()

    # Gauges + componentes
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
    with st.expander(T["metodologia"]):
        st.markdown(T["metodologia_texto"])

# ════════════════════════════════════════════════════════════════════
# TAB 2 — Análisis Histórico
# ════════════════════════════════════════════════════════════════════

with tab_hist:
    from dashboard.historical import render_historical_tab
    render_historical_tab(lang=lang)