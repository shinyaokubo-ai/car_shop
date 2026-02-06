from django.shortcuts import render, get_object_or_404
from .models import Car

def stock_list(request):
    # 在庫車をすべて取得
    cars = Car.objects.all().order_by('-created_at')
    return render(request, 'cars/stock_list.html', {'cars': cars})

def car_detail(request, pk):
    # 指定されたIDの車を取得（なければ404エラー）
    car = get_object_or_404(Car, pk=pk)
    
    # ★ここが修正ポイント
    # 写真の分類はHTML側（car_detail.html）で行うので、
    # 余計なフィルタリング処理を削除して、シンプルに車データだけを渡します。
    return render(request, 'cars/car_detail.html', {'car': car})