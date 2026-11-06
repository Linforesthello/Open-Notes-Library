# resume-two-col.css 启用与导出说明（本地保留）

> 创建: 2026-08-23 ｜ 适用: 两份**重排版**简历（核心能力前置版）
> 配套文件: [resume-two-col.css](resume-two-col.css) ｜ 原样式 [resume.css](../../../Desktop/Open_Notes_Library/01-开发日志/个人发展与学习丨20250910/个人简历/resume.css)
> 导出链路: VSCode `Markdown PDF` 插件（template.html + markdown.css + 自定义 css）→ Chromium printToPDF

---

## 一、这个 CSS 解决什么

重排版把「核心能力」做成 5 行特征词索引，但**默认样式下每行会折成 2 行**，索引的"一眼看完"效果就没了。本样式做四件事：

| 目标 | 实现 |
|:--|:--|
| 核心能力 5 行**不折行** | `h2 + ul li { white-space: nowrap; font-size: 9.5pt; line-height: 1.25 }` |
| 全文段距压紧（省页面高度） | `body line-height 1.45 → 1.35`；`p` 2px→1.5px；`li` 1.5px→1.2px；`h2` margin 10px→9px；`ul/ol` 底距 6px→5px |
| 末尾技能特长紧凑分类 | 类别标签 `li > strong:first-child { white-space: nowrap }`，标签不单独占行 |
| 分页保护 | `h2/h3 { break-after: avoid }`（标题不孤立成页尾）；`li { break-inside: avoid }`（单条不跨页断开） |

> ⚠️ **注意作用域**：`h2 + ul li` 用的是"紧邻 h2 的列表"选择器。它命中的是「## 核心能力」下的那 5 行——因为核心能力是文档里**唯一**紧跟 h2 的列表。项目内的 bullet 都挂在 `###`(h3) 之下，不受影响。这也是为什么没去改 md 结构。

## 二、启用（3 步）

1. **确认路径平台**（最容易踩的坑）：
   - 若在 **Windows** 导出：CSS 路径形如 `C:\Users\86173\Documents\deepseek-harness\default-workspace\简历修订_20260823\resume-two-col.css`
   - 若在 **Linux** 导出（原 `简历导出指南.md` 记录的环境）：需先把本 CSS 复制过去，路径形如 `/home/lin/Lin_note/.../个人简历/resume-two-col.css`
   - JSON 里 Windows 路径的反斜杠要转义：`"C:\\Users\\..."`；或直接用正斜杠 `"C:/Users/..."`（JSON 与 Chromium 都接受）

2. **改 settings.json**（设置 → 扩展 → Markdown PDF → Styles）：
   ```json
   "markdown-pdf.styles": ["<resume-two-col.css 的绝对路径>"]
   ```
   - 想**保留原样式**做对照：两个都列，本文件放后面（后加载者覆盖前面的同名规则）
     ```json
     "markdown-pdf.styles": ["<resume.css 路径>", "<resume-two-col.css 路径>"]
     ```
   - ⚠️ 本项目记录过：GUI 修改会写入**当前激活的 profile**（当时是「主力-嵌软」`profiles/532aae18/settings.json`），改完没反应先查这个。

3. **导出**：VSCode 打开重排版 md → `Ctrl+Shift+P` → `Markdown PDF: Export (settings.json)` → 同目录生成同名 PDF。

## 三、导出后自己看三件事（不需要我验证）

1. **核心能力是不是 5 行**——有没有哪一行折成两行。若折行：把 `h2 + ul li` 的 `font-size` 从 9.5pt 降到 9pt，或把该行里最长的标签删一个。
2. **总页数**——原网申版是 2 页 A4。重排版内容更多（补了低物链、SLAM 四方案、传感器加装），可能到 2 页半或 3 页。超了就启用 CSS 末尾那段**兜底压缩档**（注释掉 `/* ... */` 即可）：`9.5pt / line-height 1.28`。
3. **末尾技能特长没被截断**——9 类必须完整出现在最后。

## 四、调参顺序（越往后越伤观感）

`字距(letter-spacing)` → `line-height` → `li/p margin` → `h2/h3 margin` → 页面 margin（settings.json，当前 10mm，最小建议 6mm）

## 五、回滚

把 `markdown-pdf.styles` 改回指向原 `resume.css` 即可；本文件不修改任何原文件，是独立新增。

## 六、两套样式怎么选

| 样式 | 配哪份 md | 说明 |
|:--|:--|:--|
| `resume.css`（原） | 网申版（教育背景在前，技能在末尾） | 已经是紧凑版，继续用 |
| `resume-two-col.css`（本文件） | **重排版**（核心能力 5 行索引 + 教育后移） | 专为索引块不折行设计 |

> 注意：`resume-two-col.css` **不要**用于网申版。网申版没有「核心能力」区块，`h2 + ul li` 会命中「## 获奖经历」下的第一条（无列表，不触发）或「## 技能特长」后的列表（会把它也压成 nowrap，反而可能溢出）。**一个样式配一套结构**。

## 七、未做验证的如实说明

本 CSS **未经实际渲染验证**（未跑 Chromium/PDF）。判断依据是内容宽度估算：A4 去 10mm 边距后可用约 190mm，9.5pt 下约容 68 个中文字符，而核心能力最长一行（规划版第 3 行）约 44 个字符宽，理论不折行。

**但这只是估算**——必须靠你在 VSCode 里导出 PDF 预览确认那 5 行。若折行，按 §三 第 1 条降字号即可。
