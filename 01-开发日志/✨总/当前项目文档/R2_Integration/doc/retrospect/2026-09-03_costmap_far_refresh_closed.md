# 问题①「costmap 远端不刷新」疑点结案 + 低物高度盲区细化（09-03 实车复录）

> 日期：2026-09-03（疑点始于 08-25 W3 避障）
> 任务：minimal-loop2 A1（W3 避障验收）问题① 排查的实车最终判据——远距离（1~5m）三层同框复录
> 关联：[costmap_experiment.md](../minimal-loop2/costmap_experiment.md)（08-25 独立实验，遗留 #2 = 本次执行项）、
> [relog-operation.md](../minimal-loop2/relog-operation.md)（复录操作卡）、
> [raw_relog_0903_observations_2026-09-03_2120.txt](../raw_data/raw_relog_0903_observations_2026-09-03_2120.txt)（现场原始记录）
> 状态：✅ 问题① costmap 侧排除（结案）；低物盲区断点定位待 bag 三层分析收尾

---

## 一、排查链条回顾

| 时间 | 事件 | 结论 |
|:---|:---|:---|
| 08-25 | W3 避障 3 bag（1357/1401/1405）疑「costmap 远端不刷新」，但**漏录 /velodyne_points 与 costmap 系列**（核心证据缺失） | 按 ros2-ops §9 先验原则 → 重录（核心输入缺失不补偿） |
| 08-25 | 单节点 costmap 独立实验（costmap_experiment.md） | lifecycle 未激活假象排除 + mark 管线正常；**远距离（>1m）判据未完成**（pub 异常）→ 遗留 #2 |
| 09-03 | relog_0903_2104：实车静止 + 高箱 1m/2m/4m/4.5-5m 逐段摆放，全话题录制 283s（points/scan/costmap_raw 三层同框） | **本次结案文档** |

## 二、09-03 现场结论（三层判据 → 问题① 结案）

> 现场原始观察与 scp 记录见 [raw_data 文件](../raw_data/raw_relog_0903_observations_2026-09-03_2120.txt)（第四/五节含录后自测补充）

| # | 实测项 | 结果 | 判定 |
|:--|:---|:---|:---|
| 1 | 近端 mark（1m / 2m） | 黑格正常出现，位置精确对应箱子 | ✅ |
| 2 | **远端 mark（4m / 4.5-5m）** | **黑格正常出现、正常刷新**（场地不足 6m，5m+ 仍可作用） | ✅ **问题①最终判据** |
| 3 | 多障碍同场 | 两个不同位置物体同时可识别 | ✅ |
| 4 | 移走清除 | 黑格消失（clearing 正常）；黑格周围灰圈 = inflation（正常） | ✅ |

**问题① 结案判定（对应 costmap_experiment.md §3.5 预设分支）**：

> **远端 mark 正常 → costmap 侧（感知/转换/mark 管线）排除**，问题①归入「显示层/MPPI 前瞻」——
> 与问题②同根因链（MPPI 空间前瞻 48步×0.04s×0.2m/s ≈ 0.38m + footprint 前缘 0.42m，见 costmap_experiment.md 结论②）。

⚠️ 备注：costmap 侧排除为**实测结论**；「归 MPPI 前瞻/显示层」为该分支预设的**推断**（relog 未直接测 MPPI）。
W3 当时「远处无黑格」为何未复现，候选解释（按可能性，待对账 W3 bag）：
a) W3 障碍可能是**低物/矮物**（见 §三 高度盲区）；b) W3 时 lifecycle/状态类假象（08-25 实验教训）；c) 显示层/MPPI 视角。
→ 对账项：W3 bag 1357/1401/1405 远障碍在 costmap_raw 是否真有 254/100（待分析，见 §五）。

## 三、新发现 1：低物高度盲区（与「距离」无关）

