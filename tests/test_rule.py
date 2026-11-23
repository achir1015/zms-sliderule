"""計算尺引擎、示範步驟、練習評分。"""
import math
import random

from sr import rule as R
from sr.demo import PRESETS, plan
from sr.rulebiz import make_problem


def test_scales_inverse_and_ticks():
    for s in R.SCALES:
        for k in range(1, 99):
            u = k / 100
            assert abs(s.f(s.g(u)) - u) < 1e-9, s.key
        tks = R.ticks(s, -0.1, 1.1, 1200)
        assert 60 < len(tks) < 600, (s.key, len(tks))
        assert all(-0.1 - 1e-9 <= t.u <= 1.1 + 1e-9 for t in tks)


def test_infinite_zoom_reads_more_digits():
    c = R.BY_KEY["C"]
    u = math.log10(2.0000027)
    for z, digits in ((1e3, 3), (1e6, 6), (1e9, 9)):
        x, text = R.reading(c, u, z)
        assert len(text.replace(".", "")) >= digits
        tks = R.ticks(c, u - 600 / z, u + 600 / z, z)
        assert tks and any(t.text for t in tks)


def test_wraparound_multiply():
    # 7×3.5：滑尺 1 對準 D 的 7，C 的 3.5 對著 D 的 2.45（環繞）
    st = R.RuleState(zoom=1000, slide=math.log10(7))
    st.cursor = st.slide + math.log10(3.5)
    d = R.BY_KEY["D"].value(st.cursor)
    assert abs(d - 2.45) < 1e-9


def test_demo_plans():
    for p in PRESETS + ["cos 60", "1.2^3.5", "2x3", "0.25×40"]:
        pl = plan(p)
        assert pl["steps"] and pl["result"] > 0


def test_demo_final_reading_matches_answer():
    """照示範步驟移動後，答案刻度的讀數＝答案的有效數字。"""
    for p in ("7×3.5", "5.5÷2", "18÷7.2", "3.2²", "√20", "1.5³", "1/8", "sin 30", "2^1.5"):
        pl = plan(p)
        st = R.RuleState()
        for s in pl["steps"]:
            if s["slide"] is not None:
                st.slide = s["slide"]
            if s["cursor"] is not None:
                st.cursor = s["cursor"]
        key = pl["steps"][-1]["hl"][0]
        slide_part = key in ("C", "CI", "B", "CF", "CIF")
        v = R.BY_KEY[key].value(st.cursor - (st.slide if slide_part else 0))
        m = R.mantissa(pl["result"])[0]
        assert abs(R.mantissa(v)[0] - m) / m < 1e-6 or abs(v - pl["result"]) / pl["result"] < 1e-6, (p, v)


def test_drill_problems_have_demos():
    random.seed(7)
    for k in ("MUL", "DIV", "POW", "RECIP", "TRIG", "LOG", "MIX"):
        for _ in range(30):
            e, a = make_problem(k)
            assert abs(plan(e)["result"] - a) <= 1e-9 * abs(a)
