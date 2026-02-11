import os
from pathlib import Path
import dj_database_url

# ベースディレクトリの設定
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全のため、Render上では環境変数から取得（なければ仮の値を設定）
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key')

# デバッグモード（本番ではFalseにするのが一般的ですが、今は動作確認のためTrueでもOK）
DEBUG = True

ALLOWED_HOSTS = ['*'] # Renderのドメインを許可

# --- 1. アプリケーション定義 (順番が非常に重要です) ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',  # ← ここにこの1行を追加！
    # Cloudinary用（staticfilesより上に書く）
    'cloudinary_storage',
    'django.contrib.staticfiles',
    # Cloudinary本体
    'cloudinary',
    # 慎也さんのアプリ
    'cars',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Whitenoise用（デザイン崩れ防止：SecurityMiddlewareのすぐ下）
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
                # ここはDjango標準の4つだけ！(アプリ名は入れない)
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- 2. データベース設定 (Neon PostgreSQL用) ---
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL')
    )
}

# パスワードバリデーション
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 言語・タイムゾーン設定
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

# --- 3. 静的ファイルと画像保存の設定 (Cloudinary / Whitenoise) ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Cloudinaryの接続設定（Renderの環境変数から取得）
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUD_API_KEY'),
    'API_SECRET': os.environ.get('CLOUD_API_SECRET'),
}

# 画像とデザインファイルの保存先を統一
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'