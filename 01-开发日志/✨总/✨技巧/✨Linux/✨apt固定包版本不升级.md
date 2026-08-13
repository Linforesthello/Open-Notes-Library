# ✨apt 固定包版本不升级（apt-mark hold）

#Tools/工具链/linux/apt #Problems/solving/apt/指定包不升级

> [!NOTE] 适用场景
> 系统更新时（`apt upgrade`）只想跳过个别包（如 VS Code、Edge），其余包照常更新。

## 核心操作

| 操作 | 命令 |
|:---|:---|
| 钉住（不升级） | `sudo apt-mark hold <包名>` |
| 查看已钉住的包 | `apt-mark showhold` |
| 解除钉住 | `sudo apt-mark unhold <包名>` |
| 只升级某个被钉住的包 | `sudo apt install --only-upgrade <包名>` |

## 实例（2026-08-13）

本机升级清单里有两个包不想动：

```bash
sudo apt-mark hold code                    # VS Code
sudo apt-mark hold microsoft-edge-stable   # Edge
```

## 效果与注意

- hold 后 `apt upgrade` / `full-upgrade` 会跳过该包，**其余包照常更新**
- 但 `apt list --upgradable` 里**仍会显示**该包，标记从"可从该版本升级"变为 held back（`[held back]`）——这是正常现象，不是没生效
- 验证是否生效：`apt-mark showhold` 能看到该包即已钉住
- 手动 `sudo apt install <包名>` 仍可强制升级；想彻底锁死（连手动安装也挡）用 apt preferences（`/etc/apt/preferences.d/` 配 Pin），日常场景 hold 够用
- 若包被卸载后重装，hold 状态可能丢失（apt 历史 bug：Launchpad 1904195），重装后需重新 hold
