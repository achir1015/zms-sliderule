/* 資料助秘計算尺 線上版：計算尺元件、語音示範、讀尺練習、刻度一覽、知識、語音教學。
 * 不連任何伺服器；自訂尺型、計算紀錄、練習成績都存在這台裝置的瀏覽器（localStorage）。 */
(function () {
  "use strict";
  const R = window.SR, D = window.SRDemo, DATA = window.SR_DATA || { voice: {}, lessons: [], learn: [] };
  const $ = (s, el) => (el || document).querySelector(s);
  const $$ = (s, el) => Array.from((el || document).querySelectorAll(s));
  const h = (tag, attrs, ...kids) => {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === "class") el.className = v;
      else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
      else if (v !== false && v != null) el.setAttribute(k, v === true ? "" : v);
    }
    for (const c of kids.flat()) if (c != null && c !== false) el.append(c.nodeType ? c : String(c));
    return el;
  };
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const store = {
    get(k, d) { try { const v = localStorage.getItem("sr_" + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("sr_" + k, JSON.stringify(v)); } catch (e) { /* 私密模式 */ } },
  };
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg; t.classList.add("on");
    clearTimeout(toast.tm); toast.tm = setTimeout(() => t.classList.remove("on"), 3200);
  }

  // ================================================================== 語音
  const Voice = {
    audio: new Audio(),
    on: store.get("voice", true),
    token: 0,
    zh: null,
    init() {
      const pick = () => {
        const vs = (window.speechSynthesis && speechSynthesis.getVoices()) || [];
        Voice.zh = vs.find((v) => /zh[-_]TW/i.test(v.lang)) || vs.find((v) => /zh[-_](HK|Hant)/i.test(v.lang)) ||
          vs.find((v) => /^zh/i.test(v.lang)) || null;
      };
      pick();
      if (window.speechSynthesis) speechSynthesis.onvoiceschanged = pick;
    },
    unlock() {               // iPhone／iPad：要在按鈕事件裡先播一次，之後才能自動播放
      try {
        const a = Voice.audio;
        if (!Voice.silent) {               // 0.05 秒無聲 WAV
          const n = 400, buf = new ArrayBuffer(44 + n), v = new DataView(buf);
          const w = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
          w(0, "RIFF"); v.setUint32(4, 36 + n, true); w(8, "WAVEfmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true);
          v.setUint16(22, 1, true); v.setUint32(24, 8000, true); v.setUint32(28, 8000, true); v.setUint16(32, 1, true);
          v.setUint16(34, 8, true); w(36, "data"); v.setUint32(40, n, true);
          for (let i = 0; i < n; i++) v.setUint8(44 + i, 128);
          Voice.silent = URL.createObjectURL(new Blob([buf], { type: "audio/wav" }));
        }
        a.src = Voice.silent;
        const p = a.play(); if (p && p.catch) p.catch(() => {});
        if (window.speechSynthesis) { const u = new SpeechSynthesisUtterance(""); speechSynthesis.speak(u); }
      } catch (e) { /* 忽略 */ }
    },
    stop() {
      Voice.token++;
      try { Voice.audio.pause(); } catch (e) { /* 忽略 */ }
      if (window.speechSynthesis) speechSynthesis.cancel();
    },
    estimate(text) { return Math.max(2000, text.length / 4.6 * 1000); },
    /** 講一句話，講完（或估計時間到）才 resolve；mp3 有預錄就用自然語音，否則用瀏覽器語音。 */
    say(text, file) {
      Voice.stop();
      const tk = Voice.token;
      if (!Voice.on) return sleep(Voice.estimate(text));
      const mp3 = file || (DATA.voice[text] ? "../voice/demo/" + DATA.voice[text] : "");
      return new Promise((resolve) => {
        let done = false;
        const finish = () => { if (!done) { done = true; resolve(); } };
        const fallback = () => (tk === Voice.token ? Voice.tts(text).then(finish) : finish());
        if (mp3) {
          const a = Voice.audio;
          a.onended = finish; a.onerror = fallback;
          a.src = mp3;
          const p = a.play();
          if (p && p.catch) p.catch(() => (tk === Voice.token ? sleep(Voice.estimate(text)).then(finish) : finish()));
          setTimeout(finish, Voice.estimate(text) + 30000);
        } else fallback();
      });
    },
    tts(text) {
      return new Promise((resolve) => {
        if (!window.speechSynthesis) { sleep(Voice.estimate(text)).then(resolve); return; }
        const u = new SpeechSynthesisUtterance(text);
        u.lang = "zh-TW"; if (Voice.zh) u.voice = Voice.zh; u.rate = 1.05;
        let done = false;
        const fin = () => { if (!done) { done = true; resolve(); } };
        u.onend = fin; u.onerror = fin;
        speechSynthesis.speak(u);
        setTimeout(fin, Voice.estimate(text) * 1.6 + 3000);
      });
    },
  };

  // ================================================================== 計算尺元件
  const LW = 96, SH = 38, TM = 30, BM = 30, GAP = 3, CW = 64;
  const TICK_LEN = [0.56, 0.42, 0.31, 0.24, 0.19];
  const FONT = '"Noto Sans TC", "Microsoft JhengHei", "PingFang TC", system-ui, sans-serif';
  const near = (target, cur) => target + Math.round(cur - target);

  class RuleView {
    constructor(box, parts, onChange) {
      this.box = box;
      this.canvas = h("canvas");
      box.append(this.canvas);
      this.ctx = this.canvas.getContext("2d");
      this.parts = parts.map((p) => p.slice());
      this.onChange = onChange;
      this.st = { zoom: 1000, left: -0.05, slide: 0, cursor: 0 };
      this.W = 0; this.fine = false; this.highlight = new Set(); this.marks = [];
      this.pointers = new Map(); this.drag = null; this.pending = false; this.lastEmit = 0;
      this.labelPx = (t) => this.ctx.measureText(t).width + 8;
      new ResizeObserver(() => this.resize()).observe(box);
      const c = this.canvas;
      c.addEventListener("pointerdown", (e) => this.down(e));
      c.addEventListener("pointermove", (e) => this.move(e));
      c.addEventListener("pointerup", (e) => this.up(e));
      c.addEventListener("pointercancel", (e) => this.up(e));
      c.addEventListener("wheel", (e) => this.wheel(e), { passive: false });
      this.resize();
    }
    height() { return TM + BM + this.parts.reduce((n, p) => n + p.length, 0) * SH + 2 * GAP; }
    partTop(i) { let y = TM; for (let j = 0; j < i; j++) y += this.parts[j].length * SH + GAP; return y; }
    off(i) { return i === 1 ? this.st.slide : 0; }
    xOf(u) { return LW + (u - this.st.left) * this.st.zoom; }
    zoomAt(x, f) {
      const st = this.st, u = st.left + (x - LW) / st.zoom;
      st.zoom = Math.max(150, Math.min(5e9, st.zoom * f));
      st.left = u - (x - LW) / st.zoom;
    }
    resize() {
      const w = this.box.clientWidth;
      if (!w) return;
      const first = this.W === 0, W = Math.max(100, w - LW);
      if (Math.abs(W - this.W) < 1 && !first && this.canvas.height) { this.draw(); return; }
      if (first) { this.st.zoom = W * 0.92; this.st.left = -(W - this.st.zoom) / 2 / this.st.zoom; }
      else { const c = this.st.left + this.W / 2 / this.st.zoom; this.st.zoom *= W / this.W; this.st.left = c - W / 2 / this.st.zoom; }
      this.W = W;
      this.layout();
    }
    layout() {
      const dpr = window.devicePixelRatio || 1, H = this.height(), w = this.W + LW;
      this.canvas.width = Math.round(w * dpr); this.canvas.height = Math.round(H * dpr);
      this.canvas.style.height = H + "px";
      this.dpr = dpr;
      this.draw();
      this.emit(true);
    }
    setParts(parts) { this.parts = parts.map((p) => p.slice()); this.layout(); this.emit(true); }
    setHighlight(keys, marks) { this.highlight = new Set(keys || []); this.marks = marks || []; this.redraw(); }
    reset() {
      const W = this.W, z = W * 0.92;
      Object.assign(this.st, { zoom: z, left: -(W - z) / 2 / z, slide: 0, cursor: 0 });
      this.setHighlight([]); this.emit(true);
    }
    redraw() {
      if (this.pending) return;
      this.pending = true;
      requestAnimationFrame(() => { this.pending = false; this.draw(); this.emit(); });
    }
    emit(force) {
      const now = performance.now();
      if (this.onChange && (force || now - this.lastEmit > 70)) { this.lastEmit = now; this.onChange(this); }
      else if (this.onChange) { clearTimeout(this.emitTm); this.emitTm = setTimeout(() => this.emit(true), 90); }
    }
    draw() {
      const c = this.ctx, st = this.st, W = this.W, H = this.height(), dpr = this.dpr || 1;
      if (!W) return;
      c.setTransform(dpr, 0, 0, dpr, 0, 0);
      c.clearRect(0, 0, W + LW, H);
      c.fillStyle = "#F3EEDF"; c.fillRect(0, 0, W + LW, H);
      c.font = "11px " + FONT; c.fillStyle = "#9C8E6B"; c.textAlign = "left"; c.textBaseline = "middle";
      c.fillText("↔ 拖曳這裡：整把尺精細移動（1/10）", LW + 10, TM / 2);
      c.fillText("↔ 拖曳這裡：滑尺精細移動（1/10）", LW + 10, H - BM / 2);
      for (let i = 0; i < 3; i++) {
        const keys = this.parts[i], n = keys.length;
        if (!n) continue;
        const top = this.partTop(i), off = this.off(i);
        c.fillStyle = i === 1 ? "#FFFDF6" : "#FBF7EC";
        c.fillRect(LW, top, W, n * SH);
        if (i === 1) { c.strokeStyle = "#CDBF9A"; c.lineWidth = 1; c.beginPath(); c.moveTo(LW, top + 0.5); c.lineTo(LW + W, top + 0.5);
          c.moveTo(LW, top + n * SH - 0.5); c.lineTo(LW + W, top + n * SH - 0.5); c.stroke(); }
        const uL = st.left - off, uR = uL + W / st.zoom;
        c.save(); c.beginPath(); c.rect(LW, top, W, n * SH); c.clip();
        keys.forEach((k, j) => {
          const s = R.BY_KEY[k], y0 = top + j * SH;
          const down = i === 0 ? false : i === 2 ? true : (n > 1 ? j < Math.floor((n + 1) / 2) : true);
          const edge = down ? y0 : y0 + SH, sign = down ? 1 : -1;
          if (this.highlight.has(k)) { c.fillStyle = "rgba(255,210,74,.28)"; c.fillRect(LW, y0 + 1, W, SH - 2); }
          c.font = "600 12.5px " + FONT;
          const tks = R.ticks(s, uL - 20 / st.zoom, uR + 20 / st.zoom, st.zoom, this.labelPx);
          let base = Infinity;
          for (const t of tks) if (t.level >= 0 && t.level < base) base = t.level;
          if (base === Infinity) base = 0;
          const paths = [new Path2D(), new Path2D()];
          for (const t of tks) {
            if (t.level < 0) continue;
            const x = LW + (t.u - uL) * st.zoom, rel = Math.min(TICK_LEN.length - 1, Math.max(0, t.level - base));
            const p = paths[rel === 0 ? 0 : 1];
            p.moveTo(x, edge); p.lineTo(x, edge + sign * TICK_LEN[rel] * SH);
          }
          c.strokeStyle = s.color;
          c.lineWidth = 1.5; c.stroke(paths[0]);
          c.lineWidth = 0.9; c.stroke(paths[1]);
          c.textAlign = "center"; c.textBaseline = down ? "top" : "bottom";
          for (const lb of R.placeLabels(tks, st.zoom, uL, this.labelPx)) {
            const special = lb.level < 0, rel = special ? 0 : Math.max(0, lb.level - base);
            const ln = (special || rel === 0 ? TICK_LEN[0] : TICK_LEN[Math.min(rel, 4)]) * SH, x = LW + lb.x;
            c.font = (rel === 0 || special ? "700 12.5px " : "500 10.5px ") + FONT;
            c.fillStyle = special ? "#1F6FB2" : s.color;
            c.fillText(lb.text, x, edge + sign * (ln + 2));
            if (special) { c.strokeStyle = "#1F6FB2"; c.lineWidth = 1.2; c.beginPath(); c.moveTo(x, edge); c.lineTo(x, edge + sign * ln); c.stroke(); }
          }
          for (const [mk, mu] of this.marks) {
            if (mk !== k) continue;
            for (let kk = Math.floor(uL - mu) - 1; kk <= Math.floor(uR - mu) + 1; kk++) {
              const x = LW + (mu + kk - uL) * st.zoom;
              c.strokeStyle = "#E0A526"; c.lineWidth = 2.5; c.beginPath(); c.arc(x, y0 + SH / 2, 6, 0, Math.PI * 2); c.stroke();
            }
          }
          if (j < n - 1) { c.strokeStyle = "#E7DDC3"; c.lineWidth = 0.6; c.beginPath(); c.moveTo(LW, y0 + SH); c.lineTo(LW + W, y0 + SH); c.stroke(); }
        });
        c.restore();
        if (i < 2) { c.fillStyle = "#CDBF9A"; c.fillRect(0, top + n * SH, W + LW, GAP); }
      }
      // 左邊刻度名稱欄
      c.fillStyle = "#F7F0DC"; c.fillRect(0, 0, LW, H);
      for (let i = 0; i < 3; i++) {
        const top = this.partTop(i);
        this.parts[i].forEach((k, j) => {
          const s = R.BY_KEY[k], y = top + j * SH, hi = this.highlight.has(k);
          c.fillStyle = hi ? "#FFE08A" : (i === 1 ? "#FFF8E6" : "#F7F0DC"); c.fillRect(0, y, LW, SH);
          c.textBaseline = "middle"; c.textAlign = "left";
          c.font = "800 15px " + FONT; c.fillStyle = hi ? "#7A1F1F" : s.color; c.fillText(k, 10, y + SH / 2);
          const kw = c.measureText(k).width;
          c.font = "10px " + FONT; c.fillStyle = "#5B5B5B";
          let f = s.formula; while (f.length > 1 && c.measureText(f).width > LW - kw - 20) f = f.slice(0, -1);
          c.fillText(f === s.formula ? f : f + "…", 15 + kw, y + SH / 2);
        });
        if (i < 2 && this.parts[i].length) { c.fillStyle = "#CDBF9A"; c.fillRect(0, top + this.parts[i].length * SH, LW, GAP); }
      }
      c.fillStyle = "#CDBF9A"; c.fillRect(LW - 1, 0, 1, H);
      // 游標
      const cx = this.xOf(st.cursor);
      if (cx > LW - CW && cx < W + LW + CW) {
        c.save(); c.beginPath(); c.rect(LW, 0, W, H); c.clip();
        c.fillStyle = "rgba(91,141,239,.10)"; c.strokeStyle = "rgba(91,141,239,.40)"; c.lineWidth = 1;
        rr(c, cx - CW / 2, TM - 4, CW, H - TM - BM + 8, 6); c.fill(); c.stroke();
        c.fillStyle = "rgba(58,90,140,.78)";
        rr(c, cx - 16, 4, 32, TM - 8, 8); c.fill();
        rr(c, cx - 16, H - BM + 4, 32, BM - 8, 8); c.fill();
        c.fillStyle = "#fff";
        for (const yy of [TM / 2, H - BM / 2]) for (const dx of [-4, 4]) for (const dy of [-4, 0, 4]) { c.beginPath(); c.arc(cx + dx, yy + dy, 1.3, 0, 7); c.fill(); }
        c.fillStyle = "#D62828"; c.fillRect(cx - 0.8, 0, 1.6, H);
        c.restore();
      }
    }
    // ---------------------------------------------------------------- 操作
    target(x, y) {
      const cx = this.xOf(this.st.cursor), H = this.height();
      if (y < TM || y > H - BM) {
        if (Math.abs(x - cx) <= 18) return ["cursor", 1];
        return y < TM ? ["rule", 0.1] : ["slide", 0.1];
      }
      if (Math.abs(x - cx) <= 9) return ["cursor", 1];
      const y1 = this.partTop(1);
      if (this.parts[1].length && y >= y1 && y <= y1 + this.parts[1].length * SH) return ["slide", 1];
      return ["rule", 1];
    }
    pos(e) { const r = this.canvas.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; }
    down(e) {
      this.canvas.setPointerCapture(e.pointerId);
      const p = this.pos(e);
      this.pointers.set(e.pointerId, p);
      if (this.pointers.size === 1) {
        const [what, speed] = this.target(p[0], p[1]);
        this.drag = { what, speed: speed * (this.fine ? 0.1 : 1), x: p[0] };
      } else if (this.pointers.size === 2) {
        const [a, b] = [...this.pointers.values()];
        this.drag = { pinch: Math.hypot(a[0] - b[0], a[1] - b[1]) || 1 };
      }
      if (this.onUser) this.onUser();
    }
    move(e) {
      if (!this.pointers.has(e.pointerId) || !this.drag) return;
      const p = this.pos(e);
      this.pointers.set(e.pointerId, p);
      const st = this.st;
      if (this.drag.pinch && this.pointers.size >= 2) {
        const [a, b] = [...this.pointers.values()];
        const d = Math.hypot(a[0] - b[0], a[1] - b[1]) || 1;
        this.zoomAt((a[0] + b[0]) / 2, d / this.drag.pinch);
        this.drag.pinch = d;
      } else if (!this.drag.pinch) {
        const du = (p[0] - this.drag.x) * this.drag.speed / st.zoom;
        this.drag.x = p[0];
        if (this.drag.what === "rule") st.left -= du;
        else if (this.drag.what === "slide") st.slide += du;
        else st.cursor += du;
      }
      this.redraw();
    }
    up(e) {
      this.pointers.delete(e.pointerId);
      if (this.pointers.size === 1 && this.drag && this.drag.pinch) {
        const [p] = [...this.pointers.values()];
        const [what, speed] = this.target(p[0], p[1]);
        this.drag = { what, speed: speed * (this.fine ? 0.1 : 1), x: p[0] };
      } else if (!this.pointers.size) { this.drag = null; this.emit(true); }
    }
    wheel(e) {
      e.preventDefault();
      let dy = e.deltaY * (e.deltaMode === 1 ? 33 : e.deltaMode === 2 ? 400 : 1);
      if (e.ctrlKey) dy *= 3;                        // 觸控板捏合
      this.zoomAt(this.pos(e)[0], Math.pow(1.18, -dy / 100));
      this.redraw();
    }
    zoomBy(f) { this.zoomAt(this.xOf(this.st.cursor), f); this.redraw(); }
    readings() {
      const out = [];
      this.parts.forEach((part, i) => part.forEach((k) => {
        const [x, text] = R.reading(R.BY_KEY[k], this.st.cursor - this.off(i), this.st.zoom);
        out.push([i, k, x, text]);
      }));
      return out;
    }
    ensureVisible(u, margin) {
      margin = margin == null ? 0.18 : margin;
      const x = this.xOf(u) - LW;
      if (margin * this.W <= x && x <= (1 - margin) * this.W) return this.st.left;
      return u - 0.5 * this.W / this.st.zoom;
    }
    animateTo(o, seconds, alive) {
      const st = this.st, s0 = st.slide, c0 = st.cursor, l0 = st.left;
      const s1 = o.slide == null ? s0 : near(o.slide, s0), c1 = o.cursor == null ? c0 : near(o.cursor, c0);
      const l1 = o.left == null ? l0 : o.left, t0 = performance.now(), ms = seconds * 1000;
      return new Promise((resolve) => {
        let done = false;
        const tick = (now) => {
          if (done) return;
          if (alive && !alive()) { done = true; resolve(false); return; }
          let t = Math.min(1, Math.max(0, (now - t0) / ms)); t = t * t * (3 - 2 * t);
          st.slide = s0 + (s1 - s0) * t; st.cursor = c0 + (c1 - c0) * t; st.left = l0 + (l1 - l0) * t;
          this.draw(); this.emit();
          if (t < 1) requestAnimationFrame(tick); else { done = true; this.emit(true); resolve(true); }
        };
        requestAnimationFrame(tick);
        // 分頁在背景（或手機鎖屏）時瀏覽器會暫停畫面更新 → 時間到就直接到終點，示範不會卡住
        setTimeout(() => { if (!done) tick(t0 + ms); }, ms + 300);
      });
    }
  }
  function rr(c, x, y, w, hh, r) {
    c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + hh, r); c.arcTo(x + w, y + hh, x, y + hh, r);
    c.arcTo(x, y + hh, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
  }

  function readout(rv, box) {
    box.replaceChildren(...rv.readings().map(([part, k, , text]) => {
      const s = R.BY_KEY[k];
      return h("span", { class: "chip" + (part === 1 ? " slide" : "") + (rv.highlight.has(k) ? " hi" : ""), title: s.name },
        h("b", { style: "color:" + s.color }, k), h("i", {}, s.formula), h("span", {}, text));
    }));
  }

  // ================================================================== 示範執行
  let demoRun = 0;
  function stopDemo() { demoRun++; Voice.stop(); }
  async function runDemo(rv, pl, onStep) {
    stopDemo();
    const my = ++demoRun, alive = () => my === demoRun;
    for (let i = 0; i < pl.steps.length; i++) {
      if (!alive()) return false;
      const s = pl.steps[i];
      onStep(i);
      rv.setHighlight(s.hl, s.marks);
      const speaking = Voice.say(s.text);
      let left = null;
      if (s.cursor != null) left = rv.ensureVisible(near(s.cursor, rv.st.cursor));
      await rv.animateTo({ slide: s.slide, cursor: s.cursor, left }, 1.0, alive);
      await speaking;
      if (!alive()) return false;
      await sleep(250);
    }
    return alive();
  }
  function hasScales(rv, needs) { const all = new Set(rv.parts.flat()); return needs.every((k) => all.has(k)); }
  function stepList(ol, pl) { ol.replaceChildren(...pl.steps.map((s) => h("li", {}, s.text))); }
  function markStep(ol, i) { $$("li", ol).forEach((li, j) => li.classList.toggle("on", j === i)); const li = ol.children[i]; if (li && li.scrollIntoViewIfNeeded) li.scrollIntoViewIfNeeded(); }

  // ================================================================== 尺型
  function allLayouts() {
    const out = R.LAYOUTS.map((l) => ({ key: l[0], name: l[1], parts: [l[2], l[3], l[4]], note: l[5] }));
    for (const l of store.get("layouts", [])) out.push({ key: l.key, name: "★ " + l.name, parts: l.parts, note: "我的尺型", mine: true });
    return out;
  }
  const layoutBy = (key) => allLayouts().find((l) => l.key === key);

  // ================================================================== 計算尺頁
  const pref = store.get("pref", { layout: "student" });
  const startLay = layoutBy(pref.layout) || layoutBy("student");
  const rv1 = new RuleView($("#rule1"), startLay.parts, (rv) => { readout(rv, $("#read1")); zoomText(rv); });
  function zoomText(rv) {
    const z = rv.st.zoom / Math.max(rv.W * 0.92, 1);
    const zs = z < 10 ? z.toFixed(1) : z < 1e6 ? Math.round(z).toLocaleString() : z.toExponential(2);
    $("#zoomText").textContent = "放大 " + zs + " 倍　（滑尺位移 " + (rv.st.slide - Math.floor(rv.st.slide)).toFixed(5) + "）";
  }
  function fillLayouts(sel, cur) {
    sel.replaceChildren(...allLayouts().map((l) => h("option", { value: l.key, selected: l.key === cur }, l.name)));
    if (!layoutBy(cur)) sel.append(h("option", { value: "custom", selected: true }, "（自訂）"));
  }
  let curLayout = startLay.key;
  fillLayouts($("#layout"), curLayout);
  function useLayout(key, save) {
    const l = layoutBy(key); if (!l) return;
    curLayout = key; fillLayouts($("#layout"), key);
    rv1.setParts(l.parts);
    if (save !== false) { pref.layout = key; store.set("pref", pref); }
  }
  $("#layout").addEventListener("change", (e) => useLayout(e.target.value));
  $("#zoomIn").onclick = () => rv1.zoomBy(1.6);
  $("#zoomOut").onclick = () => rv1.zoomBy(1 / 1.6);
  $("#reset").onclick = () => { stopDemo(); rv1.reset(); };
  $("#fine").onchange = (e) => { rv1.fine = e.target.checked; };
  $("#stop").onclick = () => stopDemo();
  $("#presets").append(...D.PRESETS.map((p) => h("button", { type: "button", onclick: () => { $("#expr").value = p; demo1(true); } }, p)));
  $("#demoForm").addEventListener("submit", (e) => { e.preventDefault(); demo1(true); });

  async function demo1(user) {
    let pl;
    try { pl = D.plan($("#expr").value); } catch (err) { toast(err.message); return; }
    if (user) Voice.unlock();
    if (!hasScales(rv1, pl.needs)) useLayout(pl.layout, false);
    stepList($("#steps"), pl);
    $("#answer").textContent = "";
    addRecent(pl);
    const ok = await runDemo(rv1, pl, (i) => markStep($("#steps"), i));
    if (ok) $("#answer").textContent = "答案：" + pl.result_text + "　（計算機驗算：" + pl.exact_text + "）";
  }
  function addRecent(pl) {
    const list = store.get("hist", []).filter((x) => x.e !== pl.expr);
    list.unshift({ e: pl.expr, r: pl.result_text, t: Date.now() });
    store.set("hist", list.slice(0, 30));
    showRecent();
  }
  function showRecent() {
    const list = store.get("hist", []);
    $("#recent").replaceChildren(...(list.length ? ["最近算過：", ...list.slice(0, 12).map((x) =>
      h("button", { type: "button", title: "答案 " + x.r, onclick: () => { $("#expr").value = x.e; demo1(true); } }, x.e))] : []));
  }
  showRecent();

  // ---------------------------------------------------------------- 自訂刻度
  function openPicker(rv, after) {
    const dlg = $("#pickDlg"), parts = rv.parts.map((p) => p.slice());
    const render = () => {
      $$(".pickpart", dlg).forEach((box, i) => {
        $(".sel-list", box).replaceChildren(...parts[i].map((k) => h("button", { type: "button", title: R.BY_KEY[k].name,
          onclick: () => { parts[i] = parts[i].filter((x) => x !== k); render(); } }, k)));
        const used = new Set(parts.flat());
        $(".opts", box).replaceChildren(...R.SCALES.map((s) => h("button", { type: "button", class: used.has(s.key) ? "used" : "",
          title: s.formula + "：" + s.name, onclick: () => { if (!used.has(s.key)) { parts[i].push(s.key); render(); } } }, s.key)));
      });
    };
    render();
    $("#pickName").value = "";
    dlg.onclose = () => {
      if (dlg.returnValue !== "ok") return;
      if (!parts.flat().length) { toast("至少要選一個刻度"); return; }
      const name = $("#pickName").value.trim();
      if (name) {
        const list = store.get("layouts", []).filter((l) => l.name !== name);
        const key = "u" + Date.now().toString(36);
        list.push({ key, name, parts });
        store.set("layouts", list);
        toast("已存成我的尺型「" + name + "」");
        after(parts, key);
      } else after(parts, null);
    };
    dlg.showModal();
  }
  $("#custom").onclick = () => openPicker(rv1, (parts, key) => {
    if (key) useLayout(key); else { curLayout = "custom"; rv1.setParts(parts); fillLayouts($("#layout"), "custom"); }
    renderLayouts();
  });

  // ================================================================== 讀尺練習
  $("#dKind").append(...D.DRILL_KINDS.map(([k, n]) => h("option", { value: k }, n)));
  const dpref = store.get("drillPref", { kind: "MUL", size: 10, tol: 1 });
  $("#dKind").value = dpref.kind; $("#dSize").value = dpref.size; $("#dTol").value = dpref.tol;
  let rv2 = null, drill = null;
  $("#dStart").onclick = () => {
    const size = Math.max(3, Math.min(30, parseInt($("#dSize").value, 10) || 10));
    const tol = Math.max(0.1, Math.min(10, parseFloat($("#dTol").value) || 1));
    const kind = $("#dKind").value;
    store.set("drillPref", { kind, size, tol });
    const items = [];
    for (let i = 0; i < size; i++) { const [e, ans, k] = D.makeProblem(kind); items.push({ e, ans, k }); }
    drill = { kind, tol, items, idx: 0, t: Date.now() };
    $("#drillSetup").classList.add("hidden"); $("#drillDone").classList.add("hidden"); $("#drillQ").classList.remove("hidden");
    if (!rv2) rv2 = new RuleView($("#rule2"), layoutBy("student").parts, (rv) => readout(rv, $("#read2")));
    showQ();
  };
  function showQ() {
    const it = drill.items[drill.idx];
    stopDemo();
    $("#qNo").textContent = "第 " + (drill.idx + 1) + "／" + drill.items.length + " 題";
    $("#qExpr").textContent = it.e;
    $("#qAns").value = ""; $("#qMsg").textContent = ""; $("#qMsg").className = "msg"; $("#qSteps").replaceChildren();
    $("#qForm button[type=submit]").textContent = "確定";
    try { const pl = D.plan(it.e); if (!hasScales(rv2, pl.needs)) rv2.setParts(layoutBy(pl.layout).parts); } catch (e) { /* 忽略 */ }
    rv2.setHighlight([]);
    setTimeout(() => $("#qAns").focus({ preventScroll: true }), 50);
  }
  $("#qForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const it = drill.items[drill.idx];
    if (it.done) { next(); return; }
    const v = parseFloat($("#qAns").value.replace(/[，,\s]/g, ""));
    if (!isFinite(v)) { toast("請輸入數字"); return; }
    const err = Math.abs(v - it.ans) / Math.max(Math.abs(it.ans), 1e-12) * 100;
    Object.assign(it, { given: v, err, ok: err <= drill.tol && !it.hint, done: true });
    const m = $("#qMsg");
    m.className = "msg " + (it.ok ? "ok" : "bad");
    m.textContent = (err <= drill.tol ? "✔ 答對了！" : "✘ 差了一點。") + "正確答案約 " + D.sig(it.ans, 4) + "，誤差 " + err.toFixed(2) + "%" +
      (it.hint && err <= drill.tol ? "（看過示範，這題不計分）" : "");
    $("#qForm button[type=submit]").textContent = drill.idx + 1 < drill.items.length ? "下一題 ▶" : "看成績";
  });
  function next() { if (++drill.idx < drill.items.length) showQ(); else finish(); }
  $("#qHint").onclick = async () => {
    const it = drill.items[drill.idx];
    let pl; try { pl = D.plan(it.e); } catch (e) { toast(e.message); return; }
    Voice.unlock();
    it.hint = true;
    if (!hasScales(rv2, pl.needs)) rv2.setParts(layoutBy(pl.layout).parts);
    stepList($("#qSteps"), pl);
    const ok = await runDemo(rv2, pl, (i) => markStep($("#qSteps"), i));
    if (ok && !it.done) $("#qMsg").textContent = "計算尺讀出約 " + pl.result_text;
  };
  $("#qQuit").onclick = () => {
    stopDemo();
    if (drill && drill.items.some((x) => x.done) && confirm("結束練習？已作答的題目會記錄成績。")) {
      drill.items = drill.items.filter((x) => x.done); finish();
    } else if (drill && !drill.items.some((x) => x.done)) {
      drill = null; $("#drillQ").classList.add("hidden"); $("#drillSetup").classList.remove("hidden");
    }
  };
  function finish() {
    stopDemo();
    const n = drill.items.length, right = drill.items.filter((x) => x.ok).length, score = Math.round(right / n * 100);
    const rec = { t: Date.now(), kind: drill.kind, tol: drill.tol, n, right, score,
      items: drill.items.map((x) => ({ e: x.e, k: x.k, a: x.ans, g: x.given, err: x.err, ok: !!x.ok, hint: !!x.hint })) };
    const hist = store.get("drills", []); hist.push(rec); store.set("drills", hist.slice(-200));
    const kindName = Object.fromEntries(D.DRILL_KINDS)[drill.kind];
    const box = $("#drillDone");
    box.replaceChildren(
      h("h3", {}, h("span", { class: "tile amber" }, "🏁"), "練習完成：" + kindName),
      h("div", { class: "score " + (score >= 60 ? "ok" : "bad") }, score + " 分"),
      h("p", { class: "muted" }, "答對 " + right + "／" + n + " 題（容許誤差 " + drill.tol + "%）"),
      h("div", { class: "tablewrap" }, h("table", {}, h("tr", {}, ...["題目", "你的答案", "正確答案", "誤差", "結果"].map((x) => h("th", {}, x))),
        ...rec.items.map((x) => h("tr", {}, h("td", {}, x.e), h("td", {}, x.g == null ? "—" : String(x.g)), h("td", {}, D.sig(x.a, 4)),
          h("td", {}, x.err == null ? "—" : x.err.toFixed(2) + "%"),
          h("td", { style: "color:" + (x.ok ? "var(--ok)" : "var(--bad)") }, x.ok ? "✔" : (x.hint ? "看示範" : "✘")))))),
      h("div", { class: "row", style: "margin-top:10px" }, h("button", { class: "btn", onclick: () => $("#dStart").click() }, "再練一回"),
        h("button", { class: "btn outline", onclick: () => { box.classList.add("hidden"); $("#drillSetup").classList.remove("hidden"); } }, "換題型")));
    drill = null;
    $("#drillQ").classList.add("hidden"); box.classList.remove("hidden");
    renderGrowth();
    box.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderGrowth() {
    const hist = store.get("drills", []), box = $("#growth");
    if (!hist.length) { box.replaceChildren(h("p", { class: "muted" }, "還沒有練習紀錄。完成一回讀尺練習後，這裡會畫出分數的成長折線圖。")); return; }
    const last = hist.slice(-30), Wd = 720, Hd = 220, pl = 40, pr = 14, pt = 14, pb = 28;
    const xs = (i) => pl + (last.length === 1 ? (Wd - pl - pr) / 2 : i * (Wd - pl - pr) / (last.length - 1));
    const ys = (v) => pt + (100 - v) * (Hd - pt - pb) / 100;
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", `0 0 ${Wd} ${Hd}`); svg.setAttribute("width", "100%"); svg.style.maxWidth = Wd + "px";
    let s = "";
    for (const v of [0, 20, 40, 60, 80, 100]) s += `<line x1="${pl}" x2="${Wd - pr}" y1="${ys(v)}" y2="${ys(v)}" stroke="${v === 60 ? "#F4B4B4" : "#E5EAF1"}" ${v === 60 ? 'stroke-dasharray="5 4"' : ""}/><text x="${pl - 8}" y="${ys(v) + 4}" font-size="11" text-anchor="end" fill="#6B7280">${v}</text>`;
    s += `<polyline fill="none" stroke="#2F6FBF" stroke-width="2.5" points="${last.map((r, i) => xs(i) + "," + ys(r.score)).join(" ")}"/>`;
    last.forEach((r, i) => { s += `<circle cx="${xs(i)}" cy="${ys(r.score)}" r="4.5" fill="${r.score >= 60 ? "#15803D" : "#B91C1C"}"><title>${new Date(r.t).toLocaleString()}　${r.score} 分</title></circle>`; });
    s += `<text x="${pl}" y="${Hd - 8}" font-size="11" fill="#6B7280">最近 ${last.length} 回（紅色虛線＝60 分）</text>`;
    svg.innerHTML = s;
    const kinds = {};
    for (const r of hist) for (const it of r.items) {
      const k = kinds[it.k] || (kinds[it.k] = { n: 0, ok: 0, err: 0, en: 0 });
      k.n++; if (it.ok) k.ok++; if (it.err != null) { k.err += it.err; k.en++; }
    }
    const names = Object.fromEntries(D.DRILL_KINDS);
    const best = Math.max(...hist.map((r) => r.score)), avg = Math.round(hist.reduce((a, r) => a + r.score, 0) / hist.length);
    box.replaceChildren(
      h("p", {}, "共練習 ", h("b", {}, hist.length), " 回，平均 ", h("b", {}, avg), " 分，最高 ", h("b", {}, best), " 分。"),
      svg,
      h("div", { class: "tablewrap" }, h("table", {}, h("tr", {}, ...["題型", "題數", "答對率", "平均誤差"].map((x) => h("th", {}, x))),
        ...Object.entries(kinds).map(([k, v]) => h("tr", {}, h("td", {}, names[k] || k), h("td", {}, v.n),
          h("td", {}, Math.round(v.ok / v.n * 100) + "%"), h("td", {}, v.en ? (v.err / v.en).toFixed(2) + "%" : "—"))))),
      h("p", { style: "margin-top:8px" }, h("button", { class: "btn ghost", onclick: () => {
        if (confirm("清除這台裝置上的全部練習紀錄？清除後無法復原。")) { store.set("drills", []); renderGrowth(); }
      } }, "清除練習紀錄")));
  }
  renderGrowth();

  // ================================================================== 刻度一覽
  function rangeText(s) {
    const a = Math.min(s.lo, s.hi), b = Math.max(s.lo, s.hi);
    return D.sig(a, 4) + s.unit + "～" + D.sig(b, 4) + s.unit;
  }
  const KIND = { log: "對數", lin: "線性", trig: "三角", ll: "雙對數" };
  const SLIDE_KEYS = new Set(["C", "CI", "CF", "CIF", "B"]);
  $("#scaleTable").append(h("tr", {}, ...["代號", "公式", "說明", "數值範圍", "種類", ""].map((x) => h("th", {}, x))),
    ...R.SCALES.map((s) => h("tr", {}, h("td", { class: "key", style: "color:" + s.color }, s.key), h("td", {}, s.formula), h("td", {}, s.name),
      h("td", {}, rangeText(s)), h("td", {}, KIND[s.kind]),
      h("td", {}, h("button", { class: "btn outline", onclick: () => showScale(s.key) }, "在計算尺上看")))));
  function showScale(key) {
    const l = allLayouts().find((x) => !x.mine && x.parts.flat().includes(key));
    location.hash = "#rule";
    if (l) useLayout(l.key);
    else {
      const parts = SLIDE_KEYS.has(key) ? [[], [key, "C"], ["D"]] : [[key], ["C"], ["D"]];
      curLayout = "custom"; rv1.setParts(parts); fillLayouts($("#layout"), "custom");
    }
    rv1.setHighlight([key]);
  }
  function renderLayouts() {
    $("#layoutList").replaceChildren(...allLayouts().map((l) => h("div", { class: "lay" },
      h("b", {}, l.name), h("div", { class: "muted" }, l.note),
      h("p", {}, "上：", h("code", {}, l.parts[0].join(" ") || "—"), "　滑：", h("code", {}, l.parts[1].join(" ") || "—"), "　下：", h("code", {}, l.parts[2].join(" ") || "—")),
      h("div", { class: "row" }, h("button", { class: "btn", onclick: () => { location.hash = "#rule"; useLayout(l.key); } }, "使用"),
        l.mine ? h("button", { class: "btn ghost", onclick: () => {
          if (!confirm("刪除我的尺型「" + l.name.slice(2) + "」？")) return;
          store.set("layouts", store.get("layouts", []).filter((x) => x.key !== l.key));
          if (curLayout === l.key) useLayout("student"); else fillLayouts($("#layout"), curLayout);
          renderLayouts();
        } }, "刪除") : null))));
  }
  renderLayouts();

  // ================================================================== 計算尺知識
  $("#learnList").append(...DATA.learn.map((sec, i) => h("div", { class: "card" },
    h("h3", {}, h("span", { class: "num" }, i + 1), sec.title,
      h("button", { class: "icon-btn", style: "margin-left:auto", title: "朗讀這一段", onclick: () => { Voice.unlock(); Voice.tts(sec.title + "。" + sec.paras.join("")); } }, "🔈")),
    h("div", { class: "learn" }, h("div", { class: "txt" }, ...sec.paras.map((p) => h("p", {}, p))),
      h("figure", {}, h("img", { src: "../img/learn/" + sec.img, alt: sec.cap, loading: "lazy" }), h("figcaption", {}, sec.cap))))),
    h("p", { class: "muted small" }, DATA.learn_source || ""));

  // ================================================================== 語音教學
  let lessonKey = DATA.lessons.length ? DATA.lessons[0].key : null, lessonTimer = null;
  const SID = { rule: "#rule", scales: "#scales", layouts: "#scales", drill: "#drill", growth: "#drill", learn: "#learn" };
  function renderLessons() {
    $("#lessonList").replaceChildren(h("h3", {}, h("span", { class: "tile rose" }, "🎧"), "語音動態教學"),
      ...DATA.lessons.map((l, i) => h("button", { class: l.key === lessonKey ? "on" : "", onclick: () => { stopLesson(); lessonKey = l.key; renderLessons(); } },
        (i + 1) + "．" + l.title)));
    const l = DATA.lessons.find((x) => x.key === lessonKey);
    if (!l) return;
    const steps = l.steps.map(([, , text, sid], i) => h("div", { class: "lstep" }, h("span", { class: "n" }, i + 1), h("span", {}, text),
      SID[sid] ? h("a", { href: SID[sid], onclick: () => stopLesson() }, "跟著做 →") :
        h("span", { class: "muted small", style: "margin-left:auto" }, "（桌面版功能）")));
    $("#lessonView").replaceChildren(
      h("h3", {}, l.title),
      h("div", { class: "row wrap" }, h("button", { class: "btn", id: "lPlay", onclick: () => playLesson(l) }, "▶ 播放語音教學"),
        h("button", { class: "btn outline", onclick: () => stopLesson() }, "■ 停止"),
        l.demo ? h("button", { class: "btn outline", onclick: () => { stopLesson(); location.hash = "#rule:" + encodeURIComponent(l.demo); Voice.unlock(); } },
          "📏 到計算尺看示範（" + l.demo + "）") : null),
      h("div", { class: "lsteps" }, ...steps),
      h("div", { class: "voice-text" }, l.voice));
  }
  function playLesson(l) {
    stopLesson(); Voice.stop();
    const a = Voice.audio, tk = Voice.token, n = l.steps.length;
    a.onended = () => { stopLesson(); }; a.onerror = () => toast("語音檔載入失敗");
    a.src = "../voice/" + l.key + ".mp3";
    const p = a.play(); if (p && p.catch) p.catch(() => toast("請再按一次播放"));
    lessonTimer = setInterval(() => {
      if (tk !== Voice.token) { stopLesson(); return; }
      const d = a.duration || 0, i = d ? Math.min(n - 1, Math.floor(a.currentTime / d * n)) : 0;
      $$(".lstep").forEach((el, j) => el.classList.toggle("on", j === i));
    }, 200);
  }
  function stopLesson() {
    if (lessonTimer) { clearInterval(lessonTimer); lessonTimer = null; Voice.stop(); }
    $$(".lstep").forEach((el) => el.classList.remove("on"));
  }
  renderLessons();

  // ================================================================== 分頁與網址
  function route() {
    const hs = decodeURIComponent(location.hash.slice(1) || "rule");
    const [tab, arg] = [hs.split(":")[0], hs.includes(":") ? hs.slice(hs.indexOf(":") + 1) : ""];
    const name = $("#tab-" + tab) ? tab : "rule";
    $$(".tab").forEach((el) => el.classList.toggle("on", el.id === "tab-" + name));
    $$("#tabs a").forEach((a) => a.classList.toggle("on", a.dataset.tab === name));
    if (name !== "help") stopLesson();
    if (name !== "rule" && name !== "drill") stopDemo();
    if (name === "rule") { rv1.resize(); if (arg) { $("#expr").value = arg; history.replaceState(null, "", "#rule"); setTimeout(() => demo1(false), 300); } }
    if (name === "drill" && rv2) rv2.resize();
    window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", route);
  $("#mute").onclick = () => {
    Voice.on = !Voice.on; store.set("voice", Voice.on);
    $("#mute").textContent = Voice.on ? "🔊" : "🔇";
    if (!Voice.on) Voice.stop();
    toast(Voice.on ? "語音已開啟" : "語音已關閉（示範仍會移動計算尺）");
  };
  $("#mute").textContent = Voice.on ? "🔊" : "🔇";
  $("#ver").textContent = "v" + (DATA.version || "");
  Voice.init();
  route();
  if ("serviceWorker" in navigator && location.protocol === "https:") navigator.serviceWorker.register("../sw.js").catch(() => {});
})();
