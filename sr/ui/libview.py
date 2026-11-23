"""刻度一覽、我的尺型、計算紀錄。"""
import flet as ft

from .. import rule as R
from . import theme as T

I = ft.Icons

USAGE = {
    "C": "滑尺上的基本對數刻度，和 D 配合做乘除。", "D": "定尺上的基本對數刻度，大部分答案在這裡讀。",
    "CI": "C 的倒數（由右到左），對準 C 的 x 讀出 1/x；連乘時少移動一次。", "DI": "D 的倒數刻度。",
    "CF": "從 π 開始的摺疊刻度，乘 π 一步完成；答案快超出尺外時改用摺疊刻度。", "DF": "定尺上的 π 摺疊刻度。",
    "CIF": "摺疊刻度的倒數。", "A": "兩個循環的平方刻度：D 的 x 對應 A 的 x²。", "B": "滑尺上的平方刻度。",
    "K": "三個循環的立方刻度：D 的 x 對應 K 的 x³。", "R1": "平方根刻度前半（1～3.16）：R 的 x 對應 D 的 x²。",
    "R2": "平方根刻度後半（3.16～10）。", "L": "線性刻度，D 的 x 對應 L 的 log₁₀x 小數部分。",
    "Ln": "線性刻度，D 的 x 對應 ln x（0～2.3）。",
    "S": "角度刻度，S 的 θ 對應 D 的 10·sin θ；反方向讀 90−θ 就是餘弦。", "T": "T 的 θ 對應 D 的 10·tan θ（θ ≤ 45°）。",
    "T2": "T2 的 θ 對應 D 的 tan θ（45°～84.3°）。", "ST": "小角度：sin θ ≈ tan θ ≈ 弧度，D 讀數除以 100。",
    "P": "畢氏刻度：D 的 x 對應 P 的 √(1−x²)（x 以 0.1～1 計），算直角三角形的邊。",
    "LL1": "雙對數：D 的 x 對應 e^(0.01x)。", "LL2": "雙對數：D 的 x 對應 e^(0.1x)。", "LL3": "雙對數：D 的 x 對應 eˣ。",
    "LL01": "負雙對數：e^(−0.01x)。", "LL02": "負雙對數：e^(−0.1x)。", "LL03": "負雙對數：e^(−x)。",
}


def _rng(s):
    a, b = min(s.lo, s.hi), max(s.lo, s.hi)
    f = (lambda v: "%.4g%s" % (v, s.unit))
    return "%s ～ %s" % (f(a), f(b))


