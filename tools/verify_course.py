# -*- coding: utf-8 -*-
"""本站专用验证器（SAP SD 培训课程站）。

检查：
  ① 每页结构（DOCTYPE / 单 article / article 在 footer 之前 / 标签配平）
  ② 导航：各页 href 列表完全一致、恰好 1 个 active
  ③ 链接：站内 .html 与 #锚点 都能解析；每页 id 不重复
  ④ 资源：assets/img/…（真实截图）与 assets/diagrams/…（自绘图）都存在
  ⑤ 图注：figure.shot 必须有「画面」编号 + 来源串；figure.dia 必须有类型标签
  ⑥ 自测：30 题，data-answer 必须是某个选项的 data-key
  ⑦ 计数与 tools/hub_stats.json 一致
  ⑧ 文本卫生：无残留 Markdown（**…**）、无占位符 TODO/lorem
退出码 0 = PASS。
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "sitegen"))
import common  # noqa: E402

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"}
PAGES = [f for f, _l, _t in common.NAV]

errs, warns = [], []


def err(msg):
    errs.append(msg)


def warn(msg):
    warns.append(msg)


class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.bad, self.ids = [], [], []
        self.article_open = self.article_close = 0

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d:
            self.ids.append(d["id"])
        if tag == "article":
            self.article_open += 1
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "article":
            self.article_close += 1
        if tag in VOID:
            return
        if not self.stack:
            self.bad.append("多余的 </%s>" % tag)
            return
        if self.stack[-1] == tag:
            self.stack.pop()
        else:
            if tag in self.stack:
                while self.stack and self.stack[-1] != tag:
                    self.bad.append("</%s> 未闭合（期望 </%s>）" % (self.stack[-1], tag))
                    self.stack.pop()
                if self.stack:
                    self.stack.pop()
            else:
                self.bad.append("孤立的 </%s>" % tag)


def main():
    htmls = {}
    for f in PAGES:
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            err("缺页：%s" % f)
            continue
        htmls[f] = open(p, encoding="utf-8").read()
    if not htmls:
        print("RESULT: FAIL\n" + "\n".join(errs))
        return 1

    ids_by_page = {}
    for f, s in htmls.items():
        # ① 结构
        if not s.startswith("<!DOCTYPE html>"):
            err("%s: 缺 DOCTYPE" % f)
        for need in ("<html", "</html>", "<head>", "</head>", "<body>", "</body>", "<footer"):
            if need not in s:
                err("%s: 缺 %s" % (f, need))
        bp = Balance()
        bp.feed(s)
        ids_by_page[f] = bp.ids
        if bp.bad:
            err("%s: 标签问题 %s" % (f, "; ".join(bp.bad[:4])))
        if bp.stack:
            err("%s: 未闭合标签 %s" % (f, bp.stack[:6]))
        if bp.article_open != 1 or bp.article_close != 1:
            err("%s: article 开=%d 闭=%d（应为 1/1）" % (f, bp.article_open, bp.article_close))
        i_a, i_f = s.find("</article>"), s.find("<footer")
        if i_a < 0 or i_f < 0 or i_a > i_f:
            err("%s: </article> 不在 <footer> 之前" % f)
        dup = [x for x in set(ids_by_page[f]) if ids_by_page[f].count(x) > 1]
        if dup:
            err("%s: id 重复 %s" % (f, dup[:5]))

        # ② 导航
        nav = re.search(r'<nav class="main">(.*?)</nav>', s, re.S)
        if not nav:
            err("%s: 找不到 nav.main" % f)
        else:
            hrefs = re.findall(r'href="([^"]+)"', nav.group(1))
            act = re.findall(r'<a class="active" href="([^"]+)"', nav.group(1))
            htmls[f] = (s, hrefs, act)

    nav_ref = None
    for f, v in htmls.items():
        if isinstance(v, tuple):
            s, hrefs, act = v
            htmls[f] = s
            if nav_ref is None:
                nav_ref = (f, hrefs)
            elif hrefs != nav_ref[1]:
                err("%s: 导航与 %s 不一致" % (f, nav_ref[0]))
            if len(act) != 1:
                err("%s: active 数量=%d（应为 1）" % (f, len(act)))
            elif act[0] != f:
                err("%s: active 指向 %s" % (f, act[0]))

    # ③④⑤ 链接与资源与图注
    shot_refs, dia_refs = [], []
    for f, s in htmls.items():
        for href in re.findall(r'href="([^"]+)"', s):
            if href.startswith(("http", "mailto", "#")):
                if href.startswith("#"):
                    if href[1:] not in ids_by_page.get(f, []):
                        err("%s: 页内锚点 %s 不存在" % (f, href))
                continue
            target, _, anchor = href.partition("#")
            if target.endswith(".html"):
                if target not in htmls:
                    err("%s: 死链 %s" % (f, target))
                elif anchor and anchor not in ids_by_page.get(target, []):
                    err("%s: 锚点 %s 在 %s 中不存在" % (f, anchor, target))
            elif not os.path.exists(os.path.join(ROOT, target)):
                err("%s: 缺失文件 %s" % (f, target))
        for src in re.findall(r'src="(assets/(?:img|diagrams)/[^"]+)"', s):
            if not os.path.exists(os.path.join(ROOT, src)):
                err("%s: 缺失图片 %s" % (f, src))
            (dia_refs if "/diagrams/" in src else shot_refs).append((f, src))
        for m in re.finditer(r'<figure class="shot[^"]*">(.*?)</figure>', s, re.S):
            blk = m.group(1)
            if "figcaption" not in blk:
                err("%s: figure.shot 缺 figcaption" % f)
            elif "<span class=\"n\">画面" not in blk:
                err("%s: figure.shot 缺「画面」编号" % f)
            if "<span class=\"src\">" not in blk:
                err("%s: figure.shot 缺来源标注" % f)
            if "alt=" not in blk:
                err("%s: 图片缺 alt" % f)
        for m in re.finditer(r'<figure class="dia">(.*?)</figure>', s, re.S):
            blk = m.group(1)
            for need, label in (('class="n"', "类型标签"), ('class="src"', "自绘标注"), ("alt=", "alt")):
                if need not in blk:
                    err("%s: figure.dia 缺 %s" % (f, label))

    # ⑥ 自测（按 quiz-q 分块，不看嵌套 div）
    qhtml = htmls.get("quiz.html", "")
    blocks = qhtml.split('<div class="quiz-q"')[1:]
    qs = []
    for blk in blocks:
        m = re.match(r' data-answer="([A-D])"', blk)
        if not m:
            err("quiz.html: 有一题的 data-answer 不是 A~D")
            continue
        qs.append((m.group(1), blk))
    if len(qs) != 30:
        err("quiz.html: 题目数 %d（应为 30）" % len(qs))
    for ans, blk in qs:
        blk = blk.split('<div class="quiz-q"')[0]
        keys = re.findall(r'<div class="opt" data-key="([A-D])">', blk)
        if keys != ["A", "B", "C", "D"]:
            err("quiz.html: 某题选项键为 %s" % keys)
        if 'class="explain"' not in blk:
            err("quiz.html: 某题缺解说")
        if ans not in keys:
            err("quiz.html: 正确答案 %s 不在选项里" % ans)

    # ⑦ 计数
    n_shot = sum(1 for _ in shot_refs)
    n_uniq = len(set(x[1] for x in shot_refs))
    n_dia = len(set(x[1] for x in dia_refs))
    hub = json.load(open(os.path.join(ROOT, "tools", "hub_stats.json"), encoding="utf-8"))
    if hub["n_pages"] != len(htmls):
        err("hub_stats.n_pages=%s 与页数 %d 不一致" % (hub["n_pages"], len(htmls)))
    if hub["figs"] != n_shot:
        err("hub_stats.figs=%s 与截图引用 %d 不一致" % (hub["figs"], n_shot))

    # ⑧ 文本卫生
    for f, s in htmls.items():
        for pat, why in ((r"\*\*[^*\n]{2,}\*\*", "残留 Markdown 粗体"),
                         (r"lorem ipsum", "占位文本"),
                         (r"TODO|FIXME", "TODO 标记"),
                         (r"\{[a-z_]+\}", "未替换的模板变量")):
            for m in re.finditer(pat, s, re.I):
                err("%s: %s → %r" % (f, why, s[max(0, m.start() - 30):m.end() + 20]))

    # 报告
    on_disk = len([1 for r, _d, fs in os.walk(os.path.join(ROOT, "assets", "img")) for _x in fs])
    print("pages=%d  figure.shot=%d（去重 %d / 磁盘 %d）  figure.dia=%d（去重 %d）  quiz=%d"
          % (len(htmls), n_shot, n_uniq, on_disk, len(dia_refs), n_dia, len(qs)))
    for w in warns:
        print("WARN:", w)
    if errs:
        print("RESULT: FAIL (%d)" % len(errs))
        for e in errs[:40]:
            print("  -", e)
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
