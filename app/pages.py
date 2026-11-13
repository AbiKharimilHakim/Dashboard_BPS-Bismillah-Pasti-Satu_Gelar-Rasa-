"""Delapan halaman dashboard. Navigasi di sidebar; sub-bagian di tab atas berbentuk pil.

Semua teks ditulis untuk pembaca awam (istilah dari app/glossary.py, narasi dari app/teks.py). Isi analisis mengikuti notebook 04–05;
angka berasal dari tabel data/processed/ dan reports/key_numbers.json. Kode lokasi tidak ditampilkan di halaman mana pun
kecuali pada halaman yang diarsipkan (app_archive/).
"""
from __future__ import annotations

import html

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import config as cfg, eda, models as M, style
from src.clean import kategori_ispu_pm25

from . import echarts as ec, glossary as G, header, nav, peta, teks, theme as T, ui
from .data import NAMA_KASUS, POLUTAN, STANDAR, jam_agregat, statistik_kotak

TIPE = cfg.URUTAN_KELOMPOK            # nama internal jenis wilayah (untuk warna & ikon)
WARNA = T.JENIS                       # warna jenis wilayah (app/theme.py)
JN = G.JENIS                          # nama internal → nama untuk pembaca
NM = G.PENDEK
fl, rp = G.fl, G.rp
BATAS_ISPU = [("Baik", "sampai 15,5"), ("Sedang", "15,5–55,4"), ("Tidak Sehat", "55,5–150,4"), ("Sangat Tidak Sehat", "150,5–250,4"), ("Berbahaya", "di atas 250,4")]


# =========================================================================== #
# alat bantu
# =========================================================================== #
def _kat(x: float) -> str:
    return str(kategori_ispu_pm25(pd.Series([x])).iloc[0]) if pd.notna(x) else "–"


def _kosong() -> None:
    ui.catatan(G.PESAN_KOSONG)


def _kosong_pm(d: pd.DataFrame) -> bool:
    if d.empty or d.pm25_ug_m3.notna().sum() == 0:
        _kosong()
        return True
    return False


JUDUL_HEADER = {
    0: ("Analisis Kualitas Udara\n& Kesehatan di Indonesia", "Bagaimana kualitas udara Indonesia saat ini?", "udara"),
    1: ("Kondisi Udara\nTiap Daerah", "Seberapa tercemar udara di tiap daerah?", "batang"),
    2: ("Waktu Rawan\nPolusi", "Kapan udara paling berbahaya?", "jam"),
    3: ("Penyebab Naiknya\nPolusi", "Apa yang membuat polusi naik?", "penyetel"),
    4: ("Dampak Polusi\npada Kesehatan", "Siapa yang paling terdampak?", "hati"),
    5: ("Sebaran Lokasi\nPengukuran", "Daerah mana yang belum diukur kualitas udaranya?", "pin"),
}


def _lencana(latar: str) -> str:
    """Gaya inline lencana/avatar berwarna: latar + warna teks yang kontras ≥ 4,5:1 (ROSE → ROSE_AKTIF bila berteks putih)."""
    tx = T.teks_di_atas(latar)
    return f"background:{T.latar_teks_putih(latar) if tx == T.PUTIH else latar};color:{tx}"


def _header(i: int, nilai: str, rasio: float, keterangan: str, kpi_label: str, kpi_nilai: str, kpi_catatan: str, kpi_ikon: str, kpi_tip: str = "") -> None:
    """Header halaman ke-i lewat satu komponen yang sama (app/header.py). Angka dihitung dari data terfilter oleh pemanggil."""
    judul, tanya, ikon = JUDUL_HEADER[i]
    header.render_header(judul, tanya, nilai, rasio, keterangan, kpi_label, kpi_nilai, kpi_catatan, kpi_ikon, ikon_gauge=ikon, kpi_tip=kpi_tip, ruang_lobe=i != 0, hal=i)


def _header_kosong(i: int, kpi_label: str, kpi_ikon: str) -> None:
    _header(i, "–", 0.0, "belum ada data untuk pilihan ini", kpi_label, "–", "coba pilih daerah atau periode lain", kpi_ikon)


def _posisi_kategori(x: float) -> float:
    """Posisi 0–1 sebuah konsentrasi PM2.5 pada skala lima kategori udara (tiap kategori = seperlima busur; Berbahaya dihitung sampai 500 µg/m³ sesuai tabel ISPU di src/config.py)."""
    b = cfg.ISPU_PM25_KONSENTRASI
    x = float(max(x, 0.0))
    for k in range(len(b) - 1):
        if x <= b[k + 1] or k == len(b) - 2:
            return (k + min(1.0, (x - b[k]) / (b[k + 1] - b[k]))) / (len(b) - 1)
    return 1.0


# ---- isi header tiap halaman: semua angka dihitung dari data terfilter (C.dat) atau dari tabel hasil analisis (reports/key_numbers.json) ----
def _header_kondisi(C) -> None:
    d = C.dat.daily; kol = C.kol; nm = G.POL_PENDEK[C.pol]
    dv = d[d[kol].notna()]
    if dv.empty:
        return _header_kosong(1, "Daerah paling tercemar", "pin")
    stdv = STANDAR[C.f["standar"]].get(C.pol); bn = G.BATAS_NAMA[C.f["standar"]]
    g = dv.groupby("kode_stasiun")[kol].mean(); top = g.idxmax()
    kpi = dict(kpi_label="Daerah paling tercemar", kpi_nilai=f"{fl(g.max())} µg/m³", kpi_catatan=f"{NM[top]} · rata-rata {nm}", kpi_ikon="pin", kpi_tip=G.TIPS["pm25"] if C.pol == "pm25" else G.TIPS["gas"])
    if stdv:
        n_atas = int((g > stdv).sum())
        _header(1, f"{n_atas} dari {len(g)}\nlokasi", n_atas / len(g), f"rata-rata polusinya di atas {G.kecil(bn)}", **kpi)
    else:
        _header(1, "Belum ada\nbatas harian", 0.0, f"{nm} tidak punya batas aman harian", **kpi)


def _header_waktu(C, prof, hm) -> None:
    kol = C.kol; nm = G.POL_PENDEK[C.pol]
    ep = episode_tabel(C.dat.daily)
    kpi = dict(kpi_label="Kejadian kabut asap", kpi_nilai=str(len(ep)),
               kpi_catatan=f"total {int(ep.hari.sum()) if len(ep) else 0} hari" + (f" · tertinggi {fl(ep.puncak_harian.max(), 0)} µg/m³" if len(ep) else ""), kpi_ikon="api", kpi_tip=G.TIPS["kabut_asap"])
    if prof.empty or hm.empty or hm[kol].notna().sum() == 0:
        return _header(2, "–", 0.0, "belum ada data untuk pilihan ini", **kpi)
    mb = hm.groupby("bulan")[kol].mean(); jam = int(prof.groupby("jam_lokal")[kol].median().idxmax())
    stdv = STANDAR[C.f["standar"]].get(C.pol)
    # panjang busur: rata-rata bulan terburuk ÷ batas aman harian (penuh = sudah melewati batas); zat tanpa batas harian: 1 − bulan terbersih ÷ terburuk
    rasio = min(1.0, mb.max() / stdv) if stdv else (1 - mb.min() / mb.max() if mb.max() > 0 else 0.0)
    _header(2, f"{G.BULAN_PANJANG[int(mb.idxmax()) - 1]} · {jam:02d}:00", rasio, f"rata-rata {nm} {fl(mb.max())} µg/m³ di bulan terburuk", **kpi)


def _header_penyebab(C) -> None:
    d = C.dat.daily; kol = C.kol; nm = G.POL_PENDEK[C.pol]
    kand = {}                                                      # faktor → kekuatan hubungan (rho Spearman) dengan zat pencemar terpilih
    cu = list(G.CUACA_NAMA)
    x = d[["kode_stasiun", kol] + cu].dropna(subset=[kol]).copy()
    if len(x) >= 30:
        x[[kol] + cu] = x.groupby("kode_stasiun")[[kol] + cu].transform(lambda s: s - s.mean())
        cm = x[[kol] + cu].corr(method="spearman")[kol]
        kand.update({G.CUACA_NAMA[c]: float(cm[c]) for c in cu if pd.notna(cm[c])})
    _, _, med = jam_agregat(C.D, C.dat, kol)
    m = med.join(C.D.sites.set_index("kode_stasiun")[["traffic_intensity_per_h", "distance_to_road_m"]]).dropna(subset=[kol])
    if len(m) >= 5:
        kand["Lalu lintas"] = float(eda.spearman(m.traffic_intensity_per_h, m[kol])["rho"])
        kand["Jarak ke jalan"] = float(eda.spearman(m.distance_to_road_m, m[kol])["rho"])
    tm = d[d[kol].notna()].groupby("tipe")[kol].mean()
    kpi = (dict(kpi_label="Jenis wilayah paling tercemar", kpi_nilai=f"{fl(tm.max())} µg/m³", kpi_catatan=f"{JN[tm.idxmax()]} · rata-rata {nm}", kpi_ikon="lapisan", kpi_tip=G.TIPS["jenis"])
           if len(tm) else dict(kpi_label="Jenis wilayah paling tercemar", kpi_nilai="–", kpi_catatan="belum ada data untuk pilihan ini", kpi_ikon="lapisan", kpi_tip=G.TIPS["jenis"]))
    kand = {k: v for k, v in kand.items() if pd.notna(v)}
    if not kand:
        return _header(3, "–", 0.0, "belum ada data untuk pilihan ini", **kpi)
    faktor = max(kand, key=lambda k: abs(kand[k]))
    _header(3, faktor, abs(kand[faktor]), f"hubungan {G.kekuatan(kand[faktor])} dengan {nm} · bukan sebab-akibat", **kpi)


