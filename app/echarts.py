"""Helper ECharts untuk dashboard: satu tema (font, palet, tooltip gelap membulat, animasi) untuk donat, batang, dan garis/area.

Efek interaksi "timbul" bersifat bawaan ECharts (emphasis/blur/select); klik dikirim ke Streamlit lewat `events`
dan dipakai halaman untuk menyorot elemen dan menampilkan kartu detail. Isi, angka, dan filter tidak berubah.
"""
from __future__ import annotations

import json
import math as _math
from typing import Sequence

import streamlit as st
from streamlit_echarts import JsCode, st_echarts

from . import theme as T, ui

FONT = "Inter, sans-serif"      # font dimuat ke tiap iframe grafik oleh skrip di app/ui.py (_JS_FONT)
DURASI = 900            # animasi masuk (ms)
BAYANGAN = T.rgba(T.ROSE_DEEP, 0.28)
REDUP = 0.35            # opasitas elemen yang tidak disorot
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


# --------------------------------------------------------------------------- #
# tooltip & dasar tema
# --------------------------------------------------------------------------- #
def _js(kode: str) -> str:
    """Kode JavaScript untuk opsi ECharts (streamlit-echarts 0.4: JsCode(...).js_code)."""
    return JsCode(kode).js_code


def _js_angka(desimal: int) -> str:
    return (f"var f=function(v){{if(v===null||v===undefined||isNaN(v))return '–';"
            f"return Number(v).toLocaleString('id-ID',{{minimumFractionDigits:{desimal},maximumFractionDigits:{desimal}}});}};")


def _tooltip(trigger: str, satuan: str, desimal: int, persen: bool = False) -> dict:
    """Tooltip gelap membulat (seperti referensi): judul tebal, penanda warna, nilai + satuan."""
    suffix = f" {satuan}" if satuan else ""
    if trigger == "item":
        fmt = (f"function(p){{{_js_angka(desimal)}"
               f"var h='<div style=\"font-weight:700;margin-bottom:4px\">'+p.name+'</div>';"
               f"var v=Array.isArray(p.value)?p.value[p.value.length-1]:p.value;"
               f"h+='<div style=\"display:flex;align-items:center;gap:6px\">'+p.marker+'<b>'+f(v)+'{suffix}</b>'"
               + ("+'<span style=\"opacity:.75;margin-left:6px\">('+Number(p.percent).toLocaleString('id-ID',{maximumFractionDigits:1})+'%)</span>'" if persen else "")
               + "+'</div>';return h;}")
    else:
        fmt = (f"function(ps){{{_js_angka(desimal)}var a=Array.isArray(ps)?ps:[ps];"
               f"var h='<div style=\"font-weight:700;margin-bottom:4px\">'+(a[0].axisValueLabel||a[0].name)+'</div>';"
               f"a.forEach(function(p){{var v=Array.isArray(p.value)?p.value[p.value.length-1]:p.value;"
               f"h+='<div style=\"display:flex;align-items:center;gap:6px\">'+p.marker+'<span style=\"opacity:.85\">'+(p.seriesName||'')+'</span>"
               f"<b style=\"margin-left:auto;padding-left:14px\">'+f(v)+'{suffix}</b></div>';}});return h;}}")
    t = {"trigger": trigger, "backgroundColor": T.rgba(T.TOOLTIP, 0.96), "borderWidth": 0, "padding": [9, 13],
         "textStyle": {"color": T.PUTIH, "fontSize": 12, "fontFamily": FONT}, "confine": True,
         "extraCssText": f"border-radius:12px;box-shadow:0 12px 30px {T.rgba(T.TOOLTIP, .35)};", "formatter": _js(fmt), "transitionDuration": 0.15}
    if trigger == "axis":
        t["axisPointer"] = {"type": "line", "lineStyle": {"width": 1, "color": T.rgba(T.CRIMSON_DARK, .30), "type": "solid"}}
    return t


_GERAK = "!window.matchMedia('(prefers-reduced-motion: reduce)').matches"


def _durasi() -> int:
    """Server selalu menggambar grafik langsung (0 ms). Animasi masuk (900 ms, cubicOut, jeda per batang/titik) dipasang oleh skrip
    app/motion.py tepat saat kartunya terlihat di layar; karena itu rerun akibat filter/klik tidak memutar ulang efek masuk."""
    return 0


def _tunda(per_item: int = 0) -> int:
    """Lihat _durasi(): jeda animasi diatur skrip app/motion.py saat grafik terlihat."""
    return 0


def _dasar(tinggi: int) -> dict:
    return {"backgroundColor": "transparent", "textStyle": {"fontFamily": FONT, "color": ui.NAVY, "fontSize": 12},
            "animation": True, "animationDuration": 0, "animationEasing": "cubicOut",
            "animationDurationUpdate": 450, "animationEasingUpdate": "cubicOut"}


