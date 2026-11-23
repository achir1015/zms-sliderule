"""成績統計（全部使用者）與練習設定。"""
import flet as ft

from . import theme as T

I = ft.Icons


class Scores(ft.Column):
    def __init__(self, ctx, **kw):
        self.ctx = ctx
        b = ctx.books
        self.grid = T.Grid([("uid", "帳號", "s", 90), ("name", "姓名", "s", 110), ("dept", "班別", "s", 120),
                            ("n", "練習回數", "s", 70), ("last_s", "最近分數", "s", 70), ("best_s", "最高分", "s", 60),
                            ("avg_s", "平均", "s", 60), ("demos", "示範次數", "s", 70), ("when", "最近練習", "s", 150)],
                           on_pick=lambda r: ctx.app.go("growth", uid=r["uid"]), height=560)
        rows = []
        for r in b.score_board():
            rows.append(dict(r, last_s="%g" % float(r["last_score"]) if r["last_score"] is not None else "",
                             best_s="%g" % float(r["best"]) if r["best"] is not None else "",
                             avg_s="%g" % float(r["avg"]) if r["avg"] is not None else "", when=T.show(r["last_at"])))
        self.grid.set_rows(rows)
        super().__init__([
            T.page_header(I.LEADERBOARD, "成績統計", "全部使用者的讀尺練習成績（點一列看該使用者的成長圖表）", "violet",
                          [ctx.export_button(self.grid, "練習成績")]),
            self.grid], spacing=12, expand=True)


class Settings(ft.Column):
    def __init__(self, ctx, **kw):
        self.ctx = ctx
        c = ctx.books.company()
        self.name = T.field("單位名稱（公司、學校或班級）", c.get("name") or "", width=420)
        self.size = T.field("讀尺練習每回題數", c.get("drill_size") or 10, width=170, suffix="題")
        self.tol = T.field("容許誤差", "%g" % float(c.get("tolerance") or 1), width=150, suffix="%",
                           helper="計算尺約可讀 3 位，建議 1%")
        self.pass_ = T.field("及格分數", c.get("pass_score") or 60, width=150, suffix="分")
        super().__init__([
            T.page_header(I.TUNE, "練習設定", "單位名稱、讀尺練習題數、容許誤差與及格分數（所有使用者共用）", "pink",
                          [T.btn("儲存", I.SAVE, lambda e: self.save())]),
            T.card(ft.Column([
                self.name, ft.Row([self.size, self.tol, self.pass_], spacing=14, wrap=True),
                T.muted("說明：答案和正確值的相對誤差在容許範圍內就算答對；按「看示範」的題目不計分。"
                        "一般十英寸計算尺可讀到 3 位有效數字（約 0.1%～0.5%）。", 12)], spacing=14), padding=22)],
            spacing=14, expand=True, scroll=ft.ScrollMode.AUTO)

    def save(self):
        self.ctx.guard(self.ctx.books.save_company, name=self.name.value, drill_size=self.size.value,
                       tolerance=self.tol.value, pass_score=self.pass_.value, ok="練習設定已儲存")
