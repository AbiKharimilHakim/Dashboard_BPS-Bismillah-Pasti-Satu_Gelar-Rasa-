"""Fungsi pendukung Data Understanding (notebook 02).

Prinsip: modul ini HANYA MENGUKUR dan MENDOKUMENTASIKAN kondisi data mentah.
Tidak ada data yang diubah, dibersihkan, atau ditulis ulang ke data/raw/.
Semua nilai dibaca sebagai teks (dtype=str) agar teks galat, string kosong,
dan format timestamp aneh tidak hilang saat dibaca.

Urutan bagian:
  1. Katalog & inventaris file
  2. Kamus data
  3. Relasi antar tabel
  4. Profil kualitas per stasiun (AQMS)
  5. Verifikasi hipotesis satuan ppm & pemeriksaan silang
  6. Profil data kesehatan
  7. Daftar masalah kualitas data
  8. Fungsi visual
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import config as cfg
from . import style

TOKEN_KOSONG = {"", "nan", "null", "none", "n/a", "na", "-", "--"}
KOLOM_NUMERIK_AQMS = [f"{p}" for p in cfg.POLUTAN] + cfg.CUACA


# =========================================================================== #
# 0. Utilitas dasar
# =========================================================================== #
def baca_mentah(path) -> pd.DataFrame:
    """Baca CSV sebagai teks apa adanya (tanpa konversi tipe / NaN otomatis)."""
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig", low_memory=False)


def deteksi_satuan(kolom) -> str:
    """Satuan polutan dari akhiran nama kolom: 'ug/m3', 'ppm', atau '-'."""
    kolom = list(kolom)
    if any(c.endswith("_ug_m3") for c in kolom):
        return "ug/m3"
    if any(c.endswith("_ppm") for c in kolom):
        return "ppm"
    return "-"


def kolom_numerik_aqms(kolom) -> list[str]:
    """Daftar kolom numerik aktual (nama sesuai satuan file) untuk satu file AQMS."""
    hasil = []
    for c in kolom:
        if c in cfg.CUACA or any(c in (f"{p}_ug_m3", f"{p}_ppm") for p in cfg.POLUTAN):
            hasil.append(c)
    return hasil


def nama_kanonik(kolom: str) -> str:
    """'pm25_ppm' / 'pm25_ug_m3' -> 'pm25'; kolom cuaca tidak berubah."""
    for p in cfg.POLUTAN:
        if kolom in (f"{p}_ug_m3", f"{p}_ppm"):
            return p
    return kolom


def faktor_ke_ugm3(polutan: str, satuan: str) -> float:
    """Faktor pengali HIPOTESIS dari satuan label file ke ug/m3.

    - PM dalam 'ppm' : x1000 (hipotesis: nilai sebenarnya mg/m3 yang salah label).
    - Gas dalam 'ppm': ppm x BM / 24,45 x 1000.
    Dipakai hanya untuk perbandingan skala saat profiling, bukan pembersihan.
    """
    if satuan != "ppm" or polutan not in cfg.POLUTAN:
        return 1.0
    if polutan in ("pm25", "pm10"):
        return 1000.0
    return cfg.BERAT_MOLEKUL[polutan] / cfg.VOLUME_MOLAR * 1000.0


def klasifikasi_nilai(s: pd.Series):
    """Pisahkan nilai teks menjadi (angka, kosong, teks).

    kosong : string kosong / token 'NaN', 'null', dst.
    teks   : bukan kosong tetapi tidak bisa dibaca sebagai angka berhingga
             (mis. '0xDEADBEEF', 'ERR_COMM_TIMEOUT', '#VALUE!').
    """
    st = s.str.strip()
    kosong = st.str.lower().isin(TOKEN_KOSONG)
    angka = pd.to_numeric(st.where(~kosong), errors="coerce")
    angka = angka.where(np.isfinite(angka))
    teks = ~kosong & angka.isna()
    return angka, kosong, teks


def jenis_token(token: str) -> str:
    """Kelompokkan teks galat pada kolom numerik menurut asalnya (untuk laporan)."""
    u = str(token).strip().upper()
    if u.startswith("0X"):
        return "kode heksadesimal (isi memori)"
    if u.startswith("#"):
        return "galat formula spreadsheet"
    if u in {"INF", "-INF", "INFINITY"}:
        return "nilai tak hingga"
    if "NULL" in u:
        return "byte kosong/null"
    if any(k in u for k in ("ADC", "VOLT", "BURNOUT", "TAPE")):
        return "galat perangkat keras sensor"
    if any(k in u for k in ("COMM", "TIMEOUT", "CHECKSUM")):
        return "galat komunikasi/integritas data"
    if u.startswith("ERR"):
        return "kode galat umum"
    return "teks lain"


def _norm(s) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def _norm_wilayah(s) -> str:
    x = str(s).lower()
    for k in ("kota", "kabupaten", "kab.", "administrasi", "kab "):
        x = x.replace(k, "")
    return re.sub(r"[^a-z0-9]", "", x)


# =========================================================================== #
# 1. Katalog & inventaris
# =========================================================================== #
def katalog_file(raw_dir=cfg.RAW_DIR) -> pd.DataFrame:
    """Daftar seluruh CSV di data/raw/ (termasuk metadata/) beserta kelompoknya."""
    baris = []
    for p in sorted(Path(raw_dir).rglob("*.csv")):
        n = p.name
        kode = None
        if n.endswith("_AQMS.csv"):
            kel, tabel = "Udara (AQMS)", "aqms"
            m = re.match(r"^([A-Z0-9]{3}-\d{2})", n)
            kode = m.group(1) if m else None
        elif n.startswith("HLT-"):
            kel, tabel = "Kesehatan", "kesehatan"
        elif p.parent.name == "metadata":
            kel, tabel = "Metadata", p.stem
        else:
            kel, tabel = "Tabel master", p.stem
        baris.append(dict(file=n, path=str(p), kelompok=kel, tabel=tabel, kode_stasiun=kode))
    return pd.DataFrame(baris)


def inventaris(raw_dir=cfg.RAW_DIR):
    """Inventaris semua file: baris, kolom, tipe data terbaca, rentang waktu, satuan.

    Return (DataFrame inventaris, dict detail per file untuk kamus data).
    """
    kat = katalog_file(raw_dir)
    baris, detail = [], {}
    for r in kat.itertuples():
        raw = baca_mentah(r.path)
        tipe = pd.read_csv(r.path, low_memory=False, encoding="utf-8-sig")
        dtypes = {c: str(t) for c, t in tipe.dtypes.items()}
        ringkas_dtype = ", ".join(f"{k}×{v}" for k, v in Counter(dtypes.values()).items())

        # kolom yang seharusnya numerik tetapi terbaca sebagai teks (objek)
        if r.tabel == "aqms":
            harap_num = kolom_numerik_aqms(raw.columns)
        elif r.tabel == "kesehatan":
            harap_num = [c for c in raw.columns if c not in ("date", "hospital_id", "dow")]
        else:
            harap_num = []
        num_jadi_teks = [c for c in harap_num if dtypes.get(c) == "object"]

        awal = akhir = None
        if r.tabel == "aqms":
            ts = pd.to_datetime(raw["timestamp_start"], format="mixed", errors="coerce")
            awal, akhir = ts.min(), ts.max()
        elif r.tabel == "kesehatan":
            d = pd.to_datetime(raw["date"], errors="coerce")
            awal, akhir = d.min(), d.max()
        elif r.tabel == "metadata_dates":
            awal = pd.to_datetime(raw["date_start"], errors="coerce").min()
            akhir = pd.to_datetime(raw["date_end"], errors="coerce").max()
        elif r.tabel == "sensors":
            awal = pd.to_datetime(raw["tanggal_instalasi"], errors="coerce").min()
            akhir = pd.to_datetime(raw["tanggal_instalasi"], errors="coerce").max()

        if r.tabel == "aqms":
            satuan = deteksi_satuan(raw.columns)
        elif r.tabel == "sites":
            satuan = "pm25_unit: " + ", ".join(sorted(raw["pm25_unit"].unique()))
        elif r.tabel == "kesehatan":
            satuan = "jumlah kasus; °C; %"
        else:
            satuan = "-"

        contoh = {}
        for c in raw.columns:
            nonkosong = raw[c][~raw[c].str.strip().str.lower().isin(TOKEN_KOSONG)]
            contoh[c] = nonkosong.iloc[0] if len(nonkosong) else ""

        baris.append(dict(
            file=r.file, kelompok=r.kelompok, tabel=r.tabel, kode_stasiun=r.kode_stasiun,
            n_baris=len(raw), n_kolom=raw.shape[1], tipe_data_terbaca=ringkas_dtype,
            kolom_numerik_terbaca_teks=", ".join(num_jadi_teks) if num_jadi_teks else "",
            waktu_awal=awal, waktu_akhir=akhir, satuan=satuan,
            ukuran_mb=round(Path(r.path).stat().st_size / 1e6, 2),
        ))
        detail[r.file] = dict(tabel=r.tabel, kolom=list(raw.columns), dtype=dtypes, contoh=contoh)
    return pd.DataFrame(baris), detail


# =========================================================================== #
# 2. Kamus data
# =========================================================================== #
_D_AQMS = {
    "measurement_id": "ID unik baris pengukuran",
    "sensor_id": "ID sensor/stasiun yang merekam (relasi ke sensors.csv)",
    "timestamp_start": "Awal jendela pengukuran (WIB)",
    "timestamp_end": "Akhir jendela pengukuran (WIB)",
    "pm25": "Partikel halus PM2.5 (diameter < 2,5 µm)",
    "pm10": "Partikel PM10 (diameter < 10 µm)",
    "so2": "Sulfur dioksida (SO2)",
    "co": "Karbon monoksida (CO)",
    "o3": "Ozon permukaan (O3)",
    "no2": "Nitrogen dioksida (NO2)",
    "temperature_c": "Suhu udara permukaan",
    "humidity_pct": "Kelembapan relatif udara",
    "wind_speed_ms": "Kecepatan angin",
    "wind_direction_deg": "Arah ASAL angin (0–360°)",
    "qc_flag": "Penanda kualitas data dari alat (QC engine)",
}
_D_SITES = {
    "location_id": "Kode unik lokasi pemantauan", "provinsi": "Provinsi lokasi",
    "kota_kabupaten": "Kota/kabupaten lokasi", "kecamatan": "Kecamatan lokasi",
    "karakteristik_wilayah": "Deskripsi karakter wilayah sekitar stasiun",
    "latitude_dd": "Lintang stasiun (derajat desimal)", "longitude_dd": "Bujur stasiun (derajat desimal)",
    "baseline_pm25": "Konsentrasi dasar PM2.5 lokasi (acuan kondisi wilayah)",
    "region_group": "Pengelompokan wilayah untuk analisis regional", "station_code": "Kode stasiun AQMS",
    "site_type": "Klasifikasi tipe lokasi (latar kota, tepi jalan, industri, gambut, dst.)",
    "distance_to_road_m": "Jarak stasiun ke jalan raya terdekat", "traffic_intensity_per_h": "Perkiraan kendaraan melintas per jam",
    "notes": "Catatan singkat konteks stasiun",
}
for _p in cfg.POLUTAN:
    _D_SITES[f"{_p}_equipment"] = f"Alat ukur parameter {_p.upper()}"
    _D_SITES[f"{_p}_unit"] = f"Satuan hasil ukur {_p.upper()} pada data logger stasiun"
_D_SITES["meteo_equipment"] = "Alat ukur meteorologi"
_D_SENSORS = {
    "sensor_id": "Kode unik sensor", "location_id": "Kode lokasi pemasangan (relasi ke sites.csv)",
    "nama_sensor": "Nama stasiun pemantau", "model_sensor": "Merek & model instrumen",
    "tipe_pemasangan": "Jenis & konfigurasi pemasangan (termasuk ketinggian)",
    "latitude": "Lintang sensor (derajat desimal)", "longitude": "Bujur sensor (derajat desimal)",
    "status_operasional": "Status operasi perangkat saat ini", "tanggal_instalasi": "Tanggal perangkat mulai dipasang",
    "region_group": "Pengelompokan wilayah untuk analisis regional",
}
_D_HOSP = {
    "hospital_id": "Kode unik RS rujukan (anonim)", "nama_rumah_sakit": "Nama RS (anonim)",
    "kota_kabupaten": "Kota/kabupaten RS", "kecamatan": "Kecamatan RS", "provinsi": "Provinsi RS",
    "kelas_faskes": "Kelas fasilitas kesehatan", "kapasitas_tempat_tidur": "Jumlah tempat tidur rawat inap (dapat kosong)",
}
_D_HLT = {
    "date": "Tanggal pencatatan harian", "time": "Nomor urut hari sejak awal pengamatan",
    "hospital_id": "Kode RS rujukan (relasi ke hospitals.csv)", "dow": "Nama hari dalam seminggu",
    "temp_c": "Suhu udara harian", "dptp_c": "Suhu titik embun harian", "rhum_pct": "Kelembapan relatif harian",
    "resp_admissions_under5": "Rawat inap gangguan pernapasan (ISPA) balita < 5 tahun",
    "resp_admissions_over60": "Rawat inap gangguan pernapasan (ISPA) lansia > 60 tahun",
    "asthma_emergency_cases": "Kasus darurat asma", "copd_admissions": "Rawat inap PPOK",
    "resp": "Kasus rawat pernapasan umum", "cvd": "Kasus penyakit kardiovaskular", "death": "Jumlah kematian",
}
_D_MSENS = {
    "Supplier": "Produsen/penyedia instrumen", "Sensors": "Model/seri instrumen", "Type": "Teknologi pengukuran",
    "Parameters": "Parameter yang diukur", "Header": "Nama kolom parameter pada file AQMS",
    "Units": "Satuan hasil ukur (standar vs ekspor logger)",
}
_D_MDATE = {
    "location_id": "Kode lokasi (relasi ke sites.csv)", "city": "Nama kota/wilayah pemantauan",
    "date_start": "Awal periode observasi stasiun", "date_end": "Akhir periode observasi stasiun",
    "nominal_resolution": "Resolusi waktu nominal", "notes": "Catatan mode perekaman telemetri",
}
DESKRIPSI = {"aqms": _D_AQMS, "sites": _D_SITES, "sensors": _D_SENSORS, "hospitals": _D_HOSP,
             "kesehatan": _D_HLT, "metadata_sensors": _D_MSENS, "metadata_dates": _D_MDATE}

_KOL_TEKS = {
    "sites": {"location_id", "provinsi", "kota_kabupaten", "kecamatan", "karakteristik_wilayah", "region_group",
              "station_code", "site_type", "notes", "meteo_equipment"} | {f"{p}_{s}" for p in cfg.POLUTAN for s in ("equipment", "unit")},
    "sensors": {"sensor_id", "location_id", "nama_sensor", "model_sensor", "tipe_pemasangan", "status_operasional", "region_group"},
    "hospitals": {"hospital_id", "nama_rumah_sakit", "kota_kabupaten", "kecamatan", "provinsi", "kelas_faskes"},
    "kesehatan": {"hospital_id", "dow"},
    "metadata_dates": {"location_id", "city", "nominal_resolution", "notes"},
}
_KOL_TANGGAL = {"aqms": {"timestamp_start", "timestamp_end"}, "kesehatan": {"date"},
                "sensors": {"tanggal_instalasi"}, "metadata_dates": {"date_start", "date_end"}}
_KOL_BULAT = {"kesehatan": {"time", "resp_admissions_under5", "resp_admissions_over60", "asthma_emergency_cases",
                            "copd_admissions", "resp", "cvd", "death"}}


def _satuan_kolom(tabel: str, kolom: str) -> str:
    if tabel == "aqms":
        if kolom.endswith("_ug_m3"):
            return "µg/m³"
        if kolom.endswith("_ppm"):
            return "ppm (sesuai label header; lihat verifikasi)"
        return {"temperature_c": "°C", "humidity_pct": "%", "wind_speed_ms": "m/s", "wind_direction_deg": "derajat"}.get(kolom, "-")
    if tabel == "sites":
        return {"latitude_dd": "derajat", "longitude_dd": "derajat", "baseline_pm25": "µg/m³",
                "distance_to_road_m": "m", "traffic_intensity_per_h": "kendaraan/jam"}.get(kolom, "-")
    if tabel == "sensors":
        return "derajat" if kolom in ("latitude", "longitude") else "-"
    if tabel == "hospitals":
        return "tempat tidur" if kolom == "kapasitas_tempat_tidur" else "-"
    if tabel == "kesehatan":
        if kolom in ("temp_c", "dptp_c"):
            return "°C"
        if kolom == "rhum_pct":
            return "%"
        if kolom in _KOL_BULAT["kesehatan"] and kolom != "time":
            return "kasus/hari"
        return "hari ke-" if kolom == "time" else "-"
    return "-"


def _tipe_konseptual(tabel: str, kolom: str) -> str:
    if kolom in ("measurement_id",) or kolom.endswith("_id"):
        return "teks (ID)"
    if kolom in _KOL_TANGGAL.get(tabel, set()):
        return "tanggal/waktu"
    if kolom == "qc_flag":
        return "kategorikal"
    if kolom in _KOL_TEKS.get(tabel, set()):
        return "teks/kategorikal"
    if tabel == "metadata_sensors":
        return "teks/kategorikal"
    if kolom in _KOL_BULAT.get(tabel, set()):
        return "bilangan bulat (tersimpan sebagai desimal)" if tabel == "kesehatan" else "bilangan bulat"
    return "numerik (desimal)"


def kamus_data(detail: dict) -> pd.DataFrame:
    """Kamus data gabungan dari `detail` hasil `inventaris`.

    27 file AQMS digabung menjadi satu tabel logis 'aqms'; kolom yang hanya muncul
    di sebagian file (varian *_ppm) dicatat jumlah file pemuatnya.
    """
    per_tabel: dict[str, dict] = {}
    for fn, d in detail.items():
        t = per_tabel.setdefault(d["tabel"], dict(files=[], kolom={}))
        t["files"].append(fn)
        for c in d["kolom"]:
            info = t["kolom"].setdefault(c, dict(n_file=0, dtypes=Counter(), contoh=""))
            info["n_file"] += 1
            info["dtypes"][d["dtype"].get(c, "?")] += 1
            if not info["contoh"] and d["contoh"].get(c):
                info["contoh"] = d["contoh"][c]
    baris = []
    for tabel, t in per_tabel.items():
        n_files = len(t["files"])
        for kolom, info in t["kolom"].items():
            kanon = nama_kanonik(kolom) if tabel == "aqms" else kolom
            desk = DESKRIPSI.get(tabel, {}).get(kanon, "")
            catatan = []
            if tabel == "aqms" and info["n_file"] != n_files:
                catatan.append(f"hanya ada di {info['n_file']} dari {n_files} file")
            if len(info["dtypes"]) > 1:
                catatan.append("tipe terbaca tidak seragam antar-file: " + ", ".join(f"{k}×{v}" for k, v in info["dtypes"].items()))
            tabel_label = {"aqms": "AQMS (27 file)"}.get(tabel, t["files"][0])
            baris.append(dict(
                tabel=tabel_label, kolom=kolom, tipe_konseptual=_tipe_konseptual(tabel, kanon if tabel == "aqms" else kolom),
                tipe_pandas=info["dtypes"].most_common(1)[0][0], satuan=_satuan_kolom(tabel, kolom),
                deskripsi=desk, contoh_nilai=info["contoh"], jumlah_file=info["n_file"], catatan="; ".join(catatan),
            ))
    return pd.DataFrame(baris)


# =========================================================================== #
# 3. Relasi antar tabel
# =========================================================================== #
def muat_master(raw_dir=cfg.RAW_DIR) -> dict[str, pd.DataFrame]:
    raw_dir = Path(raw_dir)
    return dict(
        sites=pd.read_csv(raw_dir / "sites.csv"),
        sensors=pd.read_csv(raw_dir / "sensors.csv"),
        hospitals=pd.read_csv(raw_dir / "hospitals.csv"),
        metadata_dates=pd.read_csv(raw_dir / "metadata" / "metadata_dates.csv"),
        metadata_sensors=pd.read_csv(raw_dir / "metadata" / "metadata_sensors.csv"),
    )


def _cek(kode, nama, jumlah_salah, detail="", info=False):
    status = "INFO" if info else ("OK" if jumlah_salah == 0 else "MASALAH")
    return dict(kode=kode, pemeriksaan=nama, status=status, jumlah_tidak_cocok=jumlah_salah, detail=detail)


def cek_relasi(raw_dir=cfg.RAW_DIR, ringkasan: pd.DataFrame | None = None):
    """Periksa kecocokan kunci stasiun–sensor–lokasi–RS.

    Return (tabel_pemeriksaan, tabel_pasangan_27_stasiun).
    `ringkasan` (hasil profil_semua_stasiun) opsional: dipakai untuk memeriksa
    metadata_dates terhadap rentang waktu aktual.
    """
    raw_dir = Path(raw_dir)
    m = muat_master(raw_dir)
    sites, sensors, hosp, mdate = m["sites"], m["sensors"], m["hospitals"], m["metadata_dates"]
    kat = katalog_file(raw_dir)
    aq = kat[kat.tabel == "aqms"].copy()

    sensor_per_file = {r.kode_stasiun: sorted(pd.read_csv(r.path, usecols=["sensor_id"], dtype=str)["sensor_id"].unique())
                       for r in aq.itertuples()}
    hid_kes = set(pd.read_csv(raw_dir / "HLT-01_health_outcomes_daily.csv", usecols=["hospital_id"], dtype=str)["hospital_id"])

    c = []
    c.append(_cek("R01", "sites.location_id unik", int(sites.location_id.duplicated().sum())))
    c.append(_cek("R02", "sensors.sensor_id unik", int(sensors.sensor_id.duplicated().sum())))
    c.append(_cek("R03", "hospitals.hospital_id unik", int(hosp.hospital_id.duplicated().sum())))
    s_tak = sorted(set(sensors.location_id) - set(sites.location_id))
    c.append(_cek("R04", "sensors.location_id ada di sites.location_id", len(s_tak), ", ".join(s_tak)))
    l_tak = sorted(set(sites.location_id) - set(sensors.location_id))
    c.append(_cek("R05", "setiap lokasi di sites.csv punya sensor", len(l_tak), ", ".join(l_tak)))
    md_tak = sorted(set(mdate.location_id) ^ set(sites.location_id))
    c.append(_cek("R06", "metadata_dates.location_id sama dengan sites.location_id", len(md_tak), ", ".join(md_tak)))

    banyak = {k: v for k, v in sensor_per_file.items() if len(v) != 1}
    c.append(_cek("R07", "tiap file AQMS memuat tepat 1 sensor_id", len(banyak), str(banyak)))
    sid_set = set(sensors.sensor_id)
    asing = {k: v for k, v in sensor_per_file.items() if not set(v) <= sid_set}
    c.append(_cek("R08", "sensor_id di file AQMS terdaftar di sensors.csv", len(asing), str(asing)))

    sens_by_loc = sensors.set_index("location_id").sensor_id.to_dict()
    salah_kode = []
    for kode, ids in sensor_per_file.items():
        harap = sens_by_loc.get(f"LOC-{kode}")
        if harap is None or ids != [harap]:
            salah_kode.append(f"{kode}: file={ids} vs sensors.csv={harap}")
    c.append(_cek("R09", "kode di nama file (LOC-<kode>) cocok dengan sensor_id di dalam file", len(salah_kode), " | ".join(salah_kode)))
    dobel = sorted(k for k, v in Counter(sum(sensor_per_file.values(), [])).items() if v > 1)
    c.append(_cek("R10", "tidak ada sensor_id yang dipakai dua file", len(dobel), ", ".join(dobel)))

    kes_tak = sorted(hid_kes - set(hosp.hospital_id))
    c.append(_cek("R11", "hospital_id di data kesehatan terdaftar di hospitals.csv", len(kes_tak), ", ".join(kes_tak)))
    rs_tak = sorted(set(hosp.hospital_id) - hid_kes)
    c.append(_cek("R12", "setiap RS di hospitals.csv punya data kesehatan", len(rs_tak), ", ".join(rs_tak)))

    # koordinat & atribut konsisten sites <-> sensors
    sj = sensors.merge(sites, on="location_id", how="left", suffixes=("_s", "_l"))
    koord = sj[(sj.latitude - sj.latitude_dd).abs().gt(1e-6) | (sj.longitude - sj.longitude_dd).abs().gt(1e-6)]
    c.append(_cek("R13", "koordinat sensors.csv = sites.csv", len(koord), ", ".join(koord.location_id)))
    rg = sj[sj.region_group_s != sj.region_group_l]
    c.append(_cek("R14", "region_group sensors.csv = sites.csv", len(rg),
                  "; ".join(f"{r.location_id}: {r.region_group_s}≠{r.region_group_l}" for r in rg.itertuples())))
    sc = sites[sites.station_code != ("AQMS-" + sites.location_id.str.replace("LOC-", "", regex=False))]
    c.append(_cek("R15", "station_code = 'AQMS-' + kode lokasi", len(sc), ", ".join(sc.location_id)))

    # satuan di sites.csv vs header file
    unit_file = {r.kode_stasiun: deteksi_satuan(pd.read_csv(r.path, nrows=0).columns) for r in aq.itertuples()}
    su = sites.assign(kode=sites.location_id.str.replace("LOC-", "", regex=False))
    su["unit_file"] = su.kode.map(unit_file)
    beda = su[(su.pm25_unit == "ppm") != (su.unit_file == "ppm")]
    c.append(_cek("R16", "sites.pm25_unit konsisten dengan header file AQMS", len(beda), ", ".join(beda.kode)))
    ppm_sites = su[su.pm25_unit == "ppm"].kode.tolist()
    c.append(_cek("R17", "stasiun berunit ppm (sites.pm25_unit)", len(ppm_sites), ", ".join(ppm_sites), info=True))

    # status sensor & tanggal instalasi
    nonaktif = sensors[sensors.status_operasional != "Active"]
    c.append(_cek("R18", "sensor berstatus selain Active", len(nonaktif),
                  "; ".join(f"{r.sensor_id}({r.location_id.replace('LOC-', '')})={r.status_operasional}" for r in nonaktif.itertuples()), info=True))
    telat = sensors[pd.to_datetime(sensors.tanggal_instalasi) > cfg.WINDOW_START]
    c.append(_cek("R19", "tanggal_instalasi sensor lebih awal dari awal data (2024-01-01)", len(telat), ", ".join(telat.sensor_id)))

    # pasangan stasiun <-> RS (aturan nomor urut)
    sens = sensors.copy()
    sens["nomor"] = sens.sensor_id.str[-3:].astype(int)
    sens["hospital_id"] = sens.nomor.map(lambda n: f"RS-XXX-{n:02d}")
    sens["kode_stasiun"] = sens.location_id.str.replace("LOC-", "", regex=False)
    p = (sens.merge(sites[["location_id", "provinsi", "kota_kabupaten", "kecamatan", "site_type"]], on="location_id", how="left")
         .merge(hosp.rename(columns={"provinsi": "provinsi_rs", "kota_kabupaten": "kota_rs", "kecamatan": "kecamatan_rs"}), on="hospital_id", how="left")
         .merge(aq[["kode_stasiun", "file"]], on="kode_stasiun", how="left"))
    p["provinsi_cocok"] = p.provinsi.map(cfg.normalisasi_provinsi) == p.provinsi_rs.map(cfg.normalisasi_provinsi)
    p["kota_cocok"] = [(_norm_wilayah(a) in _norm_wilayah(b)) or (_norm_wilayah(b) in _norm_wilayah(a))
                       for a, b in zip(p.kota_kabupaten, p.kota_rs)]
    p["kecamatan_cocok"] = [(_norm(a) in _norm(b)) or (_norm(b) in _norm(a))
                            for a, b in zip(p.kecamatan, p.kecamatan_rs)]
    p["rs_ada_di_data_kesehatan"] = p.hospital_id.isin(hid_kes)
    pas = p[["nomor", "kode_stasiun", "location_id", "sensor_id", "file", "hospital_id", "nama_rumah_sakit",
             "provinsi", "provinsi_rs", "kota_kabupaten", "kota_rs", "kecamatan", "kecamatan_rs",
             "provinsi_cocok", "kota_cocok", "kecamatan_cocok", "kelas_faskes", "kapasitas_tempat_tidur",
             "status_operasional", "site_type", "rs_ada_di_data_kesehatan"]].sort_values("nomor").reset_index(drop=True)
    pas["pulau"] = pas.provinsi.map(cfg.pulau_dari_provinsi)
    pas["kelompok_lokasi"] = pas.site_type.map(cfg.kelompok_lokasi)

    c.append(_cek("R20", "pasangan nomor sensor ↔ RS (SENS-0NN ↔ RS-XXX-NN) lengkap 27/27",
                  int(27 - pas.rs_ada_di_data_kesehatan.sum()), "pasangan mengikuti Tabel E booklet"))
    c.append(_cek("R21", "provinsi stasiun = provinsi RS pasangannya", int((~pas.provinsi_cocok).sum()),
                  ", ".join(pas[~pas.provinsi_cocok].kode_stasiun)))
    c.append(_cek("R22", "kota/kabupaten stasiun = kota/kabupaten RS pasangannya (pencocokan longgar)", int((~pas.kota_cocok).sum()),
                  "; ".join(f"{r.kode_stasiun}: {r.kota_kabupaten} vs {r.kota_rs}" for r in pas[~pas.kota_cocok].itertuples())))
    c.append(_cek("R23", "kecamatan stasiun = kecamatan RS pasangannya (pencocokan longgar)", int((~pas.kecamatan_cocok).sum()),
                  "; ".join(f"{r.kode_stasiun}: {r.kecamatan} vs {r.kecamatan_rs}" for r in pas[~pas.kecamatan_cocok].itertuples())))
    tak_pulau = pas[pas.pulau == "Tidak terpetakan"]
    c.append(_cek("R24", "semua provinsi terpetakan ke pulau", len(tak_pulau), ", ".join(tak_pulau.provinsi.unique())))
    lain = pas[pas.kelompok_lokasi == "Lainnya"]
    c.append(_cek("R25", "semua site_type terpetakan ke 5 kelompok lokasi", len(lain), ", ".join(lain.site_type.unique())))

    if ringkasan is not None:
        r = ringkasan.set_index("kode")
        md = mdate.assign(kode=mdate.location_id.str.replace("LOC-", "", regex=False)).set_index("kode")
        beda_akhir = []
        for kode in md.index.intersection(r.index):
            ds, de = pd.Timestamp(md.loc[kode, "date_start"]), pd.Timestamp(md.loc[kode, "date_end"])
            if (ds != cfg.WINDOW_START) or (de != cfg.WINDOW_END):
                beda_akhir.append(kode)
        c.append(_cek("R26", "metadata_dates (awal–akhir) = 2024-01-01 00:00 s.d. 2026-10-14 23:00", len(beda_akhir), ", ".join(beda_akhir)))
        sel = r[r.n_baris != cfg.EXPECTED_HOURS]
        c.append(_cek("R27", f"jumlah baris file = {cfg.EXPECTED_HOURS:,} (sesuai resolusi 1 jam di metadata_dates)".replace(",", "."), len(sel),
                      "; ".join(f"{k}={int(v)}" for k, v in sel.n_baris.items())))
    return pd.DataFrame(c), pas


# =========================================================================== #
# 4. Profil kualitas per stasiun (AQMS)
# =========================================================================== #
def _run_terpanjang(hilang: pd.DatetimeIndex) -> int:
    if len(hilang) == 0:
        return 0
    jam = (hilang.values.astype("datetime64[h]").astype("int64"))
    putus = np.where(np.diff(jam) != 1)[0]
    batas = np.concatenate([[-1], putus, [len(jam) - 1]])
    return int(np.max(np.diff(batas)))


def profil_stasiun(df: pd.DataFrame, kode: str, nama_file: str = ""):
    """Profil kualitas satu stasiun dari DataFrame teks mentah.

    Return dict berisi: ringkasan (dict), kolom (DataFrame), token (DataFrame),
    qc (DataFrame), sentinel_qc (DataFrame), desk (DataFrame), bulanan (DataFrame),
    harian (Series: PM2.5 harian pendekatan, hanya untuk pemeriksaan silang).
    """
    n = len(df)
    satuan = deteksi_satuan(df.columns)
    kolom_num = kolom_numerik_aqms(df.columns)

    # ---- timestamp ----
    ts = pd.to_datetime(df["timestamp_start"], format="mixed", errors="coerce")
    te = pd.to_datetime(df["timestamp_end"], format="mixed", errors="coerce")
    ts_r = ts.dt.round("h")
    offset = (ts - ts.dt.floor("h")).dt.total_seconds()
    geser = np.minimum(offset, 3600 - offset)          # jarak ke jam terdekat (detik)
    bergeser = geser.fillna(0) > 0
    # geseran bertanda (menit): + = lewat dari jam penuh, − = sebelum jam penuh (mis. 23:48 -> −12)
    geser_tanda = (np.where(offset <= 1800, offset, offset - 3600) / 60)
    geser_tanda = pd.Series(geser_tanda, index=df.index).where(offset.notna())
    sebaran_offset = (offset[bergeser] / 60).round().astype("Int64").value_counts().head(4)
    ket_offset = "; ".join(f"+{int(k)} mnt: {int(v)}" for k, v in sebaran_offset.items())
    dalam = (ts_r >= cfg.WINDOW_START) & (ts_r <= cfg.WINDOW_END)
    luar = ts_r.notna() & ~dalam
    durasi = (te - ts).dt.total_seconds()
    subjam = durasi.notna() & (durasi < 3600)      # jendela < 1 jam (mis. logger beresolusi 15 menit)
    sj_awal = ts[subjam].min() if subjam.any() else pd.NaT
    sj_akhir = ts[subjam].max() if subjam.any() else pd.NaT
    n_blok_sj, ket_blok_sj = 0, ""
    if subjam.any():                                   # blok jam berurutan yang memuat baris sub-jam
        jam_sj = ts[subjam].dt.floor("h").drop_duplicates().sort_values()
        blok_sj = jam_sj.groupby((jam_sj.diff() != pd.Timedelta(hours=1)).cumsum()).agg(["min", "max"])
        n_blok_sj = len(blok_sj)
        ket_blok_sj = "; ".join(f"{a:%Y-%m-%d}…{b:%Y-%m-%d}" for a, b in zip(blok_sj["min"], blok_sj["max"]))

    # ---- nilai numerik ----
    angka, kosong, teks = {}, {}, {}
    baris_kolom, baris_token, baris_desk, baris_sent = [], [], [], []
    any_teks = pd.Series(False, index=df.index)
    any_kosong = pd.Series(False, index=df.index)
    any_mustahil = pd.Series(False, index=df.index)
    any_ekstrem = pd.Series(False, index=df.index)
    sent_qc_rows = []
    for col in kolom_num:
        v, k, t = klasifikasi_nilai(df[col])
        kanon = nama_kanonik(col)
        sentinel_aktif = [x for x in cfg.SENTINEL if not (satuan == "ug/m3" and x in cfg.SENTINEL_KECUALI.get(kanon, []))]
        sent = v.isin(sentinel_aktif)
        neg = pd.Series(False, index=df.index)
        luar_r = pd.Series(False, index=df.index)
        if kanon in cfg.POLUTAN:
            neg = (v < 0) & ~sent
        else:
            lo, hi = cfg.BATAS_CUACA[kanon]
            luar_r = ((v < lo) | (v > hi)) & ~sent
        mustahil = sent | neg | luar_r
        faktor = faktor_ke_ugm3(kanon, satuan)
        ekstrem = pd.Series(False, index=df.index)
        if kanon in cfg.BATAS_EKSTREM_PM:
            ekstrem = (v * faktor > cfg.BATAS_EKSTREM_PM[kanon]) & ~mustahil
        angka[kanon], kosong[kanon], teks[kanon] = v, k, t
        any_teks |= t
        any_kosong |= k
        any_mustahil |= mustahil
        any_ekstrem |= ekstrem
        baris_kolom.append(dict(
            kode=kode, kolom=col, n=n, n_kosong=int(k.sum()), n_teks=int(t.sum()), n_numerik=int(v.notna().sum()),
            n_sentinel=int(sent.sum()), n_negatif=int(neg.sum()), n_luar_rentang=int(luar_r.sum()),
            n_mustahil=int(mustahil.sum()), n_ekstrem=int(ekstrem.sum()),
        ))
        for tok, jml in df[col][t].str.strip().value_counts().items():
            baris_token.append(dict(kode=kode, kolom=col, token=tok, n=int(jml)))
        # statistik deskriptif mentah (apa adanya, termasuk nilai sentinel/mustahil)
        vv = v.dropna()
        if len(vv):
            q = vv.quantile([0.01, 0.05, 0.5, 0.95, 0.99])
            baris_desk.append(dict(kode=kode, kolom=col, kanon=kanon, satuan_label=satuan if kanon in cfg.POLUTAN else "-",
                                   n=len(vv), rata2=vv.mean(), sd=vv.std(), min=vv.min(), p01=q.iloc[0], p05=q.iloc[1],
                                   median=q.iloc[2], p95=q.iloc[3], p99=q.iloc[4], maks=vv.max()))
        if sent.any():
            tmp = pd.DataFrame(dict(nilai=v[sent], qc_flag=df.qc_flag[sent]))
            tmp["kolom"] = col
            sent_qc_rows.append(tmp)
        angka[kanon + "__mustahil"] = mustahil

    # ---- QC ----
    qc = df["qc_flag"].str.strip()
    qc_valid = qc.eq("VALID")
    mustahil_by_qc = qc[any_mustahil].value_counts()

    # ---- jam & duplikat ----
    jam_dalam = ts_r[dalam]
    jam_unik = pd.DatetimeIndex(jam_dalam.unique())
    harap = pd.date_range(cfg.WINDOW_START, cfg.WINDOW_END, freq="h")
    hilang = harap.difference(jam_unik)
    pm25_col = [c for c in kolom_num if nama_kanonik(c) == "pm25"][0]
    cnt = jam_dalam.value_counts()
    jam_dup = cnt[cnt > 1].index
    nunik = df.loc[dalam, pm25_col].groupby(jam_dalam).nunique()
    n_konflik = int(((nunik > 1) & nunik.index.isin(jam_dup)).sum())

    # jam "valid": ada >=1 baris qc VALID dengan PM2.5 numerik wajar
    pm25 = angka["pm25"]
    baris_ok = qc_valid & pm25.notna() & ~angka["pm25__mustahil"] & dalam
    jam_valid = pd.DatetimeIndex(ts_r[baris_ok].unique())

    # ---- bulanan ----
    bulan = pd.period_range(cfg.WINDOW_START, cfg.WINDOW_END, freq="M")
    jam_harap_bulan = pd.Series(1, index=harap).groupby(harap.to_period("M")).sum().reindex(bulan, fill_value=0)
    jt = pd.Series(1, index=jam_unik).groupby(jam_unik.to_period("M")).sum().reindex(bulan, fill_value=0)
    jv = pd.Series(1, index=jam_valid).groupby(jam_valid.to_period("M")).sum().reindex(bulan, fill_value=0)
    bulanan = pd.DataFrame(dict(kode=kode, bulan=bulan.to_timestamp(), jam_harap=jam_harap_bulan.values,
                                jam_tercatat=jt.values, jam_valid=jv.values))

    # ---- PM2.5 harian pendekatan (qc VALID, bukan mustahil), unit diseragamkan hipotesis ----
    fak = faktor_ke_ugm3("pm25", satuan)
    per_jam = (pm25[baris_ok] * fak).groupby(ts_r[baris_ok]).mean()
    harian = per_jam.groupby(per_jam.index.floor("D")).agg(["mean", "count"])
    harian = harian["mean"].where(harian["count"] >= 12)
    harian.name = kode

    pm10 = angka["pm10"]
    pm25_gt_pm10 = int(((pm25 > pm10) & ~angka["pm25__mustahil"] & ~angka["pm10__mustahil"]).sum())

    ring = dict(
        kode=kode, file=nama_file, satuan=satuan, n_baris=n, selisih_baris=n - cfg.EXPECTED_HOURS,
        sensor_id=";".join(sorted(df["sensor_id"].unique())),
        ts_tak_terbaca=int(ts.isna().sum()), ts_min_mentah=ts.min(), ts_maks_mentah=ts.max(),
        n_ts_luar_jendela=int(luar.sum()), n_ts_bergeser=int(bergeser.sum()),
        persen_ts_bergeser=round(100 * bergeser.mean(), 2),
        geser_median_menit=round(float(geser_tanda[bergeser].median()), 2) if bergeser.any() else 0.0,
        geser_min_menit=round(float(geser_tanda[bergeser].min()), 2) if bergeser.any() else 0.0,
        geser_maks_menit=round(float(geser_tanda[bergeser].max()), 2) if bergeser.any() else 0.0,
        n_geser_tepat_30menit=int((offset == 1800).sum()), sebaran_offset=ket_offset,
        n_durasi_bukan_1jam=int((durasi.notna() & (durasi != 3600)).sum()),
        n_durasi_subjam=int(subjam.sum()), subjam_awal=sj_awal, subjam_akhir=sj_akhir,
        n_blok_subjam=n_blok_sj, blok_subjam=ket_blok_sj,
        durasi_subjam_menit=(", ".join(str(int(x)) for x in sorted((durasi[subjam] / 60).unique())) if subjam.any() else ""),
        n_jam_unik=len(jam_unik), n_jam_hilang=len(hilang),
        persen_jam_hilang=round(100 * len(hilang) / cfg.EXPECTED_HOURS, 2), gap_terpanjang_jam=_run_terpanjang(hilang),
        n_baris_lebih_per_jam=int(dalam.sum() - len(jam_unik)), n_jam_duplikat=len(jam_dup), n_jam_duplikat_konflik=n_konflik,
        n_ts_duplikat_persis=int(ts.dropna().duplicated().sum()), n_id_duplikat=int(df["measurement_id"].duplicated().sum()),
        n_baris_identik=int(df.drop(columns=["measurement_id"]).duplicated().sum()),
        n_baris_teks=int(any_teks.sum()), n_baris_kosong=int(any_kosong.sum()), n_baris_mustahil=int(any_mustahil.sum()),
        n_baris_ekstrem=int(any_ekstrem.sum()), n_baris_ekstrem_valid=int((any_ekstrem & qc_valid).sum()), n_pm25_gt_pm10=pm25_gt_pm10,
        n_valid=int(qc_valid.sum()), persen_valid=round(100 * qc_valid.mean(), 2),
        n_valid_tapi_mustahil=int((qc_valid & any_mustahil).sum()), n_valid_tapi_kosong=int((qc_valid & any_kosong).sum()),
        n_jam_valid=len(jam_valid), persen_jam_valid=round(100 * len(jam_valid) / cfg.EXPECTED_HOURS, 2),
        n_flag_beragam=int(qc.nunique()), n_flag_nonstandar=int((~qc.isin(cfg.QC_STANDAR)).sum()),
    )
    qc_df = qc.value_counts().rename_axis("qc_flag").reset_index(name="n").assign(kode=kode)
    qc_df["persen"] = (100 * qc_df.n / n).round(2)
    sent_df = (pd.concat(sent_qc_rows).groupby(["kolom", "nilai", "qc_flag"]).size().rename("n").reset_index().assign(kode=kode)
               if sent_qc_rows else pd.DataFrame(columns=["kolom", "nilai", "qc_flag", "n", "kode"]))
    return dict(
        ringkasan=ring, kolom=pd.DataFrame(baris_kolom), token=pd.DataFrame(baris_token), qc=qc_df,
        sentinel_qc=sent_df, desk=pd.DataFrame(baris_desk), bulanan=bulanan, harian=harian,
        mustahil_qc=mustahil_by_qc.rename_axis("qc_flag").reset_index(name="n").assign(kode=kode),
    )


def profil_semua_stasiun(raw_dir=cfg.RAW_DIR, verbose=True):
    """Jalankan `profil_stasiun` untuk seluruh file AQMS dan gabungkan hasilnya."""
    kat = katalog_file(raw_dir)
    kat = kat[kat.tabel == "aqms"]
    hasil = []
    for r in kat.itertuples():
        df = baca_mentah(r.path)
        h = profil_stasiun(df, r.kode_stasiun, r.file)
        hasil.append(h)
        if verbose:
            print(f"  {r.kode_stasiun}: {len(df):>6} baris | VALID {h['ringkasan']['persen_valid']:>6.2f}% | "
                  f"jam hilang {h['ringkasan']['n_jam_hilang']:>5}")
        del df
    gabung = lambda k: pd.concat([h[k] for h in hasil], ignore_index=True)
    return dict(
        ringkasan=pd.DataFrame([h["ringkasan"] for h in hasil]),
        kolom=gabung("kolom"), token=gabung("token"), qc=gabung("qc"), sentinel_qc=gabung("sentinel_qc"),
        desk=gabung("desk"), bulanan=gabung("bulanan"), mustahil_qc=gabung("mustahil_qc"),
        harian=pd.concat([h["harian"] for h in hasil], axis=1),
    )


def periode_subjam(kode: str, raw_dir=cfg.RAW_DIR) -> pd.DataFrame:
    """Blok jam berurutan yang memuat baris berjendela < 1 jam (logger beresolusi lebih halus)."""
    kat = katalog_file(raw_dir)
    path = kat[(kat.tabel == "aqms") & (kat.kode_stasiun == kode)].path.iloc[0]
    df = pd.read_csv(path, usecols=["timestamp_start", "timestamp_end"], dtype=str)
    ts = pd.to_datetime(df.timestamp_start, format="mixed", errors="coerce")
    te = pd.to_datetime(df.timestamp_end, format="mixed", errors="coerce")
    sub = ((te - ts).dt.total_seconds() < 3600) & ts.notna()
    jam = ts[sub].dt.floor("h").drop_duplicates().sort_values()
    if jam.empty:
        return pd.DataFrame(columns=["blok", "awal", "akhir", "jumlah_jam", "baris_subjam"])
    g = (jam.diff() != pd.Timedelta(hours=1)).cumsum()
    blok = jam.groupby(g).agg(awal="min", akhir="max", jumlah_jam="size").reset_index(drop=True)
    cnt = ts[sub].dt.floor("h").value_counts()
    blok["baris_subjam"] = [int(cnt[(cnt.index >= a) & (cnt.index <= b)].sum()) for a, b in zip(blok.awal, blok.akhir)]
    blok.insert(0, "blok", range(1, len(blok) + 1))
    return blok


def bulan_nilai_sentinel(kode: str, nilai: float = 999.0, raw_dir=cfg.RAW_DIR) -> pd.Series:
    """Jumlah baris per bulan kalender (1–12) yang memuat tepat `nilai` pada kolom PM2.5/PM10."""
    kat = katalog_file(raw_dir)
    path = kat[(kat.tabel == "aqms") & (kat.kode_stasiun == kode)].path.iloc[0]
    df = baca_mentah(path)
    ts = pd.to_datetime(df.timestamp_start, format="mixed", errors="coerce")
    pm = [c for c in df.columns if nama_kanonik(c) in ("pm25", "pm10")]
    hit = pd.concat([pd.to_numeric(df[c], errors="coerce") == nilai for c in pm], axis=1).any(axis=1)
    return ts[hit].dt.month.value_counts().sort_index().rename("baris")


def format_milidetik(raw_dir=cfg.RAW_DIR) -> list[str]:
    """Kode stasiun yang `timestamp_start`-nya memakai format dengan pecahan detik (mis. 00:00:00.000)."""
    kat = katalog_file(raw_dir)
    hasil = []
    for r in kat[kat.tabel == "aqms"].itertuples():
        s = pd.read_csv(r.path, usecols=["timestamp_start"], nrows=200, dtype=str).timestamp_start
        if s.str.contains(r"\.\d+$").any():
            hasil.append(r.kode_stasiun)
    return hasil


def tanda_curiga(ring: pd.DataFrame, desk: pd.DataFrame, sites: pd.DataFrame,
                 musiman: pd.DataFrame | None = None, silang: pd.DataFrame | None = None) -> pd.DataFrame:
    """Tandai stasiun mencurigakan berdasarkan statistik mentah (sebelum pembersihan).

    Aturan (tiap aturan menghasilkan satu butir keterangan):
      - satuan ppm; - baris ≠ 24.432; - %VALID < 90; - ada teks galat; - ada nilai mustahil;
      - median PM2.5 (estimasi µg/m³) di luar 0,5–2× baseline_pm25; - PM2.5 maks > 500 µg/m³;
      - PM2.5 > PM10 pada > 1% baris;
      - (opsional) `musiman`: korelasi profil musiman < 0,5 terhadap stasiun sejenis;
      - (opsional) `silang`: peringkat kasus RS ≥ 10 tingkat lebih rendah dari peringkat PM2.5.
    """
    kor = musiman.set_index("kode").korelasi_musiman_vs_rekan if musiman is not None else pd.Series(dtype=float)
    sel = silang.set_index("kode").selisih_peringkat if silang is not None else pd.Series(dtype=float)
    base = sites.assign(kode=sites.location_id.str.replace("LOC-", "", regex=False)).set_index("kode").baseline_pm25
    d25 = desk[desk.kanon == "pm25"].set_index("kode")
    baris = []
    for r in ring.itertuples():
        alasan = []
        if r.satuan == "ppm":
            alasan.append("satuan ppm")
        if r.n_baris != cfg.EXPECTED_HOURS:
            alasan.append(f"jumlah baris {r.n_baris} ≠ {cfg.EXPECTED_HOURS}")
        if r.persen_valid < 90:
            alasan.append(f"VALID hanya {r.persen_valid:.1f}%")
        if r.n_baris_teks > 0:
            alasan.append("ada teks galat")
        if r.n_baris_mustahil > 0:
            alasan.append("ada nilai mustahil")
        med_est = mx_est = rasio = np.nan
        if r.kode in d25.index:
            fak = faktor_ke_ugm3("pm25", r.satuan)
            med_est, mx_est = d25.loc[r.kode, "median"] * fak, d25.loc[r.kode, "maks"] * fak
            rasio = med_est / base[r.kode]
            if not (0.5 <= rasio <= 2.0):
                alasan.append(f"median PM2.5 {rasio:.1f}× baseline")
            if mx_est > cfg.BATAS_EKSTREM_PM["pm25"]:
                alasan.append(f"PM2.5 maks {mx_est:,.0f} µg/m³".replace(",", "."))
        if r.n_pm25_gt_pm10 / max(r.n_baris, 1) > 0.01:
            alasan.append("PM2.5 > PM10 >1% baris")
        if r.kode in kor.index and kor[r.kode] < 0.5:
            alasan.append(f"pola musiman menyimpang (r={kor[r.kode]:.2f} vs stasiun gambut lain)")
        if r.kode in sel.index and pd.notna(sel[r.kode]) and sel[r.kode] >= 10:
            alasan.append(f"PM2.5 tinggi tetapi kasus RS rendah (peringkat kasus {int(sel[r.kode])} tingkat di bawah peringkat PM2.5)")
        baris.append(dict(kode=r.kode, median_pm25_est=med_est, maks_pm25_est=mx_est, baseline_pm25=base.get(r.kode, np.nan),
                          rasio_median_baseline=rasio, jumlah_tanda=len(alasan), mencurigakan=len(alasan) > 0,
                          alasan="; ".join(alasan)))
    return pd.DataFrame(baris)


# =========================================================================== #
# 5. Verifikasi hipotesis satuan & pemeriksaan silang
# =========================================================================== #
def verifikasi_ppm(desk: pd.DataFrame, ring: pd.DataFrame, sites: pd.DataFrame) -> pd.DataFrame:
    """Uji hipotesis konversi ppm -> µg/m³ dengan membandingkan median terhadap acuan.

    PM2.5 : acuan = baseline_pm25 stasiun yang sama.
    Gas/PM10 : acuan = median dari median stasiun berunit µg/m³ (mengecualikan JMB-02 & MER-01).
    Hipotesis 'didukung' bila rasio median-terkonversi / acuan berada pada 0,5–2,0 (PM2.5, acuan
    spesifik-stasiun) atau 1/3–3,0 (polutan lain, acuan median seluruh stasiun yang heterogen).
    Kolom `faktor_implisit` = faktor yang diperlukan agar tepat sama dengan acuan, sebagai
    pembanding terhadap faktor hipotesis. Ini uji kewajaran orde besaran, bukan bukti pasti.
    """
    ppm = ring[ring.satuan == "ppm"].kode.tolist()
    ug = ring[(ring.satuan == "ug/m3") & ~ring.kode.isin(["JMB-02", "MER-01"])].kode.tolist()
    base = sites.assign(kode=sites.location_id.str.replace("LOC-", "", regex=False)).set_index("kode").baseline_pm25
    baris = []
    for kode in ppm:
        for p in cfg.POLUTAN:
            d = desk[(desk.kode == kode) & (desk.kanon == p)]
            if d.empty:
                continue
            med_raw = float(d["median"].iloc[0])
            fak = faktor_ke_ugm3(p, "ppm")
            if p == "pm25":
                acuan, jenis = float(base[kode]), "baseline_pm25 stasiun"
            else:
                acuan = float(desk[(desk.kode.isin(ug)) & (desk.kanon == p)]["median"].median())
                jenis = "median antar-stasiun µg/m³"
            est = med_raw * fak
            rasio = est / acuan if acuan else np.nan
            faktor_implisit = acuan / med_raw if med_raw else np.nan
            baris.append(dict(kode=kode, polutan=p, median_label_ppm=med_raw, faktor_hipotesis=round(fak, 2),
                              median_terkonversi_ugm3=round(est, 2), acuan_ugm3=round(acuan, 2), jenis_acuan=jenis,
                              rasio=round(rasio, 2), faktor_implisit=round(faktor_implisit, 1),
                              hipotesis_didukung=bool((0.5 <= rasio <= 2.0) if p == "pm25" else (1 / 3 <= rasio <= 3.0))))
    return pd.DataFrame(baris)


def korelasi_musiman(harian: pd.DataFrame, kelompok: pd.Series, grup="Gambut", kecualikan=("JMB-02",)) -> pd.DataFrame:
    """Korelasi profil musiman bulanan PM2.5 tiap stasiun satu kelompok terhadap rata-rata stasiun lain.

    `harian`: DataFrame tanggal × stasiun; `kelompok`: Series kode -> kelompok_lokasi.
    Untuk stasiun gambut, pola musiman yang negatif terhadap stasiun gambut lain mencurigakan.
    """
    klim = harian.groupby(harian.index.month).mean()
    anggota = [k for k in kelompok[kelompok == grup].index if k in klim.columns and k not in kecualikan]
    baris = []
    for k in anggota:
        lain = [x for x in anggota if x != k]
        ref = klim[lain].apply(lambda s: (s - s.mean()) / s.std(), axis=0).mean(axis=1)
        r = np.corrcoef(klim[k].fillna(klim[k].mean()), ref)[0, 1]
        bulan_puncak = int(klim[k].idxmax())
        baris.append(dict(kode=k, korelasi_musiman_vs_rekan=round(r, 2), bulan_puncak=bulan_puncak,
                          pm25_bulan_puncak=round(klim[k].max(), 1), pm25_bulan_terendah=round(klim[k].min(), 1)))
    return pd.DataFrame(baris).sort_values("korelasi_musiman_vs_rekan").reset_index(drop=True)


def silang_pm25_kasus(harian: pd.DataFrame, kes: pd.DataFrame, pasangan: pd.DataFrame) -> pd.DataFrame:
    """Perbandingan awal PM2.5 harian stasiun vs kasus RS pasangannya (deskriptif, tanpa inferensi)."""
    baris = []
    kes = kes.assign(date=pd.to_datetime(kes["date"]))
    for r in pasangan.itertuples():
        if r.kode_stasiun not in harian.columns:
            continue
        rs = kes[kes.hospital_id == r.hospital_id].set_index("date")
        j = pd.concat([harian[r.kode_stasiun].rename("pm25"), pd.to_numeric(rs["resp"], errors="coerce").rename("resp"),
                       pd.to_numeric(rs["resp_admissions_under5"], errors="coerce").rename("u5")], axis=1).dropna()
        kap = r.kapasitas_tempat_tidur
        baris.append(dict(kode=r.kode_stasiun, hospital_id=r.hospital_id, n_hari_bersama=len(j),
                          pm25_rata2=j.pm25.mean() if len(j) else np.nan,
                          resp_rata2_per_hari=pd.to_numeric(rs["resp"], errors="coerce").mean(),
                          u5_rata2_per_hari=pd.to_numeric(rs["resp_admissions_under5"], errors="coerce").mean(),
                          kapasitas_tt=kap, resp_per_100_tt=(pd.to_numeric(rs["resp"], errors="coerce").mean() / kap * 100) if pd.notna(kap) and kap else np.nan,
                          spearman_pm25_resp=j.pm25.corr(j.resp, method="spearman") if len(j) > 30 else np.nan))
    out = pd.DataFrame(baris)
    out["peringkat_pm25"] = out.pm25_rata2.rank(ascending=False, method="min")
    out["peringkat_resp"] = out.resp_rata2_per_hari.rank(ascending=False, method="min")
    out["selisih_peringkat"] = out.peringkat_resp - out.peringkat_pm25
    return out


# =========================================================================== #
# 6. Profil data kesehatan
# =========================================================================== #
KOLOM_KASUS = ["resp_admissions_under5", "resp_admissions_over60", "asthma_emergency_cases", "copd_admissions", "resp", "cvd", "death"]
KOLOM_CUACA_KES = ["temp_c", "dptp_c", "rhum_pct"]


def profil_kesehatan(raw_dir=cfg.RAW_DIR) -> dict:
    """Profil lengkap HLT-01: rentang tanggal, missing, duplikat, distribusi, konsistensi."""
    raw_dir = Path(raw_dir)
    df = baca_mentah(raw_dir / "HLT-01_health_outcomes_daily.csv")
    hosp = pd.read_csv(raw_dir / "hospitals.csv")
    n = len(df)
    tgl = pd.to_datetime(df["date"], errors="coerce")
    hari_semua = pd.date_range(tgl.min(), tgl.max(), freq="D")
    rs_semua = sorted(df["hospital_id"].unique())
    harap = len(hari_semua) * len(rs_semua)

    # --- numerik ---
    ang = {}
    kol_rows = []
    for c in KOLOM_KASUS + KOLOM_CUACA_KES + ["time"]:
        v, k, t = klasifikasi_nilai(df[c])
        ang[c] = v
        vv = v.dropna()
        non_bulat = int(((vv % 1) != 0).sum()) if c in KOLOM_KASUS + ["time"] else np.nan
        rata, var = (vv.mean(), vv.var()) if len(vv) else (np.nan, np.nan)
        kol_rows.append(dict(
            kolom=c, n_kosong=int(k.sum()), n_teks=int(t.sum()), n_negatif=int((vv < 0).sum()), n_nol=int((vv == 0).sum()),
            persen_nol=round(100 * (vv == 0).mean(), 1), n_non_bulat=non_bulat, rata2=rata, sd=vv.std(), min=vv.min(),
            p50=vv.median(), p95=vv.quantile(0.95), p99=vv.quantile(0.99), maks=vv.max(),
            dispersi_var_per_rata2=round(var / rata, 2) if c in KOLOM_KASUS and rata else np.nan,
        ))
    kolom_df = pd.DataFrame(kol_rows)

    # --- kunci & duplikat ---
    kunci = pd.DataFrame(dict(tgl=tgl, rs=df["hospital_id"]))
    dup_kunci = kunci.duplicated(keep=False)
    dup_identik = df.duplicated(keep=False)
    per_rs = kunci.groupby("rs").tgl.agg(n_baris="size", hari_unik="nunique", awal="min", akhir="max").reset_index()
    per_rs["hari_hilang"] = len(hari_semua) - per_rs.hari_unik
    per_rs = per_rs.merge(hosp[["hospital_id", "nama_rumah_sakit", "provinsi", "kelas_faskes", "kapasitas_tempat_tidur"]],
                          left_on="rs", right_on="hospital_id", how="left").drop(columns="hospital_id")
    ada = set(zip(kunci.tgl, kunci.rs))
    hilang = [(d, r) for r in rs_semua for d in hari_semua if (d, r) not in ada]
    hilang_df = pd.DataFrame(hilang, columns=["tanggal", "hospital_id"])
    hilang_df["tanggal"] = pd.to_datetime(hilang_df["tanggal"])

    # --- konsistensi ---
    dow_harap = tgl.dt.day_name()
    dow_beda = int((dow_harap != df["dow"].str.strip()).sum())
    # `time` = nomor urut hari PER RS (1 = observasi pertama RS tsb), bukan indeks global
    urut_per_rs = kunci.sort_values(["rs", "tgl"]).groupby("rs").cumcount().add(1).sort_index()
    time_beda = int((ang["time"] != urut_per_rs).sum())
    sebelum_jendela = int((tgl < cfg.WINDOW_START.normalize()).sum())
    hilang_dalam = int((hilang_df.tanggal >= cfg.WINDOW_START.normalize()).sum())
    dp_gt_t = int((ang["dptp_c"] > ang["temp_c"] + 0.05).sum())
    rh_luar = int(((ang["rhum_pct"] < 0) | (ang["rhum_pct"] > 100)).sum())
    suhu_luar = int(((ang["temp_c"] < 5) | (ang["temp_c"] > 45)).sum())
    resp_lt_sum = int((ang["resp"] < (ang["resp_admissions_under5"] + ang["resp_admissions_over60"])).sum())

    ring = dict(
        n_baris=n, n_rs=len(rs_semua), tanggal_awal=tgl.min(), tanggal_akhir=tgl.max(), n_hari=len(hari_semua),
        baris_diharapkan=harap, baris_hilang=harap - len(kunci.drop_duplicates()),
        hari_rs_hilang_dalam_periode_aqms=hilang_dalam, baris_sebelum_periode_aqms=sebelum_jendela,
        tanggal_tak_terbaca=int(tgl.isna().sum()), n_baris_kunci_duplikat=int(dup_kunci.sum()),
        n_baris_identik_duplikat=int(dup_identik.sum()), dow_tidak_cocok=dow_beda, time_tidak_cocok=time_beda,
        dptp_lebih_besar_dari_suhu=dp_gt_t, rh_di_luar_0_100=rh_luar, suhu_di_luar_5_45=suhu_luar,
        resp_lebih_kecil_dari_balita_plus_lansia=resp_lt_sum,
        rs_di_hospitals_tapi_tidak_di_kesehatan=len(set(hosp.hospital_id) - set(rs_semua)),
        rs_di_kesehatan_tapi_tidak_di_hospitals=len(set(rs_semua) - set(hosp.hospital_id)),
        kapasitas_kosong=int(hosp.kapasitas_tempat_tidur.isna().sum()),
    )
    harian_total = pd.DataFrame({c: ang[c] for c in KOLOM_KASUS}).assign(tgl=tgl).groupby("tgl").sum()
    return dict(ringkasan=ring, kolom=kolom_df, per_rs=per_rs, hilang=hilang_df, raw=df, angka=pd.DataFrame(ang).assign(tgl=tgl, rs=df.hospital_id),
                harian_total=harian_total, hospitals=hosp)


# =========================================================================== #
# 7. Daftar masalah kualitas data
# =========================================================================== #
def _tingkat(persen: float, override: str | None = None) -> str:
    if override:
        return override
    if persen >= 20:
        return "Kritis"
    if persen >= 5:
        return "Tinggi"
    if persen >= 1:
        return "Sedang"
    return "Rendah"


def susun_masalah(prof: dict, relasi: pd.DataFrame, kes: dict, ppm: pd.DataFrame, sensors: pd.DataFrame,
                  curiga: pd.DataFrame | None = None) -> pd.DataFrame:
    """Susun tabel masalah kualitas data (satu baris per masalah) untuk reports/data_quality_issues.csv.

    Tingkat keparahan: Kritis ≥20% baris terdampak; Tinggi ≥5%; Sedang ≥1%; Rendah <1%.
    Beberapa jenis memakai penetapan khusus karena dapat diperbaiki deterministik
    (mis. satuan ppm & timestamp bergeser).
    """
    ring, kol, tok = prof["ringkasan"], prof["kolom"], prof["token"]
    status = sensors.assign(kode=sensors.location_id.str.replace("LOC-", "", regex=False)).set_index("kode").status_operasional
    out = []

    def tambah(sumber, entitas, kategori, kolom, deskripsi, n_terdampak, total, dampak, tindakan, override=None):
        persen = round(100 * n_terdampak / total, 2) if total else 0.0
        out.append(dict(sumber=sumber, entitas=entitas, kategori=kategori, kolom=kolom, deskripsi=deskripsi,
                        jumlah_terdampak=int(n_terdampak), total_baris=int(total), persen_terdampak=persen,
                        tingkat=_tingkat(persen, override), dampak_analisis=dampak, tindakan_usulan=tindakan))

    for r in ring.itertuples():
        n = r.n_baris
        f = r.file
        if r.satuan == "ppm":
            hip = ppm[ppm.kode == r.kode]
            ok = int(hip.hipotesis_didukung.sum()) if len(hip) else 0
            tambah(f, r.kode, "Satuan tidak standar (ppm)", "pm25,pm10,so2,co,o3,no2",
                   f"Header kolom polutan *_ppm; faktor hipotesis didukung pada {ok}/{len(hip)} polutan.", n, n,
                   "Tanpa konversi, konsentrasi 1000× terlalu kecil → stasiun tampak 'bersih' dan salah peringkat/ISPU.",
                   "Konversi ke µg/m³ (PM ×1000; gas ppm×BM/24,45×1000) setelah hipotesis dikonfirmasi per polutan.", override="Tinggi")
        if r.n_baris_teks:
            toks = tok[tok.kode == r.kode].groupby("token").n.sum().sort_values(ascending=False)
            ket = ", ".join(f"{k}×{v}" for k, v in toks.head(6).items())
            tambah(f, r.kode, "Nilai non-numerik (teks galat)", "semua kolom numerik",
                   f"{len(toks)} jenis teks: {ket}{'…' if len(toks) > 6 else ''}.", r.n_baris_teks, n,
                   "Kolom terbaca sebagai teks; agregasi gagal tanpa pembersihan.", "Ubah ke NaN (coerce) dan catat jumlah per jenis.")
        if r.n_baris_kosong:
            tambah(f, r.kode, "Nilai kosong (missing)", "semua kolom numerik", "Baris dengan ≥1 kolom numerik kosong.", r.n_baris_kosong, n,
                   "Rata-rata & kelengkapan bias bila tidak ditangani.", "Biarkan NaN; jangan imputasi untuk PM; hitung kelengkapan.")
        sub = kol[(kol.kode == r.kode)]
        for jenis, kolkey, desk in (("Nilai sentinel (999/-9999 dst.)", "n_sentinel", "Nilai pengganti galat/saturasi alat"),
                                    ("Nilai negatif (polutan)", "n_negatif", "Konsentrasi negatif secara fisik mustahil"),
                                    ("Nilai di luar rentang fisik (cuaca)", "n_luar_rentang", "Suhu <5/>45 °C, RH di luar 0–100, angin >40 m/s, arah di luar 0–360")):
            s = sub[sub[kolkey] > 0]
            if len(s):
                tambah(f, r.kode, jenis, ",".join(s.kolom), f"{desk}. Rincian: " + ", ".join(f"{a}={b}" for a, b in zip(s.kolom, s[kolkey])) + ".",
                       int(s[kolkey].max()), n, "Mencemari rata-rata, maksimum, dan ISPU bila tidak dikecualikan.", "Ubah ke NaN sebelum agregasi.")
        if r.n_baris_ekstrem:
            tambah(f, r.kode, "Nilai ekstrem (perlu verifikasi)", "pm25,pm10", "PM > 500 µg/m³ (batas atas ISPU); bisa episode asap nyata.",
                   r.n_baris_ekstrem, n, "Pencilan bisa nyata (karhutla) atau galat; jangan dibuang otomatis.",
                   "Verifikasi terhadap CO, rasio PM2.5/PM10, musim, dan stasiun tetangga.", override="Sedang")
        if r.ts_tak_terbaca:
            tambah(f, r.kode, "Timestamp tidak terbaca", "timestamp_start", "Format waktu tidak dapat di-parse.", r.ts_tak_terbaca, n,
                   "Baris tidak bisa ditempatkan pada sumbu waktu.", "Tandai & kecualikan.")
        if r.n_ts_luar_jendela:
            tambah(f, r.kode, "Timestamp di luar periode observasi", "timestamp_start",
                   f"Rentang mentah {r.ts_min_mentah:%Y-%m-%d} s.d. {r.ts_maks_mentah:%Y-%m-%d}; di luar 2024-01-01…2026-10-14.",
                   r.n_ts_luar_jendela, n, "Terbaca sebagai epoch 1970 / tanggal mustahil.", "Kecualikan dari analisis deret waktu.")
        if r.n_ts_bergeser:
            tambah(f, r.kode, "Timestamp bergeser dari awal jam", "timestamp_start",
                   f"Geseran bertanda median {r.geser_median_menit} mnt (rentang {r.geser_min_menit}…{r.geser_maks_menit} mnt); "
                   f"sebaran offset dari awal jam: {r.sebaran_offset}."
                   + (f" {r.n_geser_tepat_30menit} baris tepat :30 → pembulatan ke jam terdekat ambigu." if r.n_geser_tepat_30menit else ""),
                   r.n_ts_bergeser, n,
                   "Join antar-stasiun/harian bisa tidak sejajar; duplikat semu setelah pembulatan.", "Bulatkan ke jam terdekat.", override="Sedang" if r.persen_ts_bergeser >= 50 else None)
        if r.n_durasi_bukan_1jam:
            ket = "Selisih timestamp_end − timestamp_start bukan 3600 detik."
            if r.n_durasi_subjam:
                ket += (f" {r.n_durasi_subjam} baris berjendela {r.durasi_subjam_menit} menit, terkumpul dalam {r.n_blok_subjam} blok jam berurutan "
                        f"({r.blok_subjam}); logger beresolusi lebih halus dari 1 jam hanya pada blok tersebut.")
            tambah(f, r.kode, "Durasi jendela ≠ 1 jam", "timestamp_end", ket,
                   r.n_durasi_bukan_1jam, n, "Resolusi nominal 1 jam tidak terpenuhi; baris sub-jam perlu diagregasi ke jam.",
                   "Agregasi baris sub-jam ke rata-rata per jam; gunakan timestamp_start sebagai acuan.")
        if r.n_jam_hilang:
            tambah(f, r.kode, "Jam hilang (tidak ada baris)", "timestamp_start",
                   f"{r.n_jam_hilang} dari {cfg.EXPECTED_HOURS} jam tidak tercatat; gap terpanjang {r.gap_terpanjang_jam} jam.",
                   r.n_jam_hilang, cfg.EXPECTED_HOURS, "Kelengkapan rendah; bias musiman bila gap menumpuk pada bulan tertentu.",
                   "Reindex ke 24.432 jam; jangan imputasi PM.")
        if r.n_baris_lebih_per_jam:
            sub = " Penyebab dominan: bacaan sub-jam (:15/:30/:45), bukan salinan baris." if r.n_durasi_subjam else ""
            tambah(f, r.kode, "Duplikat per jam", "timestamp_start",
                   f"{r.n_baris_lebih_per_jam} baris lebih; {r.n_jam_duplikat} jam berisi >1 baris, {r.n_jam_duplikat_konflik} di antaranya "
                   f"bernilai PM2.5 berbeda.{sub}",
                   r.n_baris_lebih_per_jam, n, "Menggandakan bobot jam tertentu bila tidak dideduplikasi.",
                   "Kelompokkan per jam penuh (floor) lalu agregasi (pilih VALID; rata-rata) dan dokumentasikan.")
        if r.n_baris_identik:
            tambah(f, r.kode, "Baris identik (selain measurement_id)", "semua", "Seluruh nilai sama persis dengan baris lain.", r.n_baris_identik, n,
                   "Duplikat murni.", "Hapus duplikat murni.")
        nonvalid = n - r.n_valid
        if r.persen_valid < 99:
            tambah(f, r.kode, "Baris tidak berstatus VALID", "qc_flag", f"Hanya {r.persen_valid:.1f}% VALID; {r.n_flag_beragam} label qc_flag berbeda.", nonvalid, n,
                   "Data non-VALID tidak boleh masuk analisis konsentrasi.", "Pakai hanya VALID untuk analisis utama; uji sensitivitas untuk SUSPECT.")
        if r.n_flag_nonstandar:
            tambah(f, r.kode, "Label qc_flag di luar spesifikasi metadata", "qc_flag",
                   "Label selain VALID/SUSPECT/CALIBRATING/MISSING (mis. WARMUP, MAINTENANCE, kode galat).", r.n_flag_nonstandar, n,
                   "Pemetaan label→valid/tidak valid perlu aturan eksplisit.", "Buat kamus pemetaan qc_flag.")
        if r.n_valid_tapi_mustahil:
            tambah(f, r.kode, "qc_flag VALID tetapi nilai mustahil", "qc_flag + nilai", "Penanda QC alat tidak menangkap nilai mustahil.",
                   r.n_valid_tapi_mustahil, n, "Memfilter hanya dengan qc_flag = VALID tidak cukup.", "Tambahkan aturan rentang fisik di luar qc_flag.")
        if r.n_pm25_gt_pm10 / max(n, 1) > 0.01:
            tambah(f, r.kode, "PM2.5 > PM10 (tidak konsisten fisik)", "pm25,pm10", "PM2.5 seharusnya ≤ PM10.", r.n_pm25_gt_pm10, n,
                   "Rasio PM2.5/PM10 (indikator asap) tidak andal.", "Periksa kalibrasi; tandai sebagai kecurigaan.")
        st = status.get(r.kode)
        if st and st != "Active":
            tambah("sensors.csv", r.kode, "Status sensor tidak aktif penuh", "status_operasional", f"Status: {st}.", r.n_baris, n,
                   "Keandalan stasiun lebih rendah; relevan untuk evaluasi jaringan.", "Beri bobot keandalan; sertakan pada Tujuan 5.", override="Sedang")

    # --- anomali lintas-sumber (pola musiman / PM2.5 vs kasus RS) ---
    if curiga is not None:
        nbaris = ring.set_index("kode").n_baris
        for r in curiga.itertuples():
            for butir in r.alasan.split("; "):
                if butir.startswith("pola musiman") or butir.startswith("PM2.5 tinggi tetapi kasus"):
                    tambah("lintas data AQMS + kesehatan", r.kode, "Anomali pola (perlu investigasi)", "pm25 / kasus RS", butir + ".", nbaris[r.kode], nbaris[r.kode],
                           "Hubungan PM2.5–kesehatan stasiun ini tidak dapat dipercaya sebelum anomali dijelaskan.",
                           "Investigasi di EDA/notebook 03–04; uji sensitivitas dengan dan tanpa stasiun ini.", override="Tinggi")

    # --- relasi (R27 sudah tercakup per-stasiun, jadi tidak diulang) ---
    for r in relasi[(relasi.status == "MASALAH") & (relasi.kode != "R27")].itertuples():
        tambah("relasi antar-tabel", r.kode, "Konsistensi antar-tabel tidak cocok", r.pemeriksaan, r.detail or "-", r.jumlah_tidak_cocok, 27,
               "Join antar-tabel bisa kehilangan baris.", "Perbaiki/pemetaan manual sebelum join.")

    # --- kesehatan ---
    k = kes["ringkasan"]
    f = "HLT-01_health_outcomes_daily.csv"
    n = k["n_baris"]
    if k["hari_rs_hilang_dalam_periode_aqms"]:
        tambah(f, "HLT-01", "Hari-RS hilang (dalam periode AQMS)", "date,hospital_id",
               f"{k['hari_rs_hilang_dalam_periode_aqms']} kombinasi tanggal×RS tidak ada pada 2024-01-01…2026-10-14.",
               k["hari_rs_hilang_dalam_periode_aqms"], 27 * (k["n_hari"] - 1), "Deret waktu RS berlubang; memengaruhi model lag.",
               "Reindex; tandai NaN, jangan isi nol.")
    if k["baris_sebelum_periode_aqms"]:
        tambah(f, "HLT-01", "Baris kesehatan sebelum periode AQMS", "date",
               f"{k['baris_sebelum_periode_aqms']} baris bertanggal 2023-12-31 (hanya ada di sebagian RS; AQMS mulai 2024-01-01).",
               k["baris_sebelum_periode_aqms"], n, "Tidak punya pasangan data paparan; tidak seragam antar-RS.",
               "Kecualikan dari analisis paparan–respons.", override="Rendah")
    if k["resp_lebih_kecil_dari_balita_plus_lansia"]:
        tambah(f, "HLT-01", "resp < balita + lansia (uji kewajaran)", "resp,resp_admissions_under5,resp_admissions_over60",
               "Kolom `resp` lebih kecil dari jumlah rawat inap balita + lansia; definisi `resp` tidak dijelaskan booklet.",
               k["resp_lebih_kecil_dari_balita_plus_lansia"], n, "Tidak aman menganggap `resp` sebagai total yang mencakup kolom lain.",
               "Perlakukan `resp` sebagai outcome terpisah; jangan dijumlahkan dengan kolom umur.", override="Rendah")
    if k["n_baris_kunci_duplikat"]:
        tambah(f, "HLT-01", "Duplikat (tanggal, RS)", "date,hospital_id", "Kunci ganda.", k["n_baris_kunci_duplikat"], n, "Menggandakan kasus.", "Deduplikasi.")
    for c in kes["kolom"].itertuples():
        if c.n_kosong:
            tambah(f, "HLT-01", "Nilai kosong (missing)", c.kolom, "Sel kosong.", c.n_kosong, n, "Mengurangi n efektif.", "Biarkan NaN.")
        if c.n_teks:
            tambah(f, "HLT-01", "Nilai non-numerik", c.kolom, "Teks pada kolom numerik.", c.n_teks, n, "Gagal agregasi.", "Ubah ke NaN.")
        if c.n_negatif:
            tambah(f, "HLT-01", "Nilai negatif", c.kolom, "Jumlah kasus negatif mustahil.", c.n_negatif, n, "Bias model.", "Ubah ke NaN.")
    for kunci, nama, kol in (("dow_tidak_cocok", "Nama hari tidak cocok dengan tanggal", "dow"), ("time_tidak_cocok", "Nomor urut hari tidak cocok", "time"),
                             ("dptp_lebih_besar_dari_suhu", "Titik embun > suhu udara (mustahil fisik)", "dptp_c,temp_c"),
                             ("rh_di_luar_0_100", "Kelembapan di luar 0–100%", "rhum_pct"), ("suhu_di_luar_5_45", "Suhu di luar 5–45 °C", "temp_c")):
        if k[kunci]:
            tambah(f, "HLT-01", nama, kol, "Pemeriksaan konsistensi internal.", k[kunci], n, "Kovariat cuaca RS tidak andal.", "Periksa lalu tandai.")
    if k["kapasitas_kosong"]:
        tambah("hospitals.csv", "hospitals", "Kapasitas tempat tidur kosong", "kapasitas_tempat_tidur", "Sebagian RS tanpa kapasitas.",
               k["kapasitas_kosong"], 27, "Normalisasi beban per tempat tidur tidak bisa untuk RS tsb.", "Tandai; jangan imputasi diam-diam.")
    df = pd.DataFrame(out)
    df.insert(0, "id_masalah", [f"DQ-{i:03d}" for i in range(1, len(df) + 1)])
    df["tingkat"] = pd.Categorical(df.tingkat, categories=style.KEPARAHAN_URUTAN, ordered=True)
    return df.sort_values(["tingkat", "persen_terdampak"], ascending=[True, False]).reset_index(drop=True).assign(
        id_masalah=lambda d: [f"DQ-{i:03d}" for i in range(1, len(d) + 1)])


# =========================================================================== #
# 8. Fungsi visual
# =========================================================================== #
def urutan_stasiun(pasangan: pd.DataFrame) -> list[str]:
    """Urutan tampilan stasiun: pulau → kelompok lokasi → kode."""
    p = pasangan.copy()
    p["o_pulau"] = p.pulau.map({k: i for i, k in enumerate(cfg.URUTAN_PULAU)})
    p["o_kel"] = p.kelompok_lokasi.map({k: i for i, k in enumerate(cfg.URUTAN_KELOMPOK)})
    return p.sort_values(["o_pulau", "o_kel", "kode_stasiun"]).kode_stasiun.tolist()


def fig_heatmap_ketersediaan(bulanan: pd.DataFrame, urutan: list[str], jenis="jam_valid", judul="") -> go.Figure:
    """Heatmap stasiun × bulan. jenis: 'jam_valid' (jam berstatus VALID) atau 'jam_tercatat'."""
    b = bulanan.assign(persen=100 * bulanan[jenis] / bulanan.jam_harap)
    pv = b.pivot(index="kode", columns="bulan", values="persen").reindex(urutan[::-1])
    fig = go.Figure(go.Heatmap(
        z=pv.values, x=[d.strftime("%b %Y") for d in pv.columns], y=pv.index, zmin=0, zmax=100,
        colorscale=style.SKALA_KELENGKAPAN, xgap=1, ygap=1,
        colorbar=dict(title="% jam", ticksuffix="%"),
        hovertemplate="Stasiun %{y}<br>%{x}<br>%{z:.1f}% jam<extra></extra>"))
    fig.update_xaxes(tickangle=-60, side="top", showgrid=False)
    fig.update_yaxes(showgrid=False, autorange=True)
    return style.terapkan(fig, judul, tinggi=max(520, 22 * len(urutan) + 160))


def _kelompok_qc(flag: str) -> str:
    if flag in style.QC_WARNA:
        return flag
    return "Galat alat" if flag in cfg.QC_GALAT else "Lainnya"


def fig_qc_distribusi(qc: pd.DataFrame, urutan: list[str], judul="") -> go.Figure:
    """Bar 100% tertumpuk distribusi qc_flag per stasiun (label galat alat digabung)."""
    q = qc.assign(grup=qc.qc_flag.map(_kelompok_qc)).groupby(["kode", "grup"]).persen.sum().reset_index()
    fig = go.Figure()
    for grup in ["VALID", "SUSPECT", "CALIBRATING", "WARMUP", "MAINTENANCE", "MISSING", "Galat alat", "Lainnya"]:
        s = q[q.grup == grup].set_index("kode").persen.reindex(urutan).fillna(0)
        if s.sum() == 0:
            continue
        fig.add_bar(y=urutan, x=s.values, name=grup, orientation="h", marker_color=style.QC_WARNA[grup],
                    hovertemplate="%{y}<br>" + grup + ": %{x:.2f}%<extra></extra>")
    fig.update_layout(barmode="stack")
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return style.terapkan(fig, judul, tinggi=max(520, 22 * len(urutan) + 140), sumbu_x="Persentase baris (%)")


def fig_ringkasan_masalah(masalah: pd.DataFrame, urutan: list[str]) -> go.Figure:
    """Peta panas ringkas: stasiun × kategori masalah, warna = tingkat keparahan tertinggi."""
    m = masalah[masalah.entitas.isin(urutan)].copy()
    skala = {k: i for i, k in enumerate(style.KEPARAHAN_URUTAN[::-1], start=1)}   # Rendah=1 … Kritis=4
    m["skor"] = m.tingkat.astype(str).map(skala)
    pv = m.pivot_table(index="entitas", columns="kategori", values="skor", aggfunc="max").reindex(urutan[::-1])
    urut_kolom = pv.notna().sum().sort_values(ascending=False).index
    pv = pv[urut_kolom]
    warna = [[0.0, style.WARNA_NA], [0.0001, style.KEPARAHAN_WARNA["Rendah"]], [1 / 3, style.KEPARAHAN_WARNA["Sedang"]],
             [2 / 3, style.KEPARAHAN_WARNA["Tinggi"]], [1.0, style.KEPARAHAN_WARNA["Kritis"]]]
    fig = go.Figure(go.Heatmap(
        z=pv.fillna(0).values, x=list(pv.columns), y=list(pv.index), colorscale=warna, zmin=0, zmax=4, xgap=2, ygap=2,
        showscale=False, hovertemplate="%{y}<br>%{x}<extra></extra>"))
    for k in style.KEPARAHAN_URUTAN:
        fig.add_scatter(x=[None], y=[None], mode="markers", marker=dict(size=11, color=style.KEPARAHAN_WARNA[k], symbol="square"), name=k)
    fig.update_xaxes(tickangle=-40, side="top", showgrid=False)
    fig.update_yaxes(showgrid=False)
    return style.terapkan(fig, "", tinggi=max(560, 22 * len(urutan) + 280))


def fig_kesehatan_distribusi(kes: dict) -> go.Figure:
    """Histogram jumlah kasus harian per RS-hari untuk tiap kolom kasus."""
    a = kes["angka"]
    fig = make_subplots(rows=2, cols=4, subplot_titles=[c.replace("_", " ") for c in KOLOM_KASUS], vertical_spacing=0.18)
    for i, c in enumerate(KOLOM_KASUS):
        v = a[c].dropna()
        fig.add_histogram(x=v, nbinsx=min(40, int(v.max()) + 1), marker_color=style.WARNA_UTAMA, showlegend=False, row=1 + i // 4, col=1 + i % 4,
                          hovertemplate="%{x} kasus: %{y} RS-hari<extra></extra>")
    fig.update_yaxes(title_text="Jumlah RS-hari", col=1)
    return style.terapkan(fig, "Distribusi kasus harian per rumah sakit", tinggi=520)


def fig_kesehatan_kelengkapan(kes: dict) -> go.Figure:
    """Heatmap RS × bulan: persen hari terisi."""
    a = kes["raw"].assign(tgl=pd.to_datetime(kes["raw"]["date"]))
    a["bulan"] = a.tgl.dt.to_period("M").dt.to_timestamp()
    cnt = a.drop_duplicates(["tgl", "hospital_id"]).groupby(["hospital_id", "bulan"]).size().unstack(fill_value=0)
    hari = pd.Series(1, index=pd.date_range(a.tgl.min(), a.tgl.max())).groupby(lambda d: d.to_period("M").to_timestamp()).sum()
    pct = (cnt / hari.reindex(cnt.columns).values * 100).clip(upper=100)
    fig = go.Figure(go.Heatmap(z=pct.values[::-1], x=[d.strftime("%b %Y") for d in pct.columns], y=list(pct.index)[::-1],
                               zmin=0, zmax=100, colorscale=style.SKALA_KELENGKAPAN, xgap=1, ygap=1,
                               colorbar=dict(title="% hari", ticksuffix="%"), hovertemplate="%{y}<br>%{x}<br>%{z:.1f}% hari<extra></extra>"))
    fig.update_xaxes(tickangle=-60, side="top", showgrid=False)
    fig.update_yaxes(showgrid=False)
    return style.terapkan(fig, "", tinggi=700)
