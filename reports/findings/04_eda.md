# 04 — EDA: Temuan
> Dihasilkan otomatis oleh `notebooks/04_eda.ipynb` dari `data/processed/` (hasil notebook 03). Angka identik dengan `reports/key_numbers.json`. 20 grafik tersimpan di `reports/figures/04_*` (PNG 1600 px + HTML).
> Semua uji nonparametrik; sampel berklaster per stasiun sehingga **ukuran efek** (ε², r, ρ) lebih informatif daripada nilai-p. Seluruh hubungan adalah asosiasi, bukan kausalitas.

## Cakupan
26 stasiun pada tabel per jam; 25 stasiun dengan ≥ 100 hari PM2.5 sah dipakai untuk analisis harian (24.234 hari-stasiun); 591.047 jam PM2.5. Ditinggalkan pada analisis harian: MER-01. Tren hanya memakai stasiun Layak (22).

## A. Kondisi & tren (Tujuan 1)
- **Tingkat PM2.5.** Rata-rata harian seluruh stasiun-hari 41,7 µg/m³ (median 30,8). 22 dari 25 stasiun rata-ratanya > 15 µg/m³ (PP 22/2021 tahunan) dan 25 > 5 µg/m³ (WHO). Tertinggi BJB-01 (102,1), terendah IDP-01 (9,3).
- **Baku mutu.** 17,3% hari melebihi 55 µg/m³ (PP 22/2021) dan 82,6% melebihi 15 µg/m³ (WHO). Pelampauan tertinggi pada Industri (36,2% hari); χ² tipe × pelampauan p < 0,001, V = 0,34.
- **ISPU PM2.5.** Baik 17,7%, Sedang 65,1%, Tidak Sehat 15,2%, Sangat Tidak Sehat 0,7%, Berbahaya 1,2%; Tidak Sehat atau lebih buruk 17,2% hari.
- **Tren (Mann-Kendall musiman + Sen, bulanan, 22 stasiun Layak).** 1 stasiun signifikan tanpa koreksi, **0** setelah Benjamini–Hochberg; median kemiringan Sen 0,010 µg/m³/tahun. Agregat: τ = 0,20, p = 0,405. Hanya 2,8 tahun data (daya rendah) — tidak ada bukti tren, bukan bukti stabil. SM2-01/PLB-01/MDN-01/MER-01 dikeluarkan karena pola data hilang menciptakan tren palsu.
- **Antar pulau & tipe (Kruskal-Wallis + Dunn–Holm).** Pulau: H = 1.888, ε² = 0,078; tipe: H = 10.575, ε² = 0,436; 9/10 pasangan tipe dan 10/10 pasangan pulau signifikan. Ketahanan (unit stasiun): tipe p = 0,010, pulau p = 0,539.

| tipe lokasi   | stasiun   | hari   | rata-rata   | median   | P95   | maks    |
|:--------------|:----------|:-------|:------------|:---------|:------|:--------|
| Perkotaan     | 7         | 6.479  | 42,8        | 37,0     | 78,0  | 1.127,6 |
| Jalan Raya    | 2         | 2.036  | 36,6        | 35,1     | 58,4  | 60,3    |
| Industri      | 4         | 3.825  | 50,5        | 44,9     | 97,2  | 292,3   |
| Gambut        | 7         | 6.804  | 57,9        | 33,4     | 156,1 | 1.119,6 |
| Latar Bersih  | 5         | 5.090  | 14,2        | 13,0     | 24,4  | 189,0   |

