# -*- coding: utf-8 -*-
"""生成 SAP SD 培训课程站的全部页面（幂等）。

    python3 tools/build_pages.py

统计数字（页数 / 截图数 / 自绘图数）全部从生成结果里数出来，不手写。
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "sitegen"))
import common  # noqa: E402
import p_overview as P1  # noqa: E402
import p_process as P2  # noqa: E402
import p_admin as P3  # noqa: E402

ROOT = common.ROOT

PAGES = [
    ("index.html", "首页 · 课程地图与学习路线", "首页", P1.page_index),
    ("concept.html", "概念与定位", "概念与定位：SD 到底在管什么", P1.page_concept),
    ("org.html", "组织结构", "组织结构：先给数据定坐标", P1.page_org),
    ("master.html", "主数据", "主数据：客户、物料、价格", P1.page_master),
    ("pricing.html", "定价与条件技术", "定价：条件技术的四层结构", P1.page_pricing),
    ("flow.html", "端到端流程", "端到端流程：从询价到收款", P2.page_flow),
    ("order.html", "销售订单处理", "流程 ① 销售订单处理", P2.page_order),
    ("delivery.html", "交货与发货过账", "流程 ② 外向交货与发货过账", P2.page_delivery),
    ("billing.html", "开票与财务过账", "流程 ③ 开票与过账到财务", P2.page_billing),
    ("analysis.html", "分析与监控", "分析与监控：把流程管起来", P2.page_analysis),
    ("config.html", "配置路线（48 任务）", "配置路线：48 个任务的完整索引", P3.page_config),
    ("practice.html", "实训任务", "实训：五个动手任务", P3.page_practice),
    ("instructor.html", "讲师版", "讲师版：上课怎么讲、怎么考", P3.page_instructor),
    ("worksheet.html", "学员版（记入表）", "学员版：记入表（可打印）", P3.page_worksheet),
    ("quiz.html", "自测（30 题）", "自测：30 题", P3.page_quiz),
    ("glossary.html", "术语与 T-code 速查", "术语与 T-code 速查", P3.page_glossary),
]


def main():
    # 先算出不依赖正文的统计量
    stats = {"pages": len(PAGES), "tasks": len(common.SD_SOURCE),
             "shots": 0, "diagrams": 0, "steps": sum(len(t["steps"]) for t in common.SD_SOURCE)}
    bodies, meta = {}, {}
    for fn, title, kicker, func in PAGES:
        if fn == "index.html":
            continue
        body = func(stats)
        bodies[fn] = "\n".join(body)
        meta[fn] = (title, kicker)
    all_html = "\n".join(bodies.values())
    stats["shots"] = len(re.findall(r'<figure class="shot', all_html))
    stats["uniqueshots"] = len(set(re.findall(r'src="(assets/img/[^"]+)"', all_html)))
    stats["diagrams"] = len(re.findall(r'<figure class="dia', all_html))

    # 首页（用真实统计数字）。首页自身只用 1 张自绘图（思维导图）、0 张截图，
    # 生成后再数一遍核对这个假设，不靠记忆。
    body = "\n".join(P1.page_index(dict(stats, diagrams=stats["diagrams"] + 1)))
    bodies["index.html"] = body
    meta["index.html"] = ("首页 · 课程地图与学习路线", "首页")
    final = "\n".join(bodies.values())
    n_shot2 = len(re.findall(r'<figure class="shot', final))
    n_dia2 = len(re.findall(r'<figure class="dia', final))
    if n_shot2 != stats["shots"] or n_dia2 != stats["diagrams"] + 1:
        print("WARN: 首页统计假设不成立（shot %d→%d / dia %d→%d），按实数重写首页"
              % (stats["shots"], n_shot2, stats["diagrams"], n_dia2))
        stats["shots"], stats["diagrams"] = n_shot2, n_dia2
        bodies["index.html"] = "\n".join(P1.page_index(stats))
    else:
        stats["diagrams"] += 1

    written = []
    for fn, title, kicker, _f in PAGES:
        html = common.shell(fn, title, kicker, bodies[fn])
        path = os.path.join(ROOT, fn)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        written.append((fn, len(html)))

    # 站点自报统计（给训练站索引页 hub 用）
    hub = {"n_pages": stats["pages"], "n_steps": stats["steps"], "figs": stats["shots"],
           "n_cfg": len(common.SD_SOURCE), "has_wbs": True,
           "note": "SAP SD 培训课程站（真实截图 + 自绘流程图/结构图/思维导图）"}
    with open(os.path.join(ROOT, "tools", "hub_stats.json"), "w", encoding="utf-8") as f:
        json.dump(hub, f, ensure_ascii=False, indent=1)

    print("pages: %d   截图引用: %d（去重 %d）  自绘图: %d   配置任务: %d"
          % (stats["pages"], stats["shots"], stats["uniqueshots"], stats["diagrams"], stats["tasks"]))
    for fn, sz in written:
        print("  %-16s %7d bytes" % (fn, sz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