def _header_kesehatan(C, K2) -> None:
    cum = K2["rr_kumulatif"]; ub = cum[NAMA_KASUS["resp_admissions_under5"]]
    n_naik = sum(1 for v in cum.values() if v["bawah"] > 1)         # penyakit yang pasiennya naik nyata (batas bawah rentang kepastian > 1)
    h = C.dat.health
    bal, lan = (int(h[c].sum()) for c in ("resp_admissions_under5", "resp_admissions_over60")) if len(h) else (0, 0)
    kpi = dict(kpi_label="Pasien ISPA balita + lansia", kpi_nilai=rp(bal + lan) if len(h) else "–", kpi_catatan=f"balita {rp(bal)} · lansia {rp(lan)}" if len(h) else "belum ada data untuk pilihan ini",
               kpi_ikon="stetoskop", kpi_tip=G.TIPS["ispa"])
    _header(4, f"{n_naik} dari {len(cum)}\npenyakit", n_naik / len(cum), f"+{fl(100 * (ub['rr'] - 1), 1)}% pasien ISPA balita tiap debu halus naik 10 µg/m³", **kpi)


def _header_lokasi(C, stat) -> None:
    semua = peta.nama_provinsi(); tanpa = peta.provinsi_tanpa_alat(C.D.sites)
    n_dengan = len(semua) - len(tanpa)
    n_stt = C.D.sites[C.D.sites.kode_stasiun.isin(C.dat.stas)].kode_stasiun.map(stat).value_counts()
    _header(5, f"{n_dengan} dari {len(semua)}\nprovinsi", n_dengan / len(semua), "provinsi sudah memiliki alat pengukur", "Lokasi dengan data lengkap", f"{int(n_stt.get('Layak', 0))}",
            f"dari {int(n_stt.sum())} lokasi terpilih", "centang", kpi_tip=G.TIPS["lengkap"])


def _tabel(df: pd.DataFrame, fmt: dict | None = None, tinggi: int | None = None) -> None:
    """Tabel dengan angka berformat Indonesia (koma desimal, titik ribuan); pengurutan tetap memakai nilai asli."""
    fmt = fmt or {}
    def _f(v, n):
        try:
            return "–" if pd.isna(v) else (rp(v) if n == 0 else fl(v, n))
        except (TypeError, ValueError):
            return str(v)
    sty = df.reset_index(drop=True).style.format({c: (lambda v, n=n: _f(v, n)) for c, n in fmt.items()}, na_rep="–")
    st.dataframe(sty, width="stretch", hide_index=True, height=tinggi or min(430, 36 * (len(df) + 1) + 4))


def _bulanan(d: pd.DataFrame, kol: str, by: str | None = None) -> pd.DataFrame:
    x = d[d[kol].notna()].assign(ym=lambda t: t.tanggal.dt.to_period("M").dt.to_timestamp())
    if by:
        return x.groupby(["ym", by])[kol].mean().reset_index()
    return x.groupby("ym")[kol].mean().reset_index()


def episode_tabel(d: pd.DataFrame) -> pd.DataFrame:
    e = d[d.episode & d.pm25_ug_m3.notna()]
    if e.empty:
        return pd.DataFrame(columns=["episode", "stasiun", "tipe", "mulai", "selesai", "hari", "puncak_harian"])
    g = e.groupby("id_episode").agg(stasiun=("kode_stasiun", "first"), tipe=("tipe", "first"), mulai=("tanggal", "min"), selesai=("tanggal", "max"), hari=("tanggal", "size"), puncak_harian=("pm25_ug_m3", "max")).reset_index()
    return g.rename(columns={"id_episode": "episode"}).sort_values("mulai", ascending=False).reset_index(drop=True)


def _legenda_jenis() -> None:
    st.markdown('<div class="chips">' + "".join(f'<span class="chip-s"><i class="sq" style="background:{T.rgba(WARNA[t], T.OPASITAS_BATANG)}"></i>{JN[t]}</span>' for t in TIPE) + "</div>", unsafe_allow_html=True)


def _detail_lokasi(C, g: pd.DataFrame, dv: pd.DataFrame, kode: str, kol: str, nm: str, stdv, eksplisit: bool) -> None:
    """Kartu rincian lokasi yang diklik pada grafik peringkat; nilai berasal dari tabel yang sama dengan grafik dan tabel di sebelahnya."""
    s = C.D.sites.set_index("kode_stasiun").loc[kode]; r = g.loc[kode]
    qc = C.D.qc.set_index("kode_stasiun").status_analisis.get(kode, "–")
    rk = {x["kode_stasiun"]: x for x in C.D.kn["insight"]["5_risiko"]["peringkat"]}.get(kode)
    ui.judul_kartu("Rincian lokasi", "Dipilih dari grafik" if eksplisit else "Peringkat 1 · klik batang pada grafik untuk mengganti")
    kv = [(f"Rata-rata {nm}", f"{fl(r.rata2)} µg/m³"), ("Nilai tengah", f"{fl(r['median'])} µg/m³"), ("95% hari di bawah", f"{fl(r.p95)} µg/m³"), ("Hari terburuk", f"{fl(r.maks)} µg/m³"),
          ("Catatan harian yang bisa dipakai", f"{rp(int(r.n_hari))} hari")]
    if stdv:
        kv.append((f"Hari di atas {fl(stdv, 0)} µg/m³", f"{fl(100 * (dv[dv.kode_stasiun == kode][kol] > stdv).mean())}%"))
    if C.pol == "pm25":
        kv.append(("Kategori udara (rata-rata)", _kat(r.rata2)))
    kv += [("Kelengkapan data", G.STATUS_DATA.get(str(qc), str(qc))), ("Skor risiko", f"{fl(rk['skor'], 0)} (peringkat {rk['peringkat']})" if rk else "tidak dinilai")]
    st.markdown(f'<div class="dh"><span class="lg" style="{_lencana(WARNA[r.tipe])}">{html.escape(NM[kode][:2])}</span><div><b>{html.escape(NM[kode])}</b><span>{html.escape(str(s.provinsi))} · {JN[r.tipe]}</span></div></div>'
                + "".join(f'<div class="kv"><span>{html.escape(a)}</span><b>{html.escape(b)}</b></div>' for a, b in kv), unsafe_allow_html=True)


def _rs(i: str) -> str:
    s = G.RS_DARI_KODE.get(i, i)
    return s[:1].upper() + s[1:]


def _kasus(k: str) -> str:
    return G.KASUS_NAMA.get(k, k)


# =========================================================================== #
# 0 — BERANDA
# =========================================================================== #
def p0(C) -> None:
    _p0_ringkasan(C)


def _toggle_jenis(t: str) -> None:
    st.session_state["p0_jenis"] = None if st.session_state.get("p0_jenis") == t else t


def _buka_halaman(t: str, slug: str) -> None:
    """Callback tombol tautan: atur filter jenis wilayah (sebelum widget filter dibuat pada eksekusi berikutnya), lalu pindah halaman."""
    st.session_state["f_jenis"] = [JN[t]]
    st.session_state["_pindah"] = slug


def _warna_teks_badge(kat: str) -> str:
    return T.teks_di_atas(T.ISPU[kat])


