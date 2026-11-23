"""計算尺本體（畫面元件）：上定尺、滑尺、下定尺三段＋游標（髮線）。

操作（和 Infinirule 類似）：
* 拖曳上定尺或下定尺 → 整把尺左右移動；拖曳滑尺 → 只移動滑尺；拖曳游標（髮線或上下把手）→ 移動游標。
* 拖曳尺上方或下方的空白處 → 精細移動（1/10 速度）：上方空白移動整把尺、下方空白移動滑尺。
* 滑鼠滾輪或兩指縮放 → 放大縮小（無限精度）。
* 刻度自動環繞（像圓形計算尺），永遠不會「超出尺外」。

效能：每一段畫在 3 倍寬的畫布上，拖曳時只改畫布的 left；移到緩衝區外或放大縮小時才重畫。
"""
import math
import threading
import time

import flet as ft
import flet.canvas as cv

from .. import rule as R

LW = 96          # 左邊刻度名稱欄寬
SH = 38          # 每個刻度的高度
TM = 30          # 上方空白（游標把手、精細移動）
BM = 30          # 下方空白
GAP = 3          # 定尺與滑尺之間的縫
CW = 64          # 游標玻璃寬度
TICK_LEN = (0.56, 0.42, 0.31, 0.24, 0.19)
STATOR_BG = "#FBF7EC"
SLIDE_BG = "#FFFDF6"
BODY_LINE = "#CDBF9A"
CURSOR_LINE = "#D62828"


