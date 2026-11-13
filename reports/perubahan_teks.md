# Perubahan teks dashboard (sebelum → sesudah)

> Hanya teks yang berubah. Angka, data, perhitungan, dan gaya visual tidak diubah. Sumber istilah: `app/glossary.py`; narasi: `app/teks.py`; nama daerah: `data/processed/nama_lokasi.csv`.


## Menu sidebar & judul halaman

| Elemen | Sebelum | Sesudah |
|---|---|---|
| Halaman 1 | Menu "Ringkasan"; judul tab/hero memakai istilah teknis | Menu "BERANDA"; judul halaman: "Bagaimana kualitas udara Indonesia saat ini?" |
| Halaman 2 | Menu "Kondisi"; judul tab/hero memakai istilah teknis | Menu "KONDISI UDARA"; judul halaman: "Seberapa tercemar udara di tiap daerah?" |
| Halaman 3 | Menu "Waktu kritis"; judul tab/hero memakai istilah teknis | Menu "WAKTU RAWAN"; judul halaman: "Kapan udara paling berbahaya?" |
| Halaman 4 | Menu "Faktor pemicu"; judul tab/hero memakai istilah teknis | Menu "PENYEBAB POLUSI"; judul halaman: "Apa yang membuat polusi naik?" |
| Halaman 5 | Menu "Kesehatan"; judul tab/hero memakai istilah teknis | Menu "DAMPAK KESEHATAN"; judul halaman: "Siapa yang paling terdampak?" |
| Halaman 6 | Menu "Jaringan"; judul tab/hero memakai istilah teknis | Menu "LOKASI PENGUKURAN"; judul halaman: "Daerah mana yang belum diukur kualitas udaranya?" |
| Halaman 7 | Menu "Peringatan"; judul tab/hero memakai istilah teknis | Menu "REKOMENDASI"; judul halaman: "Apa yang perlu dilakukan?" |
| Halaman 8 | Menu "Kualitas data"; judul tab/hero memakai istilah teknis | Menu "TENTANG DATA"; judul halaman: "Dari mana angka-angka ini berasal?" |
| Alamat halaman (URL) | /kondisi, /waktu-kritis, /faktor-pemicu, /kesehatan, /jaringan, /peringatan, /kualitas-data | /kondisi-udara, /waktu-rawan, /penyebab-polusi, /dampak-kesehatan, /lokasi-pengukuran, /rekomendasi, /tentang-data |

## Label tab

| Elemen | Sebelum | Sesudah |
|---|---|---|
| Beranda | Gambaran / Temuan kunci | Ringkasan / Temuan utama |
| Kondisi udara | Peringkat stasiun / Baku mutu & ISPU / Tren & perbandingan | Peringkat daerah / Batas aman & kategori udara / Perubahan dari waktu ke waktu |
| Waktu rawan | Pola jam / Musim & bulan / Episode kabut asap | Jam rawan / Bulan rawan / Kabut asap |
| Penyebab polusi | Cuaca / Lalu lintas & lokasi / Model (notebook 05) | Cuaca / Lalu lintas & jenis wilayah / Faktor paling berpengaruh |
| Dampak kesehatan | Kasus & PM2.5 / Risiko relatif / Kasus berlebih | Pasien dan polusi / Seberapa besar risikonya / Tambahan pasien saat kabut asap |
| Lokasi pengukuran | Peta jaringan / Kelengkapan & status / Prioritas | Sebaran lokasi / Kelengkapan catatan / Prioritas |
| Rekomendasi | Status terkini / Rekomendasi per tipe / Aturan peringatan | Kondisi terakhir / Langkah per jenis wilayah / Kapan perlu waspada |
| Tentang data | Ringkasan QC / Masalah data / Metodologi & keterbatasan | Sumber & pengolahan / Kamus istilah / Detail teknis |

## Filter & pemilih