def _p0_ubin(C, d: pd.DataFrame, std: float, bn: str) -> None:
    """Lima ubin jenis wilayah yang bisa diklik; klik membuka panel daftar lokasi tepat di bawahnya (klik lagi = tutup)."""
    pilih = st.session_state.get("p0_jenis")
    st.markdown('<div class="ubin-judul">Jenis wilayah</div>', unsafe_allow_html=True)
    with st.container(key="ubin_grid"):
        for i, t in enumerate(TIPE):
            x = d[d.tipe == t]
            n = x.kode_stasiun.nunique()
            v = fl(x.pm25_ug_m3.mean()) if n and x.pm25_ug_m3.notna().any() else "–"
            with st.container(key=f"ubin_t{i}"):
                st.markdown(f'<div class="ubin-in{" sel" if pilih == t else ""}">{ui.ikon(t.lower(), 28)}<div class="t">{JN[t]}</div><div class="v">{n} lokasi</div><div class="v">{v} µg/m³</div><div class="chev">⌄</div></div>', unsafe_allow_html=True)
                st.button(f"{'Tutup' if pilih == t else 'Lihat'} daftar lokasi {JN[t]}", key=f"ubin_btn_{i}", on_click=_toggle_jenis, args=(t,))
    if not pilih:
        ui.keterangan("Klik salah satu jenis wilayah untuk melihat lokasinya.")
        return
    i = TIPE.index(pilih)
    sites = C.D.sites.set_index("kode_stasiun")
    status = C.D.qc.set_index("kode_stasiun").status_analisis
    x = d[d.tipe == pilih]
    rata = x.groupby("kode_stasiun").pm25_ug_m3.mean()
    urut = rata.sort_values(ascending=False, na_position="last").index
    with st.container(key=f"ubin_panel_{i}"):
        st.markdown(f'<div class="pnl-h"><b>{JN[pilih]} · {len(urut)} lokasi</b><span>{html.escape(G.JENIS_ARTI[pilih])}</span></div>', unsafe_allow_html=True)
        if len(urut) == 0:
            ui.catatan(G.PESAN_KOSONG)
        else:
            skala = max(float(np.nanmax(rata.values)) if rata.notna().any() else 0.0, std) * 1.12
            baris = []
            for k in urut:
                m = rata.get(k)
                batas = f'<u style="left:{100 * std / skala:.1f}%" title="{html.escape(bn)} ({fl(std, 0)} µg/m³)"></u>'
                lbl = "" if str(status.get(k, "Layak")) == "Layak" else '<span class="ltd">data terbatas</span>'
                if pd.isna(m):
                    baris.append(f'<div class="lok-row"><div class="lok-top"><div class="lok-nm"><b>{html.escape(G.TAMPIL[k])}</b>{lbl}</div><div class="lok-v">tidak ada data pada periode ini</div></div><div class="lok-bar">{batas}</div></div>')
                    continue
                kat = _kat(m); wrn = T.ISPU[kat]
                baris.append(f'<div class="lok-row"><div class="lok-top"><div class="lok-nm"><b>{html.escape(G.TAMPIL[k])}</b>{lbl}</div>'
                             f'<div class="lok-v"><b>{fl(m)}</b> µg/m³ <span class="bdg" style="{_lencana(wrn)}">{kat}</span></div></div>'
                             f'<div class="lok-bar"><i style="width:{min(100.0, 100 * m / skala):.1f}%;background:{wrn}"></i>{batas}</div></div>')
            st.markdown("".join(baris), unsafe_allow_html=True)
            ui.keterangan(f"Rata-rata debu halus (PM2.5) per lokasi pada periode terpilih. Garis tipis = {G.kecil(bn)} ({fl(std, 0)} µg/m³).")
        with st.container(key="lnk_baris"):                                      # satu baris: kiri & kanan; bertumpuk rata kiri bila sempit (ui.py)
            st.button("Lihat di peta", key="p0_lnk_peta", type="tertiary", icon=":material/map:", on_click=_buka_halaman, args=(pilih, "lokasi-pengukuran"))
            st.button("Bandingkan di Kondisi Udara →", key="p0_lnk_kondisi", type="tertiary", on_click=_buka_halaman, args=(pilih, "kondisi-udara"))



def _p0_ringkasan(C) -> None:
    d = C.dat.daily
    tujuan = st.session_state.pop("_pindah", None)
    if tujuan:
        st.switch_page(nav.REG[tujuan])
    if d.empty or d.pm25_ug_m3.notna().sum() == 0:
        _header_kosong(0, "Rata-rata debu halus (PM2.5)", "debu")
        return _kosong()
    pm = d.pm25_ug_m3.dropna()
    std = STANDAR[C.f["standar"]]["pm25"]; bn = G.BATAS_NAMA[C.f["standar"]]
    pct = 100 * (pm > std).mean()
    D = C.D
    _header(0, _kat(pm.mean()), _posisi_kategori(pm.mean()), f"{fl(pct)}% hari di atas {G.kecil(bn)}", "Rata-rata debu halus (PM2.5)", f"{fl(pm.mean())} µg/m³",
            f"{len(C.dat.stas)} lokasi · {rp(len(pm))} catatan harian", "debu", kpi_tip=G.TIPS["pm25"])
    kiri, tengah, kanan = st.columns([1, 1.25, 1.05], gap="medium")

    with kiri:
        mst = d.groupby("kode_stasiun").pm25_ug_m3.agg(["mean", "count"])
        mst = mst[mst["count"] >= 30] if (mst["count"] >= 30).any() else mst
        top = mst["mean"].idxmax(); s = C.D.sites.set_index("kode_stasiun").loc[top]
        st.markdown(f"""<div class="card-teal"><div class="lbl">Paling tercemar</div><div class="num">{html.escape(NM[top])}</div>
<div class="meta"><span>{html.escape(str(s.provinsi))}</span><span>{JN[s.kelompok_lokasi]}</span></div>
<div class="meta" style="margin-top:.3rem"><span>Rata-rata: {fl(mst.loc[top, 'mean'])} µg/m³</span><span>Alat: {G.STATUS_ALAT.get(str(s.status_sensor), 'Bermasalah').lower()}</span></div>
</div>""", unsafe_allow_html=True)
        ep = episode_tabel(d)
        with st.container(key="asap_link"):
            st.page_link(nav.REG["waktu-rawan"], label=f"**{len(ep)}** kejadian kabut asap di lokasi terpilih", icon=":material/local_fire_department:")
        with ui.kartu("p0_tipe"):
            _p0_ubin(C, d, std, bn)

    with tengah:
        st.markdown('<div style="height:132px"></div>', unsafe_allow_html=True)      # ruang di bawah lengkungan header (setengah lingkaran 133 px)
        with ui.kartu("p0_tren"):
            b = _bulanan(d, "pm25_ug_m3")
            pk = b.loc[b.pm25_ug_m3.idxmax()]
            ui.judul_kartu(f"Debu halus paling tinggi pada {G.bln(pk.ym)}: {fl(pk.pm25_ug_m3)} µg/m³", f"Rata-rata bulanan di lokasi terpilih (µg/m³). Garis putus-putus = {G.kecil(bn)} ({fl(std, 0)})", tip=G.TIPS["pm25"])
            ec.tampil(ec.garis([G.bln(t) for t in b.ym], [dict(name="Debu halus (PM2.5)", data=b.pm25_ug_m3.round(2), color=T.SERI, area=True)], satuan="µg/m³", judul_y="µg/m³",
                               ambang=(std, f"{bn} ({fl(std, 0)})", T.BATAS[C.f["standar"]]), tinggi=250), "p0_tren", 250, klik=False)
            bk = b.assign(k=b.ym.dt.month.isin(cfg.MUSIM_KEMARAU_BULAN))
            if bk[bk.k].pm25_ug_m3.mean() > bk[~bk.k].pm25_ug_m3.mean():
                ui.keterangan("Polusi cenderung naik pada musim kemarau (Mei–Oktober), saat lahan kering mudah terbakar. <b>Warga perlu lebih waspada pada bulan-bulan itu.</b>")
        with ui.kartu("p0_epi"):
            ui.judul_kartu("Kabut asap terbaru", "Polusi di atas 150 µg/m³ selama minimal 3 hari berturut-turut", tip=G.TIPS["kabut_asap"])
            if ep.empty:
                ui.keterangan("Tidak ada kejadian kabut asap pada pilihan ini.")
            for r in ep.head(3).itertuples():
                ic = ui.ikon("keluar", 18, T.ROSE_DEEP)
                st.markdown(f'<div class="row-mint"><div class="ico">{ic}</div><div class="tt">{G.tgl(r.mulai)} – {G.tgl(r.selesai)}<br><b>{html.escape(NM[r.stasiun])} · {r.hari} hari</b></div>'
                            f'<div class="vv neg" data-countup="{fl(r.puncak_harian, 0)}">{fl(r.puncak_harian, 0)} µg/m³<small style="display:block;font-weight:500;font-size:.62rem;color:{T.TEKS2}">tertinggi</small></div></div>', unsafe_allow_html=True)

    with kanan:
        sem = C.D.daily[C.f["versi"]]
        sem = sem[(sem.tanggal >= C.dat.tgl[0]) & (sem.tanggal <= C.dat.tgl[1])]
        with ui.kartu("p0_radar"):
            kk = [f"{p}_ug_m3" for p in POLUTAN]
            # indeks relatif: rata-rata lokasi terpilih ÷ rata-rata lokasi tertinggi (seluruh lokasi, periode & versi data sama)
            puncak = [sem.groupby("kode_stasiun")[k].mean().max() for k in kk]
            rel = [d[k].mean() / pk_ if pd.notna(pk_) and pk_ > 0 and d[k].notna().any() else 0.0 for k, pk_ in zip(kk, puncak)]
            nm_ = [G.POL_PENDEK[p] for p in POLUTAN]
            ui.judul_kartu(f"{nm_[int(np.argmax(rel))]} paling menonjol di lokasi terpilih", "Makin ke tepi, makin dekat ke lokasi terburuk (tepi = 100%)", tip=G.TIPS["gas"])
            ec.tampil(ec.radar(nm_, rel, warna_isi=T.RADAR_ISI, warna_garis=T.RADAR_GARIS, tinggi=250), "p0_radar", 250, klik=False)
        with ui.kartu("p0_top"):
            ui.judul_kartu("Daerah paling berisiko", "Skor 0–100: gabungan polusi, beban kesehatan, kerentanan, dan tren", tip=G.TIPS["skor_risiko"])
            rk = pd.DataFrame(C.D.kn["insight"]["5_risiko"]["peringkat"]); rk = rk[rk.kode_stasiun.isin(C.dat.stas)].head(3)
            if rk.empty:
                ui.keterangan("Tidak ada daerah yang dinilai pada pilihan ini.")
            for r in rk.itertuples():
                ser = _bulanan(d[d.kode_stasiun == r.kode_stasiun], "pm25_ug_m3").pm25_ug_m3.to_numpy()
                prov = C.D.sites.set_index("kode_stasiun").loc[r.kode_stasiun, "provinsi"]
                st.markdown(f'<div class="gainer"><div class="lg" style="{_lencana(WARNA[r.tipe])}">{html.escape(NM[r.kode_stasiun][:2])}</div><div class="nm"><b>{html.escape(NM[r.kode_stasiun])}</b><span>{html.escape(str(prov))}</span></div>'
                            f'<div class="pr" data-countup="{fl(r.skor, 0)}">{fl(r.skor, 0)}<span>peringkat {r.peringkat}</span></div><div>{ui.sparkline(ser, T.SPARKLINE)}</div></div>', unsafe_allow_html=True)

    with ui.kartu("p0_peta"):
        ui.judul_kartu("Peta Indonesia: di mana udara paling kotor?", f"Satu titik = satu lokasi pengukuran; warna = kategori udara rata-rata (debu halus PM2.5) · arsir merah muda = provinsi tanpa alat", tip=G.TIPS["lokasi"])
        status = C.D.qc.set_index("kode_stasiun").status_analisis
        peta.render_peta(peta.siapkan_titik(C, d, std, bn, status), "beranda", "peta_beranda", C.D.sites)
        ui.keterangan("Klik sebuah titik untuk melihat rincian dan memperbesar peta; ganti ke <b>Peta panas polusi</b> untuk melihat sebaran umum. Warna titik mengikuti rata-rata pada periode dan pilihan filter yang aktif.")


