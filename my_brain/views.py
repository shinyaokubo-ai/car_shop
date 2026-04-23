import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from google.cloud import storage
import google.generativeai as genai

# 🌟 追加：先ほど作ったデータベースの箱（モデル）を読み込む
from .models import ChatLog

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# 🌟 追加：画面を表示するための関数（これが消えていたためエラーになっていました！）
def chat_interface(request):
    return render(request, 'my_brain/chat.html')

def get_shinya_knowledge():
    """GCSから知識を自動取得。無関係なファイルを読み込まないようフィルタリングも可能"""
    knowledge = cache.get("shinya_multi_knowledge")
    
    if not knowledge:
        BUCKET_NAME = "car-shop-media-0709"
        FOLDER_PREFIX = "brain_files/"
        
        try:
            client = storage.Client()
            bucket = client.bucket(BUCKET_NAME)
            
            media_parts = []
            text_data = ""
            
            blobs = bucket.list_blobs(prefix=FOLDER_PREFIX)
            
            for blob in blobs:
                if blob.name == FOLDER_PREFIX or blob.name.endswith('/'):
                    continue
                
                name_lower = blob.name.lower()
                
                # テキストファイル読み込み
                if name_lower.endswith('.txt'):
                    text_data += blob.download_as_text() + "\n\n"
                    continue
                
                # 画像・PDF読み込み
                mime_type = None
                if name_lower.endswith(('.jpg', '.jpeg')):
                    mime_type = "image/jpeg"
                elif name_lower.endswith('.png'):
                    mime_type = "image/png"
                elif name_lower.endswith('.pdf'):
                    mime_type = "application/pdf"
                    
                if mime_type:
                    media_parts.append({
                        "mime_type": mime_type,
                        "data": blob.download_as_bytes()
                    })
            
            knowledge = {
                "text": text_data,
                "media_parts": media_parts
            }
            cache.set("shinya_multi_knowledge", knowledge, 3600)
            
        except Exception as e:
            print("【GCSエラー発生】", str(e))
            return None
            
    return knowledge

@csrf_exempt
def api_chat(request):
    if request.method == "POST":
        try:
            # 🌟修正：どんな形式で送られてきても絶対に受け取る「最強の入り口」
            user_message = ""
            try:
                if request.body:
                    data = json.loads(request.body)
                    user_message = data.get("message", "")
            except json.JSONDecodeError:
                # JSON形式じゃなかった場合（画像添付など）はこっちで受け取る
                user_message = request.POST.get("message", "")

            # 空っぽの場合はダミー文字を入れる（DBエラー防止）
            if not user_message:
                user_message = "（メッセージなし）"

            knowledge = get_shinya_knowledge()
            if not knowledge:
                return JsonResponse({"reply": "記憶にアクセスできないな。設定を確認してくれ。"})

            # ★ 喋りすぎ防止の制約
            system_instruction = f"""
            あなたは「慎也」の分身です。以下のこだわりを信念として持っています。
            
            【制約事項】
            1. 慎也本人のようなトーン（論理的かつ情熱的）で短めに答えてください。
            2. 質問に直接関係がない限り、提供された知識（ファイルの内容）を長々と解説しないでください。
            3. ファイル内に答えがない場合は、自分の知識で答えて構いません。
            4. 常に「引き算」を意識し、簡潔に核心を突いてください。

            【慎也のこだわり】
            {knowledge["text"]}
            """
            
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash", # 最新安定版を使用
                system_instruction=system_instruction
            )
            
            prompt_parts = [user_message] + knowledge["media_parts"]
            response = model.generate_content(prompt_parts)
            
            # 🌟🌟 データベース（ChatLog）に会話を保存する！ 🌟🌟
            from .models import ChatLog
            ChatLog.objects.create(
                user_message=user_message,
                ai_response=response.text
            )
            
            return JsonResponse({"reply": response.text})
            
        except Exception as e:
            # 万が一エラーが起きても原因がわかるように出力
            print(f"【AIチャットエラー】{str(e)}")
            return JsonResponse({"error": f"システムエラー: {str(e)}"}, status=500)
            
    return JsonResponse({"error": "不正なリクエストです"}, status=405)