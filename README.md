# claude-tmux-status

Claude Code のトークン使用量をリアルタイムで tmux ステータスバーに表示するツールです。

## 表示例

```
🤖 in:26.3K out:63.0K $0.42  |  14:35 2026-02-23
```

## 仕組み

`~/.claude/projects/**/*.jsonl` を読み込み、**本日分**のトークン使用量を集計します。
tmux の `status-interval` に合わせて定期的に更新されます。

## 必要環境

- Python 3.8+
- tmux 3.0+
- Claude Code (`~/.claude/` ディレクトリが存在すること)

## インストール

```bash
git clone https://github.com/long-910/claude-tmux-status.git
cd claude-tmux-status
bash install.sh
```

インストール後、`~/.tmux.conf` に以下が追加されます：

```tmux
set -g status-right-length 120
set -g status-interval 30
set -g status-right "#[fg=colour39]#(claude-usage short)#[default] | %H:%M %Y-%m-%d"
```

## 手動設定

`install.sh` を使わない場合、以下の手順で設定してください。

```bash
# 1. スクリプトをインストール
cp claude_usage.py ~/.local/bin/claude-usage
chmod +x ~/.local/bin/claude-usage

# 2. ~/.tmux.conf に追加
cat >> ~/.tmux.conf << 'EOF'
# claude-tmux-status
set -g status-right-length 120
set -g status-interval 30
set -g status-right "#[fg=colour39]#(claude-usage short)#[default] | %H:%M %Y-%m-%d"
EOF

# 3. tmux をリロード
tmux source-file ~/.tmux.conf
```

## 出力モード

| モード | コマンド | 出力例 |
|--------|----------|--------|
| short  | `claude-usage short` | `🤖 in:26.3K out:63.0K $0.42` |
| long   | `claude-usage long`  | `Claude \| in:26.3K out:63.0K cache_r:20.4M cache_w:1.6M total:89.3K cost:$0.42` |
| json   | `claude-usage json`  | JSON 形式の詳細データ |

## コスト計算

Claude Sonnet 4.x の公式料金をもとに計算しています：

| トークン種別 | 料金 (USD/M tokens) |
|-------------|---------------------|
| Input       | $3.00               |
| Output      | $15.00              |
| Cache read  | $0.30               |
| Cache create| $3.75               |

> [!NOTE]
> 実際の請求額とは異なる場合があります。概算値としてご利用ください。

## ライセンス

MIT