# =========================================================================== #
# 1 — KONDISI UDARA
# =========================================================================== #
def p1(C) -> None:
    _header_kondisi(C)
    t1, t2, t3 = st.tabs(["Peringkat daerah", "Batas aman & kategori udara", "Perubahan dari waktu ke waktu"])
    with t1:
        _p1_peringkat(C)
    with t2:
        _p1_batas(C)
    with t3:
        _p1_tren(C)


def _p1_peringkat(C) -> None:
    d = C.dat.daily; kol = C.kol; nm = G.POL_PENDEK[C.pol]
    dv = d[d[kol].notna()]
    stdv = STANDAR[C.f["standar"]].get(C.pol); bn = G.BATAS_NAMA[C.f["standar"]]
    if dv.empty:
        return _kosong()
    g = dv.groupby("kode_stasiun")[kol].agg(["mean", "median", lambda s: s.quantile(.95), "max", "count"])
    g.columns = ["rata2", "median", "p95", "maks", "n_hari"]
    g["tipe"] = g.index.map(C.D.sites.set_index("kode_stasiun").kelompok_lokasi)
    g = g.sort_values("rata2", ascending=False)
    n_atas = int((g.rata2 > (stdv or np.inf)).sum()) if stdv else 0
    names = [NM[k] for k in g.index]
    cb, cd = st.columns([2.2, 1], gap="medium")
    with cb, ui.kartu("p1_bar"):
        if len(g) > 1:
            judul = f"Udara {names[0]} paling tercemar ({fl(g.rata2.iloc[0])} µg/m³), {names[-1]} paling bersih ({fl(g.rata2.iloc[-1])} µg/m³)"
        else:
            judul = f"Rata-rata {nm} di {names[0]}: {fl(g.rata2.iloc[0])} µg/m³ per hari"
        ui.judul_kartu(judul, f"Rata-rata harian {nm} per lokasi (µg/m³) · klik batang untuk melihat rincian", tip=G.TIPS["pm25"] if C.pol == "pm25" else G.TIPS["gas"])
        _legenda_jenis()
        pilih = ec.terpilih("p1_bar"); pilih = pilih if pilih in names else None
        ec.tampil(ec.batang(names, [dict(name=nm, data=g.rata2.round(2), warna=[T.rgba(WARNA[t], T.OPASITAS_BATANG) for t in g.tipe])], horizontal=True, satuan="µg/m³", desimal=1, label=True, pilih=pilih,
                            judul_nilai=f"{nm} (µg/m³)", garis=(stdv, f"{bn} ({fl(stdv, 0)})", T.BATAS[C.f["standar"]]) if stdv else None), "p1_bar", max(320, 22 * len(g) + 90))
        if stdv:
            ui.keterangan(f"Batang yang melewati garis putus-putus berarti rata-rata polusinya di atas {G.kecil(bn)}. <b>Di daerah itu udara lebih sering tidak aman.</b>")
    with cd, ui.kartu("p1_detail"):
        sel = ec.terpilih("p1_bar")
        sel_kode = G.KODE_DARI_PENDEK[sel] if sel in names else g.index[0]
        _detail_lokasi(C, g, dv, sel_kode, kol, nm, stdv, eksplisit=sel in names)


def _p1_batas(C) -> None:
    d = C.dat.daily; kol = C.kol
    dv = d[d[kol].notna()]
    bn = G.BATAS_NAMA[C.f["standar"]]
    pm = d[d.pm25_ug_m3.notna()]
    if dv.empty or pm.empty:
        return _kosong()
    std25 = STANDAR[C.f["standar"]]["pm25"]
    x = pm.assign(k=kategori_ispu_pm25(pm.pm25_ug_m3).astype(str))
    c1, c2 = st.columns([1, 2], gap="medium")
    with c1, ui.kartu("p1_don"):
        jml = x.k.value_counts().reindex(cfg.ISPU_KATEGORI, fill_value=0)
        pb = 100 * jml["Baik"] / max(jml.sum(), 1)
        ui.judul_kartu(f"Hanya {fl(pb)}% hari udara berkategori Baik" if pb < 50 else f"{fl(pb)}% hari udara berkategori Baik", "Seluruh catatan harian (jumlah hari) · klik irisan untuk menyorot", tip=G.TIPS["kategori"])
        sel_k = ec.terpilih("p1_don")
        ec.tampil(ec.donat([(k, jml[k], T.ISPU[k]) for k in cfg.ISPU_KATEGORI if jml[k] > 0], judul=rp(int(jml.sum())), sub="hari tercatat", satuan="hari", pilih=sel_k), "p1_don", 400)
        for k, rg in BATAS_ISPU:
            st.markdown(f'<div class="row-mint"><div class="ico" style="background:{T.ISPU[k]}"></div><div class="tt"><b>{k}</b> · {rg} µg/m³<br>{G.KATEGORI_ARTI[k]}</div></div>', unsafe_allow_html=True)
    with c2, ui.kartu("p1_ispu"):
        ct = pd.crosstab(x.kode_stasiun, x.k, normalize="index").mul(100).reindex(columns=cfg.ISPU_KATEGORI, fill_value=0)
        buruk = ct[["Tidak Sehat", "Sangat Tidak Sehat", "Berbahaya"]].sum(axis=1)
        if buruk.max() > 0:
            ui.judul_kartu(f"{NM[buruk.idxmax()]} paling sering Tidak Sehat atau lebih buruk ({fl(buruk.max())}% hari)", "Kategori udara di tiap lokasi (% hari)" + (f" · disorot: {sel_k}" if sel_k else ""), tip=G.TIPS["kategori"])
        else:
            ui.judul_kartu("Tidak ada lokasi yang berkategori Tidak Sehat", "Kategori udara di tiap lokasi (% hari)", tip=G.TIPS["kategori"])
        ec.tampil(ec.batang([NM[k] for k in ct.index], [dict(name=k, data=ct[k].round(2), color=T.ISPU[k]) for k in cfg.ISPU_KATEGORI], horizontal=True, tumpuk=True, satuan="% hari", desimal=1,
                            rentang=(0, 100), judul_nilai="% hari", redup_seri=[k for k in cfg.ISPU_KATEGORI if sel_k and k != sel_k]), "p1_ispu", max(340, 24 * len(ct) + 110), klik=False)
        ui.keterangan("Hijau = Baik, biru kehijauan = Sedang, jingga = Tidak Sehat, merah muda = Sangat Tidak Sehat, merah tua = Berbahaya. <b>Makin banyak warna jingga, merah muda, dan merah tua, makin sering udara berbahaya bagi warga.</b>")


