"""Model & analisis lanjutan untuk notebook 05 (insight).

Bagian:
  1. Model ML PM2.5 harian (time-split), permutation importance berkelompok, regresi berganda
  2. Model kesehatan: quasi-Poisson/NB dengan efek tetap RS, spline waktu, distributed lag (Almon), kasus berlebih
  3. Clustering profil stasiun
  4. Uji anomali (pergeseran fase, titik perubahan, korelasi silang)
  5. Skor risiko & analisis sensitivitas bobot
  6. Geometri jaringan (jarak, IDW) dan skor prioritas

Semua fungsi membaca hanya tabel dari data/processed/ (diberikan oleh pemanggil).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from patsy import dmatrix
from scipy import stats
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

from . import config as cfg

# =========================================================================== #
# 1. ML PM2.5 harian
# =========================================================================== #
TIPE_DUMMY = [f"tipe_{t}" for t in cfg.URUTAN_KELOMPOK]
GRUP_FITUR = {
    "Cuaca (suhu, kelembapan, angin)": ["temperature_c", "humidity_pct", "wind_speed_ms"],
    "Waktu (bulan, hari-tahun, hari-minggu)": ["bulan", "doy", "hari_ke"],
    "Tipe lokasi": TIPE_DUMMY,
    "Lalu lintas & jarak ke jalan": ["lalu_lintas", "jarak_jalan"],
    "Koordinat (lintang, bujur)": ["lintang", "bujur"],
}


def bangun_fitur(daily: pd.DataFrame, sites: pd.DataFrame, stasiun: list[str]) -> pd.DataFrame:
    """Tabel fitur harian per stasiun-hari untuk stasiun terpilih (PM2.5 sah). baseline_pm25 SENGAJA tidak dipakai (hampir tautologis dengan target)."""
    st = sites.set_index("kode_stasiun")
    d = daily[daily["kode_stasiun"].astype(str).isin(stasiun) & daily["pm25_ug_m3"].notna()].copy()
    d["kode_stasiun"] = d["kode_stasiun"].astype(str)
    d = d.dropna(subset=["temperature_c", "humidity_pct", "wind_speed_ms"])
    d["tipe"] = d["kode_stasiun"].map(st["kelompok_lokasi"])
    d["doy"] = d["tanggal"].dt.dayofyear
    for t in cfg.URUTAN_KELOMPOK:
        d[f"tipe_{t}"] = (d["tipe"] == t).astype(int)
    d["lalu_lintas"] = d["kode_stasiun"].map(st["traffic_intensity_per_h"])
    d["jarak_jalan"] = d["kode_stasiun"].map(st["distance_to_road_m"])
    d["lintang"] = d["kode_stasiun"].map(st["latitude_dd"])
    d["bujur"] = d["kode_stasiun"].map(st["longitude_dd"])
    d["y"] = d["pm25_ug_m3"]
    d["y_log"] = np.log1p(d["pm25_ug_m3"])
    d["episode"] = d["episode_asap"].astype(bool)
    return d.reset_index(drop=True)


def kolom_fitur(grup: list[str]) -> list[str]:
    return [c for g in grup for c in GRUP_FITUR[g]]


def skor(y_log: np.ndarray, p_log: np.ndarray, mask_non_episode: np.ndarray | None = None) -> dict:
    """Metrik pada skala log (R²) dan skala asli (R², MAE, RMSE). Prediksi dikembalikan dengan expm1."""
    y, p = np.expm1(y_log), np.clip(np.expm1(p_log), 0, None)
    out = dict(r2_log=float(r2_score(y_log, p_log)), r2=float(r2_score(y, p)), mae=float(mean_absolute_error(y, p)), rmse=float(np.sqrt(np.mean((y - p) ** 2))))
    if mask_non_episode is not None and mask_non_episode.sum() > 10:
        out["r2_non_episode"] = float(r2_score(y[mask_non_episode], p[mask_non_episode]))
        out["mae_non_episode"] = float(mean_absolute_error(y[mask_non_episode], p[mask_non_episode]))
    return out


def buat_model(jenis: str, seed: int = 1):
    if jenis == "rf":
        return RandomForestRegressor(n_estimators=300, min_samples_leaf=3, max_features=0.6, n_jobs=-1, random_state=seed)
    return GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.8, random_state=seed)


def permutation_berkelompok(model, X: pd.DataFrame, y_log: np.ndarray, grup: dict[str, list[str]], n_ulang: int = 10, seed: int = 0) -> pd.DataFrame:
    """Permutation importance per KELOMPOK fitur (kolom satu kelompok diacak bersama, menjaga hubungan di dalam kelompok).
    Penurunan R² (skala log) pada data uji; semakin besar = semakin penting."""
    rng = np.random.default_rng(seed)
    dasar = r2_score(y_log, model.predict(X))
    baris = []
    for nama, kol in grup.items():
        kol = [c for c in kol if c in X.columns]
        if not kol:
            continue
        d = []
        for _ in range(n_ulang):
            Xp = X.copy()
            idx = rng.permutation(len(X))
            Xp[kol] = X[kol].to_numpy()[idx]
            d.append(dasar - r2_score(y_log, model.predict(Xp)))
        baris.append(dict(kelompok=nama, penurunan_r2=float(np.mean(d)), sd=float(np.std(d, ddof=1)), n_fitur=len(kol)))
    return pd.DataFrame(baris).sort_values("penurunan_r2", ascending=False).reset_index(drop=True)


def permutation_fitur(model, X: pd.DataFrame, y_log: np.ndarray, n_ulang: int = 10, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dasar = r2_score(y_log, model.predict(X))
    baris = []
    for c in X.columns:
        d = []
        for _ in range(n_ulang):
            Xp = X.copy(); Xp[c] = X[c].to_numpy()[rng.permutation(len(X))]
            d.append(dasar - r2_score(y_log, model.predict(Xp)))
        baris.append(dict(fitur=c, penurunan_r2=float(np.mean(d)), sd=float(np.std(d, ddof=1))))
    return pd.DataFrame(baris).sort_values("penurunan_r2", ascending=False).reset_index(drop=True)


def permutation_dalam_strata(model, X: pd.DataFrame, y_log: np.ndarray, kolom: list[str], strata: np.ndarray, n_ulang: int = 10, seed: int = 0) -> tuple[float, float]:
    """Permutation importance dengan pengacakan HANYA di dalam strata (mis. stasiun): memisahkan pengaruh variasi dalam-stasiun (harian)
    dari perbedaan rata-rata antar-stasiun. Mengembalikan (rata-rata penurunan R², sd)."""
    rng = np.random.default_rng(seed)
    dasar = r2_score(y_log, model.predict(X))
    idx_strata = [np.where(strata == s)[0] for s in np.unique(strata)]
    d = []
    for _ in range(n_ulang):
        Xp = X.copy()
        arr = X[kolom].to_numpy().copy()
        for ix in idx_strata:
            arr[ix] = arr[rng.permutation(ix)]
        Xp[kolom] = arr
        d.append(dasar - r2_score(y_log, model.predict(Xp)))
    return float(np.mean(d)), float(np.std(d, ddof=1))


def regresi_berganda(latih: pd.DataFrame, uji: pd.DataFrame, bulan_dummy: bool = True):
    """OLS pada log1p(PM2.5): cuaca + tipe lokasi + lalu lintas/jarak + bulan (dummy) + akhir pekan; SE klaster per stasiun.
    Mengembalikan (hasil, prediksi_uji_log, tabel_koefisien_terstandar)."""
    kol = ["temperature_c", "humidity_pct", "wind_speed_ms", "lalu_lintas", "jarak_jalan"] + [t for t in TIPE_DUMMY if t != "tipe_Perkotaan"]
    X = latih[kol].copy(); Xu = uji[kol].copy()
    X["akhir_pekan"] = latih["akhir_pekan"].astype(int).values; Xu["akhir_pekan"] = uji["akhir_pekan"].astype(int).values
    if bulan_dummy:
        for m in range(2, 13):
            X[f"bulan_{m}"] = (latih["bulan"] == m).astype(int).values; Xu[f"bulan_{m}"] = (uji["bulan"] == m).astype(int).values
    mu, sd = X.mean(), X.std().replace(0, 1)
    Xs, Xus = (X - mu) / sd, (Xu - mu) / sd
    res = sm.OLS(latih["y_log"].values, sm.add_constant(Xs)).fit(cov_type="cluster", cov_kwds={"groups": latih["kode_stasiun"].astype("category").cat.codes})
    pred = res.predict(sm.add_constant(Xus, has_constant="add"))
    tabel = pd.DataFrame({"koef_terstandar": res.params, "se": res.bse, "p": res.pvalues}).drop(index="const")
    return res, np.asarray(pred), tabel


# =========================================================================== #
# 2. Model kesehatan
# =========================================================================== #
LAG = list(cfg.LAG_PM25)
KOL_LAG = [f"pm25_lag{k}" for k in LAG]
KASUS = ["resp_admissions_under5", "resp_admissions_over60", "asthma_emergency_cases", "copd_admissions", "resp", "cvd", "death"]
NAMA_KASUS = {"resp_admissions_under5": "ISPA balita (<5 th)", "resp_admissions_over60": "ISPA lansia (>60 th)", "asthma_emergency_cases": "Asma (IGD)",
              "copd_admissions": "PPOK", "resp": "Pernapasan umum", "cvd": "Kardiovaskular", "death": "Kematian"}
CAP_PM25 = 250.4        # batas atas kategori ISPU 'Sangat Tidak Sehat': eksposur di atasnya dipotong (utama); tanpa pemotongan = sensitivitas
SATUAN = 10.0           # RR dilaporkan per +10 µg/m³


def siapkan_kesehatan(health: pd.DataFrame, cap: float | None = CAP_PM25, lag_lengkap: bool = True) -> pd.DataFrame:
    """Baris RS-hari dengan paparan lag 0–7 lengkap; eksposur dalam satuan 10 µg/m³ (dipotong pada `cap`)."""
    H = health.copy()
    if lag_lengkap:
        H = H[H[KOL_LAG].notna().all(axis=1)].copy()
    H["t"] = (H["date"] - cfg.WINDOW_START.normalize()).dt.days
    for k in LAG:
        x = H[f"pm25_lag{k}"]
        H[f"e{k}"] = (x.clip(upper=cap) if cap else x) / SATUAN
    H["balita_lansia"] = H["resp_admissions_under5"].astype(float) + H["resp_admissions_over60"].astype(float)
    H["hospital_id"] = H["hospital_id"].astype(str)
    return H.reset_index(drop=True)


def desain_dasar(H: pd.DataFrame, df_waktu: int = 20) -> pd.DataFrame:
    """Matriks desain tanpa eksposur: efek tetap RS, hari dalam minggu, spline suhu & kelembapan (df 3), spline waktu (df)."""
    f = f"C(hospital_id) + C(dow) + cr(temp_c, df=3) + cr(rhum_pct, df=3) + cr(t, df={df_waktu})"
    return dmatrix(f, H, return_type="dataframe")


def fit_poisson(y, X: pd.DataFrame, groups, skala_x2: bool = True):
    """GLM Poisson dengan skala Pearson (quasi-Poisson) dan kovarians robust klaster per RS."""
    return sm.GLM(np.asarray(y, float), X, family=sm.families.Poisson()).fit(cov_type="cluster", cov_kwds={"groups": np.asarray(groups)}, scale="X2" if skala_x2 else None)


def alpha_nb(res_pois, y) -> float:
    """Alpha NB2 dengan metode momen dari fit Poisson."""
    mu = res_pois.mu
    y = np.asarray(y, float)
    return float(max(1e-6, np.sum((y - mu) ** 2 - mu) / np.sum(mu ** 2)))


def fit_nb(y, X: pd.DataFrame, groups, alpha: float):
    return sm.GLM(np.asarray(y, float), X, family=sm.families.NegativeBinomial(alpha=alpha)).fit(cov_type="cluster", cov_kwds={"groups": np.asarray(groups)})


def rr(res, nama: str) -> dict:
    """RR per +10 µg/m³ (eksposur sudah dalam satuan 10) dengan CI 95% robust."""
    b, se = res.params[nama], res.bse[nama]
    return dict(rr=float(np.exp(b)), rr_bawah=float(np.exp(b - 1.96 * se)), rr_atas=float(np.exp(b + 1.96 * se)), beta=float(b), se=float(se), p=float(res.pvalues[nama]))


def tabel_rr_lag(H: pd.DataFrame, Xd: pd.DataFrame, groups, kasus: list[str], nb: bool = False) -> pd.DataFrame:
    """RR per +10 µg/m³ untuk setiap kasus dan lag tunggal (sampel sama: lag 0–7 lengkap)."""
    baris = []
    for c in kasus:
        y = H[c].astype(float).to_numpy()
        for k in LAG:
            X = Xd.copy(); X[f"e{k}"] = H[f"e{k}"].to_numpy()
            r = fit_poisson(y, X, groups)
            baris.append(dict(kasus=c, lag=k, dispersi=float(r.scale), **rr(r, f"e{k}")))
    return pd.DataFrame(baris)


def almon_basis(H: pd.DataFrame, deg: int = 2) -> pd.DataFrame:
    """Z_j = Σ_k k^j · e_k (polynomial distributed lag Almon, derajat `deg`)."""
    Z = pd.DataFrame(index=H.index)
    for j in range(deg + 1):
        Z[f"z{j}"] = sum((k ** j) * H[f"e{k}"] for k in LAG)
    return Z


def dlm_almon(H: pd.DataFrame, Xd: pd.DataFrame, y, groups, deg: int = 2) -> dict:
    """DLM terkendala (Almon). Mengembalikan θ, kovarians, RR per lag, dan RR kumulatif lag 0–7 (per +10 µg/m³ pada semua lag)."""
    Z = almon_basis(H, deg)
    X = pd.concat([Xd, Z], axis=1)
    res = fit_poisson(y, X, groups)
    nm = list(Z.columns)
    th, cov = res.params[nm].to_numpy(), res.cov_params().loc[nm, nm].to_numpy()
    A = np.array([[k ** j for j in range(deg + 1)] for k in LAG], float)            # (8, deg+1)
    beta_k = A @ th
    se_k = np.sqrt(np.einsum("ij,jk,ik->i", A, cov, A))
    c = A.sum(axis=0)
    cum, se_c = float(c @ th), float(np.sqrt(c @ cov @ c))
    lag_tab = pd.DataFrame(dict(lag=LAG, rr=np.exp(beta_k), rr_bawah=np.exp(beta_k - 1.96 * se_k), rr_atas=np.exp(beta_k + 1.96 * se_k)))
    return dict(res=res, theta=th, cov=cov, A=A, tabel_lag=lag_tab, rr_kumulatif=float(np.exp(cum)), rr_kum_bawah=float(np.exp(cum - 1.96 * se_c)), rr_kum_atas=float(np.exp(cum + 1.96 * se_c)),
                beta_kum=cum, se_kum=se_c, dispersi=float(res.scale))


def selisih_rr(H: pd.DataFrame, Xd: pd.DataFrame, groups, kasus_a: str, kasus_b: str, kolom_e: list[str] | str) -> dict:
    """Uji selisih koefisien dua kasus pada model gabungan (blok-diagonal) dengan kovarians klaster per RS yang menangkap korelasi antar-model.
    `kolom_e`: satu nama eksposur atau daftar kolom (jumlahkan = efek kumulatif pada lag-lag itu)."""
    kolom_e = [kolom_e] if isinstance(kolom_e, str) else kolom_e
    ea = H[kolom_e].sum(axis=1) if len(kolom_e) > 1 else H[kolom_e[0]]
    n = len(H)
    Xa, Xb = Xd.copy(), Xd.copy(); Xa["e"], Xb["e"] = ea.to_numpy(), ea.to_numpy()
    Xa.columns = [f"a_{c}" for c in Xa.columns]; Xb.columns = [f"b_{c}" for c in Xb.columns]
    blok = pd.concat([pd.concat([Xa, pd.DataFrame(0.0, index=Xa.index, columns=Xb.columns)], axis=1),
                      pd.concat([pd.DataFrame(0.0, index=Xb.index, columns=Xa.columns), Xb], axis=1)], axis=0, ignore_index=True)
    y = np.r_[H[kasus_a].astype(float).to_numpy(), H[kasus_b].astype(float).to_numpy()]
    g = np.r_[np.asarray(groups), np.asarray(groups)]
    r = fit_poisson(y, blok, g)
    ba, bb = r.params["a_e"], r.params["b_e"]
    cov = r.cov_params().loc[["a_e", "b_e"], ["a_e", "b_e"]].to_numpy()
    d = ba - bb
    se = float(np.sqrt(cov[0, 0] + cov[1, 1] - 2 * cov[0, 1]))
    z = d / se
    return dict(beta_a=float(ba), beta_b=float(bb), selisih=float(d), se=se, z=float(z), p=float(2 * (1 - stats.norm.cdf(abs(z)))), rasio_rr=float(np.exp(d)),
                rasio_bawah=float(np.exp(d - 1.96 * se)), rasio_atas=float(np.exp(d + 1.96 * se)))


def kasus_berlebih(H: pd.DataFrame, dl: dict, kasus: str, mask_hari: np.ndarray, x_ref: pd.Series, n_sim: int = 1000, seed: int = 0) -> dict:
    """Kasus berlebih pada hari terpilih (mis. episode asap) relatif terhadap eksposur acuan `x_ref` (µg/m³ per baris, di-pakai pada SEMUA lag).
    log RR_t = Σ_k β_k (e_{t−k} − e_ref);  berlebih_t = y_t · (1 − exp(−log RR_t)). CI: simulasi θ ~ N(θ̂, Σ)."""
    A, th, cov = dl["A"], dl["theta"], dl["cov"]
    E = H.loc[mask_hari, [f"e{k}" for k in LAG]].to_numpy()                                    # (n, 8) satuan 10
    e_ref = (np.minimum(x_ref.loc[mask_hari].to_numpy(), CAP_PM25) / SATUAN)[:, None]
    y = H.loc[mask_hari, kasus].astype(float).to_numpy()
    rng = np.random.default_rng(seed)
    thetas = rng.multivariate_normal(th, cov, size=n_sim)
    def total(theta):
        bk = A @ theta
        lr = ((E - e_ref) * bk[None, :]).sum(axis=1)
        return np.sum(y * (1 - np.exp(-lr)))
    est = total(th)
    sims = np.array([total(t) for t in thetas])
    return dict(berlebih=float(est), bawah=float(np.percentile(sims, 2.5)), atas=float(np.percentile(sims, 97.5)), n_hari=int(mask_hari.sum()), kasus_teramati=float(y.sum()),
                persen_dari_kasus=float(100 * est / max(y.sum(), 1)))


# =========================================================================== #
# 3. Clustering profil stasiun
# =========================================================================== #
def profil_stasiun(hourly: pd.DataFrame, stasiun: list[str], min_jam_bulan: int = 40) -> pd.DataFrame:
    """Profil bulanan (12) dan per jam lokal (24) PM2.5 per stasiun, dinormalkan dengan rata-rata profilnya (bentuk, bukan tingkat)."""
    h = hourly[hourly["kode_stasiun"].astype(str).isin(stasiun)]
    h = h.assign(kode=h["kode_stasiun"].astype(str))
    bln = h.groupby(["kode", "bulan"]).pm25_ug_m3.agg(["mean", "count"])
    bln["mean"] = bln["mean"].where(bln["count"] >= min_jam_bulan)
    B = bln["mean"].unstack().reindex(columns=range(1, 13))
    B = B.apply(lambda r: r.fillna(r.mean()), axis=1)
    J = h.groupby(["kode", "jam_lokal"]).pm25_ug_m3.median().unstack().reindex(columns=range(24))
    Br, Jr = B.div(B.mean(axis=1), axis=0), J.div(J.mean(axis=1), axis=0)
    Br.columns = [f"bln_{c}" for c in Br.columns]; Jr.columns = [f"jam_{c}" for c in Jr.columns]
    return pd.concat([Br, Jr], axis=1).reindex(stasiun)


# =========================================================================== #
# 4. Anomali
# =========================================================================== #
def ccf(a: pd.Series, b: pd.Series, lags: range, min_n: int = 100) -> pd.DataFrame:
    """Korelasi Pearson antara a(t) dan b(t − L) untuk lag L (hari) pada indeks tanggal harian. L>0: a mengikuti b setelah L hari."""
    baris = []
    for L in lags:
        x = pd.concat([a, b.shift(L, freq="D")], axis=1, join="inner").dropna()
        baris.append(dict(lag=L, r=float(x.corr().iloc[0, 1]) if len(x) >= min_n else np.nan, n=len(x)))
    return pd.DataFrame(baris)


def pettitt(x: np.ndarray) -> dict:
    """Uji titik-perubahan Pettitt (nonparametrik, perubahan tingkat tunggal)."""
    x = np.asarray(x, float); n = len(x)
    r = stats.rankdata(x)
    U = np.array([2 * r[:t + 1].sum() - (t + 1) * (n + 1) for t in range(n - 1)])
    k = int(np.argmax(np.abs(U))); K = float(np.abs(U[k]))
    p = float(min(1.0, 2 * np.exp(-6 * K ** 2 / (n ** 3 + n ** 2))))
    return dict(indeks=k, K=K, p=p)


def geser_melingkar(profil_a: np.ndarray, profil_b: np.ndarray) -> pd.DataFrame:
    """Korelasi profil bulanan a terhadap b yang digeser s bulan (melingkar)."""
    return pd.DataFrame([dict(geser_bulan=s, r=float(np.corrcoef(profil_a, np.roll(profil_b, s))[0, 1])) for s in range(12)])


def deteksi_flatline(hourly: pd.DataFrame, kolom: str = "pm25_ug_m3", min_jam: int = 24) -> pd.DataFrame:
    """Deret nilai IDENTIK berturut-turut (jam berurutan tanpa celah) sepanjang ≥ `min_jam` jam: indikasi sensor macet / nilai tertahan.
    Pada data valid, nilai kontinu hampir tidak pernah identik > beberapa jam."""
    baris = []
    for k, x in hourly.assign(k=hourly["kode_stasiun"].astype(str)).sort_values(["k", "jam"]).groupby("k"):
        x = x.dropna(subset=[kolom])
        v = x[kolom].to_numpy()
        t = x["jam"].to_numpy()
        if len(v) == 0:
            continue
        putus = np.r_[True, (v[1:] != v[:-1]) | ((t[1:] - t[:-1]) != np.timedelta64(1, "h"))]
        gid = np.cumsum(putus)
        g = pd.DataFrame({"gid": gid, "v": v, "t": t}).groupby("gid").agg(n=("v", "size"), nilai=("v", "first"), awal=("t", "min"), akhir=("t", "max"))
        g = g[g.n >= min_jam]
        for _, r in g.iterrows():
            baris.append(dict(kode_stasiun=k, awal=pd.Timestamp(r.awal), akhir=pd.Timestamp(r.akhir), n_jam=int(r.n), nilai=float(r.nilai), n_hari=round(r.n / 24, 1)))
    return pd.DataFrame(baris, columns=["kode_stasiun", "awal", "akhir", "n_jam", "nilai", "n_hari"]).sort_values(["kode_stasiun", "awal"]).reset_index(drop=True)


def lag_dari_harian(health: pd.DataFrame, daily: pd.DataFrame, kolom: str = "pm25_ug_m3") -> pd.DataFrame:
    """Hitung ulang PM2.5 lag 0–7 (hari kalender) dan rata-rata 3 hari dari tabel harian (yang boleh sudah dimodifikasi/bertopeng)."""
    P = daily.assign(k=daily["kode_stasiun"].astype(str)).pivot(index="tanggal", columns="k", values=kolom)
    P = P.reindex(pd.date_range(cfg.WINDOW_START.normalize(), cfg.WINDOW_END.normalize(), freq="D"))
    h = health.copy()
    k = h["kode_stasiun"].astype(str)
    for L in LAG:
        ser = P.shift(L)
        h[f"pm25_lag{L}"] = [ser.at[d, s] if (s in ser.columns and d in ser.index) else np.nan for d, s in zip(h["date"], k)]
    return h


# =========================================================================== #
# 5. Skor risiko & sensitivitas bobot
# =========================================================================== #
def persentil(s: pd.Series) -> pd.Series:
    """Peringkat persentil 0–1 (nilai tinggi = 1); NaN dipertahankan."""
    return s.rank(pct=True, method="average")


def skor_berbobot(komp: pd.DataFrame, bobot: dict[str, float]) -> pd.Series:
    w = pd.Series(bobot, dtype=float); w = w / w.sum()
    return (komp[list(w.index)] * w).sum(axis=1, min_count=1)


def sensitivitas_bobot(komp: pd.DataFrame, bobot_dasar: dict[str, float], n: int = 5000, seed: int = 7, top_k: int = 5) -> dict:
    """Sensitivitas peringkat terhadap bobot: (a) Dirichlet(1) acak; (b) satu-per-satu ±50%. Peringkat 1 = risiko tertinggi."""
    rng = np.random.default_rng(seed)
    kol = list(bobot_dasar)
    dasar = skor_berbobot(komp, bobot_dasar).rank(ascending=False, method="min")
    W = rng.dirichlet(np.ones(len(kol)), size=n)
    K = komp[kol].to_numpy()
    S = np.nansum(K[None, :, :] * W[:, None, :], axis=2)
    R = (-S).argsort(axis=1).argsort(axis=1) + 1
    rk = pd.DataFrame(R, columns=komp.index)
    ring = pd.DataFrame({"peringkat_dasar": dasar, "median": rk.median(), "p05": rk.quantile(0.05), "p95": rk.quantile(0.95), f"peluang_top{top_k}": (rk <= top_k).mean()})
    rho = [stats.spearmanr(dasar, rk.iloc[i])[0] for i in range(0, n, max(1, n // 500))]
    oat = []
    for k in kol:
        for f in (0.5, 1.5):
            b = dict(bobot_dasar); b[k] = b[k] * f
            r = skor_berbobot(komp, b).rank(ascending=False, method="min")
            oat.append(dict(komponen=k, faktor=f, spearman_vs_dasar=float(stats.spearmanr(dasar, r)[0]), top_k_sama=int(len(set(dasar.nsmallest(top_k).index) & set(r.nsmallest(top_k).index)))))
    return dict(ringkasan=ring.sort_values("peringkat_dasar"), rho_dirichlet_median=float(np.median(rho)), rho_dirichlet_p05=float(np.percentile(rho, 5)), oat=pd.DataFrame(oat))


# =========================================================================== #
# 6. Geometri jaringan
# =========================================================================== #
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl = np.radians(np.asarray(lon2) - np.asarray(lon1)); dp = p2 - p1
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def matriks_jarak(df: pd.DataFrame, lat="latitude_dd", lon="longitude_dd") -> pd.DataFrame:
    la, lo = df[lat].to_numpy(), df[lon].to_numpy()
    M = haversine_km(la[:, None], lo[:, None], la[None, :], lo[None, :])
    return pd.DataFrame(M, index=df.index, columns=df.index)


def idw(lat: float, lon: float, ref: pd.DataFrame, nilai: pd.Series, k: int = 3, p: float = 2.0, lat_c="latitude_dd", lon_c="longitude_dd") -> tuple[float, list[str], np.ndarray]:
    """Rata-rata berbobot jarak-invers dari k stasiun acuan terdekat (nilai NaN dilewati)."""
    d = haversine_km(lat, lon, ref[lat_c].to_numpy(), ref[lon_c].to_numpy())
    o = pd.DataFrame({"d": d, "v": nilai.reindex(ref.index).to_numpy()}, index=ref.index).dropna().sort_values("d").head(k)
    w = 1 / np.maximum(o.d.to_numpy(), 1.0) ** p
    return float(np.sum(w * o.v.to_numpy()) / w.sum()), o.index.tolist(), o.d.to_numpy()


# Sentroid kasar 38 provinsi (pengetahuan umum, BUKAN data proyek; akurasi ± ratusan km) untuk analisis kesenjangan jaringan.
PROVINSI_ACUAN = {
    "Aceh": (4.7, 96.7), "Sumatera Utara": (2.1, 99.5), "Sumatera Barat": (-0.9, 100.4), "Riau": (0.5, 101.7), "Kepulauan Riau": (1.0, 104.5), "Jambi": (-1.6, 103.6),
    "Sumatera Selatan": (-3.3, 104.0), "Bengkulu": (-3.8, 102.3), "Lampung": (-4.9, 105.0), "Kepulauan Bangka Belitung": (-2.7, 106.4),
    "DKI Jakarta": (-6.2, 106.8), "Jawa Barat": (-6.9, 107.6), "Banten": (-6.4, 106.1), "Jawa Tengah": (-7.2, 110.2), "DI Yogyakarta": (-7.9, 110.4), "Jawa Timur": (-7.8, 112.5),
    "Bali": (-8.4, 115.2), "Nusa Tenggara Barat": (-8.6, 117.4), "Nusa Tenggara Timur": (-9.6, 121.0),
    "Kalimantan Barat": (0.0, 110.5), "Kalimantan Tengah": (-1.7, 113.4), "Kalimantan Selatan": (-3.1, 115.3), "Kalimantan Timur": (0.5, 116.4), "Kalimantan Utara": (3.0, 116.5),
    "Sulawesi Utara": (1.0, 124.8), "Gorontalo": (0.7, 122.4), "Sulawesi Tengah": (-1.4, 121.4), "Sulawesi Barat": (-2.5, 119.4), "Sulawesi Selatan": (-3.7, 120.0), "Sulawesi Tenggara": (-4.1, 122.2),
    "Maluku": (-3.2, 129.4), "Maluku Utara": (1.2, 127.9), "Papua Barat": (-1.3, 133.0), "Papua Barat Daya": (-1.0, 131.5), "Papua": (-3.5, 139.5),
    "Papua Tengah": (-3.5, 136.2), "Papua Pegunungan": (-4.1, 138.9), "Papua Selatan": (-7.5, 139.5),
}
assert len(PROVINSI_ACUAN) == 38
