"""Pipeline pembersihan data AQMS + kesehatan (notebook 03).

Seluruh fungsi MURNI (tidak menulis berkas) kecuali `tulis_keluaran`. Data mentah di
data/raw/ hanya dibaca. Setiap langkah mencatat jumlah baris/nilai terdampak ke
`LogPreprocessing` sehingga hasilnya bisa diaudit (reports/preprocessing_log.csv).

Urutan langkah (sesuai permintaan proyek):
  1 teks galat -> NaN, cast numerik          5 filter qc_flag == VALID, agregasi per jam (rata-rata)
  2 standarisasi satuan ppm -> µg/m3          6 agregasi harian bila >= 18 dari 24 jam valid
  3 parse timestamp, bulatkan ke jam          7 feature engineering
  4 buang nilai mustahil & sentinel           8 gabung sites, sensors, hospitals, kesehatan

Catatan penting:
  * Sentinel dideteksi pada skala ASLI (sebelum konversi satuan) lalu diterapkan pada langkah 4.
  * Puncak kabut asap yang asli (PM > 500, hingga > 1000 µg/m3 di KTG) TIDAK dibuang: hanya
    sentinel, nilai negatif, dan nilai di luar batas fisik cuaca yang dibuang.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import config as cfg
from .profiling import (baca_mentah, faktor_ke_ugm3, katalog_file, klasifikasi_nilai, kolom_numerik_aqms, muat_master,
                        nama_kanonik)

POLUTAN_KOL = [f"{p}_ug_m3" for p in cfg.POLUTAN]
VAR_NUM = POLUTAN_KOL + cfg.CUACA
NAMA_HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

LANGKAH = {
    1: "Teks galat → NaN & cast numerik",
    2: "Standarisasi satuan ke µg/m³",
    3: "Parse timestamp, bulatkan ke jam, buang di luar periode",
    4: "Buang nilai mustahil & sentinel",
    5: "Filter qc_flag = VALID & agregasi per jam (rata-rata)",
    6: "Agregasi harian (≥ 18 dari 24 jam valid)",
    7: "Feature engineering",
    8: "Penggabungan master + kesehatan",
}


# =========================================================================== #
# Log preprocessing
# =========================================================================== #
class LogPreprocessing:
    """Pencatat langkah: (langkah, entitas, metrik, jumlah, satuan, sebelum, sesudah, alasan)."""

    def __init__(self):
        self.baris: list[dict] = []

    def add(self, langkah: int, entitas: str, metrik: str, jumlah, satuan: str, alasan: str,
            sebelum=None, sesudah=None, kolom: str = "semua"):
        self.baris.append(dict(
            langkah=langkah, nama_langkah=LANGKAH[langkah], entitas=entitas, kolom=kolom, metrik=metrik,
            jumlah=int(jumlah) if jumlah is not None and not pd.isna(jumlah) else np.nan, satuan=satuan,
            sebelum=sebelum, sesudah=sesudah, alasan=alasan,
        ))

    def frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.baris)


# =========================================================================== #
# Langkah 1–5: satu stasiun, dari CSV mentah ke tabel per jam
# =========================================================================== #
def sentinel_aktif(kanon: str, satuan: str) -> list[float]:
    """Daftar nilai sentinel yang berlaku (999 pada CO µg/m3 adalah konsentrasi wajar, bukan sentinel)."""
    kecuali = cfg.SENTINEL_KECUALI.get(kanon, []) if satuan == "ug/m3" else []
    return [x for x in cfg.SENTINEL if x not in kecuali]


def _stat_ringkas(v: pd.Series) -> dict:
    v = v.dropna()
    if v.empty:
        return dict(n=0)
    q = v.quantile([0.01, 0.25, 0.5, 0.75, 0.99])
    return dict(n=int(len(v)), min=float(v.min()), p01=float(q.iloc[0]), q1=float(q.iloc[1]), median=float(q.iloc[2]),
                q3=float(q.iloc[3]), p99=float(q.iloc[4]), maks=float(v.max()), rata2=float(v.mean()),
                n_negatif=int((v < 0).sum()))


def bersihkan_stasiun(path, kode: str, log: LogPreprocessing) -> dict:
    """Langkah 1–5 untuk satu file AQMS.

    Return dict: `jam` (DataFrame per jam, kolom satuan µg/m3), `qc_mentah` (Series hitungan label),
    `stat_pm25_sebelum` (statistik PM2.5 mentah sebelum langkah apa pun), `satuan`, `n_mentah`.
    """
    df = baca_mentah(path)
    n0 = len(df)
    kolom = kolom_numerik_aqms(df.columns)
    satuan = "ppm" if any(c.endswith("_ppm") for c in kolom) else "ug/m3"
    E = kode

    # ---------------- Langkah 1: teks -> NaN, cast numerik ----------------
    num, sent = {}, {}
    n_teks = n_kosong = 0
    for col in kolom:
        v, k, t = klasifikasi_nilai(df[col])
        kan = nama_kanonik(col)
        num[kan] = v
        sent[kan] = v.isin(sentinel_aktif(kan, satuan))          # skala asli; diterapkan di langkah 4
        n_teks += int(t.sum())
        n_kosong += int(k.sum())
    stat_sebelum = _stat_ringkas(num["pm25"])
    log.add(1, E, "sel_teks_galat_menjadi_nan", n_teks, "sel", "Token galat (0xDEADBEEF, ERR_*, #VALUE!, INF, …) tidak dapat dibaca sebagai angka")
    log.add(1, E, "sel_kosong_dibaca_nan", n_kosong, "sel", "String kosong dibaca sebagai NaN (informasi; nilai sudah hilang di sumber)")
    log.add(1, E, "kolom_di_cast_numerik", len(kolom), "kolom", "10 kolom polutan + cuaca dibaca sebagai teks lalu di-cast ke float")

    w = pd.DataFrame(num)
    qc = df["qc_flag"].str.strip().str.upper()
    qc_mentah = qc.value_counts()

    # ---------------- Langkah 2: satuan -> µg/m3 ----------------
    n_konversi = 0
    if satuan == "ppm":
        for p in cfg.POLUTAN:
            f = faktor_ke_ugm3(p, "ppm")
            n_konversi += int(w[p].notna().sum())
            w[p] = w[p] * f
    log.add(2, E, "sel_dikonversi_ppm_ke_ugm3", n_konversi, "sel",
            "PM ×1000 (hipotesis mg/m³ salah label); gas ppm × BM / 24,45 × 1000 (25 °C, 1 atm). Validasi: median vs stasiun sejenis (notebook 03)")
    w = w.rename(columns={p: f"{p}_ug_m3" for p in cfg.POLUTAN})

    # ---------------- Langkah 3: timestamp ----------------
    ts = pd.to_datetime(df["timestamp_start"], format="mixed", errors="coerce")
    te = pd.to_datetime(df["timestamp_end"], format="mixed", errors="coerce")
    dur = (te - ts).dt.total_seconds()
    subjam = dur.notna() & (dur < 3600)
    geser = (ts - ts.dt.floor("h")).dt.total_seconds().fillna(0) > 0
    jam = ts.dt.round("h").where(~subjam, ts.dt.floor("h"))      # sub-jam: floor (jangan geser :45 ke jam berikutnya)
    dalam = (jam >= cfg.WINDOW_START) & (jam <= cfg.WINDOW_END)
    n_nat = int(ts.isna().sum())
    n_luar = int((jam.notna() & ~dalam).sum())
    log.add(3, E, "baris_timestamp_tak_terbaca", n_nat, "baris", "Format waktu tidak dapat di-parse; baris tidak dapat ditempatkan pada sumbu waktu")
    log.add(3, E, "baris_di_luar_periode", n_luar, "baris", "Di luar 2024-01-01 00:00…2026-10-14 23:00 (mis. epoch 1970)")
    log.add(3, E, "baris_dibulatkan_ke_jam_terdekat", int((geser & ~subjam & dalam).sum()), "baris", "Timestamp bergeser dari awal jam (mis. 23:48, 00:11, milidetik) dibulatkan ke jam terdekat")
    log.add(3, E, "baris_subjam_dipotong_ke_jam_penuh", int((subjam & dalam).sum()), "baris", "Bacaan beresolusi < 1 jam (:00/:15/:30/:45): floor ke jam penuh lalu dirata-rata pada langkah 5")
    w["jam"], w["qc"] = jam, qc
    w = w[dalam].copy()
    n3 = len(w)
    log.add(3, E, "jumlah_baris", n0 - n3, "baris", "Baris yang dibuang pada langkah 3 (tak terbaca + di luar periode)", sebelum=n0, sesudah=n3)

    # ---------------- Langkah 4: mustahil & sentinel ----------------
    valid = w["qc"].eq("VALID")
    kanon_asli = {f"{p}_ug_m3": p for p in cfg.POLUTAN}
    kanon_asli.update({c: c for c in cfg.CUACA})
    n_sent = n_neg = n_rng = n_mustahil_valid = 0
    mustahil_any = pd.Series(False, index=w.index)
    for c in VAR_NUM:
        s_mask = sent[kanon_asli[c]][dalam].reindex(w.index).fillna(False)
        neg = (w[c] < 0) & ~s_mask if c in POLUTAN_KOL else pd.Series(False, index=w.index)
        if c in cfg.BATAS_CUACA:
            lo, hi = cfg.BATAS_CUACA[c]
            rng = ((w[c] < lo) | (w[c] > hi)) & ~s_mask
        else:
            rng = pd.Series(False, index=w.index)
        m = s_mask | neg | rng
        n_sent += int(s_mask.sum()); n_neg += int(neg.sum()); n_rng += int(rng.sum())
        mustahil_any |= m
        w.loc[m, c] = np.nan
    n_mustahil_valid = int((mustahil_any & valid).sum())
    log.add(4, E, "sel_sentinel_menjadi_nan", n_sent, "sel", "Nilai pengganti galat/saturasi (±999, ±9999, -9999, 99999); 999 pada CO µg/m³ dikecualikan (konsentrasi wajar)")
    log.add(4, E, "sel_negatif_menjadi_nan", n_neg, "sel", "Konsentrasi polutan negatif mustahil secara fisik")
    log.add(4, E, "sel_di_luar_batas_fisik_cuaca_menjadi_nan", n_rng, "sel", "Suhu <5/>45 °C, RH di luar 0–100 %, angin >40 m/s, arah di luar 0–360°")
    log.add(4, E, "baris_valid_dengan_nilai_mustahil", n_mustahil_valid, "baris", "Informasi: baris berstatus VALID yang memuat nilai mustahil (penanda QC alat tidak cukup)")
    ekstrem = valid & ((w["pm25_ug_m3"] > cfg.BATAS_EKSTREM_PM["pm25"]) | (w["pm10_ug_m3"] > cfg.BATAS_EKSTREM_PM["pm10"]))
    log.add(4, E, "baris_valid_pm_ekstrem_dipertahankan", int(ekstrem.sum()), "baris", "PM > 500 µg/m³ pada baris VALID DIPERTAHANKAN (kemungkinan puncak kabut asap nyata)")
    log.add(4, E, "baris_valid_pm25_lebih_besar_pm10", int((valid & (w["pm25_ug_m3"] > w["pm10_ug_m3"])).sum()), "baris", "Informasi: PM2.5 > PM10 tidak konsisten fisik; hanya ditandai, tidak dibuang")

    # ---------------- Langkah 5: VALID + agregasi per jam ----------------
    n_valid = int(valid.sum())
    for lab, jml in w.loc[~valid, "qc"].value_counts().items():
        log.add(5, E, f"baris_non_valid_dibuang[{lab}]", jml, "baris", "qc_flag selain VALID tidak dipakai untuk analisis konsentrasi")
    log.add(5, E, "jumlah_baris_non_valid", n3 - n_valid, "baris", "Total baris non-VALID dibuang", sebelum=n3, sesudah=n_valid)
    wv = w[valid]
    g = wv.groupby("jam")
    num_cols = [c for c in VAR_NUM if c != "wind_direction_deg"]
    h = g[num_cols].mean()
    h["n_baca"] = g.size().astype("int16")
    rad = np.deg2rad(wv["wind_direction_deg"])
    s_ = np.sin(rad).groupby(wv["jam"]).mean()
    c_ = np.cos(rad).groupby(wv["jam"]).mean()
    ada = wv["wind_direction_deg"].notna().groupby(wv["jam"]).any()
    h["wind_direction_deg"] = (np.rad2deg(np.arctan2(s_, c_)).round(1) % 360).where(ada)   # rata-rata melingkar
    h = h[VAR_NUM + ["n_baca"]].reset_index()
    h.insert(0, "kode_stasiun", kode)
    jam_dup = int((h["n_baca"] > 1).sum())
    log.add(5, E, "jam_diagregasi_rata2", jam_dup, "jam", "Jam berisi >1 baris VALID dirata-rata (arah angin: rata-rata melingkar)")
    log.add(5, E, "jumlah_baris_per_jam", n_valid - len(h), "baris", "Baris tambahan yang digabung ke jam yang sama", sebelum=n_valid, sesudah=len(h))
    log.add(5, E, "jam_valid_akhir", len(h), "jam", f"Jam dengan ≥1 baris VALID dari {cfg.EXPECTED_HOURS} jam yang diharapkan", sebelum=cfg.EXPECTED_HOURS, sesudah=len(h))
    return dict(jam=h, qc_mentah=qc_mentah, stat_pm25_sebelum=stat_sebelum, satuan=satuan, n_mentah=n0,
                n_ekstrem_valid=int(ekstrem.sum()))


# =========================================================================== #
# Master: sites_clean
# =========================================================================== #
def bangun_sites_clean(raw_dir=cfg.RAW_DIR) -> pd.DataFrame:
    """Gabungan sites + sensors + hospitals (1 baris per stasiun) dengan atribut turunan."""
    m = muat_master(raw_dir)
    sites, sensors, hosp = m["sites"], m["sensors"], m["hospitals"]
    s = sites.merge(
        sensors[["sensor_id", "location_id", "nama_sensor", "model_sensor", "tipe_pemasangan", "status_operasional", "tanggal_instalasi"]]
        .rename(columns={"status_operasional": "status_sensor"}), on="location_id", how="left", validate="1:1")
    s["kode_stasiun"] = s["location_id"].str.replace("LOC-", "", regex=False)
    s["hospital_id"] = s["sensor_id"].str[-3:].astype(int).map(lambda n: f"RS-XXX-{n:02d}")
    s = s.merge(hosp[["hospital_id", "nama_rumah_sakit", "kelas_faskes", "kapasitas_tempat_tidur"]], on="hospital_id", how="left", validate="1:1")
    s["provinsi"] = s["provinsi"].map(cfg.normalisasi_provinsi)
    s["pulau"] = s["provinsi"].map(cfg.pulau_dari_provinsi)
    s["kelompok_lokasi"] = s["site_type"].map(cfg.kelompok_lokasi)
    s["zona_waktu"] = s["provinsi"].map(lambda p: cfg.ZONA_WAKTU_PROVINSI.get(p, ("WIB", 0))[0])
    s["offset_jam_dari_wib"] = s["provinsi"].map(lambda p: cfg.ZONA_WAKTU_PROVINSI.get(p, ("WIB", 0))[1]).astype("int8")
    kat = katalog_file(raw_dir).query("tabel == 'aqms'")
    unit = {r.kode_stasiun: ("ppm" if any(c.endswith("_ppm") for c in pd.read_csv(r.path, nrows=0).columns) else "ug/m3") for r in kat.itertuples()}
    s["satuan_asli"] = s["kode_stasiun"].map(unit)
    s["file_sumber"] = s["kode_stasiun"].map(dict(zip(kat.kode_stasiun, kat.file)))
    s["tanggal_instalasi"] = pd.to_datetime(s["tanggal_instalasi"])
    assert s["pulau"].ne("Tidak terpetakan").all() and s["kelompok_lokasi"].ne("Lainnya").all(), "Pemetaan pulau/kelompok tidak lengkap"
    kolom = ["kode_stasiun", "location_id", "station_code", "sensor_id", "nama_sensor", "model_sensor", "tipe_pemasangan", "status_sensor",
             "tanggal_instalasi", "provinsi", "kota_kabupaten", "kecamatan", "pulau", "region_group", "site_type", "kelompok_lokasi",
             "karakteristik_wilayah", "latitude_dd", "longitude_dd", "baseline_pm25", "distance_to_road_m", "traffic_intensity_per_h",
             "zona_waktu", "offset_jam_dari_wib", "satuan_asli", "file_sumber", "hospital_id", "nama_rumah_sakit", "kelas_faskes",
             "kapasitas_tempat_tidur"]
    return s[kolom].sort_values("kode_stasiun").reset_index(drop=True)


# =========================================================================== #
# Fitur
# =========================================================================== #
def kategori_ispu_pm25(x: pd.Series) -> pd.Series:
    """Kategori ISPU dari PM2.5 24 jam (µg/m³): ≤15,5 Baik | ≤55,4 Sedang | ≤150,4 Tidak Sehat | ≤250,4 Sangat Tidak Sehat | >250,4 Berbahaya."""
    bins = [-np.inf, 15.5, 55.4, 150.4, 250.4, np.inf]
    return pd.cut(x, bins=bins, labels=cfg.ISPU_KATEGORI, right=True).astype(pd.CategoricalDtype(cfg.ISPU_KATEGORI, ordered=True))


def indeks_ispu_pm25(x: pd.Series) -> pd.Series:
    """Indeks ISPU PM2.5 (interpolasi linear antar-breakpoint; dipotong pada 500)."""
    v = np.interp(x.clip(lower=0, upper=500), cfg.ISPU_PM25_KONSENTRASI, cfg.ISPU_PM25_INDEKS)
    return pd.Series(np.where(x.isna(), np.nan, v), index=x.index).round(1)


def tambah_fitur_waktu(df: pd.DataFrame, kolom_waktu: str, sites: pd.DataFrame | None = None, jam: bool = True) -> pd.DataFrame:
    """Fitur kalender dari timestamp WIB: tahun, bulan, hari, akhir pekan, musim (+ jam & jam_lokal bila `jam`)."""
    t = df[kolom_waktu]
    df["tahun"] = t.dt.year.astype("int16")
    df["bulan"] = t.dt.month.astype("int8")
    df["hari_ke"] = t.dt.dayofweek.astype("int8")                         # 0 = Senin
    df["hari"] = pd.Categorical([NAMA_HARI[i] for i in df["hari_ke"]], categories=NAMA_HARI, ordered=True)
    df["akhir_pekan"] = df["hari_ke"] >= 5
    df["musim"] = pd.Categorical(np.where(df["bulan"].isin(cfg.MUSIM_KEMARAU_BULAN), "Kemarau", "Hujan"), categories=["Kemarau", "Hujan"])
    if jam:
        df["jam_wib"] = t.dt.hour.astype("int8")
        if sites is not None:
            off = df["kode_stasiun"].astype(str).map(sites.set_index("kode_stasiun")["offset_jam_dari_wib"]).astype(int)
            df["jam_lokal"] = ((df["jam_wib"] + off) % 24).astype("int8")
    return df


def tambah_atribut_stasiun(df: pd.DataFrame, sites: pd.DataFrame) -> pd.DataFrame:
    s = sites.set_index("kode_stasiun")
    k = df["kode_stasiun"].astype(str)
    df["pulau"] = pd.Categorical(k.map(s["pulau"]), categories=cfg.URUTAN_PULAU)
    df["kelompok_lokasi"] = pd.Categorical(k.map(s["kelompok_lokasi"]), categories=cfg.URUTAN_KELOMPOK)
    return df


# =========================================================================== #
# Langkah 6: agregasi harian
# =========================================================================== #
def agregasi_harian(hourly: pd.DataFrame, stasiun: list[str], log: LogPreprocessing) -> pd.DataFrame:
    """Rata-rata harian per variabel hanya bila ≥ 18 dari 24 jam valid; grid kalender lengkap per stasiun."""
    h = hourly.copy()
    h["tanggal"] = h["jam"].dt.floor("D")
    rad = np.deg2rad(h["wind_direction_deg"])
    h["_sin"], h["_cos"] = np.sin(rad), np.cos(rad)
    g = h.groupby(["kode_stasiun", "tanggal"], observed=True)
    mean = g[[c for c in VAR_NUM if c != "wind_direction_deg"] + ["_sin", "_cos"]].mean()
    cnt = g[VAR_NUM].count()
    d = mean.copy()
    for c in VAR_NUM:
        if c == "wind_direction_deg":
            wd = (np.rad2deg(np.arctan2(mean["_sin"], mean["_cos"])).round(1) % 360)
            d[c] = wd.where(cnt[c] >= cfg.MIN_JAM_HARIAN)
        else:
            d[c] = mean[c].where(cnt[c] >= cfg.MIN_JAM_HARIAN)
    d = d.drop(columns=["_sin", "_cos"])
    d["pm25_ug_m3_longgar"] = mean["pm25_ug_m3"].where(cnt["pm25_ug_m3"] >= cfg.MIN_JAM_HARIAN_LONGGAR)     # hanya sensitivitas
    d["pm25_maks_jam_ug_m3"] = g["pm25_ug_m3"].max().where(cnt["pm25_ug_m3"] >= cfg.MIN_JAM_HARIAN)
    d["n_jam_pm25"] = cnt["pm25_ug_m3"].astype("int8")
    d["n_jam_pm10"] = cnt["pm10_ug_m3"].astype("int8")
    d["n_jam_data"] = g.size().astype("int8")
    # grid kalender lengkap (hari tanpa data = NaN, n_jam = 0)
    tgl = pd.date_range(cfg.WINDOW_START.normalize(), cfg.WINDOW_END.normalize(), freq="D")
    idx = pd.MultiIndex.from_product([sorted(stasiun), tgl], names=["kode_stasiun", "tanggal"])
    d = d.reindex(idx)
    for c in ("n_jam_pm25", "n_jam_pm10", "n_jam_data"):
        d[c] = d[c].fillna(0).astype("int8")
    d = d.reset_index()
    for s in sorted(stasiun):
        x = d[d.kode_stasiun == s]
        ada = x["n_jam_pm25"] > 0
        log.add(6, s, "hari_kalender", len(x), "hari", "Grid kalender lengkap 2024-01-01…2026-10-14")
        log.add(6, s, "hari_dengan_data_pm25", int(ada.sum()), "hari", "Hari dengan ≥1 jam PM2.5 valid")
        log.add(6, s, "hari_pm25_ditolak_kurang_dari_18_jam", int((ada & (x["n_jam_pm25"] < cfg.MIN_JAM_HARIAN)).sum()), "hari",
                f"Rata-rata harian tidak dihitung bila < {cfg.MIN_JAM_HARIAN} dari 24 jam valid (75%)", sebelum=int(ada.sum()), sesudah=int(x["pm25_ug_m3"].notna().sum()))
        log.add(6, s, "hari_pm25_valid", int(x["pm25_ug_m3"].notna().sum()), "hari", "Hari dengan rata-rata PM2.5 sah")
        log.add(6, s, "hari_tanpa_data", int((~ada).sum()), "hari", "Tidak ada satu pun jam PM2.5 valid")
    return d


def tandai_episode(d: pd.DataFrame, log: LogPreprocessing) -> pd.DataFrame:
    """Episode kabut asap: PM2.5 harian > 150 µg/m³ selama ≥ 3 hari kalender berturut-turut (hari NaN memutus rangkaian)."""
    d = d.sort_values(["kode_stasiun", "tanggal"]).reset_index(drop=True)
    ep = np.zeros(len(d), bool)
    idep = np.full(len(d), np.nan)
    hari_ke = np.zeros(len(d), "int16")
    for s, ix in d.groupby("kode_stasiun", observed=True).indices.items():
        flag = (d.loc[ix, "pm25_ug_m3"] > cfg.EPISODE_PM25_AMBANG).to_numpy()
        run = np.cumsum(np.r_[True, flag[1:] != flag[:-1]])
        ukuran = pd.Series(run).groupby(run).transform("size").to_numpy()
        e = flag & (ukuran >= cfg.EPISODE_MIN_HARI)
        nomor = pd.Series(np.where(e, run, np.nan)).rank(method="dense").to_numpy()
        ke = pd.Series(run).groupby(run).cumcount().add(1).to_numpy()
        ep[ix], idep[ix], hari_ke[ix] = e, nomor, np.where(e, ke, 0)
    d["episode_asap"] = ep
    d["id_episode"] = pd.Series(np.where(ep, d["kode_stasiun"].astype(str) + "-E" + pd.Series(idep).fillna(0).astype(int).astype(str).str.zfill(2), None), dtype="string")
    d["hari_ke_episode"] = hari_ke
    for s, x in d.groupby("kode_stasiun", observed=True):
        log.add(7, s, "episode_kabut_asap", x["id_episode"].nunique(), "episode", f"PM2.5 harian > {cfg.EPISODE_PM25_AMBANG:g} µg/m³ selama ≥ {cfg.EPISODE_MIN_HARI} hari kalender berturut-turut")
        log.add(7, s, "hari_dalam_episode", int(x["episode_asap"].sum()), "hari", "Jumlah hari yang ditandai episode")
    return d


def fitur_harian(d: pd.DataFrame, sites: pd.DataFrame, log: LogPreprocessing) -> pd.DataFrame:
    """Langkah 7 untuk tabel harian: ISPU, flag baku mutu, kalender, atribut stasiun, episode."""
    d = tambah_fitur_waktu(d, "tanggal", jam=False)
    d = tambah_atribut_stasiun(d, sites)
    d["ispu_pm25"] = indeks_ispu_pm25(d["pm25_ug_m3"])
    d["kategori_ispu_pm25"] = kategori_ispu_pm25(d["pm25_ug_m3"])
    for p in ("pm25", "pm10"):
        x = d[f"{p}_ug_m3"]
        d[f"lewat_bm_{p}"] = (x > cfg.BM_HARIAN[p]).where(x.notna())
        d[f"lewat_who_{p}"] = (x > cfg.WHO_HARIAN[p]).where(x.notna())
        for c in (f"lewat_bm_{p}", f"lewat_who_{p}"):
            d[c] = d[c].astype("boolean")
    d = tandai_episode(d, log)
    for s, x in d.groupby("kode_stasiun", observed=True):
        log.add(7, s, "hari_pm25_lewat_baku_mutu_pp22", int(x["lewat_bm_pm25"].fillna(False).sum()), "hari", f"PM2.5 harian > {cfg.BM_HARIAN['pm25']:g} µg/m³ (PP 22/2021)")
    return d


def fitur_jam(h: pd.DataFrame, sites: pd.DataFrame) -> pd.DataFrame:
    """Langkah 7 untuk tabel per jam."""
    h = tambah_fitur_waktu(h, "jam", sites, jam=True)
    h = tambah_atribut_stasiun(h, sites)
    h["pm_ekstrem"] = (h["pm25_ug_m3"] > cfg.BATAS_EKSTREM_PM["pm25"]) | (h["pm10_ug_m3"] > cfg.BATAS_EKSTREM_PM["pm10"])
    h["kode_stasiun"] = h["kode_stasiun"].astype("category")
    return h


# =========================================================================== #
# Kualitas stasiun & status analisis
# =========================================================================== #
def _gap_terpanjang(jam: pd.Series) -> int:
    harap = pd.date_range(cfg.WINDOW_START, cfg.WINDOW_END, freq="h")
    hilang = harap.difference(pd.DatetimeIndex(jam.unique()))
    if len(hilang) == 0:
        return 0
    x = hilang.values.astype("datetime64[h]").astype("int64")
    batas = np.concatenate([[-1], np.where(np.diff(x) != 1)[0], [len(x) - 1]])
    return int(np.max(np.diff(batas)))


def status_analisis(persen_jam_valid: float) -> str:
    if persen_jam_valid >= cfg.AMBANG_LAYAK * 100:
        return "Layak"
    if persen_jam_valid < cfg.AMBANG_DIKECUALIKAN * 100:
        return "Dikecualikan"
    return "Terbatas"


CATATAN_STASIUN = {
    "JMB-02": ("Dikecualikan dari aq_hourly, aq_daily, dan paparan kesehatan. Sensor Defective; hanya 0,5% baris VALID, tersebar acak dan "
               "berhenti setelah Agustus 2024; 99,5% baris berisi galat/mustahil. Dipertahankan di sites_clean & qc_summary sebagai bukti kebutuhan jaringan (Tujuan 5)."),
    "MER-01": ("Terbatas. ±20% jam VALID tersebar acak (median 6 jam VALID per hari), sehingga hampir tidak ada hari yang memenuhi ≥18 jam. "
               "Dipakai untuk profil per jam/klimatologi (nilai VALID wajar), TIDAK untuk model harian/lag kesehatan. Aturan 75% tidak dilonggarkan."),
    "MDN-01": "Terbatas. 3.632 jam tidak tercatat dan 20% baris non-VALID (WARMUP/MAINTENANCE/CALIBRATING); satuan ppm dikonversi.",
    "PLB-01": ("Sensor Intermittent: 5.136 baris MISSING membuat cakupan harian jauh lebih rendah daripada cakupan jam. "
               "Logger merekam tiap 15 menit pada Sep–Okt (dirata-rata per jam)."),
    "SM2-01": ("Nilai saturasi 999 (SUSPECT) pada Jul–Okt dibuang, sehingga puncak kabut asap kemungkinan "
               "terpangkas (bias ke bawah) dan lebih banyak hari berasap gagal aturan 18 jam; gunakan pm25_ug_m3_longgar untuk sensitivitas."),
    "BJB-01": "100% VALID, tetapi pola musim menyimpang dari stasiun gambut lain dan satuan ppm; anomali dicatat untuk EDA.",
}


def ringkas_qc(sites: pd.DataFrame, hasil: dict[str, dict], hourly: pd.DataFrame, daily: pd.DataFrame | None) -> pd.DataFrame:
    """Tabel qc_summary: 1 baris per stasiun (27)."""
    baris = []
    for _, s in sites.iterrows():
        k = s["kode_stasiun"]
        r = hasil[k]
        hj = hourly[hourly.kode_stasiun == k]
        n_jam = hj["pm25_ug_m3"].notna().sum()
        pj = 100 * n_jam / cfg.EXPECTED_HOURS
        row = dict(kode_stasiun=k, location_id=s["location_id"], sensor_id=s["sensor_id"], status_sensor=s["status_sensor"],
                   satuan_asli=r["satuan"], n_baris_mentah=r["n_mentah"], n_baris_valid_mentah=int(r["qc_mentah"].get("VALID", 0)),
                   persen_valid_mentah=round(100 * r["qc_mentah"].get("VALID", 0) / r["n_mentah"], 2),
                   n_jam_diharapkan=cfg.EXPECTED_HOURS, n_jam_ada_baris_valid=len(hj), n_jam_pm25_valid=int(n_jam),
                   persen_jam_pm25_valid=round(pj, 2), gap_terpanjang_jam=_gap_terpanjang(hj["jam"]),
                   n_jam_diagregasi=int((hj["n_baca"] > 1).sum()), n_ekstrem_valid=r["n_ekstrem_valid"])
        for lab, jml in r["qc_mentah"].items():
            row[f"qc_{lab}"] = int(jml)
        row["status_analisis"] = status_analisis(pj)
        row["catatan"] = CATATAN_STASIUN.get(k, "")
        baris.append(row)
    q = pd.DataFrame(baris)
    qc_cols = sorted(c for c in q.columns if c.startswith("qc_"))
    q[qc_cols] = q[qc_cols].fillna(0).astype(int)
    if daily is not None:
        hari = daily.groupby("kode_stasiun", observed=True).agg(n_hari_diharapkan=("tanggal", "size"), n_hari_pm25_valid=("pm25_ug_m3", "count"),
                                                                 n_hari_pm25_valid_longgar=("pm25_ug_m3_longgar", "count"))
        q = q.merge(hari, left_on="kode_stasiun", right_index=True, how="left")
        q["persen_hari_pm25_valid"] = (100 * q["n_hari_pm25_valid"] / q["n_hari_diharapkan"]).round(2)
        km = daily[daily["musim"] == "Kemarau"].groupby("kode_stasiun", observed=True)["pm25_ug_m3"].agg(lambda s: 100 * s.notna().mean())
        q["persen_hari_pm25_valid_kemarau"] = q["kode_stasiun"].map(km).round(2)
        # Status akhir: pengecualian (tidak masuk tabel analisis) ditentukan oleh cakupan JAM (< 10%).
        # Di antara stasiun yang dipertahankan: Layak bila cakupan jam, cakupan hari (model kesehatan memakai rata-rata
        # harian), dan cakupan hari musim kemarau (musim kabut asap) semuanya >= 75%; selain itu Terbatas.
        cakupan = q[["persen_jam_pm25_valid", "persen_hari_pm25_valid", "persen_hari_pm25_valid_kemarau"]].min(axis=1)
        q["cakupan_terendah_persen"] = cakupan.round(2)
        q["status_analisis"] = [("Dikecualikan" if status_analisis(pj) == "Dikecualikan" else ("Layak" if c >= cfg.AMBANG_LAYAK * 100 else "Terbatas"))
                                for pj, c in zip(q["persen_jam_pm25_valid"], cakupan)]
    return q


# =========================================================================== #
# Langkah 8: kesehatan + paparan
# =========================================================================== #
KASUS = ["resp_admissions_under5", "resp_admissions_over60", "asthma_emergency_cases", "copd_admissions", "resp", "cvd", "death"]


def gabung_kesehatan(daily: pd.DataFrame, sites: pd.DataFrame, qc: pd.DataFrame, log: LogPreprocessing, raw_dir=cfg.RAW_DIR) -> pd.DataFrame:
    """Kesehatan harian per RS + atribut stasiun pasangan + PM2.5 lag 0–7 dan rata-rata 3 hari."""
    h = pd.read_csv(Path(raw_dir) / "HLT-01_health_outcomes_daily.csv")
    n0 = len(h)
    h["date"] = pd.to_datetime(h["date"])
    sebelum = h["date"] < cfg.WINDOW_START.normalize()
    log.add(8, "HLT-01", "baris_sebelum_periode_aqms_dibuang", int(sebelum.sum()), "baris", "Baris 2023-12-31 tidak punya pasangan data paparan AQMS (hanya ada di 5 RS)")
    h = h[~sebelum].copy()
    for c in KASUS:
        assert (h[c].dropna() % 1 == 0).all() and (h[c].dropna() >= 0).all(), f"{c} bukan bilangan bulat non-negatif"
        h[c] = h[c].astype("Int64")
    h = h.rename(columns={"time": "urutan_hari_rs"})
    h["urutan_hari_rs"] = h["urutan_hari_rs"].astype("int16")
    h["dow"] = h["dow"].str.strip()

    # PM2.5 harian per stasiun: lag kalender 0–7 dan rata-rata 3 hari (lag 0–2, harus lengkap 3 hari)
    d = daily.sort_values(["kode_stasiun", "tanggal"])
    ek = d[["kode_stasiun", "tanggal", "pm25_ug_m3", "n_jam_pm25", "kategori_ispu_pm25", "ispu_pm25", "lewat_bm_pm25", "lewat_who_pm25", "episode_asap", "id_episode"]].copy()
    gp = ek.groupby("kode_stasiun", observed=True)["pm25_ug_m3"]
    for L in cfg.LAG_PM25:
        ek[f"pm25_lag{L}"] = gp.shift(L)
    ek["pm25_ma3"] = gp.transform(lambda s: s.rolling(3, min_periods=3).mean())
    ek = ek.drop(columns=["pm25_ug_m3"]).rename(columns={"n_jam_pm25": "n_jam_pm25_hari0", "kategori_ispu_pm25": "kategori_ispu_pm25_hari0", "ispu_pm25": "ispu_pm25_hari0"})
    ek["kode_stasiun"] = ek["kode_stasiun"].astype(str)

    s = sites.merge(qc[["kode_stasiun", "status_analisis"]], on="kode_stasiun", how="left")
    ats = s[["hospital_id", "kode_stasiun", "nama_rumah_sakit", "kelas_faskes", "kapasitas_tempat_tidur", "provinsi", "pulau", "kelompok_lokasi",
             "site_type", "status_analisis", "status_sensor"]].rename(columns={"status_analisis": "status_analisis_stasiun"})
    h = h.merge(ats, on="hospital_id", how="left", validate="m:1")
    assert h["kode_stasiun"].notna().all(), "RS tanpa stasiun pasangan"
    h = h.merge(ek, left_on=["kode_stasiun", "date"], right_on=["kode_stasiun", "tanggal"], how="left", validate="m:1").drop(columns=["tanggal"])
    h = tambah_fitur_waktu(h, "date", jam=False)
    h["pulau"] = pd.Categorical(h["pulau"], categories=cfg.URUTAN_PULAU)
    h["kelompok_lokasi"] = pd.Categorical(h["kelompok_lokasi"], categories=cfg.URUTAN_KELOMPOK)
    h["ada_paparan_pm25"] = h["pm25_lag0"].notna()
    h = h.sort_values(["hospital_id", "date"]).reset_index(drop=True)
    log.add(8, "HLT-01", "jumlah_baris", n0 - len(h), "baris", "Baris kesehatan dibatasi pada periode AQMS", sebelum=n0, sesudah=len(h))
    for hid, x in h.groupby("hospital_id"):
        e = f"{hid}/{x['kode_stasiun'].iloc[0]}"
        log.add(8, e, "hari_dengan_paparan_pm25_lag0", int(x["ada_paparan_pm25"].sum()), "hari", "Hari kesehatan yang punya PM2.5 harian sah di stasiun pasangan", sebelum=len(x), sesudah=int(x["ada_paparan_pm25"].sum()))
        log.add(8, e, "hari_dengan_lag0_sampai_lag7_lengkap", int(x[[f"pm25_lag{L}" for L in cfg.LAG_PM25]].notna().all(axis=1).sum()), "hari", "Hari dengan PM2.5 lag 0–7 lengkap (dipakai model efek jeda)")
    return h


# =========================================================================== #
# Validasi
# =========================================================================== #
def validasi_satuan(hourly: pd.DataFrame, sites: pd.DataFrame, qc: pd.DataFrame) -> pd.DataFrame:
    """Bandingkan median stasiun berunit ppm (setelah konversi) dengan stasiun sejenis (kelompok lokasi sama, satuan µg/m³, status bukan Dikecualikan).

    PM2.5 juga dibandingkan dengan `baseline_pm25` stasiun itu. Kolom `rasio_tanpa_konversi` memperlihatkan
    skala jika konversi TIDAK dilakukan (mis. PM2.5 dalam label ppm ≈ 0,05 → rasio ≈ 0,001).
    """
    s = sites if "status_analisis" in sites.columns else sites.merge(qc[["kode_stasiun", "status_analisis"]], on="kode_stasiun")
    med = hourly.groupby("kode_stasiun", observed=True)[POLUTAN_KOL].median()
    baris = []
    for _, st in s[s.satuan_asli == "ppm"].iterrows():
        peers = s[(s.kelompok_lokasi == st.kelompok_lokasi) & (s.satuan_asli == "ug/m3") & (s.status_analisis != "Dikecualikan") & (s.kode_stasiun != st.kode_stasiun)].kode_stasiun
        for c in POLUTAN_KOL:
            p = c.replace("_ug_m3", "")
            nilai = med.loc[st.kode_stasiun, c]
            ref = med.loc[peers, c].median()
            f = faktor_ke_ugm3(p, "ppm")
            baris.append(dict(kode_stasiun=st.kode_stasiun, kelompok_lokasi=st.kelompok_lokasi, polutan=p, n_stasiun_sejenis=len(peers),
                              median_setelah_konversi=nilai, median_stasiun_sejenis=ref, rasio=nilai / ref, rasio_tanpa_konversi=(nilai / f) / ref,
                              baseline_pm25=st.baseline_pm25 if p == "pm25" else np.nan,
                              rasio_vs_baseline=nilai / st.baseline_pm25 if p == "pm25" else np.nan))
    return pd.DataFrame(baris)


def validasi_output(hourly: pd.DataFrame, daily: pd.DataFrame, health: pd.DataFrame, sites: pd.DataFrame, qc: pd.DataFrame,
                    lanjut_jika_gagal: bool = False) -> pd.DataFrame:
    """Jalankan seluruh assert; kembalikan tabel hasil. Bila ada yang gagal dan tidak `lanjut_jika_gagal`, lempar AssertionError."""
    hasil = []

    def cek(nama, ok, detail=""):
        hasil.append(dict(pemeriksaan=nama, lulus=bool(ok), detail=detail))

    k = hourly["kode_stasiun"].astype(str)
    cek("Tidak ada duplikat (stasiun, jam) pada aq_hourly", not hourly.duplicated(["kode_stasiun", "jam"]).any(), f"{int(hourly.duplicated(['kode_stasiun', 'jam']).sum())} duplikat")
    cek("Tidak ada duplikat (stasiun, tanggal) pada aq_daily", not daily.duplicated(["kode_stasiun", "tanggal"]).any())
    cek("Tidak ada duplikat (hospital_id, tanggal) pada health_aq_daily", not health.duplicated(["hospital_id", "date"]).any())
    cek("Semua jam berada di dalam periode 2024-01-01…2026-10-14 23:00", hourly["jam"].between(cfg.WINDOW_START, cfg.WINDOW_END).all())
    cek("Semua jam tepat di awal jam (menit=detik=0)", ((hourly["jam"].dt.minute == 0) & (hourly["jam"].dt.second == 0) & (hourly["jam"].dt.microsecond == 0)).all())
    neg = {c: int((hourly[c] < 0).sum()) for c in POLUTAN_KOL}
    cek("Semua polutan (PM, SO2, CO, O3, NO2) ≥ 0 di aq_hourly", sum(neg.values()) == 0, str(neg))
    negd = {c: int((daily[c] < 0).sum()) for c in POLUTAN_KOL}
    cek("Semua polutan ≥ 0 di aq_daily", sum(negd.values()) == 0, str(negd))
    cek("Satuan seragam: semua kolom polutan berakhiran _ug_m3, tidak ada _ppm",
        all(c in hourly.columns for c in POLUTAN_KOL) and not any(c.endswith("_ppm") for c in hourly.columns) and not any(c.endswith("_ppm") for c in daily.columns))
    cek("Cuaca dalam batas fisik", all(hourly[c].dropna().between(*cfg.BATAS_CUACA[c]).all() for c in cfg.BATAS_CUACA))
    cek("Tidak ada nilai sentinel tersisa (selain CO=999 yang wajar)", not hourly[[c for c in POLUTAN_KOL if c != "co_ug_m3"]].isin(cfg.SENTINEL).any().any() and not hourly[cfg.CUACA].isin([-9999.0, 9999.0, 99999.0]).any().any())
    ok_hari = (daily.loc[daily["pm25_ug_m3"].notna(), "n_jam_pm25"] >= cfg.MIN_JAM_HARIAN).all()
    cek(f"Rata-rata harian PM2.5 hanya bila ≥ {cfg.MIN_JAM_HARIAN} jam valid", ok_hari)
    cek("Setiap stasiun memiliki 1.018 baris kalender di aq_daily", (daily.groupby("kode_stasiun", observed=True).size() == len(pd.date_range(cfg.WINDOW_START.normalize(), cfg.WINDOW_END.normalize()))).all())
    cek("pm25_lag0 sama dengan PM2.5 harian stasiun pasangan", True if health["pm25_lag0"].notna().sum() == 0 else bool(
        health.merge(daily[["kode_stasiun", "tanggal", "pm25_ug_m3"]].assign(kode_stasiun=lambda d: d.kode_stasiun.astype(str)), left_on=["kode_stasiun", "date"], right_on=["kode_stasiun", "tanggal"])
        .eval("pm25_lag0 == pm25_ug_m3 or (pm25_lag0.isna() and pm25_ug_m3.isna())").all()))
    cek("Kasus kesehatan bilangan bulat ≥ 0", all((health[c].dropna() >= 0).all() for c in KASUS))
    cek("Tanggal kesehatan dalam periode AQMS", health["date"].between(cfg.WINDOW_START.normalize(), cfg.WINDOW_END.normalize()).all())
    cek("27 RS × 1.018 hari = 27.486 baris kesehatan", len(health) == 27 * 1018, str(len(health)))
    cek("Stasiun berstatus Dikecualikan tidak ada di aq_hourly/aq_daily",
        set(qc.loc[qc.status_analisis == "Dikecualikan", "kode_stasiun"]).isdisjoint(set(k)) and set(qc.loc[qc.status_analisis == "Dikecualikan", "kode_stasiun"]).isdisjoint(set(daily.kode_stasiun.astype(str))))
    # puncak kabut asap asli tidak hilang: jumlah jam PM>500 = baris VALID PM>500 (stasiun tanpa agregasi multi-baris)
    simpan = hourly.groupby("kode_stasiun", observed=True)["pm_ekstrem"].sum().rename("jam_ekstrem")
    banding = qc.set_index("kode_stasiun").join(simpan, how="inner")
    tanpa_agregasi = banding[banding["n_jam_diagregasi"] == 0]
    cek("Puncak PM>500 pada baris VALID dipertahankan (jam ekstrem = baris ekstrem, stasiun tanpa agregasi)", (tanpa_agregasi["jam_ekstrem"] == tanpa_agregasi["n_ekstrem_valid"]).all(),
        f"{int(tanpa_agregasi['jam_ekstrem'].sum())} jam pada {len(tanpa_agregasi)} stasiun")
    mx = hourly[hourly["kode_stasiun"] == "KTG-01"]["pm25_ug_m3"].max() if (hourly["kode_stasiun"] == "KTG-01").any() else np.nan
    cek("Puncak PM2.5 KTG-01 > 1000 µg/m³ masih ada", mx > 1000, f"maks {mx:.1f}")
    vs = validasi_satuan(hourly, sites, qc)
    cek("Median stasiun ppm setelah konversi sebanding stasiun sejenis (rasio 1/4–4, semua polutan)", vs["rasio"].between(0.25, 4.0).all(),
        f"rasio {vs['rasio'].min():.2f}–{vs['rasio'].max():.2f}")
    cek("PM2.5 stasiun ppm sebanding baseline_pm25 (rasio 0,5–2)", vs["rasio_vs_baseline"].dropna().between(0.5, 2.0).all(),
        f"rasio {vs['rasio_vs_baseline'].min():.2f}–{vs['rasio_vs_baseline'].max():.2f}")
    t = pd.DataFrame(hasil)
    if not lanjut_jika_gagal and not t["lulus"].all():
        raise AssertionError("Validasi gagal:\n" + t[~t["lulus"]].to_string())
    return t


# =========================================================================== #
# Orkestrasi & penulisan
# =========================================================================== #
def jalankan_pipeline(raw_dir=cfg.RAW_DIR, verbose: bool = True) -> dict:
    """Jalankan langkah 1–8 dan kembalikan semua tabel (tanpa menulis berkas)."""
    log = LogPreprocessing()
    sites = bangun_sites_clean(raw_dir)
    kat = katalog_file(raw_dir).query("tabel == 'aqms'").set_index("kode_stasiun")
    hasil, jam_list = {}, []
    for kode in sites["kode_stasiun"]:
        r = bersihkan_stasiun(kat.loc[kode, "path"], kode, log)
        hasil[kode] = r
        jam_list.append(r["jam"])
        if verbose:
            print(f"  {kode}: {r['n_mentah']:>6} baris mentah -> {len(r['jam']):>6} jam (VALID)")
    jam_all = pd.concat(jam_list, ignore_index=True)

    # status analisis dari jam PM2.5 valid; stasiun 'Dikecualikan' keluar dari tabel analisis
    qc0 = ringkas_qc(sites, hasil, jam_all, None)
    dikecualikan = qc0.loc[qc0.status_analisis == "Dikecualikan", "kode_stasiun"].tolist()
    for k in dikecualikan:
        log.add(5, k, "stasiun_dikecualikan_dari_tabel_analisis", len(hasil[k]["jam"]), "jam", CATATAN_STASIUN.get(k, "Jam valid < 10%"), sebelum=len(hasil[k]["jam"]), sesudah=0)
    hourly = jam_all[~jam_all["kode_stasiun"].isin(dikecualikan)].reset_index(drop=True)
    hourly = fitur_jam(hourly, sites)
    for k, x in hourly.groupby("kode_stasiun", observed=True):
        log.add(7, k, "fitur_waktu_dan_lokasi_ditambahkan", len(x), "jam", "tahun, bulan, hari, akhir_pekan, musim (kemarau Mei–Okt), jam_wib, jam_lokal, pulau, kelompok_lokasi, pm_ekstrem")

    aktif = [k for k in sites["kode_stasiun"] if k not in dikecualikan]
    daily = agregasi_harian(hourly, aktif, log)
    daily = fitur_harian(daily, sites, log)
    qc = ringkas_qc(sites, hasil, jam_all, daily)
    for _, r in qc.iterrows():
        cak = r["cakupan_terendah_persen"]
        log.add(8, r["kode_stasiun"], "status_analisis", None, "label",
                f"{r['status_analisis']}: cakupan terendah {cak:.1f}% (jam {r['persen_jam_pm25_valid']:.1f}%, hari {r['persen_hari_pm25_valid']:.1f}%, "
                f"hari kemarau {r['persen_hari_pm25_valid_kemarau']:.1f}%). Layak ≥75%; Terbatas <75%; Dikecualikan bila jam valid <10%")
    health = gabung_kesehatan(daily, sites, qc, log, raw_dir)

    s2 = sites.merge(qc[["kode_stasiun", "status_analisis", "persen_jam_pm25_valid", "catatan"]], on="kode_stasiun", how="left")
    s2["dipakai_di_aq_hourly_daily"] = ~s2["kode_stasiun"].isin(dikecualikan)
    log.add(8, "sites", "baris_sites_clean", len(s2), "stasiun", "sites + sensors + hospitals digabung 1 baris per stasiun (kunci location_id, sensor_id, hospital_id)", sebelum=27, sesudah=len(s2))

    # statistik PM2.5 sebelum/sesudah untuk grafik
    st_sebelum = pd.DataFrame([dict(kode_stasiun=k, tahap="sebelum", **r["stat_pm25_sebelum"]) for k, r in hasil.items()])
    st_sesudah = []
    for k, x in hourly.groupby("kode_stasiun", observed=True):
        st_sesudah.append(dict(kode_stasiun=str(k), tahap="sesudah", **_stat_ringkas(x["pm25_ug_m3"])))
    stat = pd.concat([st_sebelum, pd.DataFrame(st_sesudah)], ignore_index=True)

    validasi = validasi_output(hourly, daily, health, s2, qc)
    return dict(hourly=hourly, daily=daily, health=health, sites=s2, qc=qc, log=log.frame(), stat_pm25=stat, validasi=validasi,
                validasi_satuan=validasi_satuan(hourly, s2, qc), dikecualikan=dikecualikan)


def tulis_keluaran(res: dict, proc_dir=cfg.PROC_DIR, reports_dir=cfg.REPORTS_DIR) -> dict[str, Path]:
    """Tulis semua keluaran ke data/processed/ (parquet) dan reports/ (CSV log)."""
    proc_dir, reports_dir = Path(proc_dir), Path(reports_dir)
    proc_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    p = {
        "aq_hourly": proc_dir / "aq_hourly.parquet", "aq_daily": proc_dir / "aq_daily.parquet",
        "health_aq_daily": proc_dir / "health_aq_daily.parquet", "sites_clean": proc_dir / "sites_clean.parquet",
        "qc_summary": proc_dir / "qc_summary.parquet", "preprocessing_stat_pm25": proc_dir / "preprocessing_stat_pm25.parquet",
        "preprocessing_validasi": proc_dir / "preprocessing_validasi.parquet", "preprocessing_validasi_satuan": proc_dir / "preprocessing_validasi_satuan.parquet",
        "preprocessing_log": reports_dir / "preprocessing_log.csv",
    }
    res["hourly"].to_parquet(p["aq_hourly"], index=False)
    res["daily"].to_parquet(p["aq_daily"], index=False)
    res["health"].to_parquet(p["health_aq_daily"], index=False)
    res["sites"].to_parquet(p["sites_clean"], index=False)
    res["qc"].to_parquet(p["qc_summary"], index=False)
    res["stat_pm25"].to_parquet(p["preprocessing_stat_pm25"], index=False)
    res["validasi"].to_parquet(p["preprocessing_validasi"], index=False)
    res["validasi_satuan"].to_parquet(p["preprocessing_validasi_satuan"], index=False)
    res["log"].to_csv(p["preprocessing_log"], index=False, encoding="utf-8-sig")
    return p
