"""
KAIRI-SIO-SATELITAL — Análisis Histórico (DB-only)
Tab que consulta SOLO la base de datos Supabase, sin llamar a GEE.
Ofrece tres vistas:
  1. Selector cuenca + rango fechas + gráfica SSI
  2. Tabla con todas las observaciones del período
  3. Comparador de cuencas en una sola gráfica
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta

from config.settings import CUENCAS
from database.queries import get_ssi_history


COLOR_NIVEL = {
    "BAJO":     "#2ecc71",
    "MODERADO": "#f39c12",
    "ALTO":     "#e67e22",
    "CRITICO":  "#e74c3c",
    "SIN_DATOS":"#95a5a6",
}


# ════════════════════════════════════════════════════════════════════
# Textos trilingües
# ════════════════════════════════════════════════════════════════════

TEXTOS = {
    "ES": {
        "titulo":          "🔍 Análisis Histórico",
        "subtitulo":       "Consulta de datos históricos almacenados en la base de datos",
        "info_db":         "📊 Los datos mostrados provienen de la base de datos. El pipeline `pipeline_runner.py` los actualiza automáticamente cada 6 días.",
        "vista_label":     "Vista",
        "vista_individual":"📈 Cuenca individual",
        "vista_tabla":     "📋 Tabla de observaciones",
        "vista_compara":   "🔀 Comparador de cuencas",
        "cuenca_label":    "Cuenca",
        "dias_label":      "Días de histórico",
        "sin_datos":       "Sin datos para esta cuenca en el período seleccionado.",
        "resumen_titulo":  "📊 Resumen del período",
        "ssi_max":         "SSI máximo",
        "ssi_min":         "SSI mínimo",
        "ssi_medio":       "SSI medio",
        "alertas_alto":    "Obs. ALTO (≥70%)",
        "alertas_critico": "Obs. CRÍTICO (≥85%)",
        "tabla_titulo":    "📋 Observaciones en el período",
        "compara_titulo":  "🔀 Comparación de cuencas",
        "fecha":           "Fecha",
        "ssi":             "SSI (%)",
        "nivel":           "Nivel",
        "sar":             "SAR norm",
        "precip":          "Precip norm",
        "ndvi":            "NDVI inv",
        "error_carga":     "⚠️ Error al cargar datos",
    },
    "DE": {
        "titulo":          "🔍 Historische Analyse",
        "subtitulo":       "Abfrage historischer Daten aus der Datenbank",
        "info_db":         "📊 Die angezeigten Daten stammen aus der Datenbank. Die Pipeline `pipeline_runner.py` aktualisiert sie automatisch alle 6 Tage.",
        "vista_label":     "Ansicht",
        "vista_individual":"📈 Einzelnes Einzugsgebiet",
        "vista_tabla":     "📋 Beobachtungstabelle",
        "vista_compara":   "🔀 Vergleich",
        "cuenca_label":    "Einzugsgebiet",
        "dias_label":      "Tage Verlauf",
        "sin_datos":       "Keine Daten für dieses Einzugsgebiet im ausgewählten Zeitraum.",
        "resumen_titulo":  "📊 Zeitraum-Übersicht",
        "ssi_max":         "Max. SSI",
        "ssi_min":         "Min. SSI",
        "ssi_medio":       "Mittl. SSI",
        "alertas_alto":    "Beob. HOCH (≥70%)",
        "alertas_critico": "Beob. KRITISCH (≥85%)",
        "tabla_titulo":    "📋 Beobachtungen im Zeitraum",
        "compara_titulo":  "🔀 Vergleich der Einzugsgebiete",
        "fecha":           "Datum",
        "ssi":             "SSI (%)",
        "nivel":           "Stufe",
        "sar":             "SAR norm",
        "precip":          "Niederschlag norm",
        "ndvi":            "NDVI invers",
        "error_carga":     "⚠️ Fehler beim Laden",
    },
    "EN": {
        "titulo":          "🔍 Historical Analysis",
        "subtitulo":       "Query historical data stored in the database",
        "info_db":         "📊 Data shown comes from the database. The `pipeline_runner.py` updates it automatically every 6 days.",
        "vista_label":     "View",
        "vista_individual":"📈 Single basin",
        "vista_tabla":     "📋 Observation table",
        "vista_compara":   "🔀 Basin comparator",
        "cuenca_label":    "Basin",
        "dias_label":      "History (days)",
        "sin_datos":       "No data for this basin in the selected period.",
        "resumen_titulo":  "📊 Period summary",
        "ssi_max":         "Max SSI",
        "ssi_min":         "Min SSI",
        "ssi_medio":       "Mean SSI",
        "alertas_alto":    "Obs. HIGH (≥70%)",
        "alertas_critico": "Obs. CRITICAL (≥85%)",
        "tabla_titulo":    "📋 Observations in period",
        "compara_titulo":  "🔀 Basin comparison",
        "fecha":           "Date",
        "ssi":             "SSI (%)",
        "nivel":           "Level",
        "sar":             "SAR norm",
        "precip":          "Precip norm",
        "ndvi":            "NDVI inv",
        "error_carga":     "⚠️ Error loading data",
    },
}


# ════════════════════════════════════════════════════════════════════
# Loaders cacheados
# ════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def load_history_for(cuenca: str, dias: int):
    """Carga histórico de una cuenca con manejo defensivo."""
    try:
        return get_ssi_history(cuenca, dias)
    except Exception as e:
        st.warning(f"Error {cuenca}: {e}")
        return []


@st.cache_data(ttl=300, show_spinner=False)
def load_history_all(dias: int):
    """Carga histórico de todas las cuencas."""
    out = {}
    for c in CUENCAS:
        out[c] = load_history_for(c, dias)
    return out


# ════════════════════════════════════════════════════════════════════
# Gráficos
# ════════════════════════════════════════════════════════════════════

def build_individual_chart(series: list[dict], titulo: str) -> go.Figure:
    """Gráfica de una sola cuenca con bandas de riesgo."""
    fig = go.Figure()

    # Bandas de riesgo de fondo
    fig.add_hrect(y0=0,  y1=50, fillcolor="#2ecc71", opacity=0.05, line_width=0)
    fig.add_hrect(y0=50, y1=70, fillcolor="#f39c12", opacity=0.07, line_width=0)
    fig.add_hrect(y0=70, y1=85, fillcolor="#e67e22", opacity=0.08, line_width=0)
    fig.add_hrect(y0=85, y1=100, fillcolor="#e74c3c", opacity=0.10, line_width=0)

    # Líneas de umbral
    for y, label, color in [(50, "MOD", "#f39c12"), (70, "ALTO", "#e67e22"), (85, "CRIT", "#e74c3c")]:
        fig.add_hline(y=y, line_dash="dot", line_color=color, opacity=0.5,
                      annotation_text=label, annotation_position="right",
                      annotation_font_size=10)

    fechas  = [r["obs_date"] for r in series]
    scores  = [r["ssi_score"] for r in series]
    niveles = [r.get("risk_level", "SIN_DATOS") for r in series]
    colors  = [COLOR_NIVEL.get(n, "#95a5a6") for n in niveles]

    fig.add_trace(go.Scatter(
        x=fechas, y=scores,
        mode="lines+markers",
        name="SSI",
        line=dict(color="#3498db", width=2),
        marker=dict(size=8, color=colors, line=dict(width=1, color="white")),
        hovertemplate="<b>%{x}</b><br>SSI: %{y:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        title=titulo,
        xaxis_title="",
        yaxis_title="SSI (%)",
        yaxis=dict(range=[0, 100]),
        height=380,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=60, t=50, b=40),
    )
    return fig


def build_comparator_chart(history_all: dict, titulo: str) -> go.Figure:
    """Gráfica comparativa de las 3 cuencas."""
    fig = go.Figure()

    paleta = {
        "Jucar":        "#3498db",
        "Segura":       "#9b59b6",
        "Guadalquivir": "#1abc9c",
    }

    # Líneas de umbral
    for y, label, color in [(50, "MOD", "#f39c12"), (70, "ALTO", "#e67e22"), (85, "CRIT", "#e74c3c")]:
        fig.add_hline(y=y, line_dash="dot", line_color=color, opacity=0.4,
                      annotation_text=label, annotation_position="right",
                      annotation_font_size=10)

    for cuenca, series in history_all.items():
        if not series:
            continue
        fechas = [r["obs_date"] for r in series]
        scores = [r["ssi_score"] for r in series]
        fig.add_trace(go.Scatter(
            x=fechas, y=scores,
            mode="lines+markers",
            name=cuenca,
            line=dict(color=paleta.get(cuenca, "#7f8c8d"), width=2),
            marker=dict(size=6),
            hovertemplate=f"<b>{cuenca}</b><br>%{{x}}<br>SSI: %{{y:.1f}}%<extra></extra>",
        ))

    fig.update_layout(
        title=titulo,
        xaxis_title="",
        yaxis_title="SSI (%)",
        yaxis=dict(range=[0, 100]),
        height=420,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=60, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ════════════════════════════════════════════════════════════════════
# Render principal — llamado desde app.py
# ════════════════════════════════════════════════════════════════════

def render_historical_tab(lang: str = "ES"):
    """Renderiza el tab histórico — solo DB, sin GEE."""
    T = TEXTOS.get(lang, TEXTOS["ES"])

    st.subheader(T["titulo"])
    st.caption(T["subtitulo"])
    st.info(T["info_db"])

    # Selector de vista (radio en lugar de tabs anidados, más estable)
    vista = st.radio(
        T["vista_label"],
        options=[T["vista_individual"], T["vista_tabla"], T["vista_compara"]],
        horizontal=True,
        label_visibility="collapsed",
    )

    # Selector de días (constantes prefijadas, sin slider — sliders rompían reruns)
    dias = st.selectbox(
        T["dias_label"],
        options=[30, 60, 90, 180, 365],
        index=2,  # default 90
    )

    st.divider()

    # ── VISTA 1: Individual ────────────────────────────────────────
    if vista == T["vista_individual"]:
        cuenca = st.selectbox(T["cuenca_label"], list(CUENCAS.keys()))
        try:
            series = load_history_for(cuenca, dias)
        except Exception as e:
            st.error(f"{T['error_carga']}: {e}")
            return

        if not series:
            st.warning(T["sin_datos"])
            return

        # Resumen con métricas
        scores = [r["ssi_score"] for r in series]
        niveles = [r.get("risk_level", "SIN_DATOS") for r in series]
        n_alto = sum(1 for n in niveles if n in ("ALTO", "CRITICO"))
        n_crit = sum(1 for n in niveles if n == "CRITICO")

        st.markdown(f"### {T['resumen_titulo']}")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(T["ssi_max"],         f"{max(scores):.1f}%")
        c2.metric(T["ssi_min"],         f"{min(scores):.1f}%")
        c3.metric(T["ssi_medio"],       f"{sum(scores)/len(scores):.1f}%")
        c4.metric(T["alertas_alto"],    n_alto)
        c5.metric(T["alertas_critico"], n_crit)

        st.divider()

        # Gráfica individual
        try:
            fig = build_individual_chart(series, f"{cuenca} — {dias} {T['dias_label'].lower()}")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"{T['error_carga']}: {e}")

    # ── VISTA 2: Tabla ─────────────────────────────────────────────
    elif vista == T["vista_tabla"]:
        st.markdown(f"### {T['tabla_titulo']}")
        cuenca = st.selectbox(T["cuenca_label"], list(CUENCAS.keys()))
        try:
            series = load_history_for(cuenca, dias)
        except Exception as e:
            st.error(f"{T['error_carga']}: {e}")
            return

        if not series:
            st.warning(T["sin_datos"])
            return

        # Construir DataFrame
        rows = []
        for r in series:
            rows.append({
                T["fecha"]:  r["obs_date"],
                T["ssi"]:    r["ssi_score"],
                T["nivel"]:  r.get("risk_level", "—"),
                T["sar"]:    r.get("sar_norm", None),
                T["precip"]: r.get("precip_norm", None),
                T["ndvi"]:   r.get("ndvi_inv_norm", None),
            })
        df = pd.DataFrame(rows)
        df = df.sort_values(by=T["fecha"], ascending=False).reset_index(drop=True)

        st.dataframe(df, use_container_width=True, height=400)
        st.caption(f"{len(df)} observaciones")

    # ── VISTA 3: Comparador ────────────────────────────────────────
    elif vista == T["vista_compara"]:
        st.markdown(f"### {T['compara_titulo']}")
        try:
            history_all = load_history_all(dias)
        except Exception as e:
            st.error(f"{T['error_carga']}: {e}")
            return

        # Verificamos que haya algún dato
        total_obs = sum(len(v) for v in history_all.values())
        if total_obs == 0:
            st.warning(T["sin_datos"])
            return

        try:
            fig = build_comparator_chart(history_all, f"{dias} {T['dias_label'].lower()}")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"{T['error_carga']}: {e}")

        # Resumen por cuenca
        st.divider()
        cols = st.columns(len(CUENCAS))
        for i, (cuenca, series) in enumerate(history_all.items()):
            with cols[i]:
                if series:
                    scores = [r["ssi_score"] for r in series]
                    st.metric(
                        cuenca,
                        f"{sum(scores)/len(scores):.1f}%",
                        delta=f"{len(scores)} obs",
                    )
                else:
                    st.metric(cuenca, "—")