def _n(v):
    """Angka → float JSON-aman (NaN/None → None)."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def _legenda(tampil: bool, **kw) -> dict:
    if not tampil:
        return {"show": False}
    return {"type": "scroll", "top": 0, "left": 0, "icon": "roundRect", "itemWidth": 11, "itemHeight": 11, "itemGap": 14,
            "textStyle": {"fontSize": 11, "color": ui.NAVY, "fontFamily": FONT}, **kw}


# --------------------------------------------------------------------------- #
# pemilihan lewat klik
# --------------------------------------------------------------------------- #
def terpilih(key: str):
    """Nama elemen yang sedang dipilih (hasil klik terakhir pada grafik `key`), atau None."""
    return st.session_state.get(f"ecsel_{key}")


def hapus_pilihan(key: str) -> None:
    st.session_state.pop(f"ecsel_{key}", None)


def tampil(opsi: dict, key: str, tinggi: int = 320, klik: bool = True):
    """Render grafik. Klik pada elemen memilih/membatalkan pilihan (klik lagi = batal) lalu rerun sekali agar tampilan menyesuaikan."""
    ev = {"click": "function(p){return {n:p.name,s:p.seriesName||'',t:Date.now()};}"} if klik else None
    r = st_echarts(options=opsi, events=ev, height=f"{tinggi}px", key=f"ec_{key}")
    if klik and isinstance(r, dict) and r.get("t") is not None and st.session_state.get(f"ect_{key}") != r["t"]:
        st.session_state[f"ect_{key}"] = r["t"]
        sekarang = st.session_state.get(f"ecsel_{key}")
        st.session_state[f"ecsel_{key}"] = None if sekarang == r.get("n") else r.get("n")
        st.rerun()
    return terpilih(key)


# --------------------------------------------------------------------------- #
# donat
# --------------------------------------------------------------------------- #
def donat(data: Sequence[tuple[str, float, str]], *, judul: str, sub: str = "", satuan: str = "", desimal: int = 0, pilih=None, tinggi: int = 300) -> dict:
    """Donat: irisan yang disorot/dipilih membesar, bergaris putih, berbayang. data = [(nama, nilai, warna)]."""
    items = []
    for n, v, w in data:
        it = {"name": n, "value": _n(v) or 0.0, "itemStyle": {"color": w}}
        if pilih is not None:
            it["selected"] = n == pilih
            if n != pilih:
                it["itemStyle"]["opacity"] = REDUP
        items.append(it)
    return {**_dasar(tinggi), "tooltip": _tooltip("item", satuan, desimal, persen=True),
            "legend": _legenda(True, top="auto", bottom=0, left="center", type="plain"),
            "title": {"text": judul, "subtext": sub, "left": "center", "top": "39%", "itemGap": 2,
                      "textStyle": {"fontSize": 24, "fontWeight": 700, "color": ui.NAVY, "fontFamily": FONT},
                      "subtextStyle": {"fontSize": 11, "color": ui.MUTED, "fontFamily": FONT}},
            "series": [{"type": "pie", "radius": ["50%", "74%"], "center": ["50%", "46%"], "avoidLabelOverlap": True,
                        "selectedMode": "single", "selectedOffset": 14, "minAngle": 2,
                        "itemStyle": {"borderColor": T.PUTIH, "borderWidth": 3, "borderRadius": 4},
                        "label": {"show": False}, "labelLine": {"show": False},
                        "emphasis": {"scale": True, "scaleSize": 12, "itemStyle": {"borderColor": T.PUTIH, "borderWidth": 3, "shadowBlur": 20, "shadowColor": BAYANGAN}},
                        "select": {"itemStyle": {"borderColor": T.PUTIH, "borderWidth": 3, "shadowBlur": 20, "shadowColor": BAYANGAN}},
                        "animationType": "expansion", "animationDuration": _durasi(), "animationDelay": _tunda(), "animationEasing": "cubicOut", "data": items}]}


# --------------------------------------------------------------------------- #
# batang
# --------------------------------------------------------------------------- #
def batang(kategori: Sequence[str], seri: Sequence[dict], *, horizontal: bool = False, satuan: str = "", desimal: int = 1, tinggi: int = 320,
           pilih=None, tumpuk: bool = False, judul_nilai: str = "", rentang: tuple | None = None, label: bool = False, garis: tuple | None = None,
           legenda: bool | None = None, putar_label: int = 0, redup_seri: Sequence[str] | None = None, label_item: Sequence[str | None] | None = None) -> dict:
    """Batang tunggal/kelompok/bertumpuk. seri = [{name, data, color, warna(list per batang, opsional)}].
    Batang yang disorot menebal & berbayang, lainnya meredup (focus self/series). `pilih` = kategori terpilih; `redup_seri` = seri yang diredupkan."""
    banyak = len(seri) > 1
    sr = []
    for i, s in enumerate(seri):
        wrn = s.get("warna")
        data = []
        for j, v in enumerate(s["data"]):
            it = {"value": _n(v)}
            c = wrn[j] if wrn else s.get("color")
            it["itemStyle"] = {"color": c}
            if pilih is not None and kategori[j] != pilih:
                it["itemStyle"]["opacity"] = REDUP
            if redup_seri and s["name"] in redup_seri:
                it["itemStyle"]["opacity"] = 0.25
            if label_item and i == 0 and j < len(label_item) and label_item[j]:
                it["label"] = {"show": True, "position": "right" if horizontal else "top", "formatter": label_item[j], "color": T.MAROON, "fontSize": 10, "fontWeight": 700}
            data.append(it)
        sr_i = {"type": "bar", "name": s["name"], "data": data, "barMaxWidth": 22 if horizontal else 34, "barGap": "12%",
                "itemStyle": {"borderRadius": ([0, 6, 6, 0] if horizontal else [6, 6, 0, 0]) if not tumpuk else 0, "color": s.get("color")},
                "emphasis": {"focus": "series" if banyak else "self", "itemStyle": {"shadowBlur": 16, "shadowColor": BAYANGAN, "shadowOffsetY": 3}},
                "blur": {"itemStyle": {"opacity": REDUP}},
                "animationDelay": _tunda(60), "animationDuration": _durasi(), "animationEasing": "cubicOut"}
        if tumpuk:
            sr_i["stack"] = "t"
        if label and not banyak:
            sr_i["label"] = {"show": True, "position": "right" if horizontal else "top", "fontSize": 10, "color": ui.NAVY,
                             "formatter": _js(f"function(p){{return Number(p.value).toLocaleString('id-ID',{{minimumFractionDigits:{desimal},maximumFractionDigits:{desimal}}});}}")}
        if garis and i == 0:
            nilai, teks = garis[0], garis[1]; wg = garis[2] if len(garis) > 2 else ui.NAVY
            sr_i["markLine"] = {"silent": True, "symbol": "none", "animation": False, "lineStyle": {"type": "dashed", "color": wg, "width": 1.2},
                                "label": {"formatter": teks, "color": wg, "fontSize": 10, "position": "start" if horizontal else "insideEndTop", "rotate": 0, "distance": [0, 2],
                                          "backgroundColor": T.rgba(T.PUTIH, .92), "padding": [2, 5], "borderRadius": 4},
                                "data": [{"xAxis": nilai} if horizontal else {"yAxis": nilai}]}
        sr.append(sr_i)
    kat = {"type": "category", "data": list(kategori), "axisTick": {"show": False}, "axisLine": {"lineStyle": {"color": ui.LINE}},
           "axisLabel": {"fontSize": 10, "color": ui.MUTED, "interval": 0, "rotate": putar_label}, "inverse": horizontal}
    nil = {"type": "value", "name": judul_nilai, "nameLocation": "middle", "nameGap": 30 if horizontal else 42, "nameTextStyle": {"color": ui.MUTED, "fontSize": 11},
           "splitLine": {"lineStyle": {"color": ui.LINE}}, "axisLabel": {"fontSize": 10, "color": ui.MUTED, "formatter": _js("function(v){return Number(v).toLocaleString('id-ID');}")}}
    if rentang:
        nil["min"], nil["max"] = rentang
    tampil_leg = (banyak or tumpuk) if legenda is None else legenda
    return {**_dasar(tinggi), "tooltip": _tooltip("axis" if (banyak or tumpuk) else "item", satuan, desimal) if (banyak or tumpuk) else _tooltip("item", satuan, desimal),
            "legend": _legenda(tampil_leg), "grid": {"left": 8, "right": 34 if label else 18, "top": 38 if tampil_leg else (30 if garis else 14), "bottom": 28 if judul_nilai else 8, "containLabel": True},
            ("yAxis" if horizontal else "xAxis"): kat, ("xAxis" if horizontal else "yAxis"): nil, "series": sr}


# --------------------------------------------------------------------------- #
# garis / area
# --------------------------------------------------------------------------- #
def garis(x: Sequence[str], seri: Sequence[dict], *, satuan: str = "", desimal: int = 1, tinggi: int = 320, judul_y: str | Sequence[str] = "",
          ambang: tuple | None = None, legenda: bool | None = None, log: bool = False, garis_x: tuple | None = None, legenda_lipat: bool = False) -> dict:
    """Garis/area. seri = [{name, data, color, area(bool), y(0/1), width}]. Titik membesar saat hover, garis berbayang, penunjuk sumbu tipis."""
    dua = any(s.get("y") == 1 for s in seri)
    sr = []
    for i, s in enumerate(seri):
        c = s["color"]
        it = {"type": "line", "name": s["name"], "data": [_n(v) for v in s["data"]], "smooth": 0.25, "showSymbol": False, "symbol": "circle", "symbolSize": 6,
              "yAxisIndex": s.get("y", 0), "connectNulls": False, "sampling": "lttb",
              "lineStyle": {"width": s.get("width", 2.6), "color": c, "shadowBlur": 8, "shadowColor": T.rgba(T.ROSE_DEEP, .18), "shadowOffsetY": 3},
              "itemStyle": {"color": c, "borderColor": T.PUTIH, "borderWidth": 2},
              "emphasis": {"focus": "series", "scale": 1.9, "lineStyle": {"width": s.get("width", 2.6) + 1.2}}, "blur": {"lineStyle": {"opacity": 0.25}},
              "animationDuration": _durasi(), "animationDelay": _tunda(), "animationEasing": "cubicOut"}
        if s.get("area"):
            it["areaStyle"] = {"color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1, "colorStops": [{"offset": 0, "color": T.AREA}, {"offset": 1, "color": T.rgba(T.PINK_SOFT, 0.0)}]}}
        if garis_x and i == 0:                      # garis tegak penanda kategori x yang dipilih (mis. jam dari peta panas)
            kx, tx = garis_x
            it["markLine"] = {"silent": True, "symbol": "none", "animation": False, "lineStyle": {"type": "solid", "color": ui.MUSTARD_D, "width": 2},
                              "label": {"formatter": tx, "color": ui.MUSTARD_D, "fontSize": 10, "fontWeight": 700, "position": "end"}, "data": [{"xAxis": kx}]}
        if ambang and i == 0:
            nilai, teks = ambang[0], ambang[1]; wa = ambang[2] if len(ambang) > 2 else ui.MUTED
            it["markLine"] = {"silent": True, "symbol": "none", "animation": False, "lineStyle": {"type": "dashed", "color": wa, "width": 1.2},
                              "label": {"formatter": teks, "color": wa, "fontSize": 10, "position": "insideStartTop"}, "data": [{"yAxis": nilai}]}
        sr.append(it)
    ys = [judul_y] if isinstance(judul_y, str) else list(judul_y)
    def sumbu_y(j: int) -> dict:
        d = {"type": "log" if log else "value", "name": ys[j] if j < len(ys) else "", "nameTextStyle": {"color": ui.MUTED, "fontSize": 11, "align": "left" if j == 0 else "right"},
             "splitLine": {"show": j == 0, "lineStyle": {"color": ui.LINE}}, "axisLabel": {"fontSize": 10, "color": ui.MUTED, "formatter": _js("function(v){return Number(v).toLocaleString('id-ID');}")}, "scale": j == 1}
        return d
    tampil_leg = len(seri) > 1 if legenda is None else legenda
    leg = {**_legenda(tampil_leg), "type": "plain"} if (legenda_lipat and tampil_leg) else _legenda(tampil_leg)
    return {**_dasar(tinggi), "tooltip": _tooltip("axis", satuan, desimal), "legend": leg,
            "grid": {"left": 8, "right": 12, "top": ((88 if legenda_lipat else 66) if any(ys) else 44) if tampil_leg else 30, "bottom": 8, "containLabel": True},
            "xAxis": {"type": "category", "data": list(x), "boundaryGap": False, "axisTick": {"show": False}, "axisLine": {"lineStyle": {"color": ui.LINE}},
                      "axisLabel": {"fontSize": 10, "color": ui.MUTED, "hideOverlap": True}},
            "yAxis": [sumbu_y(0), sumbu_y(1)] if dua else sumbu_y(0), "series": sr}


def _rgba(hex_: str, a: float) -> str:
    return T.rgba(hex_, a)


# --------------------------------------------------------------------------- #
# radar (pengganti Scatterpolar Plotly di Beranda)
# --------------------------------------------------------------------------- #
def radar(sumbu: Sequence[str], nilai: Sequence[float], *, warna_isi: str, warna_garis: str, tinggi: int = 250) -> dict:
    """Radar 0–1 berbentuk lingkaran; sumbu pertama di kanan lalu berlawanan arah jarum jam (sama dengan susunan Plotly sebelumnya).
    Tooltip: tiap sumbu = persen dari lokasi terburuk. Bentuk mengembang dari pusat saat halaman dibuka."""
    nama = json.dumps(list(sumbu))
    fmt = (f"function(p){{var n={nama};var h='';p.value.forEach(function(v,i){{h+='<div style=\"display:flex;gap:10px\"><span style=\"opacity:.85\">'+n[i]+'</span>"
           f"<b style=\"margin-left:auto\">'+Math.round(v*100)+'% dari lokasi terburuk</b></div>';}});return h;}}")
    tip = {**_tooltip("item", "", 0), "formatter": _js(fmt)}
    return {**_dasar(tinggi), "tooltip": tip,
            "radar": {"indicator": [{"name": s, "max": 1, "min": 0} for s in sumbu], "shape": "circle", "startAngle": 0, "radius": "70%", "center": ["50%", "50%"], "splitNumber": 5,
                      "name": {"textStyle": {"color": ui.NAVY, "fontSize": 10, "fontFamily": FONT}}, "nameGap": 8,
                      "splitLine": {"lineStyle": {"color": ui.LINE}}, "splitArea": {"show": False}, "axisLine": {"lineStyle": {"color": ui.LINE}}},
            "series": [{"type": "radar", "data": [{"value": [_n(v) or 0.0 for v in nilai], "name": "relatif"}], "symbol": "circle", "symbolSize": 6,
                        "lineStyle": {"color": warna_garis, "width": 2}, "itemStyle": {"color": warna_garis}, "areaStyle": {"color": warna_isi},
                        "emphasis": {"lineStyle": {"width": 3}}, "animationDuration": _durasi(), "animationDelay": _tunda(), "animationEasing": "cubicOut"}]}


# --------------------------------------------------------------------------- #
# batang berkelompok per tahun (Waktu rawan › kejadian kabut asap per bulan mulai)
# --------------------------------------------------------------------------- #
def batang_tahun(kategori: Sequence[str], seri: Sequence[dict], *, judul_y: str = "", tinggi: int = 340) -> dict:
    """Batang berkelompok: satu seri per tahun. seri = [{name, color, data: [{v, tip}]}] sejajar `kategori`.
    Angka di atas tiap batang; tooltip = teks `tip` per batang. Saat terlihat, batang tumbuh bergantian (app/motion.py)."""
    sr = []
    for s in seri:
        sr.append({"type": "bar", "name": s["name"], "barMaxWidth": 36, "barGap": "16%", "barCategoryGap": "32%",
                   "data": [{"value": _n(d["v"]), "tip": d["tip"]} for d in s["data"]],
                   "itemStyle": {"color": s["color"], "borderRadius": [6, 6, 0, 0]},
                   "label": {"show": True, "position": "top", "distance": 4, "fontSize": 11, "fontWeight": 700, "color": ui.NAVY, "fontFamily": FONT},
                   "emphasis": {"focus": "series", "itemStyle": {"shadowBlur": 16, "shadowColor": BAYANGAN, "shadowOffsetY": 3}},
                   "blur": {"itemStyle": {"opacity": REDUP}},
                   "animationDelay": _tunda(60), "animationDuration": _durasi(), "animationEasing": "cubicOut"})
    tip = "function(p){return (p.data&&p.data.tip)?p.data.tip:'';}"
    return {**_dasar(tinggi), "tooltip": {**_tooltip("item", "", 0), "formatter": _js(tip)}, "legend": {**_legenda(True), "type": "plain"},
            "grid": {"left": 30, "right": 12, "top": 44, "bottom": 8, "containLabel": True},
            "xAxis": {"type": "category", "data": list(kategori), "axisTick": {"show": False}, "axisLine": {"lineStyle": {"color": ui.LINE}},
                      "axisLabel": {"fontSize": 11, "color": ui.MUTED, "interval": 0}},
            "yAxis": {"type": "value", "minInterval": 1, "name": judul_y, "nameLocation": "middle", "nameGap": 30, "nameTextStyle": {"color": ui.MUTED, "fontSize": 11},
                      "splitLine": {"lineStyle": {"color": ui.LINE}}, "axisLabel": {"fontSize": 10, "color": ui.MUTED}},
            "series": sr}


# --------------------------------------------------------------------------- #
# rentang kepastian (galat) untuk garis dan batang
# --------------------------------------------------------------------------- #
def _galat_render(warna: str | None, k: int | None = None, n: int = 1, lebar: int = 4) -> str:
    """renderItem seri custom: garis tegak bawah–atas + tutup (±lebar px). k/n = posisi batang dalam kelompok (api.barLayout)."""
    geser = (f"var L=api.barLayout({{count:{n},barGap:'30%',barCategoryGap:'20%'}});var o=L[{k}].offsetCenter;" if k is not None else "var o=0;")
    c = f"'{warna}'" if warna else "api.visual('color')"   # warna dari pemanggil (theme.py)
    return ("function(params,api){" + geser + "var x=api.value(0),lo=api.coord([x,api.value(1)]),hi=api.coord([x,api.value(2)]);var px=lo[0]+o;"
            f"var st={{stroke:{c},lineWidth:1.5,opacity:api.value(3)}};"
            f"return {{type:'group',children:[{{type:'line',shape:{{x1:px,y1:lo[1],x2:px,y2:hi[1]}},style:st}},{{type:'line',shape:{{x1:px-{lebar},y1:lo[1],x2:px+{lebar},y2:lo[1]}},style:st}},"
            f"{{type:'line',shape:{{x1:px-{lebar},y1:hi[1],x2:px+{lebar},y2:hi[1]}},style:st}}]}};}}")


def garis_galat(x: Sequence[str], seri: Sequence[dict], *, satuan: str = "", desimal: int = 2, tinggi: int = 340, judul_x: str = "", judul_y: str = "", log: bool = False) -> dict:
    """Garis + titik dengan rentang kepastian. seri = [{name, data, color, bawah?, atas?, putus(bool)}]. Garis tergambar dari kiri ke kanan."""
    sr, nama_leg = [], []
    for s in seri:
        it = {"type": "line", "name": s["name"], "data": [_n(v) for v in s["data"]], "showSymbol": not s.get("putus"), "symbol": "circle", "symbolSize": 8,
              "lineStyle": {"width": 2 if s.get("putus") else 3, "color": s["color"], "type": "dashed" if s.get("putus") else "solid"}, "itemStyle": {"color": s["color"]},
              "emphasis": {"focus": "series"}, "z": 3, "animationDuration": _durasi(), "animationDelay": _tunda(), "animationEasing": "cubicOut"}
        sr.append(it); nama_leg.append(s["name"])
        if s.get("bawah") is not None:
            sr.append({"type": "custom", "name": s["name"], "renderItem": _js(_galat_render(None)), "itemStyle": {"color": s["color"]}, "tooltip": {"show": False}, "z": 2,
                       "data": [[i, _n(b), _n(a), 1] for i, (b, a) in enumerate(zip(s["bawah"], s["atas"]))], "encode": {"x": 0, "y": [1, 2]},
                       "animationDuration": _durasi(), "animationDelay": _tunda(), "animationEasing": "cubicOut"})
    sumbu_y = {"type": "log" if log else "value", "name": judul_y, "nameLocation": "middle", "nameGap": 40, "nameTextStyle": {"color": ui.MUTED, "fontSize": 11},
               "splitLine": {"lineStyle": {"color": ui.LINE}}, "axisLabel": {"fontSize": 10, "color": ui.MUTED, "formatter": _js("function(v){return Number(v).toLocaleString('id-ID');}")}}
    if log:
        nilai = [v for s in seri for k in ("data", "bawah", "atas") for v in (s.get(k) or []) if v is not None and v > 0]
        sumbu_y.update(logBase=2, min=round(min(nilai) * 0.85, 2) if nilai else None, max=round(max(nilai) * 1.25, 1) if nilai else None,
                       axisLabel={**sumbu_y["axisLabel"], "showMinLabel": False, "showMaxLabel": False}, minorTick={"show": False})
    return {**_dasar(tinggi), "tooltip": _tooltip("axis", satuan, desimal), "legend": {**_legenda(True), "type": "plain", "data": nama_leg},
            "grid": {"left": 40, "right": 14, "top": 62, "bottom": 30, "containLabel": True},
            "xAxis": {"type": "category", "data": list(x), "name": judul_x, "nameLocation": "middle", "nameGap": 30, "nameTextStyle": {"color": ui.MUTED, "fontSize": 11},
                      "axisTick": {"show": False}, "axisLine": {"lineStyle": {"color": ui.LINE}}, "axisLabel": {"fontSize": 10, "color": ui.MUTED, "interval": 0}},
            "yAxis": sumbu_y, "series": sr}


def batang_galat(kategori: Sequence[str], seri: Sequence[dict], *, penanda: Sequence[dict] = (), satuan: str = "", tinggi: int = 340, judul_x: str = "", judul_y: str = "",
                 pilih=None, ket_penanda: str = "") -> dict:
    """Batang berkelompok + rentang kepastian (garis gelap) + penanda belah ketupat per batang.
    seri = [{name, data, color, bawah, atas}]; penanda = [{data}] sejajar seri (nilai pembanding). `pilih` = kategori yang disorot (lainnya meredup)."""
    n = len(seri); sr = []
    op = [1.0 if (pilih is None or k == pilih) else 0.3 for k in kategori]
    for k, s in enumerate(seri):
        sr.append({"type": "bar", "name": s["name"], "barGap": "30%", "barCategoryGap": "20%",
                   "data": [{"value": _n(v), "itemStyle": {"color": s["color"], "opacity": op[j]}} for j, v in enumerate(s["data"])],
                   "itemStyle": {"color": s["color"], "borderRadius": [5, 5, 0, 0]}, "emphasis": {"focus": "series", "itemStyle": {"shadowBlur": 16, "shadowColor": BAYANGAN}},
                   "blur": {"itemStyle": {"opacity": REDUP}}, "animationDuration": _durasi(), "animationDelay": _tunda(60), "animationEasing": "cubicOut"})
        sr.append({"type": "custom", "name": s["name"], "renderItem": _js(_galat_render(T.JUDUL, k, n)), "tooltip": {"show": False}, "z": 3,
                   "data": [[j, _n(b), _n(a), op[j]] for j, (b, a) in enumerate(zip(s["bawah"], s["atas"]))], "encode": {"x": 0, "y": [1, 2]},
                   "animationDuration": _durasi(), "animationDelay": _tunda(60), "animationEasing": "cubicOut"})
        if k < len(penanda):
            ket = json.dumps(ket_penanda)
            sr.append({"type": "custom", "name": s["name"], "z": 4,
                       "renderItem": _js(f"function(params,api){{var L=api.barLayout({{count:{n},barGap:'30%',barCategoryGap:'20%'}});var c=api.coord([api.value(0),api.value(1)]);var x=c[0]+L[{k}].offsetCenter,y=c[1];"
                                          f"return {{type:'polygon',shape:{{points:[[x,y-6],[x+6,y],[x,y+6],[x-6,y]]}},style:{{fill:'{ui.NAVY}',opacity:api.value(2)}}}};}}"),
                       "tooltip": {**_tooltip("item", satuan, 0), "formatter": _js(f"function(p){{return '<div style=\"font-weight:700;margin-bottom:4px\">Rumah sakit di '+p.data.nama+'</div>'+Number(p.value[1]).toLocaleString('id-ID',{{maximumFractionDigits:0}})+' '+{ket};}}")},
                       "data": [{"value": [j, _n(v), op[j]], "nama": kategori[j]} for j, v in enumerate(penanda[k]["data"])], "encode": {"x": 0, "y": 1},
                       "animationDuration": _durasi(), "animationDelay": _tunda(60), "animationEasing": "cubicOut"})
    fmt_bar = (f"function(p){{return '<div style=\"font-weight:700;margin-bottom:4px\">'+p.seriesName+'</div>Rumah sakit di '+p.name+': <b>'"
               f"+Number(p.value).toLocaleString('id-ID',{{maximumFractionDigits:0}})+' {satuan}</b>';}}")
    return {**_dasar(tinggi), "tooltip": {**_tooltip("item", satuan, 0), "formatter": _js(fmt_bar)}, "legend": {**_legenda(True), "data": [s["name"] for s in seri]},
            "grid": {"left": 40, "right": 14, "top": 40, "bottom": 30, "containLabel": True},
            "xAxis": {"type": "category", "data": list(kategori), "name": judul_x, "nameLocation": "middle", "nameGap": 52 if len(kategori) > 6 else 30,
                      "nameTextStyle": {"color": ui.MUTED, "fontSize": 11}, "axisTick": {"show": False}, "axisLine": {"lineStyle": {"color": ui.LINE}},
                      "axisLabel": {"fontSize": 10, "color": ui.MUTED, "interval": 0, "rotate": 25 if len(kategori) > 6 else 0}},
            "yAxis": {"type": "value", "name": judul_y, "nameLocation": "middle", "nameGap": 42, "nameTextStyle": {"color": ui.MUTED, "fontSize": 11},
                      "splitLine": {"lineStyle": {"color": ui.LINE}}, "axisLabel": {"fontSize": 10, "color": ui.MUTED, "formatter": _js("function(v){return Number(v).toLocaleString('id-ID');}")}},
            "series": sr}


# --------------------------------------------------------------------------- #
# sumbu log ringan: nilai dipetakan ke log10 lalu diberi label angka asli (1 · 3 · 10 · 30 · 100 …), mirip sumbu log Plotly sebelumnya
# --------------------------------------------------------------------------- #
_LABEL_LOG = ("function(v){var x=Math.pow(10,v);var p=Math.pow(10,Math.floor(Math.log10(x)+1e-9));var r=Math.round(x/p)*p;"
              "return r.toLocaleString('id-ID',{maximumFractionDigits:2});}")


def _sumbu_log(vmin: float, vmax: float, pad: float = 0.02, **kw) -> dict:
    """Sumbu nilai pada skala log10, tanda tiap setengah dekade. Batas dibulatkan ke kelipatan 0,5 dekade (syarat ECharts agar tanda jatuh
    tepat di 1 · 3 · 10 · 30 …); label di kedua ujung disembunyikan sehingga label yang tampil sama dengan sumbu Plotly sebelumnya."""
    a = _math.floor((_math.log10(max(vmin, 1e-9)) - pad) * 2) / 2
    b = _math.ceil((_math.log10(max(vmax, 1e-9)) + pad) * 2) / 2
    return {"type": "value", "min": a, "max": b, "interval": 0.5, "splitLine": {"lineStyle": {"color": ui.LINE}},
            "axisLabel": {"fontSize": 10, "color": ui.MUTED, "formatter": _js(_LABEL_LOG), "showMinLabel": False, "showMaxLabel": False}, **kw}


def _log(v):
    v = _n(v)
    return None if v is None or v <= 0 else round(_math.log10(v), 5)


# --------------------------------------------------------------------------- #
# diagram sebar (pengganti scatter Plotly di Penyebab polusi)
# --------------------------------------------------------------------------- #
def sebar(kelompok: Sequence[tuple[str, str, list[dict]]], *, judul_x: str, judul_y: str, label_x: str, label_y: str, satuan_x: str = "", satuan_y: str = "µg/m³",
          log_x: bool = False, tinggi: int = 340) -> dict:
    """kelompok = [(nama_legenda, warna, [{x, y, nama}])]. Titik bulat 11 px; tooltip: nama daerah (tebal), kelompok, nilai y & x.
    Saat terlihat, titik membesar dari 0 bergantian (diatur app/motion.py)."""
    sr, xs = [], []
    for nama, warna, titik in kelompok:
        data = []
        for t in titik:
            x = _log(t["x"]) if log_x else _n(t["x"])
            xs.append(_n(t["x"]))
            data.append({"value": [x, _n(t["y"])], "nama": t["nama"], "xa": _n(t["x"])})
        sr.append({"type": "scatter", "name": nama, "data": data, "symbolSize": 11, "itemStyle": {"color": warna},
                   "emphasis": {"focus": "series", "scale": 1.4, "itemStyle": {"shadowBlur": 12, "shadowColor": BAYANGAN}}})
    fmt = (f"function(p){{var d=p.data;var f=function(v,n){{return Number(v).toLocaleString('id-ID',{{maximumFractionDigits:n}});}};"
           f"return '<div style=\"font-weight:700;margin-bottom:4px\">'+d.nama+'</div>'+p.seriesName+'<br>{label_y}: '+f(d.value[1],1)+' {satuan_y}<br>{label_x}: '+f(d.xa,0){(chr(43) + repr(' ' + satuan_x)) if satuan_x else ''};}}")
    xs = [v for v in xs if v is not None and v > 0]
    sumbu_x = (_sumbu_log(min(xs), max(xs)) if (log_x and xs) else
               {"type": "value", "scale": True, "splitNumber": 3, "splitLine": {"lineStyle": {"color": ui.LINE}}, "axisLabel": {"fontSize": 10, "color": ui.MUTED, "formatter": _js("function(v){return Number(v).toLocaleString('id-ID');}")}})
    sumbu_x.update(name=judul_x, nameLocation="middle", nameGap=30, nameTextStyle={"color": ui.MUTED, "fontSize": 12})
    return {**_dasar(tinggi), "tooltip": {**_tooltip("item", satuan_y, 1), "formatter": _js(fmt)}, "legend": {**_legenda(True), "type": "plain"},
            "grid": {"left": 40, "right": 16, "top": 62, "bottom": 34, "containLabel": True}, "xAxis": sumbu_x,
            "yAxis": {"type": "value", "scale": True, "splitNumber": 3, "name": judul_y, "nameLocation": "middle", "nameGap": 40, "nameTextStyle": {"color": ui.MUTED, "fontSize": 12},
                      "splitLine": {"lineStyle": {"color": ui.LINE}}, "axisLabel": {"fontSize": 10, "color": ui.MUTED, "formatter": _js("function(v){return Number(v).toLocaleString('id-ID');}")}},
            "series": sr}


# --------------------------------------------------------------------------- #
# boxplot (pengganti boxplot Plotly di Kondisi udara)
# --------------------------------------------------------------------------- #
def kotak(kelompok: Sequence[tuple[str, str, Sequence[float]]], *, judul_y: str = "µg/m³", satuan: str = "µg/m³", tinggi: int = 340) -> dict:
    """kelompok = [(nama, warna, [min, Q1, median, Q3, maks])] — statistik sudah diringkas di server (5 angka per kelompok).
    Satu seri boxplot per jenis wilayah (nama = legenda, warna seri = warna jenis wilayah: isi 55%, tepi/kumis/median warna penuh 1,8 px),
    sehingga warna tetap ada setelah efek masuk dan klik legenda menyembunyikan/menampilkan kotak yang benar. Tiap seri hanya berisi kotaknya
    sendiri (kategori lain kosong) dan memakai sumbu kategori sendiri (tersembunyi, isi sama) agar kotak tetap di tengah kategori."""
    nama = [k[0] for k in kelompok]
    asli = json.dumps({n: [_n(v) for v in st] for n, _, st in kelompok})
    semua = [v for _, _, st in kelompok for v in st if v and v > 0]
    fmt = (f"function(p){{var A={asli};var a=A[p.seriesName];if(!a)return '';var f=function(v){{return Number(v).toLocaleString('id-ID',{{maximumFractionDigits:1}});}};"
           "var L=['Nilai terendah','Kuartil bawah','Nilai tengah','Kuartil atas','Nilai tertinggi'];"
           "var h='<div style=\"display:flex;align-items:center;gap:6px;font-weight:700;margin-bottom:4px\">'+p.marker+p.seriesName+'</div>';"
           "for(var i=0;i<5;i++){h+='<div style=\"display:flex;gap:14px\"><span style=\"opacity:.85\">'+L[i]+'</span><b style=\"margin-left:auto\">'+f(a[i])+'"
           f" {satuan}</b></div>';}}return h;}}")
    sumbu_kat = {"type": "category", "data": nama, "axisTick": {"show": False}, "axisLine": {"lineStyle": {"color": ui.LINE}}, "axisLabel": {"fontSize": 11, "color": ui.MUTED}}
    sr = []
    for i, (n, w, st) in enumerate(kelompok):
        sr.append({"type": "boxplot", "name": n, "xAxisIndex": i, "data": [[_log(v) for v in st] if j == i else ["-"] * 5 for j in range(len(kelompok))],
                   "boxWidth": ["30%", "56%"], "itemStyle": {"color": _rgba(w, 0.55), "borderColor": w, "borderWidth": 1.8},
                   "emphasis": {"itemStyle": {"color": _rgba(w, 0.72), "borderColor": w, "borderWidth": 2.2, "shadowBlur": 12, "shadowColor": BAYANGAN}}})
    return {**_dasar(tinggi), "tooltip": {**_tooltip("item", satuan, 1), "formatter": _js(fmt)},
            "legend": {**_legenda(True), "type": "plain", "icon": "roundRect", "data": nama},
            "grid": {"left": 40, "right": 16, "top": 40, "bottom": 8, "containLabel": True},
            "xAxis": [sumbu_kat] + [{**sumbu_kat, "show": False} for _ in kelompok[1:]],
            "yAxis": _sumbu_log(min(semua), max(semua), name=judul_y, nameLocation="middle", nameGap=40, nameTextStyle={"color": ui.MUTED, "fontSize": 12}) if semua else {"type": "value"},
            "series": sr}


# --------------------------------------------------------------------------- #
# peta panas jam × bulan (Waktu rawan)
# --------------------------------------------------------------------------- #
def peta_panas(x: Sequence[str], y: Sequence[str], sel: Sequence[dict], *, warna: Sequence[str], teks_skala: tuple[str, str], label_atas: Sequence[str | None] = (),
               pita: Sequence[tuple[int, int, str]] = (), tinggi: int = 480, judul_y: str = "") -> dict:
    """sel = [{x, y, v, nama, tip, op}] (indeks kolom/baris, nilai, nama unik untuk klik, teks tooltip siap pakai, opasitas sorotan).
    label_atas = penanda di atas tiap kolom (mis. "🔥 3" untuk bulan dengan kejadian kabut asap); pita = [(baris_awal, baris_akhir, label)]
    untuk menandai baris jam sibuk (label sumbu jam berpenanda mustard). Warna gradasi kontinu `warna` dari nilai terendah ke tertinggi."""
    nilai = [s["v"] for s in sel if s["v"] is not None]
    data = [{"value": [s["x"], s["y"], _n(s["v"]) if s["v"] is not None else "-"], "name": s["nama"], "tip": s["tip"], "itemStyle": {"opacity": s.get("op", 1.0)}} for s in sel]
    lab = json.dumps([v or "" for v in label_atas] + [""] * (len(x) - len(label_atas)))
    seri = {"type": "heatmap", "name": "peta panas", "data": data, "itemStyle": {"borderColor": T.PUTIH, "borderWidth": 1.5, "borderRadius": 3},
            "emphasis": {"itemStyle": {"borderColor": ui.NAVY, "borderWidth": 2, "shadowBlur": 10, "shadowColor": BAYANGAN}}}
    # jam sibuk: label sumbu jam diberi penanda mustard (pil kecil) pada baris-baris itu; label lain tampil tiap 3 jam
    sibuk = sorted({j for a, b, _ in pita for j in range(a, b + 1)})
    fmt_y = (f"function(v,i){{var S={json.dumps(sibuk)};if(S.indexOf(i)>=0)return '{{b|'+v+'}}';return i%3===0?v:'';}}")
    return {**_dasar(tinggi), "tooltip": {**_tooltip("item", "", 1), "formatter": _js("function(p){return p.data.tip;}")},
            "grid": {"left": 34, "right": 78, "top": 40, "bottom": 10, "containLabel": True},
            "xAxis": [{"type": "category", "data": list(x), "position": "bottom", "splitArea": {"show": False}, "axisTick": {"show": False}, "axisLine": {"show": False},
                       "axisLabel": {"fontSize": 11, "color": ui.MUTED}},
                      {"type": "category", "data": list(x), "position": "top", "axisTick": {"show": False}, "axisLine": {"show": False},
                       "axisLabel": {"interval": 0, "formatter": _js(f"function(v,i){{var L={lab};return L[i]?'{{a|'+L[i]+'}}':'';}}"),
                                     "rich": {"a": {"backgroundColor": T.BLUSH, "color": T.MAROON, "borderRadius": 8, "padding": [2, 6], "fontSize": 10, "fontWeight": 700}}}}],
            "yAxis": [{"type": "category", "data": list(y), "inverse": True, "name": judul_y, "nameLocation": "middle", "nameGap": 52, "nameTextStyle": {"color": ui.MUTED, "fontSize": 11},
                       "axisTick": {"show": False}, "axisLine": {"show": False},
                       "axisLabel": {"fontSize": 10, "color": ui.MUTED, "interval": 0, "formatter": _js(fmt_y),
                                     "rich": {"b": {"color": T.MAROON, "fontWeight": 700, "fontSize": 10, "backgroundColor": T.BLUSH, "borderRadius": 4, "padding": [1, 4]}}}}],
            "visualMap": {"type": "continuous", "min": min(nilai) if nilai else 0, "max": max(nilai) if nilai else 1, "dimension": 2, "calculable": False, "orient": "vertical",
                          "right": 4, "top": "middle", "itemWidth": 12, "itemHeight": 180, "text": list(teks_skala), "textStyle": {"fontSize": 10, "color": ui.MUTED},
                          "inRange": {"color": list(warna)}},
            "series": [seri]}


# --------------------------------------------------------------------------- #
# matriks kekuatan hubungan (pengganti heatmap Plotly di Penyebab polusi › cuaca)
# --------------------------------------------------------------------------- #
def matriks(kolom: Sequence[str], baris: Sequence[str], nilai: Sequence[Sequence[float]], teks: Sequence[Sequence[str]], *, tinggi: int = 340) -> dict:
    """Kotak-kotak berwarna: nilai −1…+1 (biru kehijauan = berlawanan, merah = searah, putih = tidak ada hubungan); tiap kotak diberi kata (Lemah/Sedang/Kuat)."""
    def _label(v):
        return {"color": T.teks_di_atas(T.skala(T.KORELASI, (v + 1) / 2)) if _n(v) is not None else ui.NAVY}
    data = [{"value": [j, i, _n(v) if _n(v) is not None else "-"], "kata": teks[i][j], "label": _label(v)} for i, r in enumerate(nilai) for j, v in enumerate(r)]
    fmt_label = "function(p){return p.data.kata;}"
    fmt_tip = (f"function(p){{var K={json.dumps(list(kolom))},B={json.dumps(list(baris))};var v=p.value[2];"
               "return '<div style=\"font-weight:700;margin-bottom:4px\">'+B[p.value[1]]+' dan '+K[p.value[0]]+'</div>Hubungan '+p.data.kata.toLowerCase()+"
               "' (angka: <b>'+(v==='-'?'–':Number(v).toLocaleString('id-ID',{minimumFractionDigits:2,maximumFractionDigits:2}))+'</b>)';}")
    return {**_dasar(tinggi), "tooltip": {**_tooltip("item", "", 2), "formatter": _js(fmt_tip)},
            "grid": {"left": 8, "right": 96, "top": 10, "bottom": 8, "containLabel": True},
            "xAxis": {"type": "category", "data": list(kolom), "splitArea": {"show": False}, "axisTick": {"show": False}, "axisLine": {"show": False}, "axisLabel": {"fontSize": 11, "color": ui.MUTED}},
            "yAxis": {"type": "category", "data": list(baris), "inverse": True, "axisTick": {"show": False}, "axisLine": {"show": False}, "axisLabel": {"fontSize": 11, "color": ui.MUTED}},
            "visualMap": {"type": "continuous", "min": -1, "max": 1, "dimension": 2, "calculable": False, "orient": "vertical", "right": 4, "top": "middle", "itemWidth": 12, "itemHeight": 170,
                          "text": ["searah", "berlawanan"], "textStyle": {"fontSize": 10, "color": ui.MUTED}, "inRange": {"color": list(T.KORELASI)}},
            "series": [{"type": "heatmap", "name": "hubungan", "data": data, "itemStyle": {"borderColor": T.PUTIH, "borderWidth": 2, "borderRadius": 4},
                        "label": {"show": True, "formatter": _js(fmt_label), "fontSize": 11, "color": ui.NAVY},
                        "emphasis": {"itemStyle": {"borderColor": ui.NAVY, "borderWidth": 2, "shadowBlur": 10, "shadowColor": BAYANGAN}}}]}
