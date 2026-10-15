# -*- coding: utf-8 -*-
"""v6.4.13 补丁二：凹透镜②号特殊光线画法更正（画布 + 三语判定文案 + 日志/角标）"""
import io, os

F = r"C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v6.4.13.html"
with io.open(F, "r", encoding="utf-8") as f:
    s = f.read()

def patch(name, old, new):
    global s
    n = s.count(old)
    assert n == 1, "[%s] 匹配 %d 处（应为 1）" % (name, n)
    s = s.replace(old, new, 1)
    print("[OK] %s" % name)

# ---------- L1 红②画法 ----------
old = """    // ② 过焦点
    if(r2){
      const dx = Fx - 20, dy = LENS_Y - inY2;
      const t = (LENS_X - 20) / dx;
      const yHit = inY2 + dy * t;
      lineSeg2(ctx, 20, inY2, LENS_X, yHit, ray2C, 2.2, false, true);
      lineSeg2(ctx, LENS_X, yHit, W - 20, yHit, ray2C, 2.2, false, true);
      labelAt(ctx, 22, inY2 - 8, '②过焦点', ray2C, 12);
    }"""
new = """    // ② 过焦点（凸透镜）/ 正对异侧虚焦点（凹透镜）★ V6.4.13 更正凹透镜画法
    if(r2){
      if(convex){
        const dx = Fx - 20, dy = LENS_Y - inY2;
        const t = (LENS_X - 20) / dx;
        const yHit = inY2 + dy * t;
        lineSeg2(ctx, 20, inY2, LENS_X, yHit, ray2C, 2.2, false, true);
        lineSeg2(ctx, LENS_X, yHit, W - 20, yHit, ray2C, 2.2, false, true);
      } else {
        /* 凹透镜：入射光线的【延长线】过异侧（右）虚焦点 F′，折射后平行于主光轴射出。
           旧实现沿用凸透镜的画法，让入射光先穿过入射侧虚焦点 F 再打在透镜上——
           虚焦点处并无光线真实通过；按薄透镜公式 u'=u+h/f 该出射也不平行，几何不成立。 */
        const dx = Fpx - 20, dy = LENS_Y - inY2;
        const t = (LENS_X - 20) / dx;
        const yHit = inY2 + dy * t;
        lineSeg2(ctx, 20, inY2, LENS_X, yHit, ray2C, 2.2, false, true);      /* 入射：止于透镜 */
        lineSeg2(ctx, LENS_X, yHit, Fpx, LENS_Y, ray2C, 1.5, true, false);   /* 延长线（虚线）过 F′ */
        lineSeg2(ctx, LENS_X, yHit, W - 20, yHit, ray2C, 2.2, false, true);  /* 出射：平行主光轴 */
      }
      labelAt(ctx, 22, inY2 - 8, convex ? '②过焦点' : '②正对异侧虚焦点', ray2C, 12);
    }"""
patch("L1 红②画法", old, new)

# ---------- L2 判定文案（三语，F/F′ 侧别更正） ----------
patch("L2 zh", "反向延长线交于虚焦点 F′；② 指向虚焦点 F 的光线折射后",
               "反向延长线交于入射侧虚焦点 F；② 指向异侧虚焦点 F′ 的光线折射后")
patch("L2 zht", "反向延長線交於虛焦點 F′；② 指向虛焦點 F 的光線折射後",
                "反向延長線交於入射側虛焦點 F；② 指向異側虛焦點 F′ 的光線折射後")
patch("L2 en", "their backward extensions meet the virtual focus F′; ② a ray aimed at F emerges",
               "their backward extensions meet the near-side virtual focus F; ② a ray aimed at the far-side virtual focus F′ emerges")

# ---------- L3 更新日志 ----------
patch("L3 更新日志", "修复切页回来后3D全屏按钮失效，唤醒即恢复渲染状态。",
                     "修复切页回来后3D全屏按钮失效；更正凹透镜②号特殊光线画法。")

# ---------- L4 版本角标 title ----------
patch("L4 角标title", "（唤醒时恢复渲染标记，回收重挂后自动补发参数）。\">v6.4.13</div>",
                      "（唤醒时恢复渲染标记，回收重挂后自动补发参数）；更正凹透镜②号特殊光线：正对异侧虚焦点入射、平行出射。\">v6.4.13</div>")

with io.open(F, "w", encoding="utf-8", newline="") as f:
    f.write(s)
print("已写回:", F, os.path.getsize(F), "bytes")
