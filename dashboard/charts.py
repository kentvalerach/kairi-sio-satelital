"""
KAIRI-SIO-SATELITAL — Charts
Gráficos Plotly para el dashboard: series temporales SSI y barras de riesgo.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots


COLORES_NIVEL = {
    "BAJO":     "#2ecc71",
    "MODERADO": "#f39c12",
    "ALTO":     "#e67e22",
    "CRITICO":  "#e74c3c",
}

COLORES_CUENCA = {
    "Jucar":        "#3498db",
    "Segura":       "#9b59b6",
    "Guadalquivir": "#1abc9c",
}


def build_ssi_timeseries(history_by_cuenca: dict) -> go.Figure:
    """
    Construye gráfico de líneas SSI para múltiples cuencas.

    history_by_cuenca = {
        "Jucar": [{"obs_date": date, "ssi_score": float, "risk_level": str}, ...]
        ...
    }
    """
    fig = go.Figure()

    # Bandas de riesgo de fondo
    fig.add_hrect(y0=0,  y1=50, fillcolor="#2ecc71", opacity=0.05, line_width=0)
    fig.add_hrect(y0=50, y1=70, fillcolor="#f39c12", opacity=0.07, line_width=0)
    fig.add_hrect(y0=70, y1=85, fillcolor="#e67e22", opacity=0.08, line_width=0)
    fig.add_hrect(y0=85, y1=100, fillcolor="#e74c3c", opacity=0.10, line_width=0)

    # Líneas de umbral
    for y, label, color in [
        (50, "MODERADO", "#f39c12"),
        (70, "ALTO",     "#e67e22"),
        (85, "CRÍTICO",  "#e74c3c"),
    ]:
        fig.add_hline(
            y=y, line_dash="dot", line_color=color, opacity=0.5,
            annotation_text=label, annotation_position="right",
            annotation_font_size=10,
        )

    for cuenca, history in history_by_cuenca.items():
        if not history:
            continue
        fechas = [r["obs_date"] for r in history]
        scores = [r["ssi_score"] for r in history]
        color  = COLORES_CUENCA.get(cuenca, "#95a5a6")

        fig.add_trace(go.Scatter(
            x=fechas, y=scores,
            mode="lines+markers",
            name=cuenca,
            line=dict(color=color, width=2),
            marker=dict(size=6),
            hovertemplate=(
                f"<b>{cuenca}</b><br>"
                "Fecha: %{x}<br>"
                "SSI: %{y:.1f}%<br>"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        title="Evolución SSI — Cuencas Mediterráneas",
        xaxis_title="Fecha",
        yaxis_title="SSI (%)",
        yaxis=dict(range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=380,
        margin=dict(l=40, r=40, t=50, b=40),
    )
    return fig


def build_risk_gauge(ssi_score: float, cuenca: str) -> go.Figure:
    """Gauge circular para el SSI actual de una cuenca."""
    if ssi_score >= 85:
        color = "#e74c3c"
    elif ssi_score >= 70:
        color = "#e67e22"
    elif ssi_score >= 50:
        color = "#f39c12"
    else:
        color = "#2ecc71"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=ssi_score,
        title={"text": cuenca, "font": {"size": 14}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar":  {"color": color},
            "steps": [
                {"range": [0,  50], "color": "#eafaf1"},
                {"range": [50, 70], "color": "#fef9e7"},
                {"range": [70, 85], "color": "#fef5e7"},
                {"range": [85, 100],"color": "#fdedec"},
            ],
            "threshold": {
                "line": {"color": "#c0392b", "width": 3},
                "thickness": 0.75,
                "value": 85,
            },
        },
        number={"suffix": "%", "font": {"size": 28}},
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def build_components_bar(ssi_result: dict, cuenca: str) -> go.Figure:
    """Barras horizontales mostrando los 3 componentes del SSI."""
    componentes = ["SAR (humedad)", "Precipitación", "NDVI inverso"]
    valores     = [
        ssi_result.get("sar_norm", 0),
        ssi_result.get("precip_norm", 0),
        ssi_result.get("ndvi_inv_norm", 0),
    ]
    colores = ["#3498db", "#2980b9", "#1abc9c"]

    fig = go.Figure(go.Bar(
        x=valores,
        y=componentes,
        orientation="h",
        marker_color=colores,
        text=[f"{v:.1f}%" for v in valores],
        textposition="outside",
    ))
    fig.update_layout(
        title=f"Componentes SSI — {cuenca}",
        xaxis=dict(range=[0, 110], title="Contribución (%)"),
        height=220,
        margin=dict(l=10, r=40, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig
