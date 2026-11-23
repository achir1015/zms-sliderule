"""計算尺業務：自訂尺型、個人偏好、計算紀錄、讀尺練習（出題、評分、成績）。"""
import datetime as dt
import json
import math
import random

from . import rule as R
from .core import BizError
from .seed import DRILL_KINDS


def _round_sig(x, n=3):
    if x == 0:
        return 0.0
    return round(x, n - 1 - math.floor(math.log10(abs(x))))


def _rand(lo, hi, digits=2):
    """lo～hi 之間、有效數字 digits 位的隨機數（計算尺好讀的數字）。"""
    while True:
        x = _round_sig(random.uniform(lo, hi), digits)
        if lo <= x <= hi and x not in (1, 10, 100):
            return x


def _fmt(x):
    s = ("%.6f" % x).rstrip("0").rstrip(".")
    return s


def make_problem(kind):
    """回傳 (算式, 正確答案)。算式都是 demo.plan() 看得懂的寫法（可以按示範）。"""
    k = kind if kind != "MIX" else random.choice(["MUL", "MUL", "DIV", "DIV", "POW", "RECIP", "TRIG", "LOG"])
    if k == "MUL":
        a = _rand(1.1, 9.9) * random.choice([1, 1, 10, 0.1])
        b = _rand(1.1, 9.9) * random.choice([1, 1, 10])
        a, b = _round_sig(a, 2), _round_sig(b, 2)
        return "%s×%s" % (_fmt(a), _fmt(b)), a * b
    if k == "DIV":
        a = _round_sig(_rand(1.1, 9.9) * random.choice([1, 10, 100]), 3)
        b = _round_sig(_rand(1.1, 9.9), 2)
        return "%s÷%s" % (_fmt(a), _fmt(b)), a / b
    if k == "POW":
        t = random.choice(["sq", "sqrt", "cube", "cbrt"])
        if t == "sq":
            a = _rand(1.1, 9.9)
            return "%s²" % _fmt(a), a * a
        if t == "sqrt":
            a = _rand(2, 99)
            return "√%s" % _fmt(a), math.sqrt(a)
        if t == "cube":
            a = _rand(1.1, 4.9)
            return "%s³" % _fmt(a), a ** 3
        a = _rand(2, 900)
        return "∛%s" % _fmt(a), a ** (1 / 3)
    if k == "RECIP":
        a = _rand(1.1, 9.9, 3)
        return "1/%s" % _fmt(a), 1 / a
    if k == "TRIG":
        t = random.choice(["sin", "cos", "tan"])
        th = random.randint(8, 80) if t != "tan" else random.randint(8, 75)
        v = {"sin": math.sin, "cos": math.cos, "tan": math.tan}[t](math.radians(th))
        return "%s %d" % (t, th), v
    if k == "LOG":
        t = random.choice(["log", "ln", "exp"])
        if t == "log":
            a = _rand(1.1, 99)
            return "log %s" % _fmt(a), math.log10(a)
        if t == "ln":
            a = _rand(1.1, 99)
            return "ln %s" % _fmt(a), math.log(a)
        x = _rand(0.2, 5, 2)
        return "e^%s" % _fmt(x), math.exp(x)
    raise BizError("不支援的題型")


