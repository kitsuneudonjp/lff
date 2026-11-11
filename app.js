/* LFF鳥取 検証ノート：閲覧を助ける小さな機能（外部ライブラリなし） */
(function () {
  'use strict';

  /* ---------- ライトボックス ---------- */
  var figures = Array.prototype.slice.call(document.querySelectorAll('main figure'));
  var items = figures.map(function (fig) {
    var img = fig.querySelector('img');
    var cap = fig.querySelector('figcaption');
    return img ? { img: img, caption: cap ? cap.innerHTML : '' } : null;
  }).filter(Boolean);

  var box = document.createElement('div');
  box.className = 'lb';
  box.setAttribute('role', 'dialog');
  box.setAttribute('aria-modal', 'true');
  box.setAttribute('aria-label', '証拠画像の拡大表示');
  box.hidden = true;
  box.innerHTML =
    '<div class="lb-bar">' +
      '<span class="lb-count" aria-live="polite"></span>' +
      '<a class="lb-btn lb-orig" target="_blank" rel="noopener">原寸を開く</a>' +
      '<button type="button" class="lb-btn lb-close" aria-label="閉じる">×</button>' +
    '</div>' +
    '<div class="lb-stage"><img class="lb-img" alt=""></div>' +
    '<button type="button" class="lb-nav lb-prev" aria-label="前の画像">‹</button>' +
    '<button type="button" class="lb-nav lb-next" aria-label="次の画像">›</button>' +
    '<div class="lb-cap"></div>';
  document.body.appendChild(box);

  var stage = box.querySelector('.lb-stage');
  var lbImg = box.querySelector('.lb-img');
  var lbCap = box.querySelector('.lb-cap');
  var lbCount = box.querySelector('.lb-count');
  var lbOrig = box.querySelector('.lb-orig');
  var current = 0;
  var lastFocus = null;

  function show(i) {
    current = (i + items.length) % items.length;
    var it = items[current];
    box.classList.remove('zoomed');
    lbImg.src = it.img.currentSrc || it.img.src;
    lbImg.alt = it.img.alt;
    lbCap.innerHTML = it.caption;
    lbCount.textContent = (current + 1) + ' / ' + items.length;
    lbOrig.href = it.img.src;
  }
  function open(i) {
    lastFocus = document.activeElement;
    show(i);
    box.hidden = false;
    document.documentElement.classList.add('lb-open');
    box.querySelector('.lb-close').focus();
  }
  function close() {
    box.hidden = true;
    document.documentElement.classList.remove('lb-open');
    if (lastFocus) lastFocus.focus();
  }

  items.forEach(function (it, i) {
    var img = it.img;
    img.tabIndex = 0;
    img.setAttribute('role', 'button');
    img.setAttribute('aria-label', '拡大表示：' + img.alt);
    img.classList.add('zoomable');
    img.addEventListener('click', function () { open(i); });
    img.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(i); }
    });
  });

  box.querySelector('.lb-close').addEventListener('click', close);
  box.querySelector('.lb-prev').addEventListener('click', function () { show(current - 1); });
  box.querySelector('.lb-next').addEventListener('click', function () { show(current + 1); });
  // 画像をクリック：画面に合わせる ⇔ 原寸（はみ出した分はスクロール）
  lbImg.addEventListener('click', function (e) { e.stopPropagation(); box.classList.toggle('zoomed'); });
  // 画像の外の暗い部分をクリックで閉じる
  stage.addEventListener('click', function (e) { if (e.target === stage) close(); });

  document.addEventListener('keydown', function (e) {
    if (box.hidden) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') show(current - 1);
    else if (e.key === 'ArrowRight') show(current + 1);
    else if (e.key === 'Tab') { // フォーカスをダイアログ内に閉じ込める
      var f = box.querySelectorAll('button, a[href]');
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

  // スマホ：左右スワイプで前後へ（拡大中は無効）
  var sx = null, sy = null;
  stage.addEventListener('touchstart', function (e) {
    if (e.touches.length === 1) { sx = e.touches[0].clientX; sy = e.touches[0].clientY; }
  }, { passive: true });
  stage.addEventListener('touchend', function (e) {
    if (sx === null || box.classList.contains('zoomed')) { sx = null; return; }
    var dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) show(current + (dx < 0 ? 1 : -1));
    sx = null;
  });

  // 本文中の「画像 LI02」などのリンクは、該当の図までスクロールして一瞬強調する
  document.querySelectorAll('a[href^="#fig-"]').forEach(function (a) {
    a.addEventListener('click', function () {
      var t = document.querySelector(a.getAttribute('href'));
      if (!t) return;
      setTimeout(function () {
        t.classList.remove('flash'); void t.offsetWidth; t.classList.add('flash');
      }, 350);
    });
  });

  /* ---------- 目次：スマホでは折りたたみ、現在地を表示 ---------- */
  var tocDetails = document.querySelector('.toc details');
  var mq = window.matchMedia('(max-width: 820px)');
  function syncToc() { if (tocDetails) tocDetails.open = !mq.matches; }
  syncToc();
  if (mq.addEventListener) mq.addEventListener('change', syncToc);
  document.querySelectorAll('.toc a').forEach(function (a) {
    a.addEventListener('click', function () { if (mq.matches && tocDetails) tocDetails.open = false; });
  });

  var tocLinks = {};
  document.querySelectorAll('.toc a[href^="#"]').forEach(function (a) { tocLinks[a.getAttribute('href').slice(1)] = a; });
  if ('IntersectionObserver' in window) {
    var visible = {};
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { visible[en.target.id] = en.isIntersecting; });
      var ids = Object.keys(tocLinks);
      var cur = null;
      for (var i = 0; i < ids.length; i++) { if (visible[ids[i]]) { cur = ids[i]; break; } }
      if (!cur) return;
      ids.forEach(function (id) { tocLinks[id].classList.toggle('active', id === cur); });
    }, { rootMargin: '-15% 0px -70% 0px' });
    Object.keys(tocLinks).forEach(function (id) { var s = document.getElementById(id); if (s) io.observe(s); });
  }

  /* ---------- 見出しへのリンク（共有用） ---------- */
  document.querySelectorAll('main section[id] > h2').forEach(function (h) {
    var a = document.createElement('a');
    a.className = 'h-anchor';
    a.href = '#' + h.parentElement.id;
    a.textContent = '#';
    a.setAttribute('aria-label', 'この節へのリンク');
    h.appendChild(a);
  });

  /* ---------- 上へ戻る ---------- */
  var top = document.createElement('button');
  top.type = 'button';
  top.className = 'to-top';
  top.setAttribute('aria-label', 'ページの先頭へ戻る');
  top.textContent = '↑';
  top.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
  document.body.appendChild(top);
  function onScroll() { top.classList.toggle('show', window.scrollY > 800); }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();
