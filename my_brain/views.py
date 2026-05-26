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
from django.db.models import Q

# 🌟 既存のcarsプロジェクトからモデルをインポート
from cars.models import Car

# 初期設定
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# ----------------------------------------------------
# 🌟 1. AIが使う「道具（在庫検索関数）」を定義
# ----------------------------------------------------
def search_inventory(model_query: str = None, max_price: int = None):
    """
    ワイズプロジェクト市原の最新在庫車両をデータベースから直接検索します。
    
    Args:
        model_query: 車種名やキーワード（例：「マカン」「911」「4WD」など）
        max_price: 支払総額の最大予算（単位：円）
    """
    # 公開中かつ在庫ありの車両に絞り込む
    qs = Car.objects.filter(is_published=True, is_sold_out=False)
    
    if model_query:
        qs = qs.filter(
            Q(title__icontains=model_query) | 
            Q(comment__icontains=model_query) |
            Q(equipment_custom__icontains=model_query)
        )
    
    if max_price:
        qs = qs.filter(price_total__lte=max_price)
    
    results = []
    # 最新の5件まで取得
    for car in qs.order_by('-created_at')[:5]:
       
        # urls.py が <int:pk>/ なので、car.pk (ID番号) を使うのが正解！
       # urls.py が <int:pk>/ なので、car.pk (ID番号) を使うのが正解！
        detail_url = f"https://car-shop-app-572463964631.asia-northeast1.run.app/cars/{car.pk}/"
        
        results.append({
            "車名": car.title,
            "総額": f"{car.price_total:,}円",
            "年式": car.registration_year,
            "走行距離": car.mileage,
            "色": car.body_color,
            "URL": detail_url,
            "特徴": car.comment[:50] + "..."
        })
    if not results:
        return "現在、ご希望の条件に合う車両は在庫にございません。"
    
    return results

def chat_interface(request):
    return render(request, 'my_brain/chat.html')

@csrf_exempt
def api_chat(request):
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

            if uploaded_file:
                client = storage.Client()
                bucket = client.bucket("car-shop-media-0709")
                ext = os.path.splitext(uploaded_file.name)[1]
                filename = f"chat_uploads/{timezone.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
                blob = bucket.blob(filename)
                blob.upload_from_file(uploaded_file, content_type=uploaded_file.content_type)
                public_url = f"https://storage.googleapis.com/car-shop-media-0709/{filename}"
                uploaded_file.seek(0)

            # 🌟 RAG（ベクトル検索）
            rag_context = ""
            if user_message:
                embed_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
                embed_payload = {"model": "models/gemini-embedding-001", "content": {"parts": [{"text": user_message}]}, "taskType": "RETRIEVAL_QUERY"}
                embed_res = requests.post(embed_url, json=embed_payload)
                if embed_res.status_code == 200:
                    query_vector = embed_res.json()['embedding']['values']
                    similar_chunks = KnowledgeChunk.objects.annotate(distance=CosineDistance('embedding', query_vector)).order_by('distance')[:3]
                    rag_context = "\n---\n".join([c.text_content for c in similar_chunks])

            # ----------------------------------------------------
            # 🌟 2. 人格設定 & Function Callingの準備
            # ----------------------------------------------------
            system_instruction = f"""
            あなたは「慎也」の分身です。論理的かつ情熱的、職人的トーンで回答してください。
            ワイズプロジェクト市原のプロであり、南インド料理の達人でもあります。

            【重要】在庫状況を聞かれたら、必ず提供されたツール（search_inventory）を使って最新のDB情報を確認し、その結果を元に案内してください。
            回答の最後には、必ず詳細ページのURLを添えて、お客様を誘導してください。

            【参考資料（RAG）】
            {rag_context}
            """
            
            # 道具箱を登録
            tools = [search_inventory]

            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash", # または gemini-2.0-flash-exp など
                system_instruction=system_instruction,
                tools=tools
            )
            
            # Function Callingを自動処理するチャットセッションを開始
            chat_session = model.start_chat(enable_automatic_function_calling=True)
            
            prompt_parts = []
            if user_message: prompt_parts.append(user_message)
            if uploaded_file:
                prompt_parts.append({"mime_type": uploaded_file.content_type, "data": uploaded_file.read()})
            
            # 🌟 ストリーミング生成
            response = chat_session.send_message(prompt_parts, stream=True)
            
            def stream_generator():
                full_text = ""
                try:
                    for chunk in response:
                        text_data = chunk.text
                        if text_data:
                            full_text += text_data
                            yield f"data: {json.dumps({'text': text_data})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'text': f'[AI生成エラー: {str(e)}]'})}\n\n"
                finally:
                    ChatLog.objects.create(user_message=user_message, ai_response=full_text, file_url=public_url)

            return StreamingHttpResponse(stream_generator(), content_type='text/event-stream')
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "不正なリクエスト"}, status=405)