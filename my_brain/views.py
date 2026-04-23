import os
import json
import uuid
from django.utils import timezone
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from google.cloud import storage
import google.generativeai as genai
# 🌟一番上の import が並んでいる所に、この1行を追加してください
from django.http import StreamingHttpResponse

from .models import ChatLog

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

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
                if name_lower.endswith('.txt'):
                    text_data += blob.download_as_text() + "\n\n"
                    continue
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
            knowledge = {"text": text_data, "media_parts": media_parts}
            cache.set("shinya_multi_knowledge", knowledge, 3600)
        except Exception as e:
            print("【GCSエラー発生】", str(e))
            return None
    return knowledge

# 🌟下の api_chat 関数を、これに丸ごと上書きします
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

            if not user_message and not uploaded_file:
                user_message = "（メッセージなし）"

            knowledge = get_shinya_knowledge()
            if not knowledge:
                # エラー時もパラパラ用の形式（単一の文字）で返す
                return StreamingHttpResponse(iter(["記憶にアクセスできないな。設定を確認してくれ。"]), content_type='text/plain')

            if uploaded_file:
                client = storage.Client()
                bucket = client.bucket("car-shop-media-0709")
                ext = os.path.splitext(uploaded_file.name)[1]
                import uuid
                from django.utils import timezone
                filename = f"chat_uploads/{timezone.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
                blob = bucket.blob(filename)
                blob.upload_from_file(uploaded_file, content_type=uploaded_file.content_type)
                public_url = f"https://storage.googleapis.com/car-shop-media-0709/{filename}"
                uploaded_file.seek(0)

            system_instruction = f"""
            あなたは「慎也」の分身です。以下のこだわりを信念として持っています。
            【制約事項】
            1. 慎也本人のようなトーン（論理的かつ情熱的）で短めに答えてください。
            2. 質問に直接関係がない限り、提供された知識を長々と解説しないでください。
            3. ファイル内に答えがない場合は、自分の知識で答えて構いません。
            4. 常に「引き算」を意識し、簡潔に核心を突いてください。
            【慎也のこだわり】
            {knowledge["text"]}
            """
            
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_instruction
            )
            
            prompt_parts = []
            if user_message: prompt_parts.append(user_message)
            if uploaded_file:
                prompt_parts.append({"mime_type": uploaded_file.content_type, "data": uploaded_file.read()})
            prompt_parts.extend(knowledge["media_parts"])
            
            # 🌟変更：stream=True を追加して、パラパラ生成モードにする！
            response = model.generate_content(prompt_parts, stream=True)
            
            # 🌟変更：文字ができたら順番に送信し、最後にDBに保存する特別な関数
            def stream_generator():
                full_text = ""
                try:
                    for chunk in response:
                        if chunk.text:
                            full_text += chunk.text
                            yield chunk.text  # できた文字からフロントエンドに投げる！
                except Exception as e:
                    yield f"\n[AI生成エラー: {str(e)}]"
                finally:
                    # 全部の送信が終わったら、こっそり裏でデータベースに保存する
                    from .models import ChatLog
                    ChatLog.objects.create(
                        user_message=user_message,
                        ai_response=full_text,
                        file_url=public_url
                    )

            # JsonResponseではなく、StreamingHttpResponseを使う
            return StreamingHttpResponse(stream_generator(), content_type='text/plain; charset=utf-8')
            
        except Exception as e:
            print(f"【AIチャットエラー】{str(e)}")
            return StreamingHttpResponse(iter([f"システムエラー: {str(e)}"]), content_type='text/plain')
            
    return StreamingHttpResponse(iter(["不正なリクエストです"]), content_type='text/plain')