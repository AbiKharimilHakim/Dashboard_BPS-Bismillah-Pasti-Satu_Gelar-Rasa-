# 01 — Business Understanding
**Kasus:** Dashboard Kualitas Udara & Dampak Kesehatan — DA Gelar Rasa 2026
**Sumber:** Booklet Case Study DA Gelar Rasa 2026 (`docs/`), inspeksi awal `data/raw/`
**Tahap:** CRISP-DM fase 1 (belum ada pemrosesan data; angka profil di bagian 6 berasal dari pengecekan cepat dan harus dikonfirmasi pada fase Data Understanding)

---

## 1. Latar Belakang Masalah

| Isu | Ringkasan | Relevansi dengan dataset |
|---|---|---|
| **Polusi udara perkotaan & industri** | Emisi kendaraan, industri (semen, batubara, pelabuhan), dan aglomerasi kota menaikkan PM2.5, NO₂, CO, dan SO₂. PM2.5 dapat masuk hingga alveoli dan aliran darah, sehingga memicu penyakit pernapasan dan kardiovaskular. WHO memperkirakan sekitar 7 juta kematian dini per tahun secara global terkait polusi udara. | Stasiun *Urban Background*, *Traffic/Roadside*, dan *Industrial Perimeter* (Jakarta, Bogor, Batam, Maros, Samarinda, Medan, dan lain-lain) beserta atribut `traffic_intensity_per_h` dan `distance_to_road_m`. |
| **Kebakaran hutan & lahan (karhutla) gambut** | Karhutla berulang pada musim kemarau, terutama Agustus–Oktober (episode besar 2015 dan 2019). Gambut terbakar secara membara (*smouldering*) dalam waktu lama dan menghasilkan kabut asap dengan PM2.5 dan CO sangat tinggi yang terbawa lintas kabupaten bahkan lintas negara. | 8 stasiun berkarakter gambut di Sumatra dan Kalimantan (Pekanbaru, Kota Jambi, Muaro Jambi, Palembang, Sampit, Pangkalan Bun, Sintang, Banjarbaru), ditambah Palangka Raya yang berada di koridor gambut. |
| **Kelompok rentan** | Balita (laju napas per berat badan tinggi, paru masih berkembang) dan lansia (komorbid PPOK/CVD, imunitas menurun) paling sensitif terhadap paparan. Dampaknya muncul dengan **jeda (lag)** beberapa hari setelah paparan. | `resp_admissions_under5`, `resp_admissions_over60`, `asthma_emergency_cases`, `copd_admissions`, `cvd`, `death` dari 27 RS rujukan. |
| **Kesenjangan informasi** | Data pemantauan tersebar, kualitasnya beragam, dan jarang dikaitkan langsung dengan data kesehatan. Akibatnya keputusan (peringatan dini, kesiapsiagaan RS, penegakan baku mutu) cenderung reaktif. | Dashboard terpadu yang menghubungkan **waktu rawan → wilayah tercemar → dampak kesehatan → tindakan**. |

**Rumusan masalah inti:** *Kapan, di mana, dan mengapa kualitas udara memburuk, seberapa besar dampaknya terhadap kesehatan kelompok rentan, dan apakah jaringan pemantauan saat ini memadai untuk mendukung keputusan yang tepat sasaran?*

---

## 2. Stakeholder & Keputusan yang Dibantu Dashboard

| Stakeholder | Peran | Keputusan yang dibantu | Pertanyaan kunci yang dijawab dashboard | Halaman utama | Frekuensi pakai |
|---|---|---|---|---|---|
| **KLHK¹ / DLH Provinsi & Kab/Kota** | Regulator mutu udara ambien, pengelola jaringan AQMS, penyusun IKU | Penegakan baku mutu (inspeksi industri/kendaraan), prioritas pengendalian emisi, penambahan atau perbaikan stasiun, pelaporan IKU | Stasiun mana yang paling sering melampaui BM? Apa sumber dominannya? Apakah tren membaik? Di mana stasiun baru dibutuhkan? | P1, P2, P3, P5 | Bulanan–tahunan |
| **Dinas Kesehatan** | Surveilans penyakit, promosi kesehatan, pengadaan logistik | Imbauan kesehatan (masker, kurangi aktivitas luar), distribusi masker/obat, penyiapan puskesmas, sasaran edukasi kelompok rentan | Berapa kenaikan kasus ISPA/asma per kenaikan PM2.5? Berapa hari jeda efeknya? Kelompok mana paling rentan? | P4, P6 | Harian (saat episode)–bulanan |
| **BNPB / BPBD** | Penanggulangan bencana, termasuk kabut asap karhutla | Penetapan status siaga/tanggap darurat asap, aktivasi posko & rumah singgah, evakuasi kelompok rentan, alokasi sumber daya pemadaman | Kapan musim/episode asap dimulai? Wilayah mana yang terdampak serentak? Berapa lama episode berlangsung? | P2, P6 | Harian (musim kemarau) |
| **Rumah Sakit rujukan** | Layanan kuratif | Penambahan kapasitas IGD/ruang rawat, penjadwalan tenaga kesehatan, stok oksigen, nebulizer, dan obat | Berapa lonjakan kasus yang diperkirakan dalam 1–7 hari setelah PM2.5 naik? Seberapa besar beban terhadap kapasitas tempat tidur? | P4, P6 | Harian–mingguan |
| *Pendukung: BMKG, Bappeda, masyarakat* | Data cuaca/hotspot, perencanaan, publik | Integrasi prakiraan cuaca, perencanaan tata ruang, perlindungan diri | Bagaimana kondisi udara hari ini dan apa yang harus dilakukan? | P0, P6 | Harian |

