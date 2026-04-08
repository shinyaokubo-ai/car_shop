

from django.contrib import admin
from .models import Car, CarImage

class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 5
    fields = ('image', 'image_type')

# ▼▼ さっき解説したデコレータ！ ▼▼
@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    # ▼ 一覧画面に表示する項目（is_published を追加！）
    list_display = ('title', 'sku', 'price_total', 'is_published', 'is_sold_out')
    
    search_fields = ('title', 'sku')
    
    # ▼ 右側の絞り込みフィルター（is_published で公開・非公開を絞れるように追加！）
    list_filter = ('is_published', 'is_sold_out', 'is_new_arrival')
    
    # ▼ 一覧画面から直接チェックボックスをオンオフできる神機能！
    list_editable = ('is_published', 'is_sold_out')
    
    inlines = [CarImageInline]
    
    fieldsets = (
        ('基本情報', {
            # ▼ 詳細画面の基本情報エリアにも is_published を追加
            'fields': ('title', 'sku', 'price_total', 'price_vehicle', 'price_misc', 'is_published', 'is_sold_out', 'is_new_arrival')
        }),
        ('スペック概略', {
            'fields': ('registration_year', 'mileage', 'inspection', 'repair_history', 'body_color', 'interior_color', 'transmission', 'drive_system')
        }),
        ('詳細カタログスペック', {
            'fields': (
                'handle', 'import_route', 'model_code', 'production_country', 'production_period', 'new_car_price',
                'length', 'width', 'height', 'wheelbase', 'tread_front', 'tread_rear', 'weight',
                'door_count', 'capacity', 'seat_rows', 'transmission_pos', 'has_ai_shift', 'has_manual_mode', 'four_ws_status',
                'has_4wd_check', 'has_diesel'
            )
        }),
        ('詳細・動画', {
            'fields': ('comment', 'youtube_url')
        }),
        ('記述式詳細(装備タブへ表示)', {
            'fields': ('equipment_standard', 'equipment_option', 'equipment_custom')
        }),
        ('安全装備', {
            'fields': ('has_aircon', 'has_power_steering', 'has_power_window', 'has_airbag', 'has_abs', 'has_esc', 'has_collision_safety', 'has_lane_assist', 'has_park_assist', 'has_auto_parking', 'has_cruise_control', 'has_keyless', 'has_smart_key', 'has_etc', 'has_back_camera', 'has_camera_360',
                       'has_auto_highbeam', 'has_auto_light', 'has_fog_lamp')
        }),
        ('外装・内装装備', {
            'fields': ('has_sunroof', 'has_leather_seat', 'has_aluminum_wheel', 'has_aero_parts', 'has_low_down', 'has_lift_up', 'has_power_gate', 'has_led_headlight', 'has_hid_headlight', 'has_seat_heater', 'has_power_seat',
                       'has_seat_aircon', 'has_half_leather_seat', 'has_custom_muffler', 'has_full_aero', 'has_runflat_tire')
        }),
        ('ナビ・オーディオ', {
            'fields': ('has_hdd_navi', 'has_memory_navi', 'has_fullseg_tv', 'has_bluetooth', 'has_dvd', 'has_music_server', 'has_usb_input',
                       'has_music_player', 'has_cd', 'has_rear_monitor')
        }),
        ('車歴・書類', {
            'fields': ('has_one_owner', 'has_warranty', 'has_service_record', 'has_record_book', 'has_manual', 'has_spare_key')
        }),
    )

# デコレータを使ったので、元々一番下にあった admin.site.register(Car, CarAdmin) は不要になり消しました。
admin.site.register(CarImage)
