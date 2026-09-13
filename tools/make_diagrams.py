# -*- coding: utf-8 -*-
"""生成课程用的流程图 / 结构图 / 思维导图（纯 Python → SVG，无外部依赖、离线可用）。

为什么手写 SVG：站点要求 file:// 直接可开、不联网、不需要 CDN 字体；同时
文字宽度必须按 CJK 全角 1.0em 估算，否则中文会溢出方框（这条在别的站踩过）。

用法:  python3 tools/make_diagrams.py            # 写 assets/diagrams/*.svg
       python3 tools/make_diagrams.py --check     # 只检查 XML 是否合法 + 文字是否溢出
"""
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "assets", "diagrams")

BLUE, BLUE_D, BLUE_L = "#0a6ed1", "#0854a0", "#e3f0fa"
TEAL, TEAL_B = "#007272", "#e6f2f2"
AMBER, AMBER_B = "#8d6e00", "#fdf3d7"
GREEN, GREEN_B = "#177245", "#e6f2ec"
RED, RED_B = "#b3261e", "#fdeae9"
INK, INK2, MUTED, LINE = "#1d2d3e", "#354a5f", "#6b7a8d", "#d9e1e8"
FONT = "'PingFang SC','Hiragino Sans GB','Noto Sans CJK SC','Microsoft YaHei',sans-serif"
MONO = "'SF Mono',Menlo,Consolas,monospace"


# --------------------------------------------------------------------------
# 文本度量（CJK 全角 1.0em / 半角约 0.55em）—— 与其它站共用的教训
# --------------------------------------------------------------------------
def char_w(ch):
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 1.0
    if ch in "iljI.,:;'|! ":
        return 0.32
    if ch in "mMW@":
        return 0.9
    return 0.575


def text_w(s, size):
    return sum(char_w(c) for c in s) * size


def wrap(s, size, maxw, max_lines=None):
    """按显示宽度折行（CJK 可断行，ASCII 词整体移动）。"\n" 视为强制换行。"""
    if "\n" in s:
        out = []
        for part in s.split("\n"):
            out.extend(wrap(part, size, maxw))
        if max_lines and len(out) > max_lines:
            out = out[:max_lines]
            out[-1] = out[-1][: max(1, len(out[-1]) - 1)] + "…"
        return out
    words, cur, lines = [], "", []
    for ch in s:
        if ch == " ":
            words.append(cur)
            words.append(" ")
            cur = ""
        else:
            cur += ch
    words.append(cur)
    line = ""
    for w in words:
        if text_w(line + w, size) <= maxw:
            line += w
        else:
            if line:
                lines.append(line.rstrip())
            while text_w(w, size) > maxw and len(w) > 1:
                k = 1
                while k < len(w) and text_w(w[: k + 1], size) <= maxw:
                    k += 1
                lines.append(w[:k])
                w = w[k:]
            line = w
    if line.strip():
        lines.append(line.rstrip())
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: max(1, len(lines[-1]) - 1)] + "…"
    return lines


# --------------------------------------------------------------------------
# SVG 原语
# --------------------------------------------------------------------------
def svg_open(w, h, title):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
        'role="img" aria-label="%s" font-family="%s">\n'
        '<title>%s</title>\n'
        '<defs>'
        '<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>'
        '<marker id="ar2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>'
        '<marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#ffffff"/></marker>'
        '</defs>\n<rect width="%d" height="%d" fill="#ffffff"/>\n'
    ) % (w, h, w, h, title, FONT, title, BLUE, TEAL, w, h)


def t(x, y, s, size=13.0, fill=INK, anchor="start", weight="400", family=None, opacity=None):
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    fam = " font-family=\"%s\"" % family if family else ""
    op = ' opacity="%s"' % opacity if opacity else ""
    return '<text x="%.1f" y="%.1f" font-size="%s" fill="%s" text-anchor="%s" font-weight="%s"%s%s>%s</text>\n' % (
        x, y, size, fill, anchor, weight, fam, op, s)


def rect(x, y, w, h, fill="#ffffff", stroke=LINE, rx=8, sw=1.4, dash=None):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%s" fill="%s" stroke="%s" stroke-width="%s"%s/>\n' % (
        x, y, w, h, rx, fill, stroke, sw, d)


def line(x1, y1, x2, y2, stroke=MUTED, sw=1.4, dash=None, marker=None):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    m = ' marker-end="url(#%s)"' % marker if marker else ""
    return '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%s"%s%s/>\n' % (
        x1, y1, x2, y2, stroke, sw, d, m)


def path(d, stroke=MUTED, sw=1.6, fill="none", dash=None, marker=None):
    da = ' stroke-dasharray="%s"' % dash if dash else ""
    m = ' marker-end="url(#%s)"' % marker if marker else ""
    return '<path d="%s" fill="%s" stroke="%s" stroke-width="%s"%s%s/>\n' % (d, fill, stroke, sw, da, m)


def badge(cx, cy, label, fill=BLUE, r=11, size=12, tcolor="#ffffff"):
    return ('<circle cx="%.1f" cy="%.1f" r="%s" fill="%s"/>' % (cx, cy, r, fill)
            + t(cx, cy + 4.3, label, size, tcolor, "middle", "700"))


def node(x, y, w, h, title, lines, accent=BLUE, bg="#ffffff", badge_txt=None,
         title_size=14.5, body_size=12, mono_lines=()):
    """标准方框：标题 + 若干正文行，自动按宽度折行并自适应高度。"""
    pad = 12
    out = [rect(x, y, w, h, bg, accent, 9)]
    out.append(rect(x, y, 4.5, h, accent, accent, rx=2))
    ty = y + 22
    out.append(t(x + pad, ty, title, title_size, accent if bg == "#ffffff" else accent,
                 weight="700"))
    cy = ty + 19
    for ln in lines:
        for seg in wrap(ln, body_size, w - 2 * pad, 3):
            out.append(t(x + pad, cy, seg, body_size, INK2))
            cy += body_size + 5.5
    for ln in mono_lines:
        out.append(t(x + pad, cy, ln, 11, MUTED, family=MONO))
        cy += 16
    if badge_txt:
        out.append(badge(x + w - 14, y + 14, badge_txt, accent, r=11))
    return "".join(out), cy


def arrow(x1, y1, x2, y2, color=BLUE, sw=1.8, dash=None, marker="ar"):
    return line(x1, y1, x2, y2, color, sw, dash, marker)


