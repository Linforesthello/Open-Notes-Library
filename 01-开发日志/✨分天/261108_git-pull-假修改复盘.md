# 复盘：`git pull` 被"假已修改"挡住（autocrlf 换行符 / index stat 缓存）

| 项 | 值 |
|---|---|
| 日期 | 2026-11-08 |
| 仓库 | `C:\Users\86173\Desktop\Open_Notes_Library`（GitHub: Linforesthello/Open-Notes-Library） |
| 分支 | `main` |
| 影响 | 无法 `git pull`，阻断 R2 镜像批次同步；**未丢失任何内容** |
| 结论 | 19 个文件被误判为"已修改"，重建 index stat 缓存后正常快进 |

---

## 0. 一句话结论

工作区里 19 个 Markdown 文件的**内容与 HEAD 逐字节相同**，但 index 里缓存的 `size` 还是它们当年 CRLF 形态的长度（30653），而磁盘上已被重写成 LF（30250），差 403 = 该文件的 LF 个数。git 先按 stat 判定"已修改"，而 `git diff` 走 clean 过滤器归一化后看不到差异 —— 于是出现「`status` 说脏、`diff` 说空」的自相矛盾，`git pull` 据此拒绝覆盖交集文件并中止。

**不是用户改过文件，不是 stash 丢失，不是 LFS 问题，不是网络问题。**

---

## 1. 现场

原始报错：

```
$ git pull
remote: Enumerating objects: 248, done.
 ...
From https://github.com/Linforesthello/Open-Notes-Library
   aa3f86f..d79f01e  main       -> origin/main
Updating aa3f86f..d79f01e
error: Your local changes to the following files would be overwritten by merge:
        01-开发日志/✨总/当前项目文档/R2_Integration/doc/two-car-architecture.md
Please commit your changes or stash them before you merge.
Aborting
```

注意两点：

1. 提示只报了 **1 个**文件，但它是"第一个撞上的"——实际有 19 个文件处于该状态。
2. `aa3f86f..d79f01e` 是**纯快进**范围（本地无自有提交），所以只需要工作区干净就能过。

环境：

```
git version 2.50.1.windows.1
core.autocrlf=true      ← 来源 C:/Git/install/Git/etc/gitconfig（Git for Windows 系统级）
core.filemode=false  core.ignorecase=true  core.symlinks=false
仓库内无 .gitattributes（git check-attr -a 为空）
core.safecrlf 未设置
```

---

## 2. 时间线

| 阶段 | 动作 | 结果 |
|---|---|---|
| ① | `git pull` | `error: local changes would be overwritten`，中止 |
| ② | 只读排查：`git diff` / `git diff --numstat` | **全空**（与"有本地修改"矛盾） |
| ③ | `git status --porcelain=v2` | 19 条 `1 .M`，且 hH == hI（HEAD 与 index 哈希相同） |
| ④ | `git hash-object --no-filters` vs `HEAD:file` | 都是 `33db1e1e...`，**逐字节相同** |
| ⑤ | 字节取证：size / CR / LF / index `--debug` | 磁盘 30250 字节、0 个 CR、403 个 LF；**index 缓存 size = 30653** |
| ⑥ | `git update-index --refresh` | 打印 19 行 `: needs update`，未清除 → 症状复现 |
| ⑦ | `git config core.autocrlf input` + `git add -u` | `git status --short` **完全干净** |
| ⑧ | `git pull --ff-only` | **`Fast-forward`**，133 files changed, 25448 insertions(+), 33 deletions(-) |

---

## 3. 关键证据（可复核）

以 `01-开发日志/✨总/当前项目文档/R2_Integration/doc/two-car-architecture.md` 为例：

| 检查项 | 结果 | 含义 |
|---|---|---|
| 磁盘文件大小 | **30250** 字节 | 当前真实长度 |
| CR (0x0D) 个数 | **0** | 纯 LF，无任何 CRLF |
| LF (0x0A) 个数 | **403** | 行数 |
| `HEAD:file` blob 大小 | **30250** | 与磁盘一致 |
| `hash-object --no-filters` | `33db1e1e...` | 与 HEAD blob 相同 |
| `hash-object`（带过滤器） | `33db1e1e...` | 同上，clean 转换不改字节 |
| `ls-files --debug` 中 `size` | **30653** | = 30250 + 403，即 **CRLF 形态的长度** |
| `git diff` / `git diff-files` / `git diff-index` | 空 / 空 / 空 | 内容维度上无任何差异 |
| `git ls-files --eol` | `i/lf w/lf` | index 与工作区都是 LF |
| 文件 mtime | 2026-11-06T06:19:45Z | 早于 index 写入时间 |
| `.git/index` 写入时间 | 2026-11-08T03:14:41Z | index 比文件新 |

