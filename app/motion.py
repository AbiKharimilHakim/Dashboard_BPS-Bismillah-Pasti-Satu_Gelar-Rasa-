"""Efek masuk (entrance animation) seluruh dashboard — satu tempat untuk CSS dan skrip animasi.

Hanya menambah gerak; data, teks, warna, ukuran, dan susunan tidak berubah. Peta 3D (Beranda & Lokasi pengukuran) dikecualikan.

Cara kerja (skrip JS di bawah, dipasang lewat ui.inject_js dalam satu iframe tak terlihat):
  * Kartu dianimasikan saat TERLIHAT di layar (IntersectionObserver, ≥30% kartu tampak), bukan saat halaman dimuat; kartu di bawah
    layar baru disembunyikan sesaat sebelum masuk layar (±150 px) dan masuk ketika digulir.
  * Kartu yang masuk bersamaan diurutkan atas→bawah, kiri→kanan dengan jeda 70 ms, maksimal 8 kartu bergantian; sisanya bersama.
  * Animasi hanya opacity + transform (tanpa blur, ringan); will-change hanya selama animasi (kelas dilepas di akhir).
  * Grafik ECharts di kartu itu diputar ulang dari nol saat terlihat (900 ms, cubicOut; batang bergantian idx×60 ms, titik scatter
    idx×25 ms). Server selalu mengirim grafik tanpa animasi, jadi rerun karena filter/klik tidak memutar ulang efek masuk.
  * Sparkline (SVG) digambar dari kiri dan angka KPI menghitung naik saat kartunya masuk.
  * Ditandai selesai per kunci kartu dalam satu halaman: kartu yang dibuat ulang oleh rerun filter tidak beranimasi lagi.
  * Satu set observer per halaman; salinan skrip lama memutus observernya sendiri (tidak menumpuk setiap rerun).
  * Bila skrip gagal, tidak ada yang tersembunyi: kelas "masuk-tunggu" punya pengaman CSS yang menampilkan kartu setelah 3 dtk.
"""
from __future__ import annotations

import streamlit as st

_HAL, _MASUK = "_m_hal", "_m_masuk"
EASE = "cubic-bezier(.2,.8,.2,1)"


def siapkan(slug: str) -> bool:
    """Panggil sekali per eksekusi. True bila halaman baru dibuka; False bila hanya filter/klik (dipakai untuk pemeriksaan)."""
    ss = st.session_state
    masuk = ss.get(_HAL, None) != slug
    ss[_HAL] = slug
    ss[_MASUK] = masuk
    return masuk


def aktif() -> bool:
    try:
        return bool(st.session_state.get(_MASUK, False))
    except Exception:
        return False