def chain(x, y, items, color=BLUE, avail=460, size=11, rowh=44):
    """横向流程链，超出可用宽度自动折到下一行。返回 (svg, 占用高度)。

    箭头只画在同一行的相邻两项之间；换行处画一个折返的小箭头，避免出现
    「指向空白」的箭头。
    """
    widths = [text_w(it, size) + 22 for it in items]
    # 先排版（决定每个元素落在第几行、x 位置）
    pos, cx_, cy_, rows = [], x, y, 1
    for i, w in enumerate(widths):
        if cx_ + w > x + avail and cx_ > x:
            cx_, cy_, rows = x, cy_ + rowh, rows + 1
        pos.append((cx_, cy_, w))
        cx_ += w + 18
    out = []
    for i, ((px, py, w), it) in enumerate(zip(pos, items)):
        out.append(rect(px, py, w, 34, "#ffffff", color, 8, 1.2))
        out.append(t(px + 11, py + 22, it, size, INK2))
        if i < len(items) - 1:
            nx, ny, _nw = pos[i + 1]
            if ny == py:                       # 同行：直箭头
                out.append(arrow(px + w + 1, py + 17, nx - 3, py + 17, color, 1.3))
            else:                              # 换行：折返到下一行行首的方框（避免箭头指向空白）
                sx = px + w + 1
                d = "M %.0f %.0f h 10 v %d h %.0f h 12" % (sx, py + 17, rowh, -(sx + 10 - (x - 14)))
                out.append(path(d, stroke=color, sw=1.3, marker="ar"))
    return "".join(out), rows * rowh + 6


def arrow_lr(x1, y1, x2, y2, color=BLUE, sw=1.8, dash=None):
    """水平双向箭头（集成关系用）。"""
    return line(x1, y1, x2, y2, color, sw, dash, "ar")


def note_bar(x, y, w, text, fill=BLUE_L, stroke=BLUE, size=12.5):
    lines = wrap(text, size, w - 24)
    h = 14 + len(lines) * (size + 6)
    out = [rect(x, y, w, h, fill, stroke, 8, 1.2)]
    cy = y + 20
    for ln in lines:
        out.append(t(x + 12, cy, ln, size, BLUE_D if stroke == BLUE else INK2))
        cy += size + 6
    return "".join(out), y + h


def title_bar(x, y, w, main, sub=None, size=20):
    out = [t(x, y, main, size, INK, weight="700")]
    if sub:
        out.append(t(x, y + 22, sub, 13, MUTED))
    return "".join(out)


# --------------------------------------------------------------------------
# 1. 思维导图 — 课程知识地图（总体 → 局部）
# --------------------------------------------------------------------------
def mindmap():
    W, H = 1420, 1240
    s = [svg_open(W, H, "SAP SD 知识地图（思维导图）")]
    s.append(t(40, 46, "SAP SD 知识地图 — 从总体到局部", 22, INK, weight="700"))
    s.append(t(40, 70, "六大板块：① 概念 ② 组织 ③ 主数据 ④ 定价 ⑤ 流程 ⑥ 配置与分析。叶节点 = 课程要点（本站自绘 SVG）", 12.5, MUTED))

    cx, cy = 710, 660
    CW = 240
    s.append(rect(cx - CW / 2, cy - 75, CW, 150, BLUE_D, BLUE_D, 16))
    s.append(t(cx, cy - 22, "SAP SD", 32, "#ffffff", "middle", "700"))
    s.append(t(cx, cy + 10, "销售与分销", 18, "#dbeafd", "middle"))
    s.append(t(cx, cy + 36, "Sales & Distribution", 12, "#a9cdf3", "middle", family=MONO))
    s.append(t(cx, cy + 60, "看地图 → 走流程 → 配系统", 11.5, "#a9cdf3", "middle"))

    branches = [
        # (标题, 颜色, 方向, 叶子)
        ("① 概念与定位", BLUE, "L", [
            "SD 管什么：卖什么 · 卖给谁 · 怎么定价 · 怎么发货 · 怎么开票",
            "与 FI / MM / PP / CO 的分界：SD 出「销售凭证」，邻居模块出库存与会计凭证",
            "三大概念层：组织结构 → 主数据 → 单据（配置顺序也是这个顺序）",
            "五大单据：询价 · 报价 · 销售订单 · 交货 · 发票",
            "核心组织键：销售范围 = 销售组织 + 分销渠道 + 产品组",
        ]),
        ("② 组织结构", TEAL, "L", [
            "企业结构：公司代码 / 销售组织 / 工厂",
            "销售结构：分销渠道 / 产品组 / 销售办公室 / 销售组",
            "装运结构：起运点 / 装载点 / 拣配库存地点 / 运送条件",
            "分配关系多为多对多（一工厂可对多销售组织，一起运点可服务多工厂）",
            "组织数据决定：主数据怎么建、单据怎么跑、库存从哪发、收入怎么记账",
        ]),
        ("③ 主数据", GREEN, "L", [
            "客户主数据三层：一般数据 / 公司代码数据 / 销售范围数据",
            "四个伙伴角色：售达方 · 送达方 · 收票方 · 付款方（可指向同一客户的不同编号）",
            "物料主数据：销售视图（销售范围级）+ 工厂级视图（MRP 等）",
            "条件记录：销售价格 PR00 / 折扣 / 销项税 MWST 等（VK11 维护）",
            "客户-物料信息记录 · 物料确定（清单与排斥）· 客户账户组",
        ]),
        ("④ 定价与条件技术", AMBER, "R", [
            "四层结构：条件表 → 存取顺序 → 条件类型 → 定价过程",
            "条件类型 PR00（价格）/ MWST（销项税）/ 折扣与附加费（教材用 RVAA01 标准过程）",
            "存取顺序决定「先找专用价，找不到再找一般价」的查找优先级",
            "定价过程确定三键：销售范围 + 客户定价过程 + 单据定价过程",
            "账户确定：账码 + 物料/客户账户分配组 → 收入科目（VKOA）",
        ]),
        ("⑤ 业务流程 O2C", RED, "R", [
            "售前：询价 VA11 → 报价 VA21（可参照创建）",
            "接单：销售订单 VA01 —— 定价 + 可用性检查 ATP → 确认交货日期",
            "交付：外向交货 VL01N → 拣配 → 发货过账 VL02N（移动类型 601 才真正出库）",
            "结算：发票 VF01 → 过账 VF02 → 会计凭证 → 收款 F-28 清账",
            "监控：单据流（VA03 → 环境）/ 订单清单 VA05 / 销售分析 MCTA",
        ]),
        ("⑥ 配置与分析", "#5b3fa8", "R", [
            "SPRO 路线：组织 → 装运 → 主数据 → 定价 → 账户确定 → 更新组",
            "凭证控制对象：销售凭证类型 / 项目类别 / 计划行类别（VOV4 / VOV5 / VOV7）",
            "检查与规则：不完整性检查 OVA2、信贷管理、合作伙伴确定",
            "输出确定：订单确认 / 交货单 / 发票的输出与打印",
            "分析：VC/2 销售汇总、VA05 订单清单、MCTA 销售分析、资产负债表",
        ]),
    ]
    left = [b for b in branches if b[2] == "L"]
    right = [b for b in branches if b[2] == "R"]
    LEAF_W = 480
    LEAF_H = 46
    HEAD_W = 200
    HEAD_H = 42
    LEFT_X = 40                      # 左侧分支：叶子与分支头都靠左，分支头右对齐到 INNER_L
    INNER_L = LEFT_X + LEAF_W        # 520
    HEAD_X_L = INNER_L - HEAD_W      # 320
    RIGHT_X = 900                    # 右侧分支：叶子与分支头都靠右
    band_top = 108
    band_h = (H - band_top - 40) / 3.0

    def draw_branch(idx, title, color, direction, leaves):
        y0 = band_top + idx * band_h
        hy = y0
        lx = LEFT_X if direction == "L" else RIGHT_X
        hx = HEAD_X_L if direction == "L" else RIGHT_X
        # 分支头（彩色药丸）
        s.append(rect(hx, hy, HEAD_W, HEAD_H, color, color, 12))
        s.append(t(hx + HEAD_W / 2, hy + 28, title, 16, "#ffffff", "middle", "700"))
        # 中心 → 分支头：只走中间那道空隙，避免穿过叶子方框
        y1 = cy - 48 + idx * 24
        if direction == "L":
            x0, x1 = cx - CW / 2, hx + HEAD_W
            c1, c2 = x0 - 46, x1 + 46
        else:
            x0, x1 = cx + CW / 2, hx
            c1, c2 = x0 + 46, x1 - 46
        s.append(path("M %.0f %.0f C %.0f %.0f %.0f %.0f %.0f %.0f"
                      % (x0, y1, c1, y1, c2, hy + HEAD_H / 2, x1, hy + HEAD_H / 2),
                      stroke=color, sw=2.6))
        # 叶子（与分支头之间用短折线相连）
        n = len(leaves)
        total = n * LEAF_H + (n - 1) * 9
        ly = y0 + HEAD_H + 12
        for leaf in leaves:
            s.append(rect(lx, ly, LEAF_W, LEAF_H, "#ffffff", color, 8, 1.2))
            lines = wrap(leaf, 12.5, LEAF_W - 24, 2)
            for i, seg in enumerate(lines):
                s.append(t(lx + 12, ly + (29 if len(lines) == 1 else 20 + i * 16), seg, 12.5, INK2))
            if direction == "L":
                s.append(line(lx + LEAF_W, ly + LEAF_H / 2, hx + HEAD_W / 2, hy + HEAD_H, color, 1.2))
            else:
                s.append(line(lx, ly + LEAF_H / 2, hx + HEAD_W / 2, hy + HEAD_H, color, 1.2))
            ly += LEAF_H + 9

    for i, b in enumerate(left):
        draw_branch(i, b[0], b[1], "L", b[3])
    for i, b in enumerate(right):
        draw_branch(i, b[0], b[1], "R", b[3])
    s.append("</svg>\n")
    return "mindmap.svg", "".join(s)


