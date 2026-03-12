import os
import re
import django
import asyncio
import urllib.request
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async

os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_rc2lj6yutPKS@ep-purple-mud-a1zso0n2-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

# 🌟追加：Cloudinaryに入るための3つの鍵
os.environ['CLOUD_NAME'] = 'dbcreggsx'
os.environ['CLOUD_API_KEY'] = '485365791581239'
os.environ['CLOUD_API_SECRET'] = 'RPXYYE8bqJaY0ZTuyeGfw7sM3w8'


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from cars.models import Car
from django.core.files.base import ContentFile

def extract_price(text):
    num_str = re.sub(r'\D', '', text)
    return int(num_str) if num_str else 0

# 🌟追加：画像をダウンロードしてCloudinaryに保存する専用機能
@sync_to_async
def save_car_images(car, image_urls):
    car.images.all().delete() # 古い画像をリセット
    print(f"\n☁️ 画像をCloudinaryにアップロード中...（最大5枚 / 少し時間がかかります）")
    
    for idx, url in enumerate(image_urls[:5]): # 最初の5枚だけ保存する
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                img_data = response.read()
                img_name = f"{car.sku}_{idx}.jpg" # ファイル名を自動生成
                img_type = 'exterior' if idx == 0 else 'other'
                
                # ここでCloudinaryへの自動転送が発動！
                car.images.create(
                    image=ContentFile(img_data, name=img_name),
                    image_type=img_type
                )
                print(f"   📸 画像 {idx+1}/5 枚目の保存完了！")
        except Exception as e:
            print(f"   ❌ 画像保存エラー: {e}")

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        url = "https://www.ysproject.jp/product-page/%E3%83%9D%E3%83%AB%E3%82%B7%E3%82%A7-%E3%83%9E%E3%82%AB%E3%83%B3-gts-2"
        print("サイトにアクセス中...")
        await page.goto(url)
        await page.wait_for_selector('[data-hook="collapse-info-item"]', timeout=20000)
        await page.wait_for_timeout(2000) 

        car_data = {}
        equipment_data = {}
        comment_text = ""
        standard_text = ""
        option_text = ""
        custom_text = ""

        items = await page.locator('[data-hook="collapse-info-item"]').all()
        for item in items:
            button = item.locator('[data-hook="collapse-info-button"]')
            if await button.count() > 0:
                is_expanded = await button.get_attribute("aria-expanded")
                if is_expanded == "false":
                    await button.click()
                    await page.wait_for_timeout(1000) 

                content = await item.inner_text()
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                
                if len(lines) > 0:
                    title = lines[0]
                    if title == "基本仕様":
                        for line in lines[1:]:
                            parts = line.split()
                            if len(parts) >= 2:
                                car_data[parts[0]] = " ".join(parts[1:])
                                
                    elif title in ["安全装備", "外装", "内装", "車歴書類", "ナビ・オーディオ", "外装・内装装備"]:
                        tables = await item.locator('table').all()
                        for table in tables:
                            rows = await table.locator('tr').all()
                            for i in range(0, len(rows) - 1, 2):
                                header_cells = await rows[i].locator('td, th').all_inner_texts()
                                value_cells = await rows[i+1].locator('td, th').all_inner_texts()
                                for j, h_text in enumerate(header_cells):
                                    h_text = h_text.strip().replace('\xa0', '')
                                    if h_text:
                                        v_text = value_cells[j].strip().replace('\xa0', '') if j < len(value_cells) else ""
                                        equipment_data[h_text] = ('〇' in v_text or '○' in v_text)
                    
                    elif "コメント" in title or "車両詳細" in title:
                        comment_text = "\n".join(lines[1:])
                    elif "標準装備" in title:
                        standard_text = "\n".join(lines[1:])
                    elif "オプション" in title:
                        option_text = "\n".join(lines[1:])
                    elif "社外" in title or "カスタム" in title:
                        custom_text = "\n".join(lines[1:])

        print("💰 金額データを抽出中...")
        price_total = price_vehicle = price_misc = 0
        description_locator = page.locator('[data-hook="description"]')
        if await description_locator.count() > 0:
            description_text = await description_locator.inner_text()
            for line in description_text.split('\n'):
                if '総額' in line: price_total = extract_price(line)
                elif '車両価格' in line: price_vehicle = extract_price(line)
                elif '諸費用' in line: price_misc = extract_price(line)

        # 🌟追加：画像のURLをかき集める！
        print("🖼️ 画像URLを探索中...")
        image_urls = []
        img_locators = await page.locator('img').all()
        for img in img_locators:
            src = await img.get_attribute('src')
            # static.wixstatic.com/media/ を含む画像だけをピックアップ
            if src and 'static.wixstatic.com/media/' in src and src not in image_urls:
                image_urls.append(src)

        tread_str = car_data.get('前トレッド/後トレッド', '')
        tread_f = tread_str.split('/')[0].replace('（mm）','').strip() if '/' in tread_str else ''
        tread_r = tread_str.split('/')[1].replace('（mm）','').strip() if '/' in tread_str else ''

        print("\n🚀 データベース（Neon）へ上書き登録を開始します...")
        
        new_car, created = await Car.objects.aupdate_or_create(
            sku="AUTO-MACAN-TEST",
            defaults={
                'title': "ポルシェ マカン GTS (自動登録)",
                'price_total': price_total,
                'price_vehicle': price_vehicle,
                'price_misc': price_misc,
                
                'registration_year': car_data.get('初年度登録', ''),
                'mileage': car_data.get('走行距離', ''),
                'inspection': car_data.get('車検', ''),
                'repair_history': car_data.get('修復歴', 'なし'),
                'body_color': car_data.get('ボディカラー', ''),
                'interior_color': car_data.get('内装色', ''),
                'handle': car_data.get('ハンドル', '右'),
                'length': car_data.get('全長', '').replace('cm', ''),
                'width': car_data.get('全幅', '').replace('cm', ''),
                'height': car_data.get('全高', '').replace('cm', ''),
                'wheelbase': car_data.get('ホイールベース', '').replace('（mm）', '').replace('(mm)', '').strip(),
                'tread_front': tread_f,
                'tread_rear': tread_r,
                'weight': car_data.get('車体重量', '').replace('（kg）', '').replace('(kg)', '').strip(),
                'door_count': car_data.get('ドア数', ''),
                'capacity': car_data.get('乗車定員', '').replace('名', ''),
                'seat_rows': car_data.get('シート列数', ''),
                'production_country': car_data.get('生産国', ''),
                'production_period': car_data.get('生産期間', ''),
                'model_code': car_data.get('型式', ''),
                'new_car_price': car_data.get('新車時車両価格', ''),
                'drive_system': car_data.get('駆動方式', '4WD'),
                'transmission': car_data.get('ミッション', 'AT'),
                'transmission_pos': car_data.get('ミッション位置', ''),
                'has_manual_mode': ('○' in car_data.get('マニュアルモード', '') or '〇' in car_data.get('マニュアルモード', '')),

                'comment': comment_text,
                'equipment_standard': standard_text,
                'equipment_option': option_text,
                'equipment_custom': custom_text,

                'has_aircon': equipment_data.get('エアコン', False),
                'has_power_steering': equipment_data.get('パワステ', False) or equipment_data.get('パワーステアリング', False),
                'has_power_window': equipment_data.get('パワーウィンドウ', False),
                'has_airbag': equipment_data.get('エアバック', False),
                'has_abs': equipment_data.get('ABS', False),
                'has_esc': equipment_data.get('ESC(横滑り防止)', False) or equipment_data.get('ESC', False),
                'has_collision_safety': equipment_data.get('衝突被害軽減システム', False) or equipment_data.get('衝突被害軽減ブレーキ', False),
                'has_lane_assist': equipment_data.get('レーンアシスト', False),
                'has_park_assist': equipment_data.get('パークアシスト', False),
                'has_auto_parking': equipment_data.get('自動駐車システム', False),
                'has_cruise_control': equipment_data.get('クルーズコントロール', False),
                'has_keyless': equipment_data.get('キーレスエントリー', False) or equipment_data.get('キーレス', False),
                'has_smart_key': equipment_data.get('スマートキー', False),
                'has_etc': equipment_data.get('ETC', False),
                'has_back_camera': equipment_data.get('バックカメラ', False),
                'has_camera_360': equipment_data.get('全周囲カメラ', False),
                'has_auto_highbeam': equipment_data.get('オートマチックハイビーム', False),
                'has_auto_light': equipment_data.get('オートライト', False),
                'has_fog_lamp': equipment_data.get('フォグランプ', False),
                
                'has_sunroof': equipment_data.get('サンルーフ', False),
                'has_leather_seat': equipment_data.get('革シート', False),
                'has_aluminum_wheel': equipment_data.get('アルミホイール', False),
                'has_aero_parts': equipment_data.get('エアロパーツ', False),
                'has_low_down': equipment_data.get('ローダウン', False),
                'has_lift_up': equipment_data.get('リフトアップ', False),
                'has_power_gate': equipment_data.get('電動リアゲート', False),
                'has_led_headlight': equipment_data.get('LEDヘッドライト', False),
                'has_hid_headlight': equipment_data.get('HIDヘッドライト', False),
                'has_seat_heater': equipment_data.get('シートヒーター', False),
                'has_power_seat': equipment_data.get('パワーシート', False),
                'has_seat_aircon': equipment_data.get('シートエアコン', False),
                'has_half_leather_seat': equipment_data.get('ハーフレザーシート', False),
                'has_custom_muffler': equipment_data.get('社外マフラー', False),
                'has_full_aero': equipment_data.get('フルエアロ', False),
                'has_runflat_tire': equipment_data.get('ランフラットタイヤ', False),
                
                'has_hdd_navi': equipment_data.get('HDDナビ', False),
                'has_memory_navi': equipment_data.get('メモリーナビ', False),
                'has_fullseg_tv': equipment_data.get('フルセグTV', False),
                'has_bluetooth': equipment_data.get('Bluetooth接続', False),
                'has_dvd': equipment_data.get('DVD再生', False) or equipment_data.get('DVD', False),
                'has_music_server': equipment_data.get('ミュージックサーバー', False),
                'has_usb_input': equipment_data.get('USB入力端子', False),
                'has_music_player': equipment_data.get('ミュージックプレイヤー接続', False),
                'has_cd': equipment_data.get('CD再生', False) or equipment_data.get('CD', False),
                'has_rear_monitor': equipment_data.get('後席モニター', False),
                
                'has_4wd_check': equipment_data.get('4WD', False),
                'has_diesel': equipment_data.get('ディーゼル', False),

                'has_one_owner': equipment_data.get('ワンオーナー', False),
                'has_warranty': equipment_data.get('保証書', False),
                'has_service_record': equipment_data.get('整備手帳', False),
                'has_record_book': equipment_data.get('記録簿', False),
                'has_manual': equipment_data.get('取扱説明書', False),
                'has_spare_key': equipment_data.get('スペアキー', False),
            }
        )

        # 🌟追加：最後にCloudinaryへ画像をアップロード
        if image_urls:
            await save_car_images(new_car, image_urls)

        print("✅ すべての処理が完了しました！")
        await browser.close()

asyncio.run(run())