CSS = f"""
/* ===== efek masuk (kelas dipasang skrip app/motion.py; tanpa skrip tidak ada yang berubah). Hanya opacity + transform. ===== */
@keyframes mHeader{{from{{opacity:0;transform:translateY(12px);}}}}
@keyframes mKartu{{from{{opacity:0;transform:translateY(16px) scale(.98);}}}}
@keyframes mArea{{from{{opacity:0;}}}}
@keyframes mBusur{{from{{stroke-dashoffset:100;}}}}
@keyframes mTitik{{from{{transform:rotate(0deg);}}}}
@keyframes mPil{{from{{opacity:0;transform:translateX(14px);}}}}
@keyframes mGaris{{from{{stroke-dashoffset:1;}}}}
@keyframes mPudar{{from{{opacity:0;}}}}
@keyframes mPengaman{{to{{opacity:1;}}}}
@keyframes mSapu{{from{{clip-path:inset(0 100% 0 0);}}to{{clip-path:inset(0 0 0 0);}}}}
.masuk-hdr{{animation:mHeader .4s {EASE} backwards;will-change:transform,opacity;}}
.masuk-hdr .hb-g .va{{animation:mBusur .8s {EASE} .3s backwards;}}
.masuk-hdr .hb-g .mk{{animation:mTitik .8s {EASE} .3s backwards;}}
.masuk-kartu{{animation:mKartu .45s {EASE} backwards !important;will-change:transform,opacity;}}
.masuk-area{{animation:mArea .4s {EASE} backwards;}}
.masuk-pil{{animation:mPil .35s {EASE} backwards;}}
.masuk-sapu iframe[title*="echarts"]{{animation:mSapu .9s cubic-bezier(.33,1,.68,1) .12s backwards;}}
/* grafik di kartu yang baru masuk: disembunyikan sebentar lalu tumbuh dari nol (maks. 0,9 dtk setelah grafik siap, lihat JS; pengaman CSS 9 dtk) */
.masuk-grafik-tunda iframe[title*="echarts"]{{opacity:0;animation:mPengaman .01s linear 9s forwards;}}
.masuk-gambar svg.spark polyline{{stroke-dasharray:1;animation:mGaris .9s cubic-bezier(.33,1,.68,1) .15s backwards;}}
.masuk-gambar svg.spark polygon{{animation:mPudar .9s ease-out .25s backwards;}}
/* menunggu masuk layar / isi kartu siap: tersembunyi, tetapi pasti tampil lagi setelah 3 dtk walau skrip berhenti */
.masuk-tunggu{{opacity:0;animation:mPengaman .01s linear 3s forwards;}}
.rm-note{{display:none;}}
@media (prefers-reduced-motion: reduce){{
  .masuk-hdr,.masuk-hdr .hb-g .va,.masuk-hdr .hb-g .mk,.masuk-kartu,.masuk-area,.masuk-pil,.masuk-gambar svg.spark *,.masuk-sapu iframe{{animation:none !important;}}
  .masuk-tunggu{{opacity:1 !important;animation:none !important;}}
  .rm-note{{display:block;font-size:.66rem;opacity:.75;margin:.4rem .2rem 0;line-height:1.35;}}
}}
"""