**30653 − 30250 = 403 = LF 行数** 是这次定位的"决定性一击"：index 记录的 stat 来自这些文件还是 CRLF 的某个历史时刻，之后文件被改写成 LF，但 `size` 没跟着更新。

---

## 4. 根因链

1. Git for Windows 在**系统级** `etc/gitconfig` 里设了 `core.autocrlf=true`（仓库里没有 `.gitattributes` 覆盖），git 认为这个仓库应该以 CRLF 形式检出。
2. 某次检出/操作把文件按 CRLF 写入（长度 30653），该形态的 stat（size/mtime）被记进 `.git/index`。
3. 之后有工具（同步脚本 / Obsidian / 编辑器保存）把同一批文件改写成纯 LF（30250），mtime 变了、**字节内容与提交内容等价**（因为 clean 过滤器 CRLF→LF 与 LF 原样都归一到 LF，哈希相同）。
4. git 判定"是否修改"先看 stat：`size` 30653 ≠ 30250 → 先标 `DATA_CHANGED`；而 `git diff` 输出走归一化后的 blob 对比 → 内容一致 → 什么都不打印。**两套视图就此分叉。**
5. `git pull` 在 `unpack_trees` 阶段对将要覆盖的路径做 `verify_uptodate`，命中了这个"脏"判定；由于 `two-car-architecture.md` 恰好在 `aa3f86f..d79f01e` 的改动范围内（该文件在本批次被 4 个提交改动：`49f8ff1`、`35ee94f`、`8e32abc`、`24f7614`），于是直接 `Aborting`。
6. `git update-index --refresh` 本应通过重算内容把条目刷成 `CE_UPTODATE`，但在 `size` 不符 + `safecrlf` 警告路径下没生效（仍打印 19 行 `: needs update`）。**这一步的具体内部判定属推断**，但"index stat 与磁盘不一致"是可以被上面的数字确证的。
7. 重建 index 条目（`git add -u`）后 stat 被正确写入，`status` 归零，快进通过。

> 放大镜：`core.autocrlf=true` + 一个实际以 LF 存放的仓库 = 结构性矛盾。只要有任何工具反复改写文件，就会周期性复现"假脏"。

---

## 5. 修复动作（实际执行，共 4 条）

```powershell
cd C:\Users\86173\Desktop\Open_Notes_Library

# 1) 关掉 autocrlf 的检出侧写回（仓库级，覆盖全局的 true）
git config core.autocrlf input

# 2) 按当前 eol 规则重建 index 条目，刷新 stat 缓存（内容不变）
git add -u

# 3) 验证：应完全无输出
git status --short

# 4) 快进
git pull --ff-only
```

各步的作用与安全性：

| 命令 | 作用 | 为什么安全 |
|---|---|---|
| `git config core.autocrlf input` | 提交时 CRLF→LF、检出时不转换，匹配 LF 仓库 | 只改配置，不动文件 |
| `git add -u` | 重写 index 条目的 stat（size 30653→30250）；仅跟踪文件 | `git diff` 为空 ⇒ 没有任何 blob 内容会变，**不可能丢内容** |
| `git status --short` | 确认干净 | 只读 |
| `git pull --ff-only` | 快进 `aa3f86f → d79f01e` | 本地无自有提交，纯快进；拒绝任何 merge 提交生成 |

**为什么没用 `git checkout -- .`**：它会把 index 内容按当时的 `autocrlf=true` 重新写成 CRLF，等于把"30653 vs 30250"的坑再挖一遍，下次同步工具改写后必然复发。`git add -u` 只是修正 stat 记账，不碰工作区字节。

**为什么没用 `git stash`**：stash 是为"有真实改动"准备的；本例内容与 HEAD 完全一致，stash 只会让 index/工作区多绕一圈，没有收益。

---

## 6. 修复结果

```
$ git pull --ff-only
Updating aa3f86f..d79f01e
Fast-forward
 ...
133 files changed, 25448 insertions(+), 33 deletions(-)
```

- 提交推进：`aa3f86f` → `d79f01e`
- 内容概要：R2 旧车 LD06 双雷达文档、探索先验地图调研、n97 部署清单、11-07 原始数据（build/smoke/retest/netdiag/scan/crop）、个人简历目录重组（`个人简历/` → `个人简历/Linux下/`、`个人简历/windows导入-261025_19-23/`）、`Attachments/` 新增 4 张截图、新增 `resume.css` 等
- 数据完整性：`git stash list` 为空（本次未产生 stash）；`git diff` 前后均为空，**无内容丢失**

---

## 7. 防复发