# --------------------------------------------------------------------------
# 2. 组织结构图（结构图）
# --------------------------------------------------------------------------
def org_structure():
    W, H = 1360, 820
    s = [svg_open(W, H, "SAP SD 组织结构图")]
    s.append(title_bar(40, 48, W - 80, "SD 组织结构（企业结构 → 销售结构 → 装运结构）",
                       "同一套组织数据同时决定：主数据怎么建、单据怎么跑、库存从哪发、收入怎么记账（本站自绘）"))

    def box(x, y, w, h, title, sub="", color=BLUE, bg="#ffffff", mono=None):
        s.append(rect(x, y, w, h, bg, color, 9))
        s.append(rect(x, y, 4.5, h, color, color, rx=2))
        s.append(t(x + 12, y + 22, title, 14, color, weight="700"))
        yy = y + 40
        for ln in wrap(sub, 11.5, w - 24, 3):
            s.append(t(x + 12, yy, ln, 11.5, INK2))
            yy += 16
        if mono:
            s.append(t(x + 12, yy + 2, mono, 10.5, MUTED, family=MONO))
        return yy

    # A 企业结构
    s.append(t(60, 110, "A. 企业结构（Enterprise Structure）", 15, BLUE_D, weight="700"))
    box(60, 122, 300, 74, "公司代码 / 公司", "财务报表与会计的最小单位", BLUE_D, BLUE_L)
    box(60, 216, 300, 74, "销售组织 (Sales Organization)", "负责销售的法律单位：产品责任、销售统计", BLUE, "#ffffff")
    box(60, 310, 300, 74, "工厂 (Plant)", "生产 / 库存地点所属的组织单位（发货从这里发生）", TEAL, "#ffffff")
    box(60, 404, 300, 74, "采购组织 / 装运点协调", "跨模块共用：SD 只关心工厂与库存", MUTED, "#f7fafc")

    # 连线 A→B
    s.append(path("M 210 196 L 210 216", BLUE))
    s.append(path("M 210 290 L 210 310", TEAL))
    s.append(path("M 210 384 L 210 404", MUTED))
    s.append(arrow(360, 160, 470, 160, BLUE))
    s.append(path("M 360 253 L 470 253", BLUE))

    # B 销售结构
    s.append(t(480, 110, "B. 销售结构（Sales Structure）", 15, TEAL))
    box(480, 122, 250, 74, "分销渠道", "产品如何到达客户：直销 / 批发 / 零售", TEAL, "#ffffff")
    box(480, 216, 250, 74, "产品组", "把产品按线分组：整机 / 备件 / 服务", TEAL, "#ffffff")
    box(480, 310, 250, 74, "销售办公室", "地理 / 责任范围（按地区划分的销售机构）", TEAL, "#ffffff")
    box(480, 404, 250, 74, "销售组", "销售办公室内的人员小组（分担责任）", TEAL, "#ffffff")
    s.append(path("M 605 290 L 605 310", TEAL))
    s.append(arrow(730, 160, 830, 160, TEAL))
    s.append(path("M 730 253 L 830 253", TEAL))
    s.append(path("M 730 347 L 830 347", TEAL))

    # C 销售范围 = 三键组合
    s.append(t(840, 110, "C. 销售范围 = 销售组织 + 分销渠道 + 产品组", 15, "#5b3fa8"))
    s.append(rect(840, 122, 460, 116, "#f4f0ff", "#5b3fa8", 10))
    s.append(t(856, 148, "销售范围（Sales Area）", 15, "#5b3fa8", weight="700"))
    for i, ln in enumerate(wrap("业务含义：某个销售组织「通过某种分销渠道」经营「某个产品组」。"
                                "它决定客户主数据、物料主数据（销售视图）、条件记录与所有销售单据的组织键，"
                                "也是定价过程确定、账户确定的输入。", 11.5, 430, 4)):
        s.append(t(856, 168 + i * 16, ln, 11.5, INK2))
    s.append(rect(840, 250, 460, 84, GREEN_B, GREEN, 10))
    s.append(t(856, 274, "例（教材场景 颐宁）", 13, GREEN, weight="700"))
    for i, ln in enumerate(wrap("1 个销售组织 × 2 个分销渠道（直销 / 批发）× 2 个产品组 → 4 个销售范围，逐一设置。",
                                11.5, 430, 2)):
        s.append(t(856, 294 + i * 16, ln, 11.5, INK2))
    s.append(rect(840, 346, 460, 84, BLUE_L, BLUE, 10))
    s.append(t(856, 370, "销售办公室 / 销售组", 13, BLUE_D, weight="700"))
    for i, ln in enumerate(wrap("分配到销售范围（后台）：用于统计与权限，不影响单价的确定。", 11.5, 430, 2)):
        s.append(t(856, 390 + i * 16, ln, 11.5, INK2))

    # D 装运结构
    s.append(t(60, 520, "D. 装运结构（Shipping）", 15, TEAL))
    shp = [
        (60, "起运点", "发货的起始地点（与工厂多对多）\n教材例：Z999 颐宁装运点"),
        (290, "装载点", "装货的具体位置（按起运点分配）"),
        (520, "拣配库存地点", "从哪个库存地点拣货（按起运点 + 工厂 + 存储条件确定）"),
        (750, "运送条件", "交货的运输方式与时间（与物料 / 工厂共同决定起运点）"),
        (980, "装载组", "与物料主数据共同决定装载点"),
    ]
    for x, ti, sub in shp:
        s.append(rect(x, 532, 210, 96, "#ffffff", TEAL, 9))
        s.append(rect(x, 532, 4.5, 96, TEAL, TEAL, rx=2))
        s.append(t(x + 12, 554, ti, 14, TEAL, weight="700"))
        yy = 572
        for ln in sub.split("\n"):
            for seg in wrap(ln, 11.5, 186, 2):
                s.append(t(x + 12, yy, seg, 11.5, INK2))
                yy += 15
    s.append(arrow(255, 580, 290, 580, TEAL))
    s.append(arrow(485, 580, 520, 580, TEAL))
    s.append(arrow(715, 580, 750, 580, TEAL))
    s.append(arrow(945, 580, 980, 580, TEAL))

    # 派生链（底部）
    s.append(rect(60, 656, 1240, 124, "#f7fafc", LINE, 10))
    s.append(t(76, 682, "系统怎么自动找到这些组织数据（自动确定的链条）", 14, INK, weight="700"))
    chain = [
        "客户主数据（销售范围层的客户）", "销售凭证类型（如 OR 标准订单）", "输入物料的物料主数据",
        "工厂 / 起运点 / 装运点", "拣配库存地点",
    ]
    x = 76
    for i, c in enumerate(chain):
        w = text_w(c, 11.5) + 22
        s.append(rect(x, 700, w, 34, "#ffffff", BLUE, 8, 1.2))
        s.append(t(x + 11, 722, c, 11.5, INK2))
        x += w + 6
        if i < len(chain) - 1:
            # 箭头从方框外侧 6px 起笔，避免「尾端从方框内部起笔」的视觉粘连
            s.append(arrow(x + 2, 717, x + 14, 717, BLUE, 1.6))
            x += 20
    for i, ln in enumerate(wrap("关键：组织数据不是「每次手输」——单据抬头/项目的销售范围由客户主数据带出、"
                                "工厂由物料主数据与装运条件推出、库存地点由后台配置决定。配置错了，单据就跑不起来或跑到错的库存。",
                                12, 1200, 2)):
        s.append(t(76, 752 + i * 18, ln, 12, INK2))
    s.append("</svg>\n")
    return "org-structure.svg", "".join(s)


