"""Grafik sebelum vs sesudah pembersihan (notebook 03). Semua grafik memakai src/style.py."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import config as cfg
from . import style

WARNA_SEBELUM = "#B3261E"
WARNA_SESUDAH = style.WARNA_UTAMA


def urutan_stasiun(sites: pd.DataFrame) -> list[str]:
    """Urutan tampilan: pulau → kelompok lokasi → kode."""
    s = sites.copy()
    s["o1"] = s["pulau"].map({k: i for i, k in enumerate(cfg.URUTAN_PULAU)})
    s["o2"] = s["kelompok_lokasi"].map({k: i for i, k in enumerate(cfg.URUTAN_KELOMPOK)})
    return s.sort_values(["o1", "o2", "kode_stasiun"]).kode_stasiun.tolist()


def fig_distribusi_sebelum_sesudah(stat: pd.DataFrame, urutan: list[str]) -> go.Figure:
    """Boxplot ringkas PM2.5 per stasiun (kuartil, persentil 1–99, titik maks) sebelum vs sesudah, sumbu log."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.07,
                        subplot_titles=("SEBELUM: nilai mentah apa adanya (satuan sesuai label file, termasuk ppm, sentinel, dan nilai negatif)",
                                        "SESUDAH: baris VALID, µg/m³, tanpa sentinel/negatif"))
    n_neg, dipotong = {}, []
    PISO = 1e-3                                                  # sumbu log tidak dapat menampilkan nilai <= 0
    for baris, tahap, warna in ((1, "sebelum", WARNA_SEBELUM), (2, "sesudah", WARNA_SESUDAH)):
        d = stat[stat.tahap == tahap].set_index("kode_stasiun").reindex(urutan)
        d = d[d["n"].fillna(0) > 0].copy()
        if tahap == "sebelum":
            n_neg = d["n_negatif"].fillna(0).astype(int).to_dict()
            dipotong = d.index[(d["p01"] <= 0) | (d["q1"] <= 0)].tolist()
        for kol in ("p01", "q1", "median", "q3", "p99"):
            d[kol] = d[kol].clip(lower=PISO)                     # nilai <= 0 digambar di lantai 0,001 (lihat anotasi)
        dd = d
        fig.add_trace(go.Box(x=dd.index, q1=dd["q1"], median=dd["median"], q3=dd["q3"], lowerfence=dd["p01"], upperfence=dd["p99"],
                             marker_color=warna, line=dict(color=warna), fillcolor="rgba(0,0,0,0)" if tahap == "sebelum" else "rgba(11,110,110,0.25)",
                             name=tahap.capitalize(), showlegend=False, hoverinfo="skip"), row=baris, col=1)
        fig.add_trace(go.Scatter(x=d.index, y=d["maks"].where(d["maks"] > 0), mode="markers", marker=dict(symbol="triangle-up", size=7, color=warna),
                                 name="Maksimum", showlegend=(baris == 1), customdata=np.c_[d["n"], d["min"], d["median"]],
                                 hovertemplate="%{x}<br>maks %{y:,.4g}<br>median %{customdata[2]:,.4g}<br>min %{customdata[1]:,.4g}<br>n %{customdata[0]:,.0f}<extra></extra>"),
                      row=baris, col=1)
        for nilai, nama, dash in ((cfg.BM_HARIAN["pm25"], "PP 22/2021 (55)", "dash"), (cfg.WHO_HARIAN["pm25"], "WHO 2021 (15)", "dot")):
            fig.add_hline(y=nilai, line=dict(color=style.WARNA_TEKS_REDUP, width=1, dash=dash), row=baris, col=1,
                          annotation_text=nama if baris == 2 else None, annotation_position="top right")
    neg_txt = ", ".join(f"{k}: {v:,}".replace(",", ".") for k, v in n_neg.items() if v > 0)
    fig.update_yaxes(type="log", title_text="PM2.5 (satuan label; sumbu log)", row=1, col=1)
    fig.update_yaxes(type="log", title_text="PM2.5 (µg/m³; sumbu log)", row=2, col=1)
    fig.update_xaxes(tickangle=-60, row=2, col=1)
    fig.add_annotation(xref="paper", yref="paper", x=0, y=1.085, showarrow=False, align="left", font=dict(size=11, color=style.WARNA_TEKS_REDUP),
                       text=(f"Kotak = kuartil 1–3, kumis = persentil 1–99, ▲ = maksimum. Nilai ≤ 0 digambar di lantai 0,001 karena sumbu log "
                             f"(stasiun terpotong pada panel sebelum: {', '.join(dipotong) or '-'}; jumlah nilai negatif mentah: {neg_txt or '0'})."))
    return style.terapkan(fig, "Distribusi PM2.5 per stasiun: sebelum vs sesudah pembersihan", tinggi=820)


