"""Teks naratif dashboard dalam bahasa awam: judul halaman, temuan utama, langkah per jenis wilayah, keterbatasan, dan
"Cara membaca halaman ini". Angka temuan dibaca dari reports/key_numbers.json dan tabel data/processed/ (format Indonesia);
angka pada tabel langkah per jenis wilayah disalin dari reports/findings/05_insights.md (diperiksa otomatis oleh
tools/cek_teks.py).
"""
from __future__ import annotations

import pandas as pd

from . import glossary as G
from .glossary import fl, rp

# judul halaman (pertanyaan) + subjudul, sesuai urutan menu
HALAMAN = [
    ("Beranda", "Bagaimana kualitas udara Indonesia saat ini?", "Ringkasan kondisi udara dan dampaknya"),
    ("Kondisi udara", "Seberapa tercemar udara di tiap daerah?", "Perbandingan antar daerah dan perubahannya tiap tahun"),
    ("Waktu rawan", "Kapan udara paling berbahaya?", "Jam, hari, dan bulan dengan polusi tertinggi"),
    ("Penyebab polusi", "Apa yang membuat polusi naik?", "Peran cuaca, angin, lalu lintas, dan jenis wilayah"),
    ("Dampak kesehatan", "Siapa yang paling terdampak?", "Hubungan polusi dengan pasien rumah sakit"),
    ("Lokasi pengukuran", "Daerah mana yang belum diukur kualitas udaranya?", "Sebaran dan kondisi alat pengukur udara"),
    ("Rekomendasi", "Apa yang perlu dilakukan?", "Langkah untuk pemerintah, rumah sakit, dan warga"),
    ("Tentang data", "Dari mana angka-angka ini berasal?", "Sumber data, cara pengolahan, dan keterbatasan"),
]

_CARA_BACA_SEMUA = [
    ("Ringkasan udara di lokasi yang Anda pilih di sebelah kiri: rata-rata debu halus, berapa hari melewati batas aman, kejadian kabut asap, dan daerah paling berisiko.",
     "Warna kategori udara: hijau = Baik, biru kehijauan = Sedang, jingga = Tidak Sehat, merah muda = Sangat Tidak Sehat, merah tua = Berbahaya. Garis putus-putus pada grafik = batas aman.",
     "Bila 'Hari udara tidak aman' menunjukkan 16,7%, artinya sekitar 1 dari 6 hari udara melewati batas aman nasional."),
    ("Daerah mana yang udaranya paling tercemar, berapa hari melewati batas aman, dan apakah polusi berubah dari waktu ke waktu.",
     "Batang yang lebih panjang = polusi lebih tinggi. Warna batang = jenis wilayah. Garis putus-putus = batas aman. Klik sebuah batang untuk melihat rincian daerahnya.",
     "Bila batang Palembang melewati garis putus-putus, rata-rata polusi harian di sana lebih tinggi daripada batas aman."),
    ("Jam, bulan, dan kejadian kabut asap dengan polusi tertinggi.",
     "Pada grafik jam dan bulan, makin tinggi garis atau makin pekat warna, makin tinggi polusi. Batang merah muda = musim kemarau (Mei–Oktober). Pada grafik kabut asap, tinggi batang = jumlah kejadian yang dimulai pada bulan itu; batang makin gelap = tahun makin baru.",
     "Bila garis memuncak pukul 07:00, udara paling kotor saat jam berangkat kerja dan sekolah."),
    ("Faktor yang diduga memengaruhi polusi: cuaca, lalu lintas, jarak ke jalan, dan jenis wilayah.",
     "Pada tabel cuaca, kotak hampir putih = hampir tidak ada hubungan; biru kehijauan atau merah pekat = hubungan kuat. Pada diagram titik, tiap titik = satu lokasi. Hubungan bukan berarti sebab-akibat.",
     "Bila titik-titik naik ke kanan, lokasi yang lalu lintasnya lebih padat cenderung lebih tercemar."),
    ("Hubungan antara polusi dan jumlah pasien di rumah sakit.",
     "'Kali lipat' membandingkan jumlah pasien dengan saat udara Baik: 2,0 berarti dua kali lebih banyak. Garis pendek di kiri-kanan titik = rentang kepastian; makin pendek, makin pasti.",
     "Bila pasien ISPA balita naik 8,6% setiap polusi naik 10 µg/m³, maka kenaikan 30 µg/m³ menambah pasien sekitar seperempatnya."),
    ("Di provinsi mana ada alat pengukur udara, seberapa lengkap catatannya, dan daerah mana yang perlu alat baru atau perbaikan.",
     "Titik berwarna di peta = lokasi pengukuran (warna = kelengkapan data). Tanda belah ketupat (◇) = provinsi yang belum punya alat. Batang lebih panjang = prioritas lebih tinggi.",
     "Bila sebuah lokasi hanya punya 20% catatan yang bisa dipakai, angka dari lokasi itu sebaiknya tidak dijadikan dasar keputusan."),
    ("Kondisi udara terakhir yang tercatat, langkah menurut jenis wilayah, dan kapan warga perlu waspada.",
     "Setiap kartu menampilkan kategori udara beserta artinya bagi warga. Kartu langkah dibagi menurut pihak yang bertindak: pemerintah, rumah sakit, dan warga.",
     "Bila kategori Tidak Sehat, warga disarankan mengurangi aktivitas di luar; bila Berbahaya, tetap di dalam ruangan."),
    ("Asal data, cara data dibersihkan, keterbatasan, dan arti istilah.",
     "Tabel 'Kamus istilah' menjelaskan setiap istilah. Bagian teknis dilipat; buka bila ingin melihat detail pemeriksaan data.",
     "Bila ingin tahu mengapa sebuah angka berubah setelah catatan alat macet dibuang, lihat 'Sumber & pengolahan'."),
]

