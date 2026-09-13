#!/usr/bin/env bash
# 最终对账：core.quotePath=false 让 git 输出原始 UTF-8 文件名（与 API 一致）
set -euo pipefail
cd /Users/jason/Desktop/work/training/sap_cn
R="raysource/sap_cn_sd"
gh api "repos/$R/git/trees/main?recursive=1" --jq '.tree[]|select(.type=="blob")|.path' | LC_ALL=C sort > /tmp/r2.txt
git -c core.quotepath=false ls-files | LC_ALL=C sort > /tmp/l2.txt
echo "remote blobs=$(wc -l < /tmp/r2.txt | tr -d ' ')  local tracked=$(wc -l < /tmp/l2.txt | tr -d ' ')"
echo "只在远端："; comm -23 /tmp/r2.txt /tmp/l2.txt
echo "只在本地："; comm -13 /tmp/r2.txt /tmp/l2.txt
echo "(两条都空 = 远端内容与我本地工作区完全一致)"
echo "--- 中文文件名在远端确认 ---"
gh api "repos/$R/contents/SAPSD_课程大纲_学习WBS.xlsx" --jq '{name,size,sha}'
