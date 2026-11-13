"""Membangun berkas peta lokal untuk komponen peta 3D (assets/peta3d/provinsi.json).

Sumber batas provinsi (38 provinsi, termasuk 4 provinsi baru di Papua): Indonesia GeoJSON & TopoJSON Maps (38 Provinces),
https://github.com/denyherianto/indonesia-geojson-topojson-maps-with-38-provinces — lisensi data CC BY 4.0 (lihat assets/peta3d/ATRIBUSI.md).
Berkas sumber diunduh sekali ke folder sementara, lalu hasil olahan disimpan di assets/peta3d/ sehingga dashboard tidak butuh internet untuk batas wilayah.

Yang dibuat:
  provinsi     FeatureCollection: nama (sesuai nama di dashboard), pulau (kelompok pulau), kode
  garis_pulau  garis terluar tiap kelompok pulau (gabungan provinsi), untuk garis batas yang lebih tebal
  arsir        garis diagonal terpotong di dalam tiap provinsi, untuk arsir "belum ada alat pengukur"

Jalankan:  python tools/bangun_peta.py <geojson_sumber> [folder_pustaka_shapely]
Butuh shapely (hanya untuk membangun; dashboard sendiri tidak memerlukannya).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if len(sys.argv) > 2:
    sys.path.insert(0, sys.argv[2])
from shapely.geometry import LineString, MultiLineString, shape  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

SUMBER = Path(sys.argv[1])
KELUAR = ROOT / "assets" / "peta3d" / "provinsi.json"
JARAK_ARSIR = 0.55   # derajat, jarak antar garis arsir (diagonal 45°)

NAMA = {"Daerah Istimewa Yogyakarta": "DI Yogyakarta"}
PULAU = {
    "Sumatera": ["Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Kepulauan Riau", "Jambi", "Sumatera Selatan", "Kepulauan Bangka Belitung", "Bengkulu", "Lampung"],
    "Jawa": ["Banten", "DKI Jakarta", "Jawa Barat", "Jawa Tengah", "DI Yogyakarta", "Jawa Timur"],
    "Kalimantan": ["Kalimantan Barat", "Kalimantan Tengah", "Kalimantan Selatan", "Kalimantan Timur", "Kalimantan Utara"],
    "Sulawesi": ["Sulawesi Utara", "Gorontalo", "Sulawesi Tengah", "Sulawesi Barat", "Sulawesi Selatan", "Sulawesi Tenggara"],
    "Bali & Nusa Tenggara": ["Bali", "Nusa Tenggara Barat", "Nusa Tenggara Timur"],
    "Maluku": ["Maluku", "Maluku Utara"],
    "Papua": ["Papua", "Papua Barat", "Papua Barat Daya", "Papua Selatan", "Papua Tengah", "Papua Pegunungan"],
}
PULAU_DARI = {p: k for k, v in PULAU.items() for p in v}


def _bulat(c, n=3):
    return [round(x, n) for x in c]


def _arsir(geom, jarak: float):
    """Garis diagonal (arah kiri-bawah ke kanan-atas) yang dipotong oleh bentuk provinsi."""
    x0, y0, x1, y1 = geom.bounds
    h = y1 - y0
    hasil = []
    k = x0 - h
    while k < x1:
        garis = LineString([(k, y0), (k + h, y1)]).intersection(geom)
        bagian = [garis] if garis.geom_type == "LineString" else list(getattr(garis, "geoms", []))
        for b in bagian:
            if b.geom_type == "LineString" and b.length > 0.05:
                hasil.append([_bulat(c) for c in b.coords])
        k += jarak
    return hasil


def main() -> None:
    g = json.loads(SUMBER.read_text(encoding="utf-8"))
    fitur, geoms = [], {}
    for f in g["features"]:
        nama = NAMA.get(f["properties"]["PROVINSI"], f["properties"]["PROVINSI"])
        if nama not in PULAU_DARI:
            raise SystemExit(f"provinsi tidak terpetakan ke pulau: {nama}")
        geom = shape(f["geometry"]).buffer(0)
        geoms[nama] = geom
        sederhana = geom.simplify(0.01, preserve_topology=True)
        fitur.append({"type": "Feature", "properties": {"nama": nama, "pulau": PULAU_DARI[nama], "kode": f["properties"]["KODE_PROV"]},
                      "geometry": {"type": sederhana.geom_type, "coordinates": json.loads(json.dumps(sederhana.__geo_interface__["coordinates"]))}})
    if len(fitur) != 38:
        raise SystemExit(f"jumlah provinsi {len(fitur)} ≠ 38")

    # garis terluar tiap kelompok pulau
    garis = []
    for pulau, daftar in PULAU.items():
        u = unary_union([geoms[p] for p in daftar]).simplify(0.01, preserve_topology=True)
        polys = [u] if u.geom_type == "Polygon" else list(u.geoms)
        for p in polys:
            garis.append({"type": "Feature", "properties": {"pulau": pulau}, "geometry": {"type": "LineString", "coordinates": [_bulat(c) for c in p.exterior.coords]}})

    arsir = {nama: _arsir(geom.simplify(0.01, preserve_topology=True), JARAK_ARSIR) for nama, geom in geoms.items()}

    def _bulatkan(coords):
        return [_bulatkan(c) for c in coords] if isinstance(coords[0], (list, tuple)) else _bulat(coords)
    for f in fitur:
        f["geometry"]["coordinates"] = _bulatkan(f["geometry"]["coordinates"])

    KELUAR.parent.mkdir(parents=True, exist_ok=True)
    KELUAR.write_text(json.dumps({"provinsi": {"type": "FeatureCollection", "features": fitur}, "garis_pulau": {"type": "FeatureCollection", "features": garis}, "arsir": arsir},
                                 ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{KELUAR.relative_to(ROOT)}: {KELUAR.stat().st_size / 1024:.0f} KB · {len(fitur)} provinsi · {len(garis)} garis pulau · {sum(len(v) for v in arsir.values())} garis arsir")


if __name__ == "__main__":
    main()