# --------------------------------------------------------------------------
# 3. SD 与其它模块的集成（结构图）
# --------------------------------------------------------------------------
def integration():
    W, H = 1300, 660
    s = [svg_open(W, H, "SD 与 FI / MM / PP / CO 的集成结构图")]
    s.append(title_bar(40, 48, W - 80, "SD 与其它模块的集成（一张图看数据往哪流）",
                       "SD 只负责「卖」；真正扣库存、记收入、拉生产的是邻居模块（本站自绘）"))
    # 中心
    s.append(rect(500, 300, 300, 150, BLUE_D, BLUE_D, 14))
    s.append(t(650, 348, "SD 销售与分销", 22, "#ffffff", "middle", "700"))
    s.append(t(650, 376, "订单 · 交货 · 发票", 13.5, "#dbeafd", "middle"))
    s.append(t(650, 400, "VA01 / VL01N / VF01", 12, "#a9cdf3", "middle", family=MONO))
    s.append(t(650, 424, "驱动的都只是 SD 自己的凭证", 11.5, "#a9cdf3", "middle"))

    def mod(x, y, w, h, title, sub, tcodes, color, lines, side):
        s.append(rect(x, y, w, h, "#ffffff", color, 11))
        s.append(rect(x, y, 4.5, h, color, color, rx=2))
        s.append(t(x + 14, y + 26, title, 16, color, weight="700"))
        s.append(t(x + 14, y + 46, sub, 11.5, MUTED))
        yy = y + 68
        for ln in lines:
            for seg in wrap(ln, 11.5, w - 28, 2):
                s.append(t(x + 14, yy, seg, 11.5, INK2))
                yy += 16
        s.append(t(x + 14, y + h - 12, tcodes, 11, color, family=MONO))
        # 箭头
        if side == "left":
            s.append(line(x + w, y + h / 2, 500, 375, color, 2.0, None, "ar"))
            s.append(line(500, 400, x + w, y + h / 2 + 22, color, 1.6, "4 3", "ar"))
        else:
            s.append(line(x, y + h / 2, 800, 375, color, 2.0, None, "ar"))
            s.append(line(800, 400, x, y + h / 2 + 22, color, 1.6, "4 3", "ar"))

    mod(60, 140, 380, 140, "MM 物料管理", "库存与采购", "MB1C / MIGO / MB52 / MD04", TEAL,
        ["发货过账 601 才真正扣库存（SD 只交货不扣账）",
         "无库存 → 交货无法创建（教材里用 MB1C 501 录入期初库存解决）",
         "采购收货 101 增加可用库存，影响订单的可用性检查结果"], "left")
    mod(60, 420, 380, 140, "FI 财务会计", "应收 / 收入 / 税", "FS00 / VKOA / F-28 / FBL5N", "#5b3fa8",
        ["发票过账（VF02）生成会计凭证：借 客户应收 / 贷 收入 + 销项税",
         "科目由 VKOA「账户确定」+ 物料/客户账户分配组推出",
         "收款 F-28 冲销应收，可用 FBL5N 查看客户未清项"], "left")
    mod(860, 140, 380, 140, "PP 生产计划", "需求传递与供给", "MD04 / MD01N / CO01 / MD61", AMBER,
        ["订单项目的需求类型/需求类别把需求传给 MRP（MD04）",
         "MTO 场景：需求进「个别客户库存」而不是自由库存",
         "MTS 场景：先有计划独立需求（MD61），订单只是消耗预测"], "right")
    mod(860, 420, 380, 140, "CO 管理会计", "收入与成本对象", "KKA2 / CJ88 / VA88 / KO88", GREEN,
        ["收入按账户确定进 CO-PA 获利分析（收入要素）",
         "ETO/项目场景：收入上 WBS，结算用 CJ88 等",
         "成本对象决定边际贡献怎么算"], "right")

    s.append(rect(470, 470, 360, 118, "#f7fafc", LINE, 10))
    s.append(t(488, 496, "共用的「技术底座」", 14, INK, weight="700"))
    for i, ln in enumerate(wrap("组织数据（公司代码 / 工厂 / 销售组织）、主数据（客户 / 物料）、"
                                "编号范围、单据流——SD 与邻居模块读同一套数据，所以配置顺序是"
                                "「先组织、后主数据、最后单据」。", 11.5, 324, 4)):
        s.append(t(488, 516 + i * 16, ln, 11.5, INK2))
    s.append("</svg>\n")
    return "integration.svg", "".join(s)


