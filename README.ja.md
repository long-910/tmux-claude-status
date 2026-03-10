# tmux-claude-status

[![CI](https://github.com/long-910/tmux-claude-status/actions/workflows/ci.yml/badge.svg)](https://github.com/long-910/tmux-claude-status/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![tmux 3.0+](https://img.shields.io/badge/tmux-3.0%2B-1BB91F?logo=tmux&logoColor=white)](https://github.com/tmux/tmux)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/long-910?label=Sponsor&logo=GitHub&color=EA4AAA)](https://github.com/sponsors/long-910)

> **お知らせ:** v0.8.0 より、リポジトリ名を `claude-tmux-status` から `tmux-claude-status` に変更しました。
> 旧プラグイン名をご利用の方は `~/.tmux.conf` を更新してください：
> ```diff
> - set -g @plugin 'long-910/claude-tmux-status'
> + set -g @plugin 'long-910/tmux-claude-status'
> ```
> また、`~/.claude/claude-tmux-status.json` が存在する場合は `~/.claude/tmux-claude-status.json` にリネームしてください。

Claude Code の**使用状況**を tmux ステータスバーに表示するツールです。
デフォルトでは **API コールを一切行いません**。
**Claude.ai サブスクリプション**（使用率%表示）と **AWS Bedrock / API キー**（ローカル JSONL からのコスト表示）に対応しています。

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

**Claude.ai Pro / Max / Team / Enterprise**（Anthropic API からの使用率%）:
```
5h:78%(2h47m) 7d:84%!  |  [CPU/MEM]  |  11:23 2026-02-23
```

**5h 専用プラン**（週間制限なし）:
```
5h:78%(2h47m)  |  [CPU/MEM]  |  11:23 2026-02-23
```

**AWS Bedrock / API キー**（ローカル JSONL からのコスト表示、API コールなし）:
```
[cost] 5h:$14.21 day:$14.21 7d:$53.17  |  [CPU/MEM]  |  11:23 2026-02-23
```

| 表示 | 意味 |
|------|------|
| `5h:78%` | 5時間ウィンドウ使用率（Anthropic API から取得、Claude.ai 設定画面と同値） |
| `(2h47m)` | 5hウィンドウのリセットまでの残り時間 |
| `7d:84%` | 週間使用率（週間制限のないプランでは非表示） |
| `!` | `allowed_warning`（75%超過） |
| `X` | `denied`（制限到達） |
| `[15m ago]` | キャッシュの経過時間（Claude 未使用時のみ表示） |
| `[cost]` | コストモード（Bedrock/API キー時または手動切替時） |

**キャッシュなし（初回）:**
```
[--] run: claude-usage --refresh
```

> **注意:** 使用率%表示は **Claude.ai Pro プランのみで動作確認済み**です。
> Max・Team・Enterprise・Bedrock など他のプランで正しく表示されない場合は、
> [Issue を発行してください](https://github.com/long-910/tmux-claude-status/issues)。

---

## インストール

### TPM (Tmux Plugin Manager) — 推奨

`~/.tmux.conf` に追加：

```tmux
set -g @plugin 'long-910/tmux-claude-status'
```

その後 `<prefix> + I` でインストール。

#### TPM オプション

```tmux
# すべてオプション（デフォルト値を示す）:
set -g @claude-tmux-toggle-key    "U"      # <prefix>+U でパーセント/コスト切替
set -g @claude-tmux-dashboard-key "B"      # <prefix>+B でダッシュボード popup を開く（tmux 3.2+）
set -g @claude-tmux-install-hook  "true"   # Claude Code Stop フックを自動設定
set -g @claude-tmux-auto-status   "true"   # status-right を自動設定
set -g @claude-tmux-realtime      "false"  # 5分ごとの API ポーリングを有効化
set -g @claude-tmux-cache-ttl    "300"    # キャッシュ有効期間（秒）
```

### GitHub Release からインストール

`git clone` 不要。最新の `claude-usage` バイナリを直接ダウンロード：

```bash
mkdir -p ~/.local/bin
curl -fsSL https://github.com/long-910/tmux-claude-status/releases/latest/download/claude-usage \
  -o ~/.local/bin/claude-usage
chmod +x ~/.local/bin/claude-usage
```

`~/.tmux.conf` に以下を追加：

```tmux
# tmux-claude-status
set -g status-right-length 200
set -g status-right "#(claude-usage short) | %H:%M %Y-%m-%d"
bind U run-shell "claude-usage toggle && tmux refresh-client -S"
bind B display-popup -E -w 82 -h 90% "claude-usage dashboard"
```

tmux を再読み込みし、Stop フックを設定：

```bash
tmux source-file ~/.tmux.conf
claude-usage --install-hook
```

初回のキャッシュ取得：

```bash
claude-usage --refresh
```

### 手動インストール

ワンライナー（git 不要）：

```bash
curl -fsSL https://raw.githubusercontent.com/long-910/tmux-claude-status/main/install.sh | bash
```

またはローカルクローンから：

```bash
git clone https://github.com/long-910/tmux-claude-status.git
cd tmux-claude-status
bash install.sh
```

---

## アンインストール

### TPM 経由

`~/.tmux.conf` からプラグイン行を削除：

```tmux
set -g @plugin 'long-910/tmux-claude-status'
```

その後 `<prefix> + alt + u` で TPM によるアンインストールを実行。

### 手動アンインストール

```bash
cd tmux-claude-status
bash uninstall.sh
```

以下が削除されます：
- `~/.local/bin/claude-usage`
- `~/.tmux.conf` の `tmux-claude-status` ブロック
- `~/.claude/settings.json` の Stop フック
- `~/.claude/tmux-claude-status.json`（設定ファイル）
- `~/.claude/tmux-rate-limit-cache.json`（キャッシュ）

---

## 必要環境

- Python 3.10+
- tmux 3.0+
- Claude Code
  - Claude.ai サブスクリプション: 使用率%表示に `~/.claude/.credentials.json` が必要
  - AWS Bedrock / API キー: 資格情報ファイル不要（ローカル JSONL からコスト表示）

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
| `claude-usage dashboard` | インタラクティブダッシュボード | Claude 使用時のみ |
| `claude-usage --version` | バージョン表示して終了 | なし |
| `claude-usage --help` | ヘルプ表示して終了 | なし |
| `claude-usage --install-hook` | Stop フックを設定 | なし |
| `claude-usage --uninstall-hook` | Stop フックを削除 | なし |

### コストモード

`<prefix> + U`（または `claude-usage toggle`）でコスト表示に切り替え：

```
5h:$14.21 day:$14.21 7d:$53.17
```

### ダッシュボード

`<prefix> + B`（または `claude-usage dashboard`）でフルスクリーンのダッシュボードを開きます。
popup ウィンドウには **tmux 3.2+** が必要です。通常のターミナルでも動作します。

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

| キー | 操作 |
|------|------|
| `r` | 即時リフレッシュ |
| `w` | 30秒自動更新（ウォッチモード）の切替 |
| `q` / `Esc` | 終了 |

### `long` モード出力例

Claude.ai サブスクリプション（Pro プランの例）:
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

AWS Bedrock / API キー:
```
-- Rate Limit [default(no API)] provider:auto(other) ------------------
  [not available] AWS Bedrock / API key — showing cost from local JSONL
-- Token Cost [local JSONL] ---------------------------------
  5h : in:38.5K out:127.8K cr:24.6M cw:1.3M cost:$14.21
  day: in:38.5K out:127.8K cr:24.6M cw:1.3M cost:$14.21
  7d : in:80.0K out:468.9K cr:89.5M cw:5.1M cost:$53.17
```

---

## 更新タイミング

デフォルトでは、Claude が実際に使用されているときのみ API を呼び出します。
idle 時は古いキャッシュを `[Xm ago]` 付きで表示し、トークンを消費しません。

### 設定ファイル

`~/.claude/tmux-claude-status.json` を編集：

```json
{
  "realtime": false,
  "cache_ttl": 300,
  "provider": "auto"
}
```

| キー | 値 | デフォルト | 説明 |
|------|-----|-----------|------|
| `realtime` | `true` / `false` | `false` | Claude の状態に関わらず `cache_ttl` 秒ごとに API ポーリング |
| `cache_ttl` | 整数（秒） | `300` | キャッシュ有効期間 |
| `provider` | `"auto"` / `"anthropic"` / `"bedrock"` / `"other"` | `"auto"` | プロバイダを手動指定。`"auto"` は `~/.claude/.credentials.json` で自動判定 |

### リアルタイムモード（opt-in）

上の設定ファイルで `"realtime": true` に設定してください。

**リアルタイムモード時のこのツール自身の消費量試算**（claude-haiku-4-5, 約9 tokens/回）：

| 期間 | API 回数 | 消費コスト |
|------|---------|-----------|
| 1日 | 288回 | ~$0.001 |
| 1週間 | 2,016回 | ~$0.009 |
| 1か月 | 8,640回 | ~$0.040 |

> デフォルト無効の理由: 「使用量確認ツールが余計な使用量を消費する本末転倒」を避けるためです。

---

## ライセンス

MIT

---

## コントリビュート

アーキテクチャ詳細・データソース・開発ガイドは [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。