¹ Sejak Oktober 2024, KLHK dipecah menjadi Kementerian Lingkungan Hidup/BPLH dan Kementerian Kehutanan. Dokumen ini tetap memakai istilah "KLHK" sesuai booklet.

---

## 3. Turunan Tujuan Booklet menjadi Pertanyaan Analisis

**Konvensi umum (berlaku untuk semua pertanyaan):**
- Hanya data `qc_flag = VALID` yang dipakai untuk analisis konsentrasi. Label lain hanya dipakai untuk metrik kualitas data (lihat 6.3).
- Nilai rata-rata harian dianggap sah jika ada ≥ 18 jam valid (75%). Nilai rata-rata tahunan dianggap sah jika ada ≥ 75% hari valid.
- Satuan seluruh polutan diseragamkan ke µg/m³ (lihat 4.5).
- Kolom turunan: `pulau` (dari `provinsi`), `kelompok_lokasi` (Perkotaan, Jalan Raya, Industri, Gambut, Latar Bersih; dari `site_type`), `jam_lokal` (WIB → WITA/WIT), `musim` (kemarau Jun–Okt, hujan Nov–Mei), `is_weekend`.
- Kunci relasi: `sensors.sensor_id` ↔ AQMS `sensor_id`; `sensors.location_id` ↔ `sites.location_id`; stasiun nomor *n* ↔ `RS-XXX-n` (sesuai tabel E booklet).

### Tujuan 1 — Kondisi kualitas udara menurut dimensi waktu & ruang

| ID | Pertanyaan analisis | Metrik / KPI | Data & kolom | Metode | Visual direncanakan |
|---|---|---|---|---|---|
| Q1.1 | Bagaimana peringkat 27 stasiun dan 5 pulau berdasarkan rata-rata tahunan PM2.5 dan PM10 (2024, 2025, Jan–14 Okt 2026)? | Rata-rata tahunan, median, persentil 98 harian (µg/m³), peringkat | AQMS: `pm25_*`, `pm10_*`, `timestamp_start`, `qc_flag`; sites: `provinsi`→`pulau`, `site_type`, `latitude_dd`, `longitude_dd` | Agregasi jam → hari → tahun; peringkat; uji Kruskal–Wallis antar-pulau + post-hoc Dunn | Peta *bubble* (warna = kategori), *bar chart* horizontal berperingkat dengan garis BM & WHO, *boxplot* per pulau |
| Q1.2 | Berapa persen hari (atau jam) setiap stasiun melampaui baku mutu PP 22/2021 per parameter dan per periode rata-rata? | % hari > BM 24 jam (PM2.5 55, PM10 75, SO₂ 75, NO₂ 65); % jam > BM 1 jam (SO₂ 150, NO₂ 200, CO 10.000, O₃ 150); % 8 jam > BM (CO 4.000, O₃ 100); status rata-rata tahunan vs BM tahunan | AQMS: semua kolom polutan, `timestamp_start` | Rolling mean 1/8/24 jam & tahunan, dibandingkan dengan BM; hitung frekuensi pelampauan | *Heatmap* stasiun × parameter (% pelampauan), *scorecard* jumlah stasiun patuh |
| Q1.3 | Seberapa jauh kondisi tiap stasiun dari pedoman WHO AQG 2021, dan interim target (IT) mana yang sudah tercapai? | Rasio rata-rata tahunan / AQG (PM2.5 5, PM10 15, NO₂ 10); level IT tercapai (IT-1 s.d. IT-4); jumlah hari > AQG 24 jam | AQMS: `pm25_*`, `pm10_*`, `no2_*` | Perbandingan dengan nilai acuan; klasifikasi IT | *Dot/bullet chart* dengan pita IT, kartu "kali lipat dari pedoman WHO" |
| Q1.4 | Bagaimana distribusi kategori ISPU harian per stasiun, pulau, dan tahun, dan parameter apa yang paling sering dominan? | % hari Baik / Sedang / Tidak Sehat / Sangat Tidak Sehat / Berbahaya; jumlah hari ISPU > 100; parameter kritis (dominan) | AQMS: semua polutan; formula & *breakpoint* Permen LHK 14/2020 | Hitung sub-indeks ISPU per parameter → ambil nilai maksimum per hari | *Stacked bar* 100% dengan warna resmi ISPU, *calendar heatmap* per stasiun, *donut* parameter dominan |
| Q1.5 | Apakah kualitas udara membaik atau memburuk dari waktu ke waktu, dan bagaimana IKU tahunan per provinsi/pulau? | Sen's slope (µg/m³/tahun) + p-value Seasonal Mann–Kendall; % perubahan Jan–Okt 2026 vs Jan–Okt 2024 (periode setara); nilai & kategori IKU per tahun | AQMS: rata-rata bulanan PM2.5, PM10, NO₂, SO₂; sites: `provinsi` | Dekomposisi STL; Seasonal Mann–Kendall; perhitungan IKU (Permen LHK 27/2021) | *Line chart* tren + garis tren, *slope chart* 2024→2026, *small multiples* per stasiun, tabel IKU berwarna |