## B. Pola waktu (Tujuan 2)
- **Diurnal.** Amplitudo relatif PM2.5 per tipe: Perkotaan 69%, Jalan Raya 26%, Industri 57%, Gambut 68%, Latar Bersih 68% (KW antar tipe p = 0,377). Jam puncak NO₂ median: Perkotaan pukul 8, Jalan Raya pukul 17, Industri pukul 8, Gambut pukul 8, Latar Bersih pukul 8.
- **Musim.** Kemarau (Mei–Okt) vs hujan, r (>0 = kemarau lebih tinggi): Perkotaan 0,62, Jalan Raya 0,17, Industri 0,57, Gambut 0,62, Latar Bersih 0,51.
- **Hari kerja vs akhir pekan.** PM2.5: 1/25 stasiun signifikan (median r 0,000); NO₂: 0/25 (median r -0,013). Efek hari kerja/akhir pekan diabaikan (kalah jauh dibanding efek musim).
- **STL.** Kekuatan musiman median per tipe: Perkotaan 1,00, Jalan Raya 0,75, Industri 1,00, Gambut 1,00, Latar Bersih 1,00; kekuatan tren median per tipe: Perkotaan 0,04, Jalan Raya 0,10, Industri 0,23, Gambut 0,98, Latar Bersih 0,17 (tinggi pada Gambut karena musim asap 2026, bukan tren bertahap). Dengan 33 bulan, kekuatan musiman ≈ 1,0 bersifat indikatif.
- **Episode kabut asap.** 21 episode pada 7 stasiun (396 hari); puncak harian tertinggi KTG-01-E01: 1.128 µg/m³ (2026-10-14). Tanpa BJB-01 (anomali 204 hari): 20 episode, 100,0% hari pada Agu–Okt (binomial p < 0,001). 5 episode (KTG-02, KTG-01, PKN-01, STG-01, PLB-01) masih berjalan pada hari terakhir data (tersensor kanan). Per tahun mulai (tanpa BJB-01): 2024: 4 episode, puncak 245 µg/m³; 2025: 6 episode, puncak 207 µg/m³; 2026: 10 episode, puncak 1.128 µg/m³. Tabel lengkap: `reports/episode_kabut_asap.csv`.

| episode    | mulai      | selesai    | hari   | puncak harian   | tanggal_puncak   | puncak jam   | kategori puncak    | status_stasiun   | tersensor kanan   |
|:-----------|:-----------|:-----------|:-------|:----------------|:-----------------|:-------------|:-------------------|:-----------------|:------------------|
| SM2-01-E01 | 2024-09-01 | 2024-09-04 | 4      | 233             | 2024-09-01       | 562          | Sangat Tidak Sehat | Terbatas         | False             |
| BJB-01-E01 | 2024-09-07 | 2025-03-29 | 204    | 337             | 2024-09-07       | 337          | Berbahaya          | Layak            | False             |
| SM2-01-E02 | 2024-09-11 | 2024-09-14 | 4      | 245             | 2024-09-11       | 577          | Sangat Tidak Sehat | Terbatas         | False             |
| SM2-01-E03 | 2024-10-03 | 2024-10-05 | 3      | 191             | 2024-10-03       | 526          | Sangat Tidak Sehat | Terbatas         | False             |
| SM2-01-E04 | 2024-10-22 | 2024-10-24 | 3      | 210             | 2024-10-23       | 580          | Sangat Tidak Sehat | Terbatas         | False             |
| PLB-01-E01 | 2025-08-30 | 2025-09-05 | 7      | 178             | 2025-09-03       | 200          | Sangat Tidak Sehat | Terbatas         | False             |
| SM2-01-E05 | 2025-09-12 | 2025-09-14 | 3      | 207             | 2025-09-12       | 561          | Sangat Tidak Sehat | Terbatas         | False             |
| PLB-01-E02 | 2025-09-16 | 2025-09-18 | 3      | 178             | 2025-09-16       | 202          | Sangat Tidak Sehat | Terbatas         | False             |
| PLB-01-E03 | 2025-09-26 | 2025-10-05 | 10     | 177             | 2025-09-28       | 202          | Sangat Tidak Sehat | Terbatas         | False             |
| PLB-01-E04 | 2025-10-14 | 2025-10-18 | 5      | 174             | 2025-10-16       | 197          | Sangat Tidak Sehat | Terbatas         | False             |
| PLB-01-E05 | 2025-10-26 | 2025-10-30 | 5      | 174             | 2025-10-28       | 197          | Sangat Tidak Sehat | Terbatas         | False             |
| PLB-01-E06 | 2026-08-05 | 2026-08-08 | 4      | 182             | 2026-08-05       | 206          | Sangat Tidak Sehat | Terbatas         | False             |
| SM2-01-E06 | 2026-08-13 | 2026-08-15 | 3      | 163             | 2026-08-14       | 286          | Sangat Tidak Sehat | Terbatas         | False             |
| PLB-01-E07 | 2026-08-30 | 2026-09-07 | 9      | 193             | 2026-09-03       | 214          | Sangat Tidak Sehat | Terbatas         | False             |
| KTG-02-E01 | 2026-09-01 | 2026-10-14 | 44     | 1.120           | 2026-10-14       | 1.531        | Berbahaya          | Layak            | True              |
| KTG-01-E01 | 2026-09-01 | 2026-10-14 | 44     | 1.128           | 2026-10-14       | 1.620        | Berbahaya          | Layak            | True              |
| PLB-01-E08 | 2026-09-11 | 2026-09-20 | 10     | 193             | 2026-09-16       | 217          | Sangat Tidak Sehat | Terbatas         | False             |
| PLB-01-E09 | 2026-09-24 | 2026-10-10 | 17     | 238             | 2026-10-09       | 282          | Sangat Tidak Sehat | Terbatas         | False             |
| PKN-01-E01 | 2026-10-09 | 2026-10-14 | 6      | 628             | 2026-10-14       | 646          | Berbahaya          | Layak            | True              |
| STG-01-E01 | 2026-10-10 | 2026-10-14 | 5      | 320             | 2026-10-14       | 338          | Berbahaya          | Layak            | True              |
| PLB-01-E10 | 2026-10-12 | 2026-10-14 | 3      | 239             | 2026-10-14       | 283          | Sangat Tidak Sehat | Terbatas         | True              |

