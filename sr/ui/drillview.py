"""讀尺練習（出題、作答、看示範、完成）與我的成績成長。"""
import flet as ft

from .. import rocdate
from ..demo import plan, sig
from ..seed import DRILL_KINDS
from . import theme as T
from .charts import bars, line_chart
from .rulescreen import RuleScreen

I = ft.Icons

KIND_ICON = {"MUL": (I.CLOSE, "blue"), "DIV": (I.SAFETY_DIVIDER, "teal"), "POW": (I.SUPERSCRIPT, "violet"),
             "RECIP": (I.SWAP_VERT, "rose"), "TRIG": (I.CHANGE_HISTORY, "amber"), "LOG": (I.TRENDING_UP, "green"),
             "MIX": (I.SHUFFLE, "slate")}
KIND_NOTE = {"MUL": "C、D 刻度：兩數相乘", "DIV": "C、D 刻度：兩數相除", "POW": "A、K 刻度：平方、立方、根號",
             "RECIP": "CI 刻度：1/x", "TRIG": "S、T、ST 刻度：sin、cos、tan", "LOG": "L、Ln、LL 刻度：log、ln、eˣ",
             "MIX": "各種題型混合"}


class Drill(ft.Column):
    def __init__(self, ctx, did=None, **kw):
        super().__init__(spacing=14, expand=True, scroll=ft.ScrollMode.AUTO)
        self.ctx = ctx
        self.b = ctx.books
        self.did = did or self.b.open_drill()
        self.cur = 0
        if self.did:
            self.session()
        else:
            self.chooser()

    # ---------------------------------------------------------------- 選題型
    def chooser(self):
        c = self.b.company()
        cards = []
        for k, name in DRILL_KINDS.items():
            ic, tone = KIND_ICON[k]
            cards.append(ft.Container(T.card(ft.Column([
                T.icon_tile(ic, tone, 52, radius=16), ft.Text(name, size=17, weight=ft.FontWeight.W_800),
                T.muted(KIND_NOTE[k], 12), T.btn("開始", I.PLAY_ARROW, lambda e, k=k: self.start(k))],
                spacing=8, horizontal_alignment=ft.CrossAxisAlignment.START), padding=18), width=250))
        self.controls = [
            T.page_header(I.EDIT_NOTE, "讀尺練習", "每回 %d 題；用計算尺算出答案後輸入，誤差 %g%% 以內算答對" % (
                c.get("drill_size") or 10, float(c.get("tolerance") or 1)), "teal"),
            ft.Row(cards, wrap=True, spacing=14, run_spacing=14)]

    def start(self, kind):
        did = self.ctx.guard(self.b.start_drill, kind)
        if did:
            self.did = did
            self.cur = 0
            self.session()
            self.update()

    # ---------------------------------------------------------------- 作答
    def session(self):
        d = self.b.drill(self.did)
        self.d = d
        if d["status"] == "DONE":
            self.result(d)
            return
        items = d["items"]
        first_open = next((i for i, it in enumerate(items) if it["given"] is None), 0)
        self.cur = min(self.cur or first_open, len(items) - 1)
        self.nums = ft.Row(wrap=True, spacing=6, run_spacing=6)
        self.q_title = ft.Text("", size=13, color=T.MUTED)
        self.q_expr = ft.Text("", size=34, weight=ft.FontWeight.W_800, color=T.PRIMARY)
        self.ans = T.field("你讀到的答案", "", width=220, on_submit=lambda e: self.submit(),
                           keyboard_type=ft.KeyboardType.NUMBER)
        self.feedback = ft.Container()
        self.ok_btn = T.btn("確定", I.CHECK, lambda e: self.submit())
        self.next_btn = T.btn("下一題", I.ARROW_FORWARD, lambda e: self.goto(self.cur + 1), kind="outline")
        self.rule = RuleScreen(self.ctx, compact=True)
        head = T.card(ft.Row([
            ft.Column([self.q_title, self.q_expr], spacing=0, width=300),
            ft.Column([ft.Row([self.ans, self.ok_btn, self.next_btn,
                               T.btn("看示範（不計分）", I.RECORD_VOICE_OVER, lambda e: self.hint(), kind="ghost")],
                              spacing=8, wrap=True), self.feedback], spacing=8, expand=True),
            ft.Column([T.muted("題號", 11), self.nums,
                       T.btn("完成練習", I.TASK_ALT, lambda e: self.finish(), bgcolor=T.GOLD)], spacing=6, width=330)],
            spacing=18, vertical_alignment=ft.CrossAxisAlignment.START), padding=18)
        kind = DRILL_KINDS.get(d["kind"], d["kind"])
        self.controls = [T.page_header(I.EDIT_NOTE, "讀尺練習：%s" % kind,
                                       "容許誤差 %g%%；看過示範的題目不計分" % float(d["tolerance"]), "teal"),
                         head, self.rule]
        self.show_q()

    def show_q(self):
        items = self.d["items"]
        it = items[self.cur]
        self.q_title.value = "第 %d 題，共 %d 題" % (self.cur + 1, len(items))
        self.q_expr.value = "%s = ?" % it["expr"]
        self.ans.value = "" if it["given"] is None else sig(float(it["given"]), 6)
        self.feedback.content = self._fb(it) if it["given"] is not None else None
        self.next_btn.disabled = self.cur >= len(items) - 1
        chips = []
        for i, x in enumerate(items):
            done = x["given"] is not None
            bg = (T.SUCCESS if x["ok"] else T.DANGER) if done else ("#FDE68A" if x["hinted"] else "#EEF2F7")
            chips.append(ft.Container(ft.Text(str(i + 1), size=12, weight=ft.FontWeight.W_700,
                                              color=ft.Colors.WHITE if done else T.TEXT),
                                      width=30, height=30, border_radius=8, bgcolor=bg, alignment=ft.Alignment.CENTER,
                                      border=ft.Border.all(2, T.PRIMARY if i == self.cur else "#00000000"),
                                      on_click=lambda e, i=i: self.goto(i), ink=True))
        self.nums.controls = chips
        try:
            pl = plan(it["expr"])
            self.rule.ensure_scales(pl["layout"], pl["needs"])
        except ValueError:
            pass

    def _fb(self, it):
        ok = bool(it["ok"])
        txt = "答對了！" if ok else ("看過示範，這題不計分" if it["hinted"] and float(it["err_pct"] or 0) <= float(
            self.d["tolerance"]) else "差一點，再算一次也可以")
        return ft.Container(ft.Row([
            ft.Icon(I.CHECK_CIRCLE if ok else I.INFO, color=T.SUCCESS if ok else T.WARN),
            ft.Text(txt, size=14, weight=ft.FontWeight.W_700, color=T.SUCCESS if ok else T.WARN),
            T.muted("正確答案 %s　你的答案 %s　誤差 %.2f%%" % (sig(float(it["answer"]), 6), sig(float(it["given"]), 6),
                                                    float(it["err_pct"] or 0)), 13)], spacing=8, wrap=True),
            bgcolor="#ECFDF5" if ok else "#FFF7ED", border_radius=10, padding=10)

    def goto(self, i):
        if 0 <= i < len(self.d["items"]):
            self.rule.stop_demo()
            self.cur = i
            self.show_q()
            self.update()

    def submit(self):
        it = self.d["items"][self.cur]
        r = self.ctx.guard(self.b.answer_drill, self.did, it["seq"], self.ans.value)
        if not r or r is True:
            return
        self.d["items"][self.cur].update(r)
        self.show_q()
        self.update()

    def hint(self):
        it = self.d["items"][self.cur]
        r = self.ctx.guard(self.b.answer_drill, self.did, it["seq"], None, hinted=True)
        if not r:
            return
        it["hinted"] = 1
        self.show_q()
        self.update()
        self.rule.expr.value = it["expr"]
        self.rule.run_demo()

    def finish(self):
        left = sum(1 for x in self.d["items"] if x["given"] is None)

        def go():
            self.rule.stop_demo()
            d = self.ctx.guard(self.b.finish_drill, self.did)
            if d and d is not True:
                self.result(d)
                self.update()
                self.ctx.say_text("練習完成，得分 %g 分" % float(d["score"]))
        if left:
            self.ctx.confirm("完成練習", "還有 %d 題沒有作答，確定要完成這回練習？" % left, go, danger=False)
        else:
            go()

    # ---------------------------------------------------------------- 結果
    def result(self, d):
        c = self.b.company()
        passed = float(d["score"]) >= float(c.get("pass_score") or 60)
        rows = []
        for it in d["items"]:
            rows.append(ft.Container(ft.Row([
                ft.Text(str(it["seq"]), width=30, color=T.MUTED),
                ft.Text(it["expr"], size=15, weight=ft.FontWeight.W_600, width=160),
                ft.Text("正確 %s" % sig(float(it["answer"]), 6), width=150),
                ft.Text("你的 %s" % (sig(float(it["given"]), 6) if it["given"] is not None else "未作答"), width=150),
                ft.Text("誤差 %.2f%%" % float(it["err_pct"]) if it["err_pct"] is not None else "", width=110),
                T.chip("答對" if it["ok"] else ("看示範" if it["hinted"] else "答錯"),
                       "green" if it["ok"] else ("amber" if it["hinted"] else "rose")),
                ft.TextButton("再看示範", icon=I.PLAY_CIRCLE,
                              on_click=lambda e, x=it["expr"]: self.ctx.app.go("rule", expr=x, autoplay=True))],
                spacing=10), padding=8, border=ft.Border.only(bottom=ft.BorderSide(1, T.LINE))))
        self.controls = [
            T.page_header(I.TASK_ALT, "練習完成：%s" % DRILL_KINDS.get(d["kind"], d["kind"]),
                          "答對 %d 題，共 %d 題　用時 %d 分 %d 秒" % (d["correct"], d["q_count"], d["seconds"] // 60,
                                                          d["seconds"] % 60), "green" if passed else "amber",
                          [T.btn("再練一回", I.REPLAY, lambda e: self.again(d["kind"])),
                           T.btn("我的成績", I.SHOW_CHART, lambda e: self.ctx.app.go("growth"), kind="outline")]),
            T.card(ft.Row([ft.Text("%g" % float(d["score"]), size=56, weight=ft.FontWeight.W_800,
                                   color=T.SUCCESS if passed else T.WARN),
                           ft.Column([ft.Text("分", size=18), T.muted("及格 %d 分" % (c.get("pass_score") or 60))],
                                     spacing=0)], spacing=8), padding=18),
            T.card(ft.Column(rows, spacing=0), padding=12)]

    def again(self, kind):
        self.did = None
        self.start(kind)