class RuleView(ft.Container):
    def __init__(self, layout=("A",), slide=("B", "CI", "C"), lower=("D", "K"), on_change=None, height_hint=None,
                 fine=False):
        super().__init__()
        self.st = R.RuleState()
        self.parts = [list(layout), list(slide), list(lower)]
        self.on_change = on_change
        self.fine = fine
        self.W = 0.0                     # 尺面寬度（像素，不含左邊名稱欄）
        self._drawn = [None, None, None]  # 每段畫布畫的時候的 (左邊 u, zoom, 位移)
        self._drag = None
        self._lock = threading.RLock()
        self._last_emit = 0
        self.highlight = set()           # 教學示範時要強調的刻度
        self.marks = []                  # 教學示範的標記 [(刻度, u, 文字)]
        self._build()

    # ================================================================ 建立
    def _build(self):
        self.canvases = [cv.Canvas(shapes=[], width=10, height=10) for _ in range(3)]
        self.layers = [ft.Container(c, left=0, top=0) for c in self.canvases]
        self.bodies = [ft.Container(left=0, right=0, top=0, height=10, bgcolor=STATOR_BG) for _ in range(3)]
        self.hair = ft.Container(width=1.6, bgcolor=CURSOR_LINE, left=CW / 2 - 0.8, top=0, bottom=0)
        self.cursor = ft.Container(ft.Stack([
            ft.Container(left=0, right=0, top=TM - 4, bottom=BM - 4, bgcolor="#1A5B8DEF", border_radius=6,
                         border=ft.Border.all(1, "#665B8DEF")),
            ft.Container(left=CW / 2 - 16, width=32, top=4, height=TM - 8, border_radius=8, bgcolor="#C83A5A8C",
                         content=ft.Icon(ft.Icons.DRAG_INDICATOR, size=14, color="#FFFFFF"),
                         alignment=ft.Alignment.CENTER),
            ft.Container(left=CW / 2 - 16, width=32, bottom=4, height=BM - 8, border_radius=8, bgcolor="#C83A5A8C",
                         content=ft.Icon(ft.Icons.DRAG_INDICATOR, size=14, color="#FFFFFF"),
                         alignment=ft.Alignment.CENTER),
            self.hair]), width=CW, left=0, top=0, bottom=0)
        self.fine_hint = ft.Text("", size=11, color="#8A7A55")
        self.top_hint = ft.Container(ft.Text("↔ 拖曳這裡：整把尺精細移動（1/10）", size=11, color="#9C8E6B"),
                                     left=10, top=7)
        self.bot_hint = ft.Container(ft.Text("↔ 拖曳這裡：滑尺精細移動（1/10）", size=11, color="#9C8E6B"),
                                     left=10, bottom=7)
        self.sizer = cv.Canvas(left=0, right=0, top=0, bottom=0, on_resize=self._on_resize, resize_interval=60)
        self.stack = ft.Stack([self.sizer,
                               self.top_hint, self.bot_hint, *self.bodies, *self.layers, self.cursor],
                              clip_behavior=ft.ClipBehavior.HARD_EDGE)
        self.gesture = ft.GestureDetector(
            content=self.stack, on_scale_start=self._start, on_scale_update=self._update, on_scale_end=self._end,
            on_scroll=self._scroll, drag_interval=12, mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT)
        self.names = ft.Column(spacing=0, width=LW)
        self.content = ft.Row([self.names, ft.Container(self.gesture, expand=True)], spacing=0,
                              vertical_alignment=ft.CrossAxisAlignment.START)
        self.border = ft.Border.all(1, BODY_LINE)
        self.border_radius = 10
        self.bgcolor = "#F3EEDF"
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self._layout()

    def total_height(self):
        n = sum(len(p) for p in self.parts)
        return TM + BM + n * SH + 2 * GAP

    def part_top(self, i):
        y = TM
        for j in range(i):
            y += len(self.parts[j]) * SH + GAP
        return y

    def _layout(self):
        h = self.total_height()
        self.height = h
        self.stack.height = h
        for i in range(3):
            n = len(self.parts[i])
            top = self.part_top(i)
            b = self.bodies[i]
            b.top, b.height = top, n * SH
            b.bgcolor = SLIDE_BG if i == 1 else STATOR_BG
            b.border = ft.Border.symmetric(vertical=ft.BorderSide(1, BODY_LINE)) if i == 1 else None
            b.visible = n > 0
            self.layers[i].top = top
            self.canvases[i].height = max(1, n * SH)
        self._names()

    def _names(self):
        rows = [ft.Container(height=TM)]
        for i, part in enumerate(self.parts):
            for k in part:
                s = R.BY_KEY[k]
                hi = k in self.highlight
                rows.append(ft.Container(ft.Row([
                    ft.Text(k, size=15, weight=ft.FontWeight.W_800, color="#7A1F1F" if hi else s.color,
                            no_wrap=True),
                    ft.Text(s.formula, size=10, color="#5B5B5B", no_wrap=True, max_lines=1, expand=True,
                            overflow=ft.TextOverflow.ELLIPSIS)], spacing=5,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    height=SH, padding=ft.Padding.only(left=10, right=4),
                    bgcolor=("#FFE08A" if hi else ("#FFF8E6" if i == 1 else "#F7F0DC")),
                    tooltip="%s：%s" % (k, s.name), alignment=ft.Alignment.CENTER_LEFT))
            if i < 2:
                rows.append(ft.Container(height=GAP, bgcolor=BODY_LINE))
        rows.append(ft.Container(height=BM))
        self.names.controls = rows

    # ================================================================ 設定
    def set_parts(self, upper, slide, lower):
        with self._lock:
            self.parts = [list(upper), list(slide), list(lower)]
            self._layout()
            self.redraw(all_parts=True)

    def set_highlight(self, keys, marks=None):
        self.highlight = set(keys or ())
        self.marks = list(marks or [])
        self._names()
        self.redraw(all_parts=True)

    def reset(self):
        with self._lock:
            z = max(self.W, 300) * 0.92
            self.st = R.RuleState(zoom=z, left=-0.04, slide=0.0, cursor=0.0)
            self.st.left = -(self.W - z) / 2 / z if self.W else -0.04
            self.redraw(all_parts=True)

    # ================================================================ 繪圖
    def _on_resize(self, e):
        w = float(getattr(e, "width", 0) or 0)
        if w <= 0 or abs(w - self.W) < 1:
            return
        first = self.W == 0
        self.W = w
        if first:
            z = w * 0.92
            self.st.zoom = z
            self.st.left = -(w - z) / 2 / z
            self.st.cursor = self.st.cursor if self.st.cursor else 0.0
        self.redraw(all_parts=True)

    def redraw(self, all_parts=False, parts=None, update=True):
        if self.W <= 0:
            return
        with self._lock:
            for i in (range(3) if all_parts or parts is None else parts):
                self._render(i)
            self._place()
        if update:
            self._push()

    def _offset(self, i):
        return self.st.slide if i == 1 else 0.0

    def _render(self, i):
        st, W = self.st, self.W
        keys = self.parts[i]
        c = self.canvases[i]
        c.width = 3 * W
        off = self._offset(i)
        u_left = st.left - W / st.zoom - off        # 畫布最左邊對應這一段刻度的 u
        u_right = u_left + 3 * W / st.zoom
        shapes = []
        n = len(keys)
        for j, k in enumerate(keys):
            s = R.BY_KEY[k]
            y0 = j * SH
            # 刻度線方向：靠近滑尺縫的那一邊
            if i == 0:
                down = False
            elif i == 2:
                down = True
            else:
                down = j < (n + 1) // 2 if n > 1 else True
            edge = y0 if down else y0 + SH
            sign = 1 if down else -1
            tks = R.ticks(s, u_left, u_right, st.zoom)
            if not tks:
                continue
            base = min((t.level for t in tks if t.level >= 0), default=0)
            major, minor = [], []
            for t in tks:
                x = (t.u - u_left) * st.zoom
                if t.level < 0:
                    continue
                rel = min(len(TICK_LEN) - 1, max(0, (t.level - base)))
                ln = TICK_LEN[rel] * SH
                (major if rel == 0 else minor).append((x, ln))
            if k in self.highlight:
                shapes.append(cv.Rect(0, y0 + 1, 3 * W, SH - 2, paint=ft.Paint(color="#40FFD24A")))
            for arr, wdt in ((major, 1.5), (minor, 0.9)):
                if arr:
                    el = []
                    for x, ln in arr:
                        el.append(cv.Path.MoveTo(x, edge))
                        el.append(cv.Path.LineTo(x, edge + sign * ln))
                    shapes.append(cv.Path(el, paint=ft.Paint(color=s.color, stroke_width=wdt,
                                                             style=ft.PaintingStyle.STROKE)))
            for x, text, lv in R.place_labels(tks, st.zoom, u_left):
                special = lv < 0
                rel = 0 if special else max(0, lv - base)
                ln = (TICK_LEN[0] if special or rel == 0 else TICK_LEN[min(rel, 4)]) * SH
                size = 12.5 if rel == 0 else 10.5
                ty = edge + sign * (ln + (2 if down else 2))
                shapes.append(cv.Text(x, ty, text, style=ft.TextStyle(
                    size=size, color="#1F6FB2" if special else s.color,
                    weight=ft.FontWeight.W_700 if rel == 0 or special else ft.FontWeight.W_500),
                    alignment=ft.Alignment.TOP_CENTER if down else ft.Alignment.BOTTOM_CENTER))
                if special:
                    shapes.append(cv.Line(x, edge, x, edge + sign * ln, paint=ft.Paint(color="#1F6FB2", stroke_width=1.2)))
            for mk, mu, mtext in self.marks:
                if mk != k:
                    continue
                for kk in range(math.floor(u_left - mu), math.floor(u_right - mu) + 1):
                    x = (mu + kk - u_left) * st.zoom
                    shapes.append(cv.Circle(x, y0 + SH / 2, 6, paint=ft.Paint(color="#E0A526", stroke_width=2.5,
                                                                              style=ft.PaintingStyle.STROKE)))
                    if mtext:
                        shapes.append(cv.Text(x + 8, y0 + SH / 2, mtext, style=ft.TextStyle(
                            size=11, color="#B45309", weight=ft.FontWeight.W_700), alignment=ft.Alignment.CENTER_LEFT))
            if j < n - 1:
                shapes.append(cv.Line(0, y0 + SH, 3 * W, y0 + SH, paint=ft.Paint(color="#E7DDC3", stroke_width=0.6)))
        c.shapes = shapes
        self._drawn[i] = (u_left, st.zoom)

    def _place(self):
        """依目前狀態放好三段畫布與游標（不重畫刻度）。"""
        st = self.st
        for i in range(3):
            d = self._drawn[i]
            if not d:
                continue
            u_left, z = d
            if abs(z - st.zoom) > 1e-9 * z:
                self._render(i)
                u_left, z = self._drawn[i]
            x = (u_left + self._offset(i) - st.left) * st.zoom       # 畫布左邊在畫面上的位置
            if x > -0.15 * self.W or x < -1.85 * self.W:              # 快移出緩衝區 → 以目前位置重畫
                self._render(i)
                u_left, _ = self._drawn[i]
                x = (u_left + self._offset(i) - st.left) * st.zoom
            self.layers[i].left = x
        self.cursor.left = st.x_of(st.cursor) - CW / 2

    def _push(self):
        try:
            self.update()
        except Exception:
            pass
        now = time.time()
        if self.on_change and now - self._last_emit > 0.08:
            self._last_emit = now
            try:
                self.on_change(self)
            except Exception:
                pass

    def emit(self):
        if self.on_change:
            self._last_emit = time.time()
            self.on_change(self)

    # ================================================================ 操作
    def _target(self, x, y):
        st = self.st
        cx = st.x_of(st.cursor)
        h = self.total_height()
        if y < TM or y > h - BM:
            if abs(x - cx) <= 18:
                return "cursor", 1.0
            return ("rule", 0.1) if y < TM else ("slide", 0.1)
        if abs(x - cx) <= 7:
            return "cursor", 1.0
        y1 = self.part_top(1)
        if self.parts[1] and y1 <= y <= y1 + len(self.parts[1]) * SH:
            return "slide", 1.0
        return "rule", 1.0

    def _start(self, e):
        p = e.local_focal_point
        what, speed = self._target(p.x, p.y)
        if self.fine:
            speed *= 0.1
        self._drag = [what, speed, None]

    def _update(self, e):
        if not self._drag:
            return
        st = self.st
        with self._lock:
            pc = getattr(e, "pointer_count", 1) or 1
            if pc >= 2:
                hs = getattr(e, "horizontal_scale", None) or getattr(e, "scale", 1.0) or 1.0
                prev = self._drag[2] or 1.0
                f = hs / prev
                self._drag[2] = hs
                if abs(f - 1) > 1e-4:
                    st.zoom_at(e.local_focal_point.x, f)
                    self._place()
                    self._push()
                return
            dx = e.focal_point_delta.x
            if not dx:
                return
            what, speed = self._drag[0], self._drag[1]
            du = dx * speed / st.zoom
            if what == "rule":
                st.left -= du
            elif what == "slide":
                st.slide += du
            else:
                st.cursor += du
            self._place()
        self._push()

    def _end(self, e):
        self._drag = None
        self.emit()

    def _scroll(self, e):
        dy = e.scroll_delta.y if e.scroll_delta else 0
        if not dy:
            return
        with self._lock:
            self.st.zoom_at(e.local_position.x, 1.18 ** (-dy / 100.0))
            self._place()
        self._push()
        self.emit()

    def zoom_by(self, f):
        with self._lock:
            self.st.zoom_at(self.st.x_of(self.st.cursor), f)
            self._place()
        self._push()
        self.emit()

    # ================================================================ 讀數
    def readings(self):
        """游標下每個刻度的讀數：[(段, 刻度, 數值, 文字)]"""
        st = self.st
        out = []
        for i, part in enumerate(self.parts):
            for k in part:
                s = R.BY_KEY[k]
                u = st.cursor - self._offset(i)
                x, text = R.reading(s, u, st.zoom)
                out.append((i, k, x, text))
        return out

    # ================================================================ 動畫（語音示範用）
    def animate_to(self, slide=None, cursor=None, left=None, seconds=0.9, stop=None):
        """把滑尺、游標（與畫面位置）平滑移動到目標；stop() 回傳 True 時中止。"""
        st = self.st
        s0, c0, l0 = st.slide, st.cursor, st.left
        s1 = s0 if slide is None else _near(slide, s0)
        c1 = c0 if cursor is None else _near(cursor, c0)
        l1 = l0 if left is None else left
        frames = max(1, int(seconds * 30))
        for k in range(1, frames + 1):
            if stop and stop():
                return False
            t = k / frames
            t = t * t * (3 - 2 * t)
            with self._lock:
                st.slide = s0 + (s1 - s0) * t
                st.cursor = c0 + (c1 - c0) * t
                st.left = l0 + (l1 - l0) * t
                self._place()
            self._push()
            time.sleep(seconds / frames)
        self.emit()
        return True

    def ensure_visible(self, u, margin=0.18):
        """u 不在畫面內時，回傳讓它出現在畫面中的 left；否則回傳目前的 left。"""
        st = self.st
        x = st.x_of(u)
        if margin * self.W <= x <= (1 - margin) * self.W:
            return st.left
        return u - 0.5 * self.W / st.zoom


def _near(target, current):
    """環繞刻度：目標 u 可以加減整數圈，挑離目前位置最近的。"""
    return target + round(current - target)
