from django.contrib import admin
from .models import Brand, Product, Category, Banner, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Name", {"fields": ["name"]}),
        ("Parent", {"fields": ["parent"]}),
        ("Slug", {"fields": ["slug"]}),
        ("Icon code", {"fields": ["icon_code"]}),
        ("Images", {"fields": ["image"]}),  # Thêm field image
        ("Status", {"fields": ["is_active", "is_featured", "display_order"]}),
    ]
    list_display = ["name", "is_active", "display_order"]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]


admin.site.register(Banner)
admin.site.register(Brand)
