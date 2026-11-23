/* 計算示範（sr/demo.py 的 JavaScript 版本）：算式 → 步驟（游標、滑尺、強調刻度、標記）。 */
(function (G) {
  "use strict";
  const R = G.SR, lg = Math.log10;
  const PRESETS = ["2×3.5", "7×3.5", "5.5÷2", "18÷7.2", "3.2²", "√2", "√20", "1.5³", "∛27", "1/8", "sin 30", "tan 60",
    "log 2", "ln 5", "e^2", "2^1.5"];

  function num(s) {
    s = s.trim().replace(/[，,]/g, "");
    if (s === "π" || s === "pi") return Math.PI;
    if (s === "e") return Math.E;
    if (!/^(\d+\.?\d*|\.\d+)$/.test(s)) throw new Error("看不懂這個數字：" + s);
    return parseFloat(s);
  }

  function sig(x, n) {
    n = n || 4;
    if (x === 0 || !isFinite(x)) return String(x);
    const d = n - 1 - Math.floor(lg(Math.abs(x)));
    let s;
    if (d >= 0) s = x.toFixed(d);
    else { const p = Math.pow(10, -d); s = (Math.round(x / p) * p).toFixed(0); }
    if (s.indexOf(".") >= 0) s = s.replace(/0+$/, "").replace(/\.$/, "");
    return s;
  }
  const sayNum = (x, n) => sig(x, n || 3);
  const rough = (x) => sig(x, 1);

  function parse(expr) {
    let t = (expr || "").trim().toLowerCase();
    t = t.replace(/([\d.π])\s*[x×]\s*(?=[\d.π])/g, "$1*").replace(/×/g, "*");
    t = t.replace(/÷/g, "/").replace(/＊/g, "*").replace(/／/g, "/").replace(/\*\*/g, "^").replace(/（/g, "(").replace(/）/g, ")");
    t = t.replace(/²/g, "^2").replace(/³/g, "^3").replace(/\s/g, "");
    let m;
    if ((m = t.match(/^(sin|cos|tan)\(?([\d.]+)°?\)?$/))) return [m[1], num(m[2]), null];
    if ((m = t.match(/^(log|lg|ln)\(?([\d.]+)\)?$/))) return [m[1] === "ln" ? "ln" : "log", num(m[2]), null];
    if ((m = t.match(/^(?:√|sqrt)\(?([\d.π]+)\)?$/))) return ["sqrt", num(m[1]), null];
    if ((m = t.match(/^(?:∛|cbrt)\(?([\d.π]+)\)?$/))) return ["cbrt", num(m[1]), null];
    if ((m = t.match(/^1\/([\d.π]+)$/))) return ["recip", num(m[1]), null];
    if ((m = t.match(/^(?:e\^|exp\()([\d.]+)\)?$/))) return ["exp", num(m[1]), null];
    if ((m = t.match(/^([\d.π]+)\^([\d.]+)$/))) {
      const a = num(m[1]), b = num(m[2]);
      if (b === 2) return ["sq", a, null];
      if (b === 3) return ["cube", a, null];
      return ["pow", a, b];
    }
    if ((m = t.match(/^([\d.π]+)\*([\d.π]+)$/))) return ["mul", num(m[1]), num(m[2])];
    if ((m = t.match(/^([\d.π]+)\/([\d.π]+)$/))) return ["div", num(m[1]), num(m[2])];
    throw new Error("看不懂這個算式。可以輸入：2×3.5、7÷2、3²、√2、1.5³、∛27、1/8、sin 30、tan 60、log 2、ln 5、e^2、2^1.5");
  }

  const step = (text, o) => Object.assign({ text, cursor: null, slide: null, hl: [], marks: [] }, o || {});

  function plan(expr) {
    const [op, a, b] = parse(expr);
    if ((a !== null && a <= 0 && !["sin", "cos", "tan"].includes(op)) || (b !== null && b <= 0 && op !== "pow"))
      throw new Error("計算尺只能算正數");
    const S = [], out = { expr: (expr || "").trim() };
    if (op === "mul") {
      const [ma] = R.mantissa(a), [mb] = R.mantissa(b), ua = lg(ma), ub = lg(mb), res = a * b;
      let mr = ma * mb; if (mr >= 10) mr /= 10;
      S.push(step(`乘法 ${sig(a)} 乘 ${sig(b)}。先把游標的紅色髮線移到下面 D 刻度的 ${sig(ma)}。`, { cursor: ua, hl: ["D"], marks: [["D", ua, ""]] }),
        step("拉動滑尺，讓滑尺上 C 刻度的 1 對準髮線。對數相加就是相乘。", { slide: ua, hl: ["C", "D"] }),
        step(`再把髮線移到 C 刻度的 ${sig(mb)}。`, { cursor: ua + ub, hl: ["C"], marks: [["C", ub, ""]] }),
        step(`在髮線下的 D 刻度讀出 ${sayNum(mr)}。`, { hl: ["D"], marks: [["D", lg(mr), ""]] }),
        step(`最後判斷小數點：${sig(a)} 乘 ${sig(b)} 大約是 ${rough(res)}，所以答案是 ${sayNum(res)}。`, { hl: ["D"] }));
      Object.assign(out, { layout: "basic", needs: ["C", "D"], result: res });
    } else if (op === "div") {
      const [ma] = R.mantissa(a), [mb] = R.mantissa(b), ua = lg(ma), ub = lg(mb), res = a / b, mr = R.mantissa(res)[0];
      S.push(step(`除法 ${sig(a)} 除以 ${sig(b)}。先把髮線移到 D 刻度的 ${sig(ma)}。`, { cursor: ua, hl: ["D"], marks: [["D", ua, ""]] }),
        step(`拉動滑尺，讓 C 刻度的 ${sig(mb)} 對準髮線。對數相減就是相除。`, { slide: ua - ub, hl: ["C", "D"], marks: [["C", ub, ""]] }),
        step("把髮線移到 C 刻度的 1，也就是滑尺的頭。", { cursor: ua - ub, hl: ["C"], marks: [["C", 0, ""]] }),
        step(`在 D 刻度讀出 ${sayNum(mr)}。`, { hl: ["D"], marks: [["D", lg(mr), ""]] }),
        step(`判斷小數點：${sig(a)} 除以 ${sig(b)} 大約是 ${rough(res)}，所以答案是 ${sayNum(res)}。`, { hl: ["D"] }));
      Object.assign(out, { layout: "basic", needs: ["C", "D"], result: res });
    } else if (op === "sq" || op === "sqrt") {
      const [m, n] = R.mantissa(a);
      let res;
      if (op === "sq") {
        res = a * a; const u = lg(m);
        S.push(step(`平方 ${sig(a)}。把髮線移到 D 刻度的 ${sig(m)}。`, { cursor: u, hl: ["D"], marks: [["D", u, ""]] }),
          step(`A 刻度是兩個循環的平方刻度，在髮線下的 A 刻度讀出 ${sayNum(m * m)}。`, { hl: ["A"], marks: [["A", u, ""]] }),
          step(`判斷小數點：${sig(a)} 的平方大約是 ${rough(res)}，所以答案是 ${sayNum(res)}。`, { hl: ["A"] }));
      } else {
        const av = ((n % 2) + 2) % 2 === 0 ? m : m * 10, u = lg(av) / 2;
        res = Math.sqrt(a);
        const half = av < 10 ? "左半邊" : "右半邊";
        S.push(step(`平方根 ${sig(a)}。A 刻度有兩個循環，${sig(a)} 要用 A 刻度${half}的 ${sig(av)}。先把髮線移過去。`, { cursor: u, hl: ["A"], marks: [["A", u, ""]] }),
          step(`在髮線下的 D 刻度讀出 ${sayNum(Math.sqrt(av))}。`, { hl: ["D"], marks: [["D", u, ""]] }),
          step(`判斷小數點：${sig(a)} 的平方根大約是 ${rough(res)}，所以答案是 ${sayNum(res)}。`, { hl: ["D"] }));
      }
      Object.assign(out, { layout: "student", needs: ["A", "D"], result: res });
    } else if (op === "cube" || op === "cbrt") {
      const [m, n] = R.mantissa(a);
      let res;
      if (op === "cube") {
        res = Math.pow(a, 3); const u = lg(m);
        S.push(step(`立方 ${sig(a)}。把髮線移到 D 刻度的 ${sig(m)}。`, { cursor: u, hl: ["D"], marks: [["D", u, ""]] }),
          step(`K 刻度是三個循環的立方刻度，在髮線下的 K 刻度讀出 ${sayNum(m * m * m)}。`, { hl: ["K"], marks: [["K", u, ""]] }),
          step(`判斷小數點：${sig(a)} 的立方大約是 ${rough(res)}，所以答案是 ${sayNum(res)}。`, { hl: ["K"] }));
      } else {
        const r3 = ((n % 3) + 3) % 3, kv = m * Math.pow(10, r3), u = lg(kv) / 3;
        res = Math.cbrt(a);
        S.push(step(`立方根 ${sig(a)}。K 刻度有三個循環，要找第 ${r3 + 1} 個循環的 ${sig(kv)}，把髮線移過去。`, { cursor: u, hl: ["K"], marks: [["K", u, ""]] }),
          step(`在髮線下的 D 刻度讀出 ${sayNum(Math.cbrt(kv))}。`, { hl: ["D"], marks: [["D", u, ""]] }),
          step(`判斷小數點：答案大約是 ${rough(res)}，所以是 ${sayNum(res)}。`, { hl: ["D"] }));
      }
      Object.assign(out, { layout: "student", needs: ["K", "D"], result: res });
    } else if (op === "recip") {
      const [m] = R.mantissa(a), u = lg(m), res = 1 / a;
      S.push(step(`倒數 1 除以 ${sig(a)}。滑尺歸零後，把髮線移到 C 刻度的 ${sig(m)}。`, { slide: 0, cursor: u, hl: ["C"], marks: [["C", u, ""]] }),
        step(`紅色的 CI 是倒數刻度，由右往左讀，在髮線下讀出 ${sayNum(R.mantissa(1 / m)[0])}。`, { hl: ["CI"], marks: [["CI", u, ""]] }),
        step(`判斷小數點：答案是 ${sayNum(res)}。`, { hl: ["CI"] }));
      Object.assign(out, { layout: "student", needs: ["C", "CI"], result: res });
    } else if (op === "sin" || op === "cos" || op === "tan") {
      let th = a, op2, res;
      const rad = (d) => d * Math.PI / 180;
      if (op === "cos") {
        const th2 = 90 - th; res = Math.cos(rad(th));
        S.push(step(`餘弦 ${sig(th)} 度等於正弦 ${sig(th2)} 度，所以改用正弦來算。`));
        th = th2; op2 = "sin";
      } else { op2 = op; res = op === "sin" ? Math.sin(rad(th)) : Math.tan(rad(th)); }
      if (op2 === "tan" && th >= 84.29) throw new Error("角度太大，正切超出刻度範圍（84.3 度以內）");
      if (!(th >= 0.573 && th <= 90)) throw new Error("角度要在 0.6～90 度之間");
      let key, div, nm;
      if (th < (op2 === "sin" ? 5.74 : 5.71)) [key, div, nm] = ["ST", 100, "小角度 ST"];
      else if (op2 === "sin") [key, div, nm] = ["S", 10, "正弦 S"];
      else if (th <= 45) [key, div, nm] = ["T", 10, "正切 T"];
      else [key, div, nm] = ["T2", 1, "正切 T2"];
      const u = R.BY_KEY[key].f(th), dv = Math.pow(10, u);
      S.push(step(`把髮線移到 ${nm} 刻度的 ${sig(th)} 度。`, { cursor: u, slide: 0, hl: [key], marks: [[key, u, ""]] }),
        step(`在髮線下的 D 刻度讀出 ${sayNum(dv)}。`, { hl: ["D"], marks: [["D", u, ""]] }),
        step(`${nm} 刻度的讀數要${{ 100: "除以 100", 10: "除以 10", 1: "直接用" }[div]}，所以答案是 ${sayNum(res)}。`, { hl: ["D"] }));
      Object.assign(out, { layout: "trig", needs: [key, "D"], result: res });
    } else if (op === "log" || op === "ln") {
      const [m, n] = R.mantissa(a), u = lg(m);
      let res;
      if (op === "log") {
        res = lg(a);
        S.push(step(`常用對數 log ${sig(a)}。把髮線移到 D 刻度的 ${sig(m)}。`, { cursor: u, hl: ["D"], marks: [["D", u, ""]] }),
          step(`線性的 L 刻度在髮線下讀出 ${sayNum(u, 3)}，這是對數的小數部分。`, { hl: ["L"], marks: [["L", u, ""]] }),
          step(`${sig(a)} 是 ${sig(m)} 乘以 10 的 ${n} 次方，所以整數部分是 ${n}，答案是 ${sayNum(res, 4)}。`, { hl: ["L"] }));
      } else {
        res = Math.log(a);
        S.push(step(`自然對數 ln ${sig(a)}。把髮線移到 D 刻度的 ${sig(m)}。`, { cursor: u, hl: ["D"], marks: [["D", u, ""]] }),
          step(`在 Ln 刻度讀出 ${sayNum(Math.log(m), 3)}，這是 ln ${sig(m)}。`, { hl: ["Ln"], marks: [["Ln", u, ""]] }),
          step(`再加上 ${n} 乘以 ln 10，也就是 ${sig(n * R.LN10, 4)}，答案是 ${sayNum(res, 4)}。`, { hl: ["Ln"] }));
      }
      Object.assign(out, { layout: "power", needs: ["D", "L", "Ln"], result: res });
    } else if (op === "exp") {
      const x = a;
      if (!(x >= 0.01 && x < 10)) throw new Error("e 的次方要在 0.01～10 之間（雙對數刻度的範圍）");
      const key = x >= 1 ? "LL3" : (x >= 0.1 ? "LL2" : "LL1"), mx = R.mantissa(x)[0], u = lg(mx), res = Math.exp(x);
      S.push(step(`e 的 ${sig(x)} 次方。把髮線移到 D 刻度的 ${sig(mx)}。`, { cursor: u, hl: ["D"], marks: [["D", u, ""]] }),
        step(`${sig(x)} 在 ${{ LL3: "1 到 10", LL2: "0.1 到 1", LL1: "0.01 到 0.1" }[key]} 的範圍，所以讀 ${key} 刻度：${sayNum(res)}。`, { hl: [key], marks: [[key, u, ""]] }),
        step(`雙對數刻度直接就是答案，不必判斷小數點：${sayNum(res)}。`, { hl: [key] }));
      Object.assign(out, { layout: "power", needs: ["D", key], result: res });
    } else if (op === "pow") {
      if (a <= 1) throw new Error("這裡示範底數大於 1 的次方（雙對數刻度 1.01～22026）");
      const la = Math.log(a), res = Math.pow(a, b), lr = b * la;
      if (!(la >= 0.01 && la < 10) || !(lr >= 0.01 && lr < 10)) throw new Error("超出雙對數刻度範圍（底數與答案都要在 1.01～22026 之間）");
      const llkey = (v) => v >= 1 ? "LL3" : (v >= 0.1 ? "LL2" : "LL1");
      const ka = llkey(la), kr = llkey(lr), ua = lg(R.mantissa(la)[0]), ub = lg(R.mantissa(b)[0]);
      S.push(step(`次方 ${sig(a)} 的 ${sig(b)} 次方。先把髮線移到雙對數 ${ka} 刻度的 ${sig(a)}。`, { cursor: ua, hl: [ka], marks: [[ka, ua, ""]] }),
        step("拉動滑尺，讓 C 刻度的 1 對準髮線。", { slide: ua, hl: ["C", ka] }),
        step(`把髮線移到 C 刻度的 ${sig(R.mantissa(b)[0])}。`, { cursor: ua + ub, hl: ["C"], marks: [["C", ub, ""]] }),
        step(`答案在 ${kr} 刻度上，讀出 ${sayNum(res)}。`, { hl: [kr], marks: [[kr, ua + ub, ""]] }));
      Object.assign(out, { layout: "power", needs: ["C", "LL1", "LL2", "LL3"], result: res });
    } else throw new Error("不支援的算式");
    out.steps = S;
    out.exact = out.result;
    out.result_text = sayNum(out.result, (op === "log" || op === "ln") ? 4 : 3);
    out.exact_text = sig(out.exact, 8);
    return out;
  }

  // 讀尺練習出題（sr/rulebiz.py make_problem）
  function rnd(a, b, n) {         // a～b 之間、有效數字 n 位（計算尺好讀的數字），不出 1、10、100
    for (;;) {
      const x = +sig(a + Math.random() * (b - a), n || 2);
      if (x >= a && x <= b && x !== 1 && x !== 10 && x !== 100) return x;
    }
  }
  const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
  const fmt = (x) => sig(x, 6);
  const DRILL_KINDS = [["MUL", "乘法"], ["DIV", "除法"], ["POW", "平方根號立方"], ["RECIP", "倒數"], ["TRIG", "三角函數"],
    ["LOG", "對數指數"], ["MIX", "綜合"]];
  function makeProblem(kind) {
    const k = kind !== "MIX" ? kind : pick(["MUL", "MUL", "DIV", "DIV", "POW", "RECIP", "TRIG", "LOG"]);
    if (k === "MUL") {
      const a = +sig(rnd(1.1, 9.9) * pick([1, 1, 10, 0.1]), 2), b = +sig(rnd(1.1, 9.9) * pick([1, 1, 10]), 2);
      return [`${fmt(a)}×${fmt(b)}`, a * b, k];
    }
    if (k === "DIV") {
      const a = +sig(rnd(1.1, 9.9) * pick([1, 10, 100]), 3), b = rnd(1.1, 9.9);
      return [`${fmt(a)}÷${fmt(b)}`, a / b, k];
    }
    if (k === "POW") {
      const t = pick(["sq", "sqrt", "cube", "cbrt"]);
      if (t === "sq") { const a = rnd(1.1, 9.9); return [`${fmt(a)}²`, a * a, k]; }
      if (t === "sqrt") { const a = rnd(2, 99); return [`√${fmt(a)}`, Math.sqrt(a), k]; }
      if (t === "cube") { const a = rnd(1.1, 4.9); return [`${fmt(a)}³`, a * a * a, k]; }
      const a = rnd(2, 900); return [`∛${fmt(a)}`, Math.cbrt(a), k];
    }
    if (k === "RECIP") { const a = rnd(1.1, 9.9, 3); return [`1/${fmt(a)}`, 1 / a, k]; }
    if (k === "TRIG") {
      const t = pick(["sin", "cos", "tan"]), th = t !== "tan" ? 8 + Math.floor(Math.random() * 73) : 8 + Math.floor(Math.random() * 68);
      return [`${t} ${th}`, Math[t](th * Math.PI / 180), k];
    }
    const t = pick(["log", "ln", "exp"]);
    if (t === "log") { const a = rnd(1.1, 99); return [`log ${fmt(a)}`, lg(a), k]; }
    if (t === "ln") { const a = rnd(1.1, 99); return [`ln ${fmt(a)}`, Math.log(a), k]; }
    const x = rnd(0.2, 5, 2); return [`e^${fmt(x)}`, Math.exp(x), k];
  }

  G.SRDemo = { PRESETS, parse, plan, sig, makeProblem, DRILL_KINDS };
})(window);