class RuleMixin:
    # ================================================================ 尺型
    def my_layouts(self):
        if not self.can("RULE", 1):
            return []
        if self.can("LAYOUT", 1):
            return self.db.rows("SELECT * FROM sr_layout WHERE owner=%s OR shared=1 ORDER BY shared, name", (self.uid,))
        return self.db.rows("SELECT * FROM sr_layout WHERE owner=%s ORDER BY name", (self.uid,))

    def save_layout(self, name, upper, slide, lower, shared=False, note="", lid=None):
        self.need("RULE", 2)
        name = (name or "").strip()[:60]
        if not name:
            raise BizError("請輸入尺型名稱")
        for k in list(upper) + list(slide) + list(lower):
            if k not in R.BY_KEY:
                raise BizError("沒有這個刻度：%s" % k)
        if not slide:
            raise BizError("滑尺至少要有一個刻度")
        if shared:
            self.need("LAYOUT", 2)
        vals = (name, ",".join(upper), ",".join(slide), ",".join(lower), (note or "")[:200], int(bool(shared)))
        if lid:
            r = self.db.row("SELECT * FROM sr_layout WHERE id=%s", (lid,))
            if not r:
                raise BizError("找不到這個尺型")
            if r["owner"] != self.uid:
                self.need("LAYOUT", 2)
            self.db.exec("UPDATE sr_layout SET name=%s, upper=%s, slide=%s, lower=%s, note=%s, shared=%s WHERE id=%s",
                         vals + (lid,))
        else:
            lid = self.db.exec("INSERT INTO sr_layout (name, upper, slide, lower, note, shared, owner) "
                               "VALUES (%s, %s, %s, %s, %s, %s, %s)", vals + (self.uid,))
        self.log("layout_save", name, json.dumps({"upper": upper, "slide": slide, "lower": lower, "shared": shared},
                                                 ensure_ascii=False))
        return lid

    def delete_layout(self, lid):
        r = self.db.row("SELECT * FROM sr_layout WHERE id=%s", (lid,))
        if not r:
            return
        if r["owner"] != self.uid:
            self.need("LAYOUT", 2)
        self.db.exec("DELETE FROM sr_layout WHERE id=%s", (lid,))
        self.log("layout_delete", r["name"])

    # ================================================================ 偏好
    def pref(self):
        r = self.db.row("SELECT * FROM sr_pref WHERE uid=%s", (self.uid,)) or {}
        out = {"layout": r.get("layout") or "student"}
        try:
            out.update(json.loads(r.get("data") or "{}"))
        except ValueError:
            pass
        return out

    def save_pref(self, layout=None, **data):
        if not self.user:
            return
        cur = self.pref()
        cur.update({k: v for k, v in data.items() if v is not None})
        lay = layout or cur.pop("layout", "student")
        cur.pop("layout", None)
        self.db.exec("REPLACE INTO sr_pref (uid, layout, data) VALUES (%s, %s, %s)",
                     (self.uid, lay[:20], json.dumps(cur, ensure_ascii=False)))

    # ================================================================ 計算紀錄
    def add_history(self, expr, result, mode="DEMO"):
        if not self.user:
            return
        self.db.exec("INSERT INTO sr_history (uid, expr, result, mode) VALUES (%s, %s, %s, %s)",
                     (self.uid, (expr or "")[:80], (result or "")[:40], mode[:6]))

    def history(self, uid=None, limit=300):
        uid = uid or self.uid
        if uid != self.uid:
            self.need("RPT", 1)
        return self.db.rows("SELECT * FROM sr_history WHERE uid=%s ORDER BY id DESC LIMIT %s", (uid, limit))

    def clear_history(self):
        self.db.exec("DELETE FROM sr_history WHERE uid=%s", (self.uid,))
        self.log("history_clear", self.uid)

    # ================================================================ 讀尺練習
    def start_drill(self, kind="MIX", n=None):
        self.need("DRILL", 1)
        if kind not in DRILL_KINDS:
            raise BizError("沒有這種練習")
        c = self.company()
        n = int(n or c.get("drill_size") or 10)
        tol = float(c.get("tolerance") or 1)
        seen, items = set(), []
        while len(items) < n:
            expr, ans = make_problem(kind)
            if expr in seen:
                continue
            seen.add(expr)
            items.append((expr, ans))
        with self.db.transaction():
            did = self.db.exec("INSERT INTO sr_drill (uid, kind, q_count, tolerance) VALUES (%s, %s, %s, %s)",
                               (self.uid, kind, n, tol))
            self.db.exec_many("INSERT INTO sr_drill_item (drill_id, seq, expr, answer) VALUES (%s, %s, %s, %s)",
                              [(did, i + 1, e, a) for i, (e, a) in enumerate(items)])
        self.log("drill_start", did, DRILL_KINDS[kind])
        return did

    def open_drill(self):
        r = self.db.row("SELECT id FROM sr_drill WHERE uid=%s AND status='OPEN' ORDER BY id DESC LIMIT 1", (self.uid,))
        return r["id"] if r else None

    def drill(self, did):
        d = self.db.row("SELECT * FROM sr_drill WHERE id=%s", (did,))
        if not d:
            raise BizError("找不到這回練習")
        if d["uid"] != self.uid:
            self.need("RPT", 1)
        d["items"] = self.db.rows("SELECT * FROM sr_drill_item WHERE drill_id=%s ORDER BY seq", (did,))
        return d

    def answer_drill(self, did, seq, given, hinted=None):
        d = self.db.row("SELECT * FROM sr_drill WHERE id=%s", (did,))
        if not d or d["uid"] != self.uid:
            raise BizError("找不到這回練習")
        if d["status"] != "OPEN":
            raise BizError("這回練習已經完成")
        it = self.db.row("SELECT * FROM sr_drill_item WHERE drill_id=%s AND seq=%s", (did, seq))
        if not it:
            raise BizError("沒有這一題")
        if hinted:
            self.db.exec("UPDATE sr_drill_item SET hinted=1 WHERE drill_id=%s AND seq=%s", (did, seq))
            it["hinted"] = 1
        if given is None or given == "":
            return it
        try:
            g = float(str(given).replace(",", "").strip())
        except ValueError:
            raise BizError("請輸入數字")
        ans = float(it["answer"])
        err = abs(g - ans) / abs(ans) * 100 if ans else abs(g) * 100
        ok = err <= float(d["tolerance"]) + 1e-9 and not it["hinted"]
        self.db.exec("UPDATE sr_drill_item SET given=%s, err_pct=%s, ok=%s WHERE drill_id=%s AND seq=%s",
                     (g, min(err, 99999), int(ok), did, seq))
        self._drill_totals(did)
        it.update(given=g, err_pct=err, ok=int(ok))
        return it

    def _drill_totals(self, did):
        r = self.db.row("SELECT COUNT(given) a, SUM(ok) c, COUNT(*) n FROM sr_drill_item WHERE drill_id=%s", (did,))
        n, c = int(r["n"] or 1), int(r["c"] or 0)
        self.db.exec("UPDATE sr_drill SET answered=%s, correct=%s, score=%s WHERE id=%s",
                     (int(r["a"] or 0), c, round(100.0 * c / n, 1), did))

    def finish_drill(self, did):
        d = self.db.row("SELECT * FROM sr_drill WHERE id=%s", (did,))
        if not d or d["uid"] != self.uid:
            raise BizError("找不到這回練習")
        self._drill_totals(did)
        secs = int((dt.datetime.now() - d["started_at"]).total_seconds())
        self.db.exec("UPDATE sr_drill SET status='DONE', finished_at=NOW(), seconds=%s WHERE id=%s", (secs, did))
        self.log("drill_done", did)
        return self.drill(did)

    def growth(self, uid=None):
        uid = uid or self.uid
        if uid != self.uid:
            self.need("RPT", 1)
        hist = self.db.rows("SELECT * FROM sr_drill WHERE uid=%s AND status='DONE' ORDER BY finished_at", (uid,))
        kinds = self.db.rows(
            "SELECT d.kind, COUNT(*) n, SUM(i.ok) c, AVG(i.err_pct) e FROM sr_drill_item i JOIN sr_drill d "
            "ON d.id=i.drill_id WHERE d.uid=%s AND d.status='DONE' AND i.given IS NOT NULL GROUP BY d.kind", (uid,))
        scores = [float(h["score"]) for h in hist]
        summ = {"count": len(hist), "last": scores[-1] if scores else 0, "best": max(scores) if scores else 0,
                "avg": round(sum(scores) / len(scores), 1) if scores else 0}
        return {"history": hist, "kinds": kinds, "summary": summ}

    def score_board(self):
        self.need("RPT", 1)
        return self.db.rows(
            "SELECT u.uid, u.name, u.dept, COUNT(d.id) n, MAX(d.score) best, ROUND(AVG(d.score),1) avg, "
            "MAX(d.finished_at) last_at, (SELECT score FROM sr_drill x WHERE x.uid=u.uid AND x.status='DONE' "
            "ORDER BY x.finished_at DESC LIMIT 1) last_score, "
            "(SELECT COUNT(*) FROM sr_history h WHERE h.uid=u.uid) demos "
            "FROM sys_user u LEFT JOIN sr_drill d ON d.uid=u.uid AND d.status='DONE' GROUP BY u.uid ORDER BY u.uid")

    def home_stats(self):
        g = self.growth() if self.can("DRILL", 1) else {"summary": {}, "history": [], "kinds": []}
        demos = self.db.value("SELECT COUNT(*) FROM sr_history WHERE uid=%s", (self.uid,)) or 0
        layouts = self.db.value("SELECT COUNT(*) FROM sr_layout WHERE owner=%s OR shared=1", (self.uid,)) or 0
        recent = self.db.rows("SELECT * FROM sr_history WHERE uid=%s ORDER BY id DESC LIMIT 8", (self.uid,))
        return {"growth": g, "demos": demos, "layouts": layouts, "recent": recent}
