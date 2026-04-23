from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import ChatLog

@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    # 管理画面の一覧に表示する項目
    list_display = ('created_at', 'user_message', 'session_id', 'has_image')
    # 右側にフィルタ機能を追加
    list_filter = ('created_at', 'session_id')
    # 検索機能を追加
    search_fields = ('user_message', 'ai_response')
    
    # 詳細画面で画像を表示する
    readonly_fields = ('image_preview',)

    def has_image(self, obj):
        # 画像がある場合はアイコンを表示
        return mark_safe("🖼️" if obj.file_url else "ー")
    has_image.short_description = "画像"

    def image_preview(self, obj):
        # 画像URLがあればクリック可能な画像を表示
        if obj.file_url:
            return mark_safe(f'<a href="{obj.file_url}" target="_blank"><img src="{obj.file_url}" style="max-width: 300px; height: auto; border-radius: 8px;"></a><br>クリックで拡大')
        return "なし"
    image_preview.short_description = "添付画像のプレビュー"