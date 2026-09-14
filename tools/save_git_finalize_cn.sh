#!/usr/bin/env bash
# 保存（第3回）最終: 新しく足した sap_cn のスクリプトを両リポジトリへ入れ、PROGRESS の確定版を push する
set -uo pipefail
cd /Users/jason/Desktop/work/training
GIT="git -c user.name=Jason -c user.email='jason@localhost'"

echo "===== 1. sap_cn（raysource/sap_cn_sd）====="
( cd sap_cn
  git add -A
  $GIT commit -q -m "tools/: 保存（第3回）用の git 手順スクリプト（save_git_cn.sh / save_git_finalize_cn.sh）" || echo "(nothing to commit)"
  git push -q origin main
  echo "sap_cn HEAD = $(git rev-parse HEAD)"
  echo "remote      = $(git ls-remote origin main | awk '{print $1}')"
  echo "api         = $(gh api repos/raysource/sap_cn_sd/commits/main --jq .sha)"
)

echo
echo "===== 2. 親リポジトリへ再取り込み（sap_cn の新規ファイルを反映）====="
bash tools/include_nested_repo_files.sh "$PWD" sap_cn
echo "親 index の sap_cn = $(git ls-files sap_cn | wc -l | tr -d ' ')  / sap_cn 側 tracked = $(cd sap_cn && git ls-files | wc -l | tr -d ' ')"

echo
echo "===== 3. 親リポジトリ commit + push ====="
git add PROGRESS.md
git diff --cached --name-only | sed 's#/.*##' | sort | uniq -c
$GIT commit -q -m "PROGRESS + sap_cn: 保存（第3回）の確定（スナップショット範囲の実測を追記 / sap_cn の保存用スクリプトを親にも取り込み）" || echo "(nothing to commit)"
git push -q origin main
echo "training HEAD = $(git rev-parse HEAD)"
echo "remote        = $(git ls-remote origin main | awk '{print $1}')"
echo "api           = $(gh api repos/raysource/sap-consult/commits/main --jq .sha)"

echo
echo "===== 4. 証拠 ====="
echo "HEAD:sap_cn/index.html md5 (local vs HEAD): $(md5 -q sap_cn/index.html) / $(git show HEAD:sap_cn/index.html | md5 -q)"
echo "HEAD 内 sap_cn ファイル数: $(git ls-tree -r --name-only HEAD -- sap_cn | wc -l | tr -d ' ')"
echo "HEAD:sap_cn/tools/save_git_finalize_cn.sh あり: $(git show HEAD:sap_cn/tools/save_git_finalize_cn.sh | wc -l | tr -d ' ') 行"
echo "公開（sap-consult）の sap_cn カード: $(gh api repos/raysource/sap-consult/contents/sap_cn/index.html --jq .size) bytes"
echo "作業ツリー: $(git status --short | wc -l | tr -d ' ') 件の差分（自分のファイルのみであること）"
git status --short
echo
git log --oneline -4
