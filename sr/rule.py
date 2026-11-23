"""計算尺引擎（純數學，不含畫面）：刻度定義、刻度線產生、讀數。

座標：一把尺的長度＝1「單位」（u）。每一種刻度把數值 x 對應到 0 ≤ u < 1，
並且每 1 單位重複一次（自動環繞，像圓形計算尺），所以乘法永遠不會「超出尺外」。

* 對數刻度（C、D、A、B、K…）：u＝log10(x) 的小數部分，例如 2、20、0.2 都在同一個位置，
  小數點位置由使用者自己判斷（和真的計算尺一樣）。
* 放大（zoom）＝每單位幾個像素；放得越大，刻度線分得越細、讀數位數越多（無限精度）。

刻度線產生：每個刻度有「主刻度值」清單，相鄰兩個主刻度之間依目前放大倍率，
遞迴分成 10、5、4 或 2 等分，直到刻度線間距小於 MIN_PX 像素為止；只計算看得到的範圍。
"""
import math
from dataclasses import dataclass, field

LN10 = math.log(10)
MIN_PX = 6.0           # 刻度線最小間距（像素）
NICE = (1.0, 2.0, 2.5, 5.0)


def _frac(u):
    return u - math.floor(u)


@dataclass
class Scale:
    key: str                     # 傳統代號：C、D、CI…
    formula: str                 # 公式寫法（像 Infinirule 用公式當名稱）：x、1/x、x²…
    name: str                    # 中文說明
    f: object                    # 數值 → u（0～1）
    g: object                    # u（0～1）→ 數值
    marks: list                  # 主刻度數值（依數值大小排序）
    lo: float = 0.0              # 這一圈的數值範圍（數值較小的一端）
    hi: float = 1.0
    color: str = "#1F2937"       # 刻度顏色（倒數刻度慣用紅色）
    kind: str = "log"            # log 對數、lin 線性、trig 三角、ll 指數
    unit: str = ""               # 讀數單位（°）
    special: list = field(default_factory=list)   # 特殊記號 [(數值, 文字)]：π、e…

    def u(self, x):
        return self.f(x)

    def value(self, u):
        return self.g(_frac(u))

    def label(self, x, step):
        """刻度上的數字：依這一層刻度的間距決定小數位數。"""
        if self.key in ("S", "T", "T2", "ST"):
            d = max(0, -math.floor(math.log10(step) + 1e-9)) if step < 1 else 0
            return _trim("%.*f" % (d, x))
        d = max(0, -math.floor(math.log10(step) + 1e-9)) if step < 1 else 0
        if abs(x) >= 1e4:
            return "%g" % x
        return _trim("%.*f" % (d, x))


def _trim(s):
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s.startswith("0.") and len(s) > 2:
        s = s[1:]                 # 0.5 → .5（刻度上的習慣寫法，比較省空間）
    if s.startswith("-0."):
        s = "-" + s[2:]
    return s or "0"


def _log_marks(lo_exp, hi_exp):
    out = []
    for e in range(lo_exp, hi_exp):
        out += [k * 10 ** e for k in range(1, 10)]
    out.append(10 ** hi_exp)
    return out


