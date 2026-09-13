# -*- coding: utf-8 -*-
"""SAP SD 培训课程站 — 公共骨架与组件（从共享设计系统 style.css 复用，只追加不覆盖）。

设计原则与其他培训站一致：
  - 纯静态 HTML，无外部依赖，file:// 直接可开
  - 真实截图来自教材文档（原文件名保留在 figcaption，可回查 Word 原稿）
  - 生成的图（流程图/结构图/思维导图）在 assets/diagrams/*.svg，页面上明确标注「自绘」
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

# --------------------------------------------------------------------------
# 站点元信息
# --------------------------------------------------------------------------
SITE = {
    "title": "SAP SD 培训课程",
    "subtitle": "销售与分销：从概念到流程、从总体到局部",
    "brand_logo": "SD",
    "brand_txt": "培训课程",
    "desc": "SAP SD（销售与分销）培训课程：概念 → 组织结构 → 主数据 → 定价 → 端到端流程（询价·报价·订单·交货·发货·开票·收款）→ 配置 → 分析。"
            "每个环节配真实的 SAP GUI 系统截图（中文界面）与自绘的流程图、结构图、思维导图。",
}

# 导航（顺序 = 教学顺序：概念 → 总体 → 局部 → 后台 → 实训）
NAV = [
    ("index.html", "首页", "课程地图与学习路线"),
    ("concept.html", "概念", "SD 是什么、三大概念层、五大单据"),
    ("org.html", "组织", "企业结构 / 销售结构 / 装运结构"),
    ("master.html", "主数据", "客户主数据 / 物料销售视图 / 条件记录"),
    ("pricing.html", "定价", "条件技术四要素与定价过程确定"),
    ("flow.html", "流程", "端到端 O2C 流程图与单据流"),
    ("order.html", "订单", "询价 · 报价 · 销售订单（局部详解）"),
    ("delivery.html", "交货", "外向交货 · 拣配 · 发货过账"),
    ("billing.html", "开票", "发票 · 过账到 FI · 收款"),
    ("analysis.html", "分析", "单据流 / 订单清单 / 销售分析"),
    ("config.html", "配置", "SPRO 配置路线（48 个任务）"),
    ("practice.html", "实训", "动手任务与完成基准"),
    ("instructor.html", "讲师", "采分点 / 必问 / 答案"),
    ("worksheet.html", "学员", "记入表（可打印）"),
    ("quiz.html", "自测", "30 题自评（合格 75%）"),
    ("glossary.html", "术语", "中英对照 / T-code 速查"),
]

IMG_MANIFEST = json.load(open(os.path.join(ROOT, "work", "img_manifest.json"), encoding="utf-8"))
CAPTURE = {
    "sd": "教材《S4.docx》SD 模块",
    "prep": "教材《S4.docx》准备章",
}

# 教材原文的 48 个 SD 任务（标题 / IMG 路径 / 手顺 / 截图）—— 页面里的路径与截图都从这里取，
# 避免手抄文件名抄错，也保证「站上写的路径 = 教材里的路径」。
SD_SOURCE = json.load(open(os.path.join(ROOT, "work", "sd_source.json"), encoding="utf-8"))
TASK = {t["no"]: t for t in SD_SOURCE}


def simg(task, step=1, k=0):
    """取教材第 task 个任务、第 step 步、第 k 张截图的路径；没有则返回 None。"""
    steps = TASK[task]["steps"]
    if not steps:
        return None
    imgs = steps[min(step, len(steps)) - 1].get("imgs") or []
    if not imgs:
        return None
    return imgs[min(k, len(imgs) - 1)]


def scap(task, step=1):
    steps = TASK[task]["steps"]
    if not steps:
        return ""
    return steps[min(step, len(steps)) - 1].get("caption", "")


def spath(task):
    return TASK[task].get("path") or ""


def stc(task):
    return TASK[task].get("tcodes") or []


def src_ref(task):
    return "教材《S4.docx》· SD 任务 %02d %s" % (task, TASK[task]["title"])


# --------------------------------------------------------------------------
# 小组件
# --------------------------------------------------------------------------
def esc(s):
    return html.escape(str(s), quote=False)


def href(file, anchor=None):
    return file + ("#" + anchor if anchor else "")


def _img_attrs(path):
    m = IMG_MANIFEST.get(path)
    if not m:
        raise KeyError("截图不在 manifest 中（assets/img/%s）" % path)
    return m["w"], m["h"], m["orig"]


def shot(path, no=None, cap="", src="", cls="", alt=None):
    """真实系统截图（教材文档原图）。path 相对 assets/img/。"""
    w, h, orig = _img_attrs(path)
    cap = cap or ""
    tag = "画面 %s" % no if no else "画面"
    srctxt = src or ("%s · %s" % (CAPTURE.get(path.split("/")[0], "教材"), orig))
    narrow = " narrow" if h <= 160 else ""
    return (
        '<figure class="shot%s%s">'
        '<a class="zoom" href="assets/img/%s" title="点击放大（1×~4×，ESC 关闭）">'
        '<img src="assets/img/%s" width="%d" height="%d" alt="%s" loading="lazy"></a>'
        '<figcaption><span class="n">%s</span><span class="cap">%s</span>'
        '<span class="src">%s</span></figcaption></figure>'
    ) % (narrow, (" " + cls if cls else ""), path, path, w, h,
         esc(alt or cap or "SAP GUI 实机截图"), tag, cap, srctxt)


def shot_grid(items, cls=""):
    """items = [(path, cap, no)] -> 并排小图，适合连续画面。"""
    inner = "".join(shot(p, no=n, cap=c) for p, c, n in items)
    return '<div class="shot-grid%s">%s</div>' % (" " + cls if cls else "", inner)


def diagram(name, alt, cap="", kind="流程图"):
    return (
        '<figure class="dia"><a class="zoom" href="assets/diagrams/%s.svg">'
        '<img src="assets/diagrams/%s.svg" alt="%s" loading="lazy"></a>'
        '<figcaption><span class="n">%s</span><span class="cap">%s</span>'
        '<span class="src">本站自绘 SVG</span></figcaption></figure>'
    ) % (name, name, esc(alt), kind, cap)


def note(kind, title, text):
    return '<div class="note %s"><span class="t">%s</span>%s</div>' % (kind, esc(title), text)


def box(kind, title, inner):
    return '<div class="box %s"><b class="t">%s</b>%s</div>' % (kind, esc(title), inner)


def pathline(label, path, copyable=True):
    attr = ' data-copy="%s"' % esc(path) if copyable else ""
    return '<div class="pathline"%s><b>%s</b>%s</div>' % (attr, esc(label), esc(path))


def tbl(headers, rows, cls="tbl", first_mono=False, row_attrs=None, tid=None):
    th = "".join("<th>%s</th>" % h for h in headers)
    trs = []
    for i, r in enumerate(rows):
        tds = []
        for c in r:
            if isinstance(c, tuple):
                c, klass = c
            else:
                klass = ""
            tds.append('<td%s>%s</td>' % (' class="%s"' % klass if klass else "", c))
        ra = ""
        if row_attrs is not None and i < len(row_attrs) and row_attrs[i]:
            ra = " " + row_attrs[i]
        trs.append("<tr%s>%s</tr>" % (ra, "".join(tds)))
    klass = cls + (" idx" if first_mono else "")
    idattr = ' id="%s"' % tid if tid else ""
    return ('<div class="tblwrap"><table class="%s"%s><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table></div>') % (klass, idattr, th, "".join(trs))


def oplist(items, start=1):
    """items = [(html, kind)] ; kind in ''|note"""
    lis = []
    for it in items:
        if isinstance(it, tuple):
            txt, kind = it
        else:
            txt, kind = it, ""
        lis.append('<li class="%s">%s</li>' % ("is-note" if kind == "note" else "", txt))
    return '<ol class="oplist" start="%d">%s</ol>' % (start, "".join(lis))


def steps_list(items):
    return '<ol class="steps">%s</ol>' % "".join("<li>%s</li>" % x for x in items)


def steph(no, title, tags=None, anchor=None):
    t = "".join('<span class="%s">%s</span>' % (k, esc(v)) for k, v in (tags or []))
    return '<div class="steph" id="%s"><span class="no">%s</span><h3>%s</h3>%s</div>' % (
        anchor or ("s" + str(no)), esc(no), esc(title), t)


def toc(items):
    return '<div class="toc">%s</div>' % "".join(
        '<a href="#%s">%s</a>' % (a, esc(t)) for t, a in items)


def cards(items):
    inner = "".join('<div class="card"><b>%s</b><span>%s</span></div>' % (b, s) for b, s in items)
    return '<div class="grid cards">%s</div>' % inner


def stat_cards(items):
    """[(数字, 单位, 说明)] -> 三栏统计卡"""
    inner = ""
    for n, unit, desc in items:
        inner += '<div class="card"><b>%s</b><span>%s</span><small>%s</small></div>' % (n, unit, desc)
    return '<div class="grid cards stats">%s</div>' % inner


# --------------------------------------------------------------------------
# 页面骨架（完整文档骨架，避免「拼装丢 skeleton」的老问题）
# --------------------------------------------------------------------------
def nav_html(active):
    out = []
    for f, label, _tip in NAV:
        cls = ' class="active"' if f == active else ""
        out.append('<a%s href="%s" title="%s">%s</a>' % (cls, f, esc(_tip), esc(label)))
    return "\n      ".join(out)


def shell(file, title, kicker, body, desc=None):
    desc = desc or SITE["desc"]
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%(title)s · %(stitle)s</title>
<meta name="description" content="%(desc)s">
<link rel="stylesheet" href="assets/style.css">
<link rel="stylesheet" href="assets/sd.css">
</head>
<body>
<header class="site">
  <div class="nav-wrap">
    <a class="brand" href="index.html"><span class="logo">%(logo)s</span><span class="txt">%(btxt)s</span></a>
    <nav class="main">
      %(nav)s
    </nav>
  </div>
</header>

<div class="wrap">
<main class="page">
<article>
%(body)s
</article>
</main>
</div>

<footer class="site">
  <div class="inner">
    <div class="cols">
      <div>
        <h5>SAP SD 培训课程</h5>
        <p>销售与分销 · 从概念到流程 · 从总体到局部</p>
      </div>
      <div>
        <h5>课程板块</h5>
        <p><a href="concept.html">概念</a> · <a href="org.html">组织</a> · <a href="master.html">主数据</a> ·
        <a href="pricing.html">定价</a> · <a href="flow.html">流程</a> · <a href="config.html">配置</a></p>
      </div>
      <div>
        <h5>课堂配套</h5>
        <p><a href="practice.html">实训任务</a> · <a href="instructor.html">讲师版</a> ·
        <a href="worksheet.html">学员版</a> · <a href="quiz.html">自测</a> ·
        <a href="glossary.html">术语表</a></p>
      </div>
      <div>
        <h5>一句话免责</h5>
        <p>截图取自教材文档的真实 SAP GUI 画面（中文界面）；图与表为本站自绘。
        标准值随版本/行业方案而异，页面标注的确认方法请在自己的系统里核对。</p>
      </div>
    </div>
    <p class="copy">© <span data-year>2026</span> SAP SD 培训课程 · 静态站点，可离线使用</p>
  </div>
</footer>
<script src="assets/main.js"></script>
<script src="assets/quiz.js"></script>
<script src="assets/sd.js"></script>
</body>
</html>
""" % {"title": esc(title), "stitle": SITE["title"], "desc": esc(desc),
       "logo": SITE["brand_logo"], "btxt": SITE["brand_txt"],
       "nav": nav_html(file), "body": body}