def fig_deret_plb_bjb(raw_plb: pd.DataFrame, hourly_plb: pd.DataFrame, raw_bjb: pd.DataFrame, daily_bjb: pd.DataFrame,
                      daily_gambut: pd.Series, awal="2024-09-01", akhir="2024-09-08") -> go.Figure:
    """Contoh deret waktu: PLB-01 (bacaan 15 menit → per jam) dan BJB-01 (ppm → µg/m³, harian)."""
    fig = make_subplots(rows=2, cols=2, vertical_spacing=0.16, horizontal_spacing=0.08, subplot_titles=(
        f"PLB-01 SEBELUM: baris mentah {awal} s.d. {akhir}", "PLB-01 SESUDAH: rata-rata per jam (hanya baris VALID)",
        "BJB-01 SEBELUM: rata-rata harian nilai mentah (label ppm)", "BJB-01 SESUDAH: µg/m³ harian (≥18 jam valid)"))
    ts = pd.to_datetime(raw_plb["timestamp_start"], format="mixed", errors="coerce")
    v = pd.to_numeric(raw_plb["pm25_ug_m3"], errors="coerce")
    m = (ts >= awal) & (ts < akhir)
    warna = {"VALID": style.QC_WARNA["VALID"], "SUSPECT": style.QC_WARNA["SUSPECT"], "CALIBRATING": style.QC_WARNA["CALIBRATING"]}
    for flag in raw_plb.loc[m, "qc_flag"].unique():
        mm = m & (raw_plb["qc_flag"] == flag) & v.notna()
        if mm.any():
            fig.add_trace(go.Scatter(x=ts[mm], y=v[mm], mode="markers", name=flag, marker=dict(size=4, color=warna.get(flag, style.QC_WARNA["Lainnya"])),
                                     legendgroup=flag, hovertemplate="%{x}<br>%{y:.1f} µg/m³<extra>" + flag + "</extra>"), row=1, col=1)
    x = hourly_plb[(hourly_plb["jam"] >= awal) & (hourly_plb["jam"] < akhir)]
    fig.add_trace(go.Scatter(x=x["jam"], y=x["pm25_ug_m3"], mode="lines+markers", marker=dict(size=4), line=dict(color=WARNA_SESUDAH, width=1.5),
                             name="Rata-rata per jam", hovertemplate="%{x}<br>%{y:.1f} µg/m³ (n=%{customdata})<extra></extra>", customdata=x["n_baca"]), row=1, col=2)
    tb = pd.to_datetime(raw_bjb["timestamp_start"], format="mixed", errors="coerce").dt.floor("D")
    vb = pd.to_numeric(raw_bjb["pm25_ppm"], errors="coerce")
    sb = vb.groupby(tb).mean()
    fig.add_trace(go.Scatter(x=sb.index, y=sb.values, mode="lines", line=dict(color=WARNA_SEBELUM, width=1.2), name="BJB-01 mentah (ppm)", showlegend=False,
                             hovertemplate="%{x|%Y-%m-%d}<br>%{y:.4f} (label ppm)<extra></extra>"), row=2, col=1)
    fig.add_trace(go.Scatter(x=daily_bjb["tanggal"], y=daily_bjb["pm25_ug_m3"], mode="lines", line=dict(color=WARNA_SESUDAH, width=1.2), name="BJB-01 (µg/m³)",
                             hovertemplate="%{x|%Y-%m-%d}<br>%{y:.1f} µg/m³<extra></extra>"), row=2, col=2)
    fig.add_trace(go.Scatter(x=daily_gambut.index, y=daily_gambut.values, mode="lines", line=dict(color=style.TIPE_LOKASI_WARNA["Gambut"], width=1.2, dash="dot"),
                             name="Rata-rata stasiun gambut lain", hovertemplate="%{x|%Y-%m-%d}<br>%{y:.1f} µg/m³<extra></extra>"), row=2, col=2)
    fig.add_hline(y=cfg.BM_HARIAN["pm25"], line=dict(color=style.WARNA_TEKS_REDUP, width=1, dash="dash"), row=2, col=2,
                  annotation_text="PP 22/2021 (55)", annotation_position="top left")
    fig.update_yaxes(title_text="PM2.5 (µg/m³)", row=1, col=1)
    fig.update_yaxes(title_text="PM2.5 (µg/m³)", row=1, col=2)
    fig.update_yaxes(title_text="PM2.5 (ppm, label file)", row=2, col=1)
    fig.update_yaxes(title_text="PM2.5 (µg/m³)", row=2, col=2)
    fig.update_xaxes(tickangle=-30)
    return style.terapkan(fig, "Contoh deret waktu: PLB-01 dan BJB-01, sebelum vs sesudah", tinggi=720)


