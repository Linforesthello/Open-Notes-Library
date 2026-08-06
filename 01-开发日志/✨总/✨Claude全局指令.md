# 全局工作偏好

## 文档规范（每次修改文档前先读）

@/home/lin/Lin_workspace/r2_integration/doc/standards.md

## Obsidian 文档同步

R2 项目文档在 Obsidian 库有镜像副本（普通文件复制，非链接），修改工作区文档后同步：

- 权威源：`~/Lin_workspace/r2_integration/doc/`（只在此处修改）
- 镜像：`~/Lin_note/Open-Notes-Library/01-开发日志/✨总/当前项目文档/R2_Integration/doc/`
- 方式：单向 `cp` 覆盖 + `diff -q` 确认一致；不删除 Obsidian 侧独有文件
- 已知 Obsidian 侧独有文件（暂不处理）：`phase1/ekf-config.yaml`、`phase1/g354-completion.md`、`phase1/g354-debug-log.md`、根级 `vlp16_slam_exploration.md`

## 疑难问题排查：先搜索，后推理

! 遇到难以解决的问题（事实不确定、报错原因不明、陌生工具/API、信息可能过时等），
  先做网页搜索（WebSearch/WebFetch），用搜索结果核实后再自行推理；不得凭猜测直接下结论
- 搜索范围优先级：Google（搜索引擎）→ 官方文档/技术社区/论坛
  （如 Stack Overflow、GitHub Issues、CSDN）→ 个人网站/博客
- 搜索结果不足以定论时，基于结果推理并标注不确定点，不得编造来源或细节

## 操作执行方式：先问再做，给用户动手空间

! 执行有实际影响的操作前（命令行、git 操作、文件修改、硬件调试等），先询问用户：
  由 AI 直接执行，还是由 AI 给出「操作指令 + 预期现象/验证方法」让用户亲手操作
- 原因：全程代劳会剥夺用户动手排障的收获；学习性操作优先考虑交给用户动手
- 纯查询/读取（读文件、查状态、搜索信息）不受此限，不必询问
- 同一任务的连续小操作归并成一次询问，不逐条打断
