#!/bin/bash
# 把線上版網頁（../docs，先在 Windows 執行 tools/make_pages.py）複製到 ios/web，
# 版本號跟著 sr/__init__.py 的 APP_VERSION，再產生 Xcode 專案。在 Mac 上執行：bash ios/sync.sh
set -e
cd "$(dirname "$0")"
[ -f ../docs/app/index.html ] || { echo "找不到 ../docs/app，請先同步整個專案"; exit 1; }
rm -rf web && mkdir web
# 只放網頁需要的檔案（不含開發文件與 iOS 安裝頁）
( cd ../docs && tar -cf - --exclude='*.md' --exclude='ios' --exclude='.nojekyll' . ) | ( cd web && tar -xf - )
V=$(python3 -c 'import re;print(re.search(r"APP_VERSION\s*=\s*\"([^\"]+)\"", open("../sr/__init__.py", encoding="utf-8").read()).group(1))')
# 版本號：1.2.3 → build 10203（每次都要比上一次大）
B=$(python3 -c "a,b,c=(int(x) for x in '$V'.split('.'));print(a*10000+b*100+c)")
sed -i '' "s/MARKETING_VERSION: \".*\"/MARKETING_VERSION: \"$V\"/; s/CURRENT_PROJECT_VERSION: \".*\"/CURRENT_PROJECT_VERSION: \"$B\"/" project.yml
XG=$(command -v xcodegen || echo /usr/local/bin/xcodegen)
"$XG" generate --quiet
echo "web ok, version $V ($B)"
