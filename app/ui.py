"""Tema & komponen tampilan dashboard (CSS + HTML/SVG).

Semua warna berasal dari app/theme.py (tema merah marun–pink, aksen hijau sage, grafik pastel); modul ini tidak menulis kode warna sendiri.
Nama konstanta lama (MUSTARD, FOREST, MINT, …) dipertahankan agar pemanggil lama tetap berjalan, tetapi nilainya kini peran warna tema.
"""
from __future__ import annotations

import html
import re
from typing import Iterable

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src import style

from . import theme as T

# nama lama → peran warna tema (lihat app/theme.py)
MUSTARD, MUSTARD_D = T.ROSE_DEEP, T.MAROON          # aksen utama & aksen gelap
FOREST, FOREST_D = T.CRIMSON_DARK, T.CRIMSON        # warna gelap sidebar
GOLD, CREAM, MINT, TEAL, CORAL = T.COPPER, T.PUTIH, T.PINK_TINT, T.BLUSH, T.ROSE
NAVY, MUTED, BG, LINE = T.JUDUL, T.TEKS2, T.LATAR, T.GARIS


def warna_bertingkat(n: int) -> list[str]:
    """n warna dari terang ke gelap (tahun lama → tahun terbaru): PINK_SOFT → ROSE → CRIMSON_DARK."""
    return T.bertingkat(T.TAHUN, n)


CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{{--mustard:{MUSTARD};--mustard-d:{MUSTARD_D};--forest:{FOREST};--forest-d:{FOREST_D};--gold:{GOLD};--cream:{CREAM};
--mint:{MINT};--teal:{TEAL};--coral:{CORAL};--navy:{NAVY};--muted:{MUTED};--bg:{BG};--line:{LINE};}}
html, body, .stApp, [data-testid="stAppViewContainer"]{{font-family:'Inter',sans-serif;color:var(--navy);}}
.stApp{{background:var(--bg);}}
header[data-testid="stHeader"]{{background:transparent;height:2.2rem;}}
/* toolbar: sembunyikan menu/Deploy, tetapi pertahankan tombol buka-sidebar yang berada di dalamnya */
[data-testid="stToolbarActions"], [data-testid="stAppDeployButton"], [data-testid="stMainMenu"], [data-testid="stDecoration"], footer{{display:none !important;visibility:hidden;}}
[data-testid="stMainBlockContainer"], .block-container{{max-width:1440px;width:calc(100% - 2.4rem);padding:1.1rem 1.7rem 2.2rem;margin:.6rem auto 1.4rem;background:{T.PUTIH};border-radius:38px;
  border:1px solid {T.PUTIH};box-shadow:0 18px 34px -22px {T.rgba(T.ROSE_DEEP, .22)};}}
h1,h2,h3,h4{{color:var(--navy);letter-spacing:-.01em;}}
p, li, label, span{{color:inherit;}}

/* ---------- elemen sidebar selain menu (menu & wadah sidebar ada di app/sidebar.py) ---------- */
.sb-label{{font-size:.64rem;letter-spacing:.16em;font-weight:700;color:var(--gold) !important;margin:1.1rem 0 .35rem .3rem;text-transform:uppercase;}}
[data-testid="stSidebar"] [data-baseweb="select"] > div, [data-testid="stSidebar"] [data-testid="stDateInput"] > div > div, [data-testid="stSidebar"] [data-baseweb="input"]{{
  background:{T.FILTER_LATAR};border:0;border-radius:14px;box-shadow:inset 0 0 0 1px {T.rgba(T.PUTIH, .15)};}}
