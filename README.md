# Weather Warning Checker for Japan

気象庁の警報・注意報を監視し、変更があった場合にGmailで通知するシステムです。

## 特徴

- 🔄 **自動スケジュール実行**: 10分間隔で警報・注意報をチェック
- 📧 **重複通知防止**: 状態変更時のみ通知（発表/継続/解除）
- 🐳 **Docker対応**: コンテナ化により簡単デプロイ
- 🔁 **自動再起動**: コンテナ停止時も自動復旧
- 💾 **データ永続化**: SQLiteで警報履歴を管理

## クイックスタート

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd docker-weather-checker
```

### 2. 環境変数の設定

```bash
cp .env.example .env
```

`.env`ファイルを編集してGmail認証情報を設定:

```env
GMAIL_APP_PASS=your_app_password
GMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com
EMAIL_BCC=bcc@example.com
```

### 3. Docker起動

```bash
docker-compose up -d
```

### 4. ログ確認

```bash
docker-compose logs -f
```

## ディレクトリ構成

```
docker-weather-checker/
├── app/                    # アプリケーションコード
│   ├── scheduler.py       # メインスケジューラー
│   ├── weather.py         # 気象情報チェックロジック
│   ├── remove_data.py     # データクリーンアップ
│   └── ...
├── data/                   # 永続化データ（自動生成）
│   ├── db/                # SQLiteデータベース
│   ├── xml/               # XMLキャッシュ
│   └── deleted/           # 削除済みXMLファイル
├── logs/                   # ログファイル（自動生成）
├── .env                    # 環境変数（要作成）
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## スケジュール

- **気象警報チェック**: 10分おき
- **データクリーンアップ**: 毎日1:00（30日以上前のデータを削除）

## 監視対象地域の変更

`app/weather.py`の`run_weather_check()`関数を編集:

```python
def run_weather_check():
    mygmail = Gmail(GMAIL_FROM, GMAIL_APP_PASS, EMAIL_TO, EMAIL_BCC)
    feed = JMAFeed()

    # 監視対象を追加
    printJMAwarningsInfo(feed, '静岡地方気象台', ['裾野市','御殿場市'], mygmail)
    printJMAwarningsInfo(feed, '東京管区気象台', ['千代田区'], mygmail)

    del feed
```

変更後、コンテナを再ビルド:

```bash
docker-compose up -d --build
```

## Docker操作コマンド

```bash
# 起動
docker-compose up -d

# 停止
docker-compose down

# 再起動
docker-compose restart

# ログ表示（リアルタイム）
docker-compose logs -f

# ログ表示（最新100行）
docker-compose logs --tail=100

# コンテナ状態確認
docker-compose ps

# コンテナ内でコマンド実行
docker-compose exec weather-checker bash
```

## ローカル開発

Dockerを使わずにローカルで開発する場合:

```bash
# 仮想環境作成
python -m venv venv310
source venv310/bin/activate

# 依存関係インストール
pip install -r app/requirements.txt

# .env設定（Docker用パスは不要）
cp .env.example .env

# データベース初期化
python app/models.py

# スケジューラー起動
python app/scheduler.py
```

## トラブルシューティング

### コンテナが起動しない

```bash
# ログを確認
docker-compose logs

# .envファイルの存在確認
cat .env

# データディレクトリ作成
mkdir -p data/db data/xml data/deleted logs
```

### データベースエラー

```bash
# データベースを再作成
docker-compose exec weather-checker python models.py
```

### 通知が来ない

1. `.env`ファイルのGmail設定を確認
2. Gmailアプリパスワードが正しいか確認
3. ログでエラーを確認: `docker-compose logs -f`

## 技術スタック

- **Python 3.10**: メイン言語
- **schedule**: タスクスケジューリング
- **SQLAlchemy**: ORMフレームワーク
- **requests**: HTTP通信
- **Docker**: コンテナ化
- **SQLite**: データベース

## ライセンス

[MITライセンス](LICENSE)

