# 1. 公式の軽量なPythonイメージをベースにする
FROM python:3.10-slim

# 2. コンテナ内の環境変数を設定（Pythonがログを即時出力できるようにする）
ENV PYTHONUNBUFFERED=1

# 3. コンテナ内の作業ディレクトリを決定
WORKDIR /app

# 4. 必要なシステムパッケージのインストール（pgvectorやpsycopg2のビルドに必要なツール）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 5. requirements.txtをコピーして依存ライブラリをインストール
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 6. プロジェクトの全ソースコードをコンテナ内にコピー
COPY . /app/

# 7. Cloud Runが使用するポート（通常は8080）を開放
EXPOSE 8080

# 8. Gunicornを使ってDjangoを起動（プロジェクト名が「car_shop」の場合）
# ※もしwsgiを呼び出す大元のフォルダ名が「car_shop」でなければ、適宜変更してください。
CMD ["gunicorn", "--bind", ":8080", "--workers", "2", "car_shop.wsgi:application"]