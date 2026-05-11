from django.contrib import admin
from .models import Brand, Product, Category, Banner


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "is_active"]


admin.site.register(Banner)
