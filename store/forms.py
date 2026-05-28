from django import forms
from .models import Product, Category


class BootstrapModelForm(forms.ModelForm):
    """Class nền tảng tự động cấu hình Bootstrap 5 cho Form"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget

            # Ép kiểu dữ liệu hiển thị lịch cho Date/DateTime fields
            if isinstance(field, forms.DateField):
                widget.attrs.update({"type": "date"})
            elif isinstance(field, forms.DateTimeField):
                widget.attrs.update({"type": "datetime-local"})

            # Tự động thêm class form-control (trừ checkbox và radio)
            if not getattr(widget, "input_type", None) in ("checkbox", "radio"):
                current_classes = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{current_classes} form-control".strip()

            # Tạo placeholder tự động dựa trên Label của Field
            widget.attrs.setdefault(
                "placeholder", field.label or field_name.replace("_", " ").title()
            )

    def lock_specific_fields(self, locked_fields):
        """Khóa cứng các trường không cho phép chỉnh sửa khi cập nhật"""
        if self.instance and self.instance.pk:
            for field_name in locked_fields:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs.update(
                        {
                            "readonly": True,
                            "class": "form-control bg-light text-muted",
                            "style": "opacity: 0.7; cursor: not-allowed;",
                        }
                    )


class CategoryUpdateForm(BootstrapModelForm):
    class Meta:
        model = Category
        fields = [
            "name",
            "parent",
            "icon_code",
            "image",
            "is_featured",
            "meta_title",
            "meta_description",
            "meta_keywords",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock_specific_fields(
            ["name"]
        )  # Bảo vệ không cho đổi tên danh mục tránh hỏng slug


class ProductUpdateForm(BootstrapModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "brand",
            "category",
            "description",
            "price",
            "sku",
            "discount_percent",
            "cost_price",
            "stock",
            "meta_title",
            "meta_description",
            "meta_keywords",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock_specific_fields(["name"])  # Bảo vệ tên sản phẩm khi update