def _mk_scales():
    lg = math.log10
    S = []
    # ---------------------------------------------------------------- 基本對數刻度
    S.append(Scale("C", "x", "基本刻度（滑尺）", lambda x: lg(x), lambda u: 10 ** u, _log_marks(0, 1), 1, 10,
                   special=[(math.pi, "π")]))
    S.append(Scale("D", "x", "基本刻度（定尺）", lambda x: lg(x), lambda u: 10 ** u, _log_marks(0, 1), 1, 10,
                   special=[(math.pi, "π")]))
    S.append(Scale("CI", "1/x", "倒數刻度（滑尺，由右到左）", lambda x: 1 - lg(x), lambda u: 10 ** (1 - u),
                   _log_marks(0, 1), 1, 10, color="#C0392B"))
    S.append(Scale("DI", "1/x", "倒數刻度（定尺，由右到左）", lambda x: 1 - lg(x), lambda u: 10 ** (1 - u),
                   _log_marks(0, 1), 1, 10, color="#C0392B"))
    pi = math.pi
    folded = [k for k in (3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35)]
    S.append(Scale("CF", "πx", "π 摺疊刻度（滑尺）", lambda x: lg(x / pi), lambda u: pi * 10 ** u, folded, pi, 10 * pi,
                   special=[(pi, "π")]))
    S.append(Scale("DF", "πx", "π 摺疊刻度（定尺）", lambda x: lg(x / pi), lambda u: pi * 10 ** u, folded, pi, 10 * pi,
                   special=[(pi, "π")]))
    S.append(Scale("CIF", "1/(πx)", "π 摺疊倒數刻度", lambda x: 1 - lg(x / pi), lambda u: pi * 10 ** (1 - u),
                   folded, pi, 10 * pi, color="#C0392B"))
    S.append(Scale("A", "x²", "平方刻度（定尺；兩個循環）", lambda x: lg(x) / 2, lambda u: 10 ** (2 * u),
                   _log_marks(0, 2), 1, 100, special=[(pi, "π")]))
    S.append(Scale("B", "x²", "平方刻度（滑尺；兩個循環）", lambda x: lg(x) / 2, lambda u: 10 ** (2 * u),
                   _log_marks(0, 2), 1, 100, special=[(pi, "π")]))
    S.append(Scale("K", "x³", "立方刻度（三個循環）", lambda x: lg(x) / 3, lambda u: 10 ** (3 * u),
                   _log_marks(0, 3), 1, 1000))
    S.append(Scale("R1", "√x", "平方根刻度（1～3.16）", lambda x: 2 * lg(x), lambda u: 10 ** (u / 2),
                   [1, 1.5, 2, 2.5, 3, 3.5], 1, 10 ** 0.5))
    S.append(Scale("R2", "√10x", "平方根刻度（3.16～10）", lambda x: 2 * lg(x) - 1, lambda u: 10 ** ((u + 1) / 2),
                   [3, 4, 5, 6, 7, 8, 9, 10], 10 ** 0.5, 10))
    # ---------------------------------------------------------------- 線性刻度
    S.append(Scale("L", "log x", "常用對數（線性，配合 D 刻度）", lambda x: x, lambda u: u,
                   [k / 10 for k in range(11)], 0, 1, kind="lin"))
    S.append(Scale("Ln", "ln x", "自然對數（線性，配合 D 刻度）", lambda x: x / LN10, lambda u: u * LN10,
                   [k / 10 for k in range(24)], 0, LN10, kind="lin"))
    # ---------------------------------------------------------------- 三角刻度（角度，十進位度數）
    rad = math.radians
    S.append(Scale("S", "sin x", "正弦（5.74°～90°，配合 C／D）", lambda t: lg(10 * math.sin(rad(t))),
                   lambda u: math.degrees(math.asin(min(1.0, 10 ** u / 10))),
                   [5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90], math.degrees(math.asin(0.1)), 90,
                   kind="trig", unit="°"))
    S.append(Scale("T", "tan x", "正切（5.71°～45°，配合 C／D）", lambda t: lg(10 * math.tan(rad(t))),
                   lambda u: math.degrees(math.atan(10 ** u / 10)),
                   [5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45], math.degrees(math.atan(0.1)), 45,
                   kind="trig", unit="°"))
    S.append(Scale("T2", "tan x", "正切（45°～84.3°，配合 C／D）", lambda t: lg(math.tan(rad(t))),
                   lambda u: math.degrees(math.atan(10 ** u)),
                   [45, 50, 55, 60, 65, 70, 75, 80, 85], 45, math.degrees(math.atan(10)), kind="trig", unit="°"))
    S.append(Scale("ST", "x (弧度)", "小角度正弦／正切（0.57°～5.73°）", lambda t: lg(100 * rad(t)),
                   lambda u: math.degrees(10 ** u / 100),
                   [0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6],
                   math.degrees(0.01), math.degrees(0.1), kind="trig", unit="°"))
    S.append(Scale("P", "√(1−x²)", "畢氏刻度（由右到左）", lambda x: lg(10 * math.sqrt(max(1e-300, 1 - x * x))),
                   lambda u: math.sqrt(max(0.0, 1 - (10 ** u / 10) ** 2)),
                   [k / 10 for k in range(10)] + [0.92, 0.94, 0.96, 0.98, 0.99, 0.995], 0, math.sqrt(0.99),
                   color="#C0392B", kind="lin"))
    # ---------------------------------------------------------------- 雙對數刻度（eˣ）
    ln = math.log
    S.append(Scale("LL1", "e^(0.01x)", "雙對數 1.01～1.105", lambda x: lg(100 * ln(x)), lambda u: math.exp(10 ** u / 100),
                   [1.01, 1.015, 1.02, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09, 1.1, 1.11], math.exp(0.01),
                   math.exp(0.1), kind="ll"))
    S.append(Scale("LL2", "e^(0.1x)", "雙對數 1.105～2.718", lambda x: lg(10 * ln(x)), lambda u: math.exp(10 ** u / 10),
                   [1.1, 1.15, 1.2, 1.25, 1.3, 1.4, 1.5, 1.6, 1.8, 2, 2.2, 2.5, 2.8], math.exp(0.1), math.e,
                   kind="ll", special=[(math.e, "e")]))
    S.append(Scale("LL3", "eˣ", "雙對數 2.718～22026", lambda x: lg(ln(x)), lambda u: math.exp(10 ** u),
                   [2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 40, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000],
                   math.e, math.exp(10), kind="ll", special=[(math.e, "e")]))
    S.append(Scale("LL01", "e^(−0.01x)", "負雙對數 0.990～0.905", lambda x: lg(-100 * ln(x)),
                   lambda u: math.exp(-(10 ** u) / 100),
                   [0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 0.995], math.exp(-0.1), math.exp(-0.01),
                   color="#C0392B", kind="ll"))
    S.append(Scale("LL02", "e^(−0.1x)", "負雙對數 0.905～0.368", lambda x: lg(-10 * ln(x)),
                   lambda u: math.exp(-(10 ** u) / 10),
                   [0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95], math.exp(-1),
                   math.exp(-0.1), color="#C0392B", kind="ll", special=[(1 / math.e, "1/e")]))
    S.append(Scale("LL03", "e^(−x)", "負雙對數 0.368～0.00005", lambda x: lg(-ln(x)), lambda u: math.exp(-(10 ** u)),
                   [0.00001, 0.00005, 0.0001, 0.0005, 0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4],
                   math.exp(-10), math.exp(-1), color="#C0392B", kind="ll", special=[(1 / math.e, "1/e")]))
    return S


