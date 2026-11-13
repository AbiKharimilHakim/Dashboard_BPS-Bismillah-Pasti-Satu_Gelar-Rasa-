"""ARSIP — halaman REKOMENDASI (p6) dan TENTANG DATA (p7), disembunyikan dari menu dashboard.

Cara mengembalikan:
  1. di app/streamlit_app.py, tambahkan ke daftar MENU:
       ("Rekomendasi", "rekomendasi", "task_alt", arsip.p6), ("Tentang data", "tentang-data", "description", arsip.p7)
     dan impor: from app_archive import halaman_rekomendasi_tentang_data as arsip
  2. tambahkan "rekomendasi" dan "tentang-data" kembali ke tools/audit_teks.py (HALAMAN) bila ingin diaudit.
Teks dan data pendukungnya masih ada di app/teks.py (HALAMAN, REKOMENDASI, KETERBATASAN, CARA_BACA) dan app/glossary.py.
"""
from __future__ import annotations

import html

import numpy as np
import pandas as pd
import streamlit as st

import app.pages as _P

globals().update({k: v for k, v in vars(_P).items() if not k.startswith("__")})


def _hero(i, gauge_persen, gauge_judul, gauge_sub, kpi_label, kpi_nilai, kpi_sub="", rapat=False, kpi_tip="", tanpa_tab=False):
    """Pembungkus agar halaman arsip tetap berjalan: memakai header tunggal app/header.py (judul & pertanyaan dari teks.HALAMAN)."""
    from app import header as _header, teks as _teks
    _, q, s = _teks.HALAMAN[i]
    _header.render_header(s, q, gauge_judul, gauge_persen / 100, gauge_sub, kpi_label, kpi_nilai, kpi_sub, "pin", ikon_gauge="pin", kpi_tip=kpi_tip)   # helper & impor milik halaman aktif (_hero, _kat, _tabel, JN, NM, ...)

def _cara_baca(i: int) -> None:
    apa, baca, contoh = teks.CARA_BACA[i]
    with st.expander("Cara membaca halaman ini"):
        st.markdown(f"- **Yang ditampilkan:** {apa}\n- **Cara membaca warna dan grafik:** {baca}\n- **Contoh pembacaan:** {contoh}")


# =========================================================================== #
# 6 — REKOMENDASI
# =========================================================================== #
def p6(C) -> None:
    t1, t2, t3 = st.tabs(["Kondisi terakhir", "Langkah per jenis wilayah", "Kapan perlu waspada"])
    with t1:
        _p6_terakhir(C)
    with t2:
        _p6_langkah(C)
    with t3:
        _p6_waspada(C)
    _cara_baca(6)


def _p6_terakhir(C) -> None:
    d = C.dat.daily
    dv = d[d.pm25_ug_m3.notna()]
    if dv.empty:
        return _kosong()
    last = dv.groupby("kode_stasiun").tanggal.max()
    x = dv.merge(last.rename("terakhir"), left_on="kode_stasiun", right_index=True); x = x[x.tanggal == x.terakhir]
    x["kategori"] = kategori_ispu_pm25(x.pm25_ug_m3).astype(str)
    berat = x[x.kategori.isin(["Tidak Sehat", "Sangat Tidak Sehat", "Berbahaya"])]
    _hero(6, 100 * len(berat) / max(len(x), 1), f"{len(berat)} dari {len(x)} lokasi", "Tidak Sehat atau lebih buruk", "Data terakhir yang tercatat", G.tgl(x.tanggal.max()), "ini kondisi terakhir, bukan prakiraan", kpi_tip=G.TIPS["kategori"])
    with ui.kartu("p6_st"):
        ui.judul_kartu(f"Pada hari data terakhir, udara di {len(berat)} dari {len(x)} lokasi tidak sehat atau lebih buruk", "Kategori udara PM2.5 pada hari terakhir yang tercatat di tiap lokasi, dari yang terburuk", tip=G.TIPS["kategori"])
        for r in x.sort_values("pm25_ug_m3", ascending=False).itertuples():
            wrn = style.ISPU_WARNA[r.kategori]
            st.markdown(f'<div class="row-mint"><div class="ico" style="background:{wrn}"></div><div class="tt"><b>{html.escape(NM[r.kode_stasiun])}</b> · {JN[r.tipe]}<br>{G.tgl(r.tanggal)}{" · kabut asap" if r.episode else ""} — {G.KATEGORI_ARTI[r.kategori]}</div>'
                        f'<div class="vv">{fl(r.pm25_ug_m3)} µg/m³<br><span style="font-size:.7rem;font-weight:600">{r.kategori}</span></div></div>', unsafe_allow_html=True)


