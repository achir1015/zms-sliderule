"""自訂刻度：上定尺、滑尺、下定尺各要放哪些刻度（依點選順序由上而下），可存成自己的尺型。"""
import flet as ft

from .. import rule as R
from . import theme as T

MAX_PER_PART = 5


class ScalePicker:
    def __init__(self, ctx, parts, on_apply):
        self.ctx = ctx
        self.parts = [list(p) for p in parts]
        self.on_apply = on_apply
        self.boxes = [ft.Row(wrap=True, spacing=6, run_spacing=6) for _ in range(3)]
        self.name = T.field("存成我的尺型（名稱，可不填）", "", width=320)
        self.shared = ft.Checkbox(label="分享給所有人", value=False,
                                  visible=bool(ctx.books and hasattr(ctx.books, "can") and ctx.books.can("LAYOUT", 2)))
        self._fill()

    def _fill(self):
        for i, box in enumerate(self.boxes):
            sel = self.parts[i]
            chips = []
            for s in R.SCALES:
                on = s.key in sel
                order = sel.index(s.key) + 1 if on else 0
                chips.append(ft.Container(ft.Row([
                    ft.Text(str(order) if on else "", size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_700,
                            width=12 if on else 0),
                    ft.Text(s.key, size=13, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE if on else s.color),
                    ft.Text(s.formula, size=10, color="#E6EEF8" if on else T.MUTED)], spacing=4, tight=True),
                    padding=ft.Padding.symmetric(horizontal=9, vertical=5), border_radius=14,
                    bgcolor=T.PRIMARY if on else "#F1F4F9", tooltip=s.name, ink=True,
                    on_click=lambda e, i=i, k=s.key: self.toggle(i, k)))
            box.controls = chips

    def toggle(self, i, k):
        sel = self.parts[i]
        if k in sel:
            sel.remove(k)
        else:
            if len(sel) >= MAX_PER_PART:
                self.ctx.toast("每一段最多 %d 個刻度" % MAX_PER_PART, True)
                return
            sel.append(k)
        self._fill()
        for b in self.boxes:
            b.update()

    def open(self):
        c = self.ctx
        titles = [("上定尺（固定）", "blue"), ("滑尺（可左右拉動）", "amber"), ("下定尺（固定）", "blue")]
        body = ft.Column([*[ft.Column([T.chip(t, tone), self.boxes[i]], spacing=6) for i, (t, tone) in enumerate(titles)],
                          T.muted("點一下加入、再點一下移除；數字是由上到下的順序。滑尺至少要一個刻度。", 12),
                          ft.Row([self.name, self.shared], spacing=10)],
                         spacing=14, tight=True, scroll=ft.ScrollMode.AUTO, height=520)
        c.dialog("自訂刻度", body, [T.btn("取消", kind="ghost", on_click=lambda e: c.close()),
                                   T.btn("套用", ft.Icons.CHECK, self.apply)], icon=ft.Icons.TUNE, width=760)

    def apply(self, e):
        if not self.parts[1]:
            self.ctx.toast("滑尺至少要有一個刻度", True)
            return
        if not (self.parts[0] or self.parts[2]):
            self.ctx.toast("定尺至少要有一個刻度", True)
            return
        saved = None
        name = (self.name.value or "").strip()
        if name and self.ctx.books and hasattr(self.ctx.books, "save_layout"):
            try:
                saved = "u%d" % self.ctx.books.save_layout(name, *self.parts, shared=bool(self.shared.value))
            except Exception as ex:
                self.ctx.toast(str(ex), True)
                return
        self.ctx.close()
        self.on_apply(*self.parts, saved_key=saved)
