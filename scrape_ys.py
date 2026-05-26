import os
import re
import time
import django
import asyncio
import urllib.request
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async

# GCPの鍵
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcp-key.json'


# 🌟 .env（金庫）から自動で読み込むように変更！直書きのURLは消去！
from dotenv import load_dotenv
load_dotenv()


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from storages.backends.gcloud import GoogleCloudStorage
from cars.models import CarImage
CarImage._meta.get_field('image').storage = GoogleCloudStorage()

from cars.models import Car
from django.core.files.base import ContentFile

def extract_price(text):
    num_str = re.sub(r'\D', '', text)
    return int(num_str) if num_str else 0

@sync_to_async
def save_car_images(car, image_urls):
    car.images.all().delete()
    print(f"\n☁️ 画像をGoogle Cloud Storageにアップロード中...")
    
    current_time = int(time.time())
    
    for idx, url in enumerate(image_urls[:15]): 
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                img_data = response.read()
                img_name = f"{car.sku}_{current_time}_{idx}.jpg"
                img_type = 'exterior' if idx < 8 else 'interior'
                
                car.images.create(
                    image=ContentFile(img_data, name=img_name),
                    image_type=img_type
                )
                print(f"   📸 画像 {idx+1}/{len(image_urls[:15])} 枚目の保存完了！")
        except Exception as e:
            print(f"   ❌ 画像保存エラー: {e}")

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        url = "https://www.ysproject.jp/product-page/%E3%83%9D%E3%83%AB%E3%82%B7%E3%82%A7-%E3%83%9E%E3%82%AB%E3%83%B3-gts-1"
        print("サイトにアクセス中...")
        await page.goto(url)

        try:
            car_title = await page.locator('h1').first.inner_text()
        except:
            car_title = "取得エラー車両"

        await page.wait_for_selector('[data-hook="collapse-info-item"]', timeout=20000)
        await page.wait_for_timeout(2000) 

        car_data = {}
        equipment_data = {}
        comment_text = standard_text = option_text = custom_text = ""

        items = await page.locator('[data-hook="collapse-info-item"]').all()
        for item in items:
            button = item.locator('[data-hook="collapse-info-button"]')
            if await button.count() > 0:
                title_raw = await button.inner_text()
                title = title_raw.strip()

                if await button.get_attribute("aria-expanded") == "false":
                    await button.click()
                    await page.wait_for_timeout(1000) 

                # 🌟 慎也さんの発見により修正：「基本仕様は表(テーブル)である！」
                if "基本" in title or "仕様" in title:
                    tables = await item.locator('table').all()
                    for table in tables:
                        rows = await table.locator('tr').all()
                        for row in rows:
                            # 1行の中にある td (左と右) を取得
                            cells = await row.locator('td, th').all_inner_texts()
                            if len(cells) >= 2:
                                key = cells[0].strip().replace('\xa0', '')
                                val = cells[1].strip().replace('\xa0', '')
                                if key:
                                    car_data[key] = val

                # 🌟 装備関係のチェックボックス表（昔から完璧に動いている部分）
                elif any(kw in title for kw in ["安全", "外装", "内装", "車歴", "書類", "ナビ", "オーディオ", "装備"]):
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

                # 🌟 それ以外の文字データ（オプションなど）
                else:
                    content = await item.inner_text()
                    # タイトル名が本文にくっついてしまうバグの回避
                    if content.startswith(title_raw):
                        body_text = content[len(title_raw):].strip()
                    elif content.startswith(title):
                        body_text = content[len(title):].strip()
                    else:
                        lines = content.split('\n')
                        if title in lines[0]:
                            body_text = "\n".join(lines[1:]).strip()
                        else:
                            body_text = content.strip()

                    if "情報" in title or "コメント" in title or "詳細" in title:
                        comment_text = body_text
                    elif "標準" in title:
                        standard_text = body_text
                    elif "オプション" in title:
                        option_text = body_text
                    elif "社外" in title or "カスタム" in title:
                        custom_text = body_text

        print("💰 金額データを抽出中...")
        price_total = price_vehicle = price_misc = 0
        desc_locator = page.locator('[data-hook="description"]')
        if await desc_locator.count() > 0:
            desc_text = await desc_locator.inner_text()
            for line in desc_text.split('\n'):
                if '総額' in line: price_total = extract_price(line)
                elif '車両価格' in line: price_vehicle = extract_price(line)
                elif '諸費用' in line: price_misc = extract_price(line)

        print("🖼️ 画像URLを解析中...")
        image_urls = []
        img_locators = await page.locator('img').all()
        for img in img_locators:
            src = await img.get_attribute('src') or ""
            if 'static.wixstatic.com/media/' in src:
                high_res_url = src.split('/v1/')[0]
                if any(bad in high_res_url.lower() for bad in ['cd0e5d', '.png', 'logo']): continue
                if high_res_url not in image_urls: image_urls.append(high_res_url)

        print("\n🚀 データベース（Neon）へ登録を開始します...")
        
        unique_sku = f"SCRAPE-{int(time.time())}"

        new_car, _ = await Car.objects.aupdate_or_create(
            sku=unique_sku,
            defaults={
                'title': car_title,
                'price_total': price_total, 'price_vehicle': price_vehicle, 'price_misc': price_misc,
                
                # --- 基本スペック ---
                'registration_year': car_data.get('初年度登録', car_data.get('年式', '')),
                'mileage': car_data.get('走行距離', ''),
                'inspection': car_data.get('車検', ''),
                'repair_history': car_data.get('修復歴', 'なし'),
                'body_color': car_data.get('ボディカラー', ''),
                'transmission': car_data.get('ミッション', 'AT'),
                'drive_system': car_data.get('駆動方式', '4WD'),
                
                # --- 慎也さんが追加した詳細スペック ---
                'handle': car_data.get('ハンドル', '右'),
                'import_route': car_data.get('輸入経路', 'ディーラー車'),
                'interior_color': car_data.get('内装色', ''),
                'length': car_data.get('全長(cm)', car_data.get('全長', '')),
                'width': car_data.get('全幅(cm)', car_data.get('全幅', '')),
                'height': car_data.get('全高(cm)', car_data.get('全高', '')),
                'production_country': car_data.get('生産国', ''),
                'production_period': car_data.get('生産期間', ''),
                'new_car_price': car_data.get('新車時車両価格', ''),
                'model_code': car_data.get('型式', ''),
                'wheelbase': car_data.get('ホイールベース(mm)', car_data.get('ホイールベース', '')),
                'tread_front': car_data.get('前トレッド(mm)', car_data.get('前トレッド/後トレッド', '').split('/')[0] if '/' in car_data.get('前トレッド/後トレッド', '') else ''),
                'tread_rear': car_data.get('後トレッド(mm)', car_data.get('前トレッド/後トレッド', '').split('/')[-1] if '/' in car_data.get('前トレッド/後トレッド', '') else ''),
                'weight': car_data.get('車体重量(kg)', car_data.get('車体重量', '')),
                'door_count': car_data.get('ドア数', ''),
                'capacity': car_data.get('乗車定員', ''),
                'seat_rows': car_data.get('シート列数', ''),
                'transmission_pos': car_data.get('ミッション位置', ''),
                
                # --- テキスト系 ---
                'comment': comment_text,
                'equipment_standard': standard_text,
                'equipment_option': option_text,
                'equipment_custom': custom_text,

                # --- 装備チェックボックス ---
                'has_aircon': equipment_data.get('エアコン', False),
                'has_power_steering': equipment_data.get('パワステ', False) or equipment_data.get('パワーステアリング', False),
                'has_power_window': equipment_data.get('パワーウィンドウ', False),
                'has_airbag': equipment_data.get('エアバック', False) or equipment_data.get('エアバッグ', False),
                'has_abs': equipment_data.get('ABS', False),
                'has_etc': equipment_data.get('ETC', False),
                'has_back_camera': equipment_data.get('バックカメラ', False),
                'has_leather_seat': equipment_data.get('革シート', False) or equipment_data.get('本革シート', False),
                'has_bluetooth': equipment_data.get('Bluetooth接続', False) or equipment_data.get('Bluetooth', False),
                
                'has_sunroof': equipment_data.get('サンルーフ', False),
                'has_aluminum_wheel': equipment_data.get('アルミホイール', False),
                'has_one_owner': equipment_data.get('ワンオーナー', False),
                'has_warranty': equipment_data.get('保証書', False),
                'has_service_record': equipment_data.get('整備手帳', False),
                'has_record_book': equipment_data.get('記録簿', False),
                'has_spare_key': equipment_data.get('スペアキー', False),

                'is_published': True, 
            }
        )
        if image_urls: await save_car_images(new_car, image_urls)
        print("✅ すべて完了！")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())