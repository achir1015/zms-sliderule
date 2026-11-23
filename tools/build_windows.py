"""一鍵建置 Windows 安裝檔：
1. 確認內附的 MariaDB（packaging/mariadb）
2. 產生資料庫腳本、圖示、語音說明（已存在且沒變則略過）
3. flet pack（PyInstaller）打包到 dist/ZMSSlideRule
4. Inno Setup 產生 dist-installer/ZMSSlideRule-Setup-<版本>.exe

用法：.venv\\Scripts\\python tools\\build_windows.py
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from sr import APP_ID, APP_NAME, APP_VERSION, AUTHOR  # noqa: E402

ISCC = [os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe", r"C:\Program Files\Inno Setup 6\ISCC.exe"]
PY = os.path.join(HERE, ".venv", "Scripts", "python.exe")
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")


def prepare():
    if not os.path.isfile(os.path.join(HERE, "packaging", "mariadb", "bin", "mariadbd.exe")):
        raise SystemExit("缺少 packaging/mariadb（請複製 MariaDB 10.11 的 bin 與 share 最小檔案）")
    subprocess.run([PY, "tools/gen_schema_doc.py"], cwd=HERE, check=True, env=ENV)
    if not os.path.isfile(os.path.join(HERE, "assets", "icon.png")):
        subprocess.run([PY, "tools/make_icon.py"], cwd=HERE, check=True, env=ENV)
    subprocess.run([PY, "tools/make_voice.py"], cwd=HERE, check=False, env=ENV)


def pack():
    flet = os.path.join(HERE, ".venv", "Scripts", "flet.exe")
    shutil.rmtree(os.path.join(HERE, "dist"), ignore_errors=True)
    cmd = [flet, "pack", "main.py", "-D", "-y", "-n", APP_ID, "-i", "packaging/icon.ico", "--distpath", "dist",
           "--add-data", "assets:assets",
           "--hidden-import", "edge_tts", "--hidden-import", "pymysql", "--hidden-import", "certifi",
           "--hidden-import", "qrcode",
           "--pyinstaller-build-args=--collect-all=flet_web",
           "--pyinstaller-build-args=--collect-all=flet_audio", "--pyinstaller-build-args=--collect-submodules=uvicorn",
           "--product-name", APP_NAME, "--file-description", APP_NAME, "--product-version", APP_VERSION,
           "--file-version", APP_VERSION + ".0", "--company-name", AUTHOR, "--copyright", "© 2026 " + AUTHOR]
    subprocess.run(cmd, cwd=HERE, check=True, env=ENV)


def installer():
    iscc = next((p for p in ISCC if os.path.isfile(p)), None)
    if not iscc:
        raise SystemExit("找不到 Inno Setup 6（ISCC.exe）")
    # 先編譯到暫存資料夾再搬回 dist-installer：直接寫 dist-installer 時常被防毒鎖檔（EndUpdateResource failed 110）
    tmp = tempfile.mkdtemp(prefix="zmssliderule-iss-")
    subprocess.run([iscc, "/DAppVer=" + APP_VERSION, "/O" + tmp, os.path.join(HERE, "packaging", "installer.iss")],
                   check=True)
    name = "%s-Setup-%s.exe" % (APP_ID, APP_VERSION)
    out = os.path.join(HERE, "dist-installer", name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    shutil.move(os.path.join(tmp, name), out)
    shutil.rmtree(tmp, ignore_errors=True)
    sha = hashlib.sha256(open(out, "rb").read()).hexdigest()
    print("完成：%s（%.1f MB）\nSHA256 %s" % (out, os.path.getsize(out) / 1e6, sha))


if __name__ == "__main__":
    prepare()
    pack()
    installer()
