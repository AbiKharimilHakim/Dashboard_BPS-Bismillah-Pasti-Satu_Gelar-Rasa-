"""Peta Indonesia 3D beranimasi (deck.gl) untuk halaman Beranda dan Lokasi pengukuran.

Komponen frontend ada di assets/peta3d/ (index.html + deck.min.js + provinsi.json, semuanya lokal; tanpa internet untuk batas wilayah).
Komponen dibuat dengan st.components.v1.declare_component supaya iframe-nya TIDAK dimuat ulang setiap filter berubah: data titik dikirim
sebagai argumen, lalu layer deck.gl diperbarui di tempat (animasi pembuka tidak terulang, mode lapisan & kamera tetap).
Semua animasi (denyut, aliran garis, kamera) berjalan di dalam komponen dengan requestAnimationFrame, tanpa rerun Streamlit.

Semua warna peta berasal dari app/theme.py dan dikirim ke komponen lewat `warna_tema()`; file JavaScript/CSS komponen tidak menulis kode warna.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd
import streamlit.components.v1 as components

from src import style
from src.clean import kategori_ispu_pm25

from . import glossary as G, theme as T, ui

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "assets" / "peta3d"

# ---------------------------------------------------------------- TEMA PETA (peran warna dari app/theme.py)
PERMUKAAN = T.PUTIH          # permukaan provinsi
DINDING = T.CRIMSON          # dinding 3D provinsi
SOROT = T.BLUSH              # provinsi yang disorot
GARIS_PROVINSI = T.GARIS     # batas provinsi
GARIS_PULAU = T.PINK_SOFT    # batas pulau / terluar
TANPA_ALAT = T.PINK_SOFT     # wilayah tanpa pengukuran (arsir berdenyut)
ALIRAN = T.PINK              # garis mengalir & cincin denyut
PANAS = T.PANAS              # lapisan panas
TINGGI_DEFAULT = 520

_komponen = components.declare_component("peta3d", path=str(FOLDER))


def warna_tema() -> dict:
    css = {"bg": T.LATAR, "latar-tengah": T.PINK_TINT, "aksen-teks": T.MAROON, "aksen": T.ROSE, "aksen-tua": T.MAROON, "tanpa-alat": TANPA_ALAT, "navy": T.JUDUL,
           "muted": T.TEKS2, "line": T.GARIS, "putih": T.PUTIH, "hover": T.PINK_TINT, "tombol": T.PINK_TINT, "tombol-hover": T.BLUSH,
           "bayang": T.rgb_teks(T.CRIMSON_DARK), "petunjuk": T.rgba(T.TOOLTIP, .9)}
    return dict(css=css, dinding=DINDING, aksen=ALIRAN, permukaan=PERMUKAAN, tanpa_alat=TANPA_ALAT, sorot=SOROT, garis_prov=GARIS_PROVINSI, garis_pulau=GARIS_PULAU,
                panas=PANAS, ispu=T.ISPU, tanpa_data=T.TANPA_DATA, putih=T.PUTIH, merah_teks=T.MAROON, kilap=T.rgb_daftar(T.campur(T.CRIMSON, T.PUTIH, .25)))


@lru_cache(maxsize=1)
def nama_provinsi() -> list[str]:
    g = json.loads((FOLDER / "provinsi.json").read_text(encoding="utf-8"))
    return [f["properties"]["nama"] for f in g["provinsi"]["features"]]


def provinsi_tanpa_alat(sites: pd.DataFrame) -> list[str]:
    """Provinsi yang tidak punya satu pun lokasi pengukuran (tidak bergantung pada filter)."""
    return sorted(set(nama_provinsi()) - set(sites.provinsi.unique()))


def kategori(x: float) -> str:
    return str(kategori_ispu_pm25(pd.Series([x])).iloc[0]) if pd.notna(x) else "–"


def siapkan_titik(C, d: pd.DataFrame, std: float, batas_nama: str, status: pd.Series, sorot_status: str | None = None) -> pd.DataFrame:
    """Satu baris per lokasi terpilih: rata-rata PM2.5 dan jumlah hari di atas batas aman pada periode & filter yang sedang dipakai."""
    fl, rp = G.fl, G.rp
    s = C.D.sites[C.D.sites.kode_stasiun.isin(C.dat.stas)]
    g = d.groupby("kode_stasiun").pm25_ug_m3
    rata, n_hari, lewat = g.mean(), g.count(), d.assign(l=d.pm25_ug_m3 > std).groupby("kode_stasiun").l.sum()
    baris = []
    for r in s.itertuples():
        k = r.kode_stasiun; m = rata.get(k); n = int(n_hari.get(k, 0)); ada = pd.notna(m) and n > 0
        stt = str(status.get(k, "Layak"))
        baris.append(dict(n=G.PENDEK[k], prov=str(r.provinsi), pulau=str(r.pulau), jenis=G.JENIS[r.kelompok_lokasi], lat=float(r.latitude_dd), lon=float(r.longitude_dd),
                          pm=round(float(m), 2) if ada else None, pm_txt=fl(m) if ada else "–", kat=kategori(m) if ada else "–",
                          hari_label=f"Hari di atas {G.kecil(batas_nama)} ({fl(std, 0)} µg/m³)",
                          hari_txt=f"{rp(int(lewat.get(k, 0)))} dari {rp(n)} hari ({fl(100 * lewat.get(k, 0) / n)}%)" if n else "–",
                          status=G.STATUS_DATA.get(stt, stt), redup=bool(sorot_status and stt != sorot_status)))
    return pd.DataFrame(baris)


def render_peta(df: pd.DataFrame, mode: str, kunci: str, sites: pd.DataFrame, tinggi: int = TINGGI_DEFAULT) -> None:
    """Menampilkan peta 3D. `mode`: "beranda" (umum) atau "lokasi" (menonjolkan wilayah tanpa pengukuran)."""
    tanpa = provinsi_tanpa_alat(sites)
    total = sites.groupby("provinsi").size()
    pilih = df.groupby("prov").size() if len(df) else pd.Series(dtype=int)
    prov = {}
    for p in nama_provinsi():
        n, m = int(total.get(p, 0)), int(pilih.get(p, 0))
        prov[p] = dict(n=n, pilih=m, txt=("Tidak ada lokasi yang dipilih" if n and not m else f"{n} lokasi pengukuran" if m == n else f"{m} dari {n} lokasi pengukuran dipilih") if n else "")
    teks = dict(lapisan_titik="Titik lokasi", lapisan_panas="Peta panas polusi", kembali="Lihat seluruh Indonesia", kosong=G.PESAN_KOSONG, legenda_judul="Kategori udara (rata-rata debu halus)",
                legenda_panas="Rata-rata debu halus (PM2.5)", rendah="Rendah", tinggi="Tinggi", belum_alat="Belum ada alat pengukur", tutup="Tutup rincian", tanpa_data="Tidak ada catatan pada periode ini",
                rata_pm="Rata-rata debu halus (PM2.5)", kelengkapan="Kelengkapan data", petunjuk_zoom="Tahan Ctrl lalu gulir untuk memperbesar peta")
    titik = json.loads(df.to_json(orient="records")) if len(df) else []
    payload = dict(mode=mode, titik=titik, tanpa=tanpa, prov=prov, warna=warna_tema(), teks=teks, tinggi=tinggi, mode_awal="titik", versi=str(hash(json.dumps(titik, sort_keys=True))))
    _komponen(d=payload, key=kunci, default=None)
