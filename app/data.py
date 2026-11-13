"""Lapisan data dashboard: memuat tabel dari data/processed/ dan reports/, menerapkan filter global.

Tidak ada angka yang dihitung ulang dengan definisi baru: semua kuantitas berasal dari tabel notebook 03 (aq_*, health_*,
sites_clean, qc_summary) dan dari reports/key_numbers.json (notebook 04–05). Hanya agregasi sederhana untuk filter.

Versi data:
  * "bertopeng"  : jam/hari flatline sensor (BJB-01) dibuang, sama seperti notebook 05;
  * "apa adanya" : persis tabel notebook 03, sama seperti angka notebook 04.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import config as cfg  # noqa: E402
from src import models as M  # noqa: E402

POLUTAN = {"pm25": "PM2.5", "pm10": "PM10", "no2": "NO₂", "so2": "SO₂", "co": "CO", "o3": "O₃"}
# baku mutu harian (µg/m³) dari reports/findings/01_business_understanding.md bagian 4.2; CO & O₃ tidak punya acuan harian
STANDAR = {
    "PP 22/2021": {"pm25": 55.0, "pm10": 75.0, "no2": 65.0, "so2": 75.0},
    "WHO 2021": {"pm25": 15.0, "pm10": 45.0, "no2": 25.0, "so2": 40.0},
}
CUACA = {"temperature_c": "Suhu", "humidity_pct": "Kelembapan", "wind_speed_ms": "Kec. angin"}
NAMA_KASUS = M.NAMA_KASUS


def _baca_md_tabel(teks: str, judul: str) -> pd.DataFrame:
    """Ambil tabel markdown pertama setelah heading yang memuat `judul`."""
    i = teks.find(judul)
    if i < 0:
        return pd.DataFrame()
    baris = []
    for ln in teks[i:].splitlines()[1:]:
        if ln.startswith("|"):
            baris.append([c.strip() for c in ln.strip().strip("|").split("|")])
        elif baris:
            break
    if len(baris) < 3:
        return pd.DataFrame()
    return pd.DataFrame(baris[2:], columns=baris[0])


@st.cache_resource(show_spinner="Memuat data…")
def muat() -> SimpleNamespace:
    PR = cfg.PROC_DIR
    daily = pd.read_parquet(PR / "aq_daily.parquet")
    hourly = pd.read_parquet(PR / "aq_hourly.parquet")
    health = pd.read_parquet(PR / "health_aq_daily.parquet")
    sites = pd.read_parquet(PR / "sites_clean.parquet")
    qc = pd.read_parquet(PR / "qc_summary.parquet")
    for df in (daily, hourly):
        df["kode_stasiun"] = df["kode_stasiun"].astype(str)
    health["kode_stasiun"] = health["kode_stasiun"].astype(str)
    st_ = sites.set_index("kode_stasiun")
    for df in (daily, hourly):
        df["tipe"] = df["kode_stasiun"].map(st_["kelompok_lokasi"]).astype(str)
        df["pulau_s"] = df["kode_stasiun"].map(st_["pulau"]).astype(str)
        df["provinsi"] = df["kode_stasiun"].map(st_["provinsi"]).astype(str)
    for c in ("hari", "musim", "pulau", "kelompok_lokasi"):
        for df in (daily, hourly):
            if c in df:
                df[c] = df[c].astype(str)

    # ---- versi bertopeng (identik dengan notebook 05, bagian 0)
    flat = M.deteksi_flatline(hourly, min_jam=24)
    hourly["flatline"] = False
    for r in flat.itertuples():
        hourly.loc[(hourly.kode_stasiun == r.kode_stasiun) & (hourly.jam >= r.awal) & (hourly.jam <= r.akhir), "flatline"] = True
    hourly_m = hourly.copy()
    hourly_m.loc[hourly_m.flatline, ["pm25_ug_m3", "pm10_ug_m3"]] = np.nan
    fh = hourly[hourly.flatline].groupby(["kode_stasiun", hourly.jam.dt.floor("D")]).size()
    hari_flat = set(fh[fh >= 12].index)
    daily_m = daily.copy()
    daily_m["flatline"] = [(k, t) in hari_flat for k, t in zip(daily_m.kode_stasiun, daily_m.tanggal)]
    daily_m.loc[daily_m.flatline, ["pm25_ug_m3", "pm25_ug_m3_longgar", "pm25_maks_jam_ug_m3", "pm10_ug_m3"]] = np.nan
    daily_m["episode"] = daily_m.episode_asap.astype(bool) & ~daily_m.flatline
    daily["episode"] = daily.episode_asap.astype(bool)
    daily["flatline"] = False
    health_m = M.lag_dari_harian(health, daily_m)
    em = daily_m.set_index(["kode_stasiun", "tanggal"]).episode
    health_m["episode"] = [bool(em.get((k, d), False)) for k, d in zip(health_m.kode_stasiun, health_m.date)]
    health["episode"] = health["episode_asap"].astype(bool)

    kn = json.loads((cfg.REPORTS_DIR / "key_numbers.json").read_text(encoding="utf-8"))
    md5 = (cfg.FINDINGS_DIR / "05_insights.md").read_text(encoding="utf-8")
    return SimpleNamespace(
        daily={"apa adanya": daily, "bertopeng": daily_m}, hourly={"apa adanya": hourly, "bertopeng": hourly_m},
        health={"apa adanya": health, "bertopeng": health_m}, sites=sites, qc=qc, flat=flat, kn=kn,
        ringkasan_insight=_baca_md_tabel(md5, "## Ringkasan"), rekomendasi=_baca_md_tabel(md5, "## Rekomendasi kebijakan per tipe wilayah"),
        keterbatasan=md5[md5.find("## Keterbatasan"):md5.find("## Lampiran")].replace("## Keterbatasan", "").strip(),
        masalah=pd.read_csv(cfg.REPORTS_DIR / "data_quality_issues.csv", encoding="utf-8-sig"),
        log=pd.read_csv(cfg.REPORTS_DIR / "preprocessing_log.csv", encoding="utf-8-sig"),
        tgl_min=daily.tanggal.min().date(), tgl_maks=daily.tanggal.max().date(),
    )


def stasiun_terpilih(D, f: dict) -> list[str]:
    s = D.sites
    m = pd.Series(True, index=s.index)
    if f["pulau"]:
        m &= s.pulau.isin(f["pulau"])
    if f["provinsi"]:
        m &= s.provinsi.isin(f["provinsi"])
    if f["tipe"]:
        m &= s.kelompok_lokasi.isin(f["tipe"])
    if f["stasiun"]:
        m &= s.kode_stasiun.isin(f["stasiun"])
    return s.loc[m, "kode_stasiun"].tolist()


@st.cache_resource(max_entries=32, show_spinner=False)
def _terfilter(_D, versi: str, stas: tuple, a: str, b: str):
    """Potongan tabel harian & kesehatan per filter (kunci = versi, stasiun, tanggal). Disimpan sekali dan dipakai bersama tanpa disalin;
    halaman hanya membaca tabel ini (setiap perubahan dibuat pada salinan)."""
    a, b = pd.Timestamp(a), pd.Timestamp(b)
    d = _D.daily[versi]
    d = d[d.kode_stasiun.isin(stas) & (d.tanggal >= a) & (d.tanggal <= b)]
    h = _D.health[versi]
    h = h[h.kode_stasiun.isin(stas) & (h.date >= a) & (h.date <= b)]
    return d, h


def data_terfilter(D, f: dict) -> SimpleNamespace:
    """Tabel harian/jam/kesehatan pada versi data terpilih, dibatasi stasiun & rentang tanggal (di-cache per filter)."""
    v = f["versi"]
    stas = stasiun_terpilih(D, f)
    a, b = pd.Timestamp(f["tgl"][0]), pd.Timestamp(f["tgl"][1])
    d, h = _terfilter(D, v, tuple(stas), str(a.date()), str(b.date()))
    return SimpleNamespace(stas=stas, daily=d, health=h, versi=v, tgl=(a, b))


@st.cache_data(show_spinner=False)
def statistik_kotak(versi: str, stas: tuple, a: str, b: str, kolom: str) -> dict:
    """Ringkasan boxplot per jenis wilayah: [min, Q1, median, Q3, maks] (kuartil linear, sama dengan boxplot Plotly tanpa titik pencilan).
    Hanya 5 angka per jenis yang dikirim ke grafik, bukan seluruh catatan harian."""
    d = muat().daily[versi]
    d = d[d.kode_stasiun.isin(stas) & (d.tanggal >= pd.Timestamp(a)) & (d.tanggal <= pd.Timestamp(b)) & d[kolom].notna()]
    hasil = {}
    for t, x in d.groupby("tipe")[kolom]:
        q = np.percentile(x.to_numpy(), [0, 25, 50, 75, 100])
        hasil[str(t)] = [round(float(v), 4) for v in q]
    return hasil


@st.cache_data(show_spinner=False)
def _jam_agregat(_D_id: str, versi: str, stas: tuple, a: str, b: str, kolom: str):
    D = muat()
    h = D.hourly[versi]
    h = h[h.kode_stasiun.isin(stas) & (h.jam >= a) & (h.jam <= b + " 23:59") & h[kolom].notna()]
    prof = h.groupby(["tipe", "jam_lokal"])[kolom].median().reset_index()
    hm = h.groupby(["bulan", "jam_lokal"])[kolom].mean().reset_index()
    med_st = h.groupby("kode_stasiun")[list(dict.fromkeys([kolom, "no2_ug_m3", "co_ug_m3"]))].median()
    return prof, hm, med_st


def jam_agregat(D, dat, kolom: str):
    return _jam_agregat("v1", dat.versi, tuple(dat.stas), str(dat.tgl[0].date()), str(dat.tgl[1].date()), kolom)
