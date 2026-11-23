"""資料助秘計算尺 — 程式進入點。

桌面版：python main.py
網頁預覽（測試用）：python run_web.py（http://127.0.0.1:8660）。
"""
import os
import sys

import flet as ft  # noqa: E402

from sr.settings import resource_dir  # noqa: E402
from sr.ui.shell import main  # noqa: E402

if __name__ == "__main__":
    if getattr(sys, "frozen", False) and os.name == "nt":
        # 讓工作列顯示本程式的圖示（而不是 Python／Flet 的）
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ZMS.SlideRule")
        except Exception:
            pass
    assets = os.path.join(resource_dir(), "assets")
    port = os.environ.get("SR_WEB_PORT")
    if port:
        host = os.environ.get("SR_WEB_HOST", "127.0.0.1")
        # 打包版的 PyInstaller 執行期掛勾會把 FLET_SERVER_IP 固定成 127.0.0.1（它優先於 host 參數），線上版要改回來
        os.environ["FLET_SERVER_IP"] = host
        ft.run(main, view=None, port=int(port), host=host, assets_dir=assets)
    else:
        # 桌面版只能開一個（每個視窗都會啟動資料庫，兩個搶同一個資料夾會弄壞資料）；手機 App 不需要
        if not (os.environ.get("FLET_APP_STORAGE_DATA") or os.environ.get("SR_MOBILE")):
            from sr import single
            if not single.acquire():
                single.activate_existing()
                sys.exit(0)
        ft.run(main, assets_dir=assets)
