# -*- coding: utf-8 -*-
"""DOM 嵌套体检：用 HTMLParser 建父指针，校验关键结构不变量。
这一步就是上一轮漏掉的检查 —— 它本可以当场抓出「多加一个 </div> 把 .right 顶出 .stage」。
"""
import sys
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parent = {}          # id -> parent_id/label
        self.parent_cls = {}      # id -> parent 的 class/id 标记
        self.stack = []           # [(tag, label)]
        self.depth_max = 0
        self.errors = []
        self.section_parents = []

    def _label(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            return "#" + a["id"]
        if a.get("class"):
            return "." + a["class"].split()[0]
        return tag

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        a = dict(attrs)
        cur = self._label(tag, attrs)
        parent = self.stack[-1][1] if self.stack else "<root>"
        if a.get("id"):
            self.parent[a["id"]] = parent
            self.parent_cls[a["id"]] = self.stack[-1][0] if self.stack else "root"
        if tag == "section" and "panel" in (a.get("class") or ""):
            self.section_parents.append((a.get("id"), parent))
        self.stack.append((tag, cur))
        self.depth_max = max(self.depth_max, len(self.stack))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return
        self.errors.append("unmatched </%s>" % tag)


def load(path):
    src = open(path, "r", encoding="utf-8", newline="").read()
    # 只体检「<body> 起 → 第一个超大内联场景脚本之前」，前面全是普通标记，解析快且够用
    cut = src.find('window.__S3D_LENS__')
    if cut < 0:
        cut = len(src)
    head_end = src.find("<script")
    t = Tree()
    t.feed(src[:cut])
    return t


def report(path, tag):
    t = load(path)
    print("=== %s ===" % tag)
    bad = []
    # ① 每个 .panel 的直接父级都应是 .wrap
    for pid, par in t.section_parents:
        if par != ".wrap":
            bad.append("panel %s 的父级是 %s（应为 .wrap）" % (pid, par))
    print("  .panel 数量 %d，父级异常 %d 个" % (len(t.section_parents), len(bad)))
    # ② 关键 id 的父级
    for k in ("disp-rgb-ctrl", "disp-obj-ctrl", "disp-mode", "disp-light",
              "cv-disp", "verdict-disp", "dataBody" if False else "disp-dataBody"):
        print("    #%-16s → 父级 %s" % (k, t.parent.get(k, "<未找到>")))
    # ③ 未闭合栈
    print("  解析结束时未闭合标签 %d 个：%s" % (len(t.stack), [x[1] for x in t.stack][:8]))
    print("  未匹配收尾标签 %d 个" % len(t.errors))
    for e in t.errors[:5]:
        print("    " + e)
    print("  最大嵌套深度 %d" % t.depth_max)
    return bad, t


if __name__ == "__main__":
    for p, tg in [(r"C:/Users/Administrator/Desktop/AI光学参赛/光学交互实验室_AI_v6.4.8.html", "v6.4.8（基线）"),
                  (r"C:/Users/Administrator/Desktop/AI光学参赛/光学交互实验室_AI_v6.4.9.html", "v6.4.9（当前）")]:
        report(p, tg)
        print()
