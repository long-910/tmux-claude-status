# claude-tmux-status

Claude Code の**使用制限パーセンテージ**をリアルタイムで tmux ステータスバーに表示するツールです。
Anthropic API のレート制限ヘッダーから正確な値を取得し、5時間ウィンドウ・週間の使用率を表示します。

## 表示例

**パーセンテージモード（デフォルト）**
```
🤖 5h:78%(2h47m) 7d:84%!  |  [CPU/MEM]  |  11:23 2026-02-23
```

**コストモード（トグル切替可）**
```
🤖 5h:$9.42 day:$9.42 7d:$48.39  |  [CPU/MEM]  |  11:23 2026-02-23
```

| 表示 | 意味 |
|------|------|
| `5h:78%` | 直近5時間のレート制限消費率（Anthropic公式値） |
| `(2h47m)` | 5時間ウィンドウのリセットまでの残り時間 |
| `7d:84%` | 週間レート制限消費率 |
| `!` | `allowed_warning` 状態（75%超過） |
| `✗` | `denied` 状態（制限到達） |

## 仕組み

- **パーセンテージ**: Anthropic API (`/v1/messages`) のレスポンスヘッダー
  `anthropic-ratelimit-unified-5h-utilization` / `7d-utilization` を使用
  → API応答結果を **5分間キャッシュ** してコストを最小化
- **コスト**: `~/.claude/projects/**/*.jsonl` のローカルログを集計

## 必要環境

- Python 3.10+
- tmux 3.0+
- Claude Code（`~/.claude/.credentials.json` が存在すること）

## インストール

```bash
git clone https://github.com/long-910/claude-tmux-status.git
cd claude-tmux-status
bash install.sh
```

インストール後、`~/.tmux.conf` に以下が追加されます：

```tmux
# claude-tmux-status
set -g status-right-length 200
set -g status-right "#[fg=colour39]#(claude-usage short)#[default] | ... | %H:%M %Y-%m-%d"
# Prefix + U: toggle percent <-> cost
bind U run-shell "claude-usage toggle && tmux refresh-client -S"
```

## コマンドリファレンス

| コマンド | 説明 |
|----------|------|
| `claude-usage` | tmux用コンパクト表示（現在のモード） |
| `claude-usage toggle` | percent / cost モードを切り替え |
| `claude-usage cost` | コスト表示（一時的） |
| `claude-usage long` | 詳細表示（パーセント＋コスト両方） |
| `claude-usage json` | JSON形式の全データ |

### `long` モード出力例

```
── Rate limit (Anthropic API) ──────────────────────────────
  5h:  78% ▓▓▓▓▓▓░░  resets in 2h47m  [allowed]
  7d:  84% ▓▓▓▓▓▓▓░  resets in 4.4d  [allowed_warning]
── Token cost (local JSONL) ─────────────────────────────────
  5h : in:10.8K out:93.6K cr:17.4M cw:725.8K cost:$9.39
  day: in:10.8K out:93.6K cr:17.4M cw:725.8K cost:$9.39
  7d : in:52.4K out:434.6K cr:82.3M cw:4.5M cost:$48.35
```

## モード切り替え

| 方法 | 操作 |
|------|------|
| tmux キーバインド | `<prefix> + U` |
| コマンド | `claude-usage toggle` |

現在のモードは `~/.claude/tmux-display-mode` に保存されます。

## コスト計算（コストモード時）

Claude Sonnet 4.x の公式料金をもとに計算：

| トークン種別 | 料金 (USD/M) |
|-------------|-------------|
| Input (in)       | $3.00  |
| Output (out)     | $15.00 |
| Cache read (cr)  | $0.30  |
| Cache create (cw)| $3.75  |

## ライセンス

MIT
