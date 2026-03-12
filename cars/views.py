from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Car, CarImage

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

def car_image_upload(request, pk):
    """ ドロップされた画像を受け取って保存する処理 """
    car = get_object_or_404(Car, pk=pk)

    if request.method == 'POST':
        # 画面から投げ込まれた画像たちと、カテゴリー(外装or内装)を受け取る
        images = request.FILES.getlist('images')
        category = request.POST.get('category', 'exterior')

        # 1枚ずつCloudinary＆データベースに保存していく
        for img in images:
            CarImage.objects.create(car=car, image=img, category=category)

        return JsonResponse({'status': 'success', 'message': 'アップロード成功！'})

    # 通常のアクセス時は、アップロード画面（HTML）を表示する
    return render(request, 'cars/image_upload.html', {'car': car})