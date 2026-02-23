# claude-tmux-status

在 tmux 状态栏实时显示 Claude Code **使用率百分比**。默认情况下**不消耗任何 token**。

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

```
5h:78%(2h47m) 7d:84%!  |  [CPU/MEM]  |  11:23 2026-02-23
```

| 字段 | 含义 |
|------|------|
| `5h:78%` | 5小时窗口使用率（来自 Anthropic API，与 Claude.ai 设置页相同） |
| `(2h47m)` | 5小时窗口重置倒计时 |
| `7d:84%` | 周使用率 |
| `!` | `allowed_warning` — 超过 75% 阈值 |
| `X` | `denied` — 已达上限 |
| `[15m ago]` | 缓存经过时间（仅在 Claude 空闲时显示） |

**无缓存（首次使用）：**
```
[--] run: claude-usage --refresh
```

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
set -g @claude-tmux-toggle-key   "U"      # <prefix>+U 切换百分比/费用显示
set -g @claude-tmux-install-hook "true"   # 自动安装 Claude Code Stop 钩子
set -g @claude-tmux-auto-status  "true"   # 自动配置 status-right
set -g @claude-tmux-realtime     "false"  # 启用 5 分钟轮询（消耗 token）
set -g @claude-tmux-cache-ttl   "300"    # 缓存有效期（秒）
```

### 手动安装

```bash
git clone https://github.com/long-910/claude-tmux-status.git
cd claude-tmux-status
bash install.sh
```

---

## 环境要求

- Python 3.10+
- tmux 3.0+
- Claude Code（需存在 `~/.claude/.credentials.json`）

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
| `claude-usage --install-hook` | 安装 Stop 钩子 | 否 |

### 费用模式

按 `<prefix> + U`（或运行 `claude-usage toggle`）切换到费用显示：

```
5h:$14.21 day:$14.21 7d:$53.17
```

### `long` 模式输出示例

```
-- Rate Limit [default(no API)] ------------------------------
  5h:  78% [XXXXXX..] reset:2h47m  (allowed)
  7d:  84% [XXXXXXX.] reset:4.3d   (allowed_warning)
  last updated: just now
-- Token Cost [local JSONL] ---------------------------------
  5h : in:38.5K out:127.8K cr:24.6M cw:1.3M cost:$14.21
  day: in:38.5K out:127.8K cr:24.6M cw:1.3M cost:$14.21
  7d : in:80.0K out:468.9K cr:89.5M cw:5.1M cost:$53.17
```

---

## 更新时机

### 默认模式（空闲时零消耗）

| 条件 | 动作 |
|------|------|
| 缓存在 `cache_ttl` 内 | 仅读取缓存（不调用 API） |
| 缓存过期 + JSONL 最近更新 | 调用 1 次 API 刷新 |
| 缓存过期 + Claude 空闲 | 显示旧缓存（附带 `[Xm ago]`） |
| Claude Code 会话结束（Stop 钩子） | 调用 1 次 API 刷新 |
| 执行 `claude-usage --refresh` | 调用 1 次 API |

### 实时模式（可选）

编辑 `~/.claude/claude-tmux-status.json`：

```json
{
  "realtime": true,
  "cache_ttl": 300
}
```

**实时模式下本工具自身的消耗估算**（claude-haiku-4-5，约 9 tokens/次）：

| 周期 | API 调用次数 | 费用 |
|------|------------|------|
| 1天 | 288次 | ~$0.001 |
| 1周 | 2,016次 | ~$0.009 |
| 1个月 | 8,640次 | ~$0.040 |

> 默认禁用的原因：避免"用来监控使用量的工具反而消耗使用量"的本末倒置问题。

---

## 数据来源

- **百分比**：`anthropic-ratelimit-unified-5h-utilization` / `7d-utilization` 响应头（与 Claude.ai 设置页数据相同）
- **费用**：`~/.claude/projects/**/*.jsonl` 本地聚合（无需网络）

### 费用计算定价（Claude Sonnet 4.x）

| Token 类型 | USD / 1M |
|-----------|----------|
| Input | $3.00 |
| Output | $15.00 |
| Cache read | $0.30 |
| Cache create | $3.75 |

---

## 许可证

MIT
