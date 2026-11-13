"""Fungsi statistik & format untuk EDA (notebook 04).

Semua fungsi menerima data dari data/processed/ (tidak membaca data mentah). Uji nonparametrik dipilih karena
PM2.5 sangat condong ke kanan dan dipenuhi episode kabut asap.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests


# --------------------------------------------------------------------------- #
# Format angka gaya Indonesia
# --------------------------------------------------------------------------- #
def rp(x) -> str:
    return "–" if pd.isna(x) else f"{int(round(x)):,}".replace(",", ".")


def fl(x, n: int = 1) -> str:
    """Desimal gaya Indonesia (titik ribuan, koma desimal); '-0,00' dinormalkan menjadi '0,00'."""
    if pd.isna(x):
        return "–"
    t = f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return t[1:] if t.startswith("-") and not any(c in "123456789" for c in t) else t


def fp(p) -> str:
    """Format nilai-p: '<0,001' bila sangat kecil."""
    if pd.isna(p):
        return "–"
    return "<0,001" if p < 0.001 else fl(p, 3)


def pv(p) -> str:
    """Nilai-p lengkap dengan simbol: 'p < 0,001' atau 'p = 0,018'."""
    if pd.isna(p):
        return "p = –"
    return "p < 0,001" if p < 0.001 else f"p = {fl(p, 3)}"


def bintang(p) -> str:
    return "" if pd.isna(p) else ("***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns")


def bh(p) -> np.ndarray:
    """Koreksi Benjamini–Hochberg (FDR) dengan penanganan NaN."""
    p = np.asarray(p, float)
    out = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    if ok.sum():
        out[ok] = multipletests(p[ok], method="fdr_bh")[1]
    return out


# --------------------------------------------------------------------------- #
# Tren: Mann–Kendall musiman + kemiringan Sen
# --------------------------------------------------------------------------- #
def mk_musiman(y: pd.Series, alpha: float = 0.05) -> dict:
    """Seasonal Mann–Kendall (Hirsch et al.) + kemiringan Sen musiman untuk deret BULANAN ber-indeks waktu.

    NaN diperbolehkan (pasangan hanya dibentuk antar-tahun pada bulan yang sama). Kemiringan dalam satuan data per TAHUN.
    Asumsi: antar-musim independen (varians S dijumlahkan); autokorelasi tidak dikoreksi. Dengan hanya ~3 tahun data,
    dayanya rendah sehingga hasil perlu dibaca sebagai indikasi.
    """
    y = y.dropna()
    S = var = 0.0
    n_pasang = 0
    slopes = []
    musim_valid = 0
    for m in range(1, 13):
        v = y[y.index.month == m]
        n = len(v)
        if n < 2:
            continue
        musim_valid += 1
        x = v.to_numpy(float)
        thn = v.index.year.to_numpy(float)
        iu = np.triu_indices(n, 1)
        d = (x[None, :] - x[:, None])[iu]
        dy = (thn[None, :] - thn[:, None])[iu]
        S += np.sign(d).sum()
        n_pasang += len(d)
        slopes.extend((d / dy).tolist())
        _, cnt = np.unique(x, return_counts=True)
        var += (n * (n - 1) * (2 * n + 5) - np.sum(cnt * (cnt - 1) * (2 * cnt + 5))) / 18
    if n_pasang == 0 or var <= 0:
        return dict(n_bulan=len(y), n_musim=musim_valid, S=np.nan, tau=np.nan, z=np.nan, p=np.nan, slope_tahun=np.nan, ci_bawah=np.nan, ci_atas=np.nan, arah="tidak dapat dihitung")
    z = 0.0 if S == 0 else (S - np.sign(S)) / np.sqrt(var)
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    sl = np.sort(np.asarray(slopes))
    N = len(sl)
    C = stats.norm.ppf(1 - alpha / 2) * np.sqrt(var)
    lo = sl[int(np.clip(np.floor((N - C) / 2), 0, N - 1))]
    hi = sl[int(np.clip(np.ceil((N + C) / 2), 0, N - 1))]
    return dict(n_bulan=len(y), n_musim=musim_valid, S=S, tau=S / n_pasang, z=z, p=p, slope_tahun=float(np.median(sl)), ci_bawah=float(lo), ci_atas=float(hi),
                arah="naik" if (p < alpha and z > 0) else "turun" if (p < alpha and z < 0) else "tidak signifikan")


# --------------------------------------------------------------------------- #
# Kruskal–Wallis + Dunn
# --------------------------------------------------------------------------- #
def kruskal(grup: dict[str, np.ndarray]) -> dict:
    """Kruskal–Wallis; efek: epsilon² = H / (n − 1) (0,01 kecil · 0,06 sedang · 0,14 besar)."""
    arr = [np.asarray(v, float)[~np.isnan(np.asarray(v, float))] for v in grup.values()]
    H, p = stats.kruskal(*arr)
    n = sum(len(a) for a in arr)
    return dict(H=float(H), p=float(p), epsilon2=float(H / (n - 1)), n=int(n), k=len(arr), df=len(arr) - 1)


def dunn(grup: dict[str, np.ndarray], metode: str = "holm") -> pd.DataFrame:
    """Uji lanjut Dunn (koreksi ikatan) dengan penyesuaian Holm. Mengembalikan semua pasangan."""
    nama = list(grup)
    arr = [np.asarray(grup[k], float)[~np.isnan(np.asarray(grup[k], float))] for k in nama]
    semua = np.concatenate(arr)
    N = len(semua)
    r = stats.rankdata(semua)
    _, t = np.unique(semua, return_counts=True)
    T = (t ** 3 - t).sum() / (12 * (N - 1))
    idx = np.cumsum([0] + [len(a) for a in arr])
    mr = [r[idx[i]:idx[i + 1]].mean() for i in range(len(arr))]
    baris = []
    for i in range(len(nama)):
        for j in range(i + 1, len(nama)):
            se = np.sqrt((N * (N + 1) / 12 - T) * (1 / len(arr[i]) + 1 / len(arr[j])))
            z = (mr[i] - mr[j]) / se
            baris.append(dict(kelompok_a=nama[i], kelompok_b=nama[j], median_a=float(np.median(arr[i])), median_b=float(np.median(arr[j])),
                              selisih_peringkat_rata2=float(mr[i] - mr[j]), z=float(z), p=float(2 * (1 - stats.norm.cdf(abs(z))))))
    d = pd.DataFrame(baris)
    d["p_adj"] = multipletests(d["p"], method=metode)[1]
    d["signifikan"] = d["p_adj"] < 0.05
    return d


# --------------------------------------------------------------------------- #
# Mann–Whitney + ukuran efek
# --------------------------------------------------------------------------- #
def mann_whitney(x, y) -> dict:
    """Mann–Whitney dua sisi. r = 2·U/(n1·n2) − 1 (rank-biserial; >0 berarti x cenderung lebih besar). Ambang |r|: 0,1 kecil · 0,3 sedang · 0,5 besar."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    x = x[~np.isnan(x)]; y = y[~np.isnan(y)]
    U, p = stats.mannwhitneyu(x, y, alternative="two-sided")
    mx, my = np.median(x), np.median(y)
    return dict(n_x=len(x), n_y=len(y), median_x=float(mx), median_y=float(my), U=float(U), p=float(p), r=float(2 * U / (len(x) * len(y)) - 1),
                selisih_persen=float(100 * (mx - my) / my) if my else np.nan)


