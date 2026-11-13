"""Audit teks dashboard (bahasa awam). Jalankan dengan server dashboard aktif:

    python tools/audit_teks.py --port 8501

Yang dilakukan:
  1. Membuka setiap halaman dan tab lewat Chrome (DevTools), menyimpan teks yang benar-benar tampil.
  2. Mencari pola yang tidak boleh tampil di luar halaman "Tentang data" › "Detail teknis":
     kode lokasi (KTG-02, SENS-, RS-XXX, LOC-), "stasiun", AQMS, sensor, lag, korelasi, signifikan, QC, VALID, SUSPECT,
     parquet, nama metode statistik, istilah teknis lain, dan nama bulan berbahasa Inggris.
  3. Memeriksa angka bertanda desimal pada teks statis (teks.py) terhadap reports/findings/05_insights.md.
Keluar dengan kode 1 bila ada temuan.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

HALAMAN = [("", 2), ("kondisi-udara", 3), ("waktu-rawan", 1), ("penyebab-polusi", 1), ("dampak-kesehatan", 3), ("lokasi-pengukuran", 1)]
POLA = {
    "kode lokasi": r"\b[A-Z]{2,3}-\d{2}\b", "SENS-": r"SENS-", "RS-XXX": r"RS-XXX", "LOC-": r"LOC-", "stasiun": r"(?i)stasiun", "AQMS": r"AQMS", "sensor": r"(?i)\bsensor\b",
    "lag": r"(?i)\blag\b", "korelasi": r"(?i)korelasi", "signifikan": r"(?i)signifikan", "QC": r"\bQC\b", "qc_flag": r"qc_flag", "VALID": r"\bVALID\b", "SUSPECT": r"SUSPECT", "parquet": r"(?i)parquet",
    "metode statistik": r"(?i)Mann-Kendall|Kruskal|quasi-Poisson|Random Forest|SHAP|Spearman|Gradient Boosting|permutation|spline|Benjamini|Dunn",
    "istilah teknis": r"(?i)\bmedian\b|outlier|agregasi|imputasi|\bparameter\b|flatline|bertopeng|\bnotebook\b|\bISPU\b|baku mutu|tipe lokasi|relative risk",
    "bulan Inggris": r"\b(?:Oct|Aug|May|Dec)\b",
}


def ambil_teks(port: int, chrome: str) -> dict:
    import requests
    import websocket
    cdp = 9341
    prof = ROOT / "reports" / ".chrome_audit"
    proc = subprocess.Popen([chrome, "--headless=new", "--disable-gpu", "--no-sandbox", f"--remote-debugging-port={cdp}", f"--user-data-dir={prof}", "--window-size=1600,1000", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    hasil = {}
    try:
        for _ in range(40):
            try:
                tabs = requests.get(f"http://127.0.0.1:{cdp}/json", timeout=1).json(); break
            except Exception:
                time.sleep(0.5)
        ws = websocket.create_connection([t for t in tabs if t["type"] == "page"][0]["webSocketDebuggerUrl"], timeout=90)
        n = [0]

        def call(method, **params):
            n[0] += 1
            ws.send(json.dumps({"id": n[0], "method": method, "params": params}))
            while True:
                r = json.loads(ws.recv())
                if r.get("id") == n[0]:
                    return r.get("result", {})

        def ev(js):
            return call("Runtime.evaluate", expression=js, returnByValue=True).get("result", {}).get("value")

        for slug, nt in HALAMAN:
            call("Page.navigate", url=f"http://localhost:{port}/{slug}")
            t0 = time.time()
            while time.time() - t0 < 120:
                time.sleep(1.5)
                if ev("!!document.querySelector('[data-testid=stAppViewContainer]') && !document.querySelector('[data-testid=stStatusWidget]') && document.querySelectorAll('[data-testid=stMarkdownContainer]').length>1"):
                    break
            time.sleep(3)
            hasil[slug] = {}
            for t in range(nt):
                ev(f"document.querySelectorAll('button[role=tab]')[{t}].click()"); time.sleep(3)
                # buka semua expander agar isinya ikut diperiksa
                ev("document.querySelectorAll('[data-testid=stExpander] summary').forEach(s=>{if(s.parentElement.getAttribute('open')===null) s.click()})"); time.sleep(1)
                # teks di dalam iframe sesama-asal (peta 3D) ikut diperiksa
                hasil[slug][str(t)] = {"main": ev("(document.querySelector('section.stMain')||document.body).innerText + '\\n' + [...document.querySelectorAll('iframe')].map(f=>{try{return f.contentDocument.body.innerText}catch(e){return ''}}).join('\\n')"), "side": ev("(document.querySelector('[data-testid=stSidebar]')||document.body).innerText") if t == 0 else ""}
    finally:
        proc.kill()
    return hasil


def cari_pola(hasil: dict) -> int:
    temuan = 0
    for slug, tabs in hasil.items():
        for t, x in tabs.items():
            teknis = slug == "tentang-data" and t == "2"
            teks = x["main"] + "\n" + (x["side"] or "")
            teks = re.sub(r"\b(?:home|trending_up|schedule|air|favorite|sensors|task_alt|description|keyboard_double_arrow_left|keyboard_arrow_down|expand_more)\b", " ", teks)   # nama ikon, tidak tampil
            for nama, pola in POLA.items():
                hit = sorted(set(m.group(0) for m in re.finditer(pola, teks)))
                if hit:
                    print(f"/{slug} tab{t}: {nama}: {hit[:8]}" + ("  [Detail teknis: diizinkan]" if teknis else ""))
                    if not teknis:
                        temuan += len(hit)
    return temuan


def cek_angka_statis() -> int:
    from app import teks as T
    md = (ROOT / "reports" / "findings" / "05_insights.md").read_text(encoding="utf-8")
    sumber = [b for r in T.REKOMENDASI.values() for b in r["bukti"]] + [r["pemerintah"] + " " + r["rumah_sakit"] + " " + r["warga"] for r in T.REKOMENDASI.values()] + T.KETERBATASAN
    salah = 0
    for kalimat in sumber:
        for tok in re.findall(r"(?<![\w.,])\d+(?:[.,]\d+)+(?!\d)", kalimat):
            if tok not in md:
                print(f"angka tidak ditemukan di 05_insights.md: {tok}  ← \"{kalimat[:70]}…\"")
                salah += 1
    return salah


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8501)
    ap.add_argument("--chrome", default=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    ap.add_argument("--keluar", default="")
    a = ap.parse_args()
    hasil = ambil_teks(a.port, a.chrome)
    if a.keluar:
        Path(a.keluar).write_text(json.dumps(hasil, ensure_ascii=False, indent=1), encoding="utf-8")
    t1 = cari_pola(hasil)
    t2 = cek_angka_statis()
    print(f"\nTemuan pola terlarang di luar Detail teknis: {t1}\nAngka statis tidak ditemukan di laporan: {t2}")
    sys.exit(1 if (t1 or t2) else 0)