# --------------------------------------------------------------------------
# 4. 定价条件技术（结构图）
# --------------------------------------------------------------------------
def pricing_chain():
    W, H = 1340, 900
    s = [svg_open(W, H, "条件技术与定价过程确定（结构图）")]
    s.append(title_bar(40, 48, W - 80, "定价的四层结构：条件表 → 存取顺序 → 条件类型 → 定价过程",
                       "「价格从哪来」是 SD 里问得最多的问题；这四层回答它，第五步决定「用哪套过程」（本站自绘）"))

    # 四层
    layers = [
        (1, "条件表 Condition Table", BLUE, "存「具体价格」。行 = 键组合（客户 / 物料 / 销售组织…），值 = 金额或百分比。",
         "教材场景：PR00 的存取顺序里包含「具有审批状态的物料」等步骤"),
        (2, "存取顺序 Access Sequence", TEAL, "按优先级排列若干条件表。系统从第一步开始找，找到就停（找不到才继续）。",
         "含义：先找该客户的专用价 → 再找该物料的一般价 → …"),
        (3, "条件类型 Condition Type", AMBER, "价格、折扣、运费、税…都是条件类型。它带出存取顺序、计算规则与账码。",
         "PR00 = 销售价格 / MWST = 销项税 / K004 类的折扣与附加费"),
        (4, "定价过程 Pricing Procedure", "#5b3fa8", "把条件类型按步骤排成一张表：步骤 → 条件类型 → 计算类型 → 账码 → 小计。",
         "教材场景：RVAA01「标准」是系统预配置、课程使用的定价过程"),
    ]
    y = 108
    for n, title, color, desc, ex in layers:
        s.append(rect(60, y, 560, 118, "#ffffff", color, 10))
        s.append(rect(60, y, 4.5, 118, color, color, rx=2))
        s.append(badge(84, y + 24, str(n), color, 12))
        s.append(t(106, y + 29, title, 16, color, weight="700"))
        yy = y + 52
        for ln in wrap(desc, 12, 520, 3):
            s.append(t(78, yy, ln, 12, INK2))
            yy += 17
        s.append(t(78, y + 106, ex, 11, MUTED))
        y += 134
    # 向右的箭头
    for i in range(3):
        s.append(arrow(620, 167 + i * 134, 660, 167 + i * 134, MUTED, 1.6))
    s.append(t(668, 140, "逐层引用：条件类型引用存取顺序，", 12, MUTED))
    s.append(t(668, 158, "定价过程引用条件类型", 12, MUTED))
    s.append(t(668, 274, "存取顺序引用条件表", 12, MUTED))
    s.append(t(668, 408, "过程里有账码 → 决定记账科目", 12, MUTED))

    # 右侧：定价过程确定 + 账户确定
    s.append(rect(660, 108, 620, 250, BLUE_L, BLUE, 11))
    s.append(t(680, 136, "第 5 层：定价过程确定（决定「用哪一套过程」）", 15, BLUE_D, weight="700"))
    det = [("销售范围", "销售组织 + 分销渠道 + 产品组"),
           ("客户定价过程", "客户主数据「销售视图 → 定价」里的字段（如 1 标准）"),
           ("单据定价过程", "销售凭证类型的定价字段（如 A 标准订单）")]
    yy = 164
    for k, v in det:
        s.append(rect(680, yy, 200, 34, "#ffffff", BLUE, 8, 1.2))
        s.append(t(692, yy + 22, k, 12.5, BLUE_D, weight="700"))
        for j, seg in enumerate(wrap(v, 11.5, 370, 2)):
            s.append(t(896, yy + 15 + j * 15, seg, 11.5, INK2))
        yy += 46
    s.append(t(680, yy + 8, "三个键 → 定出唯一一套定价过程（RVAA01）→ 系统据此逐行算价并记账", 11.5, BLUE_D))
    s.append(t(680, yy + 30, "IMG：销售和分销 → 基本功能 → 定价 → 定价控制 → 定义并分配定价过程", 11, MUTED, family=MONO))

    s.append(rect(660, 376, 620, 232, GREEN_B, GREEN, 11))
    s.append(t(680, 404, "配套：账户确定（收入记到哪个科目）", 15, GREEN, weight="700"))
    for i, ln in enumerate(wrap("发票过账时要生成会计凭证。销售收入科目不是写死的，由三个键查表（VKOA）推出：", 12, 580, 2)):
        s.append(t(680, 428 + i * 17, ln, 12, INK2))
    keys = [("账码 Account Key", "定价过程里每一步的账码，如 ERL = 收入"),
            ("物料账户分配组", "物料主数据销售视图里的字段（教材举例：M1 自制产品 / M2 贸易商品）"),
            ("客户账户分配组", "客户主数据里的字段（教材举例：01 国内收入）")]
    yy = 470
    for k, v in keys:
        s.append(rect(680, yy, 190, 36, "#ffffff", GREEN, 8, 1.2))
        s.append(t(690, yy + 23, k, 12, GREEN, weight="700"))
        for j, seg in enumerate(wrap(v, 11.5, 400, 2)):
            s.append(t(886, yy + 16 + j * 15, seg, 11.5, INK2))
        yy += 44
    s.append(t(680, yy + 14, "IMG：销售和分销 → 基本功能 → 科目分配/成本 → 收入账户确定", 11, MUTED, family=MONO))

    # 底部计算示例
    s.append(rect(60, 640, 1220, 140, "#f7fafc", LINE, 10))
    s.append(t(78, 668, "课程场景的算价例子（教材：30~120 件铸钢泵 170-230）", 14, INK, weight="700"))
    calc = [("物料 F999-100（铸钢泵 170-230）", ""), ("数量 120 PC", ""), ("PR00 单价 8,000.00", "条件类型：价格"),
            ("净价值 960,000.00 RMB", "条件类型：小计"), ("MWST 销项税", "按税分类 + 税码计算"),
            ("发票 F2 90000000", "过账后生成会计凭证")]
    x = 78
    for i, (v, sub) in enumerate(calc):
        w = max(text_w(v, 12), text_w(sub, 10.5)) + 28
        s.append(rect(x, 686, w, 44, "#ffffff", AMBER if i in (2, 3) else BLUE, 8, 1.2))
        s.append(t(x + 13, 706, v, 12, INK))
        s.append(t(x + 13, 722, sub, 10.5, MUTED))
        x += w + 4
        if i < len(calc) - 1:
            s.append(arrow(x - 2, 708, x + 2, 708, MUTED, 1.4))
            x += 8
    s.append(t(78, 760, "注：单价与税率为课程场景示意；实际金额由「条件记录 + 定价过程 + 税码」在各自系统里算出，"
                         "请在自系统用 VA03 → 项目 → 条件 页签核对。", 11.5, MUTED))
    s.append("</svg>\n")
    return "pricing-chain.svg", "".join(s)


