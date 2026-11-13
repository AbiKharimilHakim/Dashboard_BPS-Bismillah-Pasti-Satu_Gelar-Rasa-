"""Jalankan seluruh pipeline pembersihan (langkah 1–8) dan tulis keluaran.

Pemakaian (dari folder proyek):
    python etl/run_preprocessing.py

Idempoten: dijalankan ulang akan menimpa keluaran dengan hasil yang sama.
Data mentah di data/raw/ hanya dibaca. Bila salah satu validasi gagal, skrip berhenti
dengan AssertionError dan TIDAK menulis berkas keluaran.
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

from src import clean, config as cfg  # noqa: E402


def main() -> None:
    t0 = time.time()
    print("== Pipeline pembersihan DA Gelar Rasa 2026 ==")
    res = clean.jalankan_pipeline(cfg.RAW_DIR, verbose=True)
    print("\nValidasi:")
    for r in res["validasi"].itertuples():
        print(f"  [{'OK' if r.lulus else 'GAGAL'}] {r.pemeriksaan}" + (f"  ({r.detail})" if r.detail else ""))
    paths = clean.tulis_keluaran(res)
    print("\nKeluaran:")
    for nama, p in paths.items():
        print(f"  {nama:32s} -> {p.relative_to(ROOT)}")
    print(f"\nBaris: aq_hourly={len(res['hourly']):,} | aq_daily={len(res['daily']):,} | health_aq_daily={len(res['health']):,} | "
          f"sites_clean={len(res['sites'])} | log={len(res['log']):,}")
    print(f"Stasiun dikecualikan dari tabel analisis: {res['dikecualikan']}")
    print(f"Selesai dalam {time.time() - t0:.1f} detik.")


if __name__ == "__main__":
    main()