[data-testid="stSidebar"] [data-baseweb="select"] *, [data-testid="stSidebar"] input{{color:var(--cream) !important;}}
[data-testid="stSidebar"] span[data-baseweb="tag"]{{background:var(--gold);border-radius:999px;}}
[data-testid="stSidebar"] span[data-baseweb="tag"] *{{color:var(--forest) !important;font-weight:700;}}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{{font-size:.72rem;letter-spacing:.08em;opacity:1;color:{T.rgba(T.PUTIH, .75)} !important;}}
[data-testid="stSidebar"] [data-testid="stRadio"] label p{{font-size:.8rem;color:{T.rgba(T.PUTIH, .9)} !important;}}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label > div:first-child{{background:{T.FILTER_LATAR} !important;box-shadow:inset 0 0 0 2px {T.rgba(T.PUTIH, .55)};}}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) > div:first-child{{background:{T.COPPER} !important;box-shadow:none;}}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],[data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,[data-testid="stSidebar"] .rm-note{{color:{T.rgba(T.PUTIH, .78)} !important;opacity:1 !important;}}
[data-testid="stSidebar"] [data-testid="stTooltipIcon"] svg,[data-testid="stSidebar"] [data-testid="stTooltipHoverTarget"] svg{{color:{T.rgba(T.PUTIH, .6)} !important;}}
[data-testid="stSidebar"] hr{{border-color:{T.rgba(T.PUTIH, .12)};margin:.8rem 0;}}
.sb-avatars{{display:flex;align-items:center;padding:.2rem .3rem;}}
.sb-avatars .av{{width:34px;height:34px;border-radius:50%;border:2px solid var(--forest);margin-left:-9px;display:flex;align-items:center;justify-content:center;
  font-size:.6rem;font-weight:800;color:var(--forest) !important;}}
.sb-avatars .av:first-child{{margin-left:0;}}
.sb-avatars .more{{background:var(--gold);color:var(--forest) !important;}}
.sb-map{{opacity:.95;margin-top:.5rem;}}

/* ---------- tab atas berbentuk pil (gambar 1) ---------- */
[data-testid="stTabs"] [data-baseweb="tab-list"]{{background:{T.PUTIH};border-radius:999px;padding:.2rem 1.8rem;gap:.3rem;justify-content:center;box-shadow:0 4px 18px {T.BAYANGAN_KARTU},inset 0 0 0 1px {T.GARIS};
  position:relative;z-index:5;width:fit-content;margin:.1rem auto 0;border:0;}}
[data-testid="stTabs"] [data-baseweb="tab"]{{font-weight:700;font-size:.82rem;color:var(--muted);padding:.8rem 1.15rem;background:transparent;height:auto;}}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"]{{color:{T.PUTIH};background:{T.TAB_AKTIF};border-radius:999px;}}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] p{{color:{T.PUTIH};}}
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{{background:transparent;height:4px;border-radius:4px 4px 0 0;}}
[data-testid="stTabs"] [data-baseweb="tab-border"]{{display:none;}}

/* ---------- kartu ---------- */
div[class*="st-key-kartu"]{{background:{T.PUTIH};border:1px solid var(--line);border-radius:26px;padding:1.05rem 1.2rem;box-shadow:none;}}
div[class*="st-key-kartu"] > div{{gap:.6rem;}}
.ct{{display:block;color:var(--navy);margin:0 0 .25rem;}}
.ct .tt{{font-weight:700;font-size:.95rem;line-height:1.32;}}
.ct .nw{{white-space:nowrap;}}
.ct .sub{{display:block;font-weight:500;font-size:.74rem;color:var(--muted);margin-top:.2rem;line-height:1.35;}}
.cap{{font-size:.8rem;color:{T.TEKS2};line-height:1.45;margin:.35rem 0 0;}}
.cap b{{color:var(--navy);}}
.tip{{display:inline-block;position:relative;cursor:help;font-size:.82em;font-weight:600;opacity:.75;margin-left:.15rem;text-transform:none;letter-spacing:0;}}
.tip:hover,.tip:focus{{opacity:1;outline:none;}}
.ct .tip{{color:{T.ICON_PINK};opacity:1;}}
.tip::after{{content:attr(data-tip);position:absolute;bottom:135%;left:50%;transform:translateX(-50%);width:max-content;max-width:250px;background:{T.rgba(T.TOOLTIP, .97)};color:{T.PUTIH};font-size:.72rem;font-weight:500;line-height:1.4;padding:.5rem .7rem;border-radius:10px;box-shadow:0 12px 28px {T.rgba(T.TOOLTIP, .30)};opacity:0;pointer-events:none;transition:opacity .15s ease;z-index:60;white-space:normal;text-align:left;}}
.tip:hover::after,.tip:focus::after{{opacity:1;}}
/* sisi muncul tooltip menyesuaikan posisi ikon (diatur skrip di bawah): tidak tertutup sidebar dan tidak keluar layar */
.tip[data-sisi="kiri"]::after{{left:-8px;transform:none;}}
.tip[data-sisi="kanan"]::after{{left:auto;right:-8px;transform:none;}}
[data-testid="stExpander"]{{border:1px solid var(--line);border-radius:16px;background:{T.PUTIH};}}
[data-testid="stExpander"] summary{{font-weight:700;color:var(--navy);}}
.card-teal{{background:{T.BLUSH};border:1px solid {T.GARIS};border-radius:24px;padding:1.2rem 1.3rem;color:{T.MAROON};position:relative;}}
.card-teal .num{{font-size:1.35rem;letter-spacing:.01em;font-weight:800;margin:.45rem 0 .5rem;line-height:1.2;}}
.card-teal .lbl{{font-size:.66rem;letter-spacing:.14em;font-weight:700;text-transform:uppercase;opacity:.95;margin-top:0;}}
.card-teal .meta{{display:flex;justify-content:space-between;font-size:.74rem;opacity:.95;}}
.card-coral{{background:{CORAL};border-radius:24px;padding:1.2rem 1.3rem;color:{T.PUTIH};display:flex;gap:1rem;align-items:center;min-height:104px;}}
.card-coral .tx{{font-weight:700;font-size:.95rem;line-height:1.35;}}
.card-coral .tx small{{display:block;font-size:.66rem;letter-spacing:.12em;font-weight:700;margin-top:.5rem;opacity:.95;}}
.card-coral .ic{{width:56px;height:56px;flex:0 0 56px;}}
.tiles3{{display:grid;grid-template-columns:repeat(auto-fit,minmax(86px,1fr));gap:0;margin-top:.2rem;}}
.tiles3 > div{{text-align:center;padding:.9rem .2rem .6rem;border-left:1px solid var(--line);}}
.tiles3 > div:first-child{{border-left:0;}}
.tiles3 .t{{font-size:.74rem;font-weight:700;margin-top:.35rem;}}
.tiles3 .v{{font-size:.68rem;color:var(--muted);}}
.tiles3 .dot{{width:26px;height:26px;border-radius:50%;background:{MINT};color:var(--navy);margin:.5rem auto 0;display:flex;align-items:center;justify-content:center;font-size:.9rem;}}
.row-mint{{background:{MINT};border-radius:18px;padding:.8rem 1rem;display:flex;align-items:center;gap:.8rem;margin-bottom:.55rem;}}
.row-mint .ico{{width:34px;height:34px;border-radius:50%;background:{T.PUTIH};display:flex;align-items:center;justify-content:center;flex:0 0 34px;}}
.row-mint .tt{{flex:1;font-size:.72rem;color:var(--muted);line-height:1.3;}}
.row-mint .tt b{{color:var(--navy);font-size:.8rem;}}
.row-mint .vv{{font-weight:800;font-size:.86rem;}}
.pos{{color:{T.TEKS2};}} .neg{{color:{T.ROSE_DEEP};}}
.kpi-big{{font-size:2.1rem;font-weight:300;line-height:1.1;margin:.4rem 0 .1rem;}}
.kpi-sub{{font-size:.74rem;color:var(--muted);}}
.kpi-sub .up{{color:{T.TEKS2};font-weight:700;}} .kpi-sub .down{{color:{T.ROSE_DEEP};font-weight:700;}}
.badge-ic{{width:46px;height:46px;border-radius:50%;background:{T.BLUSH};display:flex;align-items:center;justify-content:center;}}
.gainer{{display:grid;grid-template-columns:34px 1fr auto 70px;align-items:center;gap:.7rem;padding:.55rem 0;border-top:1px solid var(--line);}}
.gainer:first-of-type{{border-top:0;}}
.gainer .lg{{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.6rem;font-weight:800;color:{T.PUTIH};}}
.gainer .nm b{{font-size:.82rem;display:block;}} .gainer .nm span{{font-size:.68rem;color:var(--muted);}}
.gainer .pr{{text-align:right;font-size:.78rem;font-weight:700;}} .gainer .pr span{{display:block;font-size:.68rem;color:{T.TEKS2};font-weight:600;}}
.chips{{display:flex;flex-wrap:wrap;gap:.5rem;margin:.2rem 0 .6rem;}}
.chip-s{{background:{MINT};border-radius:999px;padding:.35rem .8rem;font-size:.72rem;font-weight:600;color:var(--navy);}}
.chip-s b{{font-weight:800;}}
.chip-s .sq{{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:6px;}}
.dh{{display:flex;align-items:center;gap:.7rem;margin:.2rem 0 .5rem;}}
.dh .lg{{width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.72rem;font-weight:800;color:{T.PUTIH};}}
.dh b{{display:block;font-size:1.05rem;}} .dh span:not(.lg){{font-size:.72rem;color:var(--muted);}}
.kv{{display:flex;justify-content:space-between;gap:.8rem;padding:.5rem 0;border-top:1px solid var(--line);font-size:.78rem;}}
.kv span{{color:var(--muted);}} .kv b{{text-align:right;}}
.kosong{{font-size:.85rem;line-height:1.45;color:{T.TEKS2};margin:.5rem .1rem;}}
.insight{{background:{MINT};border-radius:20px;padding:1rem 1.2rem;margin-bottom:.7rem;}}
.insight .n{{display:inline-flex;width:28px;height:28px;border-radius:50%;background:var(--mustard);color:{T.PUTIH};align-items:center;justify-content:center;font-weight:800;font-size:.8rem;margin-right:.6rem;}}
.insight b{{font-size:.92rem;}} .insight p{{font-size:.78rem;color:{T.TEKS2};margin:.35rem 0 0;}} .insight em{{font-size:.7rem;color:var(--muted);font-style:normal;}}
[data-testid="stDataFrame"]{{border-radius:16px;overflow:hidden;}}
div[data-testid="stMainBlockContainer"] button[data-testid="stBaseButton-secondary"], div[data-testid="stMainBlockContainer"] button[data-testid="stBaseButton-primary"]{{border-radius:999px;font-weight:700;}}
div[data-testid="stMainBlockContainer"] button[data-testid="stBaseButton-primary"]{{background:{T.MAROON};border:0;color:{T.PUTIH};}}

/* ---------- efek "timbul": satu bayangan, satu durasi, satu kurva untuk kartu, daftar, dan grafik ---------- */
:root{{--e-sh:0 2px 10px {T.BAYANGAN_KARTU};--e-sh-hi:0 24px 46px -8px {T.BAYANGAN_KARTU_TINGGI},0 8px 18px {T.BAYANGAN_KARTU};--e-ease:cubic-bezier(.2,.8,.2,1);--e-t:.25s;}}
[data-testid="stHorizontalBlock"],[data-testid="stColumn"],[data-testid="stVerticalBlock"],[data-testid="stElementContainer"],[data-testid="stTabs"],[data-baseweb="tab-panel"]{{overflow:visible !important;}}
div[class*="st-key-kartu"],.card-teal,.card-coral,.insight{{border-radius:20px;box-shadow:var(--e-sh);}}
.row-mint,.gainer,.tiles3 > div{{border-radius:16px;}}
.gainer{{background:{T.PUTIH};padding:.55rem .6rem;}}
div[class*="st-key-kartu"],.card-teal,.card-coral,.insight,.row-mint,.gainer,.tiles3 > div,.timbul{{
  transition:transform var(--e-t) var(--e-ease),box-shadow var(--e-t) var(--e-ease);will-change:transform;position:relative;}}
div[class*="st-key-kartu"]:hover,.card-teal:hover,.card-coral:hover,.insight:hover,.row-mint:hover,.gainer:hover,.tiles3 > div:hover,.timbul:hover{{
  transform:translateY(-6px) scale(1.01);box-shadow:var(--e-sh-hi);z-index:6;}}
div[class*="st-key-kartu"]:active:not(:has(iframe[title*="echarts"],[data-testid="stPlotlyChart"])),.card-teal:active,.card-coral:active,.insight:active,.row-mint:active,.gainer:active,.tiles3 > div:active,.timbul:active{{
  transform:scale(.98);transition-duration:.12s;}}
/* kartu berisi grafik: menggeser grafik saat tombol ditekan membatalkan klik pada grafik, jadi "ditekan" hanya lewat bayangan */
div[class*="st-key-kartu"]:active:has(iframe[title*="echarts"],[data-testid="stPlotlyChart"]){{box-shadow:0 4px 14px {T.BAYANGAN_KARTU_TINGGI},inset 0 0 0 2px {T.rgba(T.ROSE, .40)};transition-duration:.12s;}}
/* kartu berisi peta 3D: kartu tidak naik/membesar (peta sedang diseret atau diklik); cukup bayangan yang menebal */
div[class*="st-key-kartu"]:has(iframe[title*="peta3d"]):hover,div[class*="st-key-kartu"]:has(iframe[title*="peta3d"]):active{{transform:none;box-shadow:var(--e-sh-hi);}}
iframe[title*="peta3d"]{{border-radius:20px;min-height:520px;display:block;}}
.sel{{transform:translateY(-3px);box-shadow:inset 0 -3px 0 var(--mustard),var(--e-sh);background-color:{T.PUTIH};}}
.sel:hover{{transform:translateY(-6px) scale(1.01);}}
[data-testid="stElementContainer"]:has(> iframe[title="st.iframe"]){{position:absolute;width:0;height:0;overflow:hidden;margin:0;padding:0;}}
[data-testid="stPlotlyChart"],iframe[title*="streamlit_echarts"]{{transition:transform var(--e-t) var(--e-ease),box-shadow var(--e-t) var(--e-ease);border-radius:14px;}}
[data-testid="stPlotlyChart"]:not(div[class*="st-key-kartu"] *):hover,iframe[title*="streamlit_echarts"]:not(div[class*="st-key-kartu"] *):hover{{
  transform:translateY(-6px) scale(1.01);box-shadow:var(--e-sh-hi);}}
.st-key-asap_link{{background:linear-gradient(150deg,{T.ROSE_DEEP} 0%,{T.ROSE_DEEP} 58%,{T.ROSE} 100%);border-radius:20px;box-shadow:var(--e-sh);position:relative;transition:transform var(--e-t) var(--e-ease),box-shadow var(--e-t) var(--e-ease);will-change:transform;}}
.st-key-asap_link:hover{{transform:translateY(-6px) scale(1.01);box-shadow:var(--e-sh-hi);z-index:6;}}
.st-key-asap_link:active{{transform:scale(.98);transition-duration:.12s;}}
.st-key-asap_link a[data-testid="stPageLink-NavLink"]{{display:grid;grid-template-columns:58px 1fr;align-items:center;column-gap:.95rem;row-gap:0;padding:1.1rem 1.3rem 2.7rem;min-height:140px;position:relative;
  background:transparent !important;text-decoration:none;border-radius:20px;cursor:pointer;}}
.st-key-asap_link a [data-testid="stIconMaterial"]{{font-size:54px !important;width:54px;height:54px;color:{T.PUTIH} !important;}}
.st-key-asap_link a p,.st-key-asap_link a [data-testid="stMarkdownContainer"]{{margin:0;color:{T.PUTIH} !important;font-weight:600;font-size:.92rem;line-height:1.3;white-space:normal !important;overflow:visible !important;text-overflow:clip !important;}}
.st-key-asap_link a p strong{{display:block;font-size:2.7rem;font-weight:700;line-height:1;margin-bottom:.2rem;}}
.st-key-asap_link a::after{{content:"Lihat kapan terjadi";position:absolute;left:1.3rem;bottom:1rem;font-size:.66rem;letter-spacing:.12em;font-weight:700;text-transform:uppercase;color:{T.PUTIH};}}
.st-key-asap_link a [data-testid="stMarkdownContainer"]::after{{content:"→";position:absolute;left:11rem;bottom:.85rem;font-size:1.15rem;font-weight:700;color:{T.PUTIH};transition:transform var(--e-t) var(--e-ease);}}
.st-key-asap_link a:hover [data-testid="stMarkdownContainer"]::after{{transform:translateX(6px);}}
.st-key-asap_link a:focus-visible{{outline:3px solid {T.rgba(T.PUTIH, .8)};outline-offset:-4px;}}
@media (prefers-reduced-motion: reduce){{
  .st-key-asap_link:hover,.st-key-asap_link:active{{transform:none !important;}}
  .st-key-asap_link a:hover [data-testid="stMarkdownContainer"]::after{{transform:none !important;}}
}}
/* ---------- Beranda: ubin jenis wilayah yang bisa diklik + panel daftar lokasi ---------- */
.st-key-kartu_p0_tipe{{container-type:inline-size;}}
.ubin-judul{{font-weight:700;font-size:.8rem;color:var(--navy);margin:0 0 .15rem;}}
.st-key-ubin_grid{{display:grid !important;grid-template-columns:repeat(5,minmax(0,1fr));gap:.45rem !important;margin-top:.2rem;}}
.st-key-ubin_grid > *{{min-width:0;}}
div[class*="st-key-ubin_t"]{{position:relative;background:{T.PUTIH};border:1px solid var(--line);border-radius:16px;box-shadow:none;gap:0 !important;min-height:150px;
  transition:transform var(--e-t) var(--e-ease),box-shadow var(--e-t) var(--e-ease);will-change:transform;}}
div[class*="st-key-ubin_t"]:hover{{transform:translateY(-6px) scale(1.01);box-shadow:var(--e-sh-hi);z-index:6;}}
div[class*="st-key-ubin_t"]:active{{transform:scale(.98);transition-duration:.12s;}}
div[class*="st-key-ubin_t"]:has(.ubin-in.sel){{transform:translateY(-3px);box-shadow:inset 0 -3px 0 var(--mustard),var(--e-sh);}}
div[class*="st-key-ubin_t"]:has(.ubin-in.sel):hover{{transform:translateY(-6px) scale(1.01);}}
div[class*="st-key-ubin_t"]:has(button:focus-visible){{outline:2px solid var(--mustard);outline-offset:2px;}}
.ubin-in{{display:flex;flex-direction:column;align-items:center;justify-content:flex-start;text-align:center;padding:.75rem .25rem .45rem;min-height:150px;}}
.ubin-in .t{{font-weight:700;font-size:.72rem;line-height:1.2;margin:.4rem 0 .2rem;min-height:2.4em;display:flex;align-items:center;justify-content:center;color:var(--navy);}}
.ubin-in .v{{font-size:.66rem;color:var(--muted);line-height:1.35;}}
.ubin-in .chev{{margin-top:auto;padding-top:.2rem;font-size:.9rem;line-height:1;color:var(--mustard-d);font-weight:700;transition:transform var(--e-t) var(--e-ease);}}
.ubin-in.sel .chev{{transform:rotate(180deg);}}
div[class*="st-key-ubin_t"] [data-testid="stElementContainer"]:has(button){{position:absolute;inset:0;margin:0;z-index:3;}}
div[class*="st-key-ubin_t"] [data-testid="stButton"],div[class*="st-key-ubin_t"] button{{width:100% !important;height:100% !important;min-height:0;opacity:0;cursor:pointer;}}
@container (max-width: 330px){{
  .st-key-ubin_grid{{grid-template-columns:repeat(6,minmax(0,1fr));}}
  .st-key-ubin_grid > *{{grid-column:span 2;}}
  .st-key-ubin_grid > *:nth-child(4){{grid-column:2 / span 2;}}
  .st-key-ubin_grid > *:nth-child(5){{grid-column:4 / span 2;}}
}}
div[class*="st-key-ubin_panel_"]{{animation:ubinSlide .3s var(--e-ease) both;overflow:hidden;margin-top:.7rem;padding-top:.7rem;border-top:1px solid var(--line);gap:.5rem !important;}}
@keyframes ubinSlide{{from{{opacity:0;transform:translateY(-10px);max-height:0;}}to{{opacity:1;transform:none;max-height:1600px;}}}}
.pnl-h b{{display:block;font-size:.92rem;color:var(--navy);}}
.pnl-h span{{display:block;font-size:.74rem;color:{T.TEKS2};line-height:1.4;margin-top:.15rem;}}
.lok-row{{padding:.5rem 0;border-top:1px solid var(--line);}}
.lok-row:first-of-type{{border-top:0;}}
.lok-top{{display:flex;justify-content:space-between;align-items:flex-start;gap:.6rem;}}
.lok-nm b{{display:block;font-size:.78rem;line-height:1.25;color:var(--navy);}}
.lok-v{{font-size:.7rem;color:var(--muted);text-align:right;white-space:nowrap;}}
.lok-v b{{font-size:.84rem;color:var(--navy);}}
.bdg{{display:inline-block;font-size:.6rem;font-weight:700;border-radius:999px;padding:.12rem .5rem;margin-left:.2rem;}}
.ltd{{display:inline-block;font-size:.6rem;font-weight:600;color:{T.TEKS2};background:{T.PINK_TINT};border-radius:999px;padding:.08rem .45rem;margin-top:.15rem;}}
.lok-bar{{position:relative;height:6px;background:{T.PINK_TINT};border-radius:999px;margin-top:.4rem;}}
.lok-bar i{{position:absolute;left:0;top:0;bottom:0;border-radius:999px;display:block;}}
.lok-bar u{{position:absolute;top:-3px;bottom:-3px;width:2px;background:{T.rgba(T.MAROON, .7)};border-radius:2px;text-decoration:none;}}
/* tautan panel: satu baris (kiri "Lihat di peta", kanan "Bandingkan …"), hitam, tanpa patah baris; bertumpuk rata kiri bila tidak muat */
.st-key-lnk_baris{{flex-direction:row !important;flex-wrap:wrap;justify-content:space-between;align-items:center;column-gap:1.4rem;row-gap:.55rem !important;margin-top:1.1rem;}}
.st-key-lnk_baris > [data-testid="stElementContainer"]{{width:auto !important;flex:0 0 auto;margin:0;}}
.st-key-lnk_baris [data-testid="stButton"]{{display:flex;align-items:center;height:26px;}}
.st-key-lnk_baris button{{color:{T.ROSE_DEEP} !important;font-weight:600;font-size:.8rem;line-height:1.3;padding:0;min-height:0;background:transparent !important;border:0 !important;white-space:nowrap;gap:.3rem;height:22px;display:inline-flex;align-items:center;}}
.st-key-lnk_baris button *{{color:{T.ROSE_DEEP} !important;white-space:nowrap;font-size:.8rem !important;line-height:1.3;}}
.st-key-lnk_baris button [data-testid="stIconMaterial"]{{font-size:1.05rem !important;color:{T.ICON_PINK} !important;}}
.st-key-lnk_baris button:hover p,.st-key-lnk_baris button:focus-visible p{{text-decoration:underline;text-underline-offset:3px;color:{T.TAUTAN_HOVER} !important;}}
@media (prefers-reduced-motion: reduce){{
  div[class*="st-key-ubin_t"]:hover,div[class*="st-key-ubin_t"]:active,div[class*="st-key-ubin_t"]:has(.ubin-in.sel){{transform:none !important;}}
  .ubin-in.sel .chev{{transform:none !important;}}
}}
/* ---------- Kondisi udara: kartu dalam satu baris sama tinggi ---------- */
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p1_don){{align-items:stretch !important;}}
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p1_don) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"]{{height:100%;}}
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p1_don) [data-testid="stLayoutWrapper"]:has(> .st-key-kartu_p1_don),
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p1_don) [data-testid="stLayoutWrapper"]:has(> .st-key-kartu_p1_ispu){{flex:1 1 auto;display:flex;flex-direction:column;}}
.st-key-kartu_p1_don,.st-key-kartu_p1_ispu{{flex:1 1 auto;}}
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p1_bar){{align-items:stretch !important;}}
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p1_bar) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"]{{height:100%;}}
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p1_bar) [data-testid="stLayoutWrapper"]:has(> .st-key-kartu_p1_bar),
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p1_bar) [data-testid="stLayoutWrapper"]:has(> .st-key-kartu_p1_detail){{flex:1 1 auto;display:flex;flex-direction:column;}}
.st-key-kartu_p1_bar,.st-key-kartu_p1_detail{{flex:1 1 auto;}}
/* ---------- Waktu rawan: satu alur tanpa tab ---------- */
/* pola per jam & per bulan sama tinggi */
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p2_jam){{align-items:stretch !important;}}
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p2_jam) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"]{{height:100%;}}
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p2_jam) [data-testid="stLayoutWrapper"]:has(> .st-key-kartu_p2_jam),
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p2_jam) [data-testid="stLayoutWrapper"]:has(> .st-key-kartu_p2_mus){{flex:1 1 auto;display:flex;flex-direction:column;}}
.st-key-kartu_p2_jam,.st-key-kartu_p2_mus{{flex:1 1 auto;}}
/* ---------- Penyebab polusi: dua sebar berdampingan sama tinggi; subjudul kelompok ---------- */
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p3_traf){{align-items:stretch !important;}}
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p3_traf) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"]{{height:100%;}}
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p3_traf) [data-testid="stLayoutWrapper"]:has(> .st-key-kartu_p3_traf),
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p3_traf) [data-testid="stLayoutWrapper"]:has(> .st-key-kartu_p3_dist){{flex:1 1 auto;display:flex;flex-direction:column;}}
.st-key-kartu_p3_traf,.st-key-kartu_p3_dist{{flex:1 1 auto;}}
.sj{{display:flex;align-items:center;gap:.6rem;font-size:.72rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:{T.ROSE_DEEP};margin:.9rem 0 .1rem .25rem;}}
.sj::after{{content:"";flex:1;height:1px;background:var(--line);}}
/* ---------- Lokasi pengukuran: peta dan donut status sama tinggi ---------- */
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p5_peta){{align-items:stretch !important;}}
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p5_peta) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"]{{height:100%;}}
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p5_peta) [data-testid="stLayoutWrapper"]:has(> .st-key-kartu_p5_peta),
[data-testid="stHorizontalBlock"]:has(.st-key-kartu_p5_peta) [data-testid="stLayoutWrapper"]:has(> .st-key-kartu_p5_stat){{flex:1 1 auto;display:flex;flex-direction:column;}}
.st-key-kartu_p5_peta,.st-key-kartu_p5_stat{{flex:1 1 auto;}}
@media (prefers-reduced-motion: reduce){{
  *,*::before,*::after{{transition:none !important;animation:none !important;scroll-behavior:auto !important;}}
  div[class*="st-key-kartu"]:hover,.card-teal:hover,.card-coral:hover,.insight:hover,.row-mint:hover,.gainer:hover,.tiles3 > div:hover,.timbul:hover,.sel,.sel:hover{{transform:none !important;}}
}}
"""


def inject_css(tambahan: str = "") -> None:
    """Satu blok <style> (blok terpisah menambah jarak antar-elemen di atas halaman); `tambahan` = CSS komponen lain, mis. header."""
    st.markdown(f"<style>{CSS}{tambahan}</style>", unsafe_allow_html=True)


_JS_TAB = """
<script>
/* Grafik ECharts di tab yang tersembunyi diukur 0 px; setelah tab dibuka, iframe-nya dimuat ulang sekali agar terukur benar. */
(function(){
  var P = window.parent; if (!P) return; var G = P.__ecGen = (P.__ecGen || 0) + 1;   /* salinan iframe terbaru yang bekerja */
  setInterval(function(){ if (G !== P.__ecGen) return;
    P.document.querySelectorAll('iframe[title*="echarts"]').forEach(function(f){
      var r = f.getBoundingClientRect();
      if (r.width > 0 && r.height < 5) {
        // muat ulang hanya bila grafik SUDAH digambar saat tersembunyi (ukuran 0); grafik yang masih memuat dibiarkan
        var siapTersembunyi = false; try { siapTersembunyi = !!f.contentWindow.document.querySelector('[_echarts_instance_]'); } catch (e) {}
        if (!siapTersembunyi) { f.dataset.ecSeen = ''; return; }
        if (!f.dataset.ecSeen) { f.dataset.ecSeen = Date.now(); return; }          // tunggu: tinggi iframe biasanya menyusul beberapa ms
        if (Date.now() - f.dataset.ecSeen < 900) return;
        var n = +(f.dataset.ecTry || 0), t = +(f.dataset.ecT || 0);
        if (n < 3 && Date.now() - t > 2500) { f.dataset.ecTry = n + 1; f.dataset.ecT = Date.now(); try { f.contentWindow.location.reload(); } catch (e) {} }
      } else if (r.height >= 5) { f.dataset.ecTry = 0; }
    });
  }, 600);
})();
/* Font Inter untuk grafik ECharts: tiap grafik berada di iframe sendiri yang tidak mewarisi font halaman. Stylesheet Inter dipasang ke tiap
   iframe begitu dokumennya ada; setelah font siap, grafik yang sudah tergambar dengan font cadangan diukur & digambar ulang (resize). */