### Tujuan 2 — Waktu & wilayah dengan pencemaran paling kritis

| ID | Pertanyaan analisis | Metrik / KPI | Data & kolom | Metode | Visual direncanakan |
|---|---|---|---|---|---|
| Q2.1 | Pada jam berapa konsentrasi mencapai puncak di tiap kelompok lokasi, dan seberapa besar amplitudo hariannya? | Jam puncak (waktu lokal), amplitudo diurnal (median puncak − median minimum), rasio puncak/rata-rata | AQMS: `timestamp_start`→`jam_lokal`, `pm25_*`, `no2_*`, `co_*`, `o3_*`; sites: `site_type` | Profil diurnal median + IQR per kelompok lokasi dan per musim | *Line chart* diurnal *small multiples*, *heatmap* jam × bulan |
| Q2.2 | Apakah konsentrasi pada hari kerja berbeda signifikan dibanding akhir pekan, dan di kelompok lokasi mana efeknya terbesar? | *Weekend effect* % = (hari kerja − akhir pekan) / hari kerja; p-value | AQMS: `timestamp_start`→hari; polutan; sites: `site_type`, `traffic_intensity_per_h` | Uji Mann–Whitney per stasiun; profil jam × hari | *Heatmap* jam × hari, *dumbbell chart* hari kerja vs akhir pekan per stasiun |
| Q2.3 | Bulan dan musim apa yang paling kritis per pulau atau stasiun, dan kombinasi stasiun–bulan mana yang menjadi *hotspot*? | Rata-rata bulanan; rasio kemarau/hujan; % hari ISPU > 100 per stasiun–bulan; Top-10 stasiun–bulan terburuk | AQMS: polutan harian; turunan `musim`, `bulan` | Agregasi bulanan; peringkat; uji beda musim | *Heatmap* stasiun × bulan (urut menurut pulau), *polar/radial chart* bulanan |
| Q2.4 | Kapan dan di mana episode kabut asap karhutla terjadi (awal, puncak, durasi), dan stasiun mana yang terdampak serentak? | Jumlah episode, durasi (hari), PM2.5 puncak, total hari ISPU ≥ Tidak Sehat, rasio PM2.5/PM10, kenaikan CO; tingkat keserentakan antar-stasiun | AQMS: `pm25_*`, `pm10_*`, `co_*`, `wind_*`; sites: `baseline_pm25`, `site_type` (gambut) | Deteksi episode berbasis aturan: PM2.5 harian > 3× `baseline_pm25` **atau** ISPU > 100 selama ≥ 2 hari berturut-turut pada Jun–Nov, disertai tanda pembakaran biomassa (rasio PM2.5/PM10 tinggi dan CO naik); analisis ko-okurensi spasial | *Timeline*/Gantt episode per stasiun, multi-*line* stasiun gambut dengan pita episode, peta animasi harian |
| Q2.5 | Bagaimana "sidik jari" pencemaran berbeda antara kawasan perkotaan, tepi jalan, industri, gambut, dan latar bersih? | Rata-rata & P95 per polutan, koefisien variasi, rasio NO₂/PM2.5, tingkat SO₂, kontras terhadap latar bersih (× lipat) | AQMS: semua polutan; sites: `site_type`, `karakteristik_wilayah` | Perbandingan antarkelompok; *clustering* hierarkis atas profil diurnal + musiman yang dinormalisasi untuk memvalidasi `site_type` | *Radar/fingerprint chart*, *boxplot* per kelompok, dendrogram |

### Tujuan 3 — Faktor yang memengaruhi variasi konsentrasi polutan

| ID | Pertanyaan analisis | Metrik / KPI | Data & kolom | Metode | Visual direncanakan |
|---|---|---|---|---|---|
| Q3.1 | Seberapa kuat dan ke arah mana hubungan polutan dengan suhu dan kelembapan, dan apakah hubungan itu konsisten antar-stasiun? | Spearman ρ dan korelasi parsial (dikontrol jam & bulan) per stasiun | AQMS: polutan, `temperature_c`, `humidity_pct` | Korelasi per stasiun lalu dirangkum per kelompok lokasi | *Heatmap* korelasi stasiun × variabel, *hexbin scatter* |
| Q3.2 | Bagaimana kecepatan dan arah angin memengaruhi konsentrasi, dan dari arah mana sumber dominan berasal? | Rata-rata PM2.5 per kelas angin (calm < 1 m/s, 1–3, > 3 m/s); sektor arah dengan konsentrasi tertinggi; *Conditional Probability Function* (CPF) P90 | AQMS: `wind_speed_ms`, `wind_direction_deg`, polutan | *Binning* angin; *pollution rose*; *polar plot* bivariat (kecepatan × arah) | *Pollution rose*, *polar plot*, *bar* per kelas kecepatan |
| Q3.3 | Apakah stasiun dengan intensitas lalu lintas lebih tinggi atau jarak ke jalan lebih dekat memiliki NO₂, CO, dan PM2.5 lebih tinggi? | Koefisien regresi antar-stasiun & Spearman ρ; elastisitas (% perubahan konsentrasi per 1.000 kendaraan/jam) | sites: `traffic_intensity_per_h`, `distance_to_road_m`; rata-rata stasiun NO₂, CO, PM2.5 | Regresi robust antar-stasiun (n = 27, transformasi log), stasiun gambut dikecualikan pada analisis sensitivitas | *Scatter* berlabel stasiun + garis regresi, *bubble chart* |
| Q3.4 | Setelah cuaca dikendalikan, seberapa besar perbedaan konsentrasi menurut tipe lokasi? | *Estimated marginal means* per kelompok lokasi; *effect size* | AQMS harian + sites: `site_type`, `baseline_pm25` | *Linear mixed model* / GAM (efek tetap: cuaca, jam, bulan, tipe lokasi; efek acak: stasiun) | *Coefficient/forest plot*, *bar* dengan CI |
| Q3.5 | Faktor mana yang paling berpengaruh terhadap PM2.5 secara keseluruhan (meteorologi vs waktu vs karakteristik lokasi)? | *Permutation importance* & rata-rata \|SHAP\|; kinerja model R² dan RMSE di data uji (*time-based split*) | AQMS: meteorologi, fitur waktu; sites: `site_type`, `traffic_intensity_per_h`, `distance_to_road_m` | *Gradient boosting* dengan validasi silang berbasis waktu; SHAP; *partial dependence* | *Bar* *feature importance*, SHAP *beeswarm*, kurva *partial dependence* |

