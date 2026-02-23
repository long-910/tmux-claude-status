# claude-tmux-status

Claude Code のトークン使用量を tmux ステータスバーにリアルタイム表示するツールです。
**5時間ウィンドウ**（レート制限単位）・**本日**・**週間** の3軸で使用量とコストを表示します。

## 表示例

```
🤖 5h:20.2K $4.94 | day:$4.94 | 7d:$43.90  |  [CPU/MEM]  |  02:00 2026-02-23
```

| 項目 | 意味 |
|------|------|
| `5h:20.2K` | 直近5時間のアウトプットトークン数（レート制限ウィンドウ） |
| `$4.94` | 直近5時間の推定コスト |
| `day:$4.94` | 本日の推定コスト |
| `7d:$43.90` | 直近7日間の推定コスト |

## 仕組み

`~/.claude/projects/**/*.jsonl` を読み込み、各時間ウィンドウのトークン使用量を集計します。
Claude Code の**レート制限は5時間ローリングウィンドウ**に基づくため、それに合わせた表示を行います。

## 必要環境

- Python 3.8+
- tmux 3.0+
- Claude Code（`~/.claude/` ディレクトリが存在すること）

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
set -g status-right "#[fg=colour39]#(claude-usage short)#[default] | #[fg=green,bg=black]#(tmux-mem-cpu-load --colors --interval 2)#[default] | %H:%M %Y-%m-%d"
```

`tmux-mem-cpu-load` がない環境では CPU/MEM 部分なしのシンプルな形式になります。

## 手動設定

```bash
# 1. スクリプトをインストール
cp claude_usage.py ~/.local/bin/claude-usage
chmod +x ~/.local/bin/claude-usage

# 2. ~/.tmux.conf に追加
cat >> ~/.tmux.conf << 'EOF'
# claude-tmux-status
set -g status-right-length 200
set -g status-interval 30
set -g status-right "#[fg=colour39]#(claude-usage short)#[default] | %H:%M %Y-%m-%d"
EOF

# 3. tmux をリロード
tmux source-file ~/.tmux.conf
```

## 出力モード

| モード | コマンド | 出力例 |
|--------|----------|--------|
| short  | `claude-usage short` | `🤖 5h:20.2K $4.94 \| day:$4.94 \| 7d:$43.90` |
| long   | `claude-usage long`  | 各ウィンドウの全トークン種別内訳 |
| json   | `claude-usage json`  | JSON 形式の詳細データ |

### `long` モード出力例

```
5h  (last 5h): in:10.7K out:20.2K cr:8.2M cw:569.0K cost:$4.94
day (today)  : in:10.7K out:20.2K cr:8.2M cw:569.0K cost:$4.94
7d  (last 7d): in:52.3K out:361.3K cr:73.1M cw:4.4M cost:$43.90
```

## コスト計算

Claude Sonnet 4.x の公式料金をもとに計算しています：

| トークン種別 | 略称 | 料金 (USD/M tokens) |
|-------------|------|---------------------|
| Input       | in   | $3.00               |
| Output      | out  | $15.00              |
| Cache read  | cr   | $0.30               |
| Cache create| cw   | $3.75               |

> [!NOTE]
> 実際の請求額とは異なる場合があります。概算値としてご利用ください。
> レート制限の閾値（トークン上限数）はプランによって異なります。

## ライセンス

MIT