| Elemen | Sebelum | Sesudah |
|---|---|---|
| Pilih periode | Rentang tanggal | Pilih periode |
| Pilih pulau | Pulau | Pilih pulau |
| Pilih provinsi | Provinsi | Pilih provinsi |
| Pilih jenis wilayah (setelah kota/kabupa | Tipe lokasi | Pilih jenis wilayah (setelah kota/kabupaten) |
| Pilih kota/kabupaten (nama daerah, urut  | Stasiun (kode: BGL-01, KTG-02, ...) | Pilih kota/kabupaten (nama daerah, urut abjad) |
| Pilih zat pencemar | Polutan: PM2.5, PM10, NO₂, SO₂, CO, O₃ | Pilih zat pencemar: Debu halus (PM2.5), Debu kasar (PM10), Gas NO₂, Gas SO₂, Gas CO, Gas O₃ |
| Pilih batas aman | Standar acuan: PP 22/2021 / WHO 2021 | Pilih batas aman: Batas aman nasional / Batas aman WHO |
| Buang catatan alat yang macet (disaranka | Data bertopeng (sensor macet dibuang) | Buang catatan alat yang macet (disarankan) |
| Pilih data yang ditampilkan | Filter global (judul bagian) | Pilih data yang ditampilkan |
| Lokasi terpilih (avatar dua huruf nama d | Stasiun aktif (avatar kode BGL, BGR, ...) | Lokasi terpilih (avatar dua huruf nama daerah) |
| 27 dari 27 lokasi pengukuran · 1 Jan 202 | 27 dari 27 stasiun · 01 Jan 2024 – 14 Oct 2026 | 27 dari 27 lokasi pengukuran · 1 Jan 2024 – 14 Okt 2026 |
| Semua pulau / provinsi / kota/kabupaten  | Placeholder: Semua pulau/provinsi/tipe/stasiun | Semua pulau / provinsi / kota/kabupaten / jenis wilayah |
| Rumah sakit di Jakarta Pusat (Gambir), u | RS-XXX-01 · JKT-01 (pemilih rumah sakit) | Rumah sakit di Jakarta Pusat (Gambir), urut abjad; bawaan tetap rumah sakit yang sama |
| Pilih rumah sakit | Pilih jenis penyakit | Rumah sakit / Jenis kasus | Pilih rumah sakit / Pilih jenis penyakit |

## Pita utama (gauge & KPI)

| Elemen | Sebelum | Sesudah |
|---|---|---|
| Beranda | Selamat datang, Kualitas Udara & Kesehatan / gauge "Sedang" / "16,7% hari > 55 µg/m³ (PP 22/2021)" / "Rata-rata PM2.5 39,4 µg/m³ · 27 stasiun · 23.931 hari sah" | Judul: pertanyaan halaman / gauge "Sedang" / "16,7% hari di atas batas aman nasional" / "Rata-rata debu halus (PM2.5) 39,4 µg/m³ · 27 lokasi · 23.931 catatan harian" (+ tooltip) |
| Beranda | Kartu teal: PLB 01, Kota Palembang, Gambut, Tertinggi: 71,1, Intermittent | Kartu teal: "Paling tercemar" Palembang, Sumatera Selatan, Lahan Gambut, Rata-rata: 71,1 µg/m³, Alat: bermasalah |
| Beranda | 20 episode kabut asap tercatat pada filter ini. LIHAT LINIMASA EPISODE → / tombol "Buka linimasa episode" | 20 kejadian kabut asap tercatat di lokasi terpilih. LIHAT KAPAN TERJADINYA → / tombol "Lihat kapan kabut asap terjadi" |
| Beranda | Ubin: Perkotaan, Jalan Raya, Industri, Gambut, Latar Bersih; "7 stasiun" | Pusat Kota, Pinggir Jalan Raya, Kawasan Industri, Lahan Gambut, Daerah Bersih; "7 lokasi" |
| Beranda | Kartu KPI "Hari > standar" 16,7%; "▼ 0,0 poin vs seluruh stasiun" | "Hari udara tidak aman" 16,7%; "Debu halus di atas batas aman nasional"; "3.997 dari 23.931 hari" |
| Beranda | "Peringkat risiko stasiun · notebook 05" (KTG-02 #1) | "Daerah paling berisiko" + penjelasan skor 0–100 (Sampit, peringkat 1) |
| Kondisi udara | "5/26 stasiun / rata-rata melebihi 55 µg/m³" ; "Median PM2.5" | "5 dari 26 lokasi / rata-rata di atas batas aman nasional" ; "Nilai tengah PM2.5" (+ tooltip) |
| Kondisi udara | "Uji tren / Mann-Kendall musiman + Sen / Stasiun Layak diuji 22 / 0 signifikan setelah BH (notebook 04)" | "Belum ada perubahan nyata dari tahun ke tahun / Lokasi yang diuji 22 / 0 lokasi dengan perubahan nyata" |
| Waktu rawan | "Puncak pukul 7 / median seluruh stasiun terpilih / Rentang jam PM2.5" | "Puncak 07:00 / nilai tengah semua lokasi terpilih / Kisaran sepanjang hari" |
| Waktu rawan | "Bulan puncak: Okt / kemarau = Mei–Oktober" | "Terburuk: Oktober / bulan dengan polusi tertinggi" |
| Waktu rawan | "20 episode / Hari episode 192 / puncak 1.128 µg/m³" | "20 kejadian / Total hari kabut asap 192 / tertinggi 1.128 µg/m³" |
| Penyebab polusi | "/ρ/ maks 0,16 / Pasangan /ρ/ ≥ 0,3: 0 dari 18" | "Hubungan lemah / Pasangan dengan hubungan sedang atau kuat: 0 dari 18" (angka ρ di tooltip) |
| Penyebab polusi | "ρ = 0,77 / Stasiun dianalisis 26" | "Hubungan kuat / Lokasi yang dibandingkan 26" (angka di tooltip) |
| Penyebab polusi | "R² log 0,86 / R² skala asli (uji 2026) 0,26 / gagal pada puncak asap di luar rentang latih" | "Skor ketepatan 0,86 / Ketepatan pada polusi ekstrem 0,26 / gagal menebak puncak asap yang belum pernah terjadi" |
| Dampak kesehatan | "ρ = 0,05 / RR kumulatif per +10 µg/m³: 1,086" | "Hubungan lemah/sedang / Kenaikan pasien ISPA balita +8,6% tiap debu halus naik 10 µg/m³" |
| Dampak kesehatan | "+8,6% / RR balita / lansia 1,000 · p = 1,00: tidak ada bukti beda kerentanan" | "+8,6% pasien ISPA balita tiap polusi naik 10 µg/m³ / Risiko balita dibanding lansia 1,000: sama besar" |
| Dampak kesehatan | "2.402–3.403 / Kasus teramati episode 4.957 · 148 RS-hari, tanpa BJB-01" | "2.402–3.403 tambahan pasien ISPA balita / Pasien tercatat saat kabut asap 4.957 · 148 hari-rumah sakit, tanpa Banjarbaru" |
| Lokasi pengukuran | "21/38 provinsi / Provinsi tanpa stasiun 17" | "21 dari 38 provinsi sudah punya lokasi pengukuran / Provinsi belum punya alat 17" |
| Lokasi pengukuran | "22/27 Layak / Cakupan median 99,3% / cakupan terendah (jam/hari/kemarau)" | "22 dari 27 lengkap / Kelengkapan catatan (nilai tengah) 99,3%" |
| Lokasi pengukuran | "Kepulauan Bangka Belitung / Prioritas perbaikan teratas MER-01 skor 53" | "prioritas pemasangan alat baru / Alat paling perlu diperbaiki: Merauke, skor 53 dari 100" |
| Rekomendasi | "14/26 stasiun / Tanggal data terakhir 14 Oct 2026 / bukan prakiraan" | "14 dari 26 lokasi / Data terakhir yang tercatat 14 Okt 2026 / ini kondisi terakhir, bukan prakiraan" |
| Tentang data | "2 flatline / Jam bertopeng 7.329 / 305 hari; run terpanjang stasiun lain 4 jam" | "2 kejadian alat macet / Catatan alat macet yang diabaikan 7.329 jam / 305 hari; alat lain paling lama 4 jam tanpa berubah" |

## Judul, subjudul, dan isi grafik/kartu

| Elemen | Sebelum | Sesudah |
|---|---|---|
| Beranda | Nilai PM2.5 bulanan · rata-rata stasiun terpilih | Debu halus paling tinggi pada Okt 2026: 145,9 µg/m³ (judul dihitung dari data) |
| Beranda | Profil polutan (Pinggir luar = rata-rata stasiun tertinggi) | "PM10 paling menonjol di lokasi terpilih" + penjelasan sumbu |
| Beranda | Episode terbaru · PM2.5 harian > 150 µg/m³, ≥ 3 hari | Kabut asap terbaru · Polusi di atas 150 µg/m³ selama minimal 3 hari berturut-turut (+ tooltip) |
| Kondisi udara | Rata-rata PM2.5 harian per stasiun (KTG-02, BJB-01, ...) | Udara Palembang paling tercemar (71,1 µg/m³), Indrapuri paling bersih (9,3 µg/m³) — nama daerah di sumbu |
| Kondisi udara | Detail stasiun (Median, P95, Maks, Hari sah, Kategori ISPU, Status analisis, Peringkat risiko (nb 05)) | Rincian lokasi (Nilai tengah, 95% hari di bawah, Hari terburuk, Catatan harian yang bisa dipakai, Kategori udara, Kelengkapan data, Skor risiko) |
| Kondisi udara | Statistik deskriptif (Stasiun, Tipe, Median, P95, Maks, Hari sah) | Angka ringkas per lokasi (Lokasi, Jenis wilayah, Rata-rata, Nilai tengah, 95% hari di bawah, Hari terburuk, Jumlah hari); angka berformat Indonesia |
| Kondisi udara | Komposisi kategori ISPU PM2.5 | Hanya 17,5% hari udara berkategori Baik (+ arti tiap kategori bagi warga) |
| Kondisi udara | Persentase hari melebihi standar · PP 22/2021 (batang vertikal, kode stasiun) | "21 dari 26 lokasi melewati batas aman WHO pada lebih dari separuh hari; batas aman nasional ..." (batang mendatar, nama daerah) |
| Kondisi udara | Kategori ISPU PM2.5 per stasiun | Jakarta Utara (Marunda) paling sering Tidak Sehat atau lebih buruk (100,0% hari) |
| Kondisi udara | Rata-rata PM2.5 bulanan menurut tipe lokasi | Pada Okt 2026, polusi tertinggi ada di Lahan Gambut |
| Kondisi udara | Sebaran harian PM2.5 per tipe lokasi · sumbu log | Rentang polusi harian sangat berbeda antar jenis wilayah · skala bertingkat, tiap garis ±3× lipat |
| Kondisi udara | Uji statistik (notebook 04, seluruh data): Kruskal-Wallis ε², Dunn–Holm, Mann-Kendall, Sen | Apakah polusi berubah dari tahun ke tahun? (perubahan nyata 0 dari 22; rata-rata kenaikan per tahun 0,010 µg/m³; perbedaan antar jenis wilayah: besar). Rumus statistik pindah ke Tentang data › Detail teknis |
| Waktu rawan | Profil PM2.5 menurut jam lokal · median per tipe lokasi | Polusi PM2.5 paling tinggi sekitar pukul 07:00 (pagi hari) |
| Waktu rawan | Puncak NO₂ Perkotaan: pukul 8, ... | Gas NO₂ memuncak di Pusat Kota pukul 8, ... (+ tooltip gas) |
| Waktu rawan | PM2.5: jam lokal × bulan · rata-rata | Polusi PM2.5 paling tinggi pada Agustus, September, dan Oktober |
| Waktu rawan | Rata-rata per bulan kalender | Musim kemarau (Mei–Oktober) lebih tercemar daripada musim hujan |
| Waktu rawan | Kemarau vs hujan, r — Perkotaan 0,62 | Hubungan musim kemarau dengan polusi — Pusat Kota: kuat (angka r di tooltip) |
| Waktu rawan | Linimasa episode · warna = kategori ISPU puncak (sumbu tanggal Oct 2024) | 20 dari 20 kejadian kabut asap berlangsung pada Agustus–Oktober (sumbu bulan Indonesia: Sep 2024, Des 2024, ...) |
| Waktu rawan | Tabel episode (episode, stasiun, tipe, mulai 2026-10-12, hari, puncak_harian) | Daftar kejadian kabut asap (Lokasi, Jenis wilayah, Mulai 12 Okt 2026, Selesai, Lama (hari), Polusi tertinggi (µg/m³)) |
| Penyebab polusi | Polutan vs cuaca · ρ Spearman (angka 0,15; Kec. angin) | Cuaca harian hampir tidak memengaruhi polusi di satu lokasi (sel berisi kata: Lemah; angka di tooltip; Kecepatan angin) |
| Penyebab polusi | PM2.5 vs Lalu lintas · ρ = 0,77 · p < 0,001 · n = 26 (titik berlabel kode) | Makin padat lalu lintas, polusi cenderung makin tinggi · hubungan kuat (26 lokasi) (nama daerah di tooltip) |
| Penyebab polusi | PM2.5 vs Jarak ke jalan · ρ = -0,67 | Makin jauh dari jalan, polusi cenderung makin rendah |
| Penyebab polusi | Kinerja model · R² skala log (Random Forest, Gradient Boosting, Regresi berganda; L1/L2 latih/uji) | Komputer dapat menebak tingkat polusi dengan cukup tepat (Metode komputer canggih 1 / 2, Metode sederhana; Menebak 2025 / 2026) |
| Penyebab polusi | Permutation importance · Random Forest | Lokasi dan musim paling berpengaruh; cuaca hampir tidak · seberapa turun skor ketepatan bila faktor diacak |
| Dampak kesehatan | ISPA balita (<5 th) dan PM2.5 · rata-rata bergerak 7 hari | Di Jakarta Pusat (Gambir), hubungan polusi dan pasien ISPA balita tergolong lemah (Pasien per hari / Debu halus PM2.5) |
| Dampak kesehatan | Kasus menurut kelas PM2.5 · rasio terhadap rata-rata RS | Pasien ISPA balita paling banyak saat polusi >250,4 µg/m³ (3,7× rata-rata) |
| Dampak kesehatan | RR kumulatif lag 0–7 · CI 95% (ISPA balita (<5 th), Kardiovaskular, ...) | Semua jenis penyakit bertambah saat polusi naik (ISPA balita (di bawah 5 tahun), Penyakit jantung & pembuluh darah, ...) |
| Dampak kesehatan | Respons per kelas PM2.5 · tanpa pemotongan eksposur; "ekstrapolasi linear" | Pasien makin banyak saat polusi makin pekat, lalu kenaikannya melandai; "perkiraan bila kenaikan lurus" |
| Dampak kesehatan | RR dipotong 250,4: 1,086 / RR tanpa pemotongan 1,021 / Spline waktu df 10 / df 30 | Hasil utama (polusi ekstrem dibatasi) 1,086 / Tanpa membatasi polusi ekstrem 1,021 / Dengan cara hitung tren waktu lain 1,088 dan 1,087 |
| Dampak kesehatan | Kasus berlebih per RS · batang = model, ◆ = selisih empiris (KTG-01, KTG-02, ...) | Kabut asap menambah pasien terutama di Palangka Raya dan Sampit (Rumah sakit di kota/kabupaten) |
| Lokasi pengukuran | Peta stasiun menurut status: Layak (22), Terbatas (4), Dikecualikan (1); ◇ = provinsi tanpa stasiun (sentroid kasar) | 17 provinsi belum punya alat pengukur udara: Data lengkap (22), Data terbatas (4), Tidak dipakai (1); ◇ = provinsi tanpa alat (titik tengah perkiraan) |
| Lokasi pengukuran | Donat status stasiun (Layak/Terbatas/Dikecualikan) | 22 dari 27 lokasi punya data lengkap (Data lengkap / Data terbatas / Tidak dipakai) |
| Lokasi pengukuran | Cakupan PM2.5 sah per stasiun (jam sah, hari sah, hari sah musim kemarau) | Catatan Merauke dan Muaro Jambi (Mestong) paling tidak lengkap (per jam, per hari, per hari di musim kemarau) |
| Lokasi pengukuran | Tabel: status_sensor Active/Intermittent/Defective; catatan teknis (VALID, WARMUP, MISSING, SUSPECT ...) | Alat: Berfungsi baik / Bermasalah; keterangan ditulis ulang tanpa istilah teknis |
| Lokasi pengukuran | A. Penambahan stasiun (provinsi tanpa stasiun) / B. Perbaikan stasiun (MER-01, JMB-02, ...) | Alat baru paling dibutuhkan di Kepulauan Bangka Belitung / Alat di Merauke dan Muaro Jambi (Mestong) paling perlu diperbaiki |
| Rekomendasi | Kategori ISPU PM2.5 pada hari sah terakhir (KTG-01 · Perkotaan · episode asap) | Pada hari data terakhir, udara di 14 dari 26 lokasi tidak sehat atau lebih buruk (Palangka Raya · Pusat Kota · kabut asap — Tetap di dalam ruangan.) |
| Rekomendasi | Rekomendasi per tipe: Bukti / Rekomendasi (BPBD/BNPB, DLH, Dinkes, Dishub, KLHK, BMKG; kode JKT-02, BTM-01, MER-01) | Yang terlihat di data / Yang perlu dilakukan (pemerintah, rumah sakit dan dinas kesehatan, warga); singkatan diuraikan; nama daerah |
| Rekomendasi | Aturan peringatan (episode asap, kategori ISPU, risiko RR, musim) | Kapan perlu waspada: kategori udara dan artinya bagi warga, risiko pasien, musim kabut asap |
| Tentang data | Flatline terdeteksi · ≥ 24 jam nilai identik; Ringkasan QC per stasiun; Log preprocessing; Masalah data (data_quality_issues) | Sumber & pengolahan (bahasa awam, 8 langkah) / Detail teknis (dilipat): tabel lengkap dengan nama daerah |
| Tentang data | Metodologi & keterbatasan (singkatan: RR, CI, df, DLM Almon, silhouette ...) | "Apa yang belum bisa dijawab data ini?" (7 poin, bahasa awam) + keterbatasan teknis lengkap di Detail teknis |
| Beranda › Temuan utama | Ringkasan 7 insight dari notebook 05 (Sensor partikulat BJB-01 macet ±10 bulan; R² log; RR; RS-hari; Spearman ...) | Tujuh temuan utama dalam kalimat biasa (alat macet; lokasi dan musim; ±8,6% pasien; ribuan pasien tambahan; daerah berisiko; 17 dari 38 provinsi; "polusi tinggi, pasien sedikit") |

## Istilah (kamus)

| Elemen | Sebelum | Sesudah |
|---|---|---|
| stasiun / stasiun AQMS / titik pantau / sensor | stasiun / stasiun AQMS / titik pantau / sensor | lokasi pengukuran / lokasi; alat (bukan sensor) |
| jaringan pemantauan | jaringan pemantauan | sebaran lokasi pengukuran |
| tipe lokasi (Perkotaan, Jalan Raya, Industri, Ga | tipe lokasi (Perkotaan, Jalan Raya, Industri, Gambut, Latar Bersih) | jenis wilayah (Pusat Kota, Pinggir Jalan Raya, Kawasan Industri, Lahan Gambut, Daerah Bersih) |
| RS-XXX-NN | RS-XXX-NN | rumah sakit di [nama kota] |
| PM2.5 / PM10 | PM2.5 / PM10 | Debu halus (PM2.5) / Debu kasar (PM10) |
| NO₂, SO₂, CO, O₃ | NO₂, SO₂, CO, O₃ | Gas NO₂, Gas SO₂, Gas CO, Gas O₃ (+ penjelasan di tooltip) |
| baku mutu PP 22/2021 / WHO 2021 | baku mutu PP 22/2021 / WHO 2021 | batas aman nasional / batas aman WHO |
| ISPU (Baik … Berbahaya) | ISPU (Baik … Berbahaya) | kategori udara dengan arti bagi warga |
| episode kabut asap | episode kabut asap | kejadian kabut asap (polusi > 150 µg/m³, minimal 3 hari berturut-turut) |
| lag | lag | jeda waktu |
| korelasi ρ / r / Spearman | korelasi ρ / r / Spearman | kekuatan hubungan (lemah / sedang / kuat); angka di tooltip |
| signifikan (setelah BH) | signifikan (setelah BH) | perubahan nyata (bukan kebetulan) |
| Sen's slope / median kemiringan | Sen's slope / median kemiringan | rata-rata kenaikan per tahun |
| RR (relative risk) | RR (relative risk) | kenaikan pasien; "setiap debu halus naik 10 µg/m³, pasien ISPA balita bertambah sekitar 8,6%" |
| median / P95 / Maks | median / P95 / Maks | nilai tengah / 95% hari di bawah / hari terburuk |
| kasus berlebih | kasus berlebih | tambahan pasien |
| data valid / cakupan | data valid / cakupan | catatan yang bisa dipakai / kelengkapan data |
| status Layak / Terbatas / Dikecualikan | status Layak / Terbatas / Dikecualikan | Data lengkap / Data terbatas / Tidak dipakai |
| status sensor Active / Intermittent / Defective | status sensor Active / Intermittent / Defective | Alat berfungsi baik / Alat bermasalah |
| data bertopeng / flatline | data bertopeng / flatline | buang catatan alat yang macet / angka tertahan |
| Random Forest, Gradient Boosting, regresi bergan | Random Forest, Gradient Boosting, regresi berganda, R², permutation importance | metode komputer canggih 1 / 2, metode sederhana, skor ketepatan, seberapa turun skor bila faktor diacak (nama metode hanya di Detail teknis) |
| ISPA / PPOK / Kardiovaskular | ISPA / PPOK / Kardiovaskular | infeksi saluran pernapasan (ISPA) / penyakit paru kronis / penyakit jantung & pembuluh darah |
| tanggal 14 Oct 2026; 2026-10-12; 01/01/2024 | tanggal 14 Oct 2026; 2026-10-12; 01/01/2024 | 14 Okt 2026; 12 Okt 2026; 1 Jan 2024 (bulan Bahasa Indonesia) |
| angka tabel 71.1 (titik desimal) | angka tabel 71.1 (titik desimal) | 71,1 (koma desimal; titik ribuan: 23.931) |
| kode di mana saja (KTG-02, JKT-01, SENS-001, RS- | kode di mana saja (KTG-02, JKT-01, SENS-001, RS-XXX-05) | nama daerah dari data/processed/nama_lokasi.csv; kode hanya di tabel referensi (Tentang data › Detail teknis) |

## Pesan, keterangan, dan fitur teks baru

| Elemen | Sebelum | Sesudah |
|---|---|---|
| Pesan data kosong | "Tidak ada data untuk filter ini." / "Tidak ada data PM2.5 sah untuk kombinasi filter ini. Ubah filter di sidebar." | "Belum ada data untuk pilihan ini. Coba pilih daerah atau periode lain." |
| Pesan kurang lokasi | "Minimal 5 stasiun diperlukan untuk analisis antar-stasiun; perluas filter." | "Perbandingan butuh minimal 5 lokasi. Coba pilih lebih banyak daerah." |
| Catatan versi data | "Versi 'apa adanya' memuat episode BJB-01 selama 204 hari yang merupakan artefak sensor macet (notebook 05). Aktifkan 'Data bertopeng' ..." | "Pilihan 'Buang catatan alat yang macet' sedang mati, sehingga ada satu kejadian palsu selama 204 hari di Banjarbaru ... Nyalakan pilihan itu di sebelah kiri ..." |
| Catatan tren | "Tidak ada bukti tren pada 2,8 tahun data (daya uji rendah) ... ε² = 0,44" | "Belum ada bukti polusi naik atau turun karena datanya baru 2,8 tahun. Yang jelas berbeda adalah polusi antar jenis wilayah." |
| Catatan cuaca | "Cuaca harian hampir tidak menjelaskan PM2.5 di dalam satu stasiun; ... (notebook 04–05)" | "Kotak hampir putih = hampir tidak ada hubungan. Yang jauh lebih menentukan polusi adalah lokasi dan musim, bukan cuaca harian." |
| Catatan lalu lintas | "Asosiasi antar-stasiun, bukan sebab-akibat: ... berfungsi sebagai pengenal stasiun" | "Ini hubungan, bukan sebab-akibat: lalu lintas dan jarak ke jalan bersifat tetap untuk tiap lokasi, sehingga juga mewakili ciri lokasi itu sendiri." |
| Catatan RR | "RR bergantung pada rentang eksposur: respons jenuh pada PM2.5 ekstrem ..." | "Besar kenaikan bergantung pada rentang polusi, jadi satu angka tidak boleh dipakai untuk memperkirakan polusi ekstrem. Ini hubungan, bukan bukti sebab-akibat." |
| Catatan jaringan | "Kandidat A memakai sentroid kasar provinsi dan proksi dari 3 stasiun Layak terdekat ... Peringkat perbaikan (6 kandidat) tidak stabil" | "Calon lokasi baru dinilai dari titik tengah kasar tiap provinsi ... Ini bukan hasil pengukuran." + keterangan di bawah grafik |
| Keterangan grafik (baru) | Tidak ada | Setiap grafik utama punya keterangan ≤ 2 kalimat: apa yang terlihat → artinya bagi warga |
| Expander baru | Tidak ada | "Cara membaca halaman ini" di setiap halaman: yang ditampilkan, cara membaca warna dan grafik, contoh pembacaan |
| Tooltip (ⓘ) | Tidak ada | Pada istilah yang perlu penjelasan (debu halus, gas, µg/m³, batas aman, kategori udara, kabut asap, jenis wilayah, nilai tengah, ISPA, kenaikan pasien, perubahan nyata, kekuatan hubungan, skor risiko, lokasi); isi dari app/glossary.py |

## Angka yang dipindahkan dari tampilan utama ke tooltip atau Detail teknis

Sesuai aturan "angka r hanya di tooltip" dan "metode statistik hanya di Tentang data", angka berikut tidak lagi tampil di teks utama (nilainya tidak berubah):

| Angka | Sebelumnya | Sekarang |
|---|---|---|
| ρ Spearman: 0,15 / 0,16 / 0,67 / 0,77 / 0,05 (+ nilai p) | Judul kartu & hero | Tooltip (ⓘ) dan sel peta panas; tampil sebagai kata lemah / sedang / kuat |
| r musim kemarau vs hujan: 0,17 / 0,51 / 0,57 / 0,62 | Label chip | Tooltip chip |
| ε² 0,436 / 0,078 / 0,44; kemiringan Sen; BH | Kartu "Uji statistik" | Tentang data › Detail teknis › metode statistik |
| Korelasi peringkat skor risiko 0,89 | Ringkasan insight 5 | Tentang data › Detail teknis › metode statistik |
| Hasil sebelumnya "z residual −2,8/−3,3" dan silhouette 0,53 | Ringkasan insight 7 / keterbatasan | Dihapus dari teks utama; tetap di laporan analisis (reports/findings/05_insights.md) |

## Hasil verifikasi

- `tools/audit_teks.py`: 0 temuan pola terlarang di luar Tentang data › Detail teknis (kode lokasi, SENS-, RS-XXX, LOC-, stasiun, AQMS, sensor, lag, korelasi, signifikan, QC, VALID, SUSPECT, parquet, nama metode statistik, istilah teknis, bulan berbahasa Inggris); semua angka statis di teks rekomendasi ada di `05_insights.md`.
- Perbandingan teks halaman sebelum vs sesudah: seluruh angka berdesimal/berribuan yang hilang adalah koefisien statistik di atas (dipindahkan, bukan diubah); angka baru hanya berupa angka turunan pada judul yang dihitung dari tabel yang sama (mis. 145,9 µg/m³; 17,5%; 100,0% hari), bukan perubahan angka lama.

## Revisi halaman Kondisi udara (elemen dihapus)

- Dihapus: tabel "Angka ringkas per lokasi"; grafik "batas aman WHO vs nasional" beserta caption dan tooltipnya; kartu "Apakah polusi berubah dari tahun ke tahun?" (chip dan kesimpulannya); expander "Cara membaca halaman ini" pada halaman ini.
- Tata letak: donut 1/3 lebar + batang bertumpuk 2/3 lebar dengan tinggi kartu sama; boxplot selebar penuh; kartu peringkat dan rincian lokasi sama tinggi.

## Revisi halaman Waktu rawan (elemen dihapus)

- Dihapus: chip "Gas NO₂ memuncak di [jenis wilayah] pukul …"; chip "Hubungan musim kemarau dengan polusi — [jenis wilayah]"; kartu tabel "Daftar kejadian kabut asap" beserta catatan kejadian yang masih berlangsung; expander "Cara membaca halaman ini" pada halaman ini.
- Kartu peta panas dan batang bulanan kini sama tinggi.

## Revisi menu dan halaman (elemen dihapus, dua halaman diarsipkan)

- Penyebab polusi: dihapus tab "Faktor paling berpengaruh" (dua grafik skor ketepatan, chip ketepatan, catatan kuning) dan expander "Cara membaca halaman ini".
- Dampak kesehatan: dihapus chip hasil perhitungan (1,086 / 1,021 / 1,088 dan 1,087), catatan kuning, dan expander.
- Lokasi pengukuran: dihapus tab "Kelengkapan catatan" (grafik dan tabel) dan tab "Prioritas" (dua grafik dan catatan), serta expander; halaman kini satu tampilan tanpa bar tab.
- Menu REKOMENDASI dan TENTANG DATA disembunyikan; kodenya dipindahkan ke app_archive/halaman_rekomendasi_tentang_data.py (teks dan glosarium tetap di app/teks.py dan app/glossary.py).


## Revisi peta: peta Indonesia 3D beranimasi (Beranda & Lokasi pengukuran)

**Yang berubah**
- **Lokasi pengukuran:** peta Plotly (titik + tanda ◇) diganti peta Indonesia 3D (deck.gl). Judul kartu: "17 provinsi belum punya alat pengukur udara" (angka tetap dari `key_numbers.json`); subjudul: "Titik = lokasi pengukuran (warna = kategori udara) · arsir salmon berdenyut = provinsi tanpa alat". Warna titik kini kategori udara (rata-rata debu halus), bukan lagi status kelengkapan; status kelengkapan tampil di pop-up dan irisan donat tetap menyorot titik terkait.
- **Beranda:** halaman ini sebelumnya tidak punya peta; kartu baru "Peta Indonesia: di mana udara paling kotor?" ditambahkan di bagian bawah halaman (lebar penuh).
- Teks baru di dalam peta: "Titik lokasi", "Peta panas polusi", "Lihat seluruh Indonesia", "Kategori udara (rata-rata debu halus)", "Belum ada alat pengukur", "Rata-rata debu halus (PM2.5)", "Hari di atas batas aman nasional (55 µg/m³)", "Kelengkapan data", "Klik titik untuk rincian", "Tahan Ctrl lalu gulir untuk memperbesar peta". Teks ini ada di `app/peta.py` dan ikut diperiksa `tools/audit_teks.py` (0 temuan).

**Sumber angka (tetap satu sumber):** rata-rata debu halus dan jumlah hari di atas batas aman dihitung dari tabel harian yang sama dengan hero Beranda (`C.dat.daily`, periode, filter, dan batas aman terpilih). Daftar provinsi tanpa alat dihitung dari `sites_clean.parquet` terhadap 38 provinsi pada peta (= 17, sama dengan `key_numbers.json`).

**Berkas baru:** `app/peta.py` (render_peta), `assets/peta3d/` (index.html, deck.min.js, provinsi.json, ATRIBUSI.md), `tools/bangun_peta.py` (pembuat provinsi.json; butuh shapely hanya saat membangun ulang).



## Revisi header: satu header kuning untuk semua halaman

**Yang berubah.** Header kuning enam halaman kini dibuat oleh satu komponen, `render_header(...)` di `app/header.py` (satu blok HTML/CSS, grid "1fr auto 1fr", tinggi 260 px, lengkungan di bawah). Header lama (ikon dompet, subjudul, gauge berwarna kategori di Beranda, header per tab) dihapus dari `app/ui.py`. Bar tab (pil putih) tetap ada, kini tepat di bawah header, karena tab adalah navigasi isi halaman, bukan bagian header.
Gauge kini busur putih dengan titik penanda putih bercincin mustard, ikon garis di atas jawaban, dan busur tumbuh dari 0 dalam 0,8 detik (mati bila perangkat memilih gerak dikurangi).

| Halaman | Judul | Nilai utama (gauge) | Rasio gauge | Keterangan | KPI |
|---|---|---|---|---|---|
| Beranda | Analisis Kualitas Udara & Kesehatan di Indonesia | kategori rata-rata PM2.5 | posisi rata-rata pada skala 5 kategori (Berbahaya sampai 500 µg/m³) | X% hari di atas batas aman [nasional/WHO] | Rata-rata debu halus (PM2.5) |
| Kondisi udara | Kondisi Udara Tiap Daerah | N dari M lokasi | lokasi di atas batas aman ÷ lokasi terpilih | rata-rata polusinya di atas batas aman [nasional/WHO] | Daerah paling tercemar + nilainya |
| Waktu rawan | Waktu Rawan Polusi | bulan · jam terburuk | rata-rata bulan terburuk ÷ batas aman (maks. 1); zat tanpa batas harian: 1 − bulan terbersih ÷ terburuk | rata-rata [zat] X µg/m³ di bulan terburuk | Kejadian kabut asap |
| Penyebab polusi | Penyebab Naiknya Polusi | faktor dengan hubungan terkuat (cuaca, lalu lintas, jarak ke jalan) | besar hubungan (|rho| Spearman) | hubungan [lemah/sedang/kuat] dengan [zat] · bukan sebab-akibat | Jenis wilayah paling tercemar |
| Dampak kesehatan | Dampak Polusi pada Kesehatan | N dari 7 penyakit | penyakit yang pasiennya naik nyata ÷ 7 | +X% pasien ISPA balita tiap debu halus naik 10 µg/m³ | Pasien ISPA balita + lansia (filter) |
| Lokasi pengukuran | Sebaran Lokasi Pengukuran | N dari 38 provinsi | provinsi dengan alat ÷ 38 | provinsi sudah memiliki alat pengukur | Lokasi dengan data lengkap |

**Penyimpangan dari usulan awal (disetujui pemilik):** (1) Dampak kesehatan: "kelompok paling rentan" tidak dipakai karena kenaikan pasien balita (+8,58%) dan lansia (+8,56%) sama besar; diganti "N dari 7 penyakit". (2) Waktu rawan: busur = bulan terburuk ÷ batas aman.
**Penyesuaian kecil:** jam ditulis "07:00" (sama dengan halaman lain); Lokasi pengukuran memakai "21 dari 38 provinsi sudah memiliki alat" (bukan 17 yang belum) agar angka dan gauge searah; singkatan WHO selalu kapital (`G.kecil()` di `app/glossary.py`).
**Dihapus dari tampilan (tidak ada lagi di halaman):** ringkasan per tab di header lama, mis. "Belum ada perubahan nyata" (tab tren), "Risiko balita dibanding lansia 1,000", kisaran tambahan pasien saat kabut asap, dan jumlah pasangan cuaca yang berhubungan sedang/kuat.


## Revisi animasi & performa: grafik baru ECharts/SVG
- Boxplot "Rentang polusi harian…" (Kondisi udara) → ECharts boxplot dengan 5 angka ringkas per jenis wilayah. Tooltip baru: "tertinggi · batas atas kotak · nilai tengah · batas bawah kotak · terendah" (µg/m³), menggantikan tooltip bawaan Plotly (max/q3/median/q1/min).
- Scatter lalu lintas & jarak ke jalan (Penyebab polusi) → ECharts scatter; tooltip sama: nama daerah, jenis wilayah, "Polusi PM2.5: … µg/m³", "Lalu lintas (kendaraan per jam): …" / "Jarak ke jalan (meter): …".
- Sparkline "Daerah paling berisiko" tetap SVG; hanya ditambah animasi garis tergambar.


## Revisi Waktu rawan: satu alur tanpa tab
- Tab "Jam rawan", "Bulan rawan", "Kabut asap" dihapus; isi tampil langsung: 3 kartu ringkas (Jam paling rawan · Bulan paling rawan · Kejadian kabut asap) → peta panas jam × bulan → pola per jam & per bulan → garis waktu kejadian kabut asap.
- Judul peta panas baru (dinamis): "Udara paling kotor pada {bagian hari} hari di bulan {bulan-bulan terburuk}". Tooltip: "Pukul 07.00 · Oktober · … µg/m³ · {kategori} · {n} kejadian kabut asap di bulan ini".
- Dihapus karena berulang: peta panas Plotly lama di tab "Bulan rawan" (digantikan peta panas utama ECharts).


## Revisi: Waktu rawan tanpa kartu ringkas; Penyebab polusi tanpa tab
- **Waktu rawan:** tiga kartu "Jam paling rawan", "Bulan paling rawan", "Kejadian kabut asap" (beserta teks "Klik untuk menyorot di peta panas") dan fungsi sorotan klik-kartu dihapus. Klik sel peta panas, tooltip, dan penanda 🔥 kabut asap tetap ada. Peta panas langsung di bawah header.
- **Penyebab polusi:** tab dihapus; satu alur dengan subjudul "Pengaruh cuaca" → "Pengaruh lalu lintas & jalan" → "Perbedaan antar jenis wilayah". Boxplot "Rentang polusi harian sangat berbeda antar jenis wilayah" ditambahkan di sini (kartu yang sama tetap ada di Kondisi udara › Perubahan dari waktu ke waktu). Matriks hubungan cuaca diganti dari Plotly ke ECharts (isi, kata "Lemah/Sedang/Kuat", dan warna sama).


## Revisi: warna boxplot & diagram sebar kabut asap
- **Boxplot "Rentang polusi harian sangat berbeda antar jenis wilayah"** (Kondisi udara & Penyebab polusi): warna tiap kotak dikembalikan sesuai jenis wilayah (isi 55%, tepi/kumis/median warna penuh). Legenda kini bisa diklik untuk menyembunyikan/menampilkan kotak. Tooltip baru: "{jenis wilayah} · Nilai terendah · Kuartil bawah · Nilai tengah · Kuartil atas · Nilai tertinggi" (µg/m³), menggantikan "tertinggi · batas atas kotak · nilai tengah · batas bawah kotak · terendah".
- **Waktu rawan › kabut asap:** garis waktu batang per lokasi diganti diagram sebar (satu titik = satu kejadian). Judul tetap dinamis ("{n} dari {N} kejadian kabut asap berlangsung pada Agustus–Oktober"). Subjudul baru: "Tiap titik = satu kejadian · makin tinggi makin parah · makin besar makin lama · klik titik untuk menyorot lokasi yang sama" (setelah klik: "Disorot: {lokasi} ({n} kejadian) · klik titik itu lagi untuk menampilkan semua"). Sumbu Y "Debu halus (PM2.5) tertinggi, µg/m³"; keterangan ukuran "Lama kejadian ○ 3 hari ◯ 20 hari ◯ 40 hari"; garis "150 Sangat Tidak Sehat" dan "250 Berbahaya"; pita latar "Puncak kemarau" (Agu–Okt; musim kemarau di dashboard tetap Mei–Oktober). Tooltip: "{lokasi} · {tanggal mulai – selesai} · {n} hari · puncak {x} µg/m³ · {kategori}".
- Keterangan lama "Kabut asap terbanyak terjadi pada {tahun} ({n} kejadian). Siapkan masker dan rencana kesehatan sebelum Agustus." → dua kalimat dinamis: "Kejadian kabut asap paling sering dimulai pada {bulan} ({n} dari {N} kejadian), dan yang terparah terjadi di {lokasi} pada {tanggal} dengan puncak {x} µg/m³ ({kategori}). Siapkan masker dan rencana kesehatan sebelum Agustus, terutama bagi warga di sekitar {jenis wilayah terbanyak}."
- Panduan membaca Waktu rawan: "Pada linimasa, satu batang = satu kejadian kabut asap." → "Pada diagram kabut asap, satu titik = satu kejadian; makin tinggi makin parah, makin besar makin lama."


## Revisi: header tanpa teks kecil, kabut asap jadi grafik batang, sakelar dihapus, font Inter
- **Header (semua halaman):** teks kecil di dalam lengkungan (mis. "16,7% hari di atas batas aman nasional") dan catatan di bawah angka KPI (mis. "27 lokasi · 23.931 catatan harian") tidak lagi tampil sebagai teks. Keterangan gauge menjadi tooltip saat gauge disorot; catatan KPI menjadi kalimat pertama tooltip ikon ⓘ (mis. "27 lokasi · 23.931 catatan harian. Partikel debu sangat kecil …").
- **Waktu rawan › kabut asap:** diagram sebar diganti grafik batang. Judul tetap ("{n} dari {N} kejadian kabut asap berlangsung pada Agustus–Oktober"). Subjudul baru: "Jumlah kejadian menurut bulan dimulainya, satu batang per tahun · makin gelap = makin baru · data {tahun} sampai {tanggal}". Sumbu Y "Jumlah kejadian". Tooltip: "{Bulan} {tahun} · {n} kejadian · {lokasi, …} · puncak tertinggi {x} µg/m³". Label "Puncak kemarau", garis 150/250, dan keterangan ukuran titik dihapus bersama diagram sebar.
- Keterangan kabut asap → "Kejadian kabut asap paling sering dimulai pada {bulan} ({n} dari {N} kejadian), dan jumlahnya bertambah setiap tahun: {n} pada {tahun}, … Siapkan masker dan rencana kesehatan sebelum Agustus, terutama bagi warga di sekitar {jenis wilayah}." (bila jumlah per tahun tidak selalu naik: "dengan jumlah per tahun …").
- Panduan membaca Waktu rawan: "Pada diagram kabut asap, satu titik = satu kejadian; …" → "Pada grafik kabut asap, tinggi batang = jumlah kejadian yang dimulai pada bulan itu; batang makin gelap = tahun makin baru."
- **Sidebar:** sakelar "Buang catatan alat yang macet (disarankan)" dan teks bantuannya dihapus; penyaringan selalu aktif. Catatan Waktu rawan "Pilihan 'Buang catatan alat yang macet' sedang mati …" dihapus (tidak mungkin muncul lagi). Keterbatasan: "… dibuang lewat pilihan di sebelah kiri, tetapi …" → "… selalu dibuang saat dashboard menghitung, tetapi …".
- **Panel daftar lokasi (Beranda):** tautan "Lihat di peta" dan "Bandingkan di Kondisi Udara →" kini hitam (#1F2933), satu baris (kiri & kanan); teks tidak berubah.
- **Font:** seluruh dashboard memakai Inter (judul header Inter 800); DM Serif Display dan Plus Jakarta Sans tidak dipakai lagi.


## Revisi: palet merah marun–pink (hanya warna; tata letak tidak berubah)
Hanya kata warna yang diganti agar keterangan tetap sesuai dengan warna baru; isi dan angka tidak berubah.
- Kondisi udara › kategori udara: "Hijau = Baik, biru = Sedang, kuning = Tidak Sehat, merah = Sangat Tidak Sehat, hitam = Berbahaya. Makin banyak warna kuning, merah, dan hitam, …" → "Hijau = Baik, biru kehijauan = Sedang, jingga = Tidak Sehat, merah muda = Sangat Tidak Sehat, merah tua = Berbahaya. Makin banyak warna jingga, merah muda, dan merah tua, …"
- Panduan membaca (Beranda): kalimat warna kategori udara diganti sama seperti di atas.
- Waktu rawan: "jam berlabel kuning = jam sibuk" → "jam berlabel merah muda = jam sibuk"; "Batang kuning = musim kemarau (Mei–Oktober) …" → "Batang merah muda = musim kemarau (Mei–Oktober) …" (juga di panduan membaca).
- Penyebab polusi (panduan membaca): "biru atau merah pekat = hubungan kuat" → "biru kehijauan atau merah pekat = hubungan kuat".
- Dampak kesehatan: "Garis merah = pasien, garis kuning = polusi." → "Garis biru kehijauan = pasien, garis merah = polusi."
- Beranda & Lokasi pengukuran (subjudul peta): "arsir salmon" → "arsir merah muda".