def _p1_tren(C) -> None:
    d = C.dat.daily; kol = C.kol; nm = G.POL_PENDEK[C.pol]
    dv = d[d[kol].notna()]
    if dv.empty:
        return _kosong()
    tr = C.D.kn["A"]["tren"]
    b = _bulanan(dv, kol, "tipe")
    with ui.kartu("p1_tren"):
        last = b[b.ym == b.ym.max()]
        top = last.loc[last[kol].idxmax()]
        ui.judul_kartu(f"Pada {G.bln(top.ym)}, polusi tertinggi ada di {JN[top.tipe]} ({fl(top[kol])} µg/m³)", f"Rata-rata {nm} bulanan menurut jenis wilayah (µg/m³)", tip=G.TIPS["jenis"])
        bulan = sorted(b.ym.unique())
        seri = []
        for t in TIPE:
            x = b[b.tipe == t].set_index("ym")[kol].reindex(bulan)
            if x.notna().any():
                seri.append(dict(name=JN[t], data=[None if pd.isna(v) else round(float(v), 2) for v in x], color=WARNA[t]))
        ec.tampil(ec.garis([G.bln(m) for m in bulan], seri, satuan="µg/m³", judul_y="µg/m³", tinggi=320), "p1_tren", 320, klik=False)
        ui.keterangan("Polusi naik tajam menjelang akhir periode, terutama di lahan gambut. <b>Perbedaan antar jenis wilayah jauh lebih besar daripada perubahan antar tahun.</b>")
    _kartu_kotak(C, "p1_box")


# =========================================================================== #
# 2 — WAKTU RAWAN
# =========================================================================== #
def p2(C) -> None:
    """Waktu rawan dalam SATU alur (tanpa tab): peta panas jam × bulan → pola per jam & per bulan → jumlah kejadian kabut asap per bulan & tahun.
    Angka sama dengan versi bertab sebelumnya: jam terburuk = puncak nilai tengah per jam (seperti header), bulan terburuk =
    rata-rata bulanan dari tabel jam × bulan, jumlah kabut asap = episode_tabel()."""
    prof, hm, _ = jam_agregat(C.D, C.dat, C.kol)
    _header_waktu(C, prof, hm)
    if prof.empty or hm.empty or hm[C.kol].notna().sum() == 0:
        return _kosong()
    kol = C.kol; nm = G.POL_PENDEK[C.pol]
    jam = int(prof.groupby("jam_lokal")[kol].median().idxmax())                 # sama dengan header & judul tab "Jam rawan" sebelumnya
    mb = hm.groupby("bulan")[kol].mean()                                        # sama dengan header & tab "Bulan rawan" sebelumnya
    ep = episode_tabel(C.dat.daily)
    asap_bln = ep.mulai.dt.month.value_counts().reindex(range(1, 13), fill_value=0) if len(ep) else pd.Series(0, index=range(1, 13))
    sel_hm = ec.terpilih("p2_hm")                                                # "bulan|jam" dari klik sel peta panas
    sel_b, sel_j = (int(sel_hm.split("|")[0]), int(sel_hm.split("|")[1])) if sel_hm and "|" in str(sel_hm) else (None, None)

    _p2_peta_panas(C, hm, nm, jam, mb, asap_bln, sel_b, sel_j)
    _p2_pendukung(C, prof, nm, asap_bln, sel_b, sel_j)
    _p2_asap(C, ep)


def _rentang_bulan(bulan_list) -> str:
    """[8, 9, 10] → "Agustus–Oktober"; bulan tidak berurutan → "Agustus, Oktober, dan Desember"."""
    b = sorted(int(m) for m in bulan_list)
    if len(b) > 1 and b == list(range(b[0], b[-1] + 1)):
        return f"{G.BULAN_PANJANG[b[0] - 1]}–{G.BULAN_PANJANG[b[-1] - 1]}"
    n = [G.BULAN_PANJANG[m - 1] for m in b]
    return n[0] if len(n) == 1 else (" dan ".join(n) if len(n) == 2 else ", ".join(n[:-1]) + f", dan {n[-1]}")


def _p2_peta_panas(C, hm, nm, jam, mb, asap_bln, sel_b, sel_j) -> None:
    """Peta panas jam × bulan selebar penuh (ECharts); klik sel menyorot jam & bulan itu di dua grafik pendukung."""
    kol = C.kol
    z = hm.pivot(index="jam_lokal", columns="bulan", values=kol).reindex(index=range(24), columns=range(1, 13))
    top3 = mb.sort_values(ascending=False).index[:3]
    with ui.kartu("p2_hm"):
        ui.judul_kartu(f"Udara paling kotor pada {G.bagian_hari(jam)} hari di bulan {_rentang_bulan(top3)}",
                       f"Rata-rata {nm} (µg/m³) menurut jam (waktu setempat) dan bulan · 🔥 = bulan dengan kejadian kabut asap · jam berlabel merah muda = jam sibuk (07–09 & 17–19) · klik sel untuk menyorot grafik di bawah",
                       tip=G.TIPS["kabut_asap"])
        sel = []
        for b in range(1, 13):
            for j in range(24):
                v = z.loc[j, b]
                ada = pd.notna(v)
                kat = f" · {_kat(v)}" if (ada and C.pol == "pm25") else ""
                n_asap = int(asap_bln.get(b, 0))
                tip = (f"<b>Pukul {j:02d}.00 · {G.BULAN_PANJANG[b - 1]}</b><br>{fl(v) if ada else '–'} µg/m³{kat}"
                       + (f"<br>{n_asap} kejadian kabut asap di bulan ini" if n_asap else ""))
                op = 1.0 if (sel_b is None or b == sel_b or j == sel_j) else 0.35        # sel yang diklik: baris & kolomnya tetap terang
                sel.append(dict(x=b - 1, y=j, v=round(float(v), 2) if ada else None, nama=f"{b}|{j}", tip=tip, op=op))
        nil = [s["v"] for s in sel if s["v"] is not None]
        ec.tampil(ec.peta_panas(G.BULAN, [f"{j:02d}:00" for j in range(24)], sel, warna=T.PANAS, teks_skala=(f"{fl(max(nil), 0)} µg/m³", f"{fl(min(nil), 0)}"),
                                label_atas=[f"🔥 {int(asap_bln.get(b, 0))}" if asap_bln.get(b, 0) else None for b in range(1, 13)],
                                pita=[(7, 9, "jam sibuk"), (17, 19, "jam sibuk")], tinggi=500, judul_y="Jam (waktu setempat)"), "p2_hm", 500)
        ui.keterangan(f"Makin merah warnanya, makin tinggi polusi pada jam dan bulan itu. <b>Pada {_rentang_bulan(top3)}, kurangi kegiatan di luar ruangan terutama pada {G.bagian_hari(jam)} hari.</b>")


