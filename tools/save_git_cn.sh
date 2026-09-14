#!/usr/bin/env bash
# 保存（第 3 回）の git 手順:
#   1) sap_cn リポジトリ（raysource/sap_cn_sd）に保存用スクリプトを commit + push
#   2) 親リポジトリ（raysource/sap-consult）に sap_cn のファイルを取り込み（入れ子リポジトリ対策）
#      + PROGRESS.md / index.html / tools/* を commit + push
#   3) どちらも「push の出力」ではなく ls-remote / gh api / git show で確認
# 別セッションの WIP（sap_modules_cn/）は**入れない**。
set -uo pipefail
cd /Users/jason/Desktop/work/training
GIT="git -c user.name=Jason -c user.email=jason@localhost"

echo "===== 1. sap_cn リポジトリ ====="
( cd sap_cn
  git add -A
  $GIT commit -q -m "tools/save_check.sh: 「保存进度」用の一括実測スクリプト（検証/Excel/hub/snapshot/git）" || echo "(nothing to commit)"
  git push -q origin main
  echo "sap_cn HEAD   = $(git rev-parse HEAD)"
  echo "remote main   = $(git ls-remote origin main | awk '{print $1}')"
  echo "api commits   = $(gh api repos/raysource/sap_cn_sd/commits/main --jq .sha)"
)

echo
echo "===== 2. 親リポジトリへ sap_cn のファイルを取り込む ====="
bash tools/include_nested_repo_files.sh "$PWD" sap_cn
echo "親 index の sap_cn ファイル数 = $(git ls-files sap_cn | wc -l | tr -d ' ')"
echo "sap_cn 側の tracked 数        = $(cd sap_cn && git ls-files | wc -l | tr -d ' ')"

echo
echo "===== 3. 親リポジトリ commit + push ====="
git add PROGRESS.md index.html tools/make_hub_page.py tools/make_snapshot.sh tools/README.md
echo "--- staged（sap_modules_cn が入っていないこと）---"
git diff --cached --name-only | sed 's#/.*##' | sort | uniq -c
git status --short | grep -c 'sap_modules_cn' || true
$GIT commit -q -m "保存（第3回）: sap_cn の公開（独立リポジトリ）と全体スナップショット

- sap_cn（SAP SD 培训课程 16 页 / 実機截图 269 枚 / 自绘 7 種）を親リポジトリにも普通のファイルとして取り込み
  （tools/include_nested_repo_files.sh: 親で計算した blob SHA == 入れ子リポジトリの索引の SHA を assert）
- PROGRESS §13 に「保存（第3回）」を追記（スナップショット検算 / 検証結果 / git 状態 / 保存していないもの）
- tools/README.md に sap_cn の站内ツールと踏んだ罠（qlmanage の正方形化・git trees の type 混在・comm の sort・CJK エスケープ）を追記
- 別セッションの WIP sap_modules_cn/ は**含めていない**（hub のカードだけ彼らの更新を反映）" || echo "(nothing to commit)"
git push -q origin main
echo "training HEAD = $(git rev-parse HEAD)"
echo "remote main   = $(git ls-remote origin main | awk '{print $1}')"
echo "api commits   = $(gh api repos/raysource/sap-consult/commits/main --jq .sha)"

echo
echo "===== 4. 復元・公開の証拠確認 ====="
echo "local sap_cn/index.html の md5 : $(md5 -q sap_cn/index.html)"
echo "HEAD 内 sap_cn/index.html md5  : $(git show HEAD:sap_cn/index.html | md5 -q)"
echo "HEAD 内 sap_cn ファイル数      : $(git ls-tree -r --name-only HEAD -- sap_cn | wc -l | tr -d ' ')"
echo "HEAD 内に sap_modules_cn はあるか: $(git ls-tree -r --name-only HEAD | grep -c '^sap_modules_cn/' || true) （0 が正）"
echo "HEAD:sap_cn/README.md に公開節があるか: $(git show HEAD:sap_cn/README.md | grep -c 'sap_cn_sd')"
echo "HEAD:PROGRESS.md に保存第3回があるか  : $(git show HEAD:PROGRESS.md | grep -c '保存（第 3 回')"
git log --oneline -3
