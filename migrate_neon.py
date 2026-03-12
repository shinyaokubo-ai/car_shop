import os
import django
from django.core.management import call_command

# 🔑 ここに見つけた鍵（URL）を貼り付けます！
# 例: 'postgresql://shinya:パスワード@ep-cool-sun-12345.pooler.supabase.com:5432/postgres'
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_rc2lj6yutPKS@ep-purple-mud-a1zso0n2-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

# Djangoの準備
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("🚀 Neon（本番の金庫）に接続中...")
print("🔨 新しい装備用の仕切りを作成しています...")

# 遠隔でmigrate（工事）を実行！
call_command('migrate')

print("✅ Neonの工事がすべて完了しました！")