def _p2_pendukung(C, prof, nm, asap_bln, sel_b, sel_j) -> None:
    """Pola per jam (garis per jenis wilayah) dan pola per bulan (batang, musim kemarau & kabut asap ditandai), berdampingan."""
    d = C.dat.daily; kol = C.kol
    c1, c2 = st.columns(2, gap="medium")
    with c1, ui.kartu("p2_jam"):
        h = int(prof.groupby("jam_lokal")[kol].median().idxmax())
        ui.judul_kartu(f"Polusi {nm} paling tinggi sekitar pukul {h:02d}:00 ({G.bagian_hari(h)} hari)", f"Nilai tengah {nm} tiap jam menurut jenis wilayah (µg/m³); jam dalam waktu setempat (WIB/WITA/WIT)", tip=G.TIPS["nilai_tengah"])
        seri = []
        for t in TIPE:
            x = prof[prof.tipe == t].set_index("jam_lokal")[kol].reindex(range(24))
            if x.notna().any():
                seri.append(dict(name=JN[t], data=[None if pd.isna(v) else round(float(v), 2) for v in x], color=WARNA[t]))
        ec.tampil(ec.garis([f"{j:02d}:00" for j in range(24)], seri, satuan="µg/m³", judul_y="µg/m³ (nilai tengah)", tinggi=340, legenda_lipat=True,
                           garis_x=(f"{sel_j:02d}:00", f"pukul {sel_j:02d}.00") if sel_j is not None else None), "p2_jam", 340, klik=False)
        KT = C.D.kn["B"]["diurnal"]["jam_puncak_no2_median_per_tipe"]
        ui.keterangan(f"Di Pinggir Jalan Raya, gas NO₂ (asap kendaraan) memuncak pukul {fl(KT['Jalan Raya'], 0)}, saat jam pulang kerja. <b>Hindari berolahraga di tepi jalan pada jam sibuk.</b>")
    with c2, ui.kartu("p2_mus"):
        bb = d[d[kol].notna()].groupby("bulan")[kol].mean()
        kem = bb[[m for m in bb.index if m in cfg.MUSIM_KEMARAU_BULAN]].mean(); huj = bb[[m for m in bb.index if m not in cfg.MUSIM_KEMARAU_BULAN]].mean()
        ui.judul_kartu("Musim kemarau (Mei–Oktober) lebih tercemar daripada musim hujan" if kem > huj else "Polusi di musim kemarau tidak lebih tinggi daripada musim hujan", f"Rata-rata {nm} tiap bulan (µg/m³) · 🔥 = jumlah kejadian kabut asap")
        ec.tampil(ec.batang(G.BULAN, [dict(name=nm, data=[bb.get(i, np.nan) for i in range(1, 13)], warna=[T.KEMARAU if i in cfg.MUSIM_KEMARAU_BULAN else T.HUJAN for i in range(1, 13)])],
                            satuan="µg/m³", desimal=1, judul_nilai="µg/m³", tinggi=340, pilih=G.BULAN[sel_b - 1] if sel_b else None,
                            label_item=[f"🔥 {int(asap_bln.get(i, 0))}" if asap_bln.get(i, 0) else None for i in range(1, 13)]), "p2_mus", 340, klik=False)
        ui.keterangan("Batang merah muda = musim kemarau (Mei–Oktober), saat lahan kering mudah terbakar. <b>Kabut asap hampir selalu muncul di bulan-bulan kemarau.</b>"
                      if asap_bln[[m for m in range(1, 13) if m in cfg.MUSIM_KEMARAU_BULAN]].sum() >= asap_bln.sum() * 0.5 and asap_bln.sum()
                      else "Batang merah muda = musim kemarau (Mei–Oktober), saat lahan kering mudah terbakar.")


def _p2_asap(C, ep) -> None:
    """Batang berkelompok: jumlah kejadian kabut asap menurut bulan dimulainya (Agustus–Oktober + bulan lain yang punya kejadian), satu batang per tahun.
    Warna tahun bertingkat PINK_SOFT (tahun terlama) → ROSE → CRIMSON_DARK (tahun terbaru) dari app/theme.py; total batang = jumlah kejadian."""
    if ep.empty:
        return
    with ui.kartu("p2_asap"):
        ep = ep.assign(nama=ep.stasiun.map(NM), bln=ep.mulai.dt.month, thn=ep.mulai.dt.year)
        n_ao = int(ep.bln.isin([8, 9, 10]).sum())
        tahun = sorted(int(y) for y in ep.thn.unique())
        bulan = sorted(set([8, 9, 10]) | set(int(m) for m in ep.bln.unique()))
        akhir = C.dat.tgl[1]
        sub = "Jumlah kejadian menurut bulan dimulainya, satu batang per tahun · makin gelap = makin baru"
        if akhir < pd.Timestamp(tahun[-1], 12, 31):
            sub += f" · data {tahun[-1]} sampai {G.tgl(akhir)}"
        ui.judul_kartu(f"{n_ao} dari {len(ep)} kejadian kabut asap berlangsung pada Agustus–Oktober", sub, tip=G.TIPS["kabut_asap"])
        warna = ui.warna_bertingkat(len(tahun))
        seri = []
        for y, w in zip(tahun, warna):
            data = []
            for m in bulan:
                x = ep[(ep.thn == y) & (ep.bln == m)].sort_values("puncak_harian", ascending=False)
                tip = f"<b>{G.BULAN_PANJANG[m - 1]} {y}</b> · {len(x)} kejadian"
                if len(x):
                    lok = list(dict.fromkeys(x.nama))
                    tip += f" · {html.escape(', '.join(lok[:3]))}{', …' if len(lok) > 3 else ''} · puncak tertinggi {fl(x.puncak_harian.max(), 0)} µg/m³"
                data.append(dict(v=len(x), tip=tip))
            seri.append(dict(name=str(y), color=w, data=data))
        ec.tampil(ec.batang_tahun([G.BULAN_PANJANG[m - 1] for m in bulan], seri, judul_y="Jumlah kejadian", tinggi=340), "p2_asap", 340, klik=False)
        # keterangan 2 kalimat: kapan paling sering & bagaimana jumlahnya per tahun, lalu artinya bagi warga
        bln = ep.bln.value_counts()
        b_top, n_top = int(bln.idxmax()), int(bln.max())
        th = ep.thn.value_counts().sort_index()
        per_tahun = ", ".join(f"{int(n)} pada {int(y)}" for y, n in th.items())
        naik = len(th) >= 2 and bool((th.diff().dropna() > 0).all())
        k1 = (f"Kejadian kabut asap paling sering dimulai pada {G.BULAN_PANJANG[b_top - 1]} ({n_top} dari {len(ep)} kejadian), "
              + (f"dan jumlahnya bertambah setiap tahun: {per_tahun}." if naik else f"dengan jumlah per tahun {per_tahun}."))
        tipe_top = JN[ep.tipe.value_counts().idxmax()].lower()
        k2 = (f"<b>Siapkan masker dan rencana kesehatan sebelum Agustus</b>, terutama bagi warga di sekitar {tipe_top}." if b_top in (8, 9, 10) and n_ao * 2 >= len(ep)
              else f"<b>Siapkan masker dan rencana kesehatan sebelum {G.BULAN_PANJANG[b_top - 1]}</b>, terutama bagi warga di sekitar {tipe_top}.")
        ui.keterangan(f"{k1} {k2}")


# =========================================================================== #
# 3 — PENYEBAB POLUSI
# =========================================================================== #
def p3(C) -> None:
    """Penyebab polusi dalam SATU alur (tanpa tab): pengaruh cuaca → pengaruh lalu lintas & jalan → perbedaan antar jenis wilayah."""
    _header_penyebab(C)
    ui.subjudul("Pengaruh cuaca")
    _p3_cuaca(C)
    ui.subjudul("Pengaruh lalu lintas & jalan")
    _p3_lalu_lintas(C)
    ui.subjudul("Perbedaan antar jenis wilayah")
    _kartu_kotak(C, "p3_box")


def _kartu_kotak(C, kunci: str) -> None:
    """Kartu boxplot sebaran harian per jenis wilayah (dipakai di Kondisi udara dan Penyebab polusi; hanya 5 angka per jenis wilayah yang dikirim ke grafik)."""
    kol = C.kol; nm = G.POL_PENDEK[C.pol]
    stat = statistik_kotak(C.dat.versi, tuple(C.dat.stas), str(C.dat.tgl[0].date()), str(C.dat.tgl[1].date()), kol)
    if not stat:
        return _kosong()
    with ui.kartu(kunci):
        ui.judul_kartu("Rentang polusi harian sangat berbeda antar jenis wilayah", f"Sebaran harian {nm} (µg/m³); skala bertingkat, tiap garis ±3× lipat", tip=G.TIPS["nilai_tengah"])
        ec.tampil(ec.kotak([(JN[t], WARNA[t], stat[t]) for t in TIPE if t in stat], judul_y="µg/m³", tinggi=340), kunci, 340, klik=False)
        ui.keterangan("Kotak = rentang hari-hari yang umum; garis tengah = nilai tengah; garis ke atas = hari terburuk. <b>Lahan gambut punya hari-hari terburuk paling ekstrem.</b>")


