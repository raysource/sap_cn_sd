# -*- coding: utf-8 -*-
"""生成课程 Excel：SAPSD_课程大纲_学习WBS.xlsx

    python3 tools/make_course_xlsx.py

工作表：
  0_説明        … 这份 Excel 是什么、怎么用
  1_课程大纲    … 16 页 × 学什么 × 对应自绘图 × 页内要点
  2_学习WBS     … 按板块拆到「任务级」，可勾选进度（含 COUNTIF 统计）
  3_实训记录    … 五个实训任务的单据号/状态/金额记录（打印后手写或直接填）
  4_截图索引    … 页面里引用的每一张真实截图（页面 / 任务 / 原文件名）
  5_术语表      … 中英对照
  6_Tcode速查   … 常用 T-code
  7_自绘图清单  … 10 张流程图/结构图/思维导图

所有内容从生成好的 HTML 与 sitegen 数据里读，不手抄。
"""
import os
import re
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "sitegen"))
import common  # noqa: E402
import p_admin  # noqa: E402
import p_overview  # noqa: E402
import p_process  # noqa: E402

OUT = os.path.join(ROOT, "SAPSD_课程大纲_学习WBS.xlsx")
HEAD_FILL = PatternFill("solid", fgColor="0A6ED1")
HEAD_FONT = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
CELL_FONT = Font(name="微软雅黑", size=10)
TITLE_FONT = Font(name="微软雅黑", size=13, bold=True, color="0854A0")
THIN = Side(style="thin", color="D9E1E8")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(vertical="top", wrap_text=True)
CENTER = Alignment(horizontal="center", vertical="center")


def sheet(wb, name, title, headers, rows, widths, note=None):
    ws = wb.create_sheet(name)
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    r = 2
    if note:
        ws["A2"] = note
        ws["A2"].font = Font(name="微软雅黑", size=9, color="6B7A8D")
        r = 3
    hrow = r + 1
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=hrow, column=i, value=h)
        c.fill, c.font, c.alignment, c.border = HEAD_FILL, HEAD_FONT, CENTER, BORDER
    for j, row in enumerate(rows):
        for i, v in enumerate(row, 1):
            c = ws.cell(row=hrow + 1 + j, column=i, value=v)
            c.font, c.alignment, c.border = CELL_FONT, WRAP, BORDER
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row=hrow + 1, column=1)
    ws.row_dimensions[hrow].height = 22
    return ws, hrow


def read_pages():
    """从已生成的 HTML 里抽出每页的 h1/h2 结构 + 截图引用。"""
    pages = {}
    for f, label, tip in common.NAV:
        p = os.path.join(ROOT, f)
        s = open(p, encoding="utf-8").read()
        h1 = re.search(r"<h1>(.*?)</h1>", s, re.S)
        h2 = [re.sub("<[^>]+>", "", x).strip() for x in re.findall(r"<h2[^>]*>(.*?)</h2>", s, re.S)]
        shots = re.findall(r'src="(assets/img/[^"]+)"', s)
        dias = re.findall(r'src="(assets/diagrams/[^"]+)"', s)
        pages[f] = {"label": label, "tip": tip,
                    "h1": re.sub("<[^>]+>", "", h1.group(1)).strip() if h1 else "",
                    "h2": h2, "shots": shots, "dias": dias}
    return pages