- **现象**：与雷达水平光面**平高的物体全部正常出现**；**低于雷达水平面的物体，无论多近多远（高度不够）一律不出现在黑格**
- 性质：不是距离问题（1~5m 全程正常），是**高度/线束层面**的盲区
- 配置线索（待坐实）：velodyne_laserscan 参数 `ring: -1`；VLP-16 **无 0° 环**（偶数环向下 −1°~−15°、奇数环向上 +1°~+15°，见 VLP16db.yaml vert_correction）——
  /scan 若只含近水平线束（≈−1° 环），则低于该线束扫掠面的物体在 /scan 与 costmap 层面**结构性不可见**
- 与 costmap_experiment.md 结论③的关系：③ 原定论「低矮障碍扫不到 = 雷达高度/角分辨率物理盲区（已定论）」**需要细化**——
  盲区断点若在「/velodyne_points 有数据、/scan 无」（转换层线束选择），则③的"物理盲区"表述不准确，修法不同（多环/下俯环 vs 加低雷达）。**断点位置 = bag 三层分析收尾项（§五）**

## 四、新发现 2：打滑后地图不匹配（录后自测，边界行为）

- **现象**：静态绕行 / 多障碍绕行 / 寻路均正常；**车体严重打滑（运动中被人为搬运）后 rviz2 地图出现不匹配**
- 判读（勿当定论）：人为搬运 = 轮速里程计无法感知的外力运动 → odom 预测失真 → AMCL 定位被带偏 → 地图/点云错位；
  与 [08-17 初始位姿/膨胀修复](2026-08-17_nav2_initialpose_inflation_fix.md) 的「map 重叠」教训同源（定位一致性边界）
- 应对现状：操作纪律已有（搬运后重设初始位姿等）；系统级恢复（AMCL 自行收敛）未验证——**记录不实施**（09-10 收手线语义，后置）

## 五、收尾待办

| # | 项 | 内容 | 状态 |
|:--|:---|:---|:---|
| 1 | bag 三层断点分析 | relog_0903_2104（VM `~/Lin_workspace/bags/raw/`）：① 验证 1-5m 各段 points/scan/costmap_raw 三层同框数据齐全；② **低物时刻断点坐实**（低物在 /velodyne_points 有环数据但 /scan 无 = 转换层；points 也无 = 雷达物理）；③ 复核 /scan 实际所用线束（ring 语义 + 实测） | ☐ 待跑 |
| 2 | W3 bag 对账 | 08-25 三 bag（1357/1401/1405）：远障碍在 costmap_raw 有无 254/100（验证 §二 候选解释 a/b/c） | ☐ 待跑 |
| 3 | 低物盲区修法决策 | 多环 scan / 下俯环 / 加低处雷达 —— **后置**（09-10 前不实施，阶段二候选） | ☐ 后置 |
| 4 | 文档联动 | costmap_experiment.md 状态更新（本次已做）｜ 07-handover 状态同步（滞后 08-25 起，建议 A1 收尾时统一） | ☐ 部分完成 |

## 六、结论速览（一页版）

1. **问题①结案**：costmap 远端不刷新 = **排除**——远端 mark 链路正常（1~5m 实车实测通过）
2. **低物高度盲区** = 真实系统边界（距离无关、高度门槛），断点层待 bag 收尾坐实；是否修 = 阶段二决策
3. **打滑后地图不匹配** = odom/AMCL 一致性边界行为（08-17 同源），记录不实施
4. A1 判据不受影响：判据障碍口径 ≥0.3m³ 高箱（与雷达平高），本次实测恰证明该口径下 costmap 完全可靠

## 相关文件

- 现场记录：[raw_relog_0903_observations_2026-09-03_2120.txt](../raw_data/raw_relog_0903_observations_2026-09-03_2120.txt)
- 实验文档：[costmap_experiment.md](../minimal-loop2/costmap_experiment.md) ｜ 操作卡：[relog-operation.md](../minimal-loop2/relog-operation.md)
- bag：N97 `~/Lin_workspace/r2_integration/bags/relog_0903_2104`（已拷 VM `~/Lin_workspace/bags/raw/`，1.9G，不入 git）
- 关联事件：[08-17 初始位姿/膨胀](2026-08-17_nav2_initialpose_inflation_fix.md)