### Tujuan 4 — Dampak pencemaran terhadap kesehatan kelompok rentan

| ID | Pertanyaan analisis | Metrik / KPI | Data & kolom | Metode | Visual direncanakan |
|---|---|---|---|---|---|
| Q4.1 | Berapa persen kenaikan kasus ISPA, asma, PPOK, CVD, dan kematian untuk setiap kenaikan PM2.5 sebesar 10 µg/m³, dan apakah ada ambang? | *Relative Risk* (RR) per 10 µg/m³ + 95% CI; % perubahan; bentuk kurva *exposure–response* | Kesehatan: `resp_admissions_under5`, `resp_admissions_over60`, `asthma_emergency_cases`, `copd_admissions`, `resp`, `cvd`, `death`, `date`, `dow`, `temp_c`, `rhum_pct`; AQMS: PM2.5 harian stasiun pasangan | GLM quasi-Poisson deret waktu ala NMMAPS (spline waktu ±7 df/tahun, spline suhu, kelembapan, `dow`) per RS → meta-analisis *random effects* | *Forest plot* RR per outcome & per RS, kurva *exposure–response* |
| Q4.2 | Pada jeda berapa hari efek PM2.5 mencapai puncak, dan berapa lama efek itu bertahan? | RR per lag 0–7 (eksplorasi hingga 14); RR kumulatif lag 0–7; lag puncak | Sama dengan Q4.1 | *Distributed Lag Non-linear Model* (DLNM); *cross-correlation* sebagai eksplorasi awal | Kurva *lag–response*, *contour plot* paparan × lag |
| Q4.3 | Mana yang lebih rentan, balita atau lansia, dan apakah perbedaannya signifikan? | RR balita vs RR lansia; rasio RR + uji beda (z-test); % kenaikan kasus pada hari episode | `resp_admissions_under5`, `resp_admissions_over60`; PM2.5 harian | Model Q4.1/Q4.2 per kelompok umur; uji beda koefisien | *Dumbbell chart* balita vs lansia per RS, *forest plot* berpasangan |
| Q4.4 | Seberapa besar lonjakan kasus selama episode karhutla dibanding hari non-episode pada bulan yang sama? | Rata-rata kasus harian episode vs non-episode; % *excess*; *attributable number* (AN) dan *attributable fraction* (AF) | Output episode Q2.4; data kesehatan RS di stasiun gambut | Perbandingan hari ter-*match* (bulan sama, tahun berbeda); GLM dengan indikator episode | *Line chart* sebelum–selama–sesudah episode, *bar excess cases* |
| Q4.5 | RS/wilayah mana yang menanggung beban kasus terkait polusi terbesar relatif terhadap kapasitasnya? | AN per 100 tempat tidur; puncak rawat inap harian / kapasitas TT; kuadran paparan × beban | hospitals: `kapasitas_tempat_tidur`, `kelas_faskes`; output AN Q4.4/Q4.1 | Normalisasi beban terhadap kapasitas (nilai kosong ditangani, lihat 6.2); kuadran prioritas | Peta RS, *bar* berperingkat, *scatter* kuadran paparan vs beban |

### Tujuan 5 — Kecukupan jaringan pemantauan