def main():
    pages = read_pages()
    wb = Workbook()
    wb.remove(wb.active)

    # 0_説明
    ws = wb.create_sheet("0_説明")
    ws["A1"] = "SAP SD 培训课程 — 配套 Excel"
    ws["A1"].font = Font(name="微软雅黑", size=14, bold=True, color="0854A0")
    lines = [
        "",
        "配套站点：../sap_cn/index.html（静态 HTML，双击即可离线打开，无需服务器）",
        "课程结构：概念 → 组织结构 → 主数据 → 定价 → 端到端流程 → 配置 → 实训（16 页）",
        "",
        "本 Excel 的 8 张表：",
        "  1_课程大纲   … 每个页面讲什么、用哪张自绘图、页内小节",
        "  2_学习WBS    … 按板块拆成可勾选的任务（含进度统计公式）",
        "  3_实训记录   … 五个实训任务要做的事、要记的单据号（可打印带进机房）",
        "  4_截图索引   … 页面引用的真实 SAP GUI 截图清单（含原文件名，可回 Word 原稿核对）",
        "  5_术语表     … 中英对照术语",
        "  6_Tcode速查  … 常用事务代码与用途",
        "  7_自绘图清单 … 本站自绘的流程图/结构图/思维导图",
        "",
        "重要声明：",
        "  · 「画面 N」的真实截图取自教材文档 S4.docx 内嵌的 SAP GUI 画面（中文界面），未重绘。",
        "  · 流程图/结构图/思维导图为本课程自绘 SVG，用于讲清结构与顺序。",
        "  · 订单类型 OR、项目类别 TAN、定价过程 RVAA01、条件类型 PR00/MWST 等含义通用，",
        "    但具体编码与字段随版本/行业方案而异 —— 请在自己系统用 F1/F4 或 IMG 路径核对。",
    ]
    for i, ln in enumerate(lines, 2):
        ws.cell(row=i, column=1, value=ln).font = Font(name="微软雅黑", size=10)
    ws.column_dimensions["A"].width = 110

    # 1_课程大纲
    rows = []
    for f, label, tip in common.NAV:
        d = pages[f]
        rows.append([f, label, d["h1"], " / ".join(d["h2"][:8]),
                     len(d["shots"]), len(d["dias"])])
    sheet(wb, "1_课程大纲", "1. 课程大纲（16 页）",
          ["文件", "导航名", "页面标题", "页内小节（h2）", "截图数", "自绘图数"],
          rows, [16, 12, 30, 70, 8, 10],
          note="截图数 = 该页引用的真实画面数（同一张图多次引用会重复计数）；自绘图数 = 该页的流程图/结构图/思维导图数。")

    # 2_学习WBS
    wbs = [
        ("A 概念", "concept", "能说出 SD 管什么、与 FI/MM/PP/CO 的分工", "画出五大单据链 + 说出三大概念层", 60),
        ("A 概念", "concept", "记住 12 个常见误解（面试/考试常问）", "任选 5 条用自己的话说一遍", 30),
        ("B 组织", "org", "理解企业结构/销售结构/装运结构", "能画出组织结构图并说明分配关系", 60),
        ("B 组织", "org", "销售范围 = 三键组合，能举例", "说出本系统的销售范围（≥2 个）", 30),
        ("C 主数据", "master", "客户主数据三层 + 四个伙伴角色", "说出四角色并说明各自决定什么", 40),
        ("C 主数据", "master", "物料主数据销售视图关键字段", "指出项目类别组/税分类/账户分配组在哪", 40),
        ("C 主数据", "master", "条件记录与价格的关系", "用 VK13 查到一条 PR00 并读出金额与有效期", 40),
        ("D 定价", "pricing", "条件技术四层结构", "能背出四层并解释每层作用", 50),
        ("D 定价", "pricing", "定价过程确定三键", "说出三键并知道在哪配", 30),
        ("D 定价", "pricing", "账户确定：收入科目怎么定", "说出账码 + 两个账户分配组", 40),
        ("E 流程", "flow", "O2C 端到端流程与单据流", "默画流程图（含 T-code）", 60),
        ("E 流程", "order", "报价 VA21 → 订单 VA01 参照创建", "独立建出报价与订单并记录单号", 60),
        ("E 流程", "delivery", "交货 VL01N + 拣配 + 发货过账 601", "完成一次发货过账并记录库存变化", 60),
        ("E 流程", "billing", "发票 VF01 + 下达 VF02 + 会计凭证", "完成开票与下达，看到会计凭证", 60),
        ("E 流程", "analysis", "单据流 / VA05 / MCTA 的用法", "用单据流回答「这单到哪了」", 40),
        ("F 配置", "config", "48 个配置任务的分组与路径", "指出 3 个任务对应的后台菜单", 60),
        ("F 配置", "config", "知道哪些配置是必须自建、哪些可用标准", "列出本系统里已存在/缺失的配置", 40),
        ("G 实训", "practice", "五个实训任务全部完成", "完成基准逐条打勾（见 3_实训记录）", 180),
        ("H 收尾", "quiz", "30 题自测（≥75%）", "得分与错题回顾", 45),
    ]
    rows = []
    for i, (phase, page, what, done, mins) in enumerate(wbs, 1):
        rows.append([i, phase, common.NAV_LABEL.get(page, page) if hasattr(common, "NAV_LABEL") else page,
                     what, done, "", "", mins])
    ws, hrow = sheet(wb, "2_学习WBS", "2. 学习WBS（可勾选进度）",
                     ["#", "板块", "课程页", "学什么", "完成基准（能自己验证）", "自己判定", "笔记 / 疑问", "预计分钟"],
                     rows, [5, 10, 12, 40, 46, 10, 34, 10],
                     note="「自己判定」填 ○ / △ / ×（单元格已加下拉）。进度汇总见本表下方。")
    last = hrow + len(rows)
    for r in range(hrow + 1, last + 1):
        ws.cell(row=r, column=6).alignment = CENTER
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type="list", formula1='"○,△,×"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add("F%d:F%d" % (hrow + 1, last))
    ws.cell(row=last + 2, column=4, value="合计 / 完成率").font = Font(name="微软雅黑", size=10, bold=True)
    ws.cell(row=last + 2, column=5, value="=COUNTA(E%d:E%d)&\" 项\"" % (hrow + 1, last)).font = CELL_FONT
    ws.cell(row=last + 3, column=4, value="已完成（○）").font = Font(name="微软雅黑", size=10, bold=True)
    ws.cell(row=last + 3, column=5, value='=COUNTIF(F%d:F%d,"○")&" / "&COUNTA($D$%d:$D$%d)' % (hrow + 1, last, hrow + 1, last)).font = CELL_FONT
    ws.cell(row=last + 4, column=4, value="预计总时长（分钟）").font = Font(name="微软雅黑", size=10, bold=True)
    ws.cell(row=last + 4, column=5, value="=SUM(H%d:H%d)" % (hrow + 1, last)).font = CELL_FONT

    # 3_实训记录
    prac = [
        ["1", "看懂组织结构", "记录 2~3 个销售范围的三键组合；找到工厂→销售组织分配", "", "", "", "", ""],
        ["2", "报价 → 销售订单", "VA21 建报价 → 后继功能建订单（OR）；记录确认交货日期与净价值", "", "", "", "", ""],
        ["3", "交货与发货过账", "VL01N 建交货 → VL02N 拣配 → 发货过账（601）；记录库存前后数量", "", "", "", "", ""],
        ["4", "开票与过账", "VF01 开票（F2）→ VF02 下达；记录发票号、净价值与会计凭证借贷", "", "", "", "", ""],
        ["5", "追踪与报表", "VA03 单据流 → VA05 订单清单 → VL06O / VF04；记录三个单据号成链", "", "", "", "", ""],
    ]
    sheet(wb, "3_实训记录", "3. 实训记录（可打印带进机房）",
          ["任务", "名称", "做什么", "单据号 / 关键值", "日期", "状态", "金额 / 数量", "卡住时的现象与报错"],
          prac, [6, 18, 46, 24, 12, 16, 16, 40],
          note="做法与完成基准见站点 practice.html。建议 A4 横向打印。")

    # 4_截图索引
    rows = []
    idx = 0
    for f, label, tip in common.NAV:
        for p in pages[f]["shots"]:
            idx += 1
            rel = p.replace("assets/img/", "")
            task = re.match(r"(sd|prep)/t(\d+)/", rel)
            rows.append([idx, f, label, rel, ("任务 %s" % task.group(2)) if task else "准备章",
                         rel.split("/")[-1], p])
    sheet(wb, "4_截图索引", "4. 截图索引（真实 SAP GUI 画面）",
          ["#", "所在页", "导航名", "assets 内路径", "教材任务", "原文件名", "页面引用"],
          rows, [5, 14, 10, 34, 12, 26, 34],
          note="原文件名 = 教材文档 S4.docx 内嵌图片的原始名称，可回 Word 原稿一一核对。")

    # 5_术语表
    rows = [[zh, en, code, desc] for zh, en, code, desc in p_admin.TERMS]
    sheet(wb, "5_术语表", "5. 术语表（中英对照）", ["中文", "英文", "代码", "说明"], rows, [26, 40, 12, 60])

    # 6_Tcode
    rows = [[tc, desc, grp, src] for tc, desc, grp, src in p_admin.TCODES]
    sheet(wb, "6_Tcode速查", "6. 常用 T-code", ["T-code", "用途", "环节", "教材任务（任务号）"], rows, [22, 46, 10, 16])

    # 7_自绘图清单
    dias = {}
    for f, label, _t in common.NAV:
        for d in pages[f]["dias"]:
            dias.setdefault(d, []).append(label)
    rows = [[i, d.split("/")[-1], "、".join(v), d] for i, (d, v) in enumerate(sorted(dias.items()), 1)]
    sheet(wb, "7_自绘图清单", "7. 自绘流程图 / 结构图 / 思维导图",
          ["#", "文件", "用在哪些页", "路径"], rows, [5, 24, 40, 40],
          note="全部为本课程自绘 SVG（矢量，投影放大不糊）；页面上点击可放大到 4×。")

    wb.save(OUT)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
