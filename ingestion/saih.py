"""
KAIRI-SIO-SATELITAL - Ingesta SAIH
URLs validadas marzo 2026.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
}

URLS = {
    "CHJ": "https://saih.chj.es/embalses",
    "CHG": "https://www.chguadalquivir.es/saih/EmbalMapa.aspx",
}


def get_chj_embalses() -> pd.DataFrame:
    r = requests.get(URLS["CHJ"], headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tabla = soup.find("table", class_=lambda c: c and "table" in c)
    if not tabla:
        raise ValueError("CHJ: tabla no encontrada")

    def parse_float(s):
        try:
            return float(s.replace(",", ".").replace(" ", ""))
        except:
            return None

    rows = []
    for fila in tabla.find_all("tr")[1:]:
        cols = [td.text.strip() for td in fila.find_all("td")]
        if len(cols) < 4:
            continue
        embalse   = cols[0]
        nivel_hm3 = parse_float(cols[1])
        capacidad = parse_float(cols[3])
        if not embalse or "TOTAL" in embalse.upper() or nivel_hm3 is None:
            continue
        pct = round(nivel_hm3 / capacidad * 100, 2) if capacidad else None
        rows.append({
            "embalse":       embalse,
            "nivel_hm3":     nivel_hm3,
            "capacidad_hm3": capacidad,
            "pct_llenado":   pct,
            "obs_timestamp": datetime.now(),
            "confederacion": "CHJ",
            "cuenca":        "Jucar",
        })
    return pd.DataFrame(rows)


def get_chg_embalses() -> pd.DataFrame:
    r = requests.get(URLS["CHG"], headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    tabla = None
    for t in soup.find_all("table"):
        if "Vol. Embalsado" in t.get_text():
            tabla = t
            break
    if not tabla:
        raise ValueError("CHG: tabla no encontrada")

    def parse_es_float(s):
        try:
            s = s.strip().replace("%", "").replace(" ", "")
            if "." in s and "," in s:      # miles español: 6.867,550
                s = s.replace(".", "").replace(",", ".")
            elif "," in s:                  # decimal español: 84,56
                s = s.replace(",", ".")
            return float(s)
        except:
            return None

    rows = []
    for fila in tabla.find_all("tr")[1:]:
        # ← FIX: leer th Y td para capturar col[0] que es <th>
        cols = [c.text.strip() for c in fila.find_all(["th", "td"])]
        if len(cols) < 4:
            continue
        nombre    = cols[0]
        nivel_hm3 = parse_es_float(cols[1])
        capacidad = parse_es_float(cols[2])
        pct       = parse_es_float(cols[3])
        if not nombre or nivel_hm3 is None:
            continue
        rows.append({
            "embalse":       nombre,
            "nivel_hm3":     nivel_hm3,
            "capacidad_hm3": capacidad,
            "pct_llenado":   pct,
            "obs_timestamp": datetime.now(),
            "confederacion": "CHG",
            "cuenca":        "Guadalquivir",
        })
    return pd.DataFrame(rows)


def get_reservoir_levels(confederacion: str) -> pd.DataFrame:
    if confederacion == "CHJ":
        return get_chj_embalses()
    elif confederacion in ("CHG", "CHS"):
        return get_chg_embalses()
    else:
        raise ValueError(f"Confederacion no soportada: {confederacion}")


def get_resumen_cuenca(confederacion: str) -> dict:
    df = get_reservoir_levels(confederacion)
    if df.empty:
        return {}

    if confederacion in ("CHG", "CHS"):
        total_row = df[df["embalse"].str.contains("Total", case=False, na=False)]
        if not total_row.empty:
            row = total_row.iloc[0]
            return {
                "confederacion":       confederacion,
                "total_hm3":           row["nivel_hm3"],
                "capacidad_total_hm3": row["capacidad_hm3"],
                "pct_medio":           row["pct_llenado"],
                "n_embalses":          len(df) - 1,
                "timestamp":           datetime.now().isoformat(),
            }

    df_v = df.dropna(subset=["nivel_hm3", "capacidad_hm3"])
    total = df_v["nivel_hm3"].sum()
    cap   = df_v["capacidad_hm3"].sum()
    return {
        "confederacion":       confederacion,
        "total_hm3":           round(total, 2),
        "capacidad_total_hm3": round(cap, 2),
        "pct_medio":           round(total / cap * 100, 2) if cap > 0 else 0,
        "n_embalses":          len(df_v),
        "timestamp":           datetime.now().isoformat(),
    }


def save_to_db(confederacion: str) -> int:
    from database.queries import insert_reservoir_level
    df = get_reservoir_levels(confederacion)
    if df.empty:
        return 0
    count = 0
    for _, row in df.iterrows():
        try:
            insert_reservoir_level({
                "cuenca":        row["cuenca"],
                "embalse":       row["embalse"],
                "obs_timestamp": row["obs_timestamp"],
                "nivel_hm3":     row["nivel_hm3"],
                "capacidad_hm3": row["capacidad_hm3"],
                "pct_llenado":   row["pct_llenado"],
            })
            count += 1
        except Exception as e:
            print(f"  Error {row['embalse']}: {e}")
    return count


if __name__ == "__main__":
    print("=" * 60)
    print("  Test SAIH - niveles de embalse en tiempo real")
    print("=" * 60)

    for conf in ["CHJ", "CHG"]:
        print(f"\n{'='*20} {conf} {'='*20}")
        try:
            df = get_reservoir_levels(conf)
            print(f"  Filas: {len(df)}")
            print(df[["embalse","nivel_hm3","capacidad_hm3","pct_llenado"]].to_string(index=False))
            res = get_resumen_cuenca(conf)
            print(f"\n  Resumen: {res['total_hm3']} hm3 / {res['capacidad_total_hm3']} hm3 = {res['pct_medio']}%")
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n{'='*20} Guardando en DB {'='*20}")
    for conf in ["CHJ", "CHG"]:
        try:
            n = save_to_db(conf)
            print(f"  {conf}: {n} filas → reservoir_levels")
        except Exception as e:
            print(f"  {conf} error: {e}")

    print("\n✅ SAIH Sprint 1b completado.")