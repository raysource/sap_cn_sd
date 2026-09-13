#!/usr/bin/env bash
# 发布后验证：远端是否真的与我本地一致（不看 push 的输出，看 API 与 ls-remote）
set -euo pipefail
cd /Users/jason/Desktop/work/training/sap_cn
R="raysource/sap_cn_sd"

LOCAL="$(git rev-parse HEAD)"
LSR="$(git ls-remote origin main | awk '{print $1}')"
API="$(gh api "repos/$R/commits/main" --jq .sha)"
echo "local HEAD          : $LOCAL"
echo "git ls-remote main  : $LSR"
echo "gh api commits/main : $API"
[ "$LOCAL" = "$LSR" ] && echo "OK  ls-remote == local" || echo "FAIL ls-remote mismatch"
[ "$LOCAL" = "$API" ] && echo "OK  api == local" || echo "FAIL api mismatch"

echo "--- 远端文件清点（git trees）---"
BLOBS="$(gh api "repos/$R/git/trees/main?recursive=1" --jq '[.tree[]|select(.type=="blob")]|length')"
echo "remote blobs: $BLOBS   local tracked: $(git ls-files | wc -l | tr -d ' ')"
echo "remote pages: $(gh api "repos/$R/git/trees/main?recursive=1" --jq '[.tree[].path|select(test("^[a-z]+\\.html$"))]|length')"
echo "remote screenshots(sd+prep): $(gh api "repos/$R/git/trees/main?recursive=1" --jq '[.tree[].path|select(test("^assets/img/(sd|prep)/"))]|length')"
echo "remote diagrams: $(gh api "repos/$R/git/trees/main?recursive=1" --jq '[.tree[].path|select(test("^assets/diagrams/.+\\.svg$"))]|length')"
echo "remote xlsx: $(gh api "repos/$R/git/trees/main?recursive=1" --jq '[.tree[].path|select(test("\\.xlsx$"))]|length')"

echo "--- 关键文件在远端可读 ---"
for f in index.html config.html SAPSD_课程大纲_学习WBS.xlsx README.md tools/verify_course.py work/gui_screenshot_text.json assets/diagrams/mindmap.svg assets/img/sd/t41/01_1_image1297.png; do
  sz="$(gh api "repos/$R/contents/$f" --jq .size 2>/dev/null || echo ERR)"
  echo "  $sz  $f"
done

echo "--- 仓库信息 ---"
gh api "repos/$R" --jq '{name,visibility,default_branch:.default_branch,size_kb:.size,url:.html_url}'
echo "--- 页面内容抽查（远端 index.html 里是否含课程标记）---"
gh api "repos/$R/contents/index.html" --jq .content | base64 -d | grep -c '思维导图\|SAP SD'
