"""Sidebar navigasi: hijau tua keabu-abuan, ikon garis emas, label kapital kecil, dan pil aktif yang menyatu dengan latar konten.

Navigasi memakai st.navigation(position="hidden") + st.page_link. Halaman aktif dibungkus st.container(key="nav_active"), halaman lain
st.container(key="nav_item_<slug>") sehingga CSS menargetnya lewat kelas .st-key-* (bukan kelas acak Streamlit).

Pil aktif: sudut kiri membulat penuh, sisi kanan menempel ke tepi sidebar. Lengkungan cekung di atas dan di bawah pil dibuat dengan
pseudo-element ::before dan ::after (kuadran lingkaran transparan, sisanya berwarna latar konten) sehingga tepi sidebar melengkung halus
menuju pil, seperti pada gambar acuan.
"""
from __future__ import annotations

import base64
import io
from functools import lru_cache
from pathlib import Path

import streamlit as st

from . import theme as T

SB_BG, SB_BG2 = T.SIDEBAR_ATAS, T.SIDEBAR_BAWAH   # gradasi vertikal CRIMSON_DARK → CRIMSON
INK = T.rgba(T.PUTIH, .85)                  # teks menu (putih 85%)
EMAS = T.rgba(T.PUTIH, .85)                 # ikon menu (putih 85%)
EMAS_TULISAN = T.rgba(T.PUTIH, .78)         # label "DIBUAT OLEH" (COPPER di dasar sidebar hanya 4,2:1, jadi putih)
LATAR = T.LATAR                             # pil menu aktif = latar halaman (#FEFAFB), menyatu dengan area konten
R = 20                                      # jari-jari lengkungan cekung (px)
ASET = Path(__file__).resolve().parents[1] / "assets"
LOGO = ASET / "logo_gelar_rasa_putih.png"   # versi putih-kuning berlatar transparan (asli: assets/logo_gelar_rasa.png, tidak diubah)
LOGO_UPN = ASET / "logo_upn.png"            # logo UPN "Veteran" Jawa Timur (warna asli, berlatar transparan)
TINGGI_LOGO = 46                           # tinggi tampil kedua logo (px)
IKON = ASET / "logo_gelar_rasa_ikon.png"    # lambang saja, untuk ikon tab peramban

