"""Kamus istilah dan nama lokasi untuk seluruh dashboard: satu konsep = satu istilah.

Semua kode internal (KTG-02, RS-XXX-05, ...) hanya dipakai untuk menggabungkan tabel; yang tampil di layar selalu nama daerah
dari data/processed/nama_lokasi.csv. Modul ini juga memuat format angka/tanggal Indonesia dan sumber tunggal untuk
reports/glosarium.md (lihat `glosarium_md`).
"""
from __future__ import annotations

import html
import re

import pandas as pd

from src import config as cfg
from src.eda import fl, rp  # noqa: F401  (koma desimal, titik ribuan)

# --------------------------------------------------------------------------- #
# nama lokasi (nama_lokasi.csv)
# --------------------------------------------------------------------------- #
_NAMA = pd.read_csv(cfg.PROC_DIR / "nama_lokasi.csv")
_SITES = pd.read_parquet(cfg.PROC_DIR / "sites_clean.parquet")[["kode_stasiun", "hospital_id", "status_sensor"]]
PENDEK: dict[str, str] = dict(zip(_NAMA.kode, _NAMA.nama_pendek))
TAMPIL: dict[str, str] = dict(zip(_NAMA.kode, _NAMA.nama_tampil))
JENIS_LOK: dict[str, str] = dict(zip(_NAMA.kode, _NAMA.jenis_wilayah))
KOTA: dict[str, str] = dict(zip(_NAMA.kode, _NAMA.kota_kabupaten))
KODE_DARI_PENDEK: dict[str, str] = {v: k for k, v in PENDEK.items()}
RS_DARI_KODE: dict[str, str] = {r.hospital_id: "rumah sakit di " + PENDEK[r.kode_stasiun] for r in _SITES.itertuples()}
DAFTAR_NAMA: list[str] = sorted(PENDEK.values())

# jenis wilayah: nama internal (data) → nama untuk pembaca
JENIS = {"Perkotaan": "Pusat Kota", "Jalan Raya": "Pinggir Jalan Raya", "Industri": "Kawasan Industri", "Gambut": "Lahan Gambut", "Latar Bersih": "Daerah Bersih"}
JENIS_URUT = [JENIS[t] for t in cfg.URUTAN_KELOMPOK]
INTERNAL_DARI_JENIS = {v: k for k, v in JENIS.items()}
JENIS_ARTI = {
    "Perkotaan": "Pusat Kota adalah daerah perkotaan padat dengan permukiman, perkantoran, dan lalu lintas sehari-hari.",
    "Jalan Raya": "Pinggir Jalan Raya adalah lokasi di tepi jalan padat yang langsung terpapar asap kendaraan.",
    "Industri": "Kawasan Industri adalah lokasi di sekitar pabrik, pelabuhan, atau kawasan industri yang mengeluarkan emisi.",
    "Gambut": "Lahan Gambut adalah daerah dengan lahan gambut yang rawan terbakar saat musim kemarau.",
    "Latar Bersih": "Daerah Bersih adalah daerah pegunungan atau pedesaan yang jauh dari sumber polusi dan dipakai sebagai pembanding.",
}

POL_NAMA = {"pm25": "Debu halus (PM2.5)", "pm10": "Debu kasar (PM10)", "no2": "Gas NO₂", "so2": "Gas SO₂", "co": "Gas CO", "o3": "Gas O₃"}
POL_PENDEK = {"pm25": "PM2.5", "pm10": "PM10", "no2": "NO₂", "so2": "SO₂", "co": "CO", "o3": "O₃"}
BATAS_NAMA = {"PP 22/2021": "Batas aman nasional", "WHO 2021": "Batas aman WHO"}
CUACA_NAMA = {"temperature_c": "Suhu", "humidity_pct": "Kelembapan", "wind_speed_ms": "Kecepatan angin"}
KASUS_NAMA = {"ISPA balita (<5 th)": "ISPA balita (di bawah 5 tahun)", "ISPA lansia (>60 th)": "ISPA lansia (di atas 60 tahun)", "Asma (IGD)": "Asma (pasien IGD)",
              "PPOK": "Penyakit paru kronis", "Pernapasan umum": "Gangguan pernapasan lainnya", "Kardiovaskular": "Penyakit jantung dan pembuluh darah", "Kematian": "Kematian"}