JS = r"""
(function(){
  var P = window.parent; if (!P || !P.IntersectionObserver) return;
  // iframe skrip ini bisa dibuat ulang Streamlit; salinan terbaru mengambil alih, salinan lama memutus observernya.
  var GEN = P.__masukGen = (P.__masukGen || 0) + 1;
  (P.__masukObs || []).forEach(function(o){ try { o.disconnect(); } catch (e) {} });
  (P.__masukTimer || []).forEach(function(t){ P.clearInterval(t); });
  P.__masukObs = []; P.__masukTimer = [];
  var D = P.document, rm = P.matchMedia('(prefers-reduced-motion: reduce)');
  var SLUG = {'':0,'kondisi-udara':1,'waktu-rawan':2,'penyebab-polusi':3,'dampak-kesehatan':4,'lokasi-pengukuran':5};
  var PETA = '.st-key-kartu_p0_peta,.st-key-kartu_p5_peta';
  var S = P.__masukS = P.__masukS || {path:null, hal:0, tok:0, selesai:{}, antre:0, t0:0, mutasi:0};
  var RE = /^(\s*)([+\-–]?)(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?/;
  function hidup(){ return GEN === P.__masukGen; }
  function now(){ return P.performance.now(); }
  function halIni(){ var s = P.location.pathname.replace(/\/+$/,'').split('/').pop() || ''; return (s in SLUG) ? SLUG[s] : 0; }
  function putar(el, kelas){ el.classList.remove(kelas); void el.offsetWidth; el.classList.add(kelas);
    el.addEventListener('animationend', function f(e){ if (e.target === el){ el.classList.remove(kelas); el.removeEventListener('animationend', f); } }); }

  /* ---- hitung naik: [data-countup] (+ angka kartu kabut asap di Beranda) ---- */
  var SEL_ANGKA = '[data-countup], .st-key-asap_link a p strong';
  function teks(el){ var w = D.createTreeWalker(el, 4), n; while ((n = w.nextNode())) { if (/\d/.test(n.nodeValue) && RE.test(n.nodeValue)) return n; } return null; }
  function fmt(v, des, grup){ return v.toLocaleString('id-ID', {minimumFractionDigits:des, maximumFractionDigits:des, useGrouping:grup}); }
  function angkaDi(root){ var a = [].slice.call(root.querySelectorAll(SEL_ANGKA)); if (root.matches && root.matches('[data-countup]')) a.push(root); return a; }
  function siapkanAngka(root){
    angkaDi(root).forEach(function(e){
      if (e.__cu === S.tok) return; var n = teks(e); if (!n) return;
      var asli = n.nodeValue, m = asli.match(RE), des = m[4] ? m[4].length : 0, grup = m[3].indexOf('.') >= 0;
      var akhir = parseFloat(m[3].replace(/\./g,'') + (m[4] ? '.' + m[4] : '')); if (!isFinite(akhir)) return;
      e.__cu = S.tok; var depan = m[1] + m[2], ekor = asli.slice(m[0].length), tulis = depan + fmt(0, des, grup) + ekor;
      n.nodeValue = tulis;
      e.__mulaiAngka = function(tunda){
        var t0 = now() + tunda, dur = 900;
        (function langkah(){ if (n.nodeValue !== tulis) return;            // diubah Streamlit (rerun) → berhenti tanpa menimpa
          var u = Math.min(1, Math.max(0, (now() - t0) / dur));
          if (u >= 1) { n.nodeValue = asli; return; }
          tulis = depan + fmt(akhir * (1 - Math.pow(1 - u, 3)), des, grup) + ekor; n.nodeValue = tulis; P.requestAnimationFrame(langkah); })();
      };
    });
  }
  function mulaiAngka(root, tunda){ angkaDi(root).forEach(function(e){ if (e.__mulaiAngka) { var f = e.__mulaiAngka; e.__mulaiAngka = null; f(tunda); } }); }

  /* ---- grafik ECharts: putar ulang animasi masuk saat kartunya terlihat ---- */
  function instanceGrafik(fr){
    try {
      var div = fr.contentWindow.document.querySelector('[_echarts_instance_]'), node = div;
      for (var up = 0; up < 6 && node; up++, node = node.parentElement) {
        var kunci = Object.keys(node).filter(function(x){ return x.indexOf('__reactFiber') === 0 || x.indexOf('__reactInternalInstance') === 0; })[0];
        for (var f = kunci ? node[kunci] : null; f; f = f.return) { if (f.stateNode && typeof f.stateNode.getEchartsInstance === 'function') return f.stateNode.getEchartsInstance(); }
      }
    } catch (e) {}
    return null;
  }
  function jeda(per){ return function(i){ return 120 + Math.min(i * per, 300); }; }
  function ulang(inst){
    try {
      var o = inst.getOption();
      (o.series || []).forEach(function(s){
        var per = (s.type === 'bar' || s.type === 'custom') ? 60 : (s.type === 'scatter' ? 25 : 0);
        s.animation = true; s.animationDuration = 900; s.animationEasing = 'cubicOut'; s.animationDelay = per ? jeda(per) : 120;
      });
      o.animation = true;
      inst.clear();
      P.setTimeout(function(){ try { if (!inst.isDisposed()) inst.setOption(o, true); } catch (e) {} }, 60);
    } catch (e) {}
  }
  /* Grafik di kartu yang masuk disembunyikan sebentar (maks. 1,2 dtk), lalu diputar ulang dari nol saat halaman TENANG: tidak ada
     perubahan DOM ≥ 300 ms, tidak ada tugas berat (long task) ≥ 250 ms, dan bingkai lancar ≥ 300 ms. Selama halaman dimuat Streamlit
     mengirim ulang data ke iframe grafik (gambar ulang instan) dan thread utama/GPU sibuk, sehingga animasi yang dimulai saat itu
     tertimpa atau bingkainya terlewat. Grafik yang sudah selesai dimuat paling lama menunggu 0,9 dtk, lalu tetap diputar (mungkin
     kurang mulus). Grafik yang belum selesai dimuat memang belum tampak (iframe setinggi 0), jadi menunggunya tidak mengosongkan apa pun. Daftar tunggu disimpan di window induk agar tetap diproses walau iframe skrip ini dibuat ulang. */
  if (!S.tertunda) S.tertunda = [];
  var pantau = false;
  function pantauBingkai(){ if (pantau) return; pantau = true; var lalu = now();          // jeda bingkai > 60 ms = peramban/GPU sibuk
    (function f(){ var t = now(); if (t - lalu > 60) S.sendat = t; lalu = t; if (S.tertunda.length && hidup()) P.requestAnimationFrame(f); else pantau = false; })(); }
  function putarGrafik(k){
    if (!k.querySelector('iframe[title*="echarts"]')) return;
    k.classList.add('masuk-grafik-tunda'); S.tertunda.push({k: k, t: now()});
    pantauBingkai(); cekTertunda();
  }
  function cekTertunda(){
    var t = now(), tenang = t - (S.mutasi || 0) > 300 && t - (S.panjang || 0) > 250 && t - (S.sendat || 0) > 300;
    S.tertunda = S.tertunda.filter(function(p){
      var k = p.k; if (!k.isConnected) return false;
      var fr = [].slice.call(k.querySelectorAll('iframe[title*="echarts"]'));
      var inst = fr.map(function(f){ return f.getBoundingClientRect().height >= 5 && instanceGrafik(f); });
      var semua = fr.length && inst.every(Boolean);
      if (semua && !p.siap) p.siap = t;                                  // saat grafik selesai dimuat (sebelumnya tingginya 0, jadi menyembunyikannya tidak terlihat)
      if (semua && (tenang || t - p.siap > 900)) {
        // peta panas ECharts tidak punya animasi masuk sendiri: iframe-nya disapu terbuka dari kiri ke kanan (CSS clip-path). Diperiksa SEBELUM ulang() mengosongkan grafik.
        var panas = inst.some(function(i){ try { return i.getOption().series.some(function(s){ return s.type === 'heatmap'; }); } catch (e) { return false; } });
        inst.forEach(ulang);
        if (panas) {
          k.classList.remove('masuk-sapu'); void k.offsetWidth; k.classList.add('masuk-sapu'); P.setTimeout(function(){ k.classList.remove('masuk-sapu'); }, 1300); } P.setTimeout(function(){ k.classList.remove('masuk-grafik-tunda'); }, 30); return false; }
      if (t - p.t > 8000) { k.classList.remove('masuk-grafik-tunda'); return false; }      // grafik tidak juga siap: tampilkan apa adanya
      return true;
    });
  }  function siap(k){
    if ([].slice.call(k.querySelectorAll('iframe[title*="echarts"]')).some(function(f){ return f.getBoundingClientRect().height < 5; })) return false;
    var plot = k.querySelector('[data-testid="stPlotlyChart"]');
    return !(plot && !plot.querySelector('.main-svg'));
  }

  /* ---- kartu ---- */
  function kunci(k){ var c = [].slice.call(k.classList).filter(function(x){ return x.indexOf('st-key-') === 0; })[0]; return c || (k.classList.contains('card-teal') ? 'card-teal' : ''); }
  function daftarKartu(){
    var s = '[class*="st-key-kartu_p' + S.hal + '_"]'; if (S.hal === 0) s += ',.card-teal,.st-key-asap_link';
    return [].slice.call(D.querySelectorAll(s)).filter(function(k){ return !k.matches(PETA) && !k.closest(PETA) && !k.parentElement.closest('[class*="st-key-kartu"]'); });
  }
  function selesai(k){ return S.selesai[kunci(k)] === S.tok; }
  function sembunyikan(k){ if (k.__tunggu === S.tok || selesai(k)) return; k.__tunggu = S.tok; k.__t = now(); k.classList.add('masuk-tunggu'); siapkanAngka(k); }
  function masukkan(k, tunda){
    S.selesai[kunci(k)] = S.tok;
    P.setTimeout(function(){
      if (!k.isConnected) return;
      if (now() - k.__t > 2900) { k.classList.remove('masuk-tunggu'); mulaiAngka(k, 0); putarGrafik(k); return; }    // sudah ditampilkan pengaman CSS: kartu tidak dianimasikan lagi, grafiknya tetap tumbuh
      putarGrafik(k); k.classList.remove('masuk-tunggu'); putar(k, 'masuk-kartu'); mulaiAngka(k, 60);
      k.classList.add('masuk-gambar'); P.setTimeout(function(){ k.classList.remove('masuk-gambar'); }, 1400);
    }, tunda);
  }
  if (!S.antrean) S.antrean = [];          // kartu yang sudah terlihat tetapi isinya (grafik) belum siap
  function jadwalkan(daftar){
    daftar.sort(function(a, b){ var ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect(); return (Math.round(ra.top / 40) - Math.round(rb.top / 40)) || (ra.left - rb.left); });
    var t = now(); if (S.antre < t) S.antre = t; var i = 0;
    daftar.forEach(function(k){ masukkan(k, Math.max(0, S.antre - t) + Math.min(i, 7) * 70); i++; });
    S.antre = t + Math.min(i, 8) * 70;
  }
  var ioDekat = new P.IntersectionObserver(function(es){ if (!hidup() || rm.matches) return;
    es.forEach(function(e){ if (e.isIntersecting) sembunyikan(e.target); }); }, {rootMargin: '0px 0px 150px 0px', threshold: 0});
  var ioLihat = new P.IntersectionObserver(function(es){ if (!hidup() || rm.matches) return;
    var siapKini = [];
    es.forEach(function(e){ var k = e.target; if (!e.isIntersecting || selesai(k)) return; sembunyikan(k);
      if (siap(k)) siapKini.push(k); else if (S.antrean.indexOf(k) < 0) S.antrean.push(k); });
    if (siapKini.length) jadwalkan(siapKini);
  }, {threshold: 0.3});
  P.__masukObs.push(ioDekat, ioLihat);

  function periksa(){
    if (!hidup()) return;
    var path = P.location.pathname;
    if (path !== S.path) { S.path = path; S.hal = halIni(); S.tok++; S.selesai = {}; S.antre = 0; S.t0 = now(); S.antrean = []; S.tertunda = []; }
    if (rm.matches) return;
    var hdr = D.querySelector('.hbw[data-hal="' + S.hal + '"]');
    if (hdr && hdr.__tok !== S.tok && now() - S.t0 < 4000) { hdr.__tok = S.tok; putar(hdr, 'masuk-hdr'); siapkanAngka(hdr); mulaiAngka(hdr, 100);
      var pil = D.querySelector('.st-key-nav_active'); if (pil) putar(pil, 'masuk-pil'); }
    daftarKartu().forEach(function(k){ if (k.__obs === S.tok || selesai(k)) return; k.__obs = S.tok; ioDekat.observe(k); ioLihat.observe(k); });
    // kartu terlihat yang menunggu grafiknya: masuk begitu siap (maks. 1,5 dtk menunggu)
    if (S.antrean.length) {
      var lanjut = S.antrean.filter(function(k){ return k.isConnected && !selesai(k) && (siap(k) || now() - k.__t > 1500); });
      S.antrean = S.antrean.filter(function(k){ return lanjut.indexOf(k) < 0 && k.isConnected && !selesai(k); });
      if (lanjut.length) jadwalkan(lanjut);
    }
    if (S.tertunda.length) cekTertunda();
    // blok konten lain di layar (bar tab, chip) saat halaman dibuka — opacity saja
    if (now() - S.t0 < 3000) {
      var akar = D.querySelector('[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"]');
      if (akar) [].slice.call(akar.children).forEach(function(b){
        if (b.__tok === S.tok || !b.offsetHeight || b.querySelector('.hbw,iframe[title*="peta3d"],[class*="st-key-kartu"],.card-teal,' + PETA)) return;
        b.__tok = S.tok; putar(b, 'masuk-area');
      });
    }
  }
  // catat tugas berat terakhir (mis. iframe lain sedang memuat pustakanya) agar grafik tidak diputar saat thread utama sibuk
  try { var po = new P.PerformanceObserver(function(l){ l.getEntries().forEach(function(e){ S.panjang = Math.max(S.panjang || 0, e.startTime + e.duration); }); }); po.observe({type: 'longtask', buffered: false}); P.__masukObs.push(po); } catch (e) {}
  var jadwal = false;
  var mo = new P.MutationObserver(function(){ S.mutasi = now(); if (!jadwal) { jadwal = true; P.requestAnimationFrame(function(){ jadwal = false; periksa(); }); } });
  mo.observe(D.body, {childList: true, subtree: true});
  P.__masukObs.push(mo);
  // pemeriksaan berkala hanya bila perlu (ada kartu menunggu grafiknya, atau alamat berubah tanpa mutasi DOM) — ringan saat diam
  P.__masukTimer.push(P.setInterval(function(){ if (S.antrean.length || S.tertunda.length || P.location.pathname !== S.path) periksa(); }, 100));
  periksa();
})();
"""
