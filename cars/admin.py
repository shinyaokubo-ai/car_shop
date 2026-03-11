from django.contrib import admin
from .models import Car, CarImage

class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 5
    fields = ('image', 'image_type') 

class CarAdmin(admin.ModelAdmin):
    list_display = ('title', 'sku', 'price_total', 'is_sold_out')
    search_fields = ('title', 'sku')
    list_filter = ('is_sold_out', 'is_new_arrival')
    inlines = [CarImageInline]
    
    fieldsets = (
        ('基本情報', {
            'fields': ('title', 'sku', 'price_total', 'price_vehicle', 'price_misc', 'is_sold_out', 'is_new_arrival')
        }),
        ('スペック概略', {
            'fields': ('registration_year', 'mileage', 'inspection', 'repair_history', 'body_color', 'interior_color', 'transmission', 'drive_system')
        }),
        ('詳細カタログスペック', {
            'fields': (
                'handle', 'import_route', 'model_code', 'production_country', 'production_period', 'new_car_price',
                'length', 'width', 'height', 'wheelbase', 'tread_front', 'tread_rear', 'weight',
                'door_count', 'capacity', 'seat_rows', 'transmission_pos', 'has_ai_shift', 'has_manual_mode', 'four_ws_status',
                'has_4wd_check', 'has_diesel' # 🌟追加
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
                       'has_auto_highbeam', 'has_auto_light', 'has_fog_lamp') # 🌟追加
        }),
        ('外装・内装装備', {
            'fields': ('has_sunroof', 'has_leather_seat', 'has_aluminum_wheel', 'has_aero_parts', 'has_low_down', 'has_lift_up', 'has_power_gate', 'has_led_headlight', 'has_hid_headlight', 'has_seat_heater', 'has_power_seat',
                       'has_seat_aircon', 'has_half_leather_seat', 'has_custom_muffler', 'has_full_aero', 'has_runflat_tire') # 🌟追加
        }),
        ('ナビ・オーディオ', {
            'fields': ('has_hdd_navi', 'has_memory_navi', 'has_fullseg_tv', 'has_bluetooth', 'has_dvd', 'has_music_server', 'has_usb_input',
                       'has_music_player', 'has_cd', 'has_rear_monitor') # 🌟追加
        }),
        ('車歴・書類', {
            'fields': ('has_one_owner', 'has_warranty', 'has_service_record', 'has_record_book', 'has_manual', 'has_spare_key')
        }),
    )

admin.site.register(Car, CarAdmin)