SCALES = _mk_scales()
BY_KEY = {s.key: s for s in SCALES}

# 常見尺型：(代號, 名稱, 上定尺, 滑尺, 下定尺, 說明)
LAYOUTS = [
    ("student", "學生尺（基本）", ["A"], ["B", "CI", "C"], ["D", "K"], "最常見的單面學生尺：乘除、平方、立方、倒數"),
    ("basic", "乘除練習", [], ["C"], ["D"], "只有 C、D 兩個刻度，最適合初學乘法與除法"),
    ("trig", "三角函數", ["T", "T2"], ["C"], ["D", "S", "ST"], "正弦、正切、小角度"),
    ("power", "指數對數", ["LL1", "LL2", "LL3"], ["C"], ["D", "L", "Ln"], "eˣ、xʸ、常用與自然對數"),
    ("darmstadt", "達姆施塔特（工程）", ["L", "K", "A"], ["B", "CI", "C"], ["D", "P", "S", "T"],
     "德國經典工程尺：平方、立方、畢氏、三角"),
    ("folded", "π 摺疊（雙面）", ["DF"], ["CF", "CIF", "CI", "C"], ["D", "DI"], "摺疊刻度讓乘法少移動，乘 π 一步完成"),
    ("infinirule", "四刻度（Infinirule 風格）", ["DF"], ["CF", "C"], ["D"], "上面兩個一起動、下面的滑尺單獨動"),
]
LAYOUT_BY_KEY = {x[0]: x for x in LAYOUTS}


# ==================================================================== 刻度線
@dataclass
class Tick:
    u: float           # 位置（尺單位，含第幾圈）
    level: int         # 層級：0 主刻度、1 半刻度、2 細刻度…
    value: float
    text: str = ""     # 有文字＝要標數字


def _nice(n):
    if n <= 0 or not math.isfinite(n):
        return False
    m = n / 10 ** math.floor(math.log10(n) + 1e-12)
    return any(abs(m - k) < 1e-6 or abs(m - k * 10) < 1e-6 for k in NICE)


