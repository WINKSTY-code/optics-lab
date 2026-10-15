# DESIGN.md — AI 光学交互实验室 v3 · 实验记录本

## Purpose
初中物理老师在教室电脑双击打开，10 个光学实验随点随用；学生操作产生学情，AI 学伴用苏科版教材语言引导；评审打开即看到"实验记录本"式的教学质感。

## Aesthetic Direction
**D 实验记录本 · Neo-Brutalist 教育版** — 纸黄坐标纸 + 纯黑硬边 + 荧光绿高亮，硬阴影"贴纸感"，像一本摊开的实验记录册。

## Design Dials
- variance: 6
- motion: 5（丰富版：按钮位移阴影 + 数字跳动 + 弹窗 staggered + 面板入场）
- density: 6

## Typography
- display: "Bricolage Grotesque"（jsdelivr fontsource，离线回退雅黑/PingFang）
- body: "Space Grotesk" + 中文回退
- mono/数据: 系统等宽（数字读数）

## Color Tokens（亮=纸黄默认 / dark=黑板模式）
| token | light | dark |
|---|---|---|
| --bg | #f6f1d8 坐标纸 | #0d0d0b 黑板 |
| --panel | #fffef2 | #161613 |
| --line | #17150e | #c8f04f |
| --accent | #c8f04f 荧光绿 | #c8f04f |
| --blue(数据) | #185fa5 | #8ec9ff |
| --red(诊断) | #c8331f | #ff8a70 |

## Motion Tokens
- --ease: cubic-bezier(.16,1,.3,1)
- 全部 ≤350ms；hover 位移阴影（按下实体感）；active 压平；focus-visible 蓝环
- 高光时刻：弹窗 staggered 逐项浮现 + 实验数字变化 popNum 跳动
- `prefers-reduced-motion: reduce` 全禁

## The One Thing
**所有卡片都是"贴在坐标纸上的实体卡片"**——hover 时贴纸被按下去，阴影收缩；标题带荧光绿错位印刷阴影。

## Forbidden（本项目特殊禁用）
- 不引入圆角渐变玻璃卡（与硬边语言冲突）
- 不动功能 JS：runE2E / KNOWLEDGE_BASE / 学生身份 / Socratic 全部原样
- emoji 按钮图标本轮保留（用户辨识习惯），后续可换 Lucide
