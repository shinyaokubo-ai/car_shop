# car_lp_builder/views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CarListing
# car_lp_builder/views.py の一番上あたりにこれを追加
from django.shortcuts import get_object_or_404

@csrf_exempt # テスト通信を弾かないためのおまじない
def generate_lp_api(request):
    if request.method == 'POST':
        try:
            # 1. Vueから送られてきたデータ（買取メモなど）を受け取る
            data = json.loads(request.body)
            memo_text = data.get('memo', 'メモなし')
            car_name = data.get('car_name', '詳細不明の車両')

            # 2. AIの代わりにダミーの物語JSONを用意（後でここにGeminiを繋ぎます！）
            generated_json = {
                "catchphrase": f"時を超える、{car_name}の鼓動。",
                "story": f"買取メモ（{memo_text}）から読み取れるように、この車は前オーナーによって極上の状態に保たれてきました。"
            }

            # 3. 先ほど見た管理画面のデータベース（CarListing）に保存！
            new_lp = CarListing.objects.create(
                car_name=car_name,
                generated_story=json.dumps(generated_json, ensure_ascii=False),
                status='DRAFT' # 下書き状態
            )

            # 4. Vue側に「完成したLPのURL（ID）」を返す
            return JsonResponse({
                'status': 'success', 
                'message': 'LPの生成と保存が完了しました！',
                'lp_id': str(new_lp.id)
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    # 👇一番下にこれを追加！
def get_lp_detail(request, lp_id):
    """URLのIDをもとに、データベースからその車の物語を引っ張り出してVueに渡す関数"""
    if request.method == 'GET':
        try:
            # 1. データベースから指定されたIDの車を探す（無ければ404エラーにする）
            car_lp = get_object_or_404(CarListing, id=lp_id)

            # 2. 文字列として保存されているJSON（物語）を、Pythonで扱いやすい形に戻す
            story_data = {}
            if car_lp.generated_story:
                story_data = json.loads(car_lp.generated_story)

            # 3. Vueが画面に表示しやすい形に整理して返してあげる
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(car_lp.id),
                    'car_name': car_lp.car_name,
                    'catchphrase': story_data.get('catchphrase', ''),
                    'story': story_data.get('story', ''),
                    'status': car_lp.status,
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)