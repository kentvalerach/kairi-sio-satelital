-- KAIRI-SIO-SATELITAL — PostgreSQL Schema
-- Ejecutar: psql -U postgres -d kairi_sio_satelital -f database/schema.sql

-- Observaciones satelitales por cuenca y fecha
CREATE TABLE IF NOT EXISTS satellite_obs (
    id              SERIAL PRIMARY KEY,
    cuenca          VARCHAR(50)  NOT NULL,
    obs_date        DATE         NOT NULL,
    vv_mean_db      FLOAT,
    vv_std_db       FLOAT,
    precip_7d_mm    FLOAT,
    precip_max_1h   FLOAT,
    ndvi_mean       FLOAT,
    ndvi_std        FLOAT,
    n_sar_images    INT          DEFAULT 0,
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE(cuenca, obs_date)
);

-- Índice SSI calculado
CREATE TABLE IF NOT EXISTS ssi_scores (
    id              SERIAL PRIMARY KEY,
    cuenca          VARCHAR(50)  NOT NULL,
    obs_date        DATE         NOT NULL,
    ssi_score       FLOAT        NOT NULL,
    sar_norm        FLOAT,
    precip_norm     FLOAT,
    ndvi_inv_norm   FLOAT,
    risk_level      VARCHAR(20),
    ttt_hours       FLOAT,
    alert_level     VARCHAR(20),
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE(cuenca, obs_date)
);

-- Niveles de embalse (SAIH)
CREATE TABLE IF NOT EXISTS reservoir_levels (
    id              SERIAL PRIMARY KEY,
    cuenca          VARCHAR(50)  NOT NULL,
    embalse         VARCHAR(100) NOT NULL,
    obs_timestamp   TIMESTAMPTZ  NOT NULL,
    nivel_hm3       FLOAT,
    capacidad_hm3   FLOAT,
    pct_llenado     FLOAT,
    UNIQUE(embalse, obs_timestamp)
);

-- Log de alertas enviadas
CREATE TABLE IF NOT EXISTS alert_log (
    id              SERIAL PRIMARY KEY,
    cuenca          VARCHAR(50)  NOT NULL,
    alert_level     VARCHAR(20)  NOT NULL,
    ssi_score       FLOAT,
    ttt_hours       FLOAT,
    sent_at         TIMESTAMPTZ  DEFAULT NOW(),
    channel         VARCHAR(50)  DEFAULT 'telegram'
);

-- Índices de rendimiento
CREATE INDEX IF NOT EXISTS idx_ssi_cuenca_date
    ON ssi_scores(cuenca, obs_date DESC);
CREATE INDEX IF NOT EXISTS idx_reservoir_cuenca
    ON reservoir_levels(cuenca, obs_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_satellite_cuenca_date
    ON satellite_obs(cuenca, obs_date DESC);