# Hanya halaman yang diarsipkan (app_archive/) yang memakai panel "Cara membaca halaman ini": Rekomendasi (6) dan Tentang data (7)
CARA_BACA = {i: t for i, t in enumerate(_CARA_BACA_SEMUA) if i in (6, 7)}


def _kn(D):
    return D.kn["insight"]


def temuan_utama(D) -> list[tuple[str, str, str]]:
    """Tujuh temuan utama: (judul, isi, terutama untuk). Semua angka dari key_numbers.json dan tabel pendukung."""
    K = _kn(D)
    fn = K["0_flatline"]; r1, r2 = fn["runs"][0], fn["runs"][1]
    dam = fn["dampak_pada_04"]
    ml = K["1_ml"]; kin = pd.DataFrame(ml["kinerja"]); rf = kin[kin.model == "Random Forest"].set_index("lipatan")
    l1, l2 = list(rf.index)[:2]
    dl = pd.DataFrame(ml["permutation_dalam_vs_seluruh"]); cu = dl[dl.kelompok.str.startswith("Cuaca")].acak_dalam_stasiun.max()
    K2 = K["2_kesehatan"]; ub = K2["rr_kumulatif"]["ISPA balita (<5 th)"]
    er = pd.DataFrame(K2["respons_eksposur_kelas"]); er = er[er.kasus == "ISPA balita (<5 th)"]
    rr_55 = er[er.kelas.astype(str).str.startswith("55")].rr.iloc[0]
    kb = K2["kasus_berlebih"]; tot = kb["total"]["ISPA balita (<5 th)"]
    rk = pd.DataFrame(K["5_risiko"]["peringkat"]).head(5)
    K6 = K["6_jaringan"]
    qc = D.qc; n_blm = int((qc.status_analisis != "Layak").sum())
    A = pd.DataFrame(K6["prioritas_penambahan"]).head(3); B = pd.DataFrame(K6["prioritas_perbaikan"]).head(3)
    nm = G.pendek
    top5 = ", ".join(f"{nm(r.kode_stasiun)} (skor {fl(r.skor, 0)})" for r in rk.itertuples())
    return [
        (f"Satu alat pengukur macet berbulan-bulan, sehingga sebagian angka perlu dikoreksi",
         f"Alat di {nm('BJB-01')} menampilkan angka yang persis sama selama {rp(r1['n_jam'])} jam (±{rp(r1['n_hari'])} hari): {fl(r1['nilai'])} µg/m³, lalu {rp(r2['n_jam'])} jam: {fl(r2['nilai'])} µg/m³. "
         f"Di lokasi lain angka tidak pernah tertahan lebih dari {fn['run_terpanjang_stasiun_lain_jam']} jam. Dashboard ini membuang catatan macet itu; hasilnya rata-rata {nm('BJB-01')} turun dari "
         f"{fl(dam['rata2_bjb01']['apa_adanya'])} menjadi {fl(dam['rata2_bjb01']['bertopeng'])} µg/m³ dan kejadian kabut asap dari {rp(dam['n_episode']['apa_adanya'])} menjadi {rp(dam['n_episode']['bertopeng'])}.",
         "Dinas lingkungan hidup dan tim data"),
        ("Polusi ditentukan oleh lokasi dan musim, bukan oleh cuaca harian",
         f"Komputer dapat menebak tingkat debu halus dengan cukup tepat hanya dari lokasi dan bulan (skor ketepatan {fl(rf.loc[l1, 'r2_log'], 2)} untuk 2025 dan {fl(rf.loc[l2, 'r2_log'], 2)} untuk 2026; skor tertinggi 1). "
         f"Cuaca harian hampir tidak menambah ketepatan ({fl(cu, 2)}). Namun tebakan gagal pada puncak asap yang belum pernah terjadi sebelumnya.",
         "Dinas lingkungan hidup"),
        (f"Tiap debu halus naik 10 µg/m³, pasien ISPA balita bertambah sekitar {fl(100 * (ub['rr'] - 1), 1)}%",
         f"Pasien infeksi saluran pernapasan (ISPA) balita naik sekitar {fl(100 * (ub['rr'] - 1), 1)}% ({fl(ub['rr'], 3)} kali; rentang kepastian {fl(ub['bawah'], 2)}–{fl(ub['atas'], 2)} kali); balita dan lansia sama besar. "
         f"Dampaknya sudah terasa sejak polusi menengah: pada 55–150 µg/m³, pasien ≈ {fl(rr_55, 1)}× lebih banyak daripada saat udara Baik, lalu kenaikannya melandai pada polusi ekstrem.",
         "Dinas kesehatan dan rumah sakit"),
        ("Kabut asap menambah ribuan pasien",
         f"Selama kabut asap diperkirakan ada {rp(tot['berlebih_tanpa_potong'])}–{rp(tot['berlebih_model'])} pasien ISPA balita tambahan di lima rumah sakit "
         f"(dari {rp(tot['teramati'])} pasien yang tercatat pada {rp(kb['n_hari_episode'])} hari-rumah sakit). Bebannya terpusat di beberapa kota dan terjadi pada Agustus–Oktober.",
         "Badan penanggulangan bencana (BNPB/BPBD) dan rumah sakit"),
        ("Daerah paling berisiko ada di lahan gambut Kalimantan dan Sumatera",
         f"Lima daerah teratas: {top5}. Skor 0–100 menggabungkan beban polusi, beban kesehatan, kerentanan, dan tren; gunakan hanya untuk membandingkan antar daerah.",
         "Pemerintah pusat dan dinas lingkungan hidup"),
        (f"{K6['n_provinsi_tanpa_stasiun']} dari 38 provinsi belum punya alat pengukur udara",
         f"Selain itu, {n_blm} dari {len(qc)} lokasi datanya belum lengkap. Usulan prioritas: memasang alat di {', '.join(A.provinsi)}; memperbaiki alat di {', '.join(nm(k) for k in B.kode_stasiun)}.",
         "Pemerintah pusat dan dinas lingkungan hidup"),
        (f"\"Polusi tinggi, pasien sedikit\" di {nm('BJB-01')} dan {nm('SM2-01')} bukan berarti aman",
         f"Kedua rumah sakit mencatat pasien lebih sedikit daripada yang diharapkan dari tingkat polusinya. Sebagian di {nm('BJB-01')} berasal dari alat yang macet (temuan pertama); "
         f"sisanya berasal dari tingkat dasar pasien yang rendah dan perbedaan pencatatan rumah sakit, bukan dari udara yang lebih bersih.",
         "Dinas kesehatan dan rumah sakit"),
    ]


