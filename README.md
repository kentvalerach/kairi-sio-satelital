<div align="center">

# 🛰️ KAIRI-SIO-SATELITAL

**Sistema de Alerta Temprana de Inundaciones DANA mediante fusión de datos satelitales multifuente**

*DANA Flood Early Warning System through multi-source satellite data fusion*

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://kairi-sio-satellit.streamlit.app)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production-success.svg)](https://kairi-sio-satellit.streamlit.app)

🇪🇸 [Español](#-español) · 🇩🇪 [Deutsch](#-deutsch) · 🇬🇧 [English](#-english)

</div>

---

## 🇪🇸 Español

### Motivación

La DANA del 29 de octubre de 2024 dejó **238 fallecidos** en la Comunidad Valenciana, una de las peores catástrofes meteorológicas en España en décadas. El análisis posterior identificó una causa raíz técnica recurrente: **la ausencia de un sistema integrado de monitorización de la saturación del suelo a escala de cuenca**, que combine en tiempo cuasi-real las observaciones de humedad superficial (radar SAR), la precipitación reciente y el estado de la cobertura vegetal.

KAIRI-SIO-SATELITAL aborda esta brecha con un sistema operativo, reproducible y desplegado en producción.

### Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Sentinel-1 SAR │───▶│  Pipeline GEE    │───▶│  PostgreSQL      │
│  GPM IMERG V07  │───▶│  (cálculo SSI    │───▶│  (Supabase)      │
│  Sentinel-2     │───▶│   + niveles)     │    │                  │
└─────────────────┘    └──────────────────┘    └─────────┬────────┘
                                                          │
                                                          ▼
                                                ┌──────────────────┐
                                                │  Dashboard       │
                                                │  Streamlit Cloud │
                                                │  (trilingüe)     │
                                                └──────────────────┘
```

### Índice de saturación del suelo (SSI)

El SSI es un índice compuesto normalizado a [0, 100] que pondera tres señales independientes:

```
SSI = 0.45 · SAR_norm  +  0.40 · Precip_norm  +  0.15 · NDVI_inv_norm
```

| Fuente | Peso | Descripción |
|--------|------|-------------|
| **Sentinel-1 SAR** | 45 % | Backscatter VV — humedad superficial del suelo |
| **GPM IMERG V07** | 40 % | Precipitación acumulada en 7 días |
| **Sentinel-2 NDVI inverso** | 15 % | Saturación del dosel vegetal |

### Detección dual de DANA

El sistema implementa dos modos complementarios de alerta:

- **💧 Modo A — Saturación progresiva**: SSI > 85 % combinado con precipitación > 40 mm. Captura el escenario clásico de cuenca saturada por días previos de lluvia.
- **⚡ Modo B — DANA seco + lluvia extrema**: precipitación de 24 h > 60 mm con SSI < 50 %. Captura el escenario de Valencia 2024, donde el suelo seco no absorbió la lluvia torrencial.

### Cuencas monitorizadas

| Cuenca | Confederación | Prioridad |
|--------|---------------|-----------|
| **Júcar** | CHJ | 🔴 Crítica — epicentro de la DANA de octubre 2024 |
| **Segura** | CHS | 🔴 Crítica — flash floods recurrentes en Murcia |
| **Guadalquivir** | CHG | 🟡 Validación cruzada |

### Stack técnico

- **Ingesta**: Google Earth Engine (Sentinel-1, Sentinel-2, GPM IMERG V07)
- **Cálculo**: Python 3.11, NumPy, Pandas
- **Persistencia**: PostgreSQL (Supabase)
- **Dashboard**: Streamlit + Plotly + Folium
- **Despliegue**: Streamlit Cloud
- **Notificaciones**: Telegram Bot API (alertas automáticas)

### Instalación local

```bash
# Clonar repositorio
git clone https://github.com/kentvalerach/kairi-sio-satelital.git
cd kairi-sio-satelital

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate  # Linux / macOS

# Instalar dependencias
pip install -r requirements.txt

# Autenticar Google Earth Engine
earthengine authenticate --force

# Configurar credenciales
copy config\.env.example config\.env
# Editar config/.env con credenciales de Supabase y Telegram

# Inicializar esquema de base de datos
python setup_repo.py
```

### Ejecución

```bash
# Lanzar dashboard local
streamlit run dashboard/app.py

# Ejecutar pipeline de ingesta (últimos 30 días)
python pipeline_runner.py --dias 30

# Enviar alertas por Telegram (opcional)
python alerts/notifier.py
```

### Roadmap

- ✅ Sprint 1 — Validación SSI con DANA 2024 (73,84 % vs 39,37 % verano)
- ✅ Sprint 2 — Pipeline operativo en PostgreSQL
- ✅ Sprint 3 — Dashboard trilingüe en producción
- 🔄 Sprint 4 — Calibración por subcuencas (CHJ → 7 puntos hidrológicos)
- 🔄 Sprint 5 — Modelo predictivo a 24-48 h (LightGBM + AFML)
- ⏳ Sprint 6 — Concurso público AEMET / MITECO

### Despliegue en producción

🌐 **[https://kairi-sio-satelital.streamlit.app](https://kairi-sio-satellit.streamlit.app)**

Tres idiomas (ES / DE / EN), refresco automático cada 5 minutos, mapa interactivo con marcadores codificados por nivel de riesgo, panel de alertas, evolución histórica de 90 días y análisis comparativo entre cuencas.

---

## 🇩🇪 Deutsch

### Hintergrund

Die DANA vom 29. Oktober 2024 forderte **238 Todesopfer** in der Region Valencia und gilt als eine der schlimmsten Wetterkatastrophen Spaniens seit Jahrzehnten. Die nachträgliche Analyse identifizierte eine wiederkehrende technische Ursache: **das Fehlen eines integrierten Systems zur Überwachung der Bodensättigung auf Einzugsgebietsebene**, das in nahezu Echtzeit Beobachtungen der Oberflächenfeuchte (SAR-Radar), der jüngsten Niederschläge und des Vegetationszustands kombiniert.

KAIRI-SIO-SATELITAL schließt diese Lücke mit einem operativen, reproduzierbaren und produktiv eingesetzten System.

### Bodensättigungsindex (SSI)

Der SSI ist ein zusammengesetzter, auf [0, 100] normalisierter Index, der drei unabhängige Signale gewichtet:

```
SSI = 0,45 · SAR_norm  +  0,40 · Niederschlag_norm  +  0,15 · NDVI_inv_norm
```

| Quelle | Gewicht | Beschreibung |
|--------|---------|--------------|
| **Sentinel-1 SAR** | 45 % | VV-Rückstreuung — Oberflächenbodenfeuchte |
| **GPM IMERG V07** | 40 % | Kumulierter Niederschlag über 7 Tage |
| **Sentinel-2 NDVI invers** | 15 % | Sättigung der Vegetationsbedeckung |

### Doppelte DANA-Erkennung

Das System implementiert zwei komplementäre Warnmodi:

- **💧 Modus A — Progressive Sättigung**: SSI > 85 % kombiniert mit Niederschlag > 40 mm. Erfasst das klassische Szenario eines durch tagelange Vorregen gesättigten Einzugsgebiets.
- **⚡ Modus B — Trockener DANA + Extremregen**: 24-h-Niederschlag > 60 mm bei SSI < 50 %. Erfasst das Szenario von Valencia 2024, in dem trockener Boden den Starkregen nicht aufnehmen konnte.

### Überwachte Einzugsgebiete

| Einzugsgebiet | Behörde | Priorität |
|---------------|---------|-----------|
| **Júcar** | CHJ | 🔴 Kritisch — Epizentrum der DANA Oktober 2024 |
| **Segura** | CHS | 🔴 Kritisch — wiederkehrende Flash Floods in Murcia |
| **Guadalquivir** | CHG | 🟡 Kreuzvalidierung |

### Technologie-Stack

- **Datenerfassung**: Google Earth Engine (Sentinel-1, Sentinel-2, GPM IMERG V07)
- **Berechnung**: Python 3.11, NumPy, Pandas
- **Datenbank**: PostgreSQL (Supabase)
- **Dashboard**: Streamlit + Plotly + Folium
- **Bereitstellung**: Streamlit Cloud
- **Benachrichtigungen**: Telegram Bot API (automatische Warnungen)

### Lokale Installation

```bash
git clone https://github.com/kentvalerach/kairi-sio-satelital.git
cd kairi-sio-satelital

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
earthengine authenticate --force

copy config\.env.example config\.env
# config/.env mit Supabase- und Telegram-Zugangsdaten bearbeiten

python setup_repo.py
```

### Ausführung

```bash
# Lokales Dashboard starten
streamlit run dashboard/app.py

# Datenerfassungspipeline ausführen (letzte 30 Tage)
python pipeline_runner.py --dias 30
```

### Produktivumgebung

🌐 **[https://kairi-sio-satelital.streamlit.app](https://kairi-sio-satellit.streamlit.app)**

Dreisprachig (ES / DE / EN), automatische Aktualisierung alle 5 Minuten, interaktive Karte mit risikofarbcodierten Markierungen, Warnpanel, historischer Verlauf über 90 Tage und vergleichende Analyse zwischen Einzugsgebieten.

---

## 🇬🇧 English

### Motivation

The DANA event of 29 October 2024 caused **238 deaths** in the Valencia region, one of Spain's worst weather catastrophes in decades. Post-event analysis identified a recurring technical root cause: **the absence of an integrated soil-saturation monitoring system at the basin scale**, combining near-real-time observations of surface moisture (SAR radar), recent precipitation, and vegetation cover.

KAIRI-SIO-SATELITAL addresses this gap with an operational, reproducible, and production-deployed system.

### Soil Saturation Index (SSI)

The SSI is a composite index normalized to [0, 100] that weights three independent signals:

```
SSI = 0.45 · SAR_norm  +  0.40 · Precip_norm  +  0.15 · NDVI_inv_norm
```

| Source | Weight | Description |
|--------|--------|-------------|
| **Sentinel-1 SAR** | 45 % | VV backscatter — surface soil moisture |
| **GPM IMERG V07** | 40 % | 7-day accumulated precipitation |
| **Sentinel-2 NDVI inverse** | 15 % | Vegetation canopy saturation |

### Dual DANA Detection

The system implements two complementary alert modes:

- **💧 Mode A — Progressive saturation**: SSI > 85 % combined with precipitation > 40 mm. Captures the classic scenario of a basin saturated by days of prior rainfall.
- **⚡ Mode B — Dry DANA + extreme rainfall**: 24-h precipitation > 60 mm with SSI < 50 %. Captures the Valencia 2024 scenario, where dry soil failed to absorb the torrential downpour.

### Monitored Basins

| Basin | Authority | Priority |
|-------|-----------|----------|
| **Júcar** | CHJ | 🔴 Critical — epicenter of the October 2024 DANA |
| **Segura** | CHS | 🔴 Critical — recurrent flash floods in Murcia |
| **Guadalquivir** | CHG | 🟡 Cross-validation |

### Technical Stack

- **Ingestion**: Google Earth Engine (Sentinel-1, Sentinel-2, GPM IMERG V07)
- **Computation**: Python 3.11, NumPy, Pandas
- **Persistence**: PostgreSQL (Supabase)
- **Dashboard**: Streamlit + Plotly + Folium
- **Deployment**: Streamlit Cloud
- **Notifications**: Telegram Bot API (automatic alerts)

### Local Setup

```bash
git clone https://github.com/kentvalerach/kairi-sio-satelital.git
cd kairi-sio-satelital

python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate  # Linux / macOS

pip install -r requirements.txt
earthengine authenticate --force

copy config\.env.example config\.env
# edit config/.env with Supabase and Telegram credentials

python setup_repo.py
```

### Execution

```bash
# Launch local dashboard
streamlit run dashboard/app.py

# Run ingestion pipeline (last 30 days)
python pipeline_runner.py --dias 30

# Send Telegram alerts (optional)
python alerts/notifier.py
```

### Roadmap

- ✅ Sprint 1 — SSI validation against DANA 2024 (73.84 % vs 39.37 % summer baseline)
- ✅ Sprint 2 — Operational pipeline on PostgreSQL
- ✅ Sprint 3 — Trilingual dashboard in production
- 🔄 Sprint 4 — Sub-basin calibration (CHJ → 7 hydrological points)
- 🔄 Sprint 5 — Predictive model at 24–48 h horizon (LightGBM + AFML)
- ⏳ Sprint 6 — AEMET / MITECO public tender submission

### Production Deployment

🌐 **[https://kairi-sio-satelital.streamlit.app](https://kairi-sio-satellit.streamlit.app)**

Three languages (ES / DE / EN), 5-minute auto-refresh, interactive map with risk-coded markers, alert panel, 90-day historical evolution, and comparative basin analysis.

---

<div align="center">

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 👤 Author

**Kent Valera Chirinos** — Telecommunications Engineer
📍 Dresden, Germany

[![GitHub](https://img.shields.io/badge/GitHub-kentvalerach-181717?logo=github)](https://github.com/kentvalerach/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Kent_Valera_Chirinos-0A66C2?logo=linkedin)](https://www.linkedin.com/in/kent-valera-chirinos-44ba721b/)

---

*Built in Dresden, 2026 · Targeting Spanish public-sector flood resilience*

</div>
