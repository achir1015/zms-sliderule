"""計算尺主畫面：工具列（尺型、刻度、放大、精細）＋計算尺本體＋游標讀數＋計算示範。"""
import math
import threading

import flet as ft

from .. import rule as R
from ..demo import Demo, PRESETS, plan
from . import theme as T
from .ruleview import RuleView

I = ft.Icons


class RuleScreen(ft.Column):
    def __init__(self, ctx, layout=None, expr=None, autoplay=False, custom=None, compact=False, **kw):
        super().__init__(spacing=12, expand=True, scroll=ft.ScrollMode.AUTO)
        self.ctx = ctx
        self.books = getattr(ctx, "books", None)
        pref = self._pref()
        key = layout or pref.get("layout") or "student"
        lay = self._layouts().get(key) or R.LAYOUT_BY_KEY["student"]
        self.layout_key = key
        self.demo = None
        parts = custom or (lay[2], lay[3], lay[4])
        self.rv = RuleView(parts[0], parts[1], parts[2], on_change=self._readout)
        self.read_row = ft.Row(wrap=True, spacing=8, run_spacing=8)
        self.zoom_text = ft.Text("", size=12, color=T.MUTED)
        self.fine = ft.Switch(label="精細移動（1/10）", value=False, on_change=self._fine)
        self.pick = T.dropdown("尺型", [(k, v[1]) for k, v in self._layouts().items()], key, width=230,
                               filterable=False, on_select=lambda e: self.use_layout(e.control.value))
        self.expr = T.field("要算什麼？例：2×3.5、7÷2、√2、sin 30、2^1.5", expr or "", expand=True,
                            on_submit=lambda e: self.run_demo())
        self.steps = ft.Column(spacing=6)
        self.answer = ft.Text("", size=15, weight=ft.FontWeight.W_700, color=T.PRIMARY, selectable=True)
        self.demo_btn = T.btn("語音示範", I.PLAY_CIRCLE, lambda e: self.run_demo())
        self.stop_btn = T.btn("停止", I.STOP_CIRCLE, lambda e: self.stop_demo(), kind="outline")
        tools = ft.Row([
            self.pick,
            T.btn("自訂刻度", I.TUNE, lambda e: self.edit_scales(), kind="outline"),
            ft.IconButton(I.ZOOM_OUT, tooltip="縮小", on_click=lambda e: self.rv.zoom_by(1 / 1.6)),
            ft.IconButton(I.ZOOM_IN, tooltip="放大（也可以用滑鼠滾輪或兩指縮放）", on_click=lambda e: self.rv.zoom_by(1.6)),
            T.btn("重設", I.RESTART_ALT, lambda e: self.reset(), kind="ghost"),
            self.fine, self.zoom_text], spacing=8, wrap=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER)
        presets = ft.Row([ft.TextButton(p, on_click=lambda e, p=p: self.preset(p)) for p in PRESETS], wrap=True,
                         spacing=0)
        self.compact = compact
        demo_card = T.card(ft.Column([
            ft.Row([T.icon_tile(I.RECORD_VOICE_OVER, "rose", 36, radius=10),
                    T.title_text("小柯示範" if compact else "計算示範：輸入算式，小柯一步一步移動計算尺給你看", 16),
                    ft.Container(expand=True), T.btn("停止", I.STOP_CIRCLE, lambda e: self.stop_demo(), kind="outline")
                    if compact else ft.Container()], spacing=10),
            ft.Row([self.expr, self.demo_btn, self.stop_btn], spacing=8, visible=not compact),
            ft.Container(presets, visible=not compact), self.steps, self.answer], spacing=8), padding=16,
            visible=not compact)
        self.demo_card = demo_card
        self.controls = [
            T.card(ft.Column([tools, self.rv,
                              T.muted("拖曳定尺＝整把尺移動　拖曳滑尺＝只動滑尺　拖曳紅色髮線或上下把手＝移動游標　"
                                      "滾輪／兩指＝放大縮小（越放大越精確）", 12)], spacing=10), padding=14),
            T.card(ft.Column([ft.Row([T.icon_tile(I.STRAIGHTEN, "teal", 32, radius=9),
                                      T.title_text("游標讀數", 15),
                                      T.muted("（對數刻度只顯示有效數字，小數點位置要自己判斷，和真的計算尺一樣）", 12)],
                                     spacing=8), self.read_row], spacing=8), padding=14),
            demo_card]
        self._autoplay = bool(autoplay and expr)
        self._readout(self.rv)

    def did_mount(self):
        if self._autoplay:
            def wait_then_run():
                import time
                for _ in range(60):                # 等計算尺量好寬度（第一次畫好）再開始示範
                    if self.rv.W > 0:
                        break
                    time.sleep(0.1)
                time.sleep(0.4)
                self.run_demo()
            threading.Thread(target=wait_then_run, daemon=True).start()

    # ---------------------------------------------------------------- 尺型與偏好
    def _layouts(self):
        out = {x[0]: x for x in R.LAYOUTS}
        if self.books and hasattr(self.books, "my_layouts"):
            try:
                for r in self.books.my_layouts():
                    out["u%d" % r["id"]] = ("u%d" % r["id"], "★ " + r["name"], r["upper"].split(",") if r["upper"] else [],
                                            r["slide"].split(",") if r["slide"] else [],
                                            r["lower"].split(",") if r["lower"] else [], r.get("note") or "")
            except Exception:
                pass
        return out

    def _pref(self):
        try:
            return self.books.pref() if self.books and hasattr(self.books, "pref") else {}
        except Exception:
            return {}

    def use_layout(self, key):
        lay = self._layouts().get(key)
        if not lay:
            return
        self.layout_key = key
        self.pick.value = key
        self.rv.set_parts(lay[2], lay[3], lay[4])
        if self.books and hasattr(self.books, "save_pref"):
            try:
                self.books.save_pref(layout=key)
            except Exception:
                pass
        self._readout(self.rv)
        self.update()

    def ensure_scales(self, key, needs):
        """目前的尺上沒有需要的刻度時，換成 key 尺型（還沒顯示時不更新畫面）。"""
        if set(needs) <= set(sum(self.rv.parts, [])):
            return
        lay = self._layouts().get(key)
        if not lay:
            return
        self.layout_key = key
        self.pick.value = key
        self.rv.set_parts(lay[2], lay[3], lay[4])
        self._readout(self.rv)

    def edit_scales(self):
        from .scalepick import ScalePicker
        ScalePicker(self.ctx, self.rv.parts, self._apply_custom).open()

    def _apply_custom(self, upper, slide, lower, saved_key=None):
        if saved_key:
            self.pick.options = [ft.dropdown.Option(k, v[1]) for k, v in self._layouts().items()]
            self.use_layout(saved_key)
            return
        self.rv.set_parts(upper, slide, lower)
        self._readout(self.rv)
        self.update()

    def reset(self):
        self.stop_demo()
        self.rv.set_highlight([])
        self.rv.reset()
        self.rv.emit()

    def _fine(self, e):
        self.rv.fine = bool(self.fine.value)

    # ---------------------------------------------------------------- 讀數
    def _readout(self, rv):
        chips = []
        for part, k, x, text in rv.readings():
            s = R.BY_KEY[k]
            tone = ("#FFF4D6", "#8A5A00") if part == 1 else ("#EEF3FA", "#1E3A5F")
            hi = k in rv.highlight
            chips.append(ft.Container(ft.Row([
                ft.Text(k, size=13, weight=ft.FontWeight.W_800, color=s.color),
                ft.Text(s.formula, size=11, color=T.MUTED),
                ft.Text(text, size=15, weight=ft.FontWeight.W_700, color=tone[1], selectable=True)],
                spacing=6, tight=True), bgcolor="#FFE08A" if hi else tone[0], border_radius=10,
                padding=ft.Padding.symmetric(horizontal=10, vertical=6), tooltip=s.name))
        self.read_row.controls = chips
        z = rv.st.zoom / max(rv.W * 0.92, 1)
        self.zoom_text.value = "放大 %s 倍　（滑尺位移 %.5f）" % (_fmt_zoom(z), rv.st.slide - math.floor(rv.st.slide))
        try:
            self.read_row.update()
            self.zoom_text.update()
        except Exception:
            pass

    # ---------------------------------------------------------------- 計算示範
    def preset(self, p):
        self.expr.value = p
        self.run_demo()

    def run_demo(self):
        self.stop_demo()
        try:
            pl = plan(self.expr.value)
        except ValueError as e:
            self.ctx.toast(str(e), True)
            return
        self.ensure_scales(pl["layout"], pl["needs"])
        self.steps.controls = [self._step_row(i, s["text"], False) for i, s in enumerate(pl["steps"])]
        self.answer.value = ""
        self.demo_card.visible = True
        self.update()
        self.demo = Demo(self.rv, pl, self._on_step, self.ctx, self._on_done)
        threading.Thread(target=self.demo.run, daemon=True).start()
        if self.books and hasattr(self.books, "add_history"):
            try:
                self.books.add_history(pl["expr"], pl["result_text"], "DRILL" if self.compact else "DEMO")
            except Exception:
                pass

    def _step_row(self, i, text, on):
        return ft.Container(ft.Row([
            ft.Container(ft.Text(str(i + 1), size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_700),
                         width=22, height=22, border_radius=11, bgcolor=T.GOLD if on else "#B8C2D3",
                         alignment=ft.Alignment.CENTER),
            ft.Text(text, size=14, color=T.TEXT, expand=True, weight=ft.FontWeight.W_600 if on else None)],
            spacing=10), padding=8, border_radius=10, bgcolor="#FFF8E6" if on else None,
            border=ft.Border.all(2, T.GOLD if on else "#00000000"))

    def _on_step(self, idx, pl):
        self.steps.controls = [self._step_row(i, s["text"], i == idx) for i, s in enumerate(pl["steps"])]
        try:
            self.steps.update()
        except Exception:
            pass

    def _on_done(self, pl):
        self.answer.value = "答案：%s　（計算機驗算：%s）" % (pl["result_text"], pl["exact_text"])
        if self.compact:
            self.answer.value = "計算尺讀出約 %s" % pl["result_text"]
        try:
            self.answer.update()
        except Exception:
            pass

    def stop_demo(self):
        if self.demo:
            self.demo.cancel()
            self.demo = None
        self.ctx.stop_voice()

    def will_unmount(self):
        self.stop_demo()


def _fmt_zoom(z):
    if z < 10:
        return "%.1f" % z
    if z < 1e6:
        return "{:,.0f}".format(z)
    return "%.2e" % z
