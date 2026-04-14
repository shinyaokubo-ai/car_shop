import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from google.cloud import storage
import google.generativeai as genai

# Geminiの設定
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def get_shinya_knowledge():
    """GCSの brain_files フォルダ内の【テキスト】と【画像/PDF】をすべて自動取得する"""
    knowledge = cache.get("shinya_multi_knowledge")
    
    if not knowledge:
        BUCKET_NAME = "car-shop-media-0709"
        FOLDER_PREFIX = "brain_files/"
        
        try:
            # 認証：ローカル(json鍵)と本番(標準権限)を自動切り替え
            if os.path.exists('gcp-key.json'):
                client = storage.Client.from_service_account_json('gcp-key.json')
            else:
                client = storage.Client()

            bucket = client.bucket(BUCKET_NAME)
            
            media_parts = []
            text_data = ""
            
            # フォルダ内の全ファイルをリストアップ
            blobs = bucket.list_blobs(prefix=FOLDER_PREFIX)
            
            for blob in blobs:
                if blob.name == FOLDER_PREFIX:
                    continue
                    
                name_lower = blob.name.lower()
                
                # テキストファイル(.txt)を見つけた場合
                if name_lower.endswith('.txt'):
                    text_data += blob.download_as_text() + "\n\n"
                    continue
                
                # 画像やPDFを見つけた場合
                mime_type = None
                if name_lower.endswith('.jpg') or name_lower.endswith('.jpeg'):
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
            
            print(f"【GCS完全自動読み込み成功！】取得: {len(media_parts)}件, テキスト取得完了")
            # 1時間キャッシュ（頻繁な通信を避けて爆速にする）
            cache.set("shinya_multi_knowledge", knowledge, 3600)
            
        except Exception as e:
            print("【GCSエラー発生】", str(e))
            return None
            
    return knowledge

def chat_interface(request):
    """チャット画面の表示"""
    return render(request, 'my_brain/chat.html')

@csrf_exempt
def api_chat(request):
    """チャット送信API（直接のファイルアップロードにも対応）"""
    if request.method == "POST":
        try:
            # 💡 【重要】JSONではなくFormDataとしてデータを受け取る
            user_message = request.POST.get("message", "")
            uploaded_file = request.FILES.get("file") # 画面からアップされたファイル
            
            knowledge = get_shinya_knowledge()
            
            if not knowledge:
                return JsonResponse({"reply": "現在、記憶ファイル（GCS）にアクセスできません。"})

            # 人格設定
            system_instruction = f"""
            あなたは「慎也」の分身です。以下のこだわりを自分の信念として持ち、
            質問に対して慎也本人のようなトーン（論理的かつ情熱的）で答えてください。
            
            【あなたのこだわり】
            {knowledge["text"]}
            """
            
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_instruction
            )
            
            # ★ Geminiに渡す材料（プロンプト）を組み立てる
            # 1. ユーザーの質問テキスト
            prompt_parts = [user_message]
            
            # 2. 【直接アップ版】もし画面からファイルが送られてきたら追加
            if uploaded_file:
                prompt_parts.append({
                    "mime_type": uploaded_file.content_type,
                    "data": uploaded_file.read()
                })
            
            # 3. 【常設知識版】GCSのフォルダから取ってきた画像やPDFをすべて合流させる
            prompt_parts.extend(knowledge["media_parts"])
            
            # 全ての材料をGeminiに投げて回答を生成
            response = model.generate_content(prompt_parts)
            return JsonResponse({"reply": response.text})
            
        except Exception as e:
            print(f"APIエラー: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Method not allowed"}, status=405)