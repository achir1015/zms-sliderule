"""第一次使用的預設資料：權限功能與角色。"""

# 權限功能：(代號, 名稱, 說明)；等級 0 無、1 查詢、2 維護
FUNCS = [
    ("RULE", "計算尺與計算示範", "使用計算尺、刻度一覽、語音計算示範；等級 2 可存自己的尺型"),
    ("DRILL", "讀尺練習", "做讀尺練習題、看自己的成績與成長"),
    ("LAYOUT", "共用尺型", "等級 1 可使用別人分享的尺型；等級 2 可分享、修改、刪除共用尺型"),
    ("RPT", "成績統計", "全部使用者的練習成績與計算紀錄（自己的成績不需要這個權限）"),
    ("SYS", "系統管理", "使用者與權限、練習設定、備份還原、版本更新、操作紀錄"),
]
FUNC_NAMES = {f[0]: f[1] for f in FUNCS}
LEVEL_NAMES = {0: "無", 1: "查詢", 2: "維護"}


def _r(**kw):
    return {f[0]: kw.get(f[0], 0) for f in FUNCS}


ROLES = {
    "系統管理員": {f[0]: 2 for f in FUNCS},
    "老師": _r(RULE=2, DRILL=2, LAYOUT=2, RPT=2),
    "學生": _r(RULE=2, DRILL=2, LAYOUT=1),
    "訪客": _r(RULE=1, LAYOUT=1),
}

DRILL_KINDS = {
    "MUL": "乘法", "DIV": "除法", "POW": "平方、立方與根號", "RECIP": "倒數",
    "TRIG": "三角函數", "LOG": "對數與指數", "MIX": "綜合",
}


def seed_all(db, first=False):
    """每次開啟都會補上缺的參考資料（INSERT IGNORE，不覆蓋使用者修改過的內容）。"""
    db.exec("INSERT IGNORE INTO sys_company (id, name) VALUES (1, '')")
