from django.shortcuts import render
from django.http import HttpResponse
from google import genai
import os
import json
from dotenv import load_dotenv
from cars.models import Car 

load_dotenv()

def index(request):
    result = None
    raw_json = None

    if request.method == "POST":
        # 🌟 A：【登録する】ボタンが押された時の処理
        if "save_data" in request.POST:
            json_str = request.POST.get("json_data")
            if json_str:
                data_dict = json.loads(json_str)
                try:
                    # 1. 必須の数値項目が「不明」や空だった場合の補正（0円にする）
                    for key in ['price_total', 'price_vehicle', 'price_misc']:
                        if not data_dict.get(key) or str(data_dict[key]).isdigit() == False:
                            data_dict[key] = 0
                    
                    # 🌟 2. 文字項目のカラッポ対策（NOT NULLエラー回避）
                    text_fields = ['title', 'sku', 'registration_year', 'mileage', 'inspection', 'model_code', 'body_color']
                    for key in text_fields:
                        if not data_dict.get(key):  # もしAIが読み取れず空っぽだったら...
                            data_dict[key] = "不明"  # 「不明」という文字を入れてあげる！

                    # 🚀 データベースへ保存！ (**data_dict で各項目に自動配分されます)
                    new_car = Car.objects.create(**data_dict)
                    
                    # 🌟 成功したら「success.html」へ移動
                    return render(request, 'ai_assist/success.html', {'car': new_car})
                except Exception as e:
                    # 🌟 登録エラー時の画面（戻るボタン付き）
                    error_html = f"""
                    <div style="padding: 50px; font-family: sans-serif; text-align: center;">
                        <h1 style="color: #dc3545;">登録エラー発生</h1>
                        <p style="font-size: 1.2rem;"><b>{e}</b></p>
                        <p>管理番号の重複、または必須項目のエラーが考えられます。</p>
                        <a href="/ai-assist/" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #0d6efd; color: white; text-decoration: none; border-radius: 5px;">AIアシストTOPに戻る</a>
                    </div>
                    """
                    return HttpResponse(error_html)

        # 🌟 B：【解析ボタン】が押された時の処理
        elif request.FILES.getlist("upload_images"):
            GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
            client = genai.Client(api_key=GOOGLE_API_KEY)
            image_files = request.FILES.getlist("upload_images")
            
            # 🌟 AIへの指示：models.pyの全項目（約40個）を網羅した完全版プロンプト
            prompt = """
            提供されたすべての画像を確認し、車両情報を抽出して以下のJSON形式のみで返してください。
            チェックボックス項目は、画像内に記載やチェックがあれば True、なければ False にしてください。
            説明は一切不要です。JSONのみを出力してください。
            
            {
                "title": "車名",
                "sku": "管理番号",
                "registration_year": "年式(初年度登録)",
                "mileage": "走行距離",
                "inspection": "車検満了日",
                "model_code": "型式",
                "body_color": "ボディカラー",
                "transmission": "ミッション",
                "drive_system": "駆動方式",

                "has_4wd_check": True/False,
                "has_diesel": True/False,

                "has_aircon": True/False,
                "has_power_steering": True/False,
                "has_power_window": True/False,
                "has_airbag": True/False,
                "has_abs": True/False,
                "has_esc": True/False,
                "has_collision_safety": True/False,
                "has_lane_assist": True/False,
                "has_park_assist": True/False,
                "has_auto_parking": True/False,
                "has_cruise_control": True/False,
                "has_keyless": True/False,
                "has_smart_key": True/False,
                "has_etc": True/False,
                "has_back_camera": True/False,
                "has_camera_360": True/False,
                "has_auto_highbeam": True/False,
                "has_auto_light": True/False,
                "has_fog_lamp": True/False,

                "has_sunroof": True/False,
                "has_leather_seat": True/False,
                "has_half_leather_seat": True/False,
                "has_aluminum_wheel": True/False,
                "has_aero_parts": True/False,
                "has_full_aero": True/False,
                "has_low_down": True/False,
                "has_lift_up": True/False,
                "has_power_gate": True/False,
                "has_led_headlight": True/False,
                "has_hid_headlight": True/False,
                "has_seat_heater": True/False,
                "has_seat_aircon": True/False,
                "has_power_seat": True/False,
                "has_custom_muffler": True/False,
                "has_runflat_tire": True/False,

                "has_hdd_navi": True/False,
                "has_memory_navi": True/False,
                "has_fullseg_tv": True/False,
                "has_bluetooth": True/False,
                "has_dvd": True/False,
                "has_cd": True/False,
                "has_music_server": True/False,
                "has_music_player": True/False,
                "has_usb_input": True/False,
                "has_rear_monitor": True/False,

                "has_one_owner": True/False,
                "has_warranty": True/False,
                "has_service_record": True/False,
                "has_record_book": True/False,
                "has_manual": True/False,
                "has_spare_key": True/False
            }
            """
            contents = [prompt]
            for f in image_files:
                img_data = f.read()
                contents.append({"inline_data": {"data": img_data, "mime_type": "image/jpeg"}})

            try:
                response = client.models.generate_content(model='gemini-2.5-flash', contents=contents)
                raw_json = response.text.replace('```json', '').replace('```', '').strip()
                result = json.loads(raw_json)
            except Exception as e:
                # 🌟 解析エラー時の画面（戻るボタン付き）
                error_html = f"""
                <div style="padding: 50px; font-family: sans-serif; text-align: center;">
                    <h1 style="color: #dc3545;">解析エラー発生</h1>
                    <p style="font-size: 1.2rem;"><b>{e}</b></p>
                    <p>画像の読み取りに失敗したか、AIが正しいJSONを返しませんでした。</p>
                    <a href="/ai-assist/" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #0d6efd; color: white; text-decoration: none; border-radius: 5px;">AIアシストTOPに戻る</a>
                </div>
                """
                return HttpResponse(error_html)

    return render(request, 'ai_assist/index.html', {'result': result, 'raw_json': raw_json})