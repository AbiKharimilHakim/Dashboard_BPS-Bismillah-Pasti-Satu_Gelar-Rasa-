"""Konfigurasi bersama: path, konstanta periode, dan pemetaan kategori.

Semua notebook dan modul di src/ mengimpor konstanta dari sini agar angka
dan definisi tetap konsisten antarbagian.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------- #
# Path proyek
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROC_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"
FIG_DIR = REPORTS_DIR / "figures"
FINDINGS_DIR = REPORTS_DIR / "findings"

# --------------------------------------------------------------------------- #
# Periode observasi AQMS (metadata_dates.csv + booklet)
# --------------------------------------------------------------------------- #
WINDOW_START = pd.Timestamp("2024-01-01 00:00:00")
WINDOW_END = pd.Timestamp("2026-10-14 23:00:00")
# 1018 hari x 24 jam
EXPECTED_HOURS = int((WINDOW_END - WINDOW_START) / pd.Timedelta(hours=1)) + 1  # 24432

# --------------------------------------------------------------------------- #
# Kolom numerik data AQMS
# --------------------------------------------------------------------------- #
POLUTAN = ["pm25", "pm10", "so2", "co", "o3", "no2"]
CUACA = ["temperature_c", "humidity_pct", "wind_speed_ms", "wind_direction_deg"]
KOLOM_ID = ["measurement_id", "sensor_id", "timestamp_start", "timestamp_end", "qc_flag"]

# Berat molekul untuk konversi ppm -> ug/m3 (25 C, 1 atm; volume molar 24,45 L/mol)
BERAT_MOLEKUL = {"so2": 64.07, "co": 28.01, "o3": 48.00, "no2": 46.01}
VOLUME_MOLAR = 24.45

# Label qc_flag yang tercantum pada metadata_sensors.csv
QC_STANDAR = ["VALID", "SUSPECT", "CALIBRATING", "MISSING"]
# Label qc_flag yang menandakan galat/kegagalan alat (di luar spesifikasi)
QC_GALAT = ["COMM_LOST", "SENSOR_DEAD", "CORRUPT", "FATAL_ERR", "GARBAGE", "PARSER_FAIL"]

# Nilai pengganti (sentinel) yang tidak mungkin berupa konsentrasi/cuaca nyata
SENTINEL = [-9999.0, -999.0, 999.0, 9999.0, 99999.0]

# Pengecualian sentinel: 999 µg/m3 adalah konsentrasi CO yang wajar (CO tipikal ratusan–ribuan µg/m3),
# sehingga angka 999 pada CO (satuan µg/m3) BUKAN dianggap nilai pengganti galat.
SENTINEL_KECUALI = {"co": [999.0]}

# Batas kewajaran fisik per variabel cuaca (di luar batas = mustahil)
BATAS_CUACA = {
    "temperature_c": (5.0, 45.0),
    "humidity_pct": (0.0, 100.0),
    "wind_speed_ms": (0.0, 40.0),
    "wind_direction_deg": (0.0, 360.0),
}
# Batas atas tabel ISPU: di atas ini ditandai "ekstrem" (perlu verifikasi, bukan otomatis salah)
BATAS_EKSTREM_PM = {"pm25": 500.0, "pm10": 500.0}

# --------------------------------------------------------------------------- #
# Pengelompokan wilayah & lokasi
# --------------------------------------------------------------------------- #
PULAU_PROVINSI = {
    "Aceh": "Sumatera",
    "Sumatera Utara": "Sumatera",
    "Sumatera Barat": "Sumatera",
    "Riau": "Sumatera",
    "Kepulauan Riau": "Sumatera",
    "Jambi": "Sumatera",
    "Bengkulu": "Sumatera",
    "Sumatera Selatan": "Sumatera",
    "Lampung": "Sumatera",
    "DKI Jakarta": "Jawa",
    "Jawa Barat": "Jawa",
    "DI Yogyakarta": "Jawa",
    "Jawa Timur": "Jawa",
    "Kalimantan Barat": "Kalimantan",
    "Kalimantan Tengah": "Kalimantan",
    "Kalimantan Selatan": "Kalimantan",
    "Kalimantan Timur": "Kalimantan",
    "Sulawesi Selatan": "Sulawesi",
    "Sulawesi Tengah": "Sulawesi",
    "Papua Barat Daya": "Papua",
    "Papua Selatan": "Papua",
}
URUTAN_PULAU = ["Sumatera", "Jawa", "Kalimantan", "Sulawesi", "Papua"]
URUTAN_KELOMPOK = ["Perkotaan", "Jalan Raya", "Industri", "Gambut", "Latar Bersih"]

# Zona waktu (offset jam dari WIB). Timestamp AQMS tercatat dalam WIB untuk semua stasiun (booklet).
ZONA_WAKTU_PROVINSI = {
    "Kalimantan Timur": ("WITA", 1), "Kalimantan Selatan": ("WITA", 1),
    "Sulawesi Selatan": ("WITA", 1), "Sulawesi Tengah": ("WITA", 1),
    "Papua Barat Daya": ("WIT", 2), "Papua Selatan": ("WIT", 2),
}

# --------------------------------------------------------------------------- #
# Parameter preprocessing & fitur (notebook 03)
# --------------------------------------------------------------------------- #
MIN_JAM_HARIAN = 18               # rata-rata harian sah bila >= 18 dari 24 jam valid (75%)
MIN_JAM_HARIAN_LONGGAR = 12       # hanya untuk analisis sensitivitas (kolom *_longgar)
MUSIM_KEMARAU_BULAN = (5, 6, 7, 8, 9, 10)   # kemarau Mei–Okt (ketentuan proyek); selain itu hujan
EPISODE_PM25_AMBANG = 150.0       # µg/m3 harian
EPISODE_MIN_HARI = 3              # hari berurutan (kalender) agar disebut episode kabut asap
BM_HARIAN = {"pm25": 55.0, "pm10": 75.0}      # PP 22/2021, rata-rata 24 jam (µg/m3)
WHO_HARIAN = {"pm25": 15.0, "pm10": 45.0}     # WHO AQG 2021, rata-rata 24 jam (µg/m3)
# ISPU PM2.5 (Permen LHK 14/2020): konsentrasi 24 jam (µg/m3) -> indeks, interpolasi linear
ISPU_PM25_KONSENTRASI = [0.0, 15.5, 55.4, 150.4, 250.4, 500.0]
ISPU_PM25_INDEKS = [0, 50, 100, 200, 300, 500]
ISPU_KATEGORI = ["Baik", "Sedang", "Tidak Sehat", "Sangat Tidak Sehat", "Berbahaya"]
# Status analisis stasiun menurut persen jam valid (setelah pembersihan) dari 24.432 jam
AMBANG_LAYAK = 0.75               # >= 75% jam valid  -> "Layak"
AMBANG_DIKECUALIKAN = 0.10        # <  10% jam valid  -> "Dikecualikan"; di antaranya "Terbatas"
LAG_PM25 = tuple(range(0, 8))     # lag 0–7 hari


def normalisasi_provinsi(nama: str) -> str:
    """Seragamkan penulisan provinsi (mis. 'D.I. Yogyakarta' -> 'DI Yogyakarta')."""
    if not isinstance(nama, str):
        return ""
    n = nama.strip().replace("D.I.", "DI")
    return " ".join(n.split())


def pulau_dari_provinsi(provinsi: str) -> str:
    return PULAU_PROVINSI.get(normalisasi_provinsi(provinsi), "Tidak terpetakan")


def kelompok_lokasi(site_type: str) -> str:
    """Petakan `site_type` (sites.csv) ke 5 kelompok lokasi.

    Urutan aturan penting: tipe campuran (mis. 'Peatland Buffer / Urban')
    dimasukkan ke Gambut sesuai asumsi A6 pada reports/findings/01_business_understanding.md.
    """
    s = str(site_type).lower()
    if "peatland" in s:
        return "Gambut"
    if "traffic" in s or "roadside" in s:
        return "Jalan Raya"
    if "industrial" in s:
        return "Industri"
    if any(k in s for k in ("clean", "regional", "remote")):
        return "Latar Bersih"
    if "urban" in s:
        return "Perkotaan"
    return "Lainnya"
