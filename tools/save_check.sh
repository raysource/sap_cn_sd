#!/usr/bin/env bash
# 「保存进度」用の一括チェック：站点検証 / hub / Excel / スナップショット / git 状態を実測して出す。
# 数字を先に測ってから PROGRESS.md に書くための道具（記憶で書かない）。
set -uo pipefail
cd /Users/jason/Desktop/work/training
echo "===== 1. sap_cn 站内検証 ====="
( cd sap_cn && python3 tools/verify_course.py; python3 ~/.hermes/skills/productivity/sap-training-sites/scripts/verify_site.py . )
echo
echo "===== 2. Excel（8 sheet / 截图索引行数） ====="
python3 - <<'PY'
from openpyxl import load_workbook
wb = load_workbook('sap_cn/SAPSD_课程大纲_学习WBS.xlsx')
print("sheets:", len(wb.sheetnames), wb.sheetnames)
print("4_截图索引 rows:", wb['4_截图索引'].max_row - 4)
print("2_学习WBS rows:", wb['2_学习WBS'].max_row - 4)
PY
echo
echo "===== 3. hub（index.html）カードの実在確認 ====="
python3 - <<'PY'
import re, os
s = open('index.html', encoding='utf-8').read()
cards = re.findall(r'<h3><a href="([^"]+)"', s)
print("cards:", len(cards))
miss = [c for c in cards if not os.path.exists(os.path.join(os.path.dirname(c) or '.', c))]
for c in cards:
    print("  %-28s %s" % (c, "OK" if os.path.exists(c) else "MISSING(ローカルに無い)"))
print("合計表記:", re.findall(r'<b>(\d+) (?:个站|站)</b>', s)[:1], re.findall(r'(\d+) 个站', s)[:2])
PY
echo
echo "===== 4. スナップショット ====="
ls -lt _snapshots/*.tar.gz | head -5
echo
echo "===== 5. git 状態 ====="
echo "--- training/ (sap-consult) ---"
git status --short | head -12
echo "HEAD=$(git rev-parse HEAD)  remote=$(git ls-remote origin main 2>/dev/null | awk '{print $1}')"
echo "--- sap_cn/ (sap_cn_sd) ---"
( cd sap_cn && echo "HEAD=$(git rev-parse HEAD)  remote=$(git ls-remote origin main | awk '{print $1}')" && git status --short | head -5 )
echo "--- sap_modules_cn は .git を持つか ---"
[ -d sap_modules_cn/.git ] && echo yes || echo no
echo "files=$(find sap_modules_cn -type f | wc -l | tr -d ' ')  size=$(du -sh sap_modules_cn | awk '{print $1}')"
