"""Header tunggal (gradasi merah marun → pink) untuk SEMUA halaman dashboard.

Satu fungsi, `render_header(...)`, dipakai Beranda, Kondisi udara, Waktu rawan, Penyebab polusi, Dampak kesehatan, dan Lokasi pengukuran,
supaya warna, gradasi, radius, tinggi, ukuran huruf, ukuran gauge, dan posisi lengkungan identik di setiap halaman.

Satu blok HTML/CSS dengan grid "1fr 300px 1fr" (tinggi tetap 200 px), seluruhnya memakai Inter:
  KIRI   judul halaman (Inter 800, putih, maksimal 2 baris; ukuran huruf menyesuaikan lebar kolom agar tiap baris muat)
  TENGAH pertanyaan tepat di atas tepi bawah header, lalu gauge setengah lingkaran yang menggantung di lengkungan bawah:
         lengkungan = setengah lingkaran berjari-jari LOBE_R yang pusatnya di tepi bawah header (sumbu tengah);
         busur gauge = setengah lingkaran berjari-jari GAUGE_R dengan pusat YANG SAMA (sepusat), 20 px ke dalam dari tepi lengkungan;
         ikon dan jawaban berada di dalam mangkuk busur
  KANAN  KPI: ikon dalam lingkaran, label huruf besar + ⓘ, angka besar
Tidak ada teks kecil di header: keterangan gauge masuk ke tooltip bawaan gauge (<title>), catatan KPI masuk ke tooltip ikon ⓘ.

Angka tidak dihitung di sini; tiap halaman menghitungnya dari data terfilter (lihat app/pages.py) lalu mengirimnya ke fungsi ini.
"""
from __future__ import annotations

import html
import re

import numpy as np
import streamlit as st

from . import theme as T, ui

# --- ikon garis putih (viewBox 24×24, gaya outline) --------------------------------------------------------------
IKON = {
    "udara": '<path d="M3 8h11a3 3 0 1 0-3-3M3 12h16a3 3 0 1 1-3 3M3 16h7"/>',
    "batang": '<path d="M5 20V11M12 20V4M19 20v-6"/>',
    "jam": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.2 2"/>',
    "penyetel": '<path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
    "hati": '<path d="M12 20s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.2a4.3 4.3 0 0 1 7.5 2.6C19.5 15.4 12 20 12 20z"/>',
    "pin": '<path d="M12 21s-6.5-5.8-6.5-11.2a6.5 6.5 0 0 1 13 0C18.5 15.2 12 21 12 21z"/><circle cx="12" cy="10" r="2.3"/>',
    "debu": '<circle cx="8" cy="8" r="1.7"/><circle cx="15.5" cy="7" r="1.2"/><circle cx="12" cy="13" r="2"/><circle cx="6.5" cy="16.5" r="1.2"/><circle cx="17.5" cy="16" r="1.6"/>',
    "api": '<path d="M12 3c1 4 5 5 5 10a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-6 1-9z"/>',
    "lapisan": '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>',
    "stetoskop": '<path d="M6 3v6a4 4 0 0 0 8 0V3M10 13v2a4 4 0 0 0 8 0v-1"/><circle cx="18" cy="12" r="2"/>',
    "centang": '<circle cx="12" cy="12" r="9"/><path d="M7.5 12.5l3 3 6-6.5"/>',
}


def _ikon(nama: str, ukuran: int, sw: float = 1.6, warna: str = T.PUTIH) -> str:
    return (f'<svg width="{ukuran}" height="{ukuran}" viewBox="0 0 24 24" fill="none" stroke="{warna}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">'
            f'{IKON.get(nama, IKON["pin"])}</svg>')


# --- gauge -------------------------------------------------------------------------------------------------------
GAUGE_W, GAUGE_H, GAUGE_R, GAUGE_CY = 280, 150, 112, 14
LOBE_R = GAUGE_R + 20          # jari-jari lengkungan bawah (CSS .hb-lobe: lebar 2×LOBE_R, tinggi LOBE_R + 1)
TINGGI_HEADER = 200
FONT = "Inter,sans-serif"


def _ukuran_huruf(teks: str, lebar_maks: float, maks: float = 26.0, minim: float = 14.0) -> float:
    """Perkiraan: huruf tebal ≈ 0,6 × ukuran per karakter; kecilkan agar muat dalam lebar mangkuk pada tinggi teks itu."""
    return float(np.clip(lebar_maks / (0.6 * max(len(teks), 1)), minim, maks))