| ID | Pertanyaan analisis | Metrik / KPI | Data & kolom | Metode | Visual direncanakan |
|---|---|---|---|---|---|
| Q5.1 | Bagaimana sebaran stasiun saat ini terhadap pulau dan provinsi, dan wilayah mana yang tidak terpantau? | Jumlah stasiun per pulau/provinsi; jumlah provinsi tanpa stasiun (dari 38); jarak ke stasiun terdekat (km); luas area per stasiun (Voronoi) | sites/sensors: koordinat, `provinsi`; batas provinsi (referensi eksternal) | Analisis spasial: poligon Voronoi, *buffer* radius representatif, *nearest neighbour* | Peta stasiun + Voronoi, peta koroplet provinsi (ada/tidak ada stasiun) |
| Q5.2 | Seberapa andal data tiap stasiun (kelengkapan, *uptime*, kesehatan alat)? | % kelengkapan jam VALID terhadap 24.432 jam yang diharapkan; % SUSPECT/CALIBRATING/error; *gap* terpanjang (jam); `status_operasional` | AQMS: `qc_flag`, `timestamp_start`; sensors: `status_operasional`, `tanggal_instalasi`, `model_sensor` | Profil QC per stasiun–bulan; skor keandalan | *Heatmap* ketersediaan data stasiun × bulan, *scorecard* status alat |
| Q5.3 | Apakah ada stasiun yang redundan (informasinya tumpang tindih) atau wilayah yang representasinya lemah? | Korelasi PM2.5 harian antar-pasangan stasiun vs jarak; redundan bila r > 0,9 dan jarak < 50 km | AQMS harian; sites: koordinat | Matriks korelasi; kurva *distance-decay*; *clustering* | Matriks korelasi berurut, *scatter* korelasi vs jarak |
| Q5.4 | Apakah setiap pulau/wilayah rawan memiliki kombinasi tipe lokasi yang memadai (perkotaan, industri, gambut, latar bersih)? | Matriks kelengkapan pulau × kelompok lokasi; jumlah sel kosong | sites: `site_type`, `pulau` | Tabulasi silang dan identifikasi celah | *Heatmap* matriks pulau × tipe |
| Q5.5 | Wilayah mana yang menjadi prioritas penambahan atau perbaikan titik pemantauan? | Skor prioritas komposit 0–100 per kandidat wilayah; peringkat; stabilitas peringkat pada uji sensitivitas | Output Q5.1–Q5.4, Q1.1 (tingkat polusi), Q2.4 (risiko asap), Q4.5 (beban kesehatan); opsional data eksternal (penduduk BPS, *hotspot* SiPongi) | *Multi-Criteria Decision Analysis* (bobot ala AHP/*weighted sum*); analisis sensitivitas bobot | Peta prioritas, tabel peringkat dengan rincian skor |

### Tujuan 6 — Dashboard interaktif, komunikatif, dan bernilai insight

| ID | Pertanyaan analisis | Metrik / KPI | Data & kolom | Metode | Visual direncanakan |
|---|---|---|---|---|---|
| Q6.1 | Apakah setiap stakeholder dapat menemukan jawaban atas keputusan utamanya dengan ≤ 3 klik? | Tingkat penyelesaian tugas ≥ 80%; jumlah klik; waktu penyelesaian | Skenario tugas per persona (bagian 2) | Uji kegunaan berbasis tugas dengan 3–5 penguji | Navigasi menu per persona, tombol "Lihat untuk: Dinkes / BPBD / DLH / RS" |
| Q6.2 | Bagaimana kondisi pada periode atau tanggal terpilih, dan apakah perlu tindakan? | ISPU terkini per stasiun; jumlah stasiun ISPU > 100; tren 7 hari; level peringatan (Normal/Waspada/Siaga/Awas) | Output Q1.4, Q2.4, Q4.2 | Aturan peringatan berbasis ISPU + lag efek kesehatan (misalnya "ISPU > 100 selama 2 hari → RS siaga H+1 s.d. H+3") | Kartu KPI, peta lampu lalu lintas, *banner* peringatan |
| Q6.3 | Apakah alur cerita mengalir dari *apa → kapan/di mana → mengapa → dampak → tindakan*? | Setiap halaman memiliki 1 judul berupa kalimat temuan + 1 rekomendasi; urutan halaman sesuai alur | Seluruh output analisis | Struktur naratif Situation–Complication–Resolution; judul berupa *insight* | Anotasi pada grafik, judul kalimat, panel "Apa artinya?" |
| Q6.4 | Apakah visualisasi akurat, konsisten, dan mudah dibaca? | Palet ISPU resmi dipakai konsisten; kontras warna memenuhi WCAG AA; filter global tersinkron; waktu muat < 3 detik | Data agregat siap saji | *Checklist* desain & performa; pra-agregasi | Panduan gaya (warna, ikon, satuan) |
| Q6.5 | Rekomendasi apa yang dapat ditindaklanjuti oleh tiap stakeholder? | Jumlah rekomendasi yang memiliki pemilik, pemicu, dan indikator keberhasilan | Ringkasan temuan Q1–Q5 | Matriks temuan → rekomendasi → pemilik → pemicu | Tabel aksi per stakeholder |

---

## 4. Acuan Standar & Cara Memakainya

### 4.1 Ringkasan acuan

| Acuan | Isi yang dipakai | Cara pemakaian di analisis/dashboard | Pertanyaan |
|---|---|---|---|
| **PP No. 22 Tahun 2021**, Lampiran VII (Baku Mutu Udara Ambien) | Batas konsentrasi per parameter & periode rata-rata | Status patuh/melampaui; % pelampauan; garis referensi di grafik | Q1.2, Q2.3, Q5.5 |
| **Permen LHK No. 14 Tahun 2020** (ISPU) | *Breakpoint*, rumus interpolasi linear, 5 kategori + warna | ISPU harian per stasiun, parameter kritis, kategori untuk peta & peringatan | Q1.4, Q2.3, Q2.4, Q6.2 |
| **Permen LHK No. 27 Tahun 2021** (IKLH, termasuk IKU) | Indeks Kualitas Udara tahunan (berbasis rata-rata tahunan NO₂ & SO₂) dan kategorinya | IKU per provinsi/pulau per tahun sebagai KPI kinerja daerah | Q1.5 |
| **WHO Global Air Quality Guidelines 2021** | AQG & interim target berbasis kesehatan | Pembanding "target kesehatan" yang lebih ketat dari BM nasional; rasio terhadap AQG | Q1.3, Q4.1 |

### 4.2 Baku mutu udara ambien (PP 22/2021) vs WHO AQG 2021 — µg/m³

| Parameter | PP 22/2021: 1 jam | PP 22/2021: 8 jam | PP 22/2021: 24 jam | PP 22/2021: tahunan | WHO AQG 2021: 24 jam | WHO AQG 2021: tahunan |
|---|---|---|---|---|---|---|
| PM2.5 | – | – | 55 | 15 | 15 | 5 |
| PM10 | – | – | 75 | 40 | 45 | 15 |
| SO₂ | 150 | – | 75 | 45 | 40 | – |
| NO₂ | 200 | – | 65 | 50 | 25 | 10 |
| CO | 10.000 | 4.000 | – | – | 4.000 | – |
| O₃ | 150 | 100 | – | 35 | 100 (8 jam) | 60 (*peak season*) |

**Interim target WHO untuk PM2.5:** tahunan IT-1 35 / IT-2 25 / IT-3 15 / IT-4 10; 24 jam IT-1 75 / IT-2 50 / IT-3 37,5 / IT-4 25.
**Interim target WHO untuk PM10:** tahunan 70 / 50 / 30 / 20; 24 jam 150 / 100 / 75 / 50.
Catatan: pedoman 24 jam WHO dinilai dengan persentil 99 (sekitar 3–4 hari pelampauan per tahun).

### 4.3 Breakpoint ISPU (Permen LHK 14/2020) — µg/m³

| ISPU | Kategori (warna) | PM10 | PM2.5 | SO₂ | CO | O₃ | NO₂ |
|---|---|---|---|---|---|---|---|
| 0–50 | Baik (hijau) | ≤ 50 | ≤ 15,5 | ≤ 52 | ≤ 4.000 | ≤ 120 | ≤ 80 |
| 51–100 | Sedang (biru) | 150 | 55,4 | 180 | 8.000 | 235 | 200 |
| 101–200 | Tidak Sehat (kuning) | 350 | 150,4 | 400 | 15.000 | 400 | 1.130 |
| 201–300 | Sangat Tidak Sehat (merah) | 420 | 250,4 | 800 | 30.000 | 800 | 2.260 |
| > 300 | Berbahaya (hitam) | 500 | 500 | 1.200 | 45.000 | 1.000 | 3.000 |

**Cara hitung:** sub-indeks dihitung dengan interpolasi linear antar-*breakpoint*:
I = (Iₐ − I_b) / (Xₐ − X_b) × (Xₓ − X_b) + I_b,
dengan Xₓ = konsentrasi terukur, X_b dan Xₐ = batas bawah dan atas, I_b dan Iₐ = ISPU batas bawah dan atas. **ISPU harian = sub-indeks maksimum**, dan parameter dengan sub-indeks tertinggi menjadi parameter kritis.
Periode rata-rata tiap parameter mengikuti Lampiran Permen (PM menggunakan rata-rata 24 jam). Parameter HC tidak tersedia di dataset sehingga tidak dihitung.

### 4.4 IKU (Permen LHK 27/2021)

| Aspek | Penggunaan |
|---|---|
| Input | Rata-rata tahunan NO₂ dan SO₂ per stasiun → dirata-ratakan per provinsi (dan per pulau untuk tampilan agregat). |
| Rumus | Mengikuti Lampiran Permen 27/2021: indeks pencemaran dibandingkan nilai acuan, lalu dikonversi ke skala 0–100. |
| Kategori | 5 kelas, dari Sangat Baik hingga Sangat Kurang. |
| Catatan | Tahun 2026 hanya berisi data Jan–14 Okt, sehingga IKU 2026 diberi label *parsial*. Provinsi yang hanya memiliki 1 stasiun latar bersih (misalnya Sulteng) cenderung berskor sangat baik dan belum tentu representatif. |

### 4.5 Konversi satuan & aturan agregasi

| Aturan | Rincian |
|---|---|
| Gas ppm → µg/m³ (25 °C, 1 atm) | µg/m³ = ppm × BM × 1.000 / 24,45; BM: SO₂ 64,07; NO₂ 46,01; CO 28,01; O₃ 48,00 |
| PM dalam "ppm" | Tidak memiliki padanan fisik. Hipotesis kerja: nilai sebenarnya mg/m³ yang salah label, sehingga dikali 1.000. Hipotesis ini divalidasi terhadap `baseline_pm25` dan stasiun tetangga (lihat 6.3). |
| Zona waktu | Booklet menyatakan timestamp dalam WIB. Untuk pola jam, waktu dikonversi ke waktu lokal: WITA (+1) untuk Kaltim, Kalsel, Sulsel, Sulteng; WIT (+2) untuk Papua Selatan & Papua Barat Daya. |
| Kelengkapan | Harian ≥ 18 jam valid; 8 jam ≥ 6 jam valid; tahunan ≥ 75% hari valid. |

> Nilai acuan pada bagian 4 harus dicocokkan ulang dengan naskah resmi regulasi sebelum dikunci di pipeline analisis.

---

## 5. Rancangan Menu Dashboard

**Filter global (tersinkron di semua halaman):** rentang tanggal · pulau · provinsi · stasiun · kelompok lokasi · polutan · standar acuan (PP 22/2021 / WHO).

| Halaman | Judul menu | Tujuan | Pertanyaan | Komponen utama | Pengguna utama | Pesan cerita |
|---|---|---|---|---|---|---|
| **P0** | Ringkasan Eksekutif | 6 | Q6.2, Q6.3 (rangkuman Q1.1, Q1.4, Q2.4, Q4.1) | Kartu KPI (rata-rata PM2.5 nasional, % hari Tidak Sehat+, jumlah episode asap, RR utama), peta ISPU, 3 temuan kunci | Semua / pimpinan | "Apa yang terjadi?" |
| **P1** | Kondisi Kualitas Udara | 1 | Q1.1–Q1.5 | Peta *bubble*, peringkat stasiun vs BM & WHO, *stacked bar* ISPU, *heatmap* pelampauan, tren & IKU | KLHK/DLH | "Seberapa buruk, dan apakah membaik?" |
| **P2** | Waktu & Wilayah Kritis | 2 | Q2.1–Q2.5 | Profil diurnal, *heatmap* jam × hari, *heatmap* stasiun × bulan, *timeline* episode asap, *fingerprint* tipe lokasi | BNPB/BPBD, DLH | "Kapan dan di mana paling berbahaya?" |
| **P3** | Faktor Pemicu | 3 | Q3.1–Q3.5 | *Heatmap* korelasi, *pollution rose*, *scatter* lalu lintas–NO₂, *feature importance* / SHAP | KLHK/DLH | "Mengapa terjadi?" |
| **P4** | Dampak Kesehatan | 4 | Q4.1–Q4.5 | *Forest plot* RR, kurva lag, balita vs lansia, *excess cases* saat episode, beban RS per kapasitas | Dinkes, RS | "Siapa yang terdampak dan seberapa besar?" |
| **P5** | Jaringan Pemantauan | 5 | Q5.1–Q5.5 | Peta Voronoi, *heatmap* ketersediaan data, matriks redundansi, peta & tabel prioritas stasiun baru | KLHK/DLH, Bappeda | "Apakah kita melihat semuanya?" |
| **P6** | Peringatan Dini & Rekomendasi | 6 | Q6.2, Q6.5 | Level siaga per wilayah, aturan pemicu, tabel aksi per stakeholder | BNPB/BPBD, Dinkes, RS | "Apa yang harus dilakukan?" |
| **P7** | Kualitas Data & Metodologi | Pendukung (1–5) | Q5.2 (+ transparansi semua Q) | Ringkasan QC, aturan pembersihan, acuan standar, glosarium, asumsi | Analis / juri | "Seberapa bisa dipercaya?" |

**Pemetaan tujuan → halaman:** T1→P1 · T2→P2 · T3→P3 · T4→P4 · T5→P5 (+P7) · T6→P0, P6, serta prinsip desain di semua halaman.

---

## 6. Asumsi & Batasan Awal

### 6.1 Asumsi

| No | Asumsi | Dasar | Dampak bila salah |
|---|---|---|---|
| A1 | Stasiun nomor *n* (SENS-0*n*) berpasangan dengan RS-XXX-*n*, dan paparan RS diwakili oleh stasiun pasangannya | Tabel E booklet; kecamatan RS sama dengan lokasi stasiun | Salah klasifikasi paparan, sehingga RR bias menuju nol |
| A2 | Timestamp AQMS dalam WIB untuk semua stasiun | Booklet bagian F | Pola diurnal di WITA/WIT bergeser 1–2 jam bila tidak dikonversi |
| A3 | Hanya `qc_flag = VALID` yang dipakai untuk konsentrasi; SUSPECT dikecualikan dari analisis utama dan diuji pada analisis sensitivitas | Praktik QA/QC umum | Bila SUSPECT sebenarnya episode nyata, puncak asap akan *underestimated* |
| A4 | Kolom `*_ppm` pada 3 file perlu dikonversi ke µg/m³ (lihat 4.5) | `metadata_sensors.csv` menyatakan satuan standar µg/m³ dan ppm sebagai *logger export* | Konversi PM yang keliru akan merusak peringkat dan status BM stasiun MDN-01, BJB-01, PSW-01 |
| A5 | Musim kemarau Jun–Okt dan musim hujan Nov–Mei (generalisasi nasional) | Pola iklim monsunal Indonesia | Kurang tepat untuk wilayah dengan pola ekuatorial/lokal (Sumbar, Sulteng, Papua) |
| A6 | Pengelompokan `site_type` menjadi 5 kelompok: Perkotaan (7), Jalan Raya (2), Industri (4), Gambut (8), Latar Bersih (6); tipe campuran (misalnya "Peatland Buffer / Urban") dimasukkan ke kelompok gambut | `sites.csv` | Kontras antarkelompok bergeser; akan divalidasi dengan *clustering* (Q2.5) |
| A7 | Pulau diturunkan dari `provinsi` (Sumatra 10 stasiun termasuk Batam, Jawa 7, Kalimantan 6, Sulawesi 2, Papua 2), bukan dari `region_group` yang tidak konsisten | Booklet: "lima pulau besar" | – |
| A8 | Jumlah kasus RS mencerminkan dinamika harian populasi sekitar; populasi dianggap stabil dalam jangka pendek | Desain deret waktu ala NMMAPS | Perubahan kapasitas atau rujukan RS dapat membiaskan tren |

### 6.2 Batasan

| No | Batasan | Implikasi & mitigasi |
|---|---|---|
| B1 | **Data sintetis** | Temuan bersifat ilustratif dan tidak boleh diklaim sebagai kondisi riil daerah. Hal ini dinyatakan di dashboard (P7). |
| B2 | Analisis observasional/ekologis | Hasilnya berupa asosiasi, bukan kausalitas. Mitigasi: kontrol *confounder* (cuaca, hari, musim, tren) dan bahasa interpretasi yang hati-hati. |
| B3 | Tidak ada denominator populasi atau data umur penduduk | Tidak dapat menghitung *incidence rate* per penduduk. Sebagai gantinya dipakai RR dalam-RS, % perubahan, dan normalisasi per tempat tidur. |
| B4 | Hanya 1 stasiun per RS dan 27 titik untuk 5 pulau | Analisis faktor antar-stasiun (Q3.3) hanya memiliki n = 27, sehingga daya uji rendah. Paparan wilayah luas diwakili satu titik. |
| B5 | Tidak ada data *hotspot*, curah hujan, atau emisi | Episode karhutla diinferensikan dari sinyal polutan (Q2.4). Data eksternal (SiPongi, BMKG, BPS) bersifat opsional dan harus diberi label sebagai tambahan. |
| B6 | Periode Jan 2024 – 14 Okt 2026 (±2,8 tahun) | Tren jangka panjang terbatas. Tahun 2026 parsial, sehingga perbandingan antar-tahun memakai periode setara (Jan–Okt). |
| B7 | `kapasitas_tempat_tidur` dapat kosong (booklet) dan banyak RS bernilai seragam 180 | Normalisasi beban per kapasitas bersifat indikatif. RS tanpa data kapasitas ditandai, bukan diimputasi diam-diam. |
| B8 | Parameter HC tidak tersedia | ISPU dihitung dari 6 parameter saja. |

### 6.3 Temuan awal kualitas data (dari pengecekan cepat, perlu dikonfirmasi)

| Temuan | Stasiun/file | Implikasi |
|---|---|---|
| 3 file memakai header `*_ppm` (`pm25_ppm`, dan seterusnya); `sites.pm25_unit = ppm` | MDN-01, BJB-01, PSW-01 | Konversi satuan wajib dilakukan (A4). Contoh MDN-01: rata-rata `pm25_ppm` sekitar 0,051, atau sekitar 51 µg/m³ bila ×1.000, yang konsisten dengan `baseline_pm25` 42,8 dan mendukung hipotesis. |
| Sensor `Defective`: hanya sekitar 122 dari 24.432 baris yang VALID; terdapat label `COMM_LOST`, `SENSOR_DEAD`, `CORRUPT`, `FATAL_ERR`, `GARBAGE`, `PARSER_FAIL`; nilai *sentinel* (`-9999`, `0xDEADBEEF`, `ERR_COMM_TIMEOUT`); timestamp 1970 dan timestamp tidak tepat di awal jam | JMB-02 | Kemungkinan besar dikeluarkan dari analisis konsentrasi dan kesehatan. Stasiun ini menjadi bukti kebutuhan perbaikan jaringan (Q5.2, Q5.5). |
| Jumlah baris 36.381, sementara yang diharapkan 24.432 jam; sekitar 5.136 baris MISSING; sensor `Intermittent` | PLB-01 | Kemungkinan duplikasi atau sub-jam, sehingga perlu deduplikasi atau resampling per jam. |
| Timestamp tidak tepat di awal jam (misalnya 00:04:18.250); 20.800 baris; label `WARMUP`, `MAINTENANCE` | MDN-01 | Timestamp perlu dibulatkan ke jam dan *gap* perlu ditandai. |
| Label `qc_flag` di luar spesifikasi metadata (VALID/SUSPECT/CALIBRATING/MISSING) | Beberapa file | Perlu kamus pemetaan label → {VALID, TIDAK VALID}. |
| Status `Intermittent` | PLB-01, MER-01, MDN-01 | Bobot keandalan lebih rendah di Q5.2. |
| Nilai PM2.5 ekstrem (maks sekitar 1.620 µg/m³) | KTG-01 | Kemungkinan episode karhutla nyata, bukan *outlier*. Perlu dicek terhadap musim, CO, dan stasiun tetangga sebelum diputuskan, bukan langsung dibuang. |
| Data kesehatan mulai 2023-12-31 (1 hari sebelum AQMS); 27.491 baris, sementara yang diharapkan sekitar 27.513 | HLT-01 | Ada sekitar 22 hari-RS hilang. Data dibatasi ke periode irisan. |
| `region_group` tidak konsisten (JMB-02 = "Sumatera", JMB-01 = "Jambi") | sites, sensors | Dasar asumsi A7. |
| Format `measurement_id` berbeda dari contoh booklet (`MEAS-0000001` vs `MEAS-YKY-01-000001`) | AQMS | Tidak dipakai sebagai kunci analisis. |

---

**Langkah berikutnya:** `02_data_understanding.md`, berisi profil lengkap per file, validasi hipotesis konversi ppm, kamus `qc_flag`, dan keputusan akhir untuk JMB-02 dan PLB-01.