def label_efek(r: float) -> str:
    a = abs(r)
    return "diabaikan" if a < 0.1 else "kecil" if a < 0.3 else "sedang" if a < 0.5 else "besar"


def cramers_v(tabel: pd.DataFrame) -> dict:
    chi2, p, dof, _ = stats.chi2_contingency(tabel.to_numpy())
    n = tabel.to_numpy().sum()
    k = min(tabel.shape) - 1
    return dict(chi2=float(chi2), p=float(p), dof=int(dof), n=int(n), v=float(np.sqrt(chi2 / (n * k))) if k > 0 else np.nan)


# --------------------------------------------------------------------------- #
# Korelasi
# --------------------------------------------------------------------------- #
def spearman(x, y) -> dict:
    x = pd.Series(x, dtype=float); y = pd.Series(y, dtype=float)
    ok = x.notna() & y.notna()
    if ok.sum() < 5:
        return dict(rho=np.nan, p=np.nan, n=int(ok.sum()))
    rho, p = stats.spearmanr(x[ok], y[ok])
    return dict(rho=float(rho), p=float(p), n=int(ok.sum()))


def ringkas_rho(rhos: pd.Series) -> dict:
    """Rata-rata rho antar-RS (unit = RS), CI 95% berbasis t, uji Wilcoxon terhadap 0."""
    r = rhos.dropna()
    n = len(r)
    if n < 3:
        return dict(n_rs=n, rho_rata2=np.nan, ci_bawah=np.nan, ci_atas=np.nan, rho_median=np.nan, p_wilcoxon=np.nan, persen_positif=np.nan)
    se = r.std(ddof=1) / np.sqrt(n)
    t = stats.t.ppf(0.975, n - 1)
    try:
        pw = float(stats.wilcoxon(r).pvalue)
    except ValueError:
        pw = np.nan
    return dict(n_rs=n, rho_rata2=float(r.mean()), ci_bawah=float(r.mean() - t * se), ci_atas=float(r.mean() + t * se), rho_median=float(r.median()),
                p_wilcoxon=pw, persen_positif=float(100 * (r > 0).mean()))


def sektor_arah(deg: pd.Series, n_sektor: int = 16) -> pd.Series:
    """Indeks sektor 0..n−1 dengan sektor 0 berpusat di utara (arah asal angin)."""
    lebar = 360 / n_sektor
    return (((deg + lebar / 2) % 360) // lebar).astype("Int64")


# U=utara, T=timur, S=selatan, B=barat (urutan searah jarum jam dari utara)
NAMA_SEKTOR16 = ["U", "UTL", "TL", "TTL", "T", "TTG", "TG", "STG", "S", "SBD", "BD", "BBD", "B", "BBL", "BL", "UBL"]