def gauge_svg(rasio: float, nilai: str, ikon: str, label: str, keterangan: str = "") -> str:
    """Setengah lingkaran (mangkuk) putih seperti acuan: busur latar putih 30%, busur nilai putih solid berujung bulat, titik penanda putih bercincin mustard,
    ikon garis di atas jawaban. `nilai` boleh dua baris ("23 dari 26\\nlokasi"): baris pertama besar, kedua kecil. Busur & titik tumbuh dari 0 dalam 0,8 detik."""
    p = float(np.clip(0.0 if rasio is None or not np.isfinite(rasio) else rasio, 0.0, 1.0))
    cx, cy, r = GAUGE_W / 2, GAUGE_CY, GAUGE_R
    x0, x1 = cx - r, cx + r
    xe, ye = cx - r * np.cos(np.pi * p), cy + r * np.sin(np.pi * p)
    baris = [b.strip() for b in nilai.split("\n") if b.strip()][:2] or ["–"]

    def lebar_pada(kedalaman: float) -> float:       # lebar mangkuk pada kedalaman tertentu di bawah garis tengah, dikurangi ruang napas
        return 2 * np.sqrt(max(r * r - kedalaman * kedalaman, 1)) - 26

    m0 = re.match(r"[\d.,]+", baris[0])
    cu = f' data-countup="{html.escape(m0.group(0))}"' if m0 else ""     # angka di pusat gauge ikut menghitung naik (app/motion.py)
    if len(baris) == 1:
        d1 = 76; f1 = _ukuran_huruf(baris[0], lebar_pada(d1))
        teks = f'<text x="{cx}" y="{cy + d1:.1f}" text-anchor="middle" fill="{T.PUTIH}" font-size="{f1:.1f}" font-weight="700" font-family="{FONT}"{cu}>{html.escape(baris[0])}</text>'
    else:
        d1, d2 = 68, 90; f1 = _ukuran_huruf(baris[0], lebar_pada(d1)); f2 = float(np.clip(_ukuran_huruf(baris[1], lebar_pada(d2), 13, 11), 11, 13))
        teks = (f'<text x="{cx}" y="{cy + d1:.1f}" text-anchor="middle" fill="{T.PUTIH}" font-size="{f1:.1f}" font-weight="700" font-family="{FONT}"{cu}>{html.escape(baris[0])}</text>'
                f'<text x="{cx}" y="{cy + d2:.1f}" text-anchor="middle" fill="{T.PUTIH}" fill-opacity=".92" font-size="{f2:.1f}" font-weight="600" font-family="{FONT}">{html.escape(baris[1])}</text>')
    busur_nilai = (f'<path class="va" pathLength="100" d="M {x0:.2f} {cy:.2f} A {r} {r} 0 0 0 {xe:.2f} {ye:.2f}" fill="none" stroke="{T.PUTIH}" stroke-width="7" stroke-linecap="round"/>'
                   if p > 0.004 else "")
    judul_tip = f"<title>{html.escape(keterangan)}</title>" if keterangan else ""      # keterangan tampil sebagai tooltip saat gauge disorot
    return (f'<svg class="hb-g" width="{GAUGE_W}" height="{GAUGE_H}" viewBox="0 0 {GAUGE_W} {GAUGE_H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{html.escape(label, quote=True)}">{judul_tip}'
            f'<path d="M {x0:.2f} {cy:.2f} A {r} {r} 0 0 0 {x1:.2f} {cy:.2f}" fill="none" stroke="{T.PUTIH}" stroke-opacity=".3" stroke-width="7" stroke-linecap="round"/>{busur_nilai}'
            f'<g class="mk" style="transform-origin:{cx}px {cy}px;transform:rotate({-180 * p:.2f}deg)"><circle cx="{x0:.2f}" cy="{cy:.2f}" r="8" fill="{T.PUTIH}" stroke="var(--mustard)" stroke-width="3.5"/></g>'
            f'<svg x="{cx - 14}" y="{cy + 18}" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{T.PUTIH}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{IKON.get(ikon, IKON["pin"])}</svg>'
            f'{teks}</svg>')


