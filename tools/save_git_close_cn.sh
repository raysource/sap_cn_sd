#!/usr/bin/env bash
# 保存（第3回）の最終 commit: PROGRESS の HEAD 表を「以後動く」書き方に確定し push。最後に全状態を実測。
set -uo pipefail
cd /Users/jason/Desktop/work/training
GIT="git -c user.name=Jason -c user.email='jason@localhost'"
git add PROGRESS.md
$GIT commit -q -m "PROGRESS: HEAD 表を「執筆時点の値 / 最新は git log」方式に確定（自己参照で陳腐化しないように）" || echo "(nothing to commit)"
git push -q origin main

echo "===== 最終状態（実測） ====="
echo "training/  : HEAD=$(git rev-parse HEAD)"
echo "             remote=$(git ls-remote origin main | awk '{print $1}')  api=$(gh api repos/raysource/sap-consult/commits/main --jq .sha)"
echo "             status=$(git status --short | wc -l | tr -d ' ') 件"
echo "sap_cn/    : HEAD=$(cd sap_cn && git rev-parse HEAD)  remote=$(cd sap_cn && git ls-remote origin main | awk '{print $1}')"
echo "             status=$(cd sap_cn && git status --short | wc -l | tr -d ' ') 件"
echo
echo "親リポジトリ内 sap_cn: $(git ls-tree -r --name-only HEAD -- sap_cn | wc -l | tr -d ' ') files"
echo "sap_cn_sd の blob 数 : $(gh api 'repos/raysource/sap_cn_sd/git/trees/main?recursive=1' --jq '[.tree[]|select(.type=="blob")]|length')"
echo "公開確認（sap-consult のカード）: $(gh api repos/raysource/sap-consult/contents/sap_cn/index.html --jq .size) bytes"
echo "公開確認（sap_cn_sd のトップ）  : $(gh api repos/raysource/sap_cn_sd/contents/index.html --jq .size) bytes"
echo
echo "最新スナップショット3本:"; ls -lt _snapshots/*.tar.gz | head -3 | awk '{print "  ", $5, $6, $7, $8, $9}'
echo
git log --oneline -5
