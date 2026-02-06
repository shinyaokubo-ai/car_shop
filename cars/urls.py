from django.urls import path
from . import views

urlpatterns = [
    # http://127.0.0.1:8000/ にアクセスしたら一覧を表示
    path('', views.stock_list, name='stock_list'),

    # ★追加： <int:pk> は「整数のIDが入るよ」という意味です
    path('<int:pk>/', views.car_detail, name='car_detail')
]