KASUS_PENDEK = {"ISPA balita (<5 th)": "ISPA balita", "ISPA lansia (>60 th)": "ISPA lansia", "Asma (IGD)": "asma", "PPOK": "penyakit paru kronis", "Pernapasan umum": "gangguan pernapasan",
                "Kardiovaskular": "penyakit jantung", "Kematian": "kematian"}
STATUS_DATA = {"Layak": "Data lengkap", "Terbatas": "Data terbatas", "Dikecualikan": "Tidak dipakai"}
STATUS_ALAT = {"Active": "Berfungsi baik", "Intermittent": "Bermasalah", "Defective": "Bermasalah"}
METODE = {"Random Forest": "Metode komputer canggih 1", "Gradient Boosting": "Metode komputer canggih 2", "Regresi berganda": "Metode sederhana (garis lurus)"}
FAKTOR = {"Lalu lintas & jarak ke jalan": "Lalu lintas & jarak ke jalan", "Waktu (bulan, hari-tahun, hari-minggu)": "Waktu (bulan & hari)",
          "Cuaca (suhu, kelembapan, angin)": "Cuaca (suhu, kelembapan, angin)", "Tipe lokasi": "Jenis wilayah"}
KATEGORI_ARTI = {"Baik": "Aman untuk semua orang.", "Sedang": "Dapat diterima, tetapi orang yang sangat sensitif sebaiknya waspada.",
                 "Tidak Sehat": "Kurangi aktivitas di luar ruangan.", "Sangat Tidak Sehat": "Hindari aktivitas di luar ruangan dan gunakan masker.", "Berbahaya": "Tetap di dalam ruangan."}
PESAN_KOSONG = "Belum ada data untuk pilihan ini. Pilih daerah atau periode lain."

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
BULAN_PANJANG = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def tgl(t) -> str:
    """'14 Okt 2026' (nama bulan Indonesia)."""
    t = pd.Timestamp(t)
    return f"{t.day} {BULAN[t.month - 1]} {t.year}"


def bln(t) -> str:
    t = pd.Timestamp(t)
    return f"{BULAN[t.month - 1]} {t.year}"


def pendek(kode: str) -> str:
    return PENDEK.get(kode, kode)


def kecil(nama_batas: str) -> str:
    """"Batas aman nasional" → "batas aman nasional"; "Batas aman WHO" → "batas aman WHO" (singkatan WHO tetap kapital)."""
    return nama_batas[:1].lower() + nama_batas[1:]


def kekuatan(r: float) -> str:
    """Kekuatan hubungan untuk pembaca awam (angka r hanya di tooltip)."""
    if r is None or pd.isna(r):
        return "tidak dapat dihitung"
    a = abs(float(r))
    return "lemah" if a < 0.3 else ("sedang" if a < 0.6 else "kuat")


def arah(r: float) -> str:
    return "searah (naik bersama)" if r > 0 else "berlawanan (satu naik, yang lain turun)"


def bagian_hari(jam: int) -> str:
    return "dini hari" if jam < 5 else "pagi" if jam < 11 else "siang" if jam < 15 else "sore" if jam < 19 else "malam"


