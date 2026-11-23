"""計算示範：把算式拆成「移動游標、拉滑尺、讀刻度」的步驟，並在計算尺上邊講邊動給使用者看。

plan(算式) → {"expr", "steps": [{"text", "cursor", "slide", "hl", "marks"}], "layout", "needs",
              "result", "result_text", "exact", "exact_text"}
支援：a×b、a÷b、x²、√x、x³、∛x、1/x、sin θ、cos θ、tan θ（度）、log x、ln x、e^x、a^b
"""
import math
import os
import re
import time

from . import rule as R

PRESETS = ["2×3.5", "7×3.5", "5.5÷2", "18÷7.2", "3.2²", "√2", "√20", "1.5³", "∛27", "1/8", "sin 30", "tan 60",
           "log 2", "ln 5", "e^2", "2^1.5"]

lg = math.log10


def _num(s):
    s = s.strip().replace("，", "").replace(",", "")
    if s in ("π", "pi"):
        return math.pi
    if s == "e":
        return math.e
    try:
        return float(s)
    except ValueError:
        raise ValueError("看不懂這個數字：%s" % s)


def sig(x, n=4):
    """有效數字 n 位的文字（去掉多餘的 0）。"""
    if x == 0 or not math.isfinite(x):
        return str(x)
    d = n - 1 - math.floor(lg(abs(x)))
    s = "%.*f" % (max(0, d), round(x, d))
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def say_num(x, n=3):
    return sig(x, n)


def _rough(x):
    """估算用的「大約」數字：一位有效數字。"""
    return sig(x, 1)


def parse(expr):
    t = (expr or "").strip().lower()
    t = re.sub(r"(?<=[\d.π])\s*[x×]\s*(?=[\d.π])", "*", t).replace("×", "*")
    t = t.replace("÷", "/").replace("＊", "*").replace("／", "/").replace("**", "^").replace("（", "(").replace("）", ")")
    t = t.replace("²", "^2").replace("³", "^3").replace(" ", "")
    m = re.fullmatch(r"(sin|cos|tan)\(?([\d.]+)°?\)?", t)
    if m:
        return m.group(1), _num(m.group(2)), None
    m = re.fullmatch(r"(log|lg|ln)\(?([\d.]+)\)?", t)
    if m:
        return ("log" if m.group(1) in ("log", "lg") else "ln"), _num(m.group(2)), None
    m = re.fullmatch(r"(?:√|sqrt)\(?([\d.π]+)\)?", t)
    if m:
        return "sqrt", _num(m.group(1)), None
    m = re.fullmatch(r"(?:∛|cbrt)\(?([\d.π]+)\)?", t)
    if m:
        return "cbrt", _num(m.group(1)), None
    m = re.fullmatch(r"1/([\d.π]+)", t)
    if m:
        return "recip", _num(m.group(1)), None
    m = re.fullmatch(r"(?:e\^|exp\()([\d.]+)\)?", t)
    if m:
        return "exp", _num(m.group(1)), None
    m = re.fullmatch(r"([\d.π]+)\^([\d.]+)", t)
    if m:
        a, b = _num(m.group(1)), _num(m.group(2))
        if b == 2:
            return "sq", a, None
        if b == 3:
            return "cube", a, None
        return "pow", a, b
    m = re.fullmatch(r"([\d.π]+)\*([\d.π]+)", t)
    if m:
        return "mul", _num(m.group(1)), _num(m.group(2))
    m = re.fullmatch(r"([\d.π]+)/([\d.π]+)", t)
    if m:
        return "div", _num(m.group(1)), _num(m.group(2))
    raise ValueError("看不懂這個算式。可以輸入：2×3.5、7÷2、3²、√2、1.5³、∛27、1/8、sin 30、tan 60、log 2、ln 5、e^2、2^1.5")


def _step(text, cursor=None, slide=None, hl=(), marks=()):
    return {"text": text, "cursor": cursor, "slide": slide, "hl": list(hl), "marks": list(marks)}


