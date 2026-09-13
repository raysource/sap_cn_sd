#!/usr/bin/env bash
# 把 sap_cn 作为独立仓库发布到 https://github.com/raysource/sap_cn_sd.git
# 可重复执行（已 init / 已有 origin 时不会报错）
set -euo pipefail
cd /Users/jason/Desktop/work/training/sap_cn

if [ ! -d .git ]; then
  git init -b main
fi
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/raysource/sap_cn_sd.git
git add -A
echo "--- staged ---"
git status --short | wc -l | tr -d ' '
git status --short | awk '{print $2}' | sed 's#/.*##' | sort | uniq -c | sort -rn
echo "--- size ---"
du -sh --exclude=.git . 2>/dev/null || du -sh .
echo "--- commit ---"
git -c user.name='Jason' -c user.email='jason@localhost' \
    commit -q -m "SAP SD 培训课程站（16 页）：概念→组织→主数据→定价→端到端流程→配置（48 任务）→实训

- 16 页静态 HTML（离线可开）+ Excel 8 表（课程大纲 / 学习WBS / 实训记录 / 截图索引 / 术语 / T-code…）
- 269 张真实 SAP GUI 中文界面截图（取自教材 S4.docx 的 SD 模块与准备章，保留原文件名可回查）
- 7 种 10 张自绘 SVG：思维导图 / 端到端流程图 / 单据流 / 组织结构图 / 模块集成图 / 定价条件技术 / 订单内部处理
- 配置索引覆盖教材 48 个 IMG 任务；讲师版（必问 12 题与答案 / 评分标准）+ 学员记入表 + 30 题自测
- 生成器与验证器：tools/{make_diagrams,build_pages,make_course_xlsx,verify_course}.py
  （verify_course.py PASS：16 页 / 155 图引用 / 10 自绘图 / 30 题）" || echo "(nothing to commit)"
echo "--- push ---"
git push -u origin main 2>&1 | tail -5
echo "--- local HEAD ---"
git rev-parse HEAD
git log --oneline -1
