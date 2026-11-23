/* 計算尺引擎（sr/rule.py 的 JavaScript 版本）：刻度定義、刻度線產生、讀數。
 * 一把尺＝1 單位（u）；每種刻度 f：數值→u、g：u→數值，每 1 單位重複一次（自動環繞）。 */
(function (G) {
  "use strict";
  const LN10 = Math.log(10), MIN_PX = 6, NICE = [1, 2, 2.5, 5];
  const lg = Math.log10, rad = (d) => d * Math.PI / 180, deg = (r) => r * 180 / Math.PI;
  const frac = (u) => u - Math.floor(u);
  const PI = Math.PI, E = Math.E;

  function fixed(x, d) { return x.toFixed(Math.max(0, Math.min(20, d))); }

  function trim(s) {
    if (s.indexOf(".") >= 0) s = s.replace(/0+$/, "").replace(/\.$/, "");
    if (s.startsWith("0.") && s.length > 2) s = s.slice(1);
    if (s.startsWith("-0.")) s = "-" + s.slice(2);
    return s || "0";
  }

  function logMarks(a, b) {
    const out = [];
    for (let e = a; e < b; e++) for (let k = 1; k < 10; k++) out.push(k * Math.pow(10, e));
    out.push(Math.pow(10, b));
    return out;
  }

  function Scale(key, formula, name, f, g, marks, lo, hi, opt) {
    opt = opt || {};
    return {
      key, formula, name, f, g, marks, lo, hi,
      color: opt.color || "#1F2937", kind: opt.kind || "log", unit: opt.unit || "", special: opt.special || [],
      value(u) { return g(frac(u)); },
      label(x, step) {
        const d = step < 1 ? Math.max(0, -Math.floor(lg(step) + 1e-9)) : 0;
        if (Math.abs(x) >= 1e4 && !/^(S|T|T2|ST)$/.test(key)) return String(+x.toPrecision(6));
        return trim(fixed(x, d));
      },
    };
  }

  const RED = { color: "#C0392B" };
  const folded = [3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35];
  const SCALES = [
    Scale("C", "x", "基本刻度（滑尺）", (x) => lg(x), (u) => Math.pow(10, u), logMarks(0, 1), 1, 10, { special: [[PI, "π"]] }),
    Scale("D", "x", "基本刻度（定尺）", (x) => lg(x), (u) => Math.pow(10, u), logMarks(0, 1), 1, 10, { special: [[PI, "π"]] }),
    Scale("CI", "1/x", "倒數刻度（滑尺，由右到左）", (x) => 1 - lg(x), (u) => Math.pow(10, 1 - u), logMarks(0, 1), 1, 10, RED),
    Scale("DI", "1/x", "倒數刻度（定尺，由右到左）", (x) => 1 - lg(x), (u) => Math.pow(10, 1 - u), logMarks(0, 1), 1, 10, RED),
    Scale("CF", "πx", "π 摺疊刻度（滑尺）", (x) => lg(x / PI), (u) => PI * Math.pow(10, u), folded, PI, 10 * PI, { special: [[PI, "π"]] }),
    Scale("DF", "πx", "π 摺疊刻度（定尺）", (x) => lg(x / PI), (u) => PI * Math.pow(10, u), folded, PI, 10 * PI, { special: [[PI, "π"]] }),
    Scale("CIF", "1/(πx)", "π 摺疊倒數刻度", (x) => 1 - lg(x / PI), (u) => PI * Math.pow(10, 1 - u), folded, PI, 10 * PI, RED),
    Scale("A", "x²", "平方刻度（定尺；兩個循環）", (x) => lg(x) / 2, (u) => Math.pow(10, 2 * u), logMarks(0, 2), 1, 100, { special: [[PI, "π"]] }),
    Scale("B", "x²", "平方刻度（滑尺；兩個循環）", (x) => lg(x) / 2, (u) => Math.pow(10, 2 * u), logMarks(0, 2), 1, 100, { special: [[PI, "π"]] }),
    Scale("K", "x³", "立方刻度（三個循環）", (x) => lg(x) / 3, (u) => Math.pow(10, 3 * u), logMarks(0, 3), 1, 1000),
    Scale("R1", "√x", "平方根刻度（1～3.16）", (x) => 2 * lg(x), (u) => Math.pow(10, u / 2), [1, 1.5, 2, 2.5, 3, 3.5], 1, Math.sqrt(10)),
    Scale("R2", "√10x", "平方根刻度（3.16～10）", (x) => 2 * lg(x) - 1, (u) => Math.pow(10, (u + 1) / 2), [3, 4, 5, 6, 7, 8, 9, 10], Math.sqrt(10), 10),
    Scale("L", "log x", "常用對數（線性，配合 D 刻度）", (x) => x, (u) => u, [...Array(11).keys()].map((k) => k / 10), 0, 1, { kind: "lin" }),
    Scale("Ln", "ln x", "自然對數（線性，配合 D 刻度）", (x) => x / LN10, (u) => u * LN10, [...Array(24).keys()].map((k) => k / 10), 0, LN10, { kind: "lin" }),
    Scale("S", "sin x", "正弦（5.74°～90°，配合 C／D）", (t) => lg(10 * Math.sin(rad(t))), (u) => deg(Math.asin(Math.min(1, Math.pow(10, u) / 10))),
      [5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90], deg(Math.asin(0.1)), 90, { kind: "trig", unit: "°" }),
    Scale("T", "tan x", "正切（5.71°～45°，配合 C／D）", (t) => lg(10 * Math.tan(rad(t))), (u) => deg(Math.atan(Math.pow(10, u) / 10)),
      [5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45], deg(Math.atan(0.1)), 45, { kind: "trig", unit: "°" }),
    Scale("T2", "tan x", "正切（45°～84.3°，配合 C／D）", (t) => lg(Math.tan(rad(t))), (u) => deg(Math.atan(Math.pow(10, u))),
      [45, 50, 55, 60, 65, 70, 75, 80, 85], 45, deg(Math.atan(10)), { kind: "trig", unit: "°" }),
    Scale("ST", "x (弧度)", "小角度正弦／正切（0.57°～5.73°）", (t) => lg(100 * rad(t)), (u) => deg(Math.pow(10, u) / 100),
      [0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6], deg(0.01), deg(0.1), { kind: "trig", unit: "°" }),
    Scale("P", "√(1−x²)", "畢氏刻度（由右到左）", (x) => lg(10 * Math.sqrt(Math.max(1e-300, 1 - x * x))), (u) => Math.sqrt(Math.max(0, 1 - Math.pow(Math.pow(10, u) / 10, 2))),
      [...Array(10).keys()].map((k) => k / 10).concat([0.92, 0.94, 0.96, 0.98, 0.99, 0.995]), 0, Math.sqrt(0.99), { color: "#C0392B", kind: "lin" }),
    Scale("LL1", "e^(0.01x)", "雙對數 1.01～1.105", (x) => lg(100 * Math.log(x)), (u) => Math.exp(Math.pow(10, u) / 100),
      [1.01, 1.015, 1.02, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09, 1.1, 1.11], Math.exp(0.01), Math.exp(0.1), { kind: "ll" }),
    Scale("LL2", "e^(0.1x)", "雙對數 1.105～2.718", (x) => lg(10 * Math.log(x)), (u) => Math.exp(Math.pow(10, u) / 10),
      [1.1, 1.15, 1.2, 1.25, 1.3, 1.4, 1.5, 1.6, 1.8, 2, 2.2, 2.5, 2.8], Math.exp(0.1), E, { kind: "ll", special: [[E, "e"]] }),
    Scale("LL3", "eˣ", "雙對數 2.718～22026", (x) => lg(Math.log(x)), (u) => Math.exp(Math.pow(10, u)),
      [2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 40, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000], E, Math.exp(10), { kind: "ll", special: [[E, "e"]] }),
    Scale("LL01", "e^(−0.01x)", "負雙對數 0.990～0.905", (x) => lg(-100 * Math.log(x)), (u) => Math.exp(-Math.pow(10, u) / 100),
      [0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 0.995], Math.exp(-0.1), Math.exp(-0.01), { color: "#C0392B", kind: "ll" }),
    Scale("LL02", "e^(−0.1x)", "負雙對數 0.905～0.368", (x) => lg(-10 * Math.log(x)), (u) => Math.exp(-Math.pow(10, u) / 10),
      [0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95], Math.exp(-1), Math.exp(-0.1), { color: "#C0392B", kind: "ll", special: [[1 / E, "1/e"]] }),
    Scale("LL03", "e^(−x)", "負雙對數 0.368～0.00005", (x) => lg(-Math.log(x)), (u) => Math.exp(-Math.pow(10, u)),
      [0.00001, 0.00005, 0.0001, 0.0005, 0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4], Math.exp(-10), Math.exp(-1), { color: "#C0392B", kind: "ll", special: [[1 / E, "1/e"]] }),
  ];
  const BY_KEY = {};
  SCALES.forEach((s) => { BY_KEY[s.key] = s; });

  const LAYOUTS = [
    ["student", "學生尺（基本）", ["A"], ["B", "CI", "C"], ["D", "K"], "最常見的單面學生尺：乘除、平方、立方、倒數"],
    ["basic", "乘除練習", [], ["C"], ["D"], "只有 C、D 兩個刻度，最適合初學乘法與除法"],
    ["trig", "三角函數", ["T", "T2"], ["C"], ["D", "S", "ST"], "正弦、正切、小角度"],
    ["power", "指數對數", ["LL1", "LL2", "LL3"], ["C"], ["D", "L", "Ln"], "eˣ、xʸ、常用與自然對數"],
    ["darmstadt", "達姆施塔特（工程）", ["L", "K", "A"], ["B", "CI", "C"], ["D", "P", "S", "T"], "德國經典工程尺：平方、立方、畢氏、三角"],
    ["folded", "π 摺疊（雙面）", ["DF"], ["CF", "CIF", "CI", "C"], ["D", "DI"], "摺疊刻度讓乘法少移動，乘 π 一步完成"],
    ["infinirule", "四刻度（Infinirule 風格）", ["DF"], ["CF", "C"], ["D"], "上面兩個一起動、下面的滑尺單獨動"],
  ];
  const LAYOUT_BY_KEY = {};
  LAYOUTS.forEach((l) => { LAYOUT_BY_KEY[l[0]] = l; });

  function nice(n) {
    if (!(n > 0) || !isFinite(n)) return false;
    const m = n / Math.pow(10, Math.floor(lg(n) + 1e-12));
    return NICE.some((k) => Math.abs(m - k) < 1e-6 || Math.abs(m - k * 10) < 1e-6);
  }
  const defLabelPx = (t) => 7.2 * t.length + 8;
  function markStep(marks, i) {
    if (i + 1 < marks.length) return Math.abs(marks[i + 1] - marks[i]);
    return i ? Math.abs(marks[i] - marks[i - 1]) : 1;
  }

  /** 看得到的範圍 [u0, u1] 內的刻度線：[{u, level, value, text}] */
  function ticks(scale, u0, u1, zoom, labelPx) {
    labelPx = labelPx || defLabelPx;
    const out = [];
    const lo = Math.min(scale.lo, scale.hi), hi = Math.max(scale.lo, scale.hi);
    const pos = scale.f;
    for (let k = Math.floor(u0); k <= Math.floor(u1); k++) {
      const a = u0 - k, b = u1 - k;
      if (b < 0 || a > 1) continue;
      const visible = (x0, x1) => {
        const p0 = pos(Math.max(lo, x0)), p1 = pos(Math.min(hi, x1));
        return Math.max(p0, p1) >= a - 1e-9 && Math.min(p0, p1) <= b + 1e-9;
      };
      const add = (x, level, step, labeled) => {
        if (x < lo - 1e-12 * Math.max(1, Math.abs(lo)) || x > hi + 1e-12 * Math.max(1, Math.abs(hi))) return;
        const p = pos(x);
        if ((p >= 1 - 1e-12 || p < -1e-12) && !(Math.abs(p) < 1e-12)) return;
        if (a - 1e-9 <= p && p <= b + 1e-9) out.push({ u: p + k, level, value: x, text: labeled ? scale.label(x, step) : "" });
      };
      const gap = (x0, x1) => Math.abs(pos(Math.max(lo, Math.min(hi, x1))) - pos(Math.max(lo, Math.min(hi, x0)))) * zoom;
      const sub = (x0, x1, level, depth) => {
        if (depth > 40 || !visible(x0, x1)) return;
        const w = x1 - x0;
        if (w <= 1e-13 * Math.max(1, Math.abs(x0))) return;
        for (const n of [10, 5, 4, 2]) {
          const step = w / n;
          if (!nice(step)) continue;
          const g = Math.min(gap(x0, x0 + step), gap(x1 - step, x1));
          if (g < MIN_PX) continue;
          const lab = g >= labelPx(scale.label(x1 - step, step)) * 1.15;
          for (let i = 1; i < n; i++) {
            const lv = level + (((n === 10 && i === 5) || (n === 4 && i === 2) || n === 2) ? 1 : 2);
            add(x0 + step * i, lv, step, lab);
          }
          for (let i = 0; i < n; i++) sub(x0 + step * i, x0 + step * (i + 1), level + 2, depth + 1);
          return;
        }
      };
      const marks = scale.marks;
      for (let i = 0; i < marks.length; i++) {
        add(marks[i], 0, markStep(marks, i), true);
        if (i + 1 < marks.length) sub(marks[i], marks[i + 1], 0, 0);
      }
      for (const [x, text] of scale.special) {
        if (lo <= x && x <= hi) {
          const p = pos(x);
          if (a <= p && p <= b) out.push({ u: p + k, level: -1, value: x, text });
        }
      }
    }
    out.sort((p, q) => p.u - q.u);
    return out;
  }

  /** 去掉互相重疊的數字（層級小的優先）：[{x, text, level}] */
  function placeLabels(tks, zoom, uLeft, labelPx) {
    labelPx = labelPx || defLabelPx;
    const cand = tks.filter((t) => t.text).sort((p, q) => (p.level - q.level) || (p.u - q.u));
    const taken = [], out = [];
    for (const t of cand) {
      const x = (t.u - uLeft) * zoom, w = labelPx(t.text) / 2 + 2;
      if (taken.some(([x2, w2]) => Math.abs(x - x2) < w + w2)) continue;
      taken.push([x, w]);
      out.push({ x, text: t.text, level: t.level });
    }
    return out;
  }

  function digitsFor(scale, u, zoom) {
    const du = 0.5 / Math.max(zoom, 1e-9);
    // 取左右兩邊較小的差（游標剛好在刻度頭尾時，另一邊會繞到下一圈）
    const x = scale.value(u);
    const dx = Math.min(Math.abs(scale.value(u + du) - x), Math.abs(x - scale.value(u - du))) / 2 || 1e-15;
    return Math.max(0, Math.min(14, -Math.floor(lg(dx))));
  }

  function reading(scale, u, zoom) {
    const x = scale.value(u);
    return [x, fixed(x, digitsFor(scale, u, zoom)) + scale.unit];
  }

  function mantissa(x) {
    if (x === 0) return [0, 0];
    const n = Math.floor(lg(Math.abs(x)));
    return [x / Math.pow(10, n), n];
  }

  G.SR = { LN10, SCALES, BY_KEY, LAYOUTS, LAYOUT_BY_KEY, ticks, placeLabels, digitsFor, reading, mantissa, trim };
})(window);