def plan(expr):
    op, a, b = parse(expr)
    if (a is not None and a <= 0 and op not in ("sin", "cos", "tan")) or (b is not None and b <= 0 and op != "pow"):
        raise ValueError("計算尺只能算正數")
    S = []
    out = {"expr": (expr or "").strip()}
    if op == "mul":
        ma, na = R.mantissa(a)
        mb, nb = R.mantissa(b)
        ua, ub = lg(ma), lg(mb)
        res = a * b
        mr = ma * mb
        mr = mr / 10 if mr >= 10 else mr
        S += [_step("乘法 %s 乘 %s。先把游標的紅色髮線移到下面 D 刻度的 %s。" % (sig(a), sig(b), sig(ma)),
                    cursor=ua, hl=["D"], marks=[("D", ua, "")]),
              _step("拉動滑尺，讓滑尺上 C 刻度的 1 對準髮線。對數相加就是相乘。", slide=ua, hl=["C", "D"]),
              _step("再把髮線移到 C 刻度的 %s。" % sig(mb), cursor=ua + ub, hl=["C"], marks=[("C", ub, "")]),
              _step("在髮線下的 D 刻度讀出 %s。" % say_num(mr), hl=["D"], marks=[("D", lg(mr), "")]),
              _step("最後判斷小數點：%s 乘 %s 大約是 %s，所以答案是 %s。" % (sig(a), sig(b), _rough(res), say_num(res)),
                    hl=["D"])]
        out.update(layout="basic", needs=["C", "D"], result=res)
    elif op == "div":
        ma, _ = R.mantissa(a)
        mb, _ = R.mantissa(b)
        ua, ub = lg(ma), lg(mb)
        res = a / b
        mr = R.mantissa(res)[0]
        S += [_step("除法 %s 除以 %s。先把髮線移到 D 刻度的 %s。" % (sig(a), sig(b), sig(ma)),
                    cursor=ua, hl=["D"], marks=[("D", ua, "")]),
              _step("拉動滑尺，讓 C 刻度的 %s 對準髮線。對數相減就是相除。" % sig(mb), slide=ua - ub, hl=["C", "D"],
                    marks=[("C", ub, "")]),
              _step("把髮線移到 C 刻度的 1，也就是滑尺的頭。", cursor=ua - ub, hl=["C"], marks=[("C", 0.0, "")]),
              _step("在 D 刻度讀出 %s。" % say_num(mr), hl=["D"], marks=[("D", lg(mr), "")]),
              _step("判斷小數點：%s 除以 %s 大約是 %s，所以答案是 %s。" % (sig(a), sig(b), _rough(res), say_num(res)),
                    hl=["D"])]
        out.update(layout="basic", needs=["C", "D"], result=res)
    elif op in ("sq", "sqrt"):
        if op == "sq":
            m, n = R.mantissa(a)
            res = a * a
            u = lg(m)
            S += [_step("平方 %s。把髮線移到 D 刻度的 %s。" % (sig(a), sig(m)), cursor=u, hl=["D"], marks=[("D", u, "")]),
                  _step("A 刻度是兩個循環的平方刻度，在髮線下的 A 刻度讀出 %s。" % say_num(m * m), hl=["A"],
                        marks=[("A", u, "")]),
                  _step("判斷小數點：%s 的平方大約是 %s，所以答案是 %s。" % (sig(a), _rough(res), say_num(res)), hl=["A"])]
        else:
            m, n = R.mantissa(a)
            av = m if n % 2 == 0 else m * 10          # 偶數位用 A 的左半、奇數位用右半
            u = lg(av) / 2
            res = math.sqrt(a)
            half = "左半邊" if av < 10 else "右半邊"
            S += [_step("平方根 %s。A 刻度有兩個循環，%s 要用 A 刻度%s的 %s。先把髮線移過去。" % (sig(a), sig(a), half, sig(av)),
                        cursor=u, hl=["A"], marks=[("A", u, "")]),
                  _step("在髮線下的 D 刻度讀出 %s。" % say_num(math.sqrt(av)), hl=["D"], marks=[("D", u, "")]),
                  _step("判斷小數點：%s 的平方根大約是 %s，所以答案是 %s。" % (sig(a), _rough(res), say_num(res)), hl=["D"])]
        out.update(layout="student", needs=["A", "D"], result=res)
    elif op in ("cube", "cbrt"):
        if op == "cube":
            m, n = R.mantissa(a)
            res = a ** 3
            u = lg(m)
            S += [_step("立方 %s。把髮線移到 D 刻度的 %s。" % (sig(a), sig(m)), cursor=u, hl=["D"], marks=[("D", u, "")]),
                  _step("K 刻度是三個循環的立方刻度，在髮線下的 K 刻度讀出 %s。" % say_num(m ** 3), hl=["K"],
                        marks=[("K", u, "")]),
                  _step("判斷小數點：%s 的立方大約是 %s，所以答案是 %s。" % (sig(a), _rough(res), say_num(res)), hl=["K"])]
        else:
            m, n = R.mantissa(a)
            kv = m * 10 ** (n % 3)
            u = lg(kv) / 3
            res = a ** (1 / 3)
            S += [_step("立方根 %s。K 刻度有三個循環，要找第 %d 個循環的 %s，把髮線移過去。" % (sig(a), n % 3 + 1, sig(kv)),
                        cursor=u, hl=["K"], marks=[("K", u, "")]),
                  _step("在髮線下的 D 刻度讀出 %s。" % say_num(kv ** (1 / 3)), hl=["D"], marks=[("D", u, "")]),
                  _step("判斷小數點：答案大約是 %s，所以是 %s。" % (_rough(res), say_num(res)), hl=["D"])]
        out.update(layout="student", needs=["K", "D"], result=res)
    elif op == "recip":
        m, n = R.mantissa(a)
        u = lg(m)
        res = 1 / a
        S += [_step("倒數 1 除以 %s。滑尺歸零後，把髮線移到 C 刻度的 %s。" % (sig(a), sig(m)), slide=0.0, cursor=u,
                    hl=["C"], marks=[("C", u, "")]),
              _step("紅色的 CI 是倒數刻度，由右往左讀，在髮線下讀出 %s。" % say_num(R.mantissa(1 / m)[0]), hl=["CI"],
                    marks=[("CI", u, "")]),
              _step("判斷小數點：答案是 %s。" % say_num(res), hl=["CI"])]
        out.update(layout="student", needs=["C", "CI"], result=res)
    elif op in ("sin", "cos", "tan"):
        th = a
        if op == "cos":
            th2 = 90 - th
            res = math.cos(math.radians(th))
            S.append(_step("餘弦 %s 度等於正弦 %s 度，所以改用正弦來算。" % (sig(th), sig(th2)), hl=[]))
            th, op2 = th2, "sin"
        else:
            op2 = op
            res = math.sin(math.radians(th)) if op == "sin" else math.tan(math.radians(th))
        if op2 == "tan" and th >= 84.29:
            raise ValueError("角度太大，正切超出刻度範圍（84.3 度以內）")
        if not 0.573 <= th <= 90:
            raise ValueError("角度要在 0.6～90 度之間")
        if th < (5.74 if op2 == "sin" else 5.71):
            key, div, nm = "ST", 100, "小角度 ST"
        elif op2 == "sin":
            key, div, nm = "S", 10, "正弦 S"
        elif th <= 45:
            key, div, nm = "T", 10, "正切 T"
        else:
            key, div, nm = "T2", 1, "正切 T2"
        u = R.BY_KEY[key].f(th)
        dv = 10 ** u
        S += [_step("把髮線移到 %s 刻度的 %s 度。" % (nm, sig(th)), cursor=u, slide=0.0, hl=[key], marks=[(key, u, "")]),
              _step("在髮線下的 D 刻度讀出 %s。" % say_num(dv), hl=["D"], marks=[("D", u, "")]),
              _step("%s 刻度的讀數要%s，所以答案是 %s。" % (nm, {100: "除以 100", 10: "除以 10", 1: "直接用"}[div],
                                                say_num(res)), hl=["D"])]
        out.update(layout="trig", needs=[key, "D"], result=res)
    elif op in ("log", "ln"):
        m, n = R.mantissa(a)
        u = lg(m)
        if op == "log":
            res = lg(a)
            S += [_step("常用對數 log %s。把髮線移到 D 刻度的 %s。" % (sig(a), sig(m)), cursor=u, hl=["D"],
                        marks=[("D", u, "")]),
                  _step("線性的 L 刻度在髮線下讀出 %s，這是對數的小數部分。" % say_num(u, 3), hl=["L"], marks=[("L", u, "")]),
                  _step("%s 是 %s 乘以 10 的 %d 次方，所以整數部分是 %d，答案是 %s。" % (sig(a), sig(m), n, n, say_num(res, 4)),
                        hl=["L"])]
        else:
            res = math.log(a)
            S += [_step("自然對數 ln %s。把髮線移到 D 刻度的 %s。" % (sig(a), sig(m)), cursor=u, hl=["D"],
                        marks=[("D", u, "")]),
                  _step("在 Ln 刻度讀出 %s，這是 ln %s。" % (say_num(math.log(m), 3), sig(m)), hl=["Ln"], marks=[("Ln", u, "")]),
                  _step("再加上 %d 乘以 ln 10，也就是 %s，答案是 %s。" % (n, sig(n * R.LN10, 4), say_num(res, 4)), hl=["Ln"])]
        out.update(layout="power", needs=["D", "L", "Ln"], result=res)
    elif op == "exp":
        x = a
        if not 0.01 <= x < 10:
            raise ValueError("e 的次方要在 0.01～10 之間（雙對數刻度的範圍）")
        key = "LL3" if x >= 1 else ("LL2" if x >= 0.1 else "LL1")
        u = lg(R.mantissa(x)[0])
        res = math.exp(x)
        S += [_step("e 的 %s 次方。把髮線移到 D 刻度的 %s。" % (sig(x), sig(R.mantissa(x)[0])), cursor=u, hl=["D"],
                    marks=[("D", u, "")]),
              _step("%s 在 %s 的範圍，所以讀 %s 刻度：%s。" % (sig(x), {"LL3": "1 到 10", "LL2": "0.1 到 1", "LL1": "0.01 到 0.1"}[key],
                                                    key, say_num(res)), hl=[key], marks=[(key, u, "")]),
              _step("雙對數刻度直接就是答案，不必判斷小數點：%s。" % say_num(res), hl=[key])]
        out.update(layout="power", needs=["D", key], result=res)
    elif op == "pow":
        if a <= 1:
            raise ValueError("這裡示範底數大於 1 的次方（雙對數刻度 1.01～22026）")
        la = math.log(a)
        res = a ** b
        lr = b * la
        if not 0.01 <= la < 10 or not 0.01 <= lr < 10:
            raise ValueError("超出雙對數刻度範圍（底數與答案都要在 1.01～22026 之間）")

        def llkey(v):
            return "LL3" if v >= 1 else ("LL2" if v >= 0.1 else "LL1")
        ka, kr = llkey(la), llkey(lr)
        ua = lg(R.mantissa(la)[0])
        ub = lg(R.mantissa(b)[0])
        S += [_step("次方 %s 的 %s 次方。先把髮線移到雙對數 %s 刻度的 %s。" % (sig(a), sig(b), ka, sig(a)), cursor=ua,
                    hl=[ka], marks=[(ka, ua, "")]),
              _step("拉動滑尺，讓 C 刻度的 1 對準髮線。", slide=ua, hl=["C", ka]),
              _step("把髮線移到 C 刻度的 %s。" % sig(R.mantissa(b)[0]), cursor=ua + ub, hl=["C"], marks=[("C", ub, "")]),
              _step("答案在 %s 刻度上，讀出 %s。" % (kr, say_num(res)), hl=[kr], marks=[(kr, ua + ub, "")])]
        out.update(layout="power", needs=["C", "LL1", "LL2", "LL3"], result=res)
    else:
        raise ValueError("不支援的算式")
    out["steps"] = S
    out["exact"] = out["result"]
    out["result_text"] = say_num(out["result"], 3 if op not in ("log", "ln") else 4)
    out["exact_text"] = sig(out["exact"], 8)
    return out


