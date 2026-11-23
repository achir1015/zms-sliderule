"""同一台電腦只能開一個計算尺（桌面版）。

為什麼：每開一個視窗都會啟動自己的 MariaDB，兩個資料庫程式同時用同一個資料夾會弄壞資料。
做法：在資料夾放一個鎖定檔（instance.lock），程式開著時一直鎖住；第二次開啟時拿不到鎖，就把原本的視窗叫到最前面後結束。
程式內更新會「關閉舊版 → 安裝 → 自動開新版」，新版可能比舊版早一點啟動，所以拿不到鎖時先等幾秒再判斷。
線上版子程序、手機 App 不使用（各自沒有本機資料庫）。
"""
import os
import sys
import time

from . import APP_NAME
from .settings import data_dir

_handle = None          # 程式結束前一直開著（作業系統在程式結束時自動解鎖）


def _try_lock(f):
    try:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def acquire(wait=10.0, path=None):
    """拿到鎖回傳 True；別的計算尺開著（等了 wait 秒仍拿不到）回傳 False。"""
    global _handle
    path = path or os.path.join(data_dir(), "instance.lock")
    f = open(path, "a+")
    t0 = time.time()
    while True:
        if _try_lock(f):
            f.seek(0)
            f.truncate()
            f.write(str(os.getpid()))
            f.flush()
            _handle = f
            return True
        if time.time() - t0 >= wait:
            f.close()
            return False
        time.sleep(0.5)


def activate_existing():
    """把已經開著的計算尺視窗叫到最前面。"""
    try:
        if os.name == "nt":
            _activate_windows()
        elif sys.platform == "darwin":
            exe = os.path.realpath(sys.executable)
            app = exe.split(".app/")[0] + ".app" if ".app/" in exe else ""
            if app:
                import subprocess
                subprocess.run(["open", app], timeout=10)      # App 已在執行時，open 只會把它叫到前面
    except Exception:
        pass


def _activate_windows():
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, lp):
        n = user32.GetWindowTextLengthW(hwnd)
        if n and user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            if buf.value == APP_NAME:
                found.append(hwnd)
        return True
    user32.EnumWindows(cb, 0)
    for hwnd in found[:1]:
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)          # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
