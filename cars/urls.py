from django.urls import path
from . import views

urlpatterns = [
    # 在庫一覧ページ
    path('', views.stock_list, name='stock_list'),
    
    # 車両詳細ページ
    path('<int:pk>/', views.car_detail, name='car_detail'),
    
    # 画像アップロードページ
    path('<int:pk>/upload/', views.car_image_upload, name='car_image_upload'),
]