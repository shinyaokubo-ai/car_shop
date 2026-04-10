import os
import re
import time  # 🌟 時間を取得するライブラリを追加！
import django
import asyncio
import urllib.request
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async

# GCPの鍵
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcp-key.json'

# Neonデータベース
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_rc2lj6yutPKS@ep-purple-mud-a1zso0n2-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from storages.backends.gcloud import GoogleCloudStorage
from cars.models import CarImage
CarImage._meta.get_field('image').storage = GoogleCloudStorage()

from django.core.management import call_command
call_command('migrate')

from cars.models import Car
from django.core.files.base import ContentFile

def extract_price(text):
    num_str = re.sub(r'\D', '', text)
    return int(num_str) if num_str else 0

@sync_to_async
def save_car_images(car, image_urls):
    car.images.all().delete()
    print(f"\n☁️ 画像をGoogle Cloud Storageにアップロード中...")
    
    # 🌟 幽霊対策：現在の「秒数」を取得
    current_time = int(time.time())
    
    for idx, url in enumerate(image_urls[:15]): 
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                img_data = response.read()
                
                # 🌟 名前を毎回変える！（例：AUTO-MACAN-TEST_1712345678_0.jpg）
                # これでブラウザは「知らない名前だ！新しく読み込もう！」と動きます
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

        url = "https://www.ysproject.jp/product-page/%E3%83%9D%E3%83%AB%E3%82%B7%E3%82%A7-%E3%83%9E%E3%82%AB%E3%83%B3-gts-2"
        print("サイトにアクセス中...")
        await page.goto(url)
        await page.wait_for_selector('[data-hook="collapse-info-item"]', timeout=20000)
        await page.wait_for_timeout(2000) 

        car_data = {}
        equipment_data = {}
        comment_text = standard_text = option_text = custom_text = ""

        items = await page.locator('[data-hook="collapse-info-item"]').all()
        for item in items:
            button = item.locator('[data-hook="collapse-info-button"]')
            if await button.count() > 0:
                if await button.get_attribute("aria-expanded") == "false":
                    await button.click()
                    await page.wait_for_timeout(1000) 

            content = await item.inner_text()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            if lines:
                title = lines[0]
                if title == "基本仕様":
                    for line in lines[1:]:
                        parts = line.split()
                        if len(parts) >= 2: car_data[parts[0]] = " ".join(parts[1:])
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
                elif "コメント" in title or "車両詳細" in title: comment_text = "\n".join(lines[1:])
                elif "標準装備" in title: standard_text = "\n".join(lines[1:])
                elif "オプション" in title: option_text = "\n".join(lines[1:])
                elif "社外" in title or "カスタム" in title: custom_text = "\n".join(lines[1:])

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
                # 🚫 ロゴ徹底排除（慎也さんが特定してくれたID）
                if any(bad in high_res_url.lower() for bad in ['cd0e5d', '9c93405', '.png', 'logo']): continue
                if high_res_url not in image_urls: image_urls.append(high_res_url)

        print("\n🚀 データベース（Neon）へ登録を開始します...")
        new_car, _ = await Car.objects.aupdate_or_create(
            sku="AUTO-MACAN-TEST",
            defaults={
                'title': "ポルシェ マカン GTS (自動登録)",
                'price_total': price_total, 'price_vehicle': price_vehicle, 'price_misc': price_misc,
                'registration_year': car_data.get('初年度登録', ''),
                'mileage': car_data.get('走行距離', ''),
                'inspection': car_data.get('車検', ''),
                'repair_history': car_data.get('修復歴', 'なし'),
                'body_color': car_data.get('ボディカラー', ''),
                'handle': car_data.get('ハンドル', '右'),
                'comment': comment_text,
                'equipment_standard': standard_text,
                'has_aircon': equipment_data.get('エアコン', False),
                'has_power_steering': equipment_data.get('パワステ', False) or equipment_data.get('パワーステアリング', False),
                'has_power_window': equipment_data.get('パワーウィンドウ', False),
                'has_airbag': equipment_data.get('エアバック', False),
                'has_abs': equipment_data.get('ABS', False),
                'has_etc': equipment_data.get('ETC', False),
                'has_back_camera': equipment_data.get('バックカメラ', False),
                'has_leather_seat': equipment_data.get('革シート', False),
                'has_bluetooth': equipment_data.get('Bluetooth接続', False),
                'is_published': False, 
            }
        )
        if image_urls: await save_car_images(new_car, image_urls)
        print("✅ すべて完了！")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())