from cloudinary.models import CloudinaryField
from django.db import models

class Car(models.Model):
    # --- 基本情報 ---
    title = models.CharField("車名", max_length=100)
    sku = models.CharField("管理番号", max_length=50, unique=True)
    price_total = models.PositiveIntegerField("支払総額(税込)")
    price_vehicle = models.PositiveIntegerField("車両本体価格")
    price_misc = models.PositiveIntegerField("諸費用")
    
    # --- 基本スペック（既存） ---
    registration_year = models.CharField("年式(初年度登録)", max_length=50)
    mileage = models.CharField("走行距離", max_length=50)
    inspection = models.CharField("車検", max_length=50)
    repair_history = models.CharField("修復歴", max_length=20, choices=[('あり', 'あり'), ('なし', 'なし')], default='なし')
    body_color = models.CharField("ボディカラー", max_length=50)
    transmission = models.CharField("ミッション", max_length=50, default="AT")
    drive_system = models.CharField("駆動方式", max_length=50, blank=True, null=True, default="4WD")

    # --- 詳細スペック ---
    handle = models.CharField("ハンドル", max_length=20, choices=[('右', '右'), ('左', '左')], default='右')
    import_route = models.CharField("輸入経路", max_length=50, choices=[('ディーラー車', 'ディーラー車'), ('並行輸入車', '並行輸入車')], default='ディーラー車')
    interior_color = models.CharField("内装色", max_length=50, blank=True)
    length = models.CharField("全長(cm)", max_length=20, blank=True)
    width = models.CharField("全幅(cm)", max_length=20, blank=True)
    height = models.CharField("全高(cm)", max_length=20, blank=True)
    production_country = models.CharField("生産国", max_length=50, blank=True)
    production_period = models.CharField("生産期間", max_length=50, blank=True)
    new_car_price = models.CharField("新車時車両価格", max_length=50, blank=True)
    model_code = models.CharField("型式", max_length=50, blank=True)
    wheelbase = models.CharField("ホイールベース(mm)", max_length=20, blank=True)
    tread_front = models.CharField("前トレッド(mm)", max_length=20, blank=True)
    tread_rear = models.CharField("後トレッド(mm)", max_length=20, blank=True)
    weight = models.CharField("車体重量(kg)", max_length=20, blank=True)
    door_count = models.CharField("ドア数", max_length=20, blank=True)
    capacity = models.CharField("乗車定員", max_length=20, blank=True)
    seat_rows = models.CharField("シート列数", max_length=20, blank=True)
    transmission_pos = models.CharField("ミッション位置", max_length=50, blank=True)
    has_ai_shift = models.BooleanField("AI-SHIFT", default=False)
    has_manual_mode = models.BooleanField("マニュアルモード", default=False)
    four_ws_status = models.CharField("4WS", max_length=10, blank=True, default="△")
    
    # 🌟追加：基本スペック系のチェック項目
    has_4wd_check = models.BooleanField("4WD(チェックボックス)", default=False)
    has_diesel = models.BooleanField("ディーゼル", default=False)
    
    # --- 状態フラグ ---
    is_sold_out = models.BooleanField("SOLD OUT", default=False)
    is_new_arrival = models.BooleanField("新規入庫", default=False)
    
    # --- 安全装備 ---
    has_aircon = models.BooleanField("エアコン", default=False)
    has_power_steering = models.BooleanField("パワステ", default=False)
    has_power_window = models.BooleanField("パワーウィンドウ", default=False)
    has_airbag = models.BooleanField("エアバック", default=False)
    has_abs = models.BooleanField("ABS", default=False)
    has_esc = models.BooleanField("ESC(横滑り防止)", default=False)
    has_collision_safety = models.BooleanField("衝突被害軽減ブレーキ", default=False)
    has_lane_assist = models.BooleanField("レーンアシスト", default=False)
    has_park_assist = models.BooleanField("パークアシスト", default=False)
    has_auto_parking = models.BooleanField("自動駐車システム", default=False)
    has_cruise_control = models.BooleanField("クルーズコントロール", default=False)
    has_keyless = models.BooleanField("キーレス", default=False)
    has_smart_key = models.BooleanField("スマートキー", default=False)
    has_etc = models.BooleanField("ETC", default=False)
    has_back_camera = models.BooleanField("バックカメラ", default=False)
    has_camera_360 = models.BooleanField("全周囲カメラ", default=False)
    # 🌟追加：安全装備系の新項目
    has_auto_highbeam = models.BooleanField("オートマチックハイビーム", default=False)
    has_auto_light = models.BooleanField("オートライト", default=False)
    has_fog_lamp = models.BooleanField("フォグランプ", default=False)
    
    # --- 外装・内装装備 ---
    has_sunroof = models.BooleanField("サンルーフ", default=False)
    has_leather_seat = models.BooleanField("革シート", default=False)
    has_aluminum_wheel = models.BooleanField("アルミホイール", default=False)
    has_aero_parts = models.BooleanField("エアロパーツ", default=False)
    has_low_down = models.BooleanField("ローダウン", default=False)
    has_lift_up = models.BooleanField("リフトアップ", default=False)
    has_power_gate = models.BooleanField("電動リアゲート", default=False)
    has_led_headlight = models.BooleanField("LEDヘッドライト", default=False)
    has_hid_headlight = models.BooleanField("HIDヘッドライト", default=False)
    has_seat_heater = models.BooleanField("シートヒーター", default=False)
    has_power_seat = models.BooleanField("パワーシート", default=False)
    # 🌟追加：外装・内装系の新項目
    has_seat_aircon = models.BooleanField("シートエアコン", default=False)
    has_half_leather_seat = models.BooleanField("ハーフレザーシート", default=False)
    has_custom_muffler = models.BooleanField("社外マフラー", default=False)
    has_full_aero = models.BooleanField("フルエアロ", default=False)
    has_runflat_tire = models.BooleanField("ランフラットタイヤ", default=False)
    
    # --- ナビ・オーディオ ---
    has_hdd_navi = models.BooleanField("HDDナビ", default=False)
    has_memory_navi = models.BooleanField("メモリーナビ", default=False)
    has_fullseg_tv = models.BooleanField("フルセグTV", default=False)
    has_bluetooth = models.BooleanField("Bluetooth接続", default=False)
    has_dvd = models.BooleanField("DVD再生", default=False)
    has_music_server = models.BooleanField("ミュージックサーバー", default=False)
    has_usb_input = models.BooleanField("USB入力端子", default=False)
    # 🌟追加：ナビ・オーディオ系の新項目
    has_music_player = models.BooleanField("ミュージックプレイヤー接続", default=False)
    has_cd = models.BooleanField("CD再生", default=False)
    has_rear_monitor = models.BooleanField("後席モニター", default=False)

    # --- 車歴・書類 ---
    has_one_owner = models.BooleanField("ワンオーナー", default=False)
    has_warranty = models.BooleanField("保証書", default=False)
    has_service_record = models.BooleanField("整備手帳", default=False)
    has_record_book = models.BooleanField("記録簿", default=False)
    has_manual = models.BooleanField("取扱説明書", default=False)
    has_spare_key = models.BooleanField("スペアキー", default=False)

    # --- 詳細テキスト ---
    comment = models.TextField("車両詳細コメント", blank=True)
    equipment_standard = models.TextField("標準装備(詳細)", blank=True)
    equipment_option = models.TextField("オプション装備(詳細)", blank=True)
    equipment_custom = models.TextField("カスタム装備(詳細)", blank=True)
    youtube_url = models.URLField("YouTube URL", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_main_image_url(self):
        img = self.images.first()
        return img.image.url if img else None

# (※この上に、すでにある Car モデルなどのコードが書かれている状態にしてください)

class CarImage(models.Model):
    """ 車両の画像（複数枚）を保存するモデル """
    
    # 🌟 内装と外装を区別するための選択肢
    CATEGORY_CHOICES = (
        ('exterior', '外装'),
        ('interior', '内装'),
    )

    # どの車に紐づく画像か（Carモデルと連携）
    # ※もし車モデルの名前が 'Car' ではない場合（例えば 'Cars' など）、そこだけ書き換えてください
    car = models.ForeignKey('Car', on_delete=models.CASCADE, related_name='images')

    # Cloudinaryに保存される画像データ
    image = CloudinaryField('image')

    # 🌟 外装か内装かを記録するカラム（デフォルトは外装）
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        default='exterior', 
        verbose_name='画像カテゴリー'
    )

    # 画像が追加された日時（並び替え用）
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.car}の画像 ({self.get_category_display()})"