CSS = f"""
:root{{--sb-gold-tulis:{EMAS_TULISAN};--sb-bg:{SB_BG};--sb-bg2:{SB_BG2};--sb-ink:{INK};--sb-gold:{EMAS};--content-bg:{LATAR};--sb-r:{R}px;}}

/* ---- wadah sidebar: tanpa garis tepi, tanpa padding kanan agar pil menyentuh tepi ---- */
[data-testid="stSidebar"]{{width:288px !important;min-width:288px !important;background:linear-gradient(180deg,var(--sb-bg) 0%,var(--sb-bg2) 100%);border:0 !important;box-shadow:none !important;}}
[data-testid="stSidebar"] > div:first-child{{background:transparent;border:0;}}
/* lebar dipaksa 288px, tetapi Streamlit hanya menggeser 256px saat ditutup → sisa 32px menutupi tombol buka; geser penuh */
[data-testid="stSidebar"][aria-expanded="false"]{{transform:translateX(-100%) !important;pointer-events:none;}}
[data-testid="stSidebarContent"]{{background:transparent;padding:0 !important;overflow-x:hidden;scrollbar-gutter:auto !important;scrollbar-width:none;}}
[data-testid="stSidebarContent"]::-webkit-scrollbar{{display:none;}}
[data-testid="stSidebarUserContent"]{{padding:0 0 1.2rem 0 !important;margin:0 !important;width:100% !important;}}
[data-testid="stSidebarNav"],[data-testid="stSidebarNavSeparator"]{{display:none !important;}}
[data-testid="stSidebar"] hr{{border-color:{T.rgba(T.PUTIH, .12)};}}
[data-testid="stSidebar"] *{{color:var(--sb-ink);}}
/* header sidebar: hanya menyisakan tombol tutup/buka yang ringkas */
[data-testid="stSidebarHeader"]{{background:transparent;height:34px;min-height:34px;padding:0 .9rem;margin:0;display:flex;justify-content:flex-end;align-items:center;position:relative;z-index:3;}}
[data-testid="stSidebarCollapseButton"] button,[data-testid="stSidebarCollapseButton"] button *{{color:var(--sb-ink) !important;}}
[data-testid="stSidebarCollapseButton"] button:hover{{background:{T.rgba(T.PUTIH, .10)};}}
/* tombol buka sidebar (tampil saat sidebar ditutup atau di layar kecil) */
[data-testid="stExpandSidebarButton"]{{position:fixed;top:.9rem;left:.9rem;z-index:1000;background:var(--sb-bg);border-radius:999px;padding:.3rem .45rem;box-shadow:0 8px 18px -8px {T.rgba(T.CRIMSON_DARK, .55)};}}
[data-testid="stExpandSidebarButton"],[data-testid="stExpandSidebarButton"] *{{color:var(--sb-gold) !important;}}
[data-testid="stExpandSidebarButton"]:hover{{background:var(--sb-bg2);}}
/* jarak horizontal untuk blok selain navigasi (logo & filter) */
.st-key-sb_filter{{padding:0 1.1rem;}}

/* ---- daftar menu ---- */
.st-key-sb_nav{{gap:6px !important;padding:.5rem 0 .3rem 14px;overflow:visible !important;}}
.st-key-sb_nav [data-testid="stElementContainer"],div[class*="st-key-nav_item_"],.st-key-nav_active{{overflow:visible !important;}}
div[class*="st-key-nav_item_"],.st-key-nav_active{{position:relative;gap:0 !important;}}
.st-key-sb_nav a[data-testid="stPageLink-NavLink"]{{display:flex;align-items:center;gap:14px;width:100%;padding:12px 16px 12px 18px;min-height:0;text-decoration:none;
  border-radius:999px 0 0 999px;background:transparent !important;transition:transform .25s ease,background-color .25s ease;}}
.st-key-sb_nav a[data-testid="stPageLink-NavLink"] p{{margin:0;white-space:nowrap;font-size:12.5px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--sb-ink) !important;line-height:1.2;}}
.st-key-sb_nav a[data-testid="stPageLink-NavLink"] [data-testid="stIconMaterial"]{{color:var(--sb-gold) !important;font-size:20px;width:20px;height:20px;}}
.st-key-sb_nav a[data-testid="stPageLink-NavLink"]:focus-visible{{outline:2px solid var(--sb-gold);outline-offset:-2px;}}

/* item non-aktif: bergeser ke kanan 6px + latar putih transparan 8% saat hover */
div[class*="st-key-nav_item_"] a[data-testid="stPageLink-NavLink"]:hover{{transform:translateX(6px);background:{T.rgba(T.PUTIH, .10)} !important;}}

/* item aktif: pil sewarna latar konten, menempel ke tepi kanan, bayangan lembut di bawahnya */
.st-key-nav_active{{background:var(--content-bg);border-radius:999px 0 0 999px;margin-right:-1px;box-shadow:0 10px 14px -10px {T.rgba(T.CRIMSON_DARK, .45)};}}
.st-key-nav_active a[data-testid="stPageLink-NavLink"] p{{color:{T.MAROON} !important;font-weight:700;}}
.st-key-nav_active a[data-testid="stPageLink-NavLink"] [data-testid="stIconMaterial"]{{color:{T.MAROON} !important;}}
.st-key-nav_active a[data-testid="stPageLink-NavLink"]:hover{{background:transparent !important;transform:none;}}
/* lengkungan cekung: kuadran lingkaran transparan (menampakkan sidebar) berpusat di sudut kiri atas / kiri bawah, sisanya warna latar */
.st-key-nav_active::before,.st-key-nav_active::after{{content:"";position:absolute;right:0;width:var(--sb-r);height:var(--sb-r);pointer-events:none;}}
.st-key-nav_active::before{{top:calc(var(--sb-r) * -1);background:radial-gradient(circle at 0 0,transparent calc(var(--sb-r) - .6px),var(--content-bg) calc(var(--sb-r) - .1px));}}
.st-key-nav_active::after{{bottom:calc(var(--sb-r) * -1);background:radial-gradient(circle at 0 100%,transparent calc(var(--sb-r) - .6px),var(--content-bg) calc(var(--sb-r) - .1px));}}

/* ---- blok logo: Gelar Rasa (putih-kuning) | pemisah | UPN, satu baris, rata tengah, langsung di atas latar sidebar ---- */
/* jarak ke menu pertama tetap 39px (31px + padding atas menu 8px) = jarak pil terakhir → label filter */
.st-key-sb_logo{{padding:0;}}
.sb-logos{{display:flex;align-items:center;justify-content:center;gap:14px;margin:0 auto 31px;padding:0 16px;max-width:100%;box-sizing:border-box;}}
.sb-logos img{{display:block;height:{TINGGI_LOGO}px;width:auto;max-width:100%;flex:0 1 auto;object-fit:contain;}}
.sb-logos .sep{{display:block;width:1px;height:{TINGGI_LOGO - 8}px;background:{T.rgba(T.PUTIH, .30)};flex:0 0 1px;}}
/* ---- tulisan paling bawah ---- */
.st-key-sb_foot{{margin:1.4rem 1.1rem 0 32px;padding-top:.9rem;border-top:1px solid {T.rgba(T.PUTIH, .18)};}}
.sb-foot small{{display:block;font-size:.66rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--sb-gold-tulis) !important;margin-bottom:.2rem;}}
.sb-foot b{{display:block;font-size:13px;font-weight:700;color:{T.PUTIH} !important;line-height:1.35;}}
/* isi sidebar setinggi layar: tulisan bawah menempel di dasar bila isi pendek, dan di ujung gulir bila panjang */
[data-testid="stSidebarContent"]{{display:flex;flex-direction:column;min-height:100%;}}
[data-testid="stSidebarUserContent"]{{flex:1 1 auto;display:flex;flex-direction:column;}}
[data-testid="stSidebarUserContent"] > div{{flex:1 1 auto;display:flex;flex-direction:column;}}
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"]{{flex:1 1 auto;}}
[data-testid="stLayoutWrapper"]:has(> .st-key-sb_foot){{margin-top:auto;}}

@media (prefers-reduced-motion: reduce){{
  .st-key-sb_nav a[data-testid="stPageLink-NavLink"]{{transition:none !important;}}
  div[class*="st-key-nav_item_"] a[data-testid="stPageLink-NavLink"]:hover{{transform:none !important;}}
}}
"""


