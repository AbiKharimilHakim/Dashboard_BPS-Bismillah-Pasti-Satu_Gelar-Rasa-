"""Dashboard Kualitas Udara & Kesehatan — DA Gelar Rasa 2026.

Jalankan dari folder proyek:  streamlit run app/streamlit_app.py

Isi analisis berasal dari notebook 03–05 (tabel di data/processed/ dan reports/key_numbers.json); aplikasi ini tidak menghitung ulang
analisis. Semua teks ditulis untuk pembaca awam (lihat app/glossary.py dan app/teks.py); kode lokasi tidak ditampilkan.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import streamlit as st

st.set_page_config(page_title="Udara & Kesehatan Indonesia", page_icon=str(ROOT / "assets" / "logo_gelar_rasa_ikon.png"), layout="wide", initial_sidebar_state="expanded")

from app import data as DT  # noqa: E402
from app import glossary as G  # noqa: E402
from app import header, motion, nav, pages, sidebar, theme, ui  # noqa: E402
from src import config as cfg  # noqa: E402

D = DT.muat()

# (judul menu, slug URL, ikon Material outline, fungsi halaman) — urutan halaman tidak berubah
MENU = [("Beranda", "", "home", pages.p0), ("Kondisi udara", "kondisi-udara", "trending_up", pages.p1), ("Waktu rawan", "waktu-rawan", "schedule", pages.p2),
        ("Penyebab polusi", "penyebab-polusi", "air", pages.p3), ("Dampak kesehatan", "dampak-kesehatan", "favorite", pages.p4), ("Lokasi pengukuran", "lokasi-pengukuran", "sensors", pages.p5)]
CTX: dict = {}


def _bungkus(fn):
    def _halaman():
        fn(CTX["C"])
    _halaman.__name__ = fn.__name__
    return _halaman


daftar = []
for judul, slug, ikon, fn in MENU:
    kw = dict(default=True) if slug == "" else dict(url_path=slug)
    daftar.append((st.Page(_bungkus(fn), title=judul, icon=f":material/{ikon}:", **kw), slug, ikon))
nav.REG = {slug: pg for pg, slug, _ in daftar}
aktif = st.navigation([pg for pg, _, _ in daftar], position="hidden")

# efek masuk (app/motion.py): skrip di ui.inject_js memasang animasi saat halaman berganti; server hanya mencatat halaman terakhir
# agar grafik ECharts tahu kapan memakai animasi masuk. CSS dikirim dalam satu blok <style>.
motion.siapkan(aktif.url_path)
ui.inject_css(header.CSS + motion.CSS)
sidebar.inject_css()
ui.inject_js()

with st.sidebar:
    sidebar.render_logo()
    sidebar.render_nav(daftar, aktif)

with st.sidebar, st.container(key="sb_filter"):
    st.markdown('<div class="sb-label">Pilih data yang ditampilkan</div>', unsafe_allow_html=True)
    s = D.sites.assign(nama=D.sites.kode_stasiun.map(G.PENDEK), jenis=D.sites.kelompok_lokasi.map(G.JENIS))
    tgl = st.date_input("Pilih periode", value=(D.tgl_min, D.tgl_maks), min_value=D.tgl_min, max_value=D.tgl_maks, key="f_tgl", format="DD/MM/YYYY",
                        help="Periode catatan udara yang ditampilkan di semua halaman.")
    if not isinstance(tgl, (tuple, list)) or len(tgl) < 2:
        tgl = (tgl[0] if isinstance(tgl, (tuple, list)) else tgl, D.tgl_maks)
    pulau = st.multiselect("Pilih pulau", cfg.URUTAN_PULAU, key="f_pulau", placeholder="Semua pulau")
    opt_prov = sorted(s[s.pulau.isin(pulau)].provinsi.unique()) if pulau else sorted(s.provinsi.unique())
    provinsi = st.multiselect("Pilih provinsi", opt_prov, key="f_prov", placeholder="Semua provinsi")
    base = s
    if pulau:
        base = base[base.pulau.isin(pulau)]
    if provinsi:
        base = base[base.provinsi.isin(provinsi)]
    jenis_dipilih = st.session_state.get("f_jenis", [])
    if jenis_dipilih:
        base = base[base.jenis.isin(jenis_dipilih)]
    kota = st.multiselect("Pilih kota/kabupaten", sorted(base.nama), key="f_kota", placeholder="Semua kota/kabupaten",
                          help="Setiap pilihan = satu lokasi pengukuran udara. Tempat alat pengukur udara dipasang.")
    jenis = st.multiselect("Pilih jenis wilayah", G.JENIS_URUT, key="f_jenis", placeholder="Semua jenis wilayah", help=G.TIPS["jenis"])
    pol = st.selectbox("Pilih zat pencemar", list(DT.POLUTAN), format_func=lambda k: G.POL_NAMA[k], key="f_pol",
                       help="Debu halus (PM2.5) adalah partikel debu sangat kecil yang bisa masuk ke paru-paru. Gas pencemar: NO₂ (asap kendaraan), SO₂ (pembakaran batu bara), CO, dan O₃ (ozon).")
    standar = st.radio("Pilih batas aman", list(DT.STANDAR), format_func=lambda k: G.BATAS_NAMA[k], key="f_std",
                       help="Batas aman nasional (PP 22/2021): debu halus 55 µg/m³ per hari. Batas aman WHO: 15 µg/m³ per hari, lebih ketat.")

    f = dict(tgl=tgl, pulau=pulau, provinsi=provinsi, tipe=[G.INTERNAL_DARI_JENIS[j] for j in jenis], stasiun=[G.KODE_DARI_PENDEK[n] for n in kota],
             standar=standar, versi="bertopeng")     # catatan alat yang macet selalu dibuang (sakelar di sidebar dihapus; angka tidak berubah)
    stas = DT.stasiun_terpilih(D, f)

    st.markdown('<div class="sb-label">Lokasi terpilih</div>', unsafe_allow_html=True)
    st.markdown(ui.avatars_svg([G.pendek(k) for k in stas[:4]], max(len(stas) - 4, 0), theme.AVATAR), unsafe_allow_html=True)
    sub = D.sites[D.sites.kode_stasiun.isin(stas)]
    st.markdown(ui.peta_mini(sub.latitude_dd.to_numpy(), sub.longitude_dd.to_numpy()), unsafe_allow_html=True)
    st.caption(f"{len(stas)} dari {len(D.sites)} lokasi pengukuran · {G.tgl(tgl[0])} – {G.tgl(tgl[1])}")

with st.sidebar:
    sidebar.render_footer()

dat = DT.data_terfilter(D, f)
CTX["C"] = SimpleNamespace(D=D, dat=dat, f=f, pol=pol, kol=f"{pol}_ug_m3")
aktif.run()