def _p3_cuaca(C) -> None:
    d = C.dat.daily
    pol = [f"{p}_ug_m3" for p in POLUTAN]; cu = list(G.CUACA_NAMA)
    x = d[["kode_stasiun"] + pol + cu].copy()
    if x.kode_stasiun.nunique() < 1 or len(x) < 30:
        return _kosong()
    x[pol + cu] = x.groupby("kode_stasiun")[pol + cu].transform(lambda s: s - s.mean())
    cm = x[pol + cu].corr(method="spearman").loc[pol, cu]
    mx = float(cm.abs().max().max()); n_kuat = int((cm.abs() >= 0.3).sum().sum())
    with ui.kartu("p3_cu"):
        if mx < 0.3:
            judul = "Cuaca harian hampir tidak memengaruhi polusi di satu lokasi"
        else:
            r_, c_ = np.unravel_index(np.nanargmax(np.abs(cm.values)), cm.shape)
            judul = f"Hubungan {G.kekuatan(mx)} antara {G.CUACA_NAMA[cu[c_]].lower()} dan {G.POL_PENDEK[list(POLUTAN)[r_]]}"
        ui.judul_kartu(judul, "Kekuatan hubungan tiap zat pencemar dengan cuaca (hover untuk angka); suhu, kelembapan, dan angin dibandingkan dengan rata-rata lokasinya sendiri", tip=G.TIPS["kekuatan"])
        txt = np.vectorize(lambda v: G.kekuatan(v).capitalize())(cm.values)
        ec.tampil(ec.matriks(list(G.CUACA_NAMA.values()), [G.POL_PENDEK[p] for p in POLUTAN], cm.values.tolist(), txt.tolist(), tinggi=340), "p3_cu", 340, klik=False)
        ui.keterangan("Kotak hampir putih = hampir tidak ada hubungan. <b>Yang jauh lebih menentukan polusi adalah lokasi dan musim, bukan cuaca harian.</b>")


def _p3_lalu_lintas(C) -> None:
    nm = G.POL_PENDEK[C.pol]
    _, _, med = jam_agregat(C.D, C.dat, C.kol)
    s = C.D.sites.set_index("kode_stasiun")
    m = med.join(s[["traffic_intensity_per_h", "distance_to_road_m", "kelompok_lokasi"]]).dropna(subset=[C.kol])
    if len(m) < 5:
        return ui.catatan("Perbandingan butuh minimal 5 lokasi. Coba pilih lebih banyak daerah.")
    r1, r2 = eda.spearman(m.traffic_intensity_per_h, m[C.kol]), eda.spearman(m.distance_to_road_m, m[C.kol])
    judul1 = ("Lalu lintas tidak menunjukkan hubungan jelas dengan polusi" if abs(r1["rho"]) < 0.3 else f"Makin padat lalu lintas, polusi cenderung makin {'tinggi' if r1['rho'] > 0 else 'rendah'}")
    judul2 = ("Jarak ke jalan tidak menunjukkan hubungan jelas dengan polusi" if abs(r2["rho"]) < 0.3 else f"Makin jauh dari jalan, polusi cenderung makin {'tinggi' if r2['rho'] > 0 else 'rendah'}")
    c1, c2 = st.columns(2, gap="medium")
    for col, (xk, lab, satuan, r, jd) in zip((c1, c2), (("traffic_intensity_per_h", "Lalu lintas (kendaraan per jam)", "kendaraan/jam", r1, judul1), ("distance_to_road_m", "Jarak ke jalan (meter)", "m", r2, judul2))):
        with col, ui.kartu(f"p3_{xk[:4]}"):
            ui.judul_kartu(jd, f"Tiap titik = satu lokasi · hubungan {G.kekuatan(r['rho'])} ({r['n']} lokasi)", tip=f"{G.TIPS['kekuatan']} Angka: {fl(r['rho'], 2)}; hubungan {G.arah(r['rho'])}. Ini bukan bukti sebab-akibat.")
            kelompok = [(JN[t], WARNA[t], [dict(x=float(v), y=float(y), nama=NM[k]) for k, v, y in zip(q.index, q[xk], q[C.kol])])
                        for t in TIPE for q in [m[m.kelompok_lokasi == t]] if len(q)]
            ec.tampil(ec.sebar(kelompok, judul_x=lab, judul_y=f"Nilai tengah {nm} (µg/m³)", label_x=lab, label_y=f"Polusi {nm}", log_x=xk.startswith("traffic"), tinggi=340),
                      f"p3_{xk[:4]}", 340, klik=False)
            ui.keterangan("Arahkan kursor ke sebuah titik untuk melihat nama daerahnya.")
    ui.catatan("Ini hubungan, bukan sebab-akibat: lalu lintas dan jarak ke jalan bersifat tetap untuk tiap lokasi, sehingga juga mewakili ciri lokasi itu sendiri.")


# =========================================================================== #
# 4 — DAMPAK KESEHATAN
# =========================================================================== #
def p4(C) -> None:
    K2 = C.D.kn["insight"]["2_kesehatan"]
    _header_kesehatan(C, K2)
    t1, t2, t3 = st.tabs(["Pasien dan polusi", "Seberapa besar risikonya", "Tambahan pasien saat kabut asap"])
    with t1:
        _p4_pasien(C, K2)
    with t2:
        _p4_risiko(C, K2)
    with t3:
        _p4_tambahan(C, K2)


def _p4_pasien(C, K2) -> None:
    h = C.dat.health
    if h.empty:
        return _kosong()
    rs = h.drop_duplicates("hospital_id").set_index("hospital_id")
    urut = sorted(rs.index, key=lambda i: G.RS_DARI_KODE.get(i, i))
    with ui.kartu("p4_pilih"):
        pilih = st.columns([1.3, 1.2, 1.5])
        hid = pilih[0].selectbox("Pilih rumah sakit", urut, format_func=_rs, key="p4_rs", index=urut.index(min(urut)))
        kas = pilih[1].selectbox("Pilih jenis penyakit", list(NAMA_KASUS), format_func=lambda k: _kasus(NAMA_KASUS[k]), key="p4_kas", help=G.TIPS["ispa"])
    x = h[h.hospital_id == hid].sort_values("date")
    z = x[["pm25_lag0", kas]].dropna(); rho = eda.spearman(z.pm25_lag0, z[kas].astype(float))
    nk = _kasus(NAMA_KASUS[kas]); nkp = G.KASUS_PENDEK[NAMA_KASUS[kas]]; rsn = G.RS_DARI_KODE.get(hid, hid)
    c1, c2 = st.columns([1.5, 1], gap="medium")
    with c1, ui.kartu("p4_ts"):
        ui.judul_kartu(f"Di {rsn.replace('rumah sakit di ', '')}, hubungan polusi dan pasien {nkp} tergolong {G.kekuatan(rho['rho'])}", "Rata-rata 7 hari: pasien per hari dan debu halus PM2.5 (µg/m³)", tip=G.TIPS["kekuatan"] + f" Angka: {fl(rho['rho'], 2)}.")
        tg = [G.tgl(t) for t in x.date]
        ec.tampil(ec.garis(tg, [dict(name="Pasien per hari", data=x[kas].astype(float).rolling(7, min_periods=3).mean().round(2), color=T.PASIEN, y=0, width=2),
                                dict(name="Debu halus PM2.5 (µg/m³)", data=x.pm25_lag0.rolling(7, min_periods=3).mean().round(2), color=T.SERI, y=1, width=2)],
                           satuan="", desimal=1, judul_y=["Pasien per hari", "PM2.5 (µg/m³)"], tinggi=340), "p4_ts", 340, klik=False)
        ui.keterangan("Garis biru kehijauan = pasien, garis merah = polusi. <b>Bila naik-turunnya mirip, polusi dan pasien bergerak bersama; ini belum tentu sebab-akibat.</b>")
    with c2, ui.kartu("p4_kelas"):
        y = h.dropna(subset=["pm25_lag0"]).copy(); y["rasio"] = y[kas].astype(float) / y.groupby("hospital_id")[kas].transform(lambda s: s.astype(float).mean())
        kelas = ["≤15,5", "15,5–35", "35–55,4", "55,4–150,4", "150,4–250,4", ">250,4"]
        y["kelas"] = pd.cut(y.pm25_lag0, [-np.inf, 15.5, 35, 55.4, 150.4, 250.4, np.inf], labels=kelas)
        g = y.groupby("kelas", observed=False).rasio.mean()
        if g.notna().sum() == 0:
            return _kosong()
        im = int(np.nanargmax(g.values))
        ui.judul_kartu(f"Pasien {nkp} paling banyak saat polusi {kelas[im]} µg/m³ ({fl(g.values[im], 1)}× rata-rata)", "Jumlah pasien dibanding rata-rata (1,0 = biasa), menurut tingkat polusi hari itu (µg/m³)")
        ec.tampil(ec.batang(kelas, [dict(name="Pasien dibanding rata-rata", data=g.values.round(3), warna=[T.ISPU[k] for k in ["Baik", "Sedang", "Sedang", "Tidak Sehat", "Sangat Tidak Sehat", "Berbahaya"]])],
                            satuan="× rata-rata", desimal=2, judul_nilai="Pasien dibanding rata-rata", garis=(1, ""), label=True), "p4_kelas", 340, klik=False)
        ui.keterangan("Warna batang = kategori udara. Garis putus-putus = jumlah pasien biasa. <b>Makin tinggi polusi, makin banyak pasien yang datang.</b>")


