import streamlit as st
from config.settings import CUENCAS
from database.queries import get_latest_ssi

st.set_page_config(page_title="Test KAIRI", layout="wide")
st.title("Test mínimo KAIRI-SIO-SATELITAL")

opcion = st.selectbox("Cuenca", list(CUENCAS.keys()))

st.write(f"Datos de: **{opcion}**")
data = get_latest_ssi(opcion)
st.json(data)

st.write("Si cambias el selector y NO se pone blanco, el problema está en folium/plotly/tabs.")
st.write("Si se pone blanco, el problema es Streamlit Cloud o el conector a Supabase con reruns.")