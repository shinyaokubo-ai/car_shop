from django.contrib import admin
from .models import ChatLog

@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    # 管理画面の一覧に表示する項目
    list_display = ('created_at', 'user_message', 'session_id')
    # 右側にフィルタ機能（日付などで絞り込み）を追加
    list_filter = ('created_at', 'session_id')
    # 検索機能を追加
    search_fields = ('user_message', 'ai_response')