# --- CSS ---------------------------------------------------------------------------------------------------------
CSS = """
/* ---------- Header kuning tunggal (semua halaman): judul kiri, pertanyaan + gauge di tengah (gauge sepusat dengan lengkungan bawah), KPI kanan ---------- */
.hbw{container-type:inline-size;margin:.5rem -1.7rem 1.1rem;position:relative;}
.hbw.ruang .hb{margin-bottom:8.5rem;}                   /* ruang untuk lengkungan (133 px) + jarak; di .hb agar bisa diatur ulang oleh @container (yang hanya berlaku untuk turunan .hbw) */
.hb{--bg:__HB_BG__;position:relative;height:200px;padding:0 2.6rem;display:grid;grid-template-columns:minmax(0,1fr) 300px minmax(0,1fr);
  align-items:center;background:var(--bg);border-radius:38px 38px 44px 44px;color:__PUTIH__;font-family:'Inter',sans-serif;}
.hb-l{justify-self:start;align-self:center;min-width:0;}
/* lebar kolom judul = 50cqw − 150px − padding; baris terpanjang ±24 huruf Inter 800 ≈ 13,4 em → huruf menyesuaikan agar tidak terpotong */
.hb-l h1{font-family:'Inter',sans-serif;font-weight:800;margin:0;padding:0;color:__PUTIH__;line-height:1.12;letter-spacing:-.02em;white-space:nowrap;
  font-size:clamp(18px,calc((50cqw - 150px - 2.6rem - 16px) / 13.4),40px);text-shadow:0 2px 10px __BAYANG_JUDUL__;}
.hb-m{position:relative;z-index:2;width:300px;height:100%;text-align:center;text-shadow:0 1px 5px __BAYANG_TENGAH__;}
.hb-t{position:absolute;left:50%;transform:translateX(-50%);bottom:30px;width:max-content;max-width:300px;font-size:15px;font-weight:700;line-height:1.25;white-space:normal;text-wrap:balance;}
/* pusat busur (y = GAUGE_CY di dalam SVG) diletakkan 1 px di atas tepi bawah header = pusat lengkungan */
.hb-g{position:absolute;left:50%;top:calc(100% - 15px);transform:translateX(-50%);display:block;overflow:visible;}
.hb-g text{text-shadow:none;}
.hb-g .va{stroke-dasharray:100;}   /* animasi busur & titik: app/motion.py (hanya saat halaman dibuka) */
.hb-r{justify-self:end;max-width:100%;display:flex;align-items:center;gap:.9rem;text-align:left;}
.hb-r .ic{width:52px;height:52px;border-radius:50%;background:__IKON_KPI_BG__;display:flex;align-items:center;justify-content:center;flex:0 0 52px;}
.hb-r small{display:block;font-size:.62rem;letter-spacing:.1em;font-weight:600;text-transform:uppercase;line-height:1.35;}
.hb-r small .nw{white-space:nowrap;}
.hb-r b{display:block;font-size:2.05rem;font-weight:500;line-height:1.1;letter-spacing:-.01em;}
.hb-r b em{font-style:normal;font-size:.9rem;font-weight:500;margin-left:.3rem;}
.hb-r .tip::after{left:auto;right:-6px;transform:none;}
/* lapisan gelombang sutra BLUSH (SVG ringan); jalurnya menghindari blok KPI & pertanyaan agar kontras teks ≥ 4,5:1 */
.hb::before{content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;background:__SUTRA__ center/100% 100% no-repeat;}
.hb-l,.hb-r{position:relative;z-index:1;}
/* lengkungan: setengah lingkaran berjari-jari 132 px (LOBE_R), pusat di tepi bawah header (top − 1 px agar tanpa celah) */
.hb-lobe{position:absolute;left:50%;transform:translateX(-50%);top:calc(100% - 1px);width:264px;height:133px;border-radius:0 0 50% 50% / 0 0 100% 100%;pointer-events:none;
  background:var(--bg);background-size:100cqw 100%;background-position:calc(132px - 50cqw) 0;background-repeat:no-repeat;}
@container (max-width: 880px){
  .hb{height:auto;grid-template-columns:1fr;justify-items:center;row-gap:1.1rem;padding:1.8rem 1.4rem 2rem;text-align:center;}
  .hbw.ruang .hb{margin-bottom:0;}
  .hb-l,.hb-r{justify-self:center;}
  .hb-l h1{font-size:clamp(24px,7cqw,38px);white-space:normal;text-align:center;}
  .hb-m{width:100%;height:auto;display:flex;flex-direction:column;align-items:center;}
  .hb-t{position:static;transform:none;white-space:normal;max-width:100%;}
  .hb-g{position:static;transform:none;margin:.6rem 0 .3rem;}
  .hb-lobe{display:none;}
  .hb-r{flex-direction:column;text-align:center;gap:.5rem;}
}

"""


def _svg_uri(isi: str) -> str:
    svg = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 200' preserveAspectRatio='none'>{isi}</svg>"
    return "url(\"data:image/svg+xml;utf8," + svg.replace("#", "%23").replace('"', "'") + "\")"


_SUTRA = _svg_uri(
    f"<path d='M-20,92 C150,40 300,160 470,202 S800,212 1020,182' fill='none' stroke='{T.BLUSH}' stroke-opacity='.10' stroke-width='46'/>"
    f"<path d='M-20,74 C150,22 300,142 470,186 S800,196 1020,166' fill='none' stroke='{T.BLUSH}' stroke-opacity='.24' stroke-width='1.4'/>"
    f"<path d='M-20,112 C150,62 300,180 470,220 S800,230 1020,200' fill='none' stroke='{T.BLUSH}' stroke-opacity='.18' stroke-width='1.2'/>"
    f"<path d='M-20,28 C200,-2 360,64 620,22' fill='none' stroke='{T.BLUSH}' stroke-opacity='.07' stroke-width='30'/>")