# --------------------------------------------------------------------------- #
# tooltip (ⓘ) — isi diambil dari kamus ini
# --------------------------------------------------------------------------- #
TIPS = {
    "lokasi": "Lokasi pengukuran adalah tempat alat pengukur udara dipasang. Warna titik mengikuti kategori ISPU (Indeks Standar Pencemar Udara) berdasarkan rata-rata PM2.5.",
"lengkap": "Lokasi yang catatan alatnya cukup lengkap sehingga layak dianalisis.",
    "pm25": "PM2.5 adalah partikel debu sangat kecil, sekitar 30 kali lebih kecil daripada rambut, yang dapat masuk ke paru-paru.",
    "pm10": "PM10 adalah partikel debu yang lebih besar daripada debu halus, misalnya debu jalan dan bangunan.",
    "gas": "NO₂ berasal dari asap kendaraan dan pabrik; SO₂ dari pembakaran batu bara dan minyak; CO dari pembakaran tidak sempurna; O₃ (ozon) terbentuk dari reaksi sinar matahari dengan polusi.",
    "ugm3": "Mikrogram per meter kubik udara: banyaknya zat pencemar di setiap 1 meter kubik udara.",
    "batas_nasional": "Batas aman dari aturan pemerintah (PP 22/2021): debu halus 55 µg/m³ per hari dan 15 µg/m³ per tahun.",
    "batas_who": "Batas aman dari pedoman Badan Kesehatan Dunia (WHO) 2021: debu halus 15 µg/m³ per hari. Lebih ketat daripada batas nasional.",
    "kategori": "ISPU (Indeks Standar Pencemar Udara) membagi kualitas udara menjadi lima kategori: Baik, Sedang, Tidak Sehat, Sangat Tidak Sehat, dan Berbahaya. Semakin tinggi kategorinya, semakin besar risikonya bagi kesehatan.",
    "kabut_asap": "Kabut asap adalah polusi debu halus (PM2.5) di atas 150 µg/m³ selama minimal 3 hari berturut-turut.",
    "jenis": "Jenis wilayah terdiri atas Pusat Kota, Pinggir Jalan Raya, Kawasan Industri, Lahan Gambut, dan Daerah Bersih (kawasan pegunungan atau pedesaan).",
    "jeda": "Selang waktu antara naiknya polusi dan munculnya pasien di rumah sakit, misalnya 3 hari kemudian.",
    "nilai_tengah": "Angka yang berada di tengah jika semua nilai diurutkan. Angka ini tidak mudah terpengaruh oleh nilai yang sangat tinggi atau sangat rendah.",
    "ispa": "ISPA (infeksi saluran pernapasan akut) mencakup batuk, pilek, radang tenggorokan, hingga radang paru.",
    "risiko": "Berapa kali lipat jumlah pasien bila polusi naik. Contohnya, 1,086 berarti pasien bertambah sekitar 8,6%.",
    "nyata": "Perubahan yang cukup besar dan konsisten sehingga kecil kemungkinan terjadi hanya karena kebetulan.",
    "kekuatan": "Seberapa erat dua hal bergerak bersama, yaitu lemah, sedang, atau kuat. Angka pastinya tampil saat kursor diarahkan ke grafik.",
    "catatan_dipakai": "Catatan harian alat pengukur yang lengkap dan lolos pemeriksaan sehingga layak dianalisis.",
    "skor_risiko": "Skor 0–100 gabungan beban polusi, beban kesehatan, kerentanan, dan tren. Hanya untuk membandingkan antardaerah, bukan risiko sebenarnya.",
    "tambahan_pasien": "Perkiraan jumlah pasien tambahan saat kabut asap dibandingkan hari biasa. Hasilnya berupa kisaran, dari yang paling hati-hati hingga perkiraan model, karena bergantung pada asumsi.",
}


def tip(kunci: str, ikon: str = "ⓘ") -> str:
    """HTML ikon (i) dengan tooltip. Dipakai di dalam st.markdown(unsafe_allow_html=True)."""
    return f'<span class="tip" tabindex="0" data-tip="{html.escape(TIPS[kunci], quote=True)}">{ikon}</span>'


def istilah(label: str, kunci: str) -> str:
    return f"{html.escape(label)} {tip(kunci)}"