def ticks(scale: Scale, u0: float, u1: float, zoom: float, label_px=None):
    """看得到的範圍 [u0, u1]（尺單位）內的刻度線；zoom＝每單位像素。"""
    label_px = label_px or (lambda text: 7.2 * len(text) + 8)
    out = []
    lo, hi = min(scale.lo, scale.hi), max(scale.lo, scale.hi)
    for k in range(math.floor(u0), math.floor(u1) + 1):
        a, b = u0 - k, u1 - k            # 這一圈裡看得到的範圍（0～1 之間的部分）
        if b < 0 or a > 1:
            continue
        found = []
        marks = scale.marks

        def pos(x):
            return scale.f(x)

        def visible(x0, x1):
            p0, p1 = pos(max(lo, x0)), pos(min(hi, x1))
            return max(p0, p1) >= a - 1e-9 and min(p0, p1) <= b + 1e-9

        def add(x, level, step, labeled):
            if x < lo - 1e-12 * max(1, abs(lo)) or x > hi + 1e-12 * max(1, abs(hi)):
                return
            p = pos(x)
            if p >= 1 - 1e-12 or p < -1e-12:      # 端點屬於下一圈（避免重複）
                if not (abs(p) < 1e-12):
                    return
            if a - 1e-9 <= p <= b + 1e-9:
                found.append(Tick(p + k, level, x, scale.label(x, step) if labeled else ""))

        def gap(x0, x1):
            return abs(pos(max(lo, min(hi, x1))) - pos(max(lo, min(hi, x0)))) * zoom

        def sub(x0, x1, level, depth):
            if depth > 40 or not visible(x0, x1):
                return
            w = x1 - x0
            if w <= 1e-13 * max(1.0, abs(x0)):
                return
            for n in (10, 5, 4, 2):
                step = w / n
                if not _nice(step):
                    continue
                # 這一段裡最小的間距（對數刻度兩端不同，取較小的）
                g = min(gap(x0, x0 + step), gap(x1 - step, x1))
                if g < MIN_PX:
                    continue
                lab = g >= label_px(scale.label(x1 - step, step)) * 1.15
                for i in range(1, n):
                    x = x0 + step * i
                    lv = level + (1 if (n == 10 and i == 5) or (n == 4 and i == 2) or n == 2 else 2)
                    add(x, lv, step, lab)
                for i in range(n):
                    sub(x0 + step * i, x0 + step * (i + 1), level + 2, depth + 1)
                return

        for i, x in enumerate(marks):
            add(x, 0, _mark_step(marks, i), True)
            if i + 1 < len(marks):
                sub(x, marks[i + 1], 0, 0)
        for x, text in scale.special:
            if lo <= x <= hi:
                p = pos(x)
                if a <= p <= b:
                    found.append(Tick(p + k, -1, x, text))
        out += found
    out.sort(key=lambda t: t.u)
    return out


def _mark_step(marks, i):
    if i + 1 < len(marks):
        return abs(marks[i + 1] - marks[i])
    return abs(marks[i] - marks[i - 1]) if i else 1


def place_labels(tks, zoom, u_left, label_px=None):
    """去掉會互相重疊的數字（層級小的優先保留）。回傳 [(x 像素, 文字, 層級)]。"""
    label_px = label_px or (lambda text: 7.2 * len(text) + 8)
    cand = sorted((t for t in tks if t.text), key=lambda t: (t.level, t.u))
    taken = []
    out = []
    for t in cand:
        x = (t.u - u_left) * zoom
        w = label_px(t.text) / 2 + 2
        if any(abs(x - x2) < w + w2 for x2, w2 in taken):
            continue
        taken.append((x, w))
        out.append((x, t.text, t.level))
    return out


# ==================================================================== 讀數
def digits_for(scale: Scale, u: float, zoom: float):
    """依放大倍率決定讀數位數：半個像素造成的數值差。"""
    du = 0.5 / max(zoom, 1e-9)
    x0, x1 = scale.value(u - du / 2), scale.value(u + du / 2)
    dx = abs(x1 - x0) or 1e-15
    return max(0, min(14, -math.floor(math.log10(dx))))


def reading(scale: Scale, u: float, zoom: float):
    x = scale.value(u)
    d = digits_for(scale, u, zoom)
    s = "%.*f" % (d, x)              # 保留尾數 0：位數代表目前能讀到的精度
    return x, s + scale.unit


# ==================================================================== 尺的狀態
@dataclass
class RuleState:
    zoom: float = 1000.0         # 每單位像素
    left: float = -0.05          # 畫面左邊對應定尺的 u
    slide: float = 0.0           # 滑尺相對定尺的位移（u）
    cursor: float = 0.30103      # 游標（髮線）在定尺上的 u

    def x_of(self, u):
        return (u - self.left) * self.zoom

    def u_of(self, x):
        return self.left + x / self.zoom

    def zoom_at(self, x, factor, lo=150.0, hi=5e9):
        u = self.u_of(x)
        self.zoom = max(lo, min(hi, self.zoom * factor))
        self.left = u - x / self.zoom


def mantissa(x):
    """x 的有效數字部分與 10 的次方：x＝m×10ⁿ，1 ≤ m < 10。"""
    if x == 0:
        return 0.0, 0
    n = math.floor(math.log10(abs(x)))
    return x / 10 ** n, n
