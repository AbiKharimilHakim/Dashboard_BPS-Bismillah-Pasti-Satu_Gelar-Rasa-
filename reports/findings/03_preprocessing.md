# 03 — Preprocessing: Temuan
> Dihasilkan otomatis oleh `notebooks/03_preprocessing.ipynb` dari keluaran `etl/run_preprocessing.py`. Semua angka berasal dari `data/processed/*.parquet` dan `reports/preprocessing_log.csv`.
> Rincian setiap langkah (per stasiun) ada di `reports/preprocessing_log.csv`. Data mentah di `data/raw/` tidak diubah.

## 1. Ringkasan keluaran
| tabel           | baris   | kolom   | grain                                                     |
|:----------------|:--------|:--------|:----------------------------------------------------------|
| aq_hourly       | 591.047 | 24      | 1 baris = stasiun × jam (hanya jam dengan ≥1 baris VALID) |
| aq_daily        | 26.468  | 34      | 1 baris = stasiun × hari (grid kalender lengkap)          |
| health_aq_daily | 27.486  | 47      | 1 baris = RS × hari + paparan PM2.5 stasiun pasangan      |
| sites_clean     | 27      | 34      | 1 baris = stasiun (sites + sensors + hospitals)           |
| qc_summary      | 27      | 35      | 1 baris = stasiun (kualitas & status analisis)            |

Alur baris: **667.981** baris mentah (27 stasiun) → **599.185** baris `VALID` → **591.168** jam valid (27 stasiun) → **591.047** jam pada `aq_hourly` (26 stasiun; JMB-02 dikecualikan) → **26.468** hari-stasiun pada `aq_daily` (grid kalender lengkap, 24.236 hari dengan PM2.5 sah).

## 2. Dampak tiap langkah (seluruh stasiun)
| langkah   | aturan                                          | jumlah   | satuan   | stasiun_terdampak   |
|:----------|:------------------------------------------------|:---------|:---------|:--------------------|
| 1         | Teks galat → NaN                                | 43.171   | sel      | 1                   |
| 2         | ppm → µg/m³                                     | 414.240  | sel      | 3                   |
| 3         | Timestamp tak terbaca dibuang                   | 0        | baris    | 0                   |
| 3         | Timestamp di luar periode dibuang               | 132      | baris    | 1                   |
| 3         | Dibulatkan ke jam terdekat                      | 411.488  | baris    | 17                  |
| 3         | Bacaan sub-jam → floor jam penuh                | 16.025   | baris    | 2                   |
| 4         | Sentinel → NaN                                  | 43.185   | sel      | 2                   |
| 4         | Polutan negatif → NaN                           | 36.830   | sel      | 2                   |
| 4         | Cuaca di luar batas fisik → NaN                 | 59.659   | sel      | 2                   |
| 4         | Baris VALID ber-PM ekstrem (>500) DIPERTAHANKAN | 2.549    | baris    | 4                   |
| 5         | Baris non-VALID dibuang                         | 68.665   | baris    | 26                  |
| 5         | Baris digabung (rata-rata per jam)              | 8.016    | baris    | 1                   |
| 6         | Hari ditolak (< 18 jam valid)                   | 1.996    | hari     | 4                   |
| 7         | Episode kabut asap terdeteksi                   | 21       | episode  | 7                   |

## 3. Perlakuan untuk stasiun bermasalah
| kode_stasiun   | status_sensor   | persen_jam_pm25_valid   | persen_hari_pm25_valid   | persen_hari_pm25_valid_kemarau   | status_analisis   |
|:---------------|:----------------|:------------------------|:-------------------------|:---------------------------------|:------------------|
| BJB-01         | Active          | 100,0                   | 100,0                    | 100,0                            | Layak             |
| JMB-02         | Defective       | 0,5                     | –                        | –                                | Dikecualikan      |
| MDN-01         | Intermittent    | 68,1                    | 36,4                     | 37,2                             | Terbatas          |
| MER-01         | Intermittent    | 20,0                    | 0,2                      | 0,4                              | Terbatas          |
| PLB-01         | Intermittent    | 79,5                    | 68,4                     | 72,3                             | Terbatas          |
| SM2-01         | Active          | 85,0                    | 75,7                     | 53,8                             | Terbatas          |