# --------------------------------------------------------------------------- #
# kamus istilah (tabel di halaman TENTANG DATA dan reports/glosarium.md)
# --------------------------------------------------------------------------- #
GLOSARIUM: list[tuple[str, str, str]] = [
    ("Lokasi pengukuran", "Tempat alat pengukur udara dipasang.", "Alat di Jakarta Pusat (Gambir)."),
    ("Sebaran lokasi pengukuran", "Pola penyebaran lokasi pengukuran di seluruh Indonesia.", "17 provinsi belum memiliki lokasi pengukuran."),
    ("Jenis wilayah", "Pengelompokan lokasi menurut lingkungannya: Pusat Kota, Pinggir Jalan Raya, Kawasan Industri, Lahan Gambut, Daerah Bersih (pegunungan/pedesaan).", "Palembang tergolong Lahan Gambut."),
    ("Pulau", "Kelompok daerah menurut pulau besar: Sumatera, Jawa, Kalimantan, Sulawesi, Papua.", "Sampit berada di pulau Kalimantan."),
    ("Debu halus (PM2.5)", "Partikel debu sangat kecil (sekitar 30 kali lebih kecil daripada rambut) yang dapat masuk ke paru-paru. Penyebab utama polusi asap kebakaran.", "Asap kebakaran lahan gambut."),
    ("Debu kasar (PM10)", "Partikel debu yang lebih besar dari debu halus, misalnya debu jalan dan bangunan.", "Debu dari jalan berkendaraan padat."),
    ("Gas pencemar", "Gas berbahaya di udara: NO₂ (asap kendaraan dan pabrik), SO₂ (pembakaran batu bara dan minyak), CO (pembakaran tidak sempurna), O₃ (ozon permukaan).", "NO₂ tinggi di jalan raya saat jam sibuk."),
    ("µg/m³", "Mikrogram per meter kubik udara: banyaknya zat pencemar di setiap 1 meter kubik udara.", "55 µg/m³ = 55 sepersejuta gram debu dalam 1 m³ udara."),
    ("Batas aman nasional", "Batas polusi dari aturan pemerintah (PP 22/2021): debu halus 55 µg/m³ per hari dan 15 µg/m³ per tahun.", "Hari dengan 60 µg/m³ dianggap melewati batas."),
    ("Batas aman WHO", "Pedoman Badan Kesehatan Dunia 2021: debu halus 15 µg/m³ per hari dan 5 µg/m³ per tahun. Lebih ketat daripada batas nasional.", "Hampir semua lokasi melewati batas ini hampir setiap hari."),
    ("Kategori udara", "Penilaian kualitas udara harian: Baik; Sedang; Tidak Sehat (kurangi aktivitas di luar); Sangat Tidak Sehat (hindari aktivitas di luar, pakai masker); Berbahaya (tetap di dalam ruangan).", "Udara 80 µg/m³ berkategori Tidak Sehat."),
    ("Kabut asap (kejadian)", "Polusi debu halus sangat tinggi (di atas 150 µg/m³) selama minimal 3 hari berturut-turut.", "Palembang, 24 Sep–10 Okt 2026."),
    ("Musim kemarau", "Bulan Mei sampai Oktober, saat lahan kering mudah terbakar.", "Kabut asap terjadi pada Agustus–Oktober."),
    ("Jeda waktu", "Selang waktu antara naiknya polusi dan munculnya pasien di rumah sakit.", "'3 hari kemudian' berarti pasien bertambah 3 hari setelah polusi naik."),
    ("Kekuatan hubungan", "Seberapa erat dua hal bergerak bersama: lemah, sedang, atau kuat. Bukan bukti sebab-akibat.", "Lalu lintas dan polusi memiliki hubungan kuat antarlokasi."),
    ("Perubahan nyata", "Perubahan yang cukup besar dan konsisten sehingga kecil kemungkinan hanya kebetulan.", "Belum ada lokasi yang polusinya berubah nyata dari tahun ke tahun."),
    ("Rata-rata kenaikan per tahun", "Seberapa besar polusi naik (atau turun) rata-rata tiap tahun.", "0,010 µg/m³ per tahun = hampir tidak berubah."),
    ("Nilai tengah", "Angka yang berada di tengah bila semua nilai diurutkan. Tidak mudah terpengaruh nilai yang sangat tinggi atau rendah.", "Nilai tengah 30,8 µg/m³ berarti separuh hari lebih rendah dari itu."),
    ("Nilai tidak wajar", "Angka yang menyimpang jauh dari yang lain, misalnya karena alat rusak atau macet.", "Angka 999 µg/m³ yang berulang-ulang."),
    ("Catatan alat macet", "Alat menampilkan angka yang persis sama berjam-jam atau berhari-hari. Catatan seperti ini dibuang dari analisis.", "Alat di Banjarbaru menampilkan 336,7 selama 4.886 jam."),
    ("Data yang dapat dipakai", "Catatan alat yang lengkap dan lolos pemeriksaan sehingga layak dianalisis. Seberapa lengkap catatan alat dinyatakan dalam persen.", "Merauke hanya memiliki sekitar 20% catatan yang dapat dipakai."),
    ("Alat berfungsi baik / bermasalah", "Status alat pengukur: berfungsi baik berarti hampir selalu merekam; bermasalah berarti sering terputus atau rusak.", "Alat di Muaro Jambi bermasalah."),
    ("Infeksi saluran pernapasan (ISPA)", "Penyakit batuk, pilek, radang tenggorokan, hingga radang paru. Balita dan lansia paling rentan.", "ISPA balita: pasien ISPA berusia di bawah 5 tahun."),
    ("Penyakit paru kronis", "Penyakit paru jangka panjang yang membuat napas sesak (nama medisnya PPOK).", "Perokok dan penderita asma lama rentan."),
    ("Penyakit jantung dan pembuluh darah", "Gangguan jantung dan pembuluh darah, misalnya serangan jantung dan stroke.", "Pasien jantung bertambah saat polusi tinggi."),
    ("Kenaikan pasien (kali lipat)", "Berapa kali lipat jumlah pasien bila polusi naik. Setiap debu halus naik 10 µg/m³, pasien ISPA balita bertambah sekitar 8,6%.", "1,086 kali = naik 8,6%."),
    ("Tambahan pasien saat kabut asap", "Perkiraan jumlah pasien tambahan saat kabut asap dibandingkan hari biasa. Disajikan sebagai kisaran karena bergantung pada asumsi.", "2.402–3.403 pasien ISPA balita."),
    ("Skor risiko daerah", "Skor 0–100 gabungan beban polusi, beban kesehatan, kerentanan, dan tren. Hanya untuk membandingkan antardaerah.", "Sampit skor 81 (tertinggi)."),
    ("Seberapa besar pengaruh tiap faktor", "Ukuran seberapa besar kemampuan menebak polusi turun bila satu faktor dihilangkan. Semakin besar, semakin berpengaruh.", "Lokasi dan bulan berpengaruh besar, cuaca nyaris tidak."),
]


