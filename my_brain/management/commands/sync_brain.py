import os
import requests
from django.core.management.base import BaseCommand
from google.cloud import storage
from my_brain.models import KnowledgeChunk
from dotenv import load_dotenv

class Command(BaseCommand):
    help = 'GCSのテキストを読み込み、直接APIで座標化してNeonに保存する'

    def handle(self, *args, **kwargs):
        self.stdout.write("🌟 知識の同期（ベクトル化）を開始します...")
        
        load_dotenv()
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            self.stdout.write("❌ エラー: APIキーが見つかりません。.envファイルを確認してください。")
            return

        bucket_name = "car-shop-media-0709"
        folder_prefix = "brain_files/"
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=folder_prefix)

        KnowledgeChunk.objects.all().delete()
        self.stdout.write("古い記憶を整理しました。新しい記憶をインプットします。")

        for blob in blobs:
            if blob.name == folder_prefix or not blob.name.endswith('.txt'):
                continue

            try:
                text_data = blob.download_as_text(encoding='utf-8')
                chunks = [c.strip() for c in text_data.split('\n\n') if c.strip()]

                for chunk in chunks:
                    # 🌟 新時代の最強モデル「gemini-embedding-001」にアクセス！
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
                    payload = {
                        "model": "models/gemini-embedding-001",
                        "content": {"parts": [{"text": chunk}]},
                        "taskType": "RETRIEVAL_DOCUMENT",
                        "title": blob.name,
                        # 🌟 ここがプロの技！3072次元を、Neonの箱（768次元）に合わせて自動圧縮させる！
                        "outputDimensionality": 768
                    }
                    response = requests.post(url, json=payload)
                    
                    if response.status_code != 200:
                        self.stdout.write(f"❌ API通信エラー: {response.text}")
                        continue

                    embedding = response.json()['embedding']['values']

                    KnowledgeChunk.objects.create(
                        text_content=chunk,
                        embedding=embedding,
                        source_file=blob.name
                    )
                
                self.stdout.write(f"✅ 完了: {blob.name} ({len(chunks)}個の記憶ブロックに分割)")

            except Exception as e:
                self.stdout.write(f"❌ エラー ({blob.name}): {str(e)}")

        self.stdout.write("🎉 すべての知識のベクトル化とNeonへの保存が完了しました！")