# 🛰️ KAIRI-SIO-SATELITAL

**Sistema de Alerta Temprana de Inundaciones DANA**  
Mediante Fusión de Datos Satelitales Multifuente

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://kairi-sio-satellit.streamlit.app)

## Motivación

238+ fallecidos en la DANA de Valencia (octubre 2024).  
Causa raíz técnica: ausencia de monitoreo integrado de saturación del suelo a escala de cuenca.

## Cuencas monitorizadas

| Cuenca | Prioridad |
|--------|-----------|
| Júcar (CHJ) | 🔴 Crítica — epicentro DANA 2024 |
| Segura (CHS) | 🔴 Crítica — flash floods recurrentes |
| Guadalquivir (CHG) | 🟡 Validación |

## Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
earthengine authenticate --force
cp config/.env.example config/.env
# editar config/.env con tus credenciales
python setup_repo.py
```

## Autor

**Kent Valera Chirinos** — Telecommunications Engineer, Dresden  
[GitHub](https://github.com/kentvalerach/) · [LinkedIn](https://www.linkedin.com/in/kent-valera-chirinos-44ba721b/)