class Scales(ft.Column):
    def __init__(self, ctx, **kw):
        self.ctx = ctx
        groups = [("對數刻度（乘除、平方、立方、倒數）", "log"), ("線性刻度（對數）", "lin"), ("三角刻度", "trig"),
                  ("雙對數刻度（指數）", "ll")]
        cards = []
        for title, kind in groups:
            rows = []
            for s in R.SCALES:
                if s.kind != kind:
                    continue
                rows.append(ft.Container(ft.Row([
                    ft.Container(ft.Text(s.key, size=17, weight=ft.FontWeight.W_800, color=s.color), width=56),
                    ft.Container(ft.Text(s.formula, size=14, color=T.PRIMARY, weight=ft.FontWeight.W_600), width=110),
                    ft.Column([ft.Text(s.name, size=14, weight=ft.FontWeight.W_600),
                               T.muted(USAGE.get(s.key, ""), 12)], spacing=2, expand=True),
                    ft.Container(T.muted(_rng(s), 12), width=170),
                    T.btn("在計算尺上看", I.STRAIGHTEN, lambda e, s=s: self.show(s), kind="outline")],
                    spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding.symmetric(vertical=8, horizontal=6),
                    border=ft.Border.only(bottom=ft.BorderSide(1, T.LINE))))
            cards.append(T.card(ft.Column([T.title_text(title, 16)] + rows, spacing=4), padding=16))
        super().__init__([T.page_header(I.VIEW_LIST, "刻度一覽", "全部 %d 種刻度：代號、公式、範圍與用法" % len(R.SCALES),
                                        "blue")] + cards, spacing=14, expand=True, scroll=ft.ScrollMode.AUTO)

    def show(self, s):
        """開一把含有這個刻度的計算尺（暫用尺型）。"""
        if s.key in ("C", "CI", "CF", "CIF", "B"):
            upper, slide, lower = ["DF"] if s.key in ("CF", "CIF") else ["A"], [s.key, "C"] if s.key != "C" else ["C"], ["D"]
        else:
            upper, slide, lower = [s.key], ["C"], ["D"]
        self.ctx.app.go("rule", custom=(upper, slide, lower))


class Layouts(ft.Column):
    def __init__(self, ctx, **kw):
        self.ctx = ctx
        self.box = ft.Column(spacing=14)
        super().__init__([T.page_header(I.DASHBOARD_CUSTOMIZE, "我的尺型", "內建尺型、自己存的尺型和大家分享的尺型", "amber",
                                        [T.btn("新增尺型", I.ADD, lambda e: self.edit(None))]),
                          self.box], spacing=14, expand=True, scroll=ft.ScrollMode.AUTO)
        self.load(False)

    def _row(self, key, name, up, sl, lo, note, actions):
        def chips(keys, tone):
            return ft.Row([T.chip(k, tone) for k in keys] or [T.muted("—", 12)], spacing=4, wrap=True)
        return ft.Container(ft.Row([
            ft.Column([ft.Text(name, size=15, weight=ft.FontWeight.W_700), T.muted(note, 12)], spacing=2, width=260),
            ft.Column([T.muted("上定尺", 11), chips(up, "blue")], spacing=2, width=180),
            ft.Column([T.muted("滑尺", 11), chips(sl, "amber")], spacing=2, width=220),
            ft.Column([T.muted("下定尺", 11), chips(lo, "blue")], spacing=2, width=200),
            ft.Row(actions, spacing=4)], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER, wrap=True),
            padding=10, border=ft.Border.only(bottom=ft.BorderSide(1, T.LINE)))

    def load(self, refresh=True):
        b, app = self.ctx.books, self.ctx.app
        built = [self._row(k, n, u, s, l, note, [T.btn("使用", I.PLAY_ARROW, lambda e, k=k: app.go("rule", layout=k),
                                                       kind="outline")]) for k, n, u, s, l, note in R.LAYOUTS]
        mine = []
        for r in b.my_layouts():
            sp = lambda v: [x for x in (v or "").split(",") if x]  # noqa: E731
            can_edit = r["owner"] == b.uid or b.can("LAYOUT", 2)
            acts = [T.btn("使用", I.PLAY_ARROW, lambda e, i=r["id"]: app.go("rule", layout="u%d" % i), kind="outline")]
            if can_edit:
                acts += [ft.IconButton(I.EDIT, tooltip="修改", on_click=lambda e, r=r: self.edit(r)),
                         ft.IconButton(I.DELETE_OUTLINE, tooltip="刪除", icon_color=T.DANGER,
                                       on_click=lambda e, r=r: self.delete(r))]
            note = ("★ 分享給所有人　" if r["shared"] else "") + "建立人 %s" % r["owner"] + (
                "　" + r["note"] if r["note"] else "")
            mine.append(self._row("u%d" % r["id"], r["name"], sp(r["upper"]), sp(r["slide"]), sp(r["lower"]), note, acts))
        self.box.controls = [
            T.card(ft.Column([T.title_text("內建尺型", 16)] + built, spacing=2), padding=16),
            T.card(ft.Column([T.title_text("我的與分享的尺型", 16)] +
                             (mine or [T.muted("還沒有自訂尺型。到計算尺按「自訂刻度」，填上名稱就會存在這裡。", 13)]),
                             spacing=2), padding=16)]
        if refresh:
            self.update()

    def edit(self, r):
        from .scalepick import ScalePicker
        sp = lambda v: [x for x in (v or "").split(",") if x]  # noqa: E731
        parts = [sp(r["upper"]), sp(r["slide"]), sp(r["lower"])] if r else [["A"], ["B", "CI", "C"], ["D", "K"]]
        pk = ScalePicker(self.ctx, parts, lambda *a, **k: None)
        if r:
            pk.name.value = r["name"]
            pk.shared.value = bool(r["shared"])

        def apply(e):
            name = (pk.name.value or "").strip()
            if not name:
                self.ctx.toast("請輸入尺型名稱", True)
                return
            if self.ctx.guard(self.ctx.books.save_layout, name, *pk.parts, shared=bool(pk.shared.value),
                              lid=r["id"] if r else None, ok="尺型已儲存") is not None:
                self.ctx.close()
                self.load()
        pk.apply = apply
        pk.open()

    def delete(self, r):
        def yes():
            self.ctx.guard(self.ctx.books.delete_layout, r["id"], ok="已刪除")
            self.load()
        self.ctx.confirm("刪除尺型", "確定刪除「%s」？" % r["name"], yes)


class History(ft.Column):
    def __init__(self, ctx, **kw):
        self.ctx = ctx
        self.grid = T.Grid([("at_s", "時間", "s", 160), ("expr", "算式", "s", 160), ("result", "計算尺答案", "s", 140),
                            ("mode_s", "方式", "s", 100)],
                           on_pick=lambda r: ctx.app.go("rule", expr=r["expr"], autoplay=True), height=560)
        super().__init__([T.page_header(I.HISTORY_EDU, "計算紀錄", "我做過的計算示範（點一列再示範一次）", "slate",
                                        [ctx.export_button(self.grid, "計算紀錄"),
                                         T.btn("清除全部", I.DELETE_SWEEP, lambda e: self.clear(), kind="outline")]),
                          self.grid], spacing=12, expand=True)
        self.load(False)

    def load(self, refresh=True):
        rows = self.ctx.books.history()
        for r in rows:
            r["at_s"] = T.show(r["at"])
            r["mode_s"] = {"DEMO": "語音示範", "DRILL": "練習示範"}.get(r["mode"], r["mode"])
        self.grid.set_rows(rows)
        if refresh:
            self.update()

    def clear(self):
        def yes():
            self.ctx.guard(self.ctx.books.clear_history, ok="已清除")
            self.load()
        self.ctx.confirm("清除計算紀錄", "確定清除自己的全部計算紀錄？", yes)
