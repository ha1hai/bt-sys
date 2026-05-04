# インフラ構成 比較ドキュメント

対象規模：ユーザー数 最大5名、ボット数 数十程度

---

## 推奨構成（現時点）

**VPS（Hetzner CAX11）+ PostgreSQL + Cloudflare Pages**

```
[フロントエンド]  Cloudflare Pages         → 無料
[CDN]            Cloudflare CDN            → 無料
[API + ボット]   VPS上のPython/FastAPI     → €3.79/月
[DB]             VPS上のPostgreSQL         → 無料（VPS込み）
[認証]           自前JWT or Cognito        → 無料
```

**月額目安：€3.79〜$6/月（固定）**

---

## 構成別 総合比較

| | VPS (Hetzner) | Lambda cron | Cloud Run |
|--|--------------|------------|-----------|
| **月額** | ◎ €3.79固定 | △ $0〜$5（設計次第）/ 設計ミスで$100〜$200 | ○ $10〜$40 |
| **Python依存パッケージ** | ◎ apt-get + pip で自由 | △ ccxt/ta-libは工夫必要 | ◎ Dockerで解決 |
| **運用・監視** | △ 自前構築 | ◎ CloudWatch完備 | ○ Cloud Logging |
| **DB接続** | ◎ ローカル接続（最速） | ◎ DynamoDB AWS内部通信 | △ クロスクラウド |
| **スケーリング** | △ 手動 | ○ 自動 | ◎ 柔軟・自動 |
| **構成のシンプルさ** | ◎ ssh + systemd | △ IAM/SAM学習コスト高い | ○ Dockerfile + gcloud |
| **将来の移行性** | ◎ 制約なし | △ ベンダーロックイン | ○ Kubernetes移行可 |

**VPSを推奨する理由：**
- 月€3.79固定でコスト予測が容易
- Python依存パッケージ（ccxt、pandas、ta-lib）を制約なくインストール可能
- PostgreSQLをVPS上に置けばDBの外部依存なし
- systemdでボットを常時稼働させるだけでシンプル
- 監視スクリプトを1本書けば障害復旧も自動化可能

---

## VPS 選定比較

| サービス | プラン | 月額 | スペック | 特徴 |
|----------|--------|------|----------|------|
| **Hetzner CAX11** | ARM | €3.79 | 2vCPU, 4GB RAM, 40GB SSD | ◎ 最安・高コスパ。日本からの遅延は許容範囲 |
| **Hetzner CX22** | x86 | €3.79 | 2vCPU, 4GB RAM, 40GB SSD | ○ x86互換性が必要な場合 |
| **Vultr Cloud Compute** | Regular | $6 | 1GB RAM, 25GB SSD | △ Hetznerよりスペック低い |
| **Vultr Tokyo** | Regular | $6 | 1GB RAM | ○ 東京リージョンで低レイテンシー |
| **Contabo VPS S** | - | €4.50 | 4vCPU, 8GB RAM, 100GB SSD | ○ スペック高いが初期費用あり |

**推奨：Hetzner CAX11**（コスパ最良）またはレイテンシー優先なら**Vultr Tokyo**

---

## フロントエンド：Cloudflare Pages

| 項目 | 内容 |
|------|------|
| **料金** | 無料（帯域幅無制限、ビルド月500回） |
| **CDN** | Cloudflareグローバルネットワーク自動配信 |
| **HTTPS** | 自動（カスタムドメイン対応） |
| **API接続** | VPSのFastAPIエンドポイントをCORSで呼び出し |
| **Vercelとの比較** | 帯域無制限・ビルド500回/月でVercel（100回）より有利 |

---

## データベース：PostgreSQL on VPS

VPS上にPostgreSQLを立てることでDBの外部依存をゼロにする。

| 用途 | テーブル設計方針 |
|------|----------------|
| ユーザー管理 | users テーブル（メール、ハッシュ化パスワード、APIキー暗号化） |
| ボット状態管理 | bots テーブル（status, strategy, position, last_executed） |
| 取引履歴 | trades テーブル（時系列、ボットID、損益） |
| 戦略設定 | strategies テーブル（パラメータJSON） |

DynamoDBと異なり集計クエリ（日次損益、勝率計算）がSQLで直接実行可能。

---

## 認証方式

| 方式 | 月額 | 特徴 |
|------|------|------|
| **自前JWT（推奨）** | $0 | FastAPIで実装。5名規模では十分 |
| **Cognito** | $0（5名） | AWSに依存。過剰かもしれない |
| **Supabase Auth** | $0（無料枠） | PostgreSQLとセット利用可。ただしIPv6問題あり |

**推奨：自前JWT**（外部依存なし、VPS内で完結）

---

## IPv6問題について

本構成（VPS + PostgreSQL）はIPv6問題なし。VPSはIPv4アドレス付きで提供される。

| サービス | IPv6対応 | 備考 |
|----------|----------|------|
| **Hetzner VPS** | ○ | IPv4込み。追加費用なし |
| **Vultr VPS** | ○ | IPv4込み。追加費用なし |
| **Supabase** | △ | 直接接続はIPv6のみ。IPv4は+$4/月 |
| **Railway** | ○ | 内部接続なら問題なし |
| **AWS Lambda → DynamoDB** | ○ | AWS内部通信 |

---

## コスト試算（月額）

### 推奨構成：VPS + Cloudflare Pages

| コンポーネント | サービス | 費用 |
|---------------|----------|------|
| API + ボット実行 + DB | Hetzner CAX11 | €3.79 |
| フロントエンド | Cloudflare Pages | $0 |
| 通知（Discord/LINE） | 各無料枠 | $0 |
| ドメイン（任意） | Cloudflare Registrar | $8〜$15/年 |
| **合計** | | **€3.79/月（約$4）** |

### 比較：Lambda + DynamoDB + Cloudflare Pages

| コンポーネント | サービス | 費用 |
|---------------|----------|------|
| ボット実行 | Lambda + EventBridge | $0（1スケジュール設計厳守） |
| API | Lambda + API Gateway | $0（無料枠内） |
| DB | DynamoDB | $0（低頻度設計） |
| 認証 | Cognito | $0 |
| フロントエンド | Cloudflare Pages | $0 |
| **合計** | | **$0〜$5/月**（設計制約が多い） |

### 将来拡張時（VPS構成）

| コンポーネント | サービス | 費用 |
|---------------|----------|------|
| VPS増強 | Hetzner CX32 | €11.10 |
| フロントエンド | Cloudflare Pages | $0 |
| **合計** | | **€11/月程度** |

---

## コスト削減の設計方針

1. **VPS上にAPI・ボット・DBをすべて同居**
   - 外部サービス依存をゼロにしてコスト固定化

2. **フロントはCloudflare Pages（無料・帯域無制限）**
   - Vercelより帯域・ビルド回数の制限が緩い

3. **バックテストはオンデマンド実行**
   - APIリクエスト時のみ実行し、常時リソースを消費しない設計

4. **Redisは不使用**
   - PostgreSQLのステータス管理で代替

5. **監視はシンプルに**
   - systemdによる自動再起動 + UptimeRobot（無料）で死活監視
