"""依 sr/schema.py 產生 docs/資料表欄位明細.md。"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from sr.schema import TABLES  # noqa: E402

lines = ["# 資料助秘計算尺：資料表欄位明細", "", "（本檔由 tools/gen_schema_doc.py 依 sr/schema.py 自動產生）", ""]
for name, title, cols, extra in TABLES:
    lines += ["## %s　%s" % (name, title), "", "| 欄位 | 型別 | 說明 |", "|---|---|---|"]
    lines += ["| %s | %s | %s |" % (c, t.replace("|", "\\|"), d) for c, t, d in cols]
    if extra:
        lines += ["", "索引／鍵：" + "；".join(extra)]
    lines.append("")
os.makedirs(os.path.join(HERE, "docs"), exist_ok=True)
with open(os.path.join(HERE, "docs", "資料表欄位明細.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("ok")