class Demo:
    """在背景執行緒裡依序：亮起步驟、語音、移動計算尺。"""

    def __init__(self, rv, pl, on_step, ctx, on_done=None):
        self.rv, self.pl, self.on_step, self.ctx, self.on_done = rv, pl, on_step, ctx, on_done
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def stopped(self):
        return self.cancelled

    def run(self):
        from .voice import speaker
        web = bool(getattr(self.ctx, "web", False))
        # 先把每一步的語音都準備好（第一次需要網路，之後有快取）
        mp3s = []
        if not web and not os.environ.get("SR_NO_VOICE"):
            for s in self.pl["steps"]:
                if self.cancelled:
                    return
                mp3s.append(speaker._neural(s["text"]))
        rv = self.rv
        for i, s in enumerate(self.pl["steps"]):
            if self.cancelled:
                return
            self.on_step(i, self.pl)
            rv.highlight = set(s["hl"])
            rv.marks = s["marks"]
            rv._names()
            rv.redraw(all_parts=True)
            t0 = time.time()
            if i < len(mp3s) and mp3s[i]:
                speaker.play_file(mp3s[i])
            target_left = None
            if s["cursor"] is not None:
                c = s["cursor"] + round(rv.st.cursor - s["cursor"])
                target_left = rv.ensure_visible(c)
            rv.animate_to(slide=s["slide"], cursor=s["cursor"], left=target_left, seconds=1.0, stop=self.stopped)
            # 等語音講完（沒有語音時依字數估計）
            limit = t0 + max(2.0, len(s["text"]) / 4.6) + (30 if mp3s and i < len(mp3s) and mp3s[i] else 0)
            while not self.cancelled and time.time() < limit:
                if mp3s and i < len(mp3s) and mp3s[i]:
                    if time.time() - t0 > 1.2 and not speaker.playing():
                        break
                time.sleep(0.15)
            time.sleep(0.25)
        if not self.cancelled and self.on_done:
            self.on_done(self.pl)
