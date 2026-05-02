"""
Test 2: añade métricas + plotly (gauges y series temporales).
SIN folium, SIN tabs, SIN historical.
Si esto funciona limpio al cambiar idioma/selectbox y F5,
el culpable es st_folium o st.tabs.
"""

import streamlit as st
from config.settings import CUENCAS
from database.queries import get_latest_ssi, get_ssi_history
from dashboard.charts import build_ssi_timeseries, build_risk_gauge, build_components_bar

st.set_page_config(page_title="Test 2 KAIRI", layout="wide")
st.title("🛰️ Test 2 — Métricas + Plotly (sin folium, sin tabs)")

# Sidebar minimo con selector idioma para reproducir el rerun
with st.sidebar:
    lang = st.selectbox("Idioma", ["ES", "DE", "EN"])
    st.caption(f"Idioma actual: {lang}")

@st.cache_data(ttl=300)
def load_latest():
    out = {}
    for c in CUENCAS:
        try:
            out[c] = get_latest_ssi(c)
        except Exception as e:
            st.warning(f"Error {c}: {e}")
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

# Métricas (3 columnas)
st.subheader("Métricas")
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

# Serie temporal plotly
st.subheader("Serie temporal SSI (plotly)")
if any(len(v) > 0 for v in history.values()):
    try:
        st.plotly_chart(build_ssi_timeseries(history), use_container_width=True)
    except Exception as e:
        st.error(f"Error timeseries: {e}")
        st.exception(e)
else:
    st.info("Sin datos históricos")

st.divider()

# Gauges
st.subheader("Gauges (plotly)")
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

st.divider()
st.markdown("""
**Prueba:**
1. Cambia idioma 5 veces
2. Pulsa F5

✅ Si todo OK → culpable es `st_folium` o `st.tabs`
❌ Si pantalla blanca → culpable es **plotly**
""")