# --------------------------------------------------------------------------
# 5. 端到端流程图 O2C（泳道）
# --------------------------------------------------------------------------
def o2c_flow():
    W, H = 1420, 900
    s = [svg_open(W, H, "SD 端到端流程图（Order to Cash）")]
    s.append(title_bar(40, 48, W - 80, "端到端流程图：从询价到收款（Order to Cash）",
                       "上排 = SD 的动作，中排 = 库存/装运真正发生的事，下排 = 财务被触发的时点（本站自绘）"))
    lanes = [("SD 销售与分销", 118, BLUE, BLUE_L),
             ("MM 库存与装运", 372, TEAL, TEAL_B),
             ("FI 财务会计", 626, "#5b3fa8", "#f4f0ff")]
    for name, y, color, bg in lanes:
        s.append(rect(40, y - 40, 1340, 240, bg, color, 12, 1.0))
        s.append(t(56, y - 16, name, 14, color, weight="700"))

    steps_sd = [
        ("询价 VA11", ["客户询问：要什么、要多少"], "询价单"),
        ("报价 VA21", ["正式报价，可含有效期"], "报价单"),
        ("销售订单 VA01", ["参照报价创建 OR 订单", "定价 + 可用性检查"], "销售订单"),
        ("外向交货 VL01N", ["按订单创建交货", "确定起运点/库存地点"], "交货单"),
        ("发票 VF01", ["参照交货开票"], "发票 F2"),
    ]
    steps_mm = [("可用库存", ["订单检查 ATP：库存是否够", "不够 → 提示无可用库存"]),
                ("拣配 + 发货过账 VL02N", ["移动类型 601：真正出库", "此时才产生物料凭证"]),
                (None, None)]
    x = 70
    w = 240
    for i, (title, lines, doc) in enumerate(steps_sd):
        s.append(rect(x, 130, w, 108, "#ffffff", BLUE, 10))
        s.append(rect(x, 130, 4.5, 108, BLUE, BLUE, rx=2))
        s.append(badge(x + 22, 152, str(i + 1), BLUE, 12))
        s.append(t(x + 42, 157, title, 14.5, BLUE_D, weight="700"))
        yy = 180
        for ln in lines:
            for seg in wrap(ln, 11.5, w - 30, 2):
                s.append(t(x + 16, yy, seg, 11.5, INK2))
                yy += 15
        s.append(t(x + 16, 226, "产出：" + doc, 11, MUTED, family=MONO))
        x += w + 32
        if i < len(steps_sd) - 1:
            s.append(arrow(x - 28, 184, x - 4, 184, BLUE, 2.0))

    # MM 泳道
    s.append(rect(310, 384, 240, 108, "#ffffff", TEAL, 10))
    s.append(rect(310, 384, 4.5, 108, TEAL, TEAL, rx=2))
    s.append(t(326, 410, "可用性检查（ATP）", 14, TEAL, weight="700"))
    s.append(t(326, 432, "订单保存时 / 交货创建时检查", 11.5, INK2))
    s.append(t(326, 452, "确认日期 = 最早能满足的日期", 11.5, INK2))
    s.append(t(326, 478, "库存不足仍可保存订单（除非设了块）", 11, MUTED))
    s.append(rect(582, 384, 300, 108, "#ffffff", TEAL, 10))
    s.append(rect(582, 384, 4.5, 108, TEAL, TEAL, rx=2))
    s.append(t(598, 410, "拣配 Picking", 14, TEAL, weight="700"))
    s.append(t(598, 432, "确定并从库存地点取货（拣配数量）", 11.5, INK2))
    s.append(t(598, 452, "然后「发货过账」：移动类型 601", 11.5, INK2))
    s.append(t(598, 478, "→ 物料凭证 + 库存减少（教材用 MB1C 501 补期初库存）", 11, MUTED))
    s.append(rect(914, 384, 300, 108, "#ffffff", TEAL, 10))
    s.append(rect(914, 384, 4.5, 108, TEAL, TEAL, rx=2))
    s.append(t(930, 410, "发货过账的后效", 14, TEAL, weight="700"))
    s.append(t(930, 432, "库存数量与金额同时减少（出库）", 11.5, INK2))
    s.append(t(930, 452, "交货状态变为「已完成」，可开票", 11.5, INK2))
    s.append(t(930, 478, "成本在 CO 侧体现（销货成本）", 11, MUTED))
    s.append(path("M 430 238 L 430 384", TEAL, 1.8, None, "4 4", "ar"))
    s.append(path("M 732 238 L 732 384", TEAL, 1.8, None, "4 4", "ar"))
    s.append(arrow(550, 438, 582, 438, TEAL, 1.8))
    s.append(arrow(882, 438, 914, 438, TEAL, 1.8))
    s.append(path("M 1064 384 L 1064 300 L 990 300", TEAL, 1.8, None, "4 4", "ar"))
    s.append(t(1000, 292, "发货完成才允许开票", 11.5, TEAL))

    # FI 泳道
    s.append(rect(640, 638, 340, 108, "#ffffff", "#5b3fa8", 10))
    s.append(rect(640, 638, 4.5, 108, "#5b3fa8", "#5b3fa8", rx=2))
    s.append(t(656, 664, "发票过账（下达）VF02", 14, "#5b3fa8", weight="700"))
    s.append(t(656, 686, "点「保存 / 下达」→ 系统提示「凭证已经传送到记账」", 11.5, INK2))
    s.append(t(656, 706, "生成会计凭证：借 客户应收 / 贷 收入 + 销项税", 11.5, INK2))
    s.append(t(656, 732, "科目由 VKOA + 账户分配组推出", 11, MUTED))
    s.append(rect(1020, 638, 340, 108, "#ffffff", "#5b3fa8", 10))
    s.append(rect(1020, 638, 4.5, 108, "#5b3fa8", "#5b3fa8", rx=2))
    s.append(t(1036, 664, "收款与清账", 14, "#5b3fa8", weight="700"))
    s.append(t(1036, 686, "收到货款 → F-28 收款冲销应收（或 FBL5N 查看未清项）", 11.5, INK2))
    s.append(t(1036, 706, "流程闭环：现金回来了", 11.5, INK2))
    s.append(t(1036, 732, "本站流程以教材场景为准：交货 → 发票 → 过账", 11, MUTED))
    s.append(path("M 900 238 L 900 560 L 810 560 L 810 638", "#5b3fa8", 1.8, None, "4 4", "ar"))
    s.append(arrow(980, 692, 1020, 692, "#5b3fa8", 1.8))

    # 单据流条
    s.append(rect(40, 776, 1340, 96, "#f7fafc", LINE, 10))
    s.append(t(56, 802, "单据流（Document Flow）：每个下游单据都「参照」上游单据创建，串成一条链", 14, INK, weight="700"))
    docs = ["询价单", "报价单", "销售订单", "交货单", "发票", "会计凭证"]
    x = 56
    for i, d in enumerate(docs):
        w = text_w(d, 12.5) + 30
        s.append(rect(x, 816, w, 36, "#ffffff", BLUE if i < 5 else "#5b3fa8", 8, 1.3))
        s.append(t(x + 15, 840, d, 12.5, INK))
        x += w
        if i < len(docs) - 1:
            s.append(arrow(x + 2, 834, x + 20, 834, MUTED, 1.6))
            x += 24
    s.append(t(56, 868, "核对方法：VA03（订单）→ 环境 → 显示单据流；或 VF03（发票）→ 抬头 → 点原始凭证，"
                         "可一路点回销售订单，确认「这三个环节串在一条链上」。", 11.5, MUTED))
    s.append("</svg>\n")
    return "o2c-flow.svg", "".join(s)


