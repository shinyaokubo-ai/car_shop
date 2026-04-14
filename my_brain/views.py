import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from google.cloud import storage
import google.generativeai as genai

# APIキーは環境変数から取得（Cloud Runの設定画面で指定してください）
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def get_shinya_context():
    """GCSから知識を取得（キャッシュ優先）"""
    context = cache.get("shinya_knowledge")
    if not context:
        BUCKET_NAME = "car-shop-media-0709" 
        BLOB_NAME = "shinya_food_rules.txt"
        
        try:
            # 修正点①：鍵ファイル（gcp-key.json）を明示的に使ってGCSにアクセスする
            client = storage.Client.from_service_account_json('gcp-key.json')
            bucket = client.bucket(BUCKET_NAME)
            blob = bucket.blob(BLOB_NAME)
            context = blob.download_as_text()
            
            # 修正点②：printを使って、読み込めたテキストをターミナルに出力（味見）する
            print("【GCS読み込み成功！】\n", context)
            
            cache.set("shinya_knowledge", context, 3600)
        except Exception as e:
            # 修正点③：もしエラーが出たら、ターミナルに赤裸々にエラー原因を出力する
            print("【GCSエラー発生】", str(e))
            return f"Error loading context: {str(e)}"
            
    return context

def chat_interface(request):
    """チャット画面を表示"""
    return render(request, 'my_brain/chat.html')

@csrf_exempt
def api_chat(request):
    """Geminiとの通信エンドポイント"""
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message")
        
        knowledge = get_shinya_context()
        
        system_instruction = f"""
        あなたは「慎也」の分身です。以下のこだわりを自分の信念として持ち、
        質問に対して慎也本人のようなトーン（論理的かつ情熱的）で答えてください。
        
        【あなたのこだわり】
        {knowledge}
        """
        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash", # 最新の安定版
            system_instruction=system_instruction
        )
        
        response = model.generate_content(user_message)
        return JsonResponse({"reply": response.text})
    
    return JsonResponse({"error": "Method not allowed"}, status=405)