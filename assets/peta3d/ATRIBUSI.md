# Atribusi data & pustaka peta 3D

| Berkas | Sumber | Lisensi |
|---|---|---|
| `provinsi.json` (batas 38 provinsi, garis pulau, arsir) | Diolah dari *Indonesia GeoJSON & TopoJSON Maps (38 Provinces)* — https://github.com/denyherianto/indonesia-geojson-topojson-maps-with-38-provinces | CC BY 4.0 (data), MIT (kode); lihat `LICENSE_sumber_geojson.txt` |
| `deck.min.js` | deck.gl 8.9.36 (vis.gl) — https://deck.gl | MIT |

Perubahan terhadap data sumber (dibuat oleh `tools/bangun_peta.py`, dijalankan sekali; dashboard tidak butuh internet untuk batas wilayah):
- Bentuk disederhanakan (toleransi 0,01°) dan koordinat dibulatkan 3 desimal agar ringan (±115 KB).
- Nama provinsi disamakan dengan nama di dashboard (mis. "Daerah Istimewa Yogyakarta" → "DI Yogyakarta"); tiap provinsi diberi kelompok pulau.
- Ditambahkan `garis_pulau` (garis terluar gabungan provinsi per kelompok pulau) dan `arsir` (garis diagonal terpotong di dalam provinsi).

Batas pada peta bersifat ilustrasi untuk menampilkan sebaran lokasi pengukuran, bukan peta resmi batas wilayah.