**JMB-02 (Muaro Jambi): dikecualikan** dari `aq_hourly`, `aq_daily`, dan paparan kesehatan. Hanya 122 dari 24.432 baris `VALID` (0,50%), tidak ada baris VALID setelah 2024-08, 99,5% baris berisi nilai mustahil, dan 0 hari yang memenuhi ≥18 jam VALID. Sensor berstatus Defective. Tidak diimputasi dan tidak ada aturan yang dilonggarkan. Stasiun tetap ada di `sites_clean` dan `qc_summary` sebagai bukti kebutuhan perbaikan jaringan (Tujuan 5); RS-XXX-27 tetap ada di `health_aq_daily` dengan paparan kosong.

**MER-01 (Merauke): Terbatas.** 4.891 jam valid (20,0%) tersebar acak dalam 1.837 blok pendek; hanya 2 hari yang memenuhi ≥18 jam (54 hari bila ambang 12 jam). Nilai VALID-nya wajar dibanding stasiun latar (median PM2.5 16,1 µg/m³), sehingga **data per jam dipertahankan** untuk profil diurnal/klimatologi dan bukti kualitas jaringan, tetapi **tidak dipakai untuk model harian/efek jeda kesehatan**. Aturan 75% tidak dilonggarkan karena rata-rata dari ±6 jam tidak mewakili satu hari. Jam valid tersebar merata antar-bulan (66–213 jam/bulan), jadi tidak ada bukti bias musiman, namun puncak asap tidak mungkin tertangkap.

**Stasiun Terbatas lainnya** (MDN-01, PLB-01, SM2-01) tetap berada di tabel dengan peringatan; gunakan `status_analisis` untuk menyaringnya pada model.
- **MDN-01**: 68,1% jam valid (3.632 jam tidak tercatat di sumber; gap terpanjang 122 jam setelah pembersihan) dan hanya 36,4% hari sah.
- **PLB-01**: cakupan jam 79,5% tetapi hari sah hanya 68,4% (jam `MISSING` tersebar); logger 15 menit pada Sep–Okt dirata-rata per jam (15.933 baris), bukan dihapus sebagai duplikat.
- **SM2-01**: hari sah 75,7% secara umum, tetapi hanya **30%** pada Jul–Okt (vs 97% dengan ambang 12 jam), karena nilai saturasi 999 (`SUSPECT`) dibuang. Deteksi episode: 6 episode / 20 hari (ambang 18 jam) vs 28 episode / 223 hari (ambang 12 jam). Puncak asap SM2-01 hampir pasti **terpangkas (bias ke bawah)**.
- **BJB-01**: 100% VALID dan lolos validasi satuan, tetapi pola musimnya menyimpang dari stasiun gambut lain (lihat notebook 02) dan menghasilkan **satu episode 204 hari** (2024-09-07…2025-03-29) yang tidak lazim; dibiarkan apa adanya dan ditandai untuk EDA.

## 4. Validasi
- **21/21** pemeriksaan lulus (dijalankan di pipeline dan diulang di notebook): tidak ada duplikat (stasiun, jam), (stasiun, hari), maupun (RS, hari); semua polutan ≥ 0; semua kolom polutan `*_ug_m3` tanpa `*_ppm`; cuaca dalam batas fisik; rata-rata harian hanya dari ≥18 jam; puncak PM > 500 pada baris VALID dipertahankan (2.549 baris; PM2.5 KTG-01 maks 1.620,5 µg/m³ masih ada).
- Rekonsiliasi baris per stasiun cocok untuk seluruh 27 stasiun: mentah = tak terbaca + luar periode + non-VALID + VALID; VALID − digabung = jam akhir.
- **Konversi ppm** (BJB-01, MDN-01, PSW-01): median PM2.5 setelah ×1000 sebanding dengan `baseline_pm25` (rasio 0,80–1,29); seluruh polutan sebanding stasiun sejenis (rasio 0,65–2,04), sedangkan tanpa konversi rasionya hanya 0,0003–0,0016.

| kode_stasiun   | rasio_min   | rasio_maks   | rasio_pm25_vs_baseline   | tanpa_konversi_maks   |
|:---------------|:------------|:-------------|:-------------------------|:----------------------|
| BJB-01         | 1,165       | 1,705        | 1,289                    | 0,002                 |
| MDN-01         | 0,899       | 2,039        | 1,086                    | 0,002                 |
| PSW-01         | 0,654       | 1,445        | 0,801                    | 0,001                 |

