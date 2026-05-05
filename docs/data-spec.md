# データ仕様

## 保存先

すべてのデータは **VPS上のPostgreSQL** に保存する。

```
VPS (Hetzner CAX11)
└── PostgreSQL
    ├── users           ユーザーアカウント
    ├── exchange_keys   取引所APIキー（暗号化）
    ├── bots            ボット設定・状態
    ├── positions       オープンポジション
    └── trades          取引履歴
```

---

## テーブル定義

### users

| カラム | 型 | 説明 |
|--------|-----|------|
| `id` | STRING (UUID) | PK |
| `email` | STRING(255) | ログインID。ユニーク |
| `hashed_password` | STRING(255) | bcryptハッシュ |
| `is_active` | BOOLEAN | アカウント有効フラグ |
| `created_at` | TIMESTAMP TZ | 作成日時 |

---

### exchange_keys

| カラム | 型 | 説明 |
|--------|-----|------|
| `id` | STRING (UUID) | PK |
| `user_id` | STRING | FK → users.id（CASCADE DELETE） |
| `exchange` | STRING(50) | 取引所識別子（例: `"bitflyer"`） |
| `api_key_encrypted` | STRING(512) | Fernet暗号化済みAPIキー |
| `api_secret_encrypted` | STRING(512) | Fernet暗号化済みAPIシークレット |
| `created_at` | TIMESTAMP TZ | 登録日時 |

**セキュリティ:** APIキーは `ENCRYPTION_KEY`（環境変数）を使ってFernet対称暗号で保存。平文では保存しない。

---

### bots

| カラム | 型 | 説明 |
|--------|-----|------|
| `id` | STRING (UUID) | PK |
| `user_id` | STRING | FK → users.id（CASCADE DELETE） |
| `name` | STRING(100) | ボット名 |
| `exchange` | STRING(50) | 取引所（例: `"bitflyer"`） |
| `symbol` | STRING(20) | 通貨ペア（例: `"BTC/JPY"`） |
| `trade_type` | STRING(10) | `"spot"` or `"futures"` |
| `strategy` | STRING(50) | 戦略名（例: `"macd"`） |
| `strategy_params` | JSON | 戦略・実行パラメータ（詳細は [bot-params.md](./bot-params.md)） |
| `budget` | FLOAT | 資金枠（円） |
| `stop_loss_pct` | FLOAT | ストップロス閾値（%）。デフォルト5.0 |
| `status` | STRING(20) | `"running"` / `"stopped"` / `"error"` |
| `error_message` | STRING(500) | エラー時のメッセージ |
| `last_executed_at` | TIMESTAMP TZ | 最終実行日時（interval判定に使用） |
| `created_at` | TIMESTAMP TZ | 作成日時 |

---

### positions

ボットごとに最大1件。ポジションクローズ時に削除される。

| カラム | 型 | 説明 |
|--------|-----|------|
| `id` | STRING (UUID) | PK |
| `bot_id` | STRING | FK → bots.id（CASCADE DELETE）。ユニーク |
| `side` | STRING(10) | `"long"` or `"short"` |
| `amount` | FLOAT | 保有数量 |
| `entry_price` | FLOAT | エントリー価格 |
| `opened_at` | TIMESTAMP TZ | ポジション開始日時 |

---

### trades

約定履歴。買い・売りの両方を記録。損益（PnL）は売り時のみ記録。

| カラム | 型 | 説明 |
|--------|-----|------|
| `id` | STRING (UUID) | PK |
| `bot_id` | STRING | FK → bots.id（CASCADE DELETE） |
| `exchange_order_id` | STRING(100) | 取引所側の注文ID |
| `side` | STRING(10) | `"buy"` or `"sell"` |
| `symbol` | STRING(20) | 通貨ペア |
| `amount` | FLOAT | 約定数量 |
| `price` | FLOAT | 約定価格 |
| `pnl` | FLOAT | 損益（売り時のみ）。`(売値 - 買値) × 数量` |
| `executed_at` | TIMESTAMP TZ | 約定日時 |

---

## データの関係

```
users
 ├── exchange_keys（1対多）
 └── bots（1対多）
      ├── positions（1対1）
      └── trades（1対多）
```

- ユーザー削除 → exchange_keys・bots が CASCADE DELETE
- ボット削除 → positions・trades が CASCADE DELETE

---

## 永続化されないデータ

以下はDBに保存せず、都度取引所APIから取得する：

| データ | 取得元 |
|--------|--------|
| 現在価格（ticker） | 取引所REST API（ccxt） |
| OHLCVデータ | 取引所REST API（ccxt） |
| 残高（balance） | 取引所REST API（ccxt） |

---

## セキュリティ

| 対象 | 方式 |
|------|------|
| パスワード | bcrypt（ハッシュ化、平文保存なし） |
| 取引所APIキー | Fernet対称暗号（AES-128-CBC）。`ENCRYPTION_KEY` 環境変数で管理 |
| 認証トークン | JWT（HS256）。`SECRET_KEY` 環境変数で管理 |
| DB接続 | VPS内部通信のみ（外部に公開しない） |
