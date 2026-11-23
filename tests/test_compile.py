import importlib

import flet as ft


def test_ui_modules_import():
    for m in ("sr.ui.shell", "sr.ui.rulescreen", "sr.ui.ruleview", "sr.ui.drillview", "sr.ui.libview", "sr.ui.learnview",
              "sr.ui.reports", "sr.ui.admin", "sr.ui.dashboard", "sr.ui.helpview", "sr.ui.scalepick"):
        importlib.import_module(m)


def test_menu_and_help_consistent():
    from sr.help_text import LESSONS, PAGES
    from sr.ui.shell import menu
    sids = {it[0] for g in menu() for it in g[3]}
    for lesson in LESSONS:
        for icon, tone, text, sid in lesson["steps"]:
            assert sid in sids, sid
            assert getattr(ft.Icons, icon)
    assert set(PAGES) <= sids