def glosarium_md() -> str:
    """Isi reports/glosarium.md (sumber sama dengan tabel Kamus Istilah di dashboard)."""
    b = ["# Glosarium", "", "> Istilah yang dipakai di dasbor dan laporan. Satu konsep = satu istilah.", "", "| Istilah | Arti sederhana | Contoh |", "|---|---|---|"]
    b += [f"| {a} | {r} | {c} |" for a, r, c in GLOSARIUM]
    b += ["", "## Kategori udara dan artinya bagi masyarakat", "", "| Kategori | Artinya |", "|---|---|"] + [f"| {k} | {v} |" for k, v in KATEGORI_ARTI.items()]
    return "\n".join(b) + "\n"


# --------------------------------------------------------------------------- #
# pembersih kode (hanya dipakai pada teks teknis yang berasal dari berkas laporan)
# --------------------------------------------------------------------------- #
_RE_KODE = re.compile(r"\b([A-Z]{3}-\d{2})\b")
_RE_RS = re.compile(r"\bRS-XXX-(\d{2})\b")
_RE_SENS = re.compile(r"\b(SENS-\d{3}|LOC-[A-Z0-9]+-\d{2})\b")
_RE_EP = re.compile(r"\b([A-Z]{3}-\d{2})-E(\d+)\b")


def bersihkan(teks) -> str:
    """Ganti kode lokasi/rumah sakit/alat di dalam teks dengan nama daerah."""
    if teks is None or (isinstance(teks, float) and pd.isna(teks)):
        return ""
    t = str(teks)
    t = _RE_EP.sub(lambda m: f"kejadian ke-{m.group(2)} di {PENDEK.get(m.group(1), m.group(1))}", t)
    t = _RE_RS.sub(lambda m: RS_DARI_KODE.get(f"RS-XXX-{m.group(1)}", "rumah sakit"), t)
    t = _RE_KODE.sub(lambda m: PENDEK.get(m.group(1), m.group(1)), t)
    t = _RE_SENS.sub("alat pengukur", t)
    return t
