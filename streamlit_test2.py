"""
Test 3: añade st.tabs al stack que ya funciona.
- Selectbox idioma + plotly + tabs
- SIN folium, SIN historical
- Si esto funciona limpio → culpable es st_folium o el import de historical
- Si esto rompe → culpable es st.tabs
"""

import streamlit as st
from config.settings import CUENCAS
from database.queries import get_latest_ssi, get_ssi_history
from dashboard.charts import build_ssi_timeseries, build_risk_gauge, build_components_bar

st.set_page_config(page_title="Test 3 KAIRI", layout="wide")
st.title("🛰️ Test 3 — Plotly + Tabs (sin folium, sin historical)")

# Sidebar minimo
with st.sidebar:
    lang = st.selectbox("Idioma", ["ES", "DE", "EN"])
    st.caption(f"Idioma actual: {lang}")

# Traducciones mínimas para verificar que el idioma cambia
TXT = {
    "ES": {"tab1": "📡 Dashboard", "tab2": "🔍 Histórico", "header": "Métricas"},
    "DE": {"tab1": "📡 Übersicht", "tab2": "🔍 Verlauf", "header": "Kennzahlen"},
    "EN": {"tab1": "📡 Dashboard", "tab2": "🔍 History",  "header": "Metrics"},
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

# AQUÍ está el cambio: añadimos tabs
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
    st.info("Tab histórico (sin contenido por ahora — solo verificamos que st.tabs no rompe)")
    st.write(f"Datos históricos cargados: {sum(len(v) for v in history.values())} filas")

st.divider()
st.markdown("""
**Prueba:**
1. Cambia idioma 5 veces (ahora SÍ debe cambiar el texto de las pestañas)
2. Cambia entre tabs
3. Pulsa F5

✅ Funciona → culpable es **st_folium** o el import de **dashboard.historical**
❌ Pantalla blanca → culpable es **st.tabs**
""")
