from django.urls import path
from . import views

# 🌟 app_name は書かず、慎也さんの元のスタイルに戻しました
urlpatterns = [
    path('', views.stock_list, name='stock_list'),
    path('<int:pk>/', views.car_detail, name='car_detail'),
]