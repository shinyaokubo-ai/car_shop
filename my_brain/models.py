from django.db import models
from pgvector.django import VectorField  # 🌟 追加：ベクトルの箱を作るための部品

class ChatLog(models.Model):
    # ユーザーの入力（長文に対応）
    user_message = models.TextField(verbose_name="ユーザーの質問")
    
    # AIの回答（長文に対応）
    ai_response = models.TextField(verbose_name="AIの回答", blank=True, null=True)
    
    # GCSのファイルURL（画像などを送った場合）
    file_url = models.URLField(verbose_name="添付ファイルURL", max_length=500, blank=True, null=True)
    
    # 誰のチャットかを見分けるためのID
    session_id = models.CharField(max_length=100, verbose_name="セッションID", blank=True, null=True)
    
    # 作成日時（自動で現在時刻が入る）
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="送信日時")

    class Meta:
        verbose_name = "チャット履歴"
        verbose_name_plural = "チャット履歴一覧"
        ordering = ['-created_at'] # 新しい順に並べる

    def __str__(self):
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M')} - {self.user_message[:20]}..."
    
    # --- 🌟ここから新規追加！ AIの知識（ベクトル）の箱 ---
class KnowledgeChunk(models.Model):
    """AIの知識（文章と座標）を保存する専用の箱"""
    
    # 1. 座標の元になる「実際の文章（テキストの切れ端）」
    text_content = models.TextField()
    
    # 2. AIが検索するための「768個の数字の羅列（座標）」
    embedding = VectorField(dimensions=768)
    
    # 3. どのファイルから来たかのメモ（例: shinya_food_rules.txt）
    source_file = models.CharField(max_length=255)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.source_file}] {self.text_content[:20]}..."