"""資料庫業務：尺型、計算紀錄、讀尺練習評分與權限。"""
import pytest

from sr.core import BizError
from sr.seed import ROLES


def test_layouts_and_permissions(biz, db):
    from sr.biz import Biz
    biz.save_user("stu", "學生", "學生", False, True, ROLES["學生"], pw="stu123", is_new=True)
    lid = biz.save_layout("共用", ["A"], ["B", "C"], ["D"], shared=True)
    s = Biz(db)
    s.login("stu", "stu123")
    assert any(r["id"] == lid for r in s.my_layouts())
    my = s.save_layout("我的", [], ["C"], ["D"])
    with pytest.raises(BizError):
        s.save_layout("分享", [], ["C"], ["D"], shared=True)      # 學生不能分享
    with pytest.raises(BizError):
        s.delete_layout(lid)                                     # 也不能刪老師的
    s.delete_layout(my)
    with pytest.raises(BizError):
        s.save_layout("壞", [], ["XX"], ["D"])


def test_drill_scoring(biz):
    biz.save_company(drill_size=5, tolerance=1)
    did = biz.start_drill("MUL")
    d = biz.drill(did)
    assert len(d["items"]) == 5
    it = d["items"]
    biz.answer_drill(did, 1, float(it[0]["answer"]) * 1.005)        # 誤差 0.5%：對
    biz.answer_drill(did, 2, float(it[1]["answer"]) * 1.05)         # 5%：錯
    biz.answer_drill(did, 3, None, hinted=True)
    biz.answer_drill(did, 3, float(it[2]["answer"]))                # 看過示範：不計分
    d = biz.finish_drill(did)
    assert d["correct"] == 1 and float(d["score"]) == 20.0
    g = biz.growth()
    assert g["summary"]["count"] == 1


def test_history_and_pref(biz):
    biz.add_history("2×3.5", "7")
    assert biz.history()[0]["expr"] == "2×3.5"
    biz.save_pref(layout="trig")
    assert biz.pref()["layout"] == "trig"
