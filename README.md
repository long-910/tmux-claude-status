# claude-tmux-status

Claude Code の**使用制限パーセンテージ**を tmux ステータスバーに表示するツールです。

## 設計思想

**デフォルトでは API コールを一切行いません。**
`~/.claude/projects/**/*.jsonl` の更新を監視し、
Claude Code が実際に使用されたときだけキャッシュを更新します。

```
[Claude 使用中]  → JSONL 更新検知 → API 1回 → キャッシュ更新 → 表示
[Claude 未使用]  → キャッシュ読み取りのみ → 経過時間付きで表示
```

## 表示例

**パーセンテージモード（デフォルト）**

| 状況 | 表示 |
|------|------|
| 最新データ（Claude 使用中） | `5h:78%(2h47m) 7d:84%!` |
| 15分前のデータ（Claude 未使用） | `5h:78%(3h02m) 7d:84%! [15m前]` |
| 2時間前のデータ | `5h:78%(0h47m) 7d:84%! [2h前]` |
| キャッシュなし（初回） | `[--] run: claude-usage --refresh` |

```
5h:78%(2h47m) 7d:84%!  |  [CPU/MEM]  |  11:23 2026-02-23
```

| 項目 | 意味 |
|------|------|
| `5h:78%` | 5時間ウィンドウの使用率（Anthropic 公式値） |
| `(2h47m)` | 5hウィンドウのリセットまでの残り時間 |
| `7d:84%` | 週間レート制限使用率 |
| `!` | `allowed_warning`（75%超過） |
| `X` | `denied`（制限到達） |
| `[15m前]` | キャッシュの経過時間（データが古い場合のみ表示） |

## データソース

パーセンテージは Anthropic API のレスポンスヘッダーから取得します。

```
anthropic-ratelimit-unified-5h-utilization: 0.78
anthropic-ratelimit-unified-7d-utilization: 0.84
```

Claude.ai 設定画面の値と同一です。

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

インストール内容：
1. `claude-usage` を `~/.local/bin/` に配置
2. `~/.tmux.conf` に status-right 設定と `<prefix>+U` キーバインドを追加
3. `~/.claude/settings.json` に **Stop フック**を追加（セッション終了時に自動更新）
4. `~/.claude/claude-tmux-status.json` に設定ファイルを作成

## 更新タイミング

### デフォルトモード（API コールなし）

```
Claude Code セッション
  └─ メッセージ送受信  →  JSONL 更新
  └─ セッション終了    →  Stop フック  →  claude-usage --refresh (API 1回)
                                            └─ キャッシュ更新
tmux (30秒ごと)
  └─ claude-usage short
       ├─ JSONL が最近更新されている (< 5分) → API 1回  →  キャッシュ更新
       └─ JSONL が古い                        → キャッシュ読み取り + [X分前] 表示
```

| タイミング | API コール | 説明 |
|----------|-----------|------|
| Claude 使用中 (JSONL < 5分前) | ✅ 1回/5分 | 使用率を最新化 |
| Claude 未使用 | ❌ なし | キャッシュを表示（経過時間付き） |
| セッション終了時 (Stop フック) | ✅ 1回 | セッション終了後に更新 |
| 手動 `--refresh` | ✅ 1回 | 強制更新 |

### リアルタイムモード（opt-in）

`~/.claude/claude-tmux-status.json` を編集して有効化：

```json
{
  "realtime": true,
  "cache_ttl": 300
}
```

**このツール自体の消費量試算（リアルタイムモード）**

API コール仕様: claude-haiku-4-5-20251001, 入力 ~8 tokens, 出力 1 token

| 期間 | API コール数 | 消費コスト |
|------|-------------|-----------|
| 1日 | 288回（5分×12×24h） | ~$0.001 |
| 1週間 | 2,016回 | ~$0.009 |
| 1か月 | 8,640回 | ~$0.040 |

> **注意**: これは Claude Pro の月額料金（$20〜）と比較して非常に小さい額ですが、
> デフォルト無効としているのは「使用量確認ツールが余計な使用量を消費する本末転倒」を避けるためです。

## コマンドリファレンス

| コマンド | 説明 | API コール |
|----------|------|-----------|
| `claude-usage` | 現在モードで表示 | なし（キャッシュ読み取り or JSONL検知時のみ） |
| `claude-usage --refresh` | 強制更新 | 1回 |
| `claude-usage toggle` | percent / cost 切替 | なし |
| `claude-usage cost` | コスト表示（一時的） | なし |
| `claude-usage long` | 詳細表示（パーセント＋コスト） | なし（同上） |
| `claude-usage json` | JSON 出力 | なし（同上） |
| `claude-usage --install-hook` | Stop フック設定 | なし |

## モード切り替え

tmux で `<prefix> + U` を押すとパーセント表示とコスト表示が切り替わります。

**コストモード表示例**
```
5h:$14.21 day:$14.21 7d:$53.17
```

## 設定ファイル

`~/.claude/claude-tmux-status.json`

```json
{
  "realtime": false,
  "cache_ttl": 300
}
```

| キー | デフォルト | 説明 |
|------|-----------|------|
| `realtime` | `false` | `true` でリアルタイム更新（API 消費あり） |
| `cache_ttl` | `300` | キャッシュ有効期間（秒） |

## コスト計算（コストモード）

Claude Sonnet 4.x 料金：

| 種別 | 料金 (USD/M) |
|------|------------|
| Input       | $3.00 |
| Output      | $15.00 |
| Cache read  | $0.30 |
| Cache create| $3.75 |

## ライセンス

MIT