# langkah per jenis wilayah. Angka disalin dari reports/findings/05_insights.md (tabel "Rekomendasi kebijakan per tipe wilayah").
REKOMENDASI = {
    "Gambut": dict(
        bukti=["8 lokasi; debu halus rata-rata 50,0 µg/m³", "26,1% hari di atas batas aman nasional", "128 hari kabut asap (paling banyak)", "Skor risiko rata-rata 67,7 (tertinggi)",
               "Pasien ISPA balita naik 1,05 kali tiap +10 µg/m³ (melandai pada polusi ekstrem)"],
        pemerintah="Badan penanggulangan bencana (BNPB/BPBD): siaga kabut asap Agustus–Oktober. Dinas lingkungan hidup: pemantauan langsung dengan peringatan bila alat macet atau data kosong.",
        rumah_sakit="Dinas kesehatan dan rumah sakit rujukan di Kalimantan Tengah dan Sumatera: siapkan lonjakan pasien balita dan lansia bila polusi di atas 150 µg/m³ selama 3 hari atau lebih.",
        warga="Pakai masker pada Agustus–Oktober; balita dan lansia tetap di dalam ruangan saat kategori udara Tidak Sehat atau lebih buruk."),
    "Industri": dict(
        bukti=["4 lokasi", "36,2% hari di atas batas aman nasional (tertinggi)", "Skor risiko rata-rata 57,1", "Pasien ISPA balita naik 1,21 kali tiap +10 µg/m³", f"Lokasi paling berisiko: {G.pendek('BTM-01')}"],
        pemerintah=f"Dinas lingkungan hidup: audit emisi dan periksa kawasan di sekitar {G.pendek('JKT-02')} (100% hari di atas batas aman) serta kawasan industri lain; "
                   f"perbaiki alat di {G.pendek('SM2-01')} (nilai maksimum alat terpotong saat musim asap) sebelum menilai kepatuhan.",
        rumah_sakit="Rumah sakit di sekitar kawasan industri: catat keluhan pernapasan menurut asal pasien agar dampaknya bisa dipantau.",
        warga="Pantau kategori udara harian; gunakan masker bila tinggal di sekitar kawasan industri."),
    "Perkotaan": dict(
        bukti=["7 lokasi; debu halus rata-rata 42,8 µg/m³", "8,6% hari di atas batas aman nasional", "Gas NO₂ memuncak pukul 8", f"Lokasi paling berisiko: {G.pendek('PSW-01')} (peringkat 2)"],
        pemerintah="Pemerintah daerah dan dinas lingkungan hidup: atur lalu lintas pada jam sibuk pagi dan sore.",
        rumah_sakit="Dinas kesehatan: keluarkan imbauan sejak polusi mencapai 35–55 µg/m³ (pasien ≈ 1,7× lebih banyak daripada saat udara Baik), jangan menunggu sampai di atas 150.",
        warga="Hindari berolahraga di tepi jalan pada jam berangkat dan pulang kerja."),
    "Jalan Raya": dict(
        bukti=["2 lokasi; 17,3% hari di atas batas aman nasional", "Hubungan lalu lintas dengan polusi antar lokasi: kuat", "Gas NO₂ memuncak pukul 17", "Pasien ISPA balita naik 1,05 kali (hanya 2 rumah sakit, belum pasti)"],
        pemerintah="Dinas lingkungan hidup: tambah alat di tepi jalan (baru 2). Dinas perhubungan: kendalikan emisi di koridor padat.",
        rumah_sakit="Dinas kesehatan dan rumah sakit: dampak kesehatan di pinggir jalan belum dapat disimpulkan sampai lebih banyak rumah sakit tercatat.",
        warga="Jauhi jalan padat saat jam sibuk; tutup jendela rumah yang menghadap jalan raya bila udara Tidak Sehat."),
    "Latar Bersih": dict(
        bukti=["6 lokasi; debu halus rata-rata 14,2 µg/m³ (19,2% hari di atas batas WHO 15 µg/m³)", "0,1% hari di atas batas aman nasional", "Pasien ISPA balita naik 1,25 kali tiap +10 µg/m³ (tertinggi, tetapi bervariasi antar rumah sakit)"],
        pemerintah=f"Pemerintah pusat (Kementerian Lingkungan Hidup): pertahankan sebagai lokasi pembanding (jangan dicabut). BMKG dan dinas lingkungan hidup: periksa alat di {G.pendek('MER-01')} dan perbaiki kelengkapan data Papua.",
        rumah_sakit="Rumah sakit: pantau pasien pernapasan saat kabut asap dari daerah lain terbawa angin.",
        warga="Udara umumnya baik; tetap pantau kategori udara harian saat musim kemarau."),
}

