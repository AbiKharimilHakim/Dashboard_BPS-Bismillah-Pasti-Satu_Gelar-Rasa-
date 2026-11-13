"""Palet warna tunggal dashboard (tema merah marun–pink, aksen hijau sage, grafik pastel).

SEMUA warna di dashboard (CSS, ECharts, Plotly, peta deck.gl) dan di src/style.py diambil dari modul ini; jangan menulis kode warna di
tempat lain. Modul ini sengaja tidak mengimpor Streamlit agar bisa dipakai juga oleh notebook (lewat src/style.py).

Aturan keterbacaan: teks di atas latar berwarna harus berkontras ≥ 4,5:1 (lihat `kontras()` dan `teks_di_atas()`); warna pastel tidak
dipakai untuk teks di atas putih; makna warna selalu didampingi label atau angka.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# merah marun & pink (antarmuka)
# --------------------------------------------------------------------------- #
CRIMSON_DARK = "#6F1014"
CRIMSON = "#82242A"
MAROON = "#8C1A26"
ROSE_DEEP = "#B73750"
ROSE = "#E5506D"
ROSE_AKTIF = "#C93556"      # ROSE yang digelapkan: dipakai bila ada teks putih di atasnya (putih di atas ROSE hanya 3,68:1; di atas ROSE_AKTIF 5,09:1)
PINK = "#E9798F"
PINK_SOFT = "#F8B2B7"
BLUSH = "#FBE3E3"
PINK_TINT = "#FBEBF1"
ICON_PINK = "#C4637A"
SAGE = "#A5BF72"
COPPER = "#E0A060"

# pastel data
PASTEL_PINK = "#F5ACC2"
PASTEL_SAGE = "#CDD8B1"
PASTEL_PEACH = "#FBDFBB"
PASTEL_TEAL = "#BCD6D7"
PASTEL_LAVENDER = "#CBB6D6"

# warna data "pastel-tegas" (kategori udara & jenis wilayah)
TEAL_DATA = "#8DBFC1"
PEACH_DATA = "#F2B872"
LAVENDER_DATA = "#B49BCB"
UNGU_WHO = "#9B7FB8"        # garis batas aman WHO

# netral
LATAR = "#FEFAFB"           # latar halaman
KARTU = "#FFFFFF"
PUTIH = "#FFFFFF"
GARIS = "#F6E4EA"           # garis kartu, pemisah, kisi grafik
JUDUL = "#2E2E3A"           # judul & teks utama
TEKS2 = "#6B6B7B"           # teks sekunder
TOOLTIP = "#3A0A0D"         # latar tooltip


# --------------------------------------------------------------------------- #
# alat bantu warna
# --------------------------------------------------------------------------- #
def _rgb(hex_: str) -> tuple[int, int, int]:
    h = hex_.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgba(hex_: str, a: float) -> str:
    """'#RRGGBB' + opasitas → 'rgba(r,g,b,a)'."""
    r, g, b = _rgb(hex_)
    return f"rgba({r},{g},{b},{a})"


def campur(a: str, b: str, t: float) -> str:
    """Warna di antara a (t=0) dan b (t=1)."""
    ra, rb = _rgb(a), _rgb(b)
    return "#%02X%02X%02X" % tuple(round(x + (y - x) * t) for x, y in zip(ra, rb))


def luminans(hex_: str) -> float:
    def lin(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = _rgb(hex_)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def kontras(a: str, b: str) -> float:
    """Rasio kontras WCAG antara dua warna (1–21)."""
    la, lb = sorted((luminans(a), luminans(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def teks_di_atas(latar: str) -> str:
    """Warna teks (putih atau JUDUL) yang paling kontras di atas `latar`."""
    return PUTIH if kontras(PUTIH, latar) >= kontras(JUDUL, latar) else JUDUL


def latar_teks_putih(latar: str) -> str:
    """Latar untuk teks putih: warna aslinya bila kontras ≥ 4,5:1; ROSE diganti ROSE_AKTIF; lainnya digelapkan ke CRIMSON_DARK secukupnya."""
    if kontras(PUTIH, latar) >= 4.5:
        return latar
    if latar.upper() == ROSE:
        return ROSE_AKTIF
    for t in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6):
        c = campur(latar, CRIMSON_DARK, t)
        if kontras(PUTIH, c) >= 4.5:
            return c
    return CRIMSON_DARK


def bertingkat(warna: tuple[str, ...] | list[str], n: int) -> list[str]:
    """n warna merata di sepanjang deretan `warna` (terang → gelap)."""
    if n <= 0:
        return []
    if n == 1:
        return [warna[-1]]
    hasil = []
    for k in range(n):
        x = k / (n - 1) * (len(warna) - 1)
        i = min(int(x), len(warna) - 2)
        hasil.append(campur(warna[i], warna[i + 1], x - i))
    return hasil


# --------------------------------------------------------------------------- #
# peran warna data
# --------------------------------------------------------------------------- #
ISPU = {                      # urutan tetap: hijau → biru → kuning → merah → paling gelap
    "Baik": SAGE,
    "Sedang": TEAL_DATA,
    "Tidak Sehat": PEACH_DATA,
    "Sangat Tidak Sehat": ROSE,
    "Berbahaya": CRIMSON_DARK,
}
JENIS = {                     # kunci = nama internal jenis wilayah (src/config.py)
    "Perkotaan": LAVENDER_DATA,       # Pusat Kota
    "Jalan Raya": PEACH_DATA,         # Pinggir Jalan Raya
    "Industri": TEAL_DATA,            # Kawasan Industri
    "Gambut": ROSE,                   # Lahan Gambut
    "Latar Bersih": SAGE,             # Daerah Bersih
}
OPASITAS_BATANG = 0.85        # batang peringkat daerah: warna jenis wilayah versi pastel
PANAS = [LATAR, BLUSH, PINK_SOFT, ROSE, CRIMSON_DARK]       # peta panas jam × bulan & lapisan panas peta
SERI = ROSE_DEEP              # garis tren & seri tunggal
AREA = rgba(PINK_SOFT, 0.35)  # area di bawah garis tren
SOROT = MAROON                # elemen yang disorot
REDUP = 0.35                  # opasitas elemen yang diredupkan
BATAS = {"PP 22/2021": MAROON, "WHO 2021": UNGU_WHO}   # garis batas aman (putus-putus); kunci = app/data.py STANDAR
TAHUN = (PINK_SOFT, ROSE, CRIMSON_DARK)                      # kabut asap per tahun: lama → baru
BALITA, LANSIA = ROSE, TEAL_DATA
RADAR_GARIS, RADAR_ISI = ROSE_DEEP, rgba(PINK_SOFT, 0.5)
SPARKLINE = ROSE_DEEP
KORELASI = [TEAL_DATA, PASTEL_TEAL, LATAR, PINK_SOFT, ROSE_DEEP]   # −1 (berlawanan) … 0 … +1 (searah)
AVATAR = [PASTEL_PINK, PASTEL_PEACH, PASTEL_TEAL, PASTEL_LAVENDER]  # inisial lokasi di sidebar (tanpa makna)

# status data & prioritas (dipakai src/style.py untuk notebook dan halaman Lokasi pengukuran)
QC = {
    "VALID": SAGE, "SUSPECT": PEACH_DATA, "CALIBRATING": TEAL_DATA, "WARMUP": PASTEL_LAVENDER, "MAINTENANCE": LAVENDER_DATA,
    "MISSING": GARIS, "Galat alat": CRIMSON_DARK, "Lainnya": TEKS2,
}
PRIORITAS = {"Kritis": CRIMSON_DARK, "Tinggi": ROSE, "Sedang": PEACH_DATA, "Rendah": PASTEL_TEAL}
URUTAN_GRAFIK = [ROSE_DEEP, TEAL_DATA, LAVENDER_DATA, PEACH_DATA, SAGE, PINK, CRIMSON]   # warna seri umum (Plotly colorway)

TANPA_DATA = campur(TEKS2, PUTIH, 0.45)                      # titik peta tanpa data
STATUS = {"Layak": SAGE, "Terbatas": PEACH_DATA, "Dikecualikan": CRIMSON_DARK}   # kelengkapan data lokasi
KEMARAU, HUJAN = ROSE, PASTEL_TEAL                           # batang bulan: musim kemarau vs musim hujan
PASIEN = TEAL_DATA                                           # garis pasien (berdampingan dengan garis polusi SERI)
SKALA_KELENGKAPAN = [[0.0, LATAR], [0.25, BLUSH], [0.5, PINK_SOFT], [0.75, ROSE_DEEP], [1.0, CRIMSON_DARK]]
TRANSPARAN = "rgba(0,0,0,0)"


def skala(warna: list[str] | tuple[str, ...], t: float) -> str:
    """Warna pada posisi t (0–1) di sepanjang deretan `warna` (interpolasi linear)."""
    t = min(max(float(t), 0.0), 1.0) * (len(warna) - 1)
    i = min(int(t), len(warna) - 2)
    return campur(warna[i], warna[i + 1], t - i)


def rgb_daftar(hex_: str) -> list[int]:
    return list(_rgb(hex_))


def rgb_teks(hex_: str) -> str:
    """'r,g,b' untuk CSS rgba(var(--x), a)."""
    return ",".join(str(v) for v in _rgb(hex_))


# --------------------------------------------------------------------------- #
# peran warna antarmuka
# --------------------------------------------------------------------------- #
SIDEBAR_ATAS, SIDEBAR_BAWAH = CRIMSON_DARK, CRIMSON
FILTER_LATAR = campur(CRIMSON_DARK, "#000000", 0.22)        # kotak filter: CRIMSON_DARK sedikit lebih gelap
MENU_AKTIF = ROSE if kontras(PUTIH, ROSE) >= 4.5 else ROSE_AKTIF
LABEL_SEKSI = COPPER
TAB_AKTIF = MAROON
TAUTAN, TAUTAN_HOVER = ICON_PINK, MAROON
BAYANGAN_KARTU = rgba(ROSE_DEEP, 0.08)
BAYANGAN_KARTU_TINGGI = rgba(ROSE_DEEP, 0.18)
HEADER_KIRI, HEADER_TENGAH, HEADER_KANAN = CRIMSON_DARK, ROSE_DEEP, PINK
