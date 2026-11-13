"""Gaya visual tunggal untuk seluruh grafik (palet ISPU, tipe lokasi, QC, font, template Plotly).

Semua grafik di notebook dan dashboard WAJIB memakai modul ini agar warna,
font, dan tata letak konsisten. Kode warnanya sendiri ada di app/theme.py (satu sumber).
"""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

from app import theme as T     # palet tunggal (dashboard & notebook memakai warna yang sama)

FONT_FAMILY = "Inter, sans-serif"
WARNA_TEKS = T.JUDUL
WARNA_TEKS_REDUP = T.TEKS2
WARNA_GARIS = T.GARIS
WARNA_LATAR = T.KARTU
WARNA_UTAMA = T.ROSE_DEEP     # aksen utama dashboard
WARNA_NA = T.TANPA_DATA       # data kosong

# Kategori ISPU (Permen LHK 14/2020)
ISPU_URUTAN = ["Baik", "Sedang", "Tidak Sehat", "Sangat Tidak Sehat", "Berbahaya"]
ISPU_WARNA = dict(T.ISPU)

# Kelompok lokasi (turunan `site_type`)
TIPE_LOKASI_WARNA = dict(T.JENIS)

# Status QC
QC_WARNA = dict(T.QC)

# Tingkat keparahan masalah data
KEPARAHAN_URUTAN = ["Kritis", "Tinggi", "Sedang", "Rendah"]
KEPARAHAN_WARNA = dict(T.PRIORITAS)

# Skala warna tunggal untuk persentase kelengkapan (gelap = lengkap)
SKALA_KELENGKAPAN = [list(x) for x in T.SKALA_KELENGKAPAN]


def buat_template() -> go.layout.Template:
    t = go.layout.Template()
    t.layout = go.Layout(
        font=dict(family=FONT_FAMILY, size=13, color=WARNA_TEKS),
        title=dict(font=dict(size=17, color=WARNA_TEKS), x=0.0, xanchor="left"),
        paper_bgcolor=WARNA_LATAR,
        plot_bgcolor=WARNA_LATAR,
        colorway=list(T.URUTAN_GRAFIK),
        xaxis=dict(showgrid=False, linecolor=WARNA_GARIS, ticks="outside", tickcolor=WARNA_GARIS),
        yaxis=dict(gridcolor=WARNA_GARIS, zeroline=False, linecolor=WARNA_GARIS),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=70, r=30, t=80, b=60),
        hoverlabel=dict(font=dict(family=FONT_FAMILY)),
    )
    return t


pio.templates["dashboard_udara"] = buat_template()
pio.templates.default = "dashboard_udara"


def terapkan(fig: go.Figure, judul: str | None = None, tinggi: int | None = None,
             sumbu_x: str | None = None, sumbu_y: str | None = None) -> go.Figure:
    """Terapkan judul, tinggi, dan label sumbu (Bahasa Indonesia, lengkap dengan satuan)."""
    fig.update_layout(template="dashboard_udara")
    if judul:
        fig.update_layout(title_text=judul)
    if tinggi:
        fig.update_layout(height=tinggi)
    if sumbu_x:
        fig.update_xaxes(title_text=sumbu_x)
    if sumbu_y:
        fig.update_yaxes(title_text=sumbu_y)
    return fig


def simpan_gambar(fig: go.Figure, nama: str, tinggi: int = 800, lebar: int = 1600, folder=None) -> dict:
    """Simpan grafik penting ke reports/figures/: PNG selebar `lebar` px (default 1600) dan HTML interaktif."""
    from .config import FIG_DIR

    folder = folder or FIG_DIR
    folder.mkdir(parents=True, exist_ok=True)
    html = simpan_html(fig, nama, folder)
    png = folder / f"{nama}.png"
    import time

    for percobaan in range(4):                 # peramban kaleido kadang gagal ditutup di Windows; ulangi beberapa kali
        try:
            fig.write_image(png, width=lebar, height=tinggi, scale=1)
            break
        except RuntimeError:
            if percobaan == 3:
                raise
            time.sleep(2 + percobaan)
    return {"html": html, "png": str(png)}


def simpan_html(fig: go.Figure, nama: str, folder=None) -> str:
    """Simpan grafik interaktif sebagai HTML mandiri di reports/figures/."""
    from .config import FIG_DIR

    folder = folder or FIG_DIR
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{nama}.html"
    fig.write_html(path, include_plotlyjs="cdn", full_html=True)
    return str(path)
