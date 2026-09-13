#!/usr/bin/env bash
# 收尾：把发布/验证脚本一起提交并再推一次，然后按「排序后逐路径」对账（comm 需要两侧都 sort）
set -euo pipefail
cd /Users/jason/Desktop/work/training/sap_cn
R="raysource/sap_cn_sd"

git add -A
git -c user.name='Jason' -c user.email='jason@localhost' \
    commit -q -m "tools/: 发布与对账脚本（publish_to_github.sh / verify_publish.sh / reconcile_remote.sh）

发布后不看 push 输出，改看 API 与 ls-remote 是否一致；对账用「两侧都 sort」的路径比较，
避免把 git tree 里的目录条目（type=tree）当成文件数。" || echo "(nothing to commit)"
git push -q origin main
echo "HEAD=$(git rev-parse HEAD)"

sleep 3
LOCAL="$(git rev-parse HEAD)"
echo "remote main = $(git ls-remote origin main | awk '{print $1}')"
echo "api main    = $(gh api "repos/$R/commits/main" --jq .sha)"

# 正确对账：两侧都排序，且只比较 blob（文件）
gh api "repos/$R/git/trees/main?recursive=1" --jq '.tree[]|select(.type=="blob")|.path' | sort > /tmp/r.txt
git ls-files | sort > /tmp/l.txt
echo "remote blobs=$(wc -l < /tmp/r.txt | tr -d ' ')  local tracked=$(wc -l < /tmp/l.txt | tr -d ' ')"
echo "--- 只在远端 / 只在本地（应为空）---"
comm -23 /tmp/r.txt /tmp/l.txt | head -5
comm -13 /tmp/r.txt /tmp/l.txt | head -5
echo "--- 抽查几个文件在远端可读 ---"
for f in assets/img/sd/t48/05_1_image1326.jpeg assets/img/prep/t01/02_1_image2.png assets/diagrams/order-internal.svg tools/verify_publish.sh; do
  printf "  %-46s %s\n" "$f" "$(gh api "repos/$R/contents/$f" --jq .size 2>/dev/null || echo ERR)"
done
git log --oneline | head -3
