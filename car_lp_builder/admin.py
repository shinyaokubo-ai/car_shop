# car_lp_builder/admin.py
from django.contrib import admin
from .models import CarListing

@admin.register(CarListing)
class CarListingAdmin(admin.ModelAdmin):
    list_display = ('car_name', 'status', 'created_at', 'id')
    list_filter = ('status',)
    search_fields = ('car_name', 'id')