## 5. Dampak pada data analisis
- **Sebelum vs sesudah.** PM2.5 mentah memuat nilai hingga 99.954 dan 9.369 nilai negatif (termasuk sentinel -999/-9999); sesudah pembersihan rentang antar-stasiun 8,9–58,9 µg/m³ (median) dengan maksimum 1.620,5 µg/m³. Median stasiun ppm naik dari 0,043–0,047 (label ppm) menjadi 43,5–46,5 µg/m³.
- **Kategori ISPU PM2.5** (24.236 hari sah): Baik 17,7%, Sedang 65,1%, Tidak Sehat 15,2%, Sangat Tidak Sehat 0,7%, Berbahaya 1,2%. 301 hari berkategori Berbahaya.
- **Episode kabut asap** (PM2.5 harian > 150 µg/m³, ≥ 3 hari berturut-turut): 21 episode, 396 hari pada 7 stasiun (BJB-01, KTG-01, KTG-02, PKN-01, PLB-01, SM2-01, STG-01); episode dengan PM2.5 harian tertinggi: KTG-01 44 hari, maks harian 1.128 µg/m³; KTG-02 44 hari, maks harian 1.120 µg/m³; PKN-01 6 hari, maks harian 628 µg/m³. Episode hanya dibangun dari hari dengan rata-rata sah, sehingga stasiun dengan cakupan rendah (SM2-01, PLB-01, MDN-01) cenderung **kurang mendeteksi** episode.
- **Paparan kesehatan.** 27.486 baris RS-hari; PM2.5 lag 0 tersedia pada 88,2% baris dan lag 0–7 lengkap pada 83,9%. Baris tanpa paparan dibiarkan `NaN` (tidak diimputasi) dan dapat disaring dengan `ada_paparan_pm25` / `status_analisis_stasiun`.

## 6. Keputusan, asumsi, dan perbedaan dengan dokumen sebelumnya
1. **Musim kemarau = Mei–Oktober** (ketentuan proyek), lebih lebar daripada Jun–Okt pada `01_business_understanding.md` (asumsi A5). Seluruh fitur memakai definisi Mei–Okt.
2. **Kelompok lokasi** memakai nama "Jalan Raya" (sebelumnya "Tepi Jalan") agar konsisten dengan ketentuan proyek; `src/config.py` dan notebook 02 diperbarui.
3. **Tanggal harian memakai WIB** sesuai pencatatan sumber; `jam_lokal` (WITA/WIT) disediakan hanya untuk membaca pola harian. Tanggal kasus kesehatan diasumsikan sejajar dengan tanggal WIB (selisih ≤ 2 jam untuk stasiun WITA/WIT).
4. **ISPU hanya untuk PM2.5** (breakpoint dari CLAUDE.md); parameter lain belum dihitung karena breakpoint belum diverifikasi terhadap naskah Permen LHK 14/2020.
5. **Rata-rata 3 hari** (`pm25_ma3`) mensyaratkan 3 hari lengkap (tanpa `min_periods` longgar); lag dihitung per hari **kalender** pada grid lengkap sehingga hari tanpa data menjadi `NaN`, bukan menggeser baris.
6. **Status analisis** (Layak ≥ 75% pada jam, hari, dan hari kemarau; Terbatas; Dikecualikan < 10% jam) adalah ambang praktis proyek, bukan standar.
7. **Arah angin** dirata-rata secara melingkar; rata-rata harian arah angin juga melingkar.
8. Baris kesehatan 2023-12-31 (5 baris) dibuang karena tidak punya pasangan paparan.

## 7. Keterbatasan
- Hanya baris `VALID` yang dipakai; kebijakan ini memangkas puncak asap pada SM2-01 (dan mungkin sensor lain) sehingga estimasi dampak kabut asap bias ke bawah. Kolom `pm25_ug_m3_longgar` hanya untuk sensitivitas.
- Konversi PM "ppm" → µg/m³ (×1000) adalah hipotesis yang tervalidasi lewat orde besaran, bukan lewat pengukuran referensi.
- `pm_ekstrem` (PM > 500 µg/m³) hanya penanda untuk ditelaah; nilai ekstrem asli tidak dibuang, tetapi tidak dapat dibedakan secara pasti dari galat alat tanpa data pendukung (CO, hotspot).
- Stasiun BJB-01 dan SM2-01 memiliki PM2.5 tinggi namun kasus RS rendah; pembersihan tidak mengubah hal ini (lihat notebook 02), sehingga hasil hubungan PM2.5–kesehatan harus dilaporkan dengan sensitivitas tanpa stasiun tersebut.
- Tidak ada inferensi kausal pada tahap ini.

## 8. Cara menjalankan ulang
`python etl/run_preprocessing.py` membangun ulang seluruh keluaran (± 30 detik, deterministik). Skrip berhenti tanpa menulis apa pun bila satu validasi gagal.
