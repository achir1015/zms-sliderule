r"""開發用：在開發資料庫（data/）建立 admin/admin123、學生 student/student1，
並替學生做幾回讀尺練習與計算示範（讓成長圖表有資料）。用法：python tools/demo_data.py [--reset]"""
import os
import random
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from sr.biz import Biz  # noqa: E402
from sr.database import DB  # noqa: E402
from sr.dbserver import LocalDatabaseServer  # noqa: E402
from sr.seed import ROLES  # noqa: E402
from sr.settings import Settings  # noqa: E402

st = Settings.load()
srv = LocalDatabaseServer(st)
srv.start()
try:
    db = DB(st)
    if "--reset" in sys.argv:
        c = db.connect(use_db=False)
        with c.cursor() as cur:
            cur.execute("DROP DATABASE IF EXISTS `%s`" % st.database)
        c.close()
    db.prepare()
    st.save()
    b = Biz(db)
    if not b.has_users():
        b.create_first_admin("admin", "系統管理員", "admin123")
    b.login("admin", "admin123")
    b.save_company(name="資料助秘數學教室")
    if not db.value("SELECT 1 FROM sys_user WHERE uid='student'"):
        b.save_user("student", "王小明", "學生", False, True, ROLES["學生"], pw="student1", is_new=True, dept="三年甲班")
    if not db.value("SELECT 1 FROM sr_layout"):
        b.save_layout("老師的乘除尺", ["DF"], ["CF", "CI", "C"], ["D"], shared=True, note="摺疊刻度練習")
    s = Biz(db)
    s.login("student", "student1")
    if not db.value("SELECT COUNT(*) FROM sr_drill WHERE uid='student'"):
        for i, (kind, rate) in enumerate([("MUL", .5), ("MUL", .6), ("DIV", .6), ("POW", .7), ("MIX", .7),
                                          ("TRIG", .8), ("LOG", .8), ("MIX", .9)]):
            did = s.start_drill(kind)
            for it in s.drill(did)["items"]:
                ans = float(it["answer"])
                g = ans * (1 + random.uniform(-0.004, 0.004)) if random.random() < rate else ans * random.choice([1.05, 0.9, 10])
                s.answer_drill(did, it["seq"], "%.4g" % g)
            s.finish_drill(did)
            db.exec("UPDATE sr_drill SET finished_at=DATE_SUB(NOW(), INTERVAL %s DAY), seconds=%s, "
                    "started_at=DATE_SUB(NOW(), INTERVAL %s DAY) WHERE id=%s",
                    (16 - i * 2, random.randint(180, 600), 16 - i * 2, did))
        for e, r in (("2×3.5", "7"), ("√20", "4.47"), ("sin 30", "0.5")):
            s.add_history(e, r)
    print("ok", s.growth()["summary"])
finally:
    db.close()
    srv.stop()
