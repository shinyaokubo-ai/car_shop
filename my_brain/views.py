import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from google.cloud import storage
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def get_shinya_knowledge():
    """GCSの brain_files フォルダ内の【テキスト】と【画像/PDF】をすべて自動取得する"""
    knowledge = cache.get("shinya_multi_knowledge")
    
    if not knowledge:
        BUCKET_NAME = "car-shop-media-0709"
        FOLDER_PREFIX = "brain_files/"
        
        try:
            if os.path.exists('gcp-key.json'):
                client = storage.Client.from_service_account_json('gcp-key.json')
            else:
                client = storage.Client()

            bucket = client.bucket(BUCKET_NAME)
            
            media_parts = []
            text_data = "" # 複数のテキストファイルがあった場合、ここにどんどん繋げていく
            
            blobs = bucket.list_blobs(prefix=FOLDER_PREFIX)
            
            for blob in blobs:
                if blob.name == FOLDER_PREFIX:
                    continue
                    
                name_lower = blob.name.lower()
                
                # ★テキストファイル(.txt)を見つけた場合の処理
                if name_lower.endswith('.txt'):
                    text_data += blob.download_as_text() + "\n\n"
                    continue
                
                # ★画像やPDFを見つけた場合の処理
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
            
            print(f"【GCS全自動読み込み成功！】取得した画像/PDF: {len(media_parts)}件, テキストも取得完了")
            cache.set("shinya_multi_knowledge", knowledge, 3600)
            
        except Exception as e:
            print("【GCSエラー発生】", str(e))
            return None
            
    return knowledge

def chat_interface(request):
    return render(request, 'my_brain/chat.html')

@csrf_exempt
def api_chat(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message")
            
            knowledge = get_shinya_knowledge()
            
            if not knowledge:
                return JsonResponse({"reply": "現在、記憶ファイルにアクセスできません。"})

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
            
            # ★ 質問文のうしろに、フォルダから取ってきた全画像・PDFをガサッと添えて渡す
            prompt_parts = [user_message] + knowledge["media_parts"]
            
            response = model.generate_content(prompt_parts)
            return JsonResponse({"reply": response.text})
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Method not allowed"}, status=405)