def fig_cakupan_harian_bulan(daily: pd.DataFrame, kode: str = "SM2-01") -> go.Figure:
    """Persentase hari berrata-rata sah per bulan kalender: aturan 18 jam vs 12 jam (dampak sensor saturasi pada musim asap)."""
    d = daily[daily["kode_stasiun"] == kode]
    g = d.groupby("bulan", observed=True).agg(ketat=("pm25_ug_m3", lambda s: 100 * s.notna().mean()),
                                             longgar=("pm25_ug_m3_longgar", lambda s: 100 * s.notna().mean()))
    nama = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    fig = go.Figure()
    fig.add_bar(x=[nama[i - 1] for i in g.index], y=g["ketat"], name=f"Aturan ≥{cfg.MIN_JAM_HARIAN} jam (dipakai)", marker_color=style.WARNA_UTAMA)
    fig.add_bar(x=[nama[i - 1] for i in g.index], y=g["longgar"], name=f"Aturan ≥{cfg.MIN_JAM_HARIAN_LONGGAR} jam (sensitivitas)", marker_color=style.QC_WARNA["MISSING"])
    fig.update_layout(barmode="group")
    return style.terapkan(fig, f"{kode}: persentase hari dengan rata-rata PM2.5 sah per bulan kalender", tinggi=420,
                          sumbu_x="Bulan", sumbu_y="Hari dengan rata-rata sah (%)")


def fig_ispu_per_pulau(daily: pd.DataFrame) -> go.Figure:
    """Komposisi kategori ISPU PM2.5 harian per pulau (hanya hari berrata-rata sah)."""
    d = daily[daily["kategori_ispu_pm25"].notna()]
    t = pd.crosstab(d["pulau"], d["kategori_ispu_pm25"], normalize="index").reindex(index=cfg.URUTAN_PULAU).mul(100)
    fig = go.Figure()
    for k in cfg.ISPU_KATEGORI:
        if k in t.columns:
            fig.add_bar(y=t.index, x=t[k], name=k, orientation="h", marker_color=style.ISPU_WARNA[k], hovertemplate="%{y}<br>" + k + ": %{x:.1f}%<extra></extra>")
    fig.update_layout(barmode="stack")
    fig.update_yaxes(autorange="reversed")
    return style.terapkan(fig, "Komposisi kategori ISPU PM2.5 harian per pulau", tinggi=380, sumbu_x="Persentase hari sah (%)")
