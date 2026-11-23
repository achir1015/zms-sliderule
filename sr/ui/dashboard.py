"""首頁：打開計算尺、快速示範、練習成績、最近算過的算式。"""
import datetime as dt

import flet as ft

from .. import rocdate
from ..demo import PRESETS
from ..seed import DRILL_KINDS
from . import theme as T
from .charts import line_chart

I = ft.Icons


def greet():
    h = dt.datetime.now().hour
    return "早安" if h < 11 else "午安" if h < 14 else "下午好" if h < 18 else "晚安"


class Dashboard(ft.Column):
    def __init__(self, ctx, **kw):
        self.ctx = ctx
        b = ctx.books
        app = ctx.app
        u = b.user
        comp = b.company()
        st = b.home_stats()
        g = st["growth"]
        gs = g["summary"]
        hist = g["history"]
        can_drill = b.can("DRILL", 1)
        hero = ft.Container(ft.Row([
            ft.Column([ft.Text("%s，%s" % (u["name"], greet()), size=24, weight=ft.FontWeight.W_800,
                               color=ft.Colors.WHITE),
                       ft.Text(((comp.get("name") or "") + "　").lstrip("　") + "虛擬計算尺：拖曳、無限放大、語音示範",
                               size=14, color="#DCE6F5"),
                       ft.Row([hero_chip(I.CALENDAR_TODAY, rocdate.show(rocdate.today())),
                               hero_chip(I.STRAIGHTEN, "25 種刻度"), hero_chip(I.DASHBOARD_CUSTOMIZE, "7 種尺型"),
                               hero_chip(I.RECORD_VOICE_OVER, "語音示範")], spacing=8, wrap=True),
                       ft.Row([T.btn("打開計算尺", I.STRAIGHTEN, lambda e: app.go("rule"), bgcolor=T.GOLD)] +
                              ([T.btn("開始讀尺練習", I.EDIT_NOTE, lambda e: app.go("drill"), bgcolor="#2B5BA0")]
                               if can_drill else []), spacing=10)],
                      spacing=8, expand=True),
            ft.Image(src="icon.png", width=110, height=110)]), padding=24, border_radius=20,
            gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                                       colors=[T.SIDEBAR_TOP, "#1E4D8C", "#B7791F"]))
        ks = T.kpis([
            T.kpi("計算示範", str(st["demos"]), I.RECORD_VOICE_OVER, "rose", "我做過的示範", lambda e: app.go("history")),
            T.kpi("練習回數", str(gs.get("count", 0)), I.ASSIGNMENT_TURNED_IN, "teal", "讀尺練習",
                  lambda e: app.go("growth") if can_drill else None),
            T.kpi("最近一回", "%g 分" % gs.get("last", 0), I.SCHEDULE, "amber",
                  T.show(hist[-1]["finished_at"]) if hist else "還沒練習",
                  lambda e: app.go("growth") if can_drill else None),
            T.kpi("最高分", "%g 分" % gs.get("best", 0), I.EMOJI_EVENTS, "violet", "平均 %g" % gs.get("avg", 0),
                  lambda e: app.go("growth") if can_drill else None),
            T.kpi("我的尺型", str(st["layouts"]), I.DASHBOARD_CUSTOMIZE, "blue", "含分享的尺型",
                  lambda e: app.go("layouts"))])
        quick = T.card(ft.Column([
            ft.Row([T.icon_tile(I.PLAY_CIRCLE, "rose", 34), ft.Text("點一下，看小柯示範", size=16,
                                                                     weight=ft.FontWeight.W_700, expand=True)]),
            ft.Row([ft.OutlinedButton(p, on_click=lambda e, p=p: app.go("rule", expr=p, autoplay=True))
                    for p in PRESETS], wrap=True, spacing=8, run_spacing=8),
            ft.Divider(height=8, color=T.LINE),
            ft.Row([T.icon_tile(I.HISTORY_EDU, "slate", 30, radius=9), ft.Text("最近算過", size=14,
                                                                             weight=ft.FontWeight.W_700)]),
            ft.Column([ft.Row([ft.Text(r["expr"], size=14, width=140, weight=ft.FontWeight.W_600),
                               ft.Text("≈ " + r["result"], size=14, color=T.PRIMARY, expand=True),
                               T.muted(T.show(r["at"]), 11)]) for r in st["recent"]] or
                      [T.muted("還沒有計算紀錄", 13)], spacing=6)], spacing=10), padding=18, expand=2)
        chart = T.card(ft.Column([
            ft.Row([T.icon_tile(I.SHOW_CHART, "teal", 34), ft.Text("我的讀尺練習成績", size=16,
                                                                    weight=ft.FontWeight.W_700, expand=True),
                    T.btn("看全部", I.CHEVRON_RIGHT, lambda e: app.go("growth"), kind="ghost") if can_drill else
                    ft.Container()]),
            line_chart([float(h["score"]) for h in hist[-15:]],
                       [rocdate.show(h["finished_at"].date())[4:] for h in hist[-15:]], width=560, height=220,
                       pass_line=int(comp.get("pass_score") or 60)) if hist else
            T.empty_state(I.SHOW_CHART, "還沒有成績", "到讀尺練習做第一回（%s等七種題型）" % "、".join(
                list(DRILL_KINDS.values())[:3]))], spacing=8),
            padding=18, expand=3)
        super().__init__([hero, ks, ft.Row([chart, quick], spacing=14, vertical_alignment=ft.CrossAxisAlignment.START,
                                           data="split")], spacing=16, expand=True, scroll=ft.ScrollMode.AUTO)


def hero_chip(icon, text):
    return ft.Container(ft.Row([ft.Icon(icon, size=14, color="#DCE6F5"), ft.Text(text, size=12, color="#DCE6F5")],
                               spacing=4, tight=True), bgcolor="#22FFFFFF", border_radius=20,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=4))
