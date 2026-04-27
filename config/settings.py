import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv  # 🌟 追加：.envファイルを読み込む部品

# ベースディレクトリ
BASE_DIR = Path(__file__).resolve().parent.parent

# 🌟 追加：一番最初に .env ファイルを読み込む（ここでNeonのURLを確実にゲット！）
load_dotenv(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key')

DEBUG = True # 開発中はTrueでOK

ALLOWED_HOSTS = ['*']

# --- アプリケーション定義 ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'storages',      # Google Cloud Storageを使うための必須ライブラリ
    'cars',
    'ai_assist',
    'my_brain',      # 今回作るアプリ
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # 静的ファイル用
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- データベース設定 ---
# 🌟 load_dotenv のおかげで、確実にNeon（DATABASE_URL）へ繋がります！
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
    )
}

LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

# --- 静的ファイル・画像保存 (Google Cloud Storage / Whitenoise) ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# GCPの認証鍵（gcp-key.json）を読み込む
GCP_KEY_PATH = os.path.join(BASE_DIR, 'gcp-key.json')
if os.path.exists(GCP_KEY_PATH):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GCP_KEY_PATH

# 開発環境（ローカル）か本番環境（Cloud Run）かを判定
IS_PRODUCTION = os.environ.get('GOOGLE_CLOUD_PROJECT') is not None

if IS_PRODUCTION or os.path.exists(GCP_KEY_PATH):
    # --- 本番環境 または ローカル（鍵あり）の場合：Google Cloud Storageを使用 ---
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    GS_BUCKET_NAME = 'car-shop-media-0709'  
    MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/"
    
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }
else:
    # --- ローカル環境（鍵なし）の場合：パソコン内に保存 ---
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- セキュリティ設定（Cloud RunのURLを許可する） ---
CSRF_TRUSTED_ORIGINS = [
    'https://car-shop-app-572463964631.asia-northeast1.run.app',
]

# キャッシュの設定（ローカルメモリを使用）
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'shinya-brain-cache',
    }
}

# 🌟 緊急レスキュー：本番環境の画像をGCS（バケット）に強制固定！
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = 'car-shop-media-0709'
MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/"
GS_QUERYSTRING_AUTH = False  # 👈 🌟これです！！「余計な鍵（署名）を作らなくていいよ」という命令
STORAGES["default"] = {
    "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
}