## C. Hubungan antarvariabel (Tujuan 3)
- **Cuaca (Spearman within-station, per tipe).** 22/90 pasangan signifikan setelah BH, dan 0 yang berukuran sedang (|ρ| ≥ 0,3). Median ρ PM2.5: kecepatan angin -0,01, kelembapan 0,00, suhu 0,01.
- **Mawar angin.** Efek arah angin terhadap PM2.5 dapat diabaikan (ε² ≤ 0,000); sektor tertinggi per stasiun: JKT-01 B, JKT-03 UTL, JKT-02 TL, KTG-01 S, BGR-01 BD.
- **Antar stasiun (n = 26).** Lalu lintas vs median PM2.5: ρ = 0,77 (p < 0,001); tanpa gambut ρ = 0,76. Lalu lintas vs NO₂: ρ = 0,46 (p = 0,018). Jarak ke jalan vs NO₂: ρ = -0,44.
- **Tipe lokasi.** Perbedaan antar tipe signifikan pada semua polutan; ε²: PM2.5 0,44, NO₂ 0,21, CO 0,23, SO₂ 0,22.

## D. Kesehatan (Tujuan 4)
- **Korelasi per RS (25 RS, unit independen).** ISPA balita, lag terbaik 0: rata-rata ρ = 0,40 (varian A, within-RS) → 0,12 (varian B, musiman dibuang). Rata-rata ρ ISPA balita berubah hanya 0,02 dari lag 0 ke 7 (profil datar), sehingga jeda efek spesifik tidak teridentifikasi.
- **Balita vs lansia.** Rata-rata ρ (lag 0–7), varian A: balita 0,39 vs lansia 0,38 (Wilcoxon berpasangan p = 0,426); varian B: 0,01 vs 0,01 (p = 0,120).
- **Heterogenitas.** ρ antar-RS -0,17 hingga 0,91; antar tipe lokasi KW p = 0,061. Rata-rata ρ semua RS 0,40; tanpa BJB-01 & SM2-01 0,42; tanpa gambut 0,30.
- **Dosis-respons (lag 0).** Rasio kasus ÷ rata-rata RS pada kelas PM2.5 terendah → tertinggi: ISPA balita 0,97 → 1,86; ISPA lansia 0,97 → 1,84.

## E. Distribusi & outlier
- PM2.5 per jam: median 30,0, P99 337, maks 1.620 µg/m³; skewness 7,4 (log: 0,27); 0,16% jam > 500 µg/m³.
- Outlier harian: 1.086 hari ringan (30,3% di episode), 419 ekstrem (76,8% di episode); odds ratio outlier × episode 149,7 (Fisher p < 0,001). 97 hari ekstrem di luar episode (85 di SM2-01; 75 bersebelahan dengan hari tanpa rata-rata sah) adalah hari berasap yang rangkaiannya terputus data hilang, bukan untuk dihapus.

## Keterbatasan
1. Sampel berklaster per stasiun dan autokorelasi harian/jam: nilai-p cenderung optimistis; ukuran efek dan uji ketahanan berbasis stasiun diberikan.
2. Hanya 2,8 tahun data (2026 parsial): daya uji tren rendah.
3. Hubungan PM2.5–kesehatan adalah asosiasi pada data sintetis; musim mengacaukan varian A, dan heterogenitas antar-RS besar (BJB-01 & SM2-01 menyimpang). Tidak ada klaim kausal.
4. SM2-01 dan PLB-01 mengalami pemangkasan puncak (lihat notebook 03); mereka dikeluarkan dari uji tren dan cenderung kurang terwakili pada episode.
5. Rata-rata pulau Papua didukung 2 stasiun (MER-01 hanya pada analisis per jam); pulau Sulawesi 2 stasiun: perbandingan antar pulau lemah.
