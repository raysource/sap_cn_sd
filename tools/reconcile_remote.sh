#!/usr/bin/env bash
# 磁盘 vs 远端：逐目录对账（避免「按前缀 grep 出来 318」这类口径不一致）
set -euo pipefail
cd /Users/jason/Desktop/work/training/sap_cn
R="raysource/sap_cn_sd"
gh api "repos/$R/git/trees/main?recursive=1" --jq '.tree[].path | select(.|test("^assets/img/"))' > /tmp/remote_img.txt
echo "remote assets/img 总数: $(wc -l < /tmp/remote_img.txt | tr -d ' ')"
echo "disk   assets/img 总数: $(find assets/img -type f | wc -l | tr -d ' ')"
echo "--- 按二级目录 ---"
echo "remote:"
awk -F/ '{print $3}' /tmp/remote_img.txt | sort | uniq -c
echo "disk:"
find assets/img -type f | awk -F/ '{print $3}' | sort | uniq -c
echo "--- 差异（远端有磁盘无） ---"
find assets/img -type f | sort > /tmp/disk_img.txt
comm -23 /tmp/remote_img.txt /tmp/disk_img.txt | head
echo "--- 差异（磁盘有远端无） ---"
comm -13 /tmp/remote_img.txt /tmp/disk_img.txt | head
echo "--- git 索引里的 assets/img 文件数 ---"
git ls-files assets/img | wc -l | tr -d ' '
echo "--- 工作区未跟踪/未提交 ---"
git status --short | head
