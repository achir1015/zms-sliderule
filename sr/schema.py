"""資料表定義（唯一來源）：建表 SQL 與欄位中文說明。

表名前綴：sys_＝系統（使用者、權限、設定、紀錄）、sr_＝計算尺（尺型、偏好、計算紀錄、讀尺練習）。
tools/gen_schema_doc.py 會依這裡產生 docs/資料表欄位明細.md。
"""

# (表名, 中文名稱, [(欄位, SQL 型別與屬性, 中文說明)], 其他限制)
TABLES = [
    ("sys_meta", "系統參數", [
        ("k", "VARCHAR(40) NOT NULL PRIMARY KEY", "參數代號"),
        ("v", "TEXT", "參數值")], []),
    ("sys_company", "單位設定（單一公司）", [
        ("id", "INT NOT NULL PRIMARY KEY", "固定 1"),
        ("name", "VARCHAR(120) NOT NULL DEFAULT ''", "公司、學校或單位名稱"),
        ("drill_size", "INT NOT NULL DEFAULT 10", "讀尺練習每回題數"),
        ("tolerance", "DECIMAL(5,2) NOT NULL DEFAULT 1.00", "讀尺練習容許誤差（%）"),
        ("pass_score", "INT NOT NULL DEFAULT 60", "及格分數")], []),
    ("sys_user", "使用者", [
        ("uid", "VARCHAR(30) NOT NULL PRIMARY KEY", "帳號"),
        ("name", "VARCHAR(60) NOT NULL", "姓名"),
        ("pw_hash", "VARCHAR(200) NOT NULL", "密碼雜湊（PBKDF2）"),
        ("role", "VARCHAR(30) NOT NULL DEFAULT ''", "角色範本"),
        ("dept", "VARCHAR(30) NOT NULL DEFAULT ''", "班別或部門"),
        ("is_admin", "TINYINT NOT NULL DEFAULT 0", "系統管理員"),
        ("active", "TINYINT NOT NULL DEFAULT 1", "啟用"),
        ("last_login", "DATETIME NULL", "最近登入"),
        ("created_at", "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP", "建立時間")], []),
    ("sys_user_perm", "使用者權限", [
        ("uid", "VARCHAR(30) NOT NULL", "帳號"),
        ("func", "VARCHAR(10) NOT NULL", "功能代號"),
        ("lvl", "TINYINT NOT NULL DEFAULT 0", "等級 0 無、1 查詢、2 維護")], ["PRIMARY KEY (uid, func)"]),
    ("sys_audit_log", "操作紀錄", [
        ("id", "BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY", "流水號"),
        ("at", "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP", "時間"),
        ("uid", "VARCHAR(30) NOT NULL DEFAULT ''", "使用者"),
        ("action", "VARCHAR(30) NOT NULL", "動作"),
        ("target", "VARCHAR(80) NOT NULL DEFAULT ''", "對象"),
        ("detail", "TEXT", "內容（異動前 → 後）")], ["KEY ix_at (at)"]),
    ("sr_layout", "自訂尺型（上定尺、滑尺、下定尺各放哪些刻度）", [
        ("id", "INT NOT NULL AUTO_INCREMENT PRIMARY KEY", "流水號"),
        ("name", "VARCHAR(60) NOT NULL", "尺型名稱"),
        ("upper", "VARCHAR(120) NOT NULL DEFAULT ''", "上定尺刻度（由上而下，逗號分隔，例 A）"),
        ("slide", "VARCHAR(120) NOT NULL DEFAULT ''", "滑尺刻度（例 B,CI,C）"),
        ("lower", "VARCHAR(120) NOT NULL DEFAULT ''", "下定尺刻度（例 D,K）"),
        ("note", "VARCHAR(200) NOT NULL DEFAULT ''", "說明"),
        ("owner", "VARCHAR(30) NOT NULL DEFAULT ''", "建立人"),
        ("shared", "TINYINT NOT NULL DEFAULT 0", "分享給所有使用者"),
        ("created_at", "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP", "建立時間")], ["KEY ix_owner (owner)"]),
    ("sr_pref", "個人偏好（上次用的尺型等）", [
        ("uid", "VARCHAR(30) NOT NULL PRIMARY KEY", "帳號"),
        ("layout", "VARCHAR(20) NOT NULL DEFAULT 'student'", "上次使用的尺型代號"),
        ("data", "TEXT", "其他設定（JSON）")], []),
    ("sr_history", "計算紀錄（計算示範與計算機）", [
        ("id", "BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY", "流水號"),
        ("uid", "VARCHAR(30) NOT NULL", "使用者"),
        ("at", "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP", "時間"),
        ("expr", "VARCHAR(80) NOT NULL", "算式"),
        ("result", "VARCHAR(40) NOT NULL DEFAULT ''", "結果（計算尺讀數精度）"),
        ("mode", "VARCHAR(6) NOT NULL DEFAULT 'DEMO'", "DEMO 語音示範、DRILL 練習題示範")], ["KEY ix_uid (uid, at)"]),
    ("sr_drill", "讀尺練習（每一回）", [
        ("id", "INT NOT NULL AUTO_INCREMENT PRIMARY KEY", "流水號"),
        ("uid", "VARCHAR(30) NOT NULL", "使用者"),
        ("kind", "VARCHAR(6) NOT NULL", "MUL 乘法、DIV 除法、POW 平方立方與根號、RECIP 倒數、TRIG 三角、LOG 對數指數、MIX 綜合"),
        ("q_count", "INT NOT NULL DEFAULT 0", "題數"),
        ("answered", "INT NOT NULL DEFAULT 0", "已作答題數"),
        ("correct", "INT NOT NULL DEFAULT 0", "答對題數（誤差在容許範圍內、且沒有看示範）"),
        ("score", "DECIMAL(5,1) NOT NULL DEFAULT 0", "分數（滿分 100）"),
        ("tolerance", "DECIMAL(5,2) NOT NULL DEFAULT 1.00", "容許誤差（%）"),
        ("status", "VARCHAR(6) NOT NULL DEFAULT 'OPEN'", "OPEN 作答中、DONE 已完成"),
        ("started_at", "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP", "開始時間"),
        ("finished_at", "DATETIME NULL", "完成時間"),
        ("seconds", "INT NOT NULL DEFAULT 0", "作答秒數")], ["KEY ix_uid (uid, started_at)"]),
    ("sr_drill_item", "讀尺練習每一題", [
        ("drill_id", "INT NOT NULL", "練習回次"),
        ("seq", "INT NOT NULL", "第幾題"),
        ("expr", "VARCHAR(40) NOT NULL", "算式"),
        ("answer", "DOUBLE NOT NULL", "正確答案"),
        ("given", "DOUBLE NULL", "使用者讀出的答案（NULL＝未作答）"),
        ("err_pct", "DECIMAL(8,3) NULL", "相對誤差（%）"),
        ("hinted", "TINYINT NOT NULL DEFAULT 0", "看過語音示範（不計分）"),
        ("ok", "TINYINT NOT NULL DEFAULT 0", "答對")], ["PRIMARY KEY (drill_id, seq)"]),
]


def ddl():
    out = []
    for name, title, cols, extra in TABLES:
        body = ["  `%s` %s COMMENT '%s'" % (c, t, d.replace("'", "''")) for c, t, d in cols]
        body += ["  " + x for x in extra]
        out.append("CREATE TABLE IF NOT EXISTS `%s` (\n%s\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 "
                   "COLLATE=utf8mb4_unicode_ci COMMENT='%s'" % (name, ",\n".join(body), title))
    return out


def columns(table):
    return [c[0] for t in TABLES if t[0] == table for c in t[2]]