# gradasi CRIMSON_DARK (kiri) → ROSE_DEEP → PINK hanya di tepi paling kanan (dalam padding header; putih di atas PINK hanya 2,8:1, jadi area KPI
# tetap ROSE_DEEP), cahaya PINK di pojok kanan atas, dan nuansa SAGE sangat tipis di sudut kanan bawah (di bawah angka KPI)
_HB_BG = (f"radial-gradient(240px 62px at 100% 0%,{T.rgba(T.HEADER_KANAN, .95)} 0%,{T.rgba(T.HEADER_KANAN, 0)} 100%),"
          f"radial-gradient(220px 70px at 100% 100%,{T.rgba(T.SAGE, .35)} 0%,{T.rgba(T.SAGE, 0)} 100%),"
          f"linear-gradient(90deg,{T.HEADER_KIRI} 0%,{T.HEADER_TENGAH} 55%,{T.HEADER_TENGAH} 96%,{T.HEADER_KANAN} 100%)")
for _k, _v in {"__HB_BG__": _HB_BG, "__PUTIH__": T.PUTIH, "__BAYANG_JUDUL__": T.rgba(T.CRIMSON_DARK, .35), "__BAYANG_TENGAH__": T.rgba(T.CRIMSON_DARK, .45),
               "__IKON_KPI_BG__": T.rgba(T.PUTIH, .22), "__SUTRA__": _SUTRA}.items():
    CSS = CSS.replace(_k, _v)


def inject_css() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# --- komponen ----------------------------------------------------------------------------------------------------
def render_header(judul: str, pertanyaan: str, nilai_utama: str, rasio_gauge: float, keterangan: str, kpi_label: str, kpi_nilai: str, kpi_catatan: str, kpi_ikon: str,
                  ikon_gauge: str = "pin", kpi_tip: str = "", ruang_lobe: bool = True, hal: int | None = None) -> None:
    """Header halaman. `judul` boleh dua baris ("Kondisi Udara\\nTiap Daerah"); `nilai_utama` boleh dua baris (besar + kecil); `rasio_gauge` 0–1.
    `kpi_nilai` berbentuk angka+satuan ("39,4 µg/m³") ditampilkan angka besar + satuan kecil. `ruang_lobe=False` hanya untuk Beranda (kolom di bawahnya mengatur sendiri jaraknya).
    `keterangan` (gauge) dan `kpi_catatan` tidak ditampilkan sebagai teks: keterangan menjadi tooltip gauge, catatan KPI menjadi awal tooltip ikon ⓘ."""
    m = re.match(r"^([\d.,+\-–]+)\s*(\S.{0,13})?$", kpi_nilai.strip())
    if m and re.search(r"\d", m.group(2) or ""):
        m = None                                         # mis. "14 Okt 2026": tampilkan utuh
    nilai_html = f'{html.escape(m.group(1))}<em>{html.escape(m.group(2) or "")}</em>' if m else html.escape(kpi_nilai)
    cu_kpi = f' data-countup="{html.escape(m.group(1))}"' if m and re.search(r"\d", m.group(1)) else ""
    catatan = kpi_catatan.strip()
    isi_tip = " ".join(x for x in ((catatan[:1].upper() + catatan[1:] + ".") if catatan else "", kpi_tip.strip()) if x)
    tip = f'<span class="tip" tabindex="0" data-tip="{html.escape(isi_tip, quote=True)}">ⓘ</span>' if isi_tip else ""
    kepala, _, ekor = kpi_label.rpartition(" ")
    ujung = f'<span class="nw">{html.escape(ekor)}{(" " + tip) if tip else ""}</span>'
    label_html = f"{html.escape(kepala)} {ujung}" if kepala else ujung
    judul_html = "<br>".join(html.escape(b) for b in judul.split("\n"))
    label_aria = f'{pertanyaan} {nilai_utama.replace(chr(10), " ")}' + (f" ({keterangan})" if keterangan else "")
    st.markdown(f"""
<div class="hbw{' ruang' if ruang_lobe else ''}"{f' data-hal="{hal}"' if hal is not None else ''}><div class="hb">
  <div class="hb-l"><h1>{judul_html}</h1></div>
  <div class="hb-m"><div class="hb-t">{html.escape(pertanyaan)}</div>{gauge_svg(rasio_gauge, nilai_utama, ikon_gauge, label_aria, keterangan)}</div>
  <div class="hb-r"><div class="ic">{_ikon(kpi_ikon, 26, warna=T.SAGE)}</div><div><small>{label_html}</small><b{cu_kpi}>{nilai_html}</b></div></div>
  <div class="hb-lobe"></div>
</div></div>""", unsafe_allow_html=True)
