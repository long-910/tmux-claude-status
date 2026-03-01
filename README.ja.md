# claude-tmux-status

[![CI](https://github.com/long-910/claude-tmux-status/actions/workflows/ci.yml/badge.svg)](https://github.com/long-910/claude-tmux-status/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![tmux 3.0+](https://img.shields.io/badge/tmux-3.0%2B-1BB91F?logo=tmux&logoColor=white)](https://github.com/tmux/tmux)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/long-910?label=Sponsor&logo=GitHub&color=EA4AAA)](https://github.com/sponsors/long-910)

Claude Code の**使用制限パーセンテージ**を tmux ステータスバーに表示するツールです。
デフォルトでは **API コールを一切行いません**。

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

---

## 動作原理

Claude Code が実際に使用されたときのみ、API コールを行います。
`~/.claude/projects/**/*.jsonl` の更新を監視し、Claude が idle の間はキャッシュを読み取るだけです。

```
Claude 使用中  →  JSONL 更新検知  →  API 1回  →  キャッシュ更新  →  表示
Claude 未使用  →  キャッシュ読み取りのみ（API コールなし）  →  経過時間付きで表示
```

## 表示例

```
5h:78%(2h47m) 7d:84%!  |  [CPU/MEM]  |  11:23 2026-02-23
```

| 表示 | 意味 |
|------|------|
| `5h:78%` | 5時間ウィンドウ使用率（Anthropic API から取得、Claude.ai 設定画面と同値） |
| `(2h47m)` | 5hウィンドウのリセットまでの残り時間 |
| `7d:84%` | 週間使用率 |
| `!` | `allowed_warning`（75%超過） |
| `X` | `denied`（制限到達） |
| `[15m ago]` | キャッシュの経過時間（Claude 未使用時のみ表示） |

**キャッシュなし（初回）:**
```
[--] run: claude-usage --refresh
```

---

## インストール

### TPM (Tmux Plugin Manager) — 推奨

`~/.tmux.conf` に追加：

```tmux
set -g @plugin 'long-910/claude-tmux-status'
```

その後 `<prefix> + I` でインストール。

#### TPM オプション

```tmux
# すべてオプション（デフォルト値を示す）:
set -g @claude-tmux-toggle-key   "U"      # <prefix>+U でパーセント/コスト切替
set -g @claude-tmux-install-hook "true"   # Claude Code Stop フックを自動設定
set -g @claude-tmux-auto-status  "true"   # status-right を自動設定
set -g @claude-tmux-realtime     "false"  # 5分ごとの API ポーリングを有効化
set -g @claude-tmux-cache-ttl   "300"    # キャッシュ有効期間（秒）
```

### 手動インストール

```bash
git clone https://github.com/long-910/claude-tmux-status.git
cd claude-tmux-status
bash install.sh
```

---

## アンインストール

### TPM 経由

`~/.tmux.conf` からプラグイン行を削除：

```tmux
set -g @plugin 'long-910/claude-tmux-status'
```

その後 `<prefix> + alt + u` で TPM によるアンインストールを実行。

### 手動アンインストール

```bash
cd claude-tmux-status
bash uninstall.sh
```

以下が削除されます：
- `~/.local/bin/claude-usage`
- `~/.tmux.conf` の `claude-tmux-status` ブロック
- `~/.claude/settings.json` の Stop フック
- `~/.claude/claude-tmux-status.json`（設定ファイル）
- `~/.claude/tmux-rate-limit-cache.json`（キャッシュ）

---

## 必要環境

- Python 3.10+
- tmux 3.0+
- Claude Code（`~/.claude/.credentials.json` が存在すること）

---

## コマンドリファレンス

| コマンド | 説明 | API コール |
|----------|------|-----------|
| `claude-usage` | 現在のモードで表示 | Claude 使用時のみ |
| `claude-usage --refresh` | 強制更新 | 1回 |
| `claude-usage toggle` | パーセント ↔ コスト 切替 | なし |
| `claude-usage cost` | コスト表示（一時的） | なし |
| `claude-usage long` | 詳細表示 | Claude 使用時のみ |
| `claude-usage json` | JSON 出力 | Claude 使用時のみ |
| `claude-usage --install-hook` | Stop フックを設定 | なし |
| `claude-usage --uninstall-hook` | Stop フックを削除 | なし |

### コストモード

`<prefix> + U`（または `claude-usage toggle`）でコスト表示に切り替え：

```
5h:$14.21 day:$14.21 7d:$53.17
```

### `long` モード出力例

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

## 更新タイミング

### デフォルトモード（idle 時は消費ゼロ）

| 条件 | 動作 |
|------|------|
| キャッシュが `cache_ttl` 以内 | キャッシュ読み取りのみ（API コールなし） |
| キャッシュ超過 ＋ JSONL が最近更新 | API 1回呼び出して更新 |
| キャッシュ超過 ＋ Claude 未使用 | 古いキャッシュ表示（`[Xm ago]` 付き） |
| Claude Code セッション終了時（Stop フック） | API 1回呼び出して更新 |
| `claude-usage --refresh` 実行時 | API 1回 |

### リアルタイムモード（opt-in）

`~/.claude/claude-tmux-status.json` を編集：

```json
{
  "realtime": true,
  "cache_ttl": 300
}
```

**リアルタイムモード時のこのツール自身の消費量試算**（claude-haiku-4-5, 約9 tokens/回）：

| 期間 | API 回数 | 消費コスト |
|------|---------|-----------|
| 1日 | 288回 | ~$0.001 |
| 1週間 | 2,016回 | ~$0.009 |
| 1か月 | 8,640回 | ~$0.040 |

> デフォルト無効の理由: 「使用量確認ツールが余計な使用量を消費する本末転倒」を避けるためです。

---

## データソース

- **パーセンテージ**: `anthropic-ratelimit-unified-5h-utilization` / `7d-utilization` レスポンスヘッダー（Claude.ai 設定画面と同値）
- **コスト**: `~/.claude/projects/**/*.jsonl` のローカル集計（ネットワーク不要）

### コスト計算料金（Claude Sonnet 4.x）

| 種別 | USD / 1M |
|------|----------|
| Input | $3.00 |
| Output | $15.00 |
| Cache read | $0.30 |
| Cache create | $3.75 |

---

## ライセンス

MIT