# --------------------------------------------------------------------------
# 6. 单据流结构图（参照关系 + 状态）
# --------------------------------------------------------------------------
def doc_flow():
    W, H = 1340, 620
    s = [svg_open(W, H, "单据流与参照关系（结构图）")]
    s.append(title_bar(40, 48, W - 80, "单据流结构图：谁参照谁、各单据带什么状态",
                       "「参照创建」保证了数据一致：数量、价格、客户从上游带下来（本站自绘）"))
    stages = [
        ("询价单", "VA11", "IN", ["客户意向", "不带价格约束"], BLUE),
        ("报价单", "VA21", "QT", ["有效期", "参照询价创建"], BLUE),
        ("销售订单", "VA01", "OR", ["定价确定", "可用性检查", "交货日期", "不完整性检查"], BLUE_D),
        ("交货单", "VL01N", "LF", ["拣配", "发货过账 601", "交货状态"], TEAL),
        ("发票", "VF01", "F2", ["开票", "过账生成 FI 凭证"], "#5b3fa8"),
    ]
    x = 60
    w = 222
    for i, (name, tc, tp, lines, color) in enumerate(stages):
        s.append(rect(x, 140, w, 190, "#ffffff", color, 12))
        s.append(rect(x, 140, w, 40, color, color, 12))
        s.append(t(x + 16, 167, name, 16, "#ffffff", weight="700"))
        s.append(t(x + w - 16, 167, tc, 12.5, "#eaf4ff", "end", family=MONO))
        s.append(t(x + 16, 206, "单据类型 / 类别：" + tp, 11.5, MUTED, family=MONO))
        yy = 230
        for ln in lines:
            for seg in wrap(ln, 12, w - 32, 2):
                s.append(t(x + 16, yy, "· " + seg, 12, INK2))
                yy += 17
        s.append(rect(x + 16, 288, w - 32, 28, "#f7fafc", LINE, 7, 1))
        s.append(t(x + 26, 307, ["整体状态", "整体状态", "整体状态 / 拒绝原因", "发货状态", "开票状态"][i], 11.5, INK2))
        x += w + 36
        if i < len(stages) - 1:
            s.append(arrow(x - 32, 235, x - 4, 235, color, 2.2))
            s.append(t(x - 40, 222, "参照", 11.5, MUTED))
    s.append(rect(60, 366, 1220, 96, TEAL_B, TEAL, 10))
    s.append(t(78, 394, "为什么要「参照」而不是重新录一张单？", 14, TEAL, weight="700"))
    for i, ln in enumerate(wrap("① 数据一致：数量、单价、条款从上游带入，避免重复录入出错；"
                                "② 可追溯：任何一张发票都能点回它的交货单与销售订单（原始凭证按钮）；"
                                "③ 状态联动：交货完成后订单行的交货状态更新，发票过账后开票状态更新——"
                                "状态就是「这单走到哪一步」的答案。", 12, 1180, 3)):
        s.append(t(78, 414 + i * 17, ln, 12, INK2))
    s.append(rect(60, 478, 600, 108, "#ffffff", AMBER, 10))
    s.append(t(78, 506, "修改与重新确定（再次理解一下）", 14, AMBER, weight="700"))
    for i, ln in enumerate(wrap("改了客户或物料后，系统会重新确定：物料确定、定价、税、可用性。\n"
                                "教材里改客户后会提示 Information: New pricing carried out（重新执行定价）。", 12, 560, 3)):
        s.append(t(78, 528 + i * 17, ln, 12, INK2))
    s.append(rect(680, 478, 600, 108, "#ffffff", RED, 10))
    s.append(t(698, 506, "不能跳步（最常见的错误）", 14, RED, weight="700"))
    for i, ln in enumerate(wrap("没有交货（或没做发货过账）就开不了票；没有库存就建不了交货（教材给的对策：MB1C 501 录入期初库存）。"
                                "顺序错了不是 Bug，是业务流程的顺序要求。", 12, 560, 3)):
        s.append(t(698, 528 + i * 17, ln, 12, INK2))
    s.append("</svg>\n")
    return "doc-flow.svg", "".join(s)


