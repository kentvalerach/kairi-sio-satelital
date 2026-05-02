"""
Test 4: añade st_folium al stack que ya funciona.
- Selectbox idioma + plotly + tabs + FOLIUM
- Si esto rompe → st_folium es el culpable definitivo
- Si esto funciona → el culpable es el import lazy de dashboard.historical
"""

import streamlit as st
from streamlit_folium import st_folium
from config.settings import CUENCAS
from database.queries import get_latest_ssi, get_ssi_history
from dashboard.charts import build_ssi_timeseries, build_risk_gauge, build_components_bar
from dashboard.map_component import build_risk_map

st.set_page_config(page_title="Test 4 KAIRI", layout="wide")
st.title("🛰️ Test 4 — Plotly + Tabs + Folium")

with st.sidebar:
    lang = st.selectbox("Idioma", ["ES", "DE", "EN"])
    st.caption(f"Idioma actual: {lang}")

TXT = {
    "ES": {"tab1": "📡 Dashboard", "tab2": "🔍 Histórico", "header": "Métricas", "mapa": "Mapa de riesgo"},
    "DE": {"tab1": "📡 Übersicht", "tab2": "🔍 Verlauf", "header": "Kennzahlen", "mapa": "Risikokarte"},
    "EN": {"tab1": "📡 Dashboard", "tab2": "🔍 History",  "header": "Metrics", "mapa": "Risk map"},
}
T = TXT[lang]

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
            out[c] = get_ssi_history(c, 90)
        except Exception as e:
            out[c] = []
    return out

latest = load_latest()
history = load_hist()

tab_dash, tab_hist = st.tabs([T["tab1"], T["tab2"]])

with tab_dash:
    st.subheader(T["header"])
    cols = st.columns(len(CUENCAS))
    for i, cuenca in enumerate(CUENCAS):
        data = latest.get(cuenca)
        with cols[i]:
            if data:
                st.metric(label=cuenca, value=f"{data['ssi_score']}%",
                          delta=data['risk_level'])
            else:
                st.metric(label=cuenca, value="N/D")

    st.divider()

    # AQUÍ está el cambio: añadimos st_folium
    st.subheader(T["mapa"])
    try:
        mapa = build_risk_map(latest)
        st_folium(mapa, width=700, height=420, returned_objects=[])
    except Exception as e:
        st.error(f"Error mapa: {e}")
        st.exception(e)

    st.divider()

    if any(len(v) > 0 for v in history.values()):
        try:
            st.plotly_chart(build_ssi_timeseries(history), use_container_width=True)
        except Exception as e:
            st.error(f"Error timeseries: {e}")

    st.divider()

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

with tab_hist:
    st.info("Tab histórico (placeholder)")
    st.write(f"Datos históricos cargados: {sum(len(v) for v in history.values())} filas")

st.divider()
st.markdown("""
**Prueba:**
1. Cambia idioma 3 veces
2. Cambia entre tabs
3. Pulsa F5

❌ Pantalla blanca → **st_folium es el culpable confirmado**
✅ Funciona → entonces el culpable es el import de `dashboard.historical`
""")
