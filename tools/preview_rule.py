"""開發用：不連資料庫，單獨預覽計算尺畫面（http://127.0.0.1:8661）。"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.environ.setdefault("SR_NO_VOICE", "1")
os.environ.setdefault("FLET_FORCE_WEB_SERVER", "true")

import flet as ft  # noqa: E402

from sr.ui import theme as T  # noqa: E402
from sr.ui.rulescreen import RuleScreen  # noqa: E402


class FakeApp:
    def __init__(self, page):
        self.page = page
        self.books = None
        self.reports = None


def main(page: ft.Page):
    page.title = "計算尺預覽"
    page.fonts = {"NotoSansTC": "fonts/NotoSansTC-VF.ttf"}
    page.theme = ft.Theme(color_scheme_seed=T.PRIMARY, font_family="NotoSansTC")
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = T.BG
    page.padding = 20
    ctx = T.Ctx(FakeApp(page))
    page.add(RuleScreen(ctx, layout=os.environ.get("SR_LAYOUT")))


if __name__ == "__main__":
    ft.run(main, view=None, port=int(os.environ.get("PORT", "8661")), host="127.0.0.1",
           assets_dir=os.path.join(HERE, "assets"))