1. **仓库级 eol 策略已固定**：`core.autocrlf=input`（已写入 `.git/config`）。以后换机器、换 Git 安装，记得确认这一项。
2. 可选加固：在仓库根加 `.gitattributes`，把规则写进版本库，跨机器一致：
   ```gitattributes
   * text=auto eol=lf
   *.png binary
   *.pdf binary
   *.docx binary
   ```
   （注意：启用后首次需要 `git add --renormalize .` 一次性统一，会产生一批 eol 提交，建议单独提交、单独评审。）
3. **工具一致性**：Obsidian / VSCode / 同步脚本 的保存编码与换行都要设成 UTF-8 + LF，避免反复"改写但内容等价"。
4. **不轻易 `git add -A`**：含未跟踪文件；本仓库用 `git add -u` 足够。
5. **镜像仓库习惯**：本仓库提交信息带 `镜像|…（权威源 r2_integration <hash>）`，是单向镜像。这类仓库里出现"本地修改"要在第一时间怀疑是生成/同步工具，而不是人工编辑。

---

## 8. 下次 3 分钟定位清单

出现 `error: Your local changes ... would be overwritten` 时，按顺序跑：

```powershell
# 1. 真的改了吗？（内容维度）
git diff --numstat
git diff-files --numstat
git diff-index --numstat HEAD

# 2. 若上面全空 → 怀疑 stat 缓存 / 换行符
git status --porcelain=v2            # 看 hH 与 hI 是否相同
git ls-files --eol -- <path>         # i/lf w/lf 还是 i/lf w/crlf
git ls-files --debug -- <path>       # 看 index 缓存的 size / mtime

# 3. 对照磁盘真实字节
(Get-Item <path>).Length
$b=[IO.File]::ReadAllBytes(<path>); ($b | Where-Object {$_ -eq 13}).Count   # CR 个数

# 4. 对照 blob
git cat-file -s HEAD:<path>
git hash-object --no-filters <path>
```

判定口诀：

- `diff` 全空 + `hash-object` 与 index/HEAD 相同 ⇒ **假脏，内容安全**，用 `git add -u` 重建 stat。
- `index size` 与磁盘 `size` 的差值恰好等于 `CR` 或 `LF` 数量 ⇒ 换行符记账问题，检查 `core.autocrlf`。
- `diff` 非空 ⇒ 真有改动，才谈 stash / 提交。

---

## 9. 教训

1. **"已修改"有两层含义**：内容变了 vs 记账过期了。`git status` 的 M 只说明"统计信息对不上"，不说明内容变了；要立刻交叉验证 `git diff`。
2. **报错只点名一个文件**，不代表只有一个文件有问题；`pull` 是撞一个停一个。
3. **配置矛盾会长期潜伏**：`autocrlf=true` 配 LF 仓库，平时只是刷屏警告（`LF will be replaced by CRLF`），一旦有外部工具改写文件就升级为阻断性错误。
4. **修复要选"只改记账"的操作**（`git add -u`），而不是"重写文件"的操作（`git checkout -- .`）——后者会把矛盾的 CRLF 形态固化到磁盘，制造循环复发。

---

## 附录 A：原始输出片段

```
$ git status --short            # 修复前（节选，共 19 条，均为 " M" 且无未跟踪文件）
 M "01-开发日志/✨分天/202510_STM32_MATLAB/✨20251024.md"
 M "01-开发日志/✨总/✨标签导航.md"
 M "01-开发日志/✨总/当前项目文档/R2_Integration/doc/two-car-architecture.md"
 ...

$ git update-index --refresh    # 未生效
01-开发日志/✨总/当前项目文档/R2_Integration/doc/two-car-architecture.md: needs update
 ...（共 19 行）

$ git ls-files --debug -- .../two-car-architecture.md
  ctime: 1793945876:147244900
  mtime: 1793945876:147744600
  dev: 0	ino: 0
  uid: 0	gid: 0
  size: 30653	flags: 0
```

## 附录 B：本次涉及的 Git 配置

```
# 系统级（Git for Windows 安装目录）
C:/Git/install/Git/etc/gitconfig: core.autocrlf=true      ← 问题的源头

# 仓库级（本次新增）
core.autocrlf=input                                        ← 修复并防复发
```

## 附录 C：术语

- **CRLF / LF**：Windows 换行 `\r\n` 与 Unix 换行 `\n`。同一份文本用两种形态存，字节数之差恰好等于行数。
- **stat 缓存**：`.git/index` 为每个文件记录 (ctime, mtime, size, ino…)，用于快速判断"可能变了"，命中后再做内容哈希确认。
- **clean / smudge 过滤器**：`autocrlf` 通过它们在工作区(CRLF)与对象库(LF)之间互转；转换是可逆的，所以"换行不同"通常不算修改——但当 stat 缓存失真、且工具已改写文件时，判定会卡在中间态。