def _p4_risiko(C, K2) -> None:
    cum = K2["rr_kumulatif"]; ub = cum[NAMA_KASUS["resp_admissions_under5"]]
    bl = K2["balita_vs_lansia"]["kumulatif"]
    c1, c2 = st.columns(2, gap="medium")
    with c1, ui.kartu("p4_forest"):
        f = pd.DataFrame(cum).T.iloc[::-1]
        semua = bool((f.bawah > 1).all())
        ui.judul_kartu("Semua jenis penyakit bertambah saat polusi naik" if semua else "Pasien bertambah untuk sebagian besar jenis penyakit", "Kenaikan pasien (kali lipat) tiap debu halus naik 10 µg/m³; garis = rentang kepastian", tip=G.TIPS["risiko"])
        fig = go.Figure(go.Scatter(x=f.rr, y=[_kasus(k) for k in f.index], mode="markers", marker=dict(size=11, color=T.SERI), customdata=np.c_[f.bawah, f.atas],
                                   error_x=dict(type="data", symmetric=False, array=(f.atas - f.rr).values, arrayminus=(f.rr - f.bawah).values, color=ui.NAVY),
                                   hovertemplate="%{y}<br>naik %{x:.3f} kali (rentang %{customdata[0]:.3f}–%{customdata[1]:.3f})<extra></extra>"))
        fig.add_vline(x=1, line=dict(dash="dash", color=ui.MUTED)); fig.update_xaxes(title_text="Kali lipat (1 = tidak ada kenaikan)", gridcolor=ui.LINE)
        ui.plot(ui.tema_grafik(fig, 340), "p4_forest")
        ui.keterangan("Titik di kanan garis putus-putus = pasien bertambah. <b>Semua penyakit yang diteliti, termasuk jantung dan kematian, ikut naik.</b>")
    with c2, ui.kartu("p4_ek"):
        ui.judul_kartu("Pasien makin banyak saat polusi makin pekat, lalu kenaikannya melandai", "Berapa kali lipat pasien dibanding saat udara Baik (≤15,5 µg/m³), menurut tingkat polusi")
        er = pd.DataFrame(K2["respons_eksposur_kelas"])
        q0 = er[er.kasus == "ISPA balita (<5 th)"]; kelas_x = list(q0.kelas)
        seri = []
        for kas_, wrn in (("ISPA balita (<5 th)", T.BALITA), ("ISPA lansia (>60 th)", T.LANSIA)):
            q = er[er.kasus == kas_].set_index("kelas").reindex(kelas_x)
            seri.append(dict(name=_kasus(kas_), data=q.rr.round(4).tolist(), color=wrn, bawah=q.rr_bawah.round(4).tolist(), atas=q.rr_atas.round(4).tolist()))
        seri.append(dict(name="perkiraan bila kenaikan lurus", data=q0.rr_linier_model_utama.round(4).tolist(), color=ui.MUTED, putus=True))
        ec.tampil(ec.garis_galat(kelas_x, seri, satuan="kali lipat", desimal=2, tinggi=340, judul_x="Tingkat polusi (µg/m³)", judul_y="Kali lipat vs udara Baik", log=True), "p4_ek", 340, klik=False)
        ui.keterangan("Kenaikan pasien paling tajam pada polusi menengah. <b>Imbauan kesehatan perlu keluar sebelum polusi mencapai tingkat Tidak Sehat.</b>")


def _p4_tambahan(C, K2) -> None:
    kb = K2["kasus_berlebih"]; tot = kb["total"][NAMA_KASUS["resp_admissions_under5"]]
    per = pd.DataFrame(kb["per_rs"]); per = per[per.kasus.isin([NAMA_KASUS["resp_admissions_under5"], NAMA_KASUS["resp_admissions_over60"]])]
    per = per.assign(nama=per.kode_stasiun.map(NM))
    with ui.kartu("p4_ex"):
        bal = per[per.kasus == "ISPA balita (<5 th)"].sort_values("berlebih_model", ascending=False)
        ui.judul_kartu(f"Kabut asap menambah pasien terutama di {bal.nama.iloc[0]} dan {bal.nama.iloc[1]}", "Perkiraan tambahan pasien per rumah sakit (batang = perkiraan komputer, ◆ = selisih dibanding hari biasa) · klik batang untuk menyorot", tip=G.TIPS["tambahan_pasien"])
        nama_rs = sorted(per.nama.unique())
        seri, penanda = [], []
        for kas_, wrn in (("ISPA balita (<5 th)", T.BALITA), ("ISPA lansia (>60 th)", T.LANSIA)):
            q = per[per.kasus == kas_].set_index("nama").reindex(nama_rs)
            seri.append(dict(name=_kasus(kas_), data=q.berlebih_model.round(1).tolist(), color=wrn, bawah=q.bawah.round(1).tolist(), atas=q.atas.round(1).tolist()))
            penanda.append(dict(data=q.berlebih_empiris.round(1).tolist()))
        sel_rs = ec.terpilih("p4_ex")
        ec.tampil(ec.batang_galat(nama_rs, seri, penanda=penanda, satuan="pasien tambahan", tinggi=340, judul_x="Rumah sakit di kota/kabupaten", judul_y="Pasien tambahan",
                                  pilih=sel_rs if sel_rs in nama_rs else None, ket_penanda="(selisih dibanding hari biasa)"), "p4_ex", 340)
        ui.keterangan("Garis hitam kecil = rentang perkiraan. <b>Rumah sakit di kota dengan kabut asap terparah perlu menyiapkan tempat tidur dan tenaga tambahan.</b>")
    ui.catatan("Tambahan pasien disajikan sebagai kisaran (dari yang paling hati-hati sampai perkiraan komputer), karena hasilnya bergantung pada asumsi.")


# =========================================================================== #
# 5 — LOKASI PENGUKURAN
# =========================================================================== #
def p5(C) -> None:
    s = C.D.sites; qc = C.D.qc; K6 = C.D.kn["insight"]["6_jaringan"]
    stat = qc.set_index("kode_stasiun").status_analisis
    _header_lokasi(C, stat)
    _p5_peta(C, s, stat, K6)


def _p5_peta(C, s, stat, K6) -> None:
    warna = dict(T.STATUS)
    cm, cs = st.columns([3, 1.1], gap="medium")
    n_stt = s[s.kode_stasiun.isin(C.dat.stas)].kode_stasiun.map(stat).value_counts()
    with cs, ui.kartu("p5_stat"):
        ui.judul_kartu(f"{int(n_stt.get('Layak', 0))} dari {int(n_stt.sum())} lokasi punya data lengkap", "Kelengkapan catatan alat · klik irisan untuk menyorot")
        sel_s = ec.terpilih("p5_stat")
        sel_i = {v: k for k, v in G.STATUS_DATA.items()}.get(sel_s)
        ec.tampil(ec.donat([(G.STATUS_DATA[k], n_stt.get(k, 0), w) for k, w in warna.items() if n_stt.get(k, 0) > 0], judul=str(int(n_stt.sum())), sub="lokasi", satuan="lokasi", pilih=sel_s), "p5_stat", 290)
        if sel_i:
            for r in s[(s.kode_stasiun.map(stat) == sel_i) & s.kode_stasiun.isin(C.dat.stas)].itertuples():
                st.markdown(f'<div class="row-mint"><div class="ico" style="background:{warna[sel_i]}"></div><div class="tt"><b>{html.escape(NM[r.kode_stasiun])}</b><br>{html.escape(str(r.provinsi))} · {JN[r.kelompok_lokasi]}</div></div>', unsafe_allow_html=True)
        else:
            ui.keterangan("Klik irisan untuk melihat daftar lokasi dan menyorotnya di peta.")
    with cm, ui.kartu("p5_peta"):
        ui.judul_kartu(f"{K6['n_provinsi_tanpa_stasiun']} provinsi belum punya alat pengukur udara", "Titik = lokasi pengukuran (warna = kategori udara) · arsir merah muda berdenyut = provinsi tanpa alat (38 provinsi menurut acuan di luar proyek)", tip=G.TIPS["lokasi"])
        std = STANDAR[C.f["standar"]]["pm25"]
        titik = peta.siapkan_titik(C, C.dat.daily, std, G.BATAS_NAMA[C.f["standar"]], stat, sorot_status=sel_i)
        peta.render_peta(titik, "lokasi", "peta_lokasi", s)
        ui.keterangan("Sebagian besar alat ada di Sumatera dan Jawa, sedangkan Papua, Maluku, dan Nusa Tenggara hampir kosong. <b>Kondisi udara di daerah yang belum diukur tidak diketahui.</b>")
    mx = K6["jarak_terdekat_maks"]
    ui.chips([("Jarak ke lokasi pengukuran terdekat (nilai tengah)", f"{fl(K6['jarak_terdekat_median_km'], 0)} km", G.TIPS["nilai_tengah"]), ("Terjauh", f"{NM[mx['kode']]} {fl(mx['km'], 0)} km")])
