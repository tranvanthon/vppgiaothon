from django import forms
from .models import Product, ProductImage
from django.forms import DateInput, DateTimeInput


class ProductUpdateForm(forms.ModelForm):
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
            "color",
            "meta_title",
            "meta_description",
            "meta_keywords",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if isinstance(field, forms.DateField):
                self.fields[field_name].widget = forms.DateInput(
                    attrs={
                        "type": "date",
                        "class": "form-control",
                    }
                )

            elif isinstance(field, forms.DateTimeField):
                self.fields[field_name].widget = forms.DateTimeInput(
                    attrs={
                        "type": "datetime-local",
                        "class": "form-control",
                    }
                )

            # Các field khác vẫn thêm form-control như cũ
            else:
                widget = self.fields[field_name].widget
                try:
                    if widget.input_type not in ("checkbox", "radio"):  # type: ignore
                        current_classes = widget.attrs.get("class", "")
                        widget.attrs["class"] = (
                            f"{current_classes} form-control".strip()
                        )
                except AttributeError:
                    # Textarea, hoặc widget không có input_type
                    current_classes = widget.attrs.get("class", "")
                    widget.attrs["class"] = f"{current_classes} form-control".strip()

                # Placeholder tùy chọn
                widget.attrs.setdefault(
                    "placeholder", field.label or field_name.replace("_", " ").title()
                )

        # Clock field
        if self.instance and self.instance.pk:
            locked_fields = [
                "name",
            ]
            for field_name in locked_fields:
                self.fields[field_name].widget.attrs.update(
                    {
                        "readonly": True,
                        "class": "form-control bg-light text-muted",  # Bootstrap 5 style mờ
                        "style": "opacity: 0.7; cursor: not-allowed;",
                    }
                )
