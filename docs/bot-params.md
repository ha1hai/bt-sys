# ボット設定パラメータ仕様

ボットの取引頻度・条件はすべて `strategy_params`（JSON）にまとめて設定する。
ボット作成・編集APIで渡すことで、ボットごとに独立して制御できる。

---

## 設定場所

**APIリクエスト例（ボット作成）:**

```json
POST /api/v1/bots
{
  "name": "BTC MACD Bot",
  "exchange": "bitflyer",
  "symbol": "BTC/JPY",
  "trade_type": "spot",
  "strategy": "macd",
  "budget": 100000,
  "stop_loss_pct": 5.0,
  "strategy_params": {
    "interval_seconds": 300,
    "timeframe": "1h",
    "ohlcv_limit": 100,
    "fast": 12,
    "slow": 26,
    "signal": 9
  }
}
```

---

## 共通パラメータ（全戦略）

| パラメータ | 型 | デフォルト | 説明 |
|------------|----|-----------|------|
| `interval_seconds` | int | `60` | ボットの実行間隔（秒）。最小60秒。 |
| `timeframe` | str | `"1h"` | OHLCVのタイムフレーム |
| `ohlcv_limit` | int | `100` | 取得するOHLCVの本数（10〜500） |

### timeframe の選択肢

| 値 | 意味 | 向いている戦略 |
|----|------|---------------|
| `"1m"` | 1分足 | 高頻度（interval_seconds: 60） |
| `"5m"` | 5分足 | 短期（interval_seconds: 300） |
| `"15m"` | 15分足 | 短期〜中期（interval_seconds: 900） |
| `"1h"` | 1時間足 | 中期（interval_seconds: 3600） |
| `"4h"` | 4時間足 | 中長期（interval_seconds: 14400） |
| `"1d"` | 日足 | 長期（interval_seconds: 86400） |

> **推奨:** `timeframe` と `interval_seconds` は揃えること。
> 例：1時間足を使うなら interval_seconds: 3600（1時間ごとに実行）。

---

## ボットレベルのリスク管理パラメータ

ボット作成時のトップレベルフィールドで設定する（strategy_params外）。

| フィールド | 型 | デフォルト | 説明 |
|------------|----|-----------|------|
| `budget` | float | 必須 | 資金枠（円）。この金額を上限に発注する。 |
| `stop_loss_pct` | float | `5.0` | ポジションの含み損がこの%を超えたら自動決済。 |

---

## 戦略別パラメータ

### MACD戦略（`"strategy": "macd"`）

MACDラインがシグナルラインを上抜けで買い、下抜けで売り。

| パラメータ | 型 | デフォルト | 説明 |
|------------|----|-----------|------|
| `fast` | int | `12` | 短期EMA期間 |
| `slow` | int | `26` | 長期EMA期間 |
| `signal` | int | `9` | シグナル線（MACDのEMA）期間 |

**設定例（標準）:**
```json
{ "interval_seconds": 3600, "timeframe": "1h", "fast": 12, "slow": 26, "signal": 9 }
```

**設定例（短期・積極的）:**
```json
{ "interval_seconds": 300, "timeframe": "5m", "fast": 5, "slow": 13, "signal": 5 }
```

---

## runner の動作仕様

1. メインループは **60秒ごと** に全ボットをスキャン
2. 各ボットの `last_executed_at` と `interval_seconds` を比較
3. 経過時間 ≥ `interval_seconds` のボットのみ実行
4. 複数ボットが同時にrunningでも順次処理（競合なし）

```
runner（60秒ループ）
  ├─ BotA: interval=3600 → 前回から3600秒経過？ → 実行 or スキップ
  ├─ BotB: interval=300  → 前回から300秒経過？  → 実行 or スキップ
  └─ BotC: interval=86400 → 前回から86400秒経過？ → 実行 or スキップ
```

---

## 将来追加予定の戦略パラメータ

| 戦略 | 追加予定パラメータ |
|------|--------------------|
| RSI | `rsi_period`, `oversold`, `overbought` |
| グリッド | `grid_count`, `grid_range_pct`, `order_amount` |
| ボリンジャーバンド | `bb_period`, `bb_std`, `bb_squeeze_threshold` |