def inject_css() -> None:
    """Seluruh CSS sidebar; dipanggil sekali per eksekusi (entrypoint berjalan untuk setiap halaman)."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def render_nav(halaman: list[tuple[st.Page, str, str]], aktif: st.Page) -> None:
    """Gambar daftar menu. halaman = [(st.Page, slug, nama_ikon_material)]; `aktif` = halaman yang sedang dibuka."""
    with st.container(key="sb_nav"):
        for pg, slug, ikon in halaman:
            kunci = "nav_active" if pg.title == aktif.title else f"nav_item_{slug}"
            with st.container(key=kunci):
                st.page_link(pg, label=pg.title, icon=f":material/{ikon}:")


def _png_b64(path: Path, tinggi: int) -> tuple[str, int, int]:
    """PNG diperkecil ke `tinggi` px (3× tinggi tampil agar tajam di layar rapat) lalu dijadikan base64; warna tidak diubah."""
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    lebar = round(im.width * tinggi / im.height)
    im = im.convert("RGBa").resize((lebar, tinggi), Image.LANCZOS).convert("RGBA")     # alpha premultiplied agar tepi tetap halus
    buf = io.BytesIO(); im.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode(), lebar, tinggi


@lru_cache(maxsize=1)
def _logo_html() -> str:
    """Dua logo sebagai data-URI base64 di dalam HTML: tidak bergantung pada server file statis, jadi tetap tampil setelah deploy."""
    g, gw, gh = _png_b64(LOGO, TINGGI_LOGO * 3)
    u, uw, uh = _png_b64(LOGO_UPN, TINGGI_LOGO * 3)
    return (f'<div class="sb-logos"><img src="data:image/png;base64,{g}" alt="Logo Gelar Rasa" width="{gw}" height="{gh}">'
            f'<span class="sep" aria-hidden="true"></span>'
            f'<img src="data:image/png;base64,{u}" alt="Logo UPN Veteran Jawa Timur" width="{uw}" height="{uh}"></div>')


def render_logo() -> None:
    """Logo Gelar Rasa (putih-kuning) dan logo UPN dalam satu baris, paling atas sidebar."""
    with st.container(key="sb_logo"):
        st.markdown(_logo_html(), unsafe_allow_html=True)


def render_footer() -> None:
    """Pembuat dashboard, paling bawah sidebar (setelah semua filter)."""
    with st.container(key="sb_foot"):
        st.markdown('<div class="sb-foot"><small>Dibuat oleh</small><b>BPS (Bismillah Pasti Satu)</b></div>', unsafe_allow_html=True)