KETERBATASAN = [
    "**Data simulasi, hanya hubungan.** Hasil ini menunjukkan hubungan, bukan sebab-akibat. Rekomendasi adalah usulan analisis yang perlu diuji dengan data nyata sebelum menjadi kebijakan.",
    "**Besar dampak bergantung pada cara menghitung.** Kenaikan pasien 1,086 kali berlaku bila polusi ekstrem dibatasi, tetapi hanya 1,021 kali bila tidak dibatasi. Karena itu tambahan pasien ditampilkan sebagai kisaran, bukan satu angka.",
    f"**Catatan alat macet baru dibuang di dashboard.** Angka tertahan di {G.pendek('BJB-01')} selalu dibuang saat dashboard menghitung, tetapi belum pada pembersihan data dasar. Penyebab macetnya tidak diketahui, dan alat lain mungkin punya masalah serupa yang belum terdeteksi.",
    f"**Hari puncak kabut asap hilang di beberapa tempat.** Banyak hari puncak di {G.pendek('SM2-01')} dan {G.pendek('PLB-01')} tidak ikut dihitung karena catatan alat tidak lengkap, sehingga polusi di sana kemungkinan lebih tinggi daripada yang tampak. "
    f"{G.pendek('MER-01')} hampir tidak punya catatan harian, dan {G.pendek('JMB-02')} tidak dipakai.",
    "**Tebakan komputer terbatas.** Komputer tidak dapat memperkirakan puncak polusi yang belum pernah ada di data, dan datanya hanya 26 lokasi selama 2,8 tahun.",
    "**Kebutuhan lokasi baru hanya perkiraan kasar.** Daftar 38 provinsi dan titik tengahnya berasal dari pengetahuan umum (selisih bisa ratusan km), bukan data proyek. Perkiraan polusi calon lokasi berasal dari 3 lokasi terdekat, tanpa data penduduk, titik api, atau sebaran gambut.",
    "**Skor risiko memakai bobot pilihan analis.** Peringkat enam alat yang perlu diperbaiki tidak stabil; hanya tingkat prioritasnya yang dapat dipercaya. Tidak ada data penduduk atau kemiskinan untuk mengukur kerentanan.",
]
