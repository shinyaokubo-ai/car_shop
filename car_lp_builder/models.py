from django.db import models
import uuid

class CarListing(models.Model):
    """
    1台の車＝1つの特設LPを管理するモデル。
    このIDが、そのまま「YouTubeのような公開URL」になる。
    """
    # 1. 自動発行されるURLのID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 2. 車の基本情報
    car_name = models.CharField(max_length=255, verbose_name="車種名 (例: Porsche 911 Carrera)")
    
    # 3. 画像のURLリスト
    hero_images = models.JSONField(default=list, verbose_name="LP用メイン画像URLリスト")
    
    # 4. Gemini(RAG)が生成した「物語」
    generated_story = models.TextField(verbose_name="AI生成ストーリー", blank=True, null=True)
    
    # 5. ステータス管理
    STATUS_CHOICES = (
        ('DRAFT', '下書き（AI処理中・確認待ち）'),
        ('PUBLISHED', '公開中（LPとしてアクセス可能）'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    # 6. 【重要】my_brainアプリのChatLogと紐付ける！
    # （別アプリのモデルでも 'アプリ名.モデル名' で繋ぐことができます）
    source_chat = models.ForeignKey('my_brain.ChatLog', on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "車両LPデータ"
        verbose_name_plural = "車両LPデータ一覧"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.status}] {self.car_name} (ID: {self.id})"