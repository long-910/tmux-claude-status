# claude-tmux-status

[![CI](https://github.com/long-910/claude-tmux-status/actions/workflows/ci.yml/badge.svg)](https://github.com/long-910/claude-tmux-status/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![tmux 3.0+](https://img.shields.io/badge/tmux-3.0%2B-1BB91F?logo=tmux&logoColor=white)](https://github.com/tmux/tmux)
[![Sponsor](https://img.shields.io/badge/Sponsor-GitHub-pink?logo=github)](https://github.com/sponsors/long-910)

在 tmux 状态栏实时显示 Claude Code **使用情况**。默认情况下**不消耗任何 token**。
支持 **Claude.ai 订阅**（使用率%显示）和 **AWS Bedrock / API 密钥**（从本地 JSONL 计算费用）。

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

---

## 工作原理

默认不调用 API。脚本监控 `~/.claude/projects/**/*.jsonl` 的变化，
只有在 Claude Code 实际使用时才会进行一次 API 调用。

```
Claude 运行中  →  JSONL 更新  →  调用 1 次 API  →  更新缓存  →  显示
Claude 空闲    →  仅读取缓存（不调用 API）  →  显示数据及经过时间
```

## 显示示例

**Claude.ai Pro / Max / Team / Enterprise**（来自 Anthropic API 的使用率%）：
```
5h:78%(2h47m) 7d:84%!  |  [CPU/MEM]  |  11:23 2026-02-23
```

**仅 5h 套餐**（无每周限制）：
```
5h:78%(2h47m)  |  [CPU/MEM]  |  11:23 2026-02-23
```

**AWS Bedrock / API 密钥**（从本地 JSONL 计费，无 API 调用）：
```
[cost] 5h:$14.21 day:$14.21 7d:$53.17  |  [CPU/MEM]  |  11:23 2026-02-23
```

| 字段 | 含义 |
|------|------|
| `5h:78%` | 5小时窗口使用率（来自 Anthropic API，与 Claude.ai 设置页相同） |
| `(2h47m)` | 5小时窗口重置倒计时 |
| `7d:84%` | 周使用率（无每周限制的套餐不显示） |
| `!` | `allowed_warning` — 超过 75% 阈值 |
| `X` | `denied` — 已达上限 |
| `[15m ago]` | 缓存经过时间（仅在 Claude 空闲时显示） |
| `[cost]` | 费用模式（Bedrock/API 密钥时自动启用，或手动切换） |

**无缓存（首次使用）：**
```
[--] run: claude-usage --refresh
```

> **注意：** 使用率%显示仅在 **Claude.ai Pro 套餐**下经过测试。
> 如果在 Max、Team、Enterprise、Bedrock 等其他套餐上显示不正确，
> 请[提交 Issue](https://github.com/long-910/claude-tmux-status/issues)。

---

## 安装

### 通过 TPM（Tmux 插件管理器）— 推荐

在 `~/.tmux.conf` 中添加：

```tmux
set -g @plugin 'long-910/claude-tmux-status'
```

然后按 `<prefix> + I` 安装。

#### TPM 可选配置

```tmux
# 以下均为可选项（括号内为默认值）：
set -g @claude-tmux-toggle-key    "U"      # <prefix>+U 切换百分比/费用显示
set -g @claude-tmux-dashboard-key "D"      # <prefix>+D 打开仪表盘弹窗（tmux 3.2+）
set -g @claude-tmux-install-hook  "true"   # 自动安装 Claude Code Stop 钩子
set -g @claude-tmux-auto-status   "true"   # 自动配置 status-right
set -g @claude-tmux-realtime      "false"  # 启用 5 分钟轮询（消耗 token）
set -g @claude-tmux-cache-ttl    "300"    # 缓存有效期（秒）
```

### 从 GitHub Release 安装

无需 `git clone`，直接下载最新 `claude-usage` 二进制文件：

```bash
mkdir -p ~/.local/bin
curl -fsSL https://github.com/long-910/claude-tmux-status/releases/latest/download/claude-usage \
  -o ~/.local/bin/claude-usage
chmod +x ~/.local/bin/claude-usage
```

在 `~/.tmux.conf` 中添加：

```tmux
# claude-tmux-status
set -g status-right-length 200
set -g status-right "#(claude-usage short) | %H:%M %Y-%m-%d"
bind U run-shell "claude-usage toggle && tmux refresh-client -S"
bind D display-popup -E -w 82 -h 40 "claude-usage dashboard"
```

重新加载 tmux 并安装 Stop 钩子：

```bash
tmux source-file ~/.tmux.conf
claude-usage --install-hook
```

首次运行，填充缓存：

```bash
claude-usage --refresh
```

### 手动安装

一键安装（无需 git）：

```bash
curl -fsSL https://raw.githubusercontent.com/long-910/claude-tmux-status/main/install.sh | bash
```

或从本地克隆安装：

```bash
git clone https://github.com/long-910/claude-tmux-status.git
cd claude-tmux-status
bash install.sh
```

---

## 卸载

### 通过 TPM

从 `~/.tmux.conf` 中删除插件行：

```tmux
set -g @plugin 'long-910/claude-tmux-status'
```

然后按 `<prefix> + alt + u` 通过 TPM 卸载。

### 手动卸载

```bash
cd claude-tmux-status
bash uninstall.sh
```

将删除以下内容：
- `~/.local/bin/claude-usage`
- `~/.tmux.conf` 中的 `claude-tmux-status` 配置块
- `~/.claude/settings.json` 中的 Stop 钩子
- `~/.claude/claude-tmux-status.json`（配置文件）
- `~/.claude/tmux-rate-limit-cache.json`（缓存文件）

---

## 环境要求

- Python 3.10+
- tmux 3.0+
- Claude Code
  - Claude.ai 订阅：使用率%显示需要 `~/.claude/.credentials.json`
  - AWS Bedrock / API 密钥：无需凭证文件，从本地 JSONL 显示费用

---

## 命令参考

| 命令 | 说明 | 是否调用 API |
|------|------|------------|
| `claude-usage` | 当前模式显示 | 仅 Claude 活跃时 |
| `claude-usage --refresh` | 强制更新 | 是（1次） |
| `claude-usage toggle` | 切换百分比 ↔ 费用 | 否 |
| `claude-usage cost` | 显示费用（临时） | 否 |
| `claude-usage long` | 完整详情 | 仅 Claude 活跃时 |
| `claude-usage json` | JSON 输出 | 仅 Claude 活跃时 |
| `claude-usage dashboard` | 交互式全屏仪表盘 | 仅 Claude 活跃时 |
| `claude-usage --version` | 显示版本并退出 | 否 |
| `claude-usage --install-hook` | 安装 Stop 钩子 | 否 |
| `claude-usage --uninstall-hook` | 删除 Stop 钩子 | 否 |

### 费用模式

按 `<prefix> + U`（或运行 `claude-usage toggle`）切换到费用显示：

```
5h:$14.21 day:$14.21 7d:$53.17
```

### 仪表盘

按 `<prefix> + D`（或运行 `claude-usage dashboard`）打开全屏仪表盘。
弹窗功能需要 **tmux 3.2+**，也可在任意终端中直接运行。

```
+==============================================================================+
|                            Claude Usage Dashboard                            |
+==============================================================================+
|   Rate Limits                                                     [just now] |
|                                                                              |
|   5h:  78%  [###############.....]  reset 2h47m       (allowed_warning)      |
|   7d:  84%  [################....]  reset 5.1d        (allowed_warning)      |
|                                                                              |
+------------------------------------------------------------------------------+
|   Token Usage & Cost                                                         |
|                                                                              |
|               Input     Output    CacheRd    CacheWr       Cost              |
|       5h      38.5K     127.8K      24.6M       1.3M     $14.21              |
|    Today      38.5K     127.8K      24.6M       1.3M     $14.21              |
|       7d      80.0K     468.9K      89.5M       5.1M     $53.17              |
|                                                                              |
+------------------------------------------------------------------------------+
|   Top Projects  (7-day cost)                                                 |
|                                                                              |
|   my-app                    $28.34  [##########........]  53%                |
|   claude-plugin             $14.12  [#####.............]  27%                |
|   dotfiles                  $10.71  [####..............]  20%                |
|                                                                              |
+------------------------------------------------------------------------------+
|   Provider: anthropic(auto)  |  Mode: default(no API)  |  Display: percent   |
+==============================================================================+

  [r] refresh    [w] toggle watch(30s)    [q] quit
```

| 按键 | 操作 |
|------|------|
| `r` | 立即刷新数据 |
| `w` | 切换 30 秒自动刷新（监视模式） |
| `q` / `Esc` | 退出 |

### `long` 模式输出示例

Claude.ai 订阅（Pro 套餐示例）：
```
-- Rate Limit [default(no API)] provider:auto(anthropic) ------------------
  5h:  78% [XXXXXX..] reset:2h47m  (allowed)
  7d:  84% [XXXXXXX.] reset:4.3d   (allowed_warning)
  last updated: just now
-- Token Cost [local JSONL] ---------------------------------
  5h : in:38.5K out:127.8K cr:24.6M cw:1.3M cost:$14.21
  day: in:38.5K out:127.8K cr:24.6M cw:1.3M cost:$14.21
  7d : in:80.0K out:468.9K cr:89.5M cw:5.1M cost:$53.17
```

AWS Bedrock / API 密钥：
```
-- Rate Limit [default(no API)] provider:auto(other) ------------------
  [not available] AWS Bedrock / API key — showing cost from local JSONL
-- Token Cost [local JSONL] ---------------------------------
  5h : in:38.5K out:127.8K cr:24.6M cw:1.3M cost:$14.21
  day: in:38.5K out:127.8K cr:24.6M cw:1.3M cost:$14.21
  7d : in:80.0K out:468.9K cr:89.5M cw:5.1M cost:$53.17
```

---

## 更新时机

默认情况下，仅在 Claude 实际运行时调用 API。
空闲时显示带 `[Xm ago]` 标记的旧缓存，不消耗任何 token。

### 配置文件

编辑 `~/.claude/claude-tmux-status.json`：

```json
{
  "realtime": false,
  "cache_ttl": 300,
  "provider": "auto"
}
```

| 键 | 值 | 默认 | 说明 |
|----|-----|------|------|
| `realtime` | `true` / `false` | `false` | 无论 Claude 是否活跃，每 `cache_ttl` 秒轮询 API |
| `cache_ttl` | 整数（秒） | `300` | 缓存有效期 |
| `provider` | `"auto"` / `"anthropic"` / `"bedrock"` / `"other"` | `"auto"` | 手动指定提供商。`"auto"` 通过 `~/.claude/.credentials.json` 自动检测 |

### 实时模式（可选）

在上方配置文件中将 `"realtime"` 设为 `true`。

**实时模式下本工具自身的消耗估算**（claude-haiku-4-5，约 9 tokens/次）：

| 周期 | API 调用次数 | 费用 |
|------|------------|------|
| 1天 | 288次 | ~$0.001 |
| 1周 | 2,016次 | ~$0.009 |
| 1个月 | 8,640次 | ~$0.040 |

> 默认禁用的原因：避免"用来监控使用量的工具反而消耗使用量"的本末倒置问题。

---

## 许可证

MIT

---

## 贡献

架构详情、数据来源及开发指南请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。
