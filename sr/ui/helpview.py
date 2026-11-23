"""語音動態教學：左邊課程目錄；右邊步驟方塊隨旁白依序點亮（聚光框），每一步可「跟著做」開啟對應畫面。"""
import os
import threading
import time

import flet as ft

from .. import APP_NAME, APP_VERSION
from ..help_text import BY_KEY, LESSONS
from ..voice import help_mp3
from . import theme as T

I = ft.Icons


class Help(ft.Row):
    def __init__(self, ctx, lesson="intro", **kw):
        self.ctx = ctx
        self.sec = lesson if lesson in BY_KEY else "intro"
        self.token = 0
        self.toc = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, expand=True)
        self.stage = ft.Column(spacing=18, scroll=ft.ScrollMode.AUTO, expand=True)
        if T.MOBILE:                          # 手機：目錄改成下拉選單，教學內容一欄
            self.pick = T.dropdown("選擇課程", [(x["key"], "%d. %s" % (i + 1, x["title"])) for i, x in enumerate(LESSONS)],
                                   self.sec, filterable=False, on_select=lambda e: self.show(e.control.value))
            super().__init__([ft.Column([self.pick, T.card(self.stage, padding=14)], spacing=12, expand=True,
                                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH)], expand=True)
            self.show(self.sec, update=False, autoplay=bool(kw.get("lesson")))
            return
        super().__init__([T.card(ft.Column([T.title_text("教學目錄", 16), self.toc,
                                            T.muted("%s v%s\n開發：吳玉柱 先生 與 Claude AI Opus 5.5" % (APP_NAME, APP_VERSION), 11)],
                                           spacing=10), width=280, padding=14),
                          T.card(self.stage, expand=True, padding=28)], expand=True, spacing=16,
                         vertical_alignment=ft.CrossAxisAlignment.START)
        self.show(self.sec, update=False, autoplay=bool(kw.get("lesson")))

    def show(self, key, update=True, autoplay=False):
        self.token += 1
        self.ctx.stop_voice()
        self.sec = key
        g = BY_KEY[key]
        if getattr(self, "pick", None) is not None:
            self.pick.value = key
        self.toc.controls = [ft.Container(ft.Row([
            ft.Text("%d" % (i + 1), size=13, color=ft.Colors.WHITE if s["key"] == key else T.MUTED, width=18),
            ft.Text(s["title"], size=14, weight=ft.FontWeight.W_700 if s["key"] == key else None,
                    color=ft.Colors.WHITE if s["key"] == key else T.TEXT, expand=True)]),
            padding=10, border_radius=10, bgcolor=T.PRIMARY if s["key"] == key else None, ink=True,
            on_click=lambda e, k=s["key"]: self.show(k)) for i, s in enumerate(LESSONS)]
        self.tiles = []
        row = []
        app = self.ctx.app
        for i, (icon, tone, text, sid) in enumerate(g["steps"]):
            if i and not T.MOBILE:
                row.append(ft.Icon(I.ARROW_FORWARD_ROUNDED, color="#94A3B8", size=22))
            can = bool(app.find(sid))
            tile = ft.Container(ft.Column([
                ft.Container(ft.Text(str(i + 1), size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_700),
                             width=20, height=20, border_radius=10, bgcolor=T.GOLD, alignment=ft.Alignment.CENTER),
                T.icon_tile(getattr(I, icon, I.INFO), tone, 60, radius=18),
                ft.Text(text, size=13, text_align=ft.TextAlign.CENTER, color=T.TEXT, weight=ft.FontWeight.W_600),
                ft.TextButton("跟著做", icon=I.TOUCH_APP, on_click=lambda e, s=sid: self.follow(s), disabled=not can,
                              tooltip="開啟這一步的畫面" if can else "您沒有此功能的權限")],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                width=130 if T.MOBILE else 150, padding=12, border_radius=16, opacity=0.4,
                animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
                animate_scale=ft.Animation(400, ft.AnimationCurve.EASE_OUT_BACK), scale=0.92,
                border=ft.Border.all(3, "#00000000"))
            self.tiles.append(tile)
            row.append(tile)
        idx = [s["key"] for s in LESSONS].index(key)
        self.play_btn = T.btn("播放語音教學", I.PLAY_CIRCLE, lambda e: self.play())
        stop_btn = T.btn("停止", I.STOP_CIRCLE, lambda e: self.stop(), kind="outline")
        demo = g.get("demo")
        demo_btn = T.btn("到計算尺看示範：%s" % demo, I.STRAIGHTEN,
                         lambda e: self.follow_demo(demo), bgcolor=T.GOLD) if demo and app.find("rule") else None
        title = ft.Column([T.muted("第 %d 課，共 %d 課" % (idx + 1, len(LESSONS)), 12),
                           T.title_text(g["title"], 18 if T.MOBILE else 22)], spacing=0, expand=True)
        self.stage.controls = [
            ft.Column([ft.Row([T.icon_tile(I.RECORD_VOICE_OVER, "rose", 44, radius=14), title], spacing=10),
                       ft.Row([self.play_btn, stop_btn] + ([demo_btn] if demo_btn else []), spacing=8, wrap=True)],
                      spacing=10) if T.MOBILE else
            ft.Row([T.icon_tile(I.RECORD_VOICE_OVER, "rose", 52, radius=16), title, self.play_btn, stop_btn] +
                   ([demo_btn] if demo_btn else []), spacing=14),
            ft.Container(ft.Row(row, wrap=True, spacing=8, run_spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER), padding=10),
            ft.Container(ft.Text(g["voice"], size=15, color=T.TEXT), bgcolor="#F7F9FC", border_radius=14, padding=18),
            ft.Row([T.btn("上一課", I.CHEVRON_LEFT, lambda e: self.show(LESSONS[idx - 1]["key"], autoplay=True),
                          kind="outline", disabled=idx == 0),
                    T.btn("下一課", I.CHEVRON_RIGHT, lambda e: self.show(LESSONS[idx + 1]["key"], autoplay=True),
                          disabled=idx == len(LESSONS) - 1)], spacing=10)]
        if update:
            self.update()
        if autoplay:
            self.play()

    def follow_demo(self, expr):
        self.stop(refresh=False)
        self.ctx.app.go("rule", expr=expr, autoplay=True)

    def follow(self, sid):
        self.stop(refresh=False)
        self.ctx.app.go(sid)

    def _light(self, n):
        for i, t in enumerate(self.tiles):
            on = i <= n
            t.opacity = 1 if on else 0.4
            t.scale = 1.08 if i == n else (1 if on else 0.92)
            t.border = ft.Border.all(3, T.GOLD if i == n else "#00000000")
            t.bgcolor = "#FFF8E6" if i == n else None
            t.shadow = ft.BoxShadow(blur_radius=22, spread_radius=1, color="#66E0A526") if i == n else None

    def play(self):
        g = BY_KEY[self.sec]
        self.token += 1
        token = self.token
        self.ctx.say_help(self.sec, g["voice"])
        mp3 = help_mp3(self.sec)
        total = os.path.getsize(mp3) * 8 / 48000 if mp3 else max(len(g["voice"]) / 4.2, 3)
        per = total / len(self.tiles)

        def run():
            for i in range(len(self.tiles)):
                if token != self.token:
                    return
                self._light(i)
                try:
                    self.update()
                except Exception:
                    return
                time.sleep(per)
            if token == self.token:
                self._light(len(self.tiles))
                for t in self.tiles:
                    t.scale, t.border, t.bgcolor, t.shadow = 1, ft.Border.all(3, "#00000000"), None, None
                try:
                    self.update()
                except Exception:
                    pass
        threading.Thread(target=run, daemon=True).start()

    def stop(self, refresh=True):
        self.token += 1
        self.ctx.stop_voice()
        self._light(-1)
        if refresh:
            self.update()