def _p6_langkah(C) -> None:
    _hero(6, 0, "5 jenis wilayah", "masing-masing punya langkah sendiri", "Sumber", "Hasil analisis", "angka tidak berubah mengikuti pilihan di sebelah kiri")
    for t in TIPE:
        r = teks.REKOMENDASI[t]
        with ui.kartu(f"p6_{t[:3].lower()}"):
            st.markdown(f'<div class="ct"><div class="tt">{ui.ikon(t.lower(), 24)} {JN[t]}</div></div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2, gap="large")
            c1.markdown("**Yang terlihat di data**\n\n" + "\n".join(f"- {b}" for b in r["bukti"]))
            c2.markdown(f"**Yang perlu dilakukan**\n\n- {r['pemerintah']}\n- {r['rumah_sakit']}\n- **Warga:** {r['warga']}")
    ui.catatan("Rekomendasi adalah usulan analisis dari data simulasi; perlu diuji dengan data nyata sebelum menjadi kebijakan.")


def _p6_waspada(C) -> None:
    K2 = C.D.kn["insight"]["2_kesehatan"]; er = pd.DataFrame(K2["respons_eksposur_kelas"]); er = er[er.kasus == "ISPA balita (<5 th)"]
    ev = C.D.kn["B"]["episode"]["tanpa_bjb01"]
    _hero(6, 0, "Tiga hal", "yang perlu diperhatikan", "Batas kabut asap", "150 µg/m³", "selama minimal 3 hari berturut-turut", kpi_tip=G.TIPS["kabut_asap"])
    with ui.kartu("p6_arti"):
        ui.judul_kartu("Kategori udara dan artinya bagi warga", "Berdasarkan kadar debu halus PM2.5 harian (µg/m³)", tip=G.TIPS["kategori"])
        for k, rg in BATAS_ISPU:
            st.markdown(f'<div class="row-mint"><div class="ico" style="background:{style.ISPU_WARNA[k]}"></div><div class="tt"><b>{k}</b> · {rg} µg/m³<br>{G.KATEGORI_ARTI[k]}</div></div>', unsafe_allow_html=True)
    with ui.kartu("p6_aturan"):
        ui.judul_kartu("Kenapa imbauan perlu keluar lebih awal", "Dasar dari hasil analisis")
        st.markdown(f"""
- **Kabut asap:** polusi debu halus di atas {fl(cfg.EPISODE_PM25_AMBANG, 0)} µg/m³ selama minimal {cfg.EPISODE_MIN_HARI} hari berturut-turut. Hari tanpa catatan yang bisa dipakai memutus hitungan.
- **Risiko pasien:** dibandingkan saat udara Baik (≤15,5 µg/m³), pasien ISPA balita lebih banyak: {', '.join(f"{r.kelas} µg/m³ → {fl(r.rr, 2)}×" for r in er.itertuples())}.
- **Musim:** {ev['n_episode']} kejadian kabut asap (tanpa alat macet), {fl(ev['persen_hari_agu_okt'], 0)}% harinya jatuh pada Agustus–Oktober.
""")
    ui.catatan("Dashboard ini tidak membuat prakiraan; yang ditampilkan adalah catatan terakhir yang tersedia. Batas imbauan kesehatan perlu diuji pada data nyata.")


# =========================================================================== #
# 7 — TENTANG DATA
# =========================================================================== #
def p7(C) -> None:
    t1, t2, t3 = st.tabs(["Sumber & pengolahan", "Kamus istilah", "Detail teknis"])
    with t1:
        _p7_sumber(C)
    with t2:
        _p7_kamus(C)
    with t3:
        _p7_teknis(C)
    _cara_baca(7)


def _log(D, metrik: str) -> float:
    lg = D.log[D.log.entitas.isin(D.sites.kode_stasiun)].copy()
    lg["m"] = lg.metrik.str.replace(r"\[.*\]", "", regex=True)
    return float(lg[lg.m == metrik].jumlah.sum())


def _p7_sumber(C) -> None:
    D = C.D; fn = D.kn["insight"]["0_flatline"]
    _hero(7, 0, f"{fn['n_run']} kejadian alat macet", f"terdeteksi di {', '.join(NM[k] for k in fn['stasiun'])}", "Catatan alat macet yang diabaikan", f"{rp(fn['jam_bertopeng'])} jam", f"{fn['hari_bertopeng']} hari; alat lain paling lama {fn['run_terpanjang_stasiun_lain_jam']} jam tanpa berubah")
    with ui.kartu("p7_asal"):
        ui.judul_kartu("Dari mana angka-angka ini berasal?", "Sumber data yang dipakai")
        st.markdown(f"""
- **Catatan udara per jam** dari {len(D.sites)} lokasi pengukuran, {G.tgl(D.tgl_min)} – {G.tgl(D.tgl_maks)}: {rp(D.kn['meta']['n_jam_pm25'])} catatan jam yang bisa dipakai.
- **Catatan harian pasien** dari {len(D.sites)} rumah sakit rujukan: infeksi saluran pernapasan (ISPA), asma, penyakit paru kronis, penyakit jantung & pembuluh darah, dan kematian.
- **Daftar lokasi:** provinsi, kota/kabupaten, jenis wilayah, lalu lintas, dan jarak ke jalan.
- **Batas aman:** aturan pemerintah (PP 22/2021) dan pedoman WHO 2021. **Kategori udara:** Permen LHK 14/2020 (Indeks Standar Pencemar Udara).
""")
    with ui.kartu("p7_olah"):
        ui.judul_kartu("Bagaimana data dibersihkan?", "Setiap langkah dicatat; angka di dashboard dan laporan berasal dari data yang sama")
        L = lambda m: _log(D, m)
        baris = [
            ("1. Tulisan galat diubah menjadi kosong", f"{rp(L('sel_teks_galat_menjadi_nan'))} isian"),
            ("2. Satuan disamakan ke µg/m³", f"{rp(L('sel_dikonversi_ppm_ke_ugm3'))} nilai diubah satuannya"),
            ("3. Waktu pencatatan dibulatkan ke jam terdekat", f"{rp(L('baris_dibulatkan_ke_jam_terdekat'))} catatan; {rp(L('baris_di_luar_periode'))} di luar periode dibuang"),
            ("4. Angka mustahil dan angka khusus dibuang", f"{rp(L('sel_sentinel_menjadi_nan'))} angka khusus; {rp(L('sel_negatif_menjadi_nan'))} negatif; {rp(L('sel_di_luar_batas_fisik_cuaca_menjadi_nan'))} di luar batas wajar cuaca"),
            ("5. Hanya catatan yang lolos pemeriksaan dipakai", f"{rp(L('baris_non_valid_dibuang'))} catatan dibuang; {rp(L('jam_valid_akhir'))} jam tersisa"),
            ("6. Rata-rata harian dihitung bila minimal 18 dari 24 jam bisa dipakai", f"{rp(L('hari_pm25_ditolak_kurang_dari_18_jam'))} hari ditolak; {rp(L('hari_pm25_valid'))} hari bisa dipakai"),
            ("7. Penanda kabut asap dan batas aman ditambahkan", f"{rp(L('episode_kabut_asap'))} kejadian ({rp(L('hari_dalam_episode'))} hari); {rp(L('hari_pm25_lewat_baku_mutu_pp22'))} hari di atas batas aman nasional"),
            ("8. Data udara digabung dengan data rumah sakit", f"{rp(L('hari_dengan_paparan_pm25_lag0'))} hari punya data polusi; {rp(L('hari_dengan_lag0_sampai_lag7_lengkap'))} hari lengkap sampai 7 hari sebelumnya"),
        ]
        st.markdown("| Langkah | Jumlah yang terdampak |\n|---|---|\n" + "\n".join(f"| {a} | {b} |" for a, b in baris))
        ui.keterangan("Catatan alat macet (angka yang tertahan berhari-hari) ditemukan setelah langkah-langkah ini dan dibuang lewat pilihan di sebelah kiri.")
    with ui.kartu("p7_batas"):
        ui.judul_kartu("Apa yang belum bisa dijawab data ini?", "Keterbatasan, ditulis apa adanya")
        st.markdown("\n".join(f"{i}. {t}" for i, t in enumerate(teks.KETERBATASAN, 1)))


def _p7_kamus(C) -> None:
    ui.catatan("Satu konsep memakai satu istilah di seluruh dashboard dan laporan.")
    with ui.kartu("p7_kamus"):
        ui.judul_kartu("Kamus istilah", "Arti sederhana dan contoh")
        st.markdown("| Istilah | Arti sederhana | Contoh |\n|---|---|---|\n" + "\n".join(f"| **{a}** | {b} | {c} |" for a, b, c in G.GLOSARIUM))


def _p7_teknis(C) -> None:
    D = C.D
    ui.catatan("Bagian ini untuk pembaca teknis dan memuat istilah teknis. Pembaca umum tidak perlu membukanya.")
    A = D.kn["A"]; kw = A["kruskal_wallis"]; tr = A["tren"]; fn = D.kn["insight"]["0_flatline"]
    with st.expander("Untuk pembaca teknis: pemeriksaan data"):
        st.markdown("**Catatan alat macet (flatline, ≥ 24 jam nilai identik)**")
        fl_t = D.flat.assign(lokasi=D.flat.kode_stasiun.map(NM), awal=D.flat.awal.dt.strftime("%d/%m/%Y %H:%M"), akhir=D.flat.akhir.dt.strftime("%d/%m/%Y %H:%M"))
        _tabel(fl_t[["lokasi", "awal", "akhir", "n_jam", "nilai", "n_hari"]].rename(columns={"lokasi": "Lokasi", "awal": "Awal", "akhir": "Akhir", "n_jam": "Jam", "nilai": "Nilai tertahan (µg/m³)", "n_hari": "Hari"}),
               {"Jam": 0, "Nilai tertahan (µg/m³)": 1, "Hari": 1})
        st.markdown("**Ringkasan QC per lokasi**")
        q = D.qc[D.qc.kode_stasiun.isin(C.dat.stas)]
        _tabel(pd.DataFrame({"Lokasi": [NM[k] for k in q.kode_stasiun], "Status alat": q.status_sensor.values, "Status analisis": q.status_analisis.values, "Baris mentah": q.n_baris_mentah.values,
                             "% VALID mentah": q.persen_valid_mentah.values, "% jam PM2.5 valid": q.persen_jam_pm25_valid.values, "% hari valid": q.persen_hari_pm25_valid.values, "Celah terpanjang (jam)": q.gap_terpanjang_jam.values}),
               {"Baris mentah": 0, "% VALID mentah": 1, "% jam PM2.5 valid": 1, "% hari valid": 1, "Celah terpanjang (jam)": 0})
        st.markdown("**Log langkah pra-pemrosesan (seluruh lokasi)**")
        lg = D.log[D.log.entitas.isin(D.sites.kode_stasiun)].copy(); lg["metrik_dasar"] = lg.metrik.str.replace(r"\[.*\]", "", regex=True)
        rk = lg.groupby(["langkah", "nama_langkah", "metrik_dasar", "satuan"], sort=False).jumlah.sum().reset_index().rename(columns={"langkah": "Langkah", "nama_langkah": "Nama langkah", "metrik_dasar": "Metrik", "satuan": "Satuan", "jumlah": "Jumlah"})
        _tabel(rk, {"Langkah": 0, "Jumlah": 0})
        st.markdown("**Masalah data yang ditemukan**")
        ms = D.masalah.copy()
        for c in ("entitas", "deskripsi", "tindakan_usulan"):
            ms[c] = ms[c].map(G.bersihkan)
        _tabel(ms[["id_masalah", "entitas", "kategori", "deskripsi", "jumlah_terdampak", "persen_terdampak", "tingkat", "tindakan_usulan"]], {"jumlah_terdampak": 0, "persen_terdampak": 1})
    with st.expander("Untuk pembaca teknis: metode statistik"):
        st.markdown("""
| Pertanyaan | Metode | Dipakai pada |
|---|---|---|
| Apakah polusi berubah dari tahun ke tahun? | Uji tren Mann-Kendall musiman dan kemiringan Sen, dengan koreksi Benjamini–Hochberg | Kondisi udara › Perubahan dari waktu ke waktu |
| Apakah polusi berbeda antar kelompok? | Kruskal-Wallis dan uji lanjut Dunn–Holm; ukuran pengaruh ε² | Kondisi udara |
| Seberapa erat dua hal berhubungan? | Korelasi peringkat Spearman | Penyebab polusi, Dampak kesehatan |
| Berapa kenaikan pasien tiap polusi naik 10 µg/m³? | Regresi quasi-Poisson dengan jeda 0–7 hari, efek tetap rumah sakit, dan spline waktu (relative risk) | Dampak kesehatan |
| Seberapa tepat polusi dapat ditebak? | Random Forest, Gradient Boosting, regresi berganda; validasi menurut urutan waktu; permutation importance | Penyebab polusi |
| Seberapa besar tambahan pasien saat kabut asap? | Selisih empiris dan estimasi model quasi-Poisson | Dampak kesehatan |
""")
        ui.chips([("ε² jenis wilayah", fl(kw["tipe"]["epsilon2"], 3)), ("ε² pulau", fl(kw["pulau"]["epsilon2"], 3)), ("Pasangan jenis wilayah berbeda nyata (Dunn–Holm)", f"{kw['tipe']['n_pasangan_dunn_signifikan']}/{kw['tipe']['n_pasangan']}"),
                  ("Tren signifikan setelah koreksi", f"{tr['n_signifikan_setelah_bh']}/{tr['n_stasiun_diuji']}"), ("Median kemiringan Sen", f"{fl(tr['slope_median_stasiun_ugm3_per_tahun'], 3)} µg/m³/tahun"),
                  ("Kestabilan peringkat skor risiko (korelasi peringkat, median)", fl(D.kn["insight"]["5_risiko"]["sensitivitas"]["rho_dirichlet_median"], 2))])
    with st.expander("Untuk pembaca teknis: keterbatasan lengkap (laporan analisis)"):
        st.markdown(G.bersihkan(D.keterbatasan))
    with st.expander("Tabel nama lokasi dan kode (referensi)"):
        st.caption("Satu-satunya tempat kode lokasi ditampilkan, untuk mencocokkan dengan berkas data mentah.")
        ref = pd.read_csv(cfg.PROC_DIR / "nama_lokasi.csv")[["kode", "nama_tampil", "nama_pendek", "provinsi", "pulau", "jenis_wilayah"]]
        st.dataframe(ref, width="stretch", hide_index=True, height=430)
