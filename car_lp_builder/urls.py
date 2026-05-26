# car_lp_builder/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Vueからここに向かってデータを投げます
    path('generate-lp/', views.generate_lp_api, name='generate_lp_api'),


    # 🌟 新しくデータを読み込む道を追加！
    # <uuid:lp_id> とすることで、URLに入ってきた長いIDを変数として受け取れます
    path('detail/<uuid:lp_id>/', views.get_lp_detail, name='get_lp_detail'),
]