class Growth(ft.Column):
    def __init__(self, ctx, uid=None, **kw):
        self.ctx = ctx
        b = ctx.books
        g = b.growth(uid)
        hist = g["history"]
        s = g["summary"]
        c = b.company()
        who = ""
        if uid and uid != b.uid:
            who = next((u["name"] for u in b.users() if u["uid"] == uid), uid) if b.can("SYS", 2) else uid
        kinds = [(DRILL_KINDS.get(k["kind"], k["kind"]), round(100.0 * float(k["c"] or 0) / max(1, k["n"]), 1),
                  "%d 題　平均誤差 %.2f%%" % (k["n"], float(k["e"] or 0))) for k in g["kinds"]]
        rows = []
        for h in reversed(hist[-50:]):
            rows.append(ft.Container(ft.Row([
                ft.Text(T.show(h["finished_at"]), width=170),
                ft.Text(DRILL_KINDS.get(h["kind"], h["kind"]), width=150),
                ft.Text("%d／%d" % (h["correct"], h["q_count"]), width=80),
                ft.Text("%g 分" % float(h["score"]), width=80, weight=ft.FontWeight.W_700),
                ft.Text("%d 分 %d 秒" % (h["seconds"] // 60, h["seconds"] % 60), width=110),
                ft.TextButton("看這回", icon=I.VISIBILITY,
                              on_click=lambda e, i=h["id"]: ctx.app.go("drill", did=i))], spacing=10),
                padding=6, border=ft.Border.only(bottom=ft.BorderSide(1, T.LINE))))
        super().__init__([
            T.page_header(I.SHOW_CHART, "我的成績與成長" if not who else "%s 的成績與成長" % who,
                          "練習 %d 回　最近 %g 分　最高 %g 分　平均 %g 分" % (s["count"], s["last"], s["best"], s["avg"]),
                          "teal"),
            ft.Row([T.card(ft.Column([T.title_text("分數成長", 16),
                                      line_chart([float(h["score"]) for h in hist[-20:]],
                                                 [rocdate.show(h["finished_at"].date())[4:] for h in hist[-20:]],
                                                 width=620, height=240, pass_line=int(c.get("pass_score") or 60))
                                      if hist else T.empty_state(I.SHOW_CHART, "還沒有成績", "到讀尺練習做第一回")],
                                     spacing=8), padding=18, expand=3),
                    T.card(ft.Column([T.title_text("各題型答對率", 16),
                                      bars(kinds, 200) if kinds else T.muted("還沒有資料", 13)], spacing=10),
                           padding=18, expand=2)], spacing=14, vertical_alignment=ft.CrossAxisAlignment.START,
                   data="split"),
            T.card(ft.Column([T.title_text("練習紀錄", 16)] + (rows or [T.muted("還沒有練習紀錄", 13)]), spacing=0),
                   padding=14)], spacing=14, expand=True, scroll=ft.ScrollMode.AUTO)
