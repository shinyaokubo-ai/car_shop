import os
import re
import django
import asyncio
import urllib.request
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async

# Neonデータベースへの接続鍵
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_rc2lj6yutPKS@ep-purple-mud-a1zso0n2-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
call_command('migrate')  # 強制的にマイグレーションを実行する！

from cars.models import Car
from django.core.files.base import ContentFile

def extract_price(text):
    num_str = re.sub(r'\D', '', text)
    return int(num_str) if num_str else 0

@sync_to_async
def save_car_images(car, image_urls):
    car.images.all().delete() # 古い画像をリセット
    print(f"\n☁️ 画像をGoogle Cloud Storageにアップロード中...（最大15枚 / 少し時間がかかります）")
    
    for idx, url in enumerate(image_urls[:15]): 
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                img_data = response.read()
                img_name = f"{car.sku}_{idx}.jpg"
                
                if idx < 8:
                    img_type = 'exterior'
                else:
                    img_type = 'interior'
                
                car.images.create(
                    image=ContentFile(img_data, name=img_name),
                    image_type=img_type
                )
                print(f"   📸 画像 {idx+1}/15 枚目の保存完了！({img_type}として登録)")
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

        print("🖼️ 画像URLを探索中...")
        image_urls = []
        img_locators = await page.locator('img').all()
        for img in img_locators:
            src = await img.get_attribute('src')
            if src and 'static.wixstatic.com/media/' in src and src not in image_urls:
                # 🌟 ロゴやアイコンを除外する処理
                if 'logo' in src.lower() or 'icon' in src.lower():
                    continue
                image_urls.append(src)
        
        # 🌟 念のための保険（もし1枚目がどうしてもロゴになってしまう場合、先頭をカット）
        if len(image_urls) > 0 and '1b3d68_' in image_urls[0]: # Y'sさんのロゴの特有のファイル名を弾く
             image_urls = image_urls[1:]

        tread_str = car_data.get('前トレッド/後トレッド', '')
        tread_f = tread_str.split('/')[0].replace('（mm）','').strip() if '/' in tread_str else ''
        tread_r = tread_str.split('/')[1].replace('（mm）','').strip() if '/' in tread_str else ''

        print("\n🚀 データベース（Neon）へ登録を開始します...")
        
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
                
                # ▼▼ 新しく追加したフラグ（Falseのままなので非公開になります） ▼▼
                'is_published': False, 
            }
        )

        if image_urls:
            await save_car_images(new_car, image_urls)

        print("✅ すべての処理が完了しました！管理画面で確認し、チェックを入れて公開してください。")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())