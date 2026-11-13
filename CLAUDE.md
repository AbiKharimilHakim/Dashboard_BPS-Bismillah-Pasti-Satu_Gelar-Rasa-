# Proyek: Dashboard Analysis – DA Gelar Rasa 2026
Studi kasus kualitas udara (27 stasiun AQMS, data per jam 2024-01-01 s/d 2026-10-14) dan kesehatan
(27 RS rujukan, kasus harian). Booklet: docs/Booklet_Case_Study_DA_Gelar_Rasa_2026.pdf
Data mentah: data/raw/ (JANGAN diubah). Output olahan: data/processed/ (parquet).

## Tujuan lomba (dari booklet)
1. Kondisi kualitas udara per waktu & wilayah, vs baku mutu & tren
2. Waktu & wilayah kritis (jam, hari kerja/akhir pekan, musim, kabut asap karhutla; kota vs industri vs latar bersih)
3. Faktor pemicu (suhu, kelembapan, angin, lalu lintas, jarak ke jalan, tipe lokasi)
4. Dampak kesehatan (ISPA balita/lansia, asma, PPOK, CVD, kematian; efek jeda/lag)
5. Kecukupan jaringan pemantauan & wilayah prioritas stasiun baru
6. Dashboard interaktif dengan storytelling

## Kriteria penilaian (prioritaskan ini)
- Dashboard 70: kedalaman informasi (15), relevan & KONSISTEN antarbagian (10), visual mudah dipahami (10),
  desain menarik (5), warna/font/layout konsisten (5), navigasi intuitif (15), fitur interaktif (10)
- Laporan 30: kesimpulan sesuai data (10), kualitas preprocessing & EDA (10), struktur (5), kerapian bahasa (5)
=> Setiap angka di laporan & dashboard harus berasal dari satu sumber yang sama (data/processed).
=> Setiap langkah preprocessing harus terdokumentasi (sebelum vs sesudah, jumlah baris terdampak).

## Acuan
- PP 22/2021: PM2.5 harian 55, tahunan 15 µg/m³; PM10 harian 75, tahunan 40 µg/m³
- ISPU PM2.5 (Permen LHK 14/2020): Baik ≤15,5 | Sedang ≤55,4 | Tidak Sehat ≤150,4 | Sangat Tidak Sehat ≤250,4 | Berbahaya >250,4
- WHO 2021: PM2.5 harian 15, tahunan 5 µg/m³

## Masalah data yang sudah diketahui (verifikasi ulang, jangan diasumsikan)
- BJB-01, MDN-01, PSW-01 memakai kolom *_ppm (PM: ×1000; gas: ppm×BM/24,45×1000; BM SO2 64,07, CO 28,01, O3 48,00, NO2 46,01)
- JMB-02 Muaro Jambi: teks error (0xDEADBEEF, ERR_COMM_TIMEOUT, #VALUE!, dll), -9999, timestamp 1970, hanya ~0,5% VALID
- PLB-01: ~36rb baris (duplikat per jam); MDN-01: ~3.600 jam hilang; MER-01: ~20% VALID, PM negatif, suhu 99
- SM2-01: nilai 999 = saturasi alat saat kabut asap (bertanda SUSPECT)
- Timestamp bergeser (mis. 23:48, 00:11, milidetik) -> bulatkan ke jam terdekat
- qc_flag: VALID, SUSPECT, CALIBRATING, WARMUP, MAINTENANCE, MISSING, dll.
- Anomali: BJB-01 pola musim terbalik vs stasiun gambut lain; BJB-01 & SM2-01 PM2.5 tinggi tapi kasus RS rendah
- Relasi: RS-XXX-NN <-> SENS-0NN <-> LOC di sites.csv

## Konvensi kode
- Python 3.11+, pandas, numpy, plotly, scipy, statsmodels, scikit-learn, pymannkendall
- Struktur: notebooks/ (01–05), src/ (fungsi reusable), data/processed/, reports/figures/, reports/findings/
- Semua grafik pakai src/style.py (palet warna ISPU & tipe lokasi, font, template plotly) agar konsisten
- Label grafik & teks dalam Bahasa Indonesia, satuan selalu ditulis
- Setiap notebook diakhiri sel markdown "Temuan" berisi poin-poin yang siap dikutip ke laporan,
  dan menyimpan ringkasannya ke reports/findings/0X_*.md
- Jangan menyimpulkan kausalitas dari korelasi; tulis keterbatasan secara jujur