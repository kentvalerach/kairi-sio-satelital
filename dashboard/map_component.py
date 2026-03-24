"""
KAIRI-SIO-SATELITAL — Map Component
Mapa interactivo Folium con estado SSI por cuenca.
"""

import folium
from config.settings import CUENCAS

COLOR_MAP = {
    "BAJO":     "#2ecc71",
    "MODERADO": "#f39c12",
    "ALTO":     "#e67e22",
    "CRITICO":  "#e74c3c",
    "SIN_DATOS":"#95a5a6",
}

ICONO_NIVEL = {
    "BAJO":     "✅",
    "MODERADO": "🟡",
    "ALTO":     "🟠",
    "CRITICO":  "🔴",
    "SIN_DATOS":"⚪",
}


def build_risk_map(latest_ssi: dict) -> folium.Map:
    """
    Construye mapa Folium con marcadores por cuenca.

    latest_ssi = {
        "Jucar":        {"ssi_score": 44.86, "risk_level": "BAJO", ...},
        "Segura":       {...},
        "Guadalquivir": {...},
    }
    """
    m = folium.Map(
        location=[38.8, -2.5],
        zoom_start=6,
        tiles="CartoDB positron",
    )

    for cuenca_name, meta in CUENCAS.items():
        data       = latest_ssi.get(cuenca_name)
        risk_level = data["risk_level"] if data else "SIN_DATOS"
        ssi_score  = data["ssi_score"]  if data else 0.0
        ttt        = data.get("ttt_hours") if data else None
        obs_date   = str(data.get("obs_date", "N/D")) if data else "N/D"

        color  = COLOR_MAP[risk_level]
        icono  = ICONO_NIVEL[risk_level]
        radius = 18 + (ssi_score / 5)

        # Popup HTML
        ttt_str = f"{ttt}h" if ttt else "N/D"
        popup_html = f"""
        <div style="font-family:sans-serif; min-width:180px">
            <h4 style="margin:0;color:{color}">{icono} {cuenca_name}</h4>
            <hr style="margin:4px 0">
            <b>SSI:</b> {ssi_score}%<br>
            <b>Riesgo:</b> {risk_level}<br>
            <b>TTT:</b> {ttt_str}<br>
            <b>Actualizado:</b> {obs_date}<br>
            <b>Confederación:</b> {meta['confederacion']}
        </div>
        """

        folium.CircleMarker(
            location=meta["center"],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=2,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{cuenca_name}: SSI={ssi_score}% | {risk_level}",
        ).add_to(m)

        # Etiqueta de texto sobre el marcador
        folium.Marker(
            location=meta["center"],
            icon=folium.DivIcon(
                html=f'<div style="font-size:11px;font-weight:bold;'
                     f'color:{color};text-shadow:1px 1px 2px white;">'
                     f'{cuenca_name}</div>',
                icon_size=(100, 20),
                icon_anchor=(50, -15),
            ),
        ).add_to(m)

    # Leyenda
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
         background:white;padding:10px;border-radius:8px;
         border:1px solid #ccc;font-family:sans-serif;font-size:12px">
        <b>🛰️ KAIRI-SIO-SATELITAL</b><br>
        <span style="color:#2ecc71">●</span> BAJO (&lt;50%)<br>
        <span style="color:#f39c12">●</span> MODERADO (50-70%)<br>
        <span style="color:#e67e22">●</span> ALTO (70-85%)<br>
        <span style="color:#e74c3c">●</span> CRÍTICO (&gt;85%)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m
