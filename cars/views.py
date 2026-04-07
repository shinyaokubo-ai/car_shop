from django.shortcuts import render, get_object_or_404
from .models import Car

def stock_list(request):
    """ 在庫一覧を表示する """
# ▼▼▼ 変更：.all() を .filter(is_published=True) に変えるだけ！ ▼▼▼
    cars = Car.objects.filter(is_published=True).order_by('-created_at')
    # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲




    return render(request, 'cars/stock_list.html', {'cars': cars})

def car_detail(request, pk):
    """ 車両詳細を2列表示のHTMLに渡す """
    
# 詳細ページも、URL直打ちで非公開の車を見られないようにガードをかけます
    car = get_object_or_404(Car, pk=pk, is_published=True)
    return render(request, 'cars/car_detail.html', {'car': car})