(function(){
  var P = window.parent; if (!P) return; var G = P.__fontGen = (P.__fontGen || 0) + 1;
  var URL_F = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap';
  function inst(d){
    try { var node = d.querySelector('[_echarts_instance_]');
      for (var up = 0; up < 6 && node; up++, node = node.parentElement) {
        var k = Object.keys(node).filter(function(x){ return x.indexOf('__reactFiber') === 0 || x.indexOf('__reactInternalInstance') === 0; })[0];
        for (var f = k ? node[k] : null; f; f = f.return) { if (f.stateNode && typeof f.stateNode.getEchartsInstance === 'function') return f.stateNode.getEchartsInstance(); }
      } } catch (e) {}
    return null;
  }
  function pasang(fr){
    var d; try { d = fr.contentWindow && fr.contentWindow.document; } catch (e) { return; }
    if (!d || !d.head || d.__inter) return; d.__inter = 1;
    var l = d.createElement('link'); l.rel = 'stylesheet'; l.href = URL_F;
    l.onload = function(){
      Promise.all(['400', '500', '600', '700', '800'].map(function(w){ return d.fonts.load(w + ' 12px Inter'); })).then(function(){
        var n = 0; (function gambar(){ var i = inst(d); if (i && !i.isDisposed()) { try { i.resize(); } catch (e) {} } else if (n++ < 40) setTimeout(gambar, 150); })();
      });
    };
    d.head.appendChild(l);
  }
  setInterval(function(){ if (G !== P.__fontGen) return; P.document.querySelectorAll('iframe[title*="echarts"]').forEach(pasang); }, 150);
})();
/* Tooltip ⓘ: bila tidak muat di sisi kiri (tertutup sidebar) atau kanan layar, ratakan ke ikon (atribut data-sisi dibaca CSS). */
(function(){
  var P = window.parent; if (!P) return; var G = P.__tipGen = (P.__tipGen || 0) + 1;
  function atur(e){
    if (G !== P.__tipGen) return;
    var t = e.target && e.target.closest ? e.target.closest('.tip') : null; if (!t) return;
    var r = t.getBoundingClientRect(), c = r.left + r.width / 2, W = P.innerWidth, kiri = 8;
    var sb = P.document.querySelector('[data-testid="stSidebar"]');
    if (sb && sb.getAttribute('aria-expanded') !== 'false') kiri = sb.getBoundingClientRect().right + 8;
    var lebar = Math.min(250, Math.max(120, (t.getAttribute('data-tip') || '').length * 6.3)), s = '';
    if (c - lebar / 2 < kiri) s = 'kiri'; else if (c + lebar / 2 > W - 8) s = 'kanan';
    if (s) t.setAttribute('data-sisi', s); else t.removeAttribute('data-sisi');
  }
  P.document.addEventListener('mouseover', atur, true); P.document.addEventListener('focusin', atur, true);
})();
</script>"""


def inject_js() -> None:
    """Satu iframe tak terlihat (components.html, tinggi 0) berisi skrip untuk halaman induk: perbaikan grafik di tab tersembunyi
    dan efek masuk (app/motion.py). Dipanggil setiap eksekusi; isinya tetap sehingga iframe tidak dimuat ulang."""
    import streamlit.components.v1 as components
    from . import motion
    components.html(_JS_TAB.replace("</script>", "\n" + motion.JS + "\n</script>"), height=0)


# --------------------------------------------------------------------------- #
# ikon garis (SVG kecil)
# --------------------------------------------------------------------------- #
def _svg(path: str, size=22, color=T.ICON_PINK, sw=1.6) -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round">{path}</svg>')


IKON = {
    "perkotaan": '<rect x="4" y="9" width="6" height="11"/><rect x="10" y="4" width="6" height="16"/><rect x="16" y="12" width="4" height="8"/><path d="M6.5 12h1M6.5 15h1M12.5 7h1M12.5 10h1M12.5 13h1"/>',
    "jalan raya": '<path d="M9 3 5 21M15 3l4 18M12 4v3M12 10v3M12 16v3"/>',
    "industri": '<path d="M3 20V10l6 4V10l6 4V6h3v14z"/><path d="M7 17h1M12 17h1M16 17h1"/>',
    "gambut": '<path d="M12 3c-4 3-6 6-6 9a6 6 0 0 0 12 0c0-3-2-6-6-9z"/><path d="M12 12v9"/>',
    "latar bersih": '<path d="M3 20l6-10 4 6 3-4 5 8z"/><circle cx="17" cy="6" r="1.8"/>',
    "dompet": '<rect x="3" y="6" width="18" height="13" rx="3"/><path d="M3 10h18M16 14.5h2"/>',
    "tangan": '<path d="M12 4c2 1 3 3 3 5-2 0-3-2-3-5zM9 6c-2 0-3 1.5-3 3 2 0 3-1.5 3-3z"/><path d="M3 15l4-1 4 1h4l3-2 3 1-6 5H8l-5-1z"/>',
    "lonceng": '<path d="M6 17V11a6 6 0 0 1 12 0v6l1.5 2H4.5z"/><path d="M10 21h4"/>',
    "stetoskop": '<path d="M6 3v6a4 4 0 0 0 8 0V3M10 13v2a4 4 0 0 0 8 0v-1"/><circle cx="18" cy="12" r="2"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "masuk": '<path d="M12 4v13M7 12l5 5 5-5"/>',
    "keluar": '<path d="M12 20V7M7 12l5-5 5 5"/>',
    "api": '<path d="M12 3c1 4 5 5 5 10a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-6 1-9z"/>',
}


def ikon(nama: str, size=22, color=T.ICON_PINK) -> str:
    return _svg(IKON.get(nama, IKON["dompet"]), size, color)


# --------------------------------------------------------------------------- #
# SVG: gauge, sparkline, peta mini, avatar
# --------------------------------------------------------------------------- #
def sparkline(nilai: Iterable[float], warna: str = T.SPARKLINE, w: int = 70, h: int = 26) -> str:
    v = np.asarray([x for x in nilai if x is not None and not np.isnan(x)], float)
    if len(v) < 2:
        return ""
    x = np.linspace(2, w - 2, len(v)); lo, hi = v.min(), v.max()
    y = (h - 3) - (v - lo) / ((hi - lo) or 1) * (h - 6)
    pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in zip(x, y))
    area = f"2,{h} " + pts + f" {w - 2},{h}"
    # kelas "spark" + pathLength=1: app/motion.py menggambar garis dari kiri (stroke-dashoffset) saat kartunya terlihat; tampilan diam tidak berubah
    return (f'<svg class="spark" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><polygon points="{area}" fill="{warna}" fill-opacity=".12"/>'
            f'<polyline pathLength="1" points="{pts}" fill="none" stroke="{warna}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/></svg>')


def avatars_svg(kodes: list[str], tambahan: int, warna: list[str]) -> str:
    av = "".join(f'<span class="av" style="background:{warna[i % len(warna)]}">{html.escape(k[:2])}</span>' for i, k in enumerate(kodes))
    more = f'<span class="av more">+{tambahan}</span>' if tambahan > 0 else ""
    return f'<div class="sb-avatars">{av}{more}</div>'


def peta_mini(lat: np.ndarray, lon: np.ndarray, lebar: int = 220, tinggi: int = 100) -> str:
    """Peta samar: titik emas = stasiun terpilih, busur putus-putus emas ke stasiun terdekat (data nyata, bukan dekorasi acak)."""
    if len(lat) == 0:
        return ""
    X = (np.asarray(lon) - 94) / (142 - 94) * (lebar - 16) + 8
    Y = (6.5 - np.asarray(lat)) / (6.5 + 11.5) * (tinggi - 16) + 8
    arcs, dots = [], []
    for i in range(len(X)):
        d = (X - X[i]) ** 2 + (Y - Y[i]) ** 2; d[i] = np.inf
        if len(X) > 1:
            j = int(np.argmin(d)); mx, my = (X[i] + X[j]) / 2, min(Y[i], Y[j]) - 0.18 * np.sqrt(d[j]) - 4
            arcs.append(f'<path d="M{X[i]:.1f},{Y[i]:.1f} Q{mx:.1f},{my:.1f} {X[j]:.1f},{Y[j]:.1f}" fill="none" stroke="{GOLD}" stroke-width=".9" stroke-dasharray="1.5 2.5" opacity=".8"/>')
        dots.append(f'<circle cx="{X[i]:.1f}" cy="{Y[i]:.1f}" r="2.2" fill="{GOLD}"/>')
    return (f'<svg class="sb-map" width="{lebar}" height="{tinggi}" viewBox="0 0 {lebar} {tinggi}">{"".join(arcs)}{"".join(dots)}</svg>'
            '<div class="rm-note">Animasi dimatikan oleh pengaturan perangkat</div>')


# --------------------------------------------------------------------------- #
# komponen halaman
# --------------------------------------------------------------------------- #
def kartu(kunci: str):
    """Kontainer kartu putih membulat (CSS memilih kelas st-key-kartu*)."""
    return st.container(border=True, key=f"kartu_{kunci}")


def judul_kartu(teks: str, sub: str = "", panah: bool = False, tip: str = "") -> None:
    """Judul kartu = kalimat kesimpulan; `sub` = apa yang diukur + satuan; `tip` = teks tooltip (ⓘ). (`panah` dipertahankan agar kompatibel; tidak dipakai.)"""
    ikon_tip = f'<span class="tip" tabindex="0" data-tip="{html.escape(tip, quote=True)}">ⓘ</span>' if tip else ""
    kepala, _, ekor = html.escape(teks).rpartition(" ")
    judul = (f'{kepala} <span class="nw">{ekor} {ikon_tip}</span>' if kepala else f'<span class="nw">{ekor} {ikon_tip}</span>') if tip else html.escape(teks)   # kata terakhir + ikon ⓘ tidak terpisah baris
    st.markdown(f'<div class="ct"><div class="tt">{judul}</div>{f"<div class=sub>{html.escape(sub)}</div>" if sub else ""}</div>', unsafe_allow_html=True)


def subjudul(teks: str) -> None:
    """Subjudul kecil huruf kapital berpenggaris di atas satu kelompok kartu (halaman yang digabung tanpa tab)."""
    st.markdown(f'<div class="sj">{html.escape(teks)}</div>', unsafe_allow_html=True)


def keterangan(teks: str) -> None:
    """Keterangan di bawah grafik (maksimal 2 kalimat): apa yang terlihat → artinya bagi masyarakat. Teks sudah aman (boleh memuat <b>)."""
    st.markdown(f'<div class="cap">{teks}</div>', unsafe_allow_html=True)


def chips(pasangan: list[tuple]) -> None:
    """pasangan = (label, nilai) atau (label, nilai, teks_tooltip)."""
    def satu(p):
        a, b = p[0], p[1]
        if len(p) > 2 and p[2]:
            return f'<span class="chip-s tip" tabindex="0" data-tip="{html.escape(p[2], quote=True)}">{html.escape(a)} <b>{html.escape(b)}</b></span>'
        return f'<span class="chip-s">{html.escape(a)} <b>{html.escape(b)}</b></span>'
    st.markdown('<div class="chips">' + "".join(satu(p) for p in pasangan) + "</div>", unsafe_allow_html=True)


def kosong(teks: str) -> None:
    """Pesan saat data untuk pilihan filter kosong: teks biasa berwarna abu-abu (tanpa kotak)."""
    st.markdown(f'<div class="kosong">{html.escape(teks)}</div>', unsafe_allow_html=True)


def tema_grafik(fig: go.Figure, tinggi: int = 320, judul: str | None = None) -> go.Figure:
    """Template src/style.py + latar transparan agar menyatu dengan kartu."""
    style.terapkan(fig, judul, tinggi)
    fig.update_layout(paper_bgcolor=T.TRANSPARAN, plot_bgcolor=T.TRANSPARAN, margin=dict(l=50, r=16, t=36 if judul else 12, b=40), font=dict(size=12),
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, font=dict(size=11)),
                      # tooltip seragam dengan ECharts: gelap, teks putih
                      separators=",.", hoverlabel=dict(bgcolor=T.rgba(T.TOOLTIP, .95), bordercolor=T.rgba(T.TOOLTIP, .95), font=dict(color=T.PUTIH, size=12, family="Inter, sans-serif"), namelength=-1))
    return fig


def plot(fig: go.Figure, kunci: str, pilih: bool = False):
    """Plotly. `pilih=True` → klik titik/batang mengirim seleksi ke Streamlit (on_select='rerun'); mengembalikan daftar titik terpilih."""
    if not pilih:
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key=f"pc_{kunci}")
        return []
    ev = st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key=f"pc_{kunci}", on_select="rerun", selection_mode="points")
    return list(ev.selection.points) if ev is not None and getattr(ev, "selection", None) else []


def pilihan_plotly(kunci: str) -> list:
    """Seleksi Plotly dari eksekusi sebelumnya (dibaca sebelum figur dibuat agar bisa meredupkan sisanya)."""
    s = st.session_state.get(f"pc_{kunci}")
    try:
        return list(s.selection.points)
    except Exception:
        try:
            return list(s["selection"]["points"])
        except Exception:
            return []
