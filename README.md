# 🛰️ KAIRI-SIO-SATELITAL

**[Versión en Español abajo](#-versión-española)**

---

## 🇬🇧 English Version

### DANA Flood Early Warning System

**KAIRI-SIO-SATELITAL** is a hydrological intelligence system for early detection of DANA-type floods (isolated cold-air drops triggering extreme Mediterranean rainfall) in Spanish river basins. It fuses Earth observation satellite data with ground-based hydrometeorological sensors to estimate soil saturation state 48-72 hours in advance.

> *In the Valencia DANA (October 2024), the SAIH detected the flow anomaly at Rambla del Poyo at 11:07 — the public alert came 4 hours later. 238 people died. This system builds the intelligence layer that would have detected the risk condition in advance.*

---

### 🌍 Live Dashboard

**URL:** [https://kairi-sio-satelital.streamlit.app](https://kairi-sio-satelital.streamlit.app)

Trilingual dashboard (ES / DE / EN) with interactive map, SSI time series, alert panel, and historical analysis module.

---

### 🏞️ Monitored Basins

| Basin | Authority | Priority | Justification |
|-------|-----------|----------|---------------|
| **Júcar** | CHJ | CRITICAL | DANA epicenter Oct 2024 — 238 deaths |
| **Segura** | CHS | CRITICAL | Recurring flash floods — Murcia 2019, 2021, 2024 |
| **Guadalquivir** | CHG | VALIDATION | SAIH data available — reference basin |

---

### 🧠 System Architecture

```
Sentinel-1 SAR (ESA)     → Surface soil moisture (VV backscatter)
GPM IMERG V07 (NASA)     → 7-day accumulated precipitation + hourly monitor
Sentinel-2 NDVI (ESA)    → Vegetation cover (absorption potential)
SAIH CHJ / CHG           → Real-time reservoir levels
         ↓
   Soil Saturation Index (SSI) [0-100%]
         ↓
   Dual Detection System
         ↓
┌─────────────────────────────────────────────────────────┐
│ Mode A — Progressive saturation                         │
│   SSI > 85% AND forecast precipitation > 40mm           │
├─────────────────────────────────────────────────────────┤
│ Mode B — Dry DANA (validated Oct 2024)                  │
│   precip_24h > 60mm AND SSI < 50%                       │
│   → Maximum runoff on dry soil                          │
└─────────────────────────────────────────────────────────┘
         ↓
   PostgreSQL (Supabase) + Telegram Alert + Dashboard
```

---

### 📐 SSI Formula

```
SSI = w1·SAR_norm + w2·PRECIP_norm + w3·NDVI_inv_norm

SAR_norm    = (VV - VV_min) / (VV_max - VV_min) × 100   [VV_min=-25dB, VV_max=-5dB]
PRECIP_norm = min(precip_7d / P95_climatological, 1.0) × 100
NDVI_inv    = (1 - NDVI) × 100

Weights: w1=0.45 (SAR), w2=0.40 (Precipitation), w3=0.15 (Inverse NDVI)
```

| Level | SSI | Action |
|-------|-----|--------|
| 🟢 LOW | < 50% | Passive monitoring |
| 🟡 MODERATE | 50-70% | Daily report |
| 🟠 HIGH | 70-85% | Technical notification |
| 🔴 CRITICAL | ≥ 85% | Telegram alert + authority notification |

---

### 🔬 Retroactive Validation — Valencia DANA 2024

**Scientific finding:** The Valencia DANA was an explosive convective event on dry soil — not progressive saturation. Mode B (dry DANA) would have triggered a RED alert on the day of the event with 82.6mm/24h precipitation over a basin with SSI < 50%.

| Date | Júcar SSI | Level | 7d Precipitation |
|------|-----------|-------|-----------------|
| 01-Oct-2024 | 40.39% | LOW | 1.91 mm |
| 13-Oct-2024 | 50.70% | MODERATE | 20.40 mm |
| 25-Oct-2024 | 53.91% | MODERATE | 27.14 mm |
| **29-Oct-2024** | — | **MODE B** | **82.60 mm/24h** |

---

### 🛰️ Satellite Data Sources

| Satellite | Agency | Parameter | Resolution | Link |
|-----------|--------|-----------|------------|------|
| **Sentinel-1** | ESA / Copernicus | SAR VV backscatter | 10m / 6 days | [ESA Sentinel-1](https://sentinel.esa.int/web/sentinel/missions/sentinel-1) |
| **Sentinel-2** | ESA / Copernicus | NDVI (B8/B4) | 10m / 5 days | [ESA Sentinel-2](https://sentinel.esa.int/web/sentinel/missions/sentinel-2) |
| **GPM IMERG V07** | NASA | 30min precipitation | ~11km / 30min | [NASA GPM](https://gpm.nasa.gov/data/imerg) |
| **SAIH CHJ** | Júcar River Authority | Reservoir levels | Real-time | [SAIH CHJ](https://saih.chj.es/embalses) |
| **SAIH CHG** | Guadalquivir River Authority | Reservoir levels | Real-time | [SAIH CHG](https://www.chguadalquivir.es/saih) |

**Processing platform:** [Google Earth Engine](https://earthengine.google.com/) — cloud-based processing, no local download required.

---

### ⚙️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Satellite ingestion | Google Earth Engine Python API |
| Database | PostgreSQL (local) + Supabase (cloud) |
| Backend | Python 3.11 |
| Dashboard | Streamlit + Folium + Plotly |
| Alerts | Telegram Bot API |
| Scheduler | Windows Task Scheduler |
| Deploy | Streamlit Cloud |

---

### 🚀 Local Setup

```bash
# 1. Clone repository
git clone https://github.com/kentvalerach/kairi-sio-satelital.git
cd kairi-sio-satelital

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure credentials
cp config/.env.example config/.env
# Edit config/.env with your credentials

# 5. Authenticate Google Earth Engine
earthengine authenticate

# 6. Apply PostgreSQL schema
psql -U postgres -d kairi_sio_satelital -f database/schema.sql

# 7. Run initial pipeline
python pipeline_runner.py --dias 30

# 8. Launch dashboard
streamlit run dashboard/app.py
```

---

### 📁 Project Structure

```
kairi-sio-satelital/
├── ingestion/          # GEE ingestion (SAR, GPM, NDVI) + SAIH scraping
├── processing/         # SSI calculation + TTT (Time To Threshold)
├── alerts/             # Dual threshold logic + Telegram dispatcher
├── dashboard/          # Trilingual Streamlit app + components
├── database/           # PostgreSQL schema + CRUD queries
├── validation/         # DANA 2024 retroactive validation
├── config/             # Settings + environment variables
├── pipeline_runner.py  # Full pipeline runner (every 6 days)
├── precip_monitor.py   # Hourly precipitation monitor (Mode B)
└── setup_scheduler.ps1 # Windows Task Scheduler configuration
```

---

### 📚 Scientific References

- Ulaby, F.T. et al. (1986). *Microwave Remote Sensing*. Addison-Wesley.
- Paloscia, S. et al. (2013). Soil moisture mapping using Sentinel-1 images. *Remote Sensing of Environment*, 134, 234-248.
- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley.
- WMO (2008). *Manual on Flood Forecasting and Warning*. WMO-No. 1072.

---

### 👤 Author

**Kent Valera Chirinos**
Telecommunications Engineer | Algorithmic Trader | ML Practitioner
Dresden, Germany — 2026

---

*Built with ❤️ for the 238 victims of the Valencia DANA and all future communities at risk.*

---

---

## 🇪🇸 Versión Española

### Sistema de Alerta Temprana de Inundaciones DANA

**KAIRI-SIO-SATELITAL** es un sistema de inteligencia hidrológica para la detección temprana de inundaciones tipo DANA (Depresión Aislada en Niveles Altos) en cuencas mediterráneas españolas. Fusiona datos satelitales de observación de la Tierra con sensores hidrometeorológicos terrestres para estimar el estado de saturación del suelo con 48-72 horas de antelación.

> *En la DANA de Valencia (octubre 2024), el SAIH detectó la anomalía de caudal en Rambla del Poyo a las 11:07 — la alerta ciudadana llegó 4 horas después. 238 personas fallecieron. Este sistema construye la capa de inteligencia que habría detectado la condición de riesgo con anticipación.*

---

### 🌍 Dashboard en Producción

**URL:** [https://kairi-sio-satelital.streamlit.app](https://kairi-sio-satelital.streamlit.app)

Dashboard trilingüe (ES / DE / EN) con mapa interactivo, series temporales SSI, panel de alertas y módulo de análisis histórico.

---

### 🏞️ Cuencas Monitorizadas

| Cuenca | Confederación | Prioridad | Justificación |
|--------|--------------|-----------|---------------|
| **Júcar** | CHJ | CRÍTICA | Epicentro DANA oct 2024 — 238 fallecidos |
| **Segura** | CHS | CRÍTICA | Flash floods recurrentes — Murcia 2019, 2021, 2024 |
| **Guadalquivir** | CHG | VALIDACIÓN | Datos SAIH disponibles — cuenca de referencia |

---

### 🧠 Arquitectura del Sistema

```
Sentinel-1 SAR (ESA)     → Humedad superficial del suelo (backscatter VV)
GPM IMERG V07 (NASA)     → Precipitación acumulada 7 días + monitor horario
Sentinel-2 NDVI (ESA)    → Cobertura vegetal (absorción potencial)
SAIH CHJ / CHG           → Niveles de embalse en tiempo real
         ↓
   Soil Saturation Index (SSI) [0-100%]
         ↓
   Sistema de Detección Dual
         ↓
┌─────────────────────────────────────────────────────────┐
│ Modo A — Saturación progresiva                          │
│   SSI > 85% AND precipitación prevista > 40mm           │
├─────────────────────────────────────────────────────────┤
│ Modo B — DANA seco (validado oct 2024)                  │
│   precip_24h > 60mm AND SSI < 50%                       │
│   → Escorrentía máxima sobre suelo seco                 │
└─────────────────────────────────────────────────────────┘
         ↓
   PostgreSQL (Supabase) + Alerta Telegram + Dashboard
```

---

### 📐 Formulación del SSI

```
SSI = w1·SAR_norm + w2·PRECIP_norm + w3·NDVI_inv_norm

SAR_norm    = (VV - VV_min) / (VV_max - VV_min) × 100   [VV_min=-25dB, VV_max=-5dB]
PRECIP_norm = min(precip_7d / P95_climatologico, 1.0) × 100
NDVI_inv    = (1 - NDVI) × 100

Pesos: w1=0.45 (SAR), w2=0.40 (Precipitación), w3=0.15 (NDVI inverso)
```

| Nivel | SSI | Acción |
|-------|-----|--------|
| 🟢 BAJO | < 50% | Monitoreo pasivo |
| 🟡 MODERADO | 50-70% | Reporte diario |
| 🟠 ALTO | 70-85% | Notificación técnica |
| 🔴 CRÍTICO | ≥ 85% | Alerta Telegram + notif. autoridades |

---

### 🔬 Validación Retroactiva — DANA Valencia 2024

**Hallazgo científico:** La DANA de Valencia fue un evento convectivo explosivo sobre suelo seco — no de saturación progresiva. El Modo B habría activado alerta ROJA el día del evento con 82.6mm/24h sobre una cuenca con SSI < 50%.

| Fecha | SSI Júcar | Nivel | Precipitación 7d |
|-------|-----------|-------|-----------------|
| 01-oct-2024 | 40.39% | BAJO | 1.91 mm |
| 13-oct-2024 | 50.70% | MODERADO | 20.40 mm |
| 25-oct-2024 | 53.91% | MODERADO | 27.14 mm |
| **29-oct-2024** | — | **MODO B** | **82.60 mm/24h** |

---

### 🛰️ Fuentes de Datos Satelitales

| Satélite | Agencia | Parámetro | Resolución | Enlace |
|----------|---------|-----------|-----------|--------|
| **Sentinel-1** | ESA / Copernicus | Backscatter SAR VV | 10m / 6 días | [ESA Sentinel-1](https://sentinel.esa.int/web/sentinel/missions/sentinel-1) |
| **Sentinel-2** | ESA / Copernicus | NDVI (B8/B4) | 10m / 5 días | [ESA Sentinel-2](https://sentinel.esa.int/web/sentinel/missions/sentinel-2) |
| **GPM IMERG V07** | NASA | Precipitación 30min | ~11km / 30min | [NASA GPM](https://gpm.nasa.gov/data/imerg) |
| **SAIH CHJ** | Confederación Hidrográfica del Júcar | Niveles embalse | Tiempo real | [SAIH CHJ](https://saih.chj.es/embalses) |
| **SAIH CHG** | Confederación Hidrográfica del Guadalquivir | Niveles embalse | Tiempo real | [SAIH CHG](https://www.chguadalquivir.es/saih) |

**Plataforma de procesamiento:** [Google Earth Engine](https://earthengine.google.com/) — procesamiento en la nube sin descarga local.

---

### ⚙️ Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| Ingesta satelital | Google Earth Engine Python API |
| Base de datos | PostgreSQL (local) + Supabase (cloud) |
| Backend | Python 3.11 |
| Dashboard | Streamlit + Folium + Plotly |
| Alertas | Telegram Bot API |
| Scheduler | Windows Task Scheduler |
| Deploy | Streamlit Cloud |

---

### 🚀 Instalación Local

```bash
# 1. Clonar repositorio
git clone https://github.com/kentvalerach/kairi-sio-satelital.git
cd kairi-sio-satelital

# 2. Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar credenciales
cp config/.env.example config/.env
# Editar config/.env con tus credenciales

# 5. Autenticar Google Earth Engine
earthengine authenticate

# 6. Aplicar schema PostgreSQL
psql -U postgres -d kairi_sio_satelital -f database/schema.sql

# 7. Ejecutar pipeline inicial
python pipeline_runner.py --dias 30

# 8. Lanzar dashboard
streamlit run dashboard/app.py
```

---

### 📁 Estructura del Proyecto

```
kairi-sio-satelital/
├── ingestion/          # Ingesta GEE (SAR, GPM, NDVI) + SAIH
├── processing/         # Cálculo SSI y TTT (Tiempo al Umbral)
├── alerts/             # Lógica de umbrales dual + dispatcher Telegram
├── dashboard/          # App Streamlit trilingüe + componentes
├── database/           # Schema PostgreSQL + queries CRUD
├── validation/         # Validación retroactiva DANA 2024
├── config/             # Settings + variables de entorno
├── pipeline_runner.py  # Pipeline completo (cada 6 días)
├── precip_monitor.py   # Monitor precipitación horario (Modo B)
└── setup_scheduler.ps1 # Configuración Windows Task Scheduler
```

---

### 📚 Referencias Científicas

- Ulaby, F.T. et al. (1986). *Microwave Remote Sensing*. Addison-Wesley.
- Paloscia, S. et al. (2013). Soil moisture mapping using Sentinel-1 images. *Remote Sensing of Environment*, 134, 234-248.
- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley.
- WMO (2008). *Manual on Flood Forecasting and Warning*. WMO-No. 1072.

---

### 👤 Autor

**Kent Valera Chirinos**
Ingeniero de Telecomunicaciones | Algorithmic Trader | ML Practitioner
Dresden, Alemania — 2026

---

*Construido con ❤️ para las 238 víctimas de la DANA de Valencia y todas las comunidades en riesgo.*
