import os
import json
import uuid
import requests
from django.utils import timezone
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from google.cloud import storage
import google.generativeai as genai
from pgvector.django import CosineDistance
from dotenv import load_dotenv

# モデルのインポート
from .models import ChatLog, KnowledgeChunk

# 初期設定：.envから設定を読み込む
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

def chat_interface(request):
    """チャット画面を表示する"""
    return render(request, 'my_brain/chat.html')

@csrf_exempt
def api_chat(request):
    """SSE対応：ベクトル検索（RAG）を搭載した爆速AIチャットAPI"""
    if request.method == "POST":
        try:
            user_message = ""
            uploaded_file = None
            public_url = ""

            if "application/json" in request.content_type:
                data = json.loads(request.body.decode('utf-8'))
                user_message = data.get("message", "")
            else:
                user_message = request.POST.get("message", "")
                if request.FILES:
                    uploaded_file = list(request.FILES.values())[0]

            if not user_message and not uploaded_file:
                user_message = "（メッセージなし）"

            if uploaded_file:
                client = storage.Client()
                bucket = client.bucket("car-shop-media-0709")
                ext = os.path.splitext(uploaded_file.name)[1]
                filename = f"chat_uploads/{timezone.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
                blob = bucket.blob(filename)
                blob.upload_from_file(uploaded_file, content_type=uploaded_file.content_type)
                public_url = f"https://storage.googleapis.com/car-shop-media-0709/{filename}"
                uploaded_file.seek(0)

            # ----------------------------------------------------
            # 🌟 3. ベクトル検索（RAG）
            # ----------------------------------------------------
            rag_context = ""
            if user_message:
                embed_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
                embed_payload = {
                    "model": "models/gemini-embedding-001",
                    "content": {"parts": [{"text": user_message}]},
                    "taskType": "RETRIEVAL_QUERY",
                    "outputDimensionality": 768
                }
                
                embed_res = requests.post(embed_url, json=embed_payload)
                if embed_res.status_code != 200:
                    raise Exception(f"Google Embedding API Error: {embed_res.text}")
                
                query_vector = embed_res.json()['embedding']['values']

                similar_chunks = KnowledgeChunk.objects.annotate(
                    distance=CosineDistance('embedding', query_vector)
                ).order_by('distance')[:3]
                
                rag_context = "\n---\n".join([c.text_content for c in similar_chunks])

            # ----------------------------------------------------
            # 🌟 4. 人格設定
            # ----------------------------------------------------
            system_instruction = f"""
            あなたは「慎也」の分身です。論理的かつ情熱的、そして職人的なトーンで回答してください。
            あなたはワイズプロジェクト市原でポルシェのテクニカル・PRサポートを担うプロであり、
            同時に南インド料理の真髄を極める料理人でもあります。

            【制約事項】
            1. 以下の【参考資料】に答えがある場合は、それを最優先で回答に反映させてください。
            2. 【参考資料】にない場合でも、自分の知識で自信を持って答えてください。
            3. 常に「引き算」を意識し、無駄な解説は省いて核心を突く短めの回答を心がけてください。

            【参考資料】
            {rag_context}
            """
            
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_instruction
            )
            
            prompt_parts = []
            if user_message: prompt_parts.append(user_message)
            if uploaded_file:
                prompt_parts.append({"mime_type": uploaded_file.content_type, "data": uploaded_file.read()})
            
            # ----------------------------------------------------
            # 🌟 5. ストリーミング生成（空っぽの連絡をスルーする処理を追加！）
            # ----------------------------------------------------
            response = model.generate_content(prompt_parts, stream=True)
            
            def stream_generator():
                full_text = ""
                try:
                    for chunk in response:
                        try:
                            # テキストを取り出してみて、エラーが出たら無視する
                            text_data = chunk.text
                            if text_data:
                                full_text += text_data
                                yield f"data: {json.dumps({'text': text_data})}\n\n"
                        except Exception:
                            # 最後の「終了コード」などでテキストが無い場合はここを通過して無視する
                            continue
                except Exception as e:
                    yield f"data: {json.dumps({'text': f'[AI生成エラー: {str(e)}]'})}\n\n"
                finally:
                    ChatLog.objects.create(
                        user_message=user_message,
                        ai_response=full_text,
                        file_url=public_url
                    )

            return StreamingHttpResponse(stream_generator(), content_type='text/event-stream')
            
        except Exception as e:
            error_msg = json.dumps({"text": f"システムエラーが発生しました。\n({str(e)})"})
            return StreamingHttpResponse((f"data: {error_msg}\n\n" for _ in range(1)), content_type='text/event-stream')
            
    return JsonResponse({"error": "不正なリクエストです"}, status=405)