# --------------------------------------------------------------------------
# 7. 销售订单内部处理流程图（局部）
# --------------------------------------------------------------------------
def order_internal():
    W, H = 1340, 880
    s = [svg_open(W, H, "销售订单内部处理流程图")]
    s.append(title_bar(40, 48, W - 80, "销售订单的内部处理：一张图看懂「自动确定」",
                       "在 VA01 里你只输了几行信息，系统在后面做了这些事（本站自绘）"))
    blocks = [
        ("① 输入抬头", BLUE, ["订单类型（教材：OR 标准订单）", "售达方 / 送达方 / 收票方 / 付款方",
                              "订单日期、采购订单号（客户 PO）", "销售范围：从客户主数据带出"]),
        ("② 输入项目", BLUE, ["物料 + 数量 + 交货日期", "工厂（由物料主数据 / 装运条件推出）",
                              "价格从条件记录里「找」出来"], ),
        ("③ 自动确定", TEAL, ["项目类别（TAN 等）：订单类型 + 物料 → 决定是否定价/交货/开票",
                              "定价过程：销售范围 + 客户定价过程 + 单据定价过程 → 逐行算价",
                              "税分类 + 税码 → 销项税", "合作伙伴：从客户主数据带出售达方等角色"]),
        ("④ 检查", AMBER, ["可用性检查 ATP：确认交货日期（不足也能存单，除非设了块）",
                           "不完整性检查：必填字段没填就存不下（能存单但在单据流里标红）",
                           "信贷管理（若启用）：超额则自动加交货冻结"]),
        ("⑤ 保存与后效", GREEN, ["生成销售订单号，进入单据流", "需求传给 MRP / 计划（MD04 可见）",
                                 "输出确定：订单确认单可打印/发邮件", "状态字段更新，供 VA05 与后续环节使用"]),
    ]
    y = 116
    for title, color, lines in blocks:
        h = 58 + 12 * len(lines) + 16 * max(0, len(lines) - 2)
        h = 62 + len(lines) * 20
        s.append(rect(60, y, 700, h, "#ffffff", color, 10))
        s.append(rect(60, y, 4.5, h, color, color, rx=2))
        s.append(t(78, y + 28, title, 15.5, color, weight="700"))
        yy = y + 50
        for ln in lines:
            for seg in wrap(ln, 12, 660, 2):
                s.append(t(78, yy, "· " + seg, 12, INK2))
                yy += 17
        y += h + 12
    # 右侧：三个决定链（面板高度按内容算，避免大片空白或内容被截）
    AVAIL = 460

    def panel(y, title, bg, color, items, texts):
        chain_svg, ch = chain(818, y + 44, items, color, AVAIL) if items else ("", 6)
        ls = []
        for tx in texts:
            ls.extend(wrap(tx, 11.5, AVAIL, 4))
        h = 44 + ch + 8 + len(ls) * 17 + 10
        out = [rect(800, y, 500, h, bg, color, 11),
               t(818, y + 28, title, 14.5, color, weight="700"), chain_svg]
        yy = y + 44 + ch + 8 + 12
        for ln in ls:
            out.append(t(818, yy, ln, 11.5, INK2))
            yy += 17
        return "".join(out), h

    y = 116
    svg, h = panel(y, "决定链 1：项目类别（Item Category）", BLUE_L, BLUE,
                   ["销售凭证类型", "物料主数据（项目类别组）", "用途（用途字段）", "上层项目（空值也是键）"],
                   ["决定「这一行怎么处理」：要不要定价、要不要交货、要不要开票、库存从哪来（特别库存 E 等）。"
                    "教材工具：VOV4 / VOV7。"])
    s.append(svg)
    y += h + 16
    svg, h = panel(y, "决定链 2：定价过程（Pricing Procedure）", TEAL_B, TEAL,
                   ["销售范围", "客户定价过程", "单据定价过程"],
                   ["三个键定出唯一一套过程（教材用 RVAA01），过程里按步骤列出条件类型。"
                    "IMG：销售和分销 → 基本功能 → 定价 → 定价控制 → 定义并分配定价过程。"])
    s.append(svg)
    y += h + 16
    svg, h = panel(y, "决定链 3：账户确定（记账科目）", GREEN_B, GREEN, [],
                   ["发票过账时：账码（ERL 等，来自定价过程）+ 物料账户分配组 + 客户账户分配组 → 查表（VKOA）→ 收入科目。",
                    "所以「收入记到哪个科目」既不是写死在程序里，也不是手输的。"])
    s.append(svg)
    s.append("</svg>\n")
    return "order-internal.svg", "".join(s)


DIAGRAMS = [mindmap, org_structure, integration, pricing_chain, o2c_flow, doc_flow, order_internal]


def main():
    os.makedirs(OUT, exist_ok=True)
    files = []
    for fn in DIAGRAMS:
        name, svg = fn()
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        # XML 合法性
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            print("XML ERROR", name, e)
            return 1
        files.append((name, len(svg)))
    for n, sz in files:
        print("%-22s %6d bytes" % (n, sz))
    print("diagrams: %d" % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
