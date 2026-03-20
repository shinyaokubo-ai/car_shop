from django.shortcuts import render, get_object_or_404
from .models import Car

def stock_list(request):
    """ 在庫一覧を表示する """
    cars = Car.objects.all().order_by('-created_at')
    return render(request, 'cars/stock_list.html', {'cars': cars})

def car_detail(request, pk):
    """ 車両詳細を2列表示のHTMLに渡す """
    car = get_object_or_404(Car, pk=pk)
    # ここはシンプルに車データを渡すだけでOK。2列の振り分けはHTML側で行います。
    return render(request, 'cars/car_detail.html', {'car': car})

