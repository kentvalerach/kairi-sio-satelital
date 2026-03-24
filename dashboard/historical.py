"""
KAIRI-SIO-SATELITAL — Análisis Histórico
Tab que permite seleccionar cuenca + rango de fechas,
consulta GEE en tiempo real, calcula SSI y detecta si
se habría activado una alerta en ese período.
Límite: 90 días por consulta.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta, datetime

# ── Textos trilingues ────────────────────────────────────────────────
TEXTOS = {
    "ES": {
        "titulo":          "🔍 Análisis Histórico",
        "subtitulo":       "Consulta GEE en tiempo real para cualquier período pasado",
        "cuenca_label":    "Cuenca",
        "fecha_ini":       "Fecha inicio",
        "fecha_fin":       "Fecha fin",
        "btn_analizar":    "🚀 Analizar período",
        "limite_warning":  "⚠️ Máximo 90 días por consulta para no sobrecargar GEE.",
        "rango_error":     "❌ La fecha fin debe ser posterior a la fecha inicio.",
        "cargando":        "Consultando GEE y calculando SSI...",
        "sin_datos":       "No se obtuvieron datos satelitales para este período.",
        "resumen_titulo":  "📊 Resumen del período",
        "ssi_max":         "SSI máximo",
        "ssi_min":         "SSI mínimo",
        "ssi_medio":       "SSI medio",
        "alertas_alto":    "Obs. ALTO (≥70%)",
        "alertas_critico": "Obs. CRÍTICO (≥85%)",
        "veredicto":       "🔬 Veredicto",
        "grafico_titulo":  "Evolución SSI en el período",
        "tabla_titulo":    "📋 Datos detallados",
        "nivel_labels": {
            "BAJO": "BAJO", "MODERADO": "MODERADO",
            "ALTO": "ALTO", "CRITICO": "CRÍTICO",
        },
        "veredictos": {
            "critico":   "🔴 ALERTA CRÍTICA detectada — el sistema habría notificado",
            "alto":      "🟠 ALERTA ALTA detectada — vigilancia activada",
            "moderado":  "🟡 Período de vigilancia moderada",
            "bajo":      "🟢 Sin alertas en este período",
        },
    },
    "DE": {
        "titulo":          "🔍 Historische Analyse",
        "subtitulo":       "GEE-Abfrage in Echtzeit für beliebige vergangene Zeiträume",
        "cuenca_label":    "Einzugsgebiet",
        "fecha_ini":       "Startdatum",
        "fecha_fin":       "Enddatum",
        "btn_analizar":    "🚀 Zeitraum analysieren",
        "limite_warning":  "⚠️ Maximal 90 Tage pro Abfrage (GEE-Limit).",
        "rango_error":     "❌ Enddatum muss nach Startdatum liegen.",
        "cargando":        "GEE wird abgefragt und SSI berechnet...",
        "sin_datos":       "Keine Satellitendaten für diesen Zeitraum.",
        "resumen_titulo":  "📊 Zusammenfassung",
        "ssi_max":         "SSI Maximum",
        "ssi_min":         "SSI Minimum",
        "ssi_medio":       "SSI Durchschnitt",
        "alertas_alto":    "Obs. HOCH (≥70%)",
        "alertas_critico": "Obs. KRITISCH (≥85%)",
        "veredicto":       "🔬 Ergebnis",
        "grafico_titulo":  "SSI-Verlauf im Zeitraum",
        "tabla_titulo":    "📋 Detaildaten",
        "nivel_labels": {
            "BAJO": "NIEDRIG", "MODERADO": "MÄSSIG",
            "ALTO": "HOCH", "CRITICO": "KRITISCH",
        },
        "veredictos": {
            "critico":  "🔴 KRITISCHE WARNUNG erkannt — System hätte benachrichtigt",
            "alto":     "🟠 HOHE WARNUNG erkannt — Überwachung aktiviert",
            "moderado": "🟡 Mäßiger Überwachungszeitraum",
            "bajo":     "🟢 Keine Warnungen in diesem Zeitraum",
        },
    },
    "EN": {
        "titulo":          "🔍 Historical Analysis",
        "subtitulo":       "Real-time GEE query for any past period",
        "cuenca_label":    "Basin",
        "fecha_ini":       "Start date",
        "fecha_fin":       "End date",
        "btn_analizar":    "🚀 Analyze period",
        "limite_warning":  "⚠️ Maximum 90 days per query to avoid overloading GEE.",
        "rango_error":     "❌ End date must be after start date.",
        "cargando":        "Querying GEE and calculating SSI...",
        "sin_datos":       "No satellite data obtained for this period.",
        "resumen_titulo":  "📊 Period summary",
        "ssi_max":         "Max SSI",
        "ssi_min":         "Min SSI",
        "ssi_medio":       "Avg SSI",
        "alertas_alto":    "Obs. HIGH (≥70%)",
        "alertas_critico": "Obs. CRITICAL (≥85%)",
        "veredicto":       "🔬 Verdict",
        "grafico_titulo":  "SSI evolution in period",
        "tabla_titulo":    "📋 Detailed data",
        "nivel_labels": {
            "BAJO": "LOW", "MODERADO": "MODERATE",
            "ALTO": "HIGH", "CRITICO": "CRITICAL",
        },
        "veredictos": {
            "critico":  "🔴 CRITICAL ALERT detected — system would have notified",
            "alto":     "🟠 HIGH ALERT detected — monitoring activated",
            "moderado": "🟡 Moderate surveillance period",
            "bajo":     "🟢 No alerts in this period",
        },
    },
}

COLOR_NIVEL = {
    "BAJO": "#2ecc71", "MODERADO": "#f39c12",
    "ALTO": "#e67e22", "CRITICO": "#e74c3c",
}


# ════════════════════════════════════════════════════════════════════
# GEE — ingesta histórica
# ════════════════════════════════════════════════════════════════════

def fetch_historical_data(cuenca: str, fecha_ini: date, fecha_fin: date) -> list[dict]:
    """
    Descarga SAR + GPM + NDVI de GEE para un período dado.
    Intervalo: cada 6 días (revisita Sentinel-1).
    Retorna lista de dicts con los datos por fecha.
    """
    import ee
    from datetime import timedelta
    from config.settings import GEE_PROJECT, CUENCAS, SSI_PARAMS

    ee.Initialize(project=GEE_PROJECT)

    bbox = CUENCAS[cuenca]["bbox"]
    geom = ee.Geometry.Rectangle(bbox)

    resultados = []
    fecha_actual = fecha_ini

    while fecha_actual <= fecha_fin:
        f_str     = fecha_actual.strftime("%Y-%m-%d")
        f_fin_str = (fecha_actual + timedelta(days=6)).strftime("%Y-%m-%d")
        f_7d_str  = (fecha_actual - timedelta(days=7)).strftime("%Y-%m-%d")

        try:
            # SAR
            col_sar = (ee.ImageCollection("COPERNICUS/S1_GRD")
                       .filterBounds(geom)
                       .filterDate(f_str, f_fin_str)
                       .filter(ee.Filter.eq("instrumentMode", "IW"))
                       .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
                       .select("VV"))
            n_sar = col_sar.size().getInfo()

            vv_mean = None
            if n_sar > 0:
                stats = col_sar.mean().reduceRegion(
                    ee.Reducer.mean(), geom, 100, maxPixels=1e9
                ).getInfo()
                vv_mean = stats.get("VV")

            # GPM V07
            col_gpm = (ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
                       .filterBounds(geom)
                       .filterDate(f_7d_str, f_str)
                       .select("precipitation"))
            precip_total = col_gpm.sum().reduceRegion(
                ee.Reducer.mean(), geom, 11000, maxPixels=1e9
            ).getInfo()
            precip_7d = precip_total.get("precipitation", 0) or 0

            # NDVI
            col_ndvi = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                        .filterBounds(geom)
                        .filterDate(f_str, f_fin_str)
                        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
                        .map(lambda img: img.normalizedDifference(["B8", "B4"]).rename("NDVI")))
            n_ndvi = col_ndvi.size().getInfo()

            ndvi_mean = 0.3  # fallback si no hay imágenes
            if n_ndvi > 0:
                stats_ndvi = col_ndvi.mean().reduceRegion(
                    ee.Reducer.mean(), geom, 100, maxPixels=1e9
                ).getInfo()
                ndvi_mean = stats_ndvi.get("NDVI", 0.3) or 0.3

            resultados.append({
                "fecha":      fecha_actual,
                "vv_mean":    vv_mean,
                "precip_7d":  round(precip_7d, 2),
                "ndvi":       round(ndvi_mean, 4),
                "n_sar":      n_sar,
            })

        except Exception as e:
            resultados.append({
                "fecha":     fecha_actual,
                "vv_mean":   None,
                "precip_7d": 0,
                "ndvi":      0.3,
                "n_sar":     0,
                "error":     str(e),
            })

        fecha_actual += timedelta(days=6)

    return resultados


def compute_ssi_series(cuenca: str, raw_data: list[dict]) -> list[dict]:
    """Calcula SSI para cada observación de la serie."""
    from processing.soil_index import compute_ssi

    results = []
    for obs in raw_data:
        if obs.get("vv_mean") is None:
            continue
        ssi = compute_ssi(
            cuenca_name=cuenca,
            vv_mean=obs["vv_mean"],
            precip_7d_mm=obs["precip_7d"],
            ndvi=obs["ndvi"],
        )
        results.append({
            "fecha":         obs["fecha"],
            "ssi_score":     ssi["ssi_score"],
            "sar_norm":      ssi["sar_norm"],
            "precip_norm":   ssi["precip_norm"],
            "ndvi_inv_norm": ssi["ndvi_inv_norm"],
            "risk_level":    ssi["risk_level"],
            "vv_mean":       round(obs["vv_mean"], 3),
            "precip_7d":     obs["precip_7d"],
            "ndvi":          obs["ndvi"],
        })
    return results


# ════════════════════════════════════════════════════════════════════
# Gráfico
# ════════════════════════════════════════════════════════════════════

def build_historical_chart(series: list[dict], titulo: str) -> go.Figure:
    fig = go.Figure()

    # Bandas de riesgo
    fig.add_hrect(y0=0,  y1=50, fillcolor="#2ecc71", opacity=0.05, line_width=0)
    fig.add_hrect(y0=50, y1=70, fillcolor="#f39c12", opacity=0.07, line_width=0)
    fig.add_hrect(y0=70, y1=85, fillcolor="#e67e22", opacity=0.08, line_width=0)
    fig.add_hrect(y0=85, y1=100, fillcolor="#e74c3c", opacity=0.10, line_width=0)

    for y, label, color in [(50, "MOD", "#f39c12"), (70, "ALTO", "#e67e22"), (85, "CRIT", "#e74c3c")]:
        fig.add_hline(y=y, line_dash="dot", line_color=color, opacity=0.5,
                      annotation_text=label, annotation_position="right",
                      annotation_font_size=10)

    fechas  = [r["fecha"] for r in series]
    scores  = [r["ssi_score"] for r in series]
    niveles = [r["risk_level"] for r in series]
    colors  = [COLOR_NIVEL.get(n, "#95a5a6") for n in niveles]

    fig.add_trace(go.Scatter(
        x=fechas, y=scores,
        mode="lines+markers",
        name="SSI",
        line=dict(color="#3498db", width=2),
        marker=dict(size=8, color=colors, line=dict(width=1, color="white")),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "SSI: %{y:.1f}%<br>"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        title=titulo,
        xaxis_title="Fecha",
        yaxis_title="SSI (%)",
        yaxis=dict(range=[0, 100]),
        height=380,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=60, t=50, b=40),
    )
    return fig


# ════════════════════════════════════════════════════════════════════
# Render principal — llamado desde app.py
# ════════════════════════════════════════════════════════════════════

def render_historical_tab(lang: str = "ES"):
    """Renderiza el tab histórico completo."""
    from config.settings import CUENCAS

    T = TEXTOS[lang]

    st.subheader(T["titulo"])
    st.caption(T["subtitulo"])
    st.info(T["limite_warning"])

    # ── Controles ────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        cuenca = st.selectbox(T["cuenca_label"], list(CUENCAS.keys()))
    with col2:
        fecha_ini = st.date_input(
            T["fecha_ini"],
            value=date(2024, 10, 1),
            min_value=date(2015, 1, 1),
            max_value=date.today() - timedelta(days=7),
        )
    with col3:
        fecha_fin = st.date_input(
            T["fecha_fin"],
            value=date(2024, 10, 29),
            min_value=date(2015, 1, 1),
            max_value=date.today(),
        )

    # Validaciones
    if fecha_fin <= fecha_ini:
        st.error(T["rango_error"])
        return

    delta = (fecha_fin - fecha_ini).days
    if delta > 90:
        st.warning(f"{T['limite_warning']} ({delta} días seleccionados → se recortará a 90)")
        fecha_fin = fecha_ini + timedelta(days=90)

    # ── Botón analizar ────────────────────────────────────────────────
    if st.button(T["btn_analizar"], type="primary"):

        with st.spinner(T["cargando"]):
            # 1. Descargar datos GEE
            raw = fetch_historical_data(cuenca, fecha_ini, fecha_fin)

            # 2. Calcular SSI
            series = compute_ssi_series(cuenca, raw)

        if not series:
            st.warning(T["sin_datos"])
            return

        df = pd.DataFrame(series)

        # ── Métricas resumen ─────────────────────────────────────────
        st.divider()
        st.subheader(T["resumen_titulo"])

        ssi_max   = df["ssi_score"].max()
        ssi_min   = df["ssi_score"].min()
        ssi_medio = round(df["ssi_score"].mean(), 2)
        n_alto    = len(df[df["ssi_score"] >= 70])
        n_critico = len(df[df["ssi_score"] >= 85])

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(T["ssi_max"],         f"{ssi_max}%")
        c2.metric(T["ssi_min"],         f"{ssi_min}%")
        c3.metric(T["ssi_medio"],       f"{ssi_medio}%")
        c4.metric(T["alertas_alto"],    n_alto)
        c5.metric(T["alertas_critico"], n_critico)

        # ── Veredicto ────────────────────────────────────────────────
        st.divider()
        st.subheader(T["veredicto"])

        if n_critico > 0:
            fecha_critica = df[df["ssi_score"] >= 85]["fecha"].iloc[0]
            st.error(f"{T['veredictos']['critico']} · Primera detección: {fecha_critica}")
        elif n_alto > 0:
            fecha_alta = df[df["ssi_score"] >= 70]["fecha"].iloc[0]
            st.warning(f"{T['veredictos']['alto']} · Primera detección: {fecha_alta}")
        elif ssi_medio >= 50:
            st.warning(T["veredictos"]["moderado"])
        else:
            st.success(T["veredictos"]["bajo"])

        # Caso especial DANA seco
        precip_max = df["precip_7d"].max()
        if precip_max > 60 and ssi_medio < 50:
            st.error(
                f"⚡ **Modo B (DANA seco) detectado** — "
                f"Precip. máx 7d: {precip_max}mm sobre suelo seco (SSI medio {ssi_medio}%)"
            )

        # ── Gráfico ──────────────────────────────────────────────────
        st.divider()
        fig = build_historical_chart(series, T["grafico_titulo"])
        st.plotly_chart(fig, use_container_width=True)

        # ── Tabla detallada ──────────────────────────────────────────
        st.divider()
        st.subheader(T["tabla_titulo"])

        df_display = df.copy()
        df_display["risk_level"] = df_display["risk_level"].map(
            lambda x: T["nivel_labels"].get(x, x)
        )
        df_display.columns = [
            "Fecha", "SSI%", "SAR%", "Precip%", "NDVI-inv%",
            "Nivel", "VV(dB)", "Precip7d(mm)", "NDVI"
        ]
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # ── Guardar en DB ────────────────────────────────────────────
        try:
            from database.queries import insert_satellite_obs, insert_ssi_score
            saved = 0
            for obs, ssi_row in zip(raw, series):
                insert_satellite_obs({
                    "cuenca":        cuenca,
                    "obs_date":      obs["fecha"],
                    "vv_mean_db":    obs.get("vv_mean"),
                    "vv_std_db":     None,
                    "precip_7d_mm":  obs["precip_7d"],
                    "precip_max_1h": None,
                    "ndvi_mean":     obs["ndvi"],
                    "ndvi_std":      None,
                    "n_sar_images":  obs["n_sar"],
                })
                insert_ssi_score({
                    "cuenca":        cuenca,
                    "obs_date":      ssi_row["fecha"],
                    "ssi_score":     ssi_row["ssi_score"],
                    "sar_norm":      ssi_row["sar_norm"],
                    "precip_norm":   ssi_row["precip_norm"],
                    "ndvi_inv_norm": ssi_row["ndvi_inv_norm"],
                    "risk_level":    ssi_row["risk_level"],
                    "ttt_hours":     None,
                })
                saved += 1
            st.caption(f"✅ {saved} observaciones guardadas en PostgreSQL")
        except Exception as e:
            st.caption(f"⚠️ DB: {e}")