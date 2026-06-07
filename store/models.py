from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, Sum
from django.urls import reverse
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey
from PIL import Image

from core.images.mixins import ImageOptimizationsMixin
from core.images.paths import (
    original_upload_path,
)
from tools.slug import generate_unique_slug


class ActiveManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Brand(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name, "slug")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Banner(ImageOptimizationsMixin, models.Model):
    name = models.CharField(max_length=255)
    link = models.URLField(blank=True)
    order = models.IntegerField(blank=True, default=0)
    decristion_short = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to=original_upload_path)
    is_active = models.BooleanField(default=True, db_default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            try:
                img = Image.open(self.image.path)
                if img.width > 800 or img.height > 800:
                    img.thumbnail((800, 800))
                    img.save(self.image.path, optimize=True, quality=70)
            except FileNotFoundError:
                pass


class Category(ImageOptimizationsMixin, MPTTModel):
    name = models.CharField(max_length=255)
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    slug = models.SlugField(unique=True, blank=True)
    icon_code = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to=original_upload_path, blank=True, null=True)
    is_active = models.BooleanField(default=True, db_default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=500, blank=True)
    meta_keywords = models.CharField(max_length=300, blank=True)

    objects = models.Manager()
    active = ActiveManager()

    class MPTTMeta:
        order_insertion_by = ["display_order", "name"]

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("store:category_detail", kwargs={"slug": self.slug})

    @property
    def imageURL(self):
        return (
            self.image.url if self.image else "/static/images/default/category_icon.png"
        )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name, "slug")
        super().save(*args, **kwargs)

    def get_products_queryset(
        self, brand=None, min_price=None, max_price=None, sort=None, is_active=True
    ):
        category_ids = [self.id] + list(
            self.get_descendants().values_list("id", flat=True)
        )
        # Tối ưu select_related giảm lượng truy vấn đơn lẻ
        queryset = Product.objects.filter(category_id__in=category_ids).select_related(
            "brand", "category"
        )

        if is_active:
            queryset = queryset.filter(is_active=True)
        if brand:
            queryset = queryset.filter(brand__slug=brand)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        sort_mapping = {
            "price_asc": "price",
            "price_desc": "-price",
            "name_asc": "name",
            "name_desc": "-name",
        }
        if sort in sort_mapping:
            queryset = queryset.order_by(sort_mapping[sort])
        elif sort == "bestseller":
            queryset = queryset.annotate(sold=Sum("order_items__quantity")).order_by(
                "-sold"
            )
        else:
            queryset = queryset.order_by("-created_at")

        return queryset

    def get_grouped_products(self, limit=12, **kwargs):
        grouped_data = []
        children = self.children.filter(is_active=True)
        targets = children if children.exists() else [self]

        for child in targets:
            products = list(child.get_products_queryset(**kwargs)[:limit])
            if products:
                grouped_data.append({"category": child, "products": products})
        return grouped_data

    def get_homepage_preview(self):
        return self.get_grouped_products(limit=12)

    def restore(self):
        self.is_active = True
        self.save(update_fields=["is_active"])

    def delete(self):

        self.is_active = False
        self.save(update_fields=["is_active"])

    def hard_delete(self):

        super().delete()

    @property
    def total_product(self):
        return self.category_products.count()  # type: ignore

    @property
    def has_products(self):
        return self.total_product > 0


class Product(models.Model):

    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="category_products"
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="brand_products",
        null=True,
        blank=True,
    )
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=0, default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    sku = models.CharField(max_length=100, unique=True)
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    track_stock = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_sold = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    create_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
        blank=True,
        null=True,
    )

    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=500, blank=True)
    meta_keywords = models.CharField(max_length=300, blank=True)

    objects = models.Manager()
    active = ActiveManager()

    def get_absolute_url(self):
        return reverse("store:product_detail", kwargs={"slug": self.slug})

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name, "slug")
        super().save(*args, **kwargs)

    @property
    def is_bestseller(self):
        return self.sold_count >= 50

    @property
    def sold_count(self):
        total = self.order_items.filter(
            order__status__in=["PAID", "SHIPPED"]
        ).aggregate(total=Sum("quantity"))["total"]
        return total or 0

    @property
    def price_sale(self):
        if self.discount_percent == 0:
            return self.price
        return self.price - (self.price * self.discount_percent / Decimal("100"))

    @property
    def is_in_stock(self):
        return self.stock > 0 if self.track_stock else True

    @property
    def main_image(self):
        return self.images.filter(is_main=True).first() or self.images.first()

    @property
    def main_image_url(self):
        image = self.main_image

        if image:
            return image.medium_url

        return "/static/images/default/default.png"

    @property
    def main_image_original_url(self):
        image = self.main_image

        if image:
            return image.original_url

        return "/static/images/default/default.png"


class ProductVariant(models.Model):

    class ColorChoice(models.TextChoices):
        BLACK = "BLACK", "Black"
        GOLD = "GOLD", "Gold"
        RED = "RED", "Red"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )

    color = models.CharField(
        max_length=20,
        choices=ColorChoice.choices,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    stock = models.PositiveIntegerField(default=0)

    sku = models.CharField(
        max_length=100,
        unique=True,
    )


class ProductImage(ImageOptimizationsMixin, models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    is_main = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, db_index=True)
    image = models.ImageField(upload_to=original_upload_path)
    thumbnail = models.ImageField(
        blank=True,
        null=True,
        editable=False,
    )
    medium = models.ImageField(
        blank=True,
        null=True,
        editable=False,
    )

    class Meta:
        ordering = ["order"]
        unique_together = ("product", "order")
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=Q(is_main=True),
                name="unique_main_image_per_product",
            )
        ]

    @property
    def original_url(self):
        if self.image:
            return self.image.url
        return "/static/images/default/default.png"

    @property
    def thumb_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        return self.original_url

    @property
    def medium_url(self):
        if self.medium:
            return self.medium.url
        return self.original_url

    def save(self, *args, **kwargs):
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).exclude(
                pk=self.pk
            ).update(is_main=False)

        super().save(*args, **kwargs)


class Order(models.Model):
    # Trạng thái đơn hàng (mở rộng)
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Nháp"
        PENDING = "PENDING", "Chờ xử lý"
        CONFIRMED = "CONFIRMED", "Đã xác nhận"
        PACKED = "PACKED", "Đã đóng gói"
        SHIPPING = "SHIPPING", "Đang giao hàng"
        DELIVERED = "DELIVERED", "Đã giao"
        COMPLETED = "COMPLETED", "Hoàn thành"
        CANCELLED = "CANCELLED", "Đã hủy"

    # Phương thức thanh toán
    class PaymentMethod(models.TextChoices):
        COD = "COD", "Thanh toán khi nhận hàng"
        BANK = "BANK", "Chuyển khoản ngân hàng"
        MOMO = "MOMO", "Ví MoMo"
        ZALOPAY = "ZALOPAY", "ZaloPay"

    # Trạng thái thanh toán
    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Chưa thanh toán"
        AWAITING = "AWAITING", "Chờ thanh toán"
        PAID = "PAID", "Đã thanh toán"
        FAILED = "FAILED", "Thanh toán thất bại"
        REFUNDED = "REFUNDED", "Đã hoàn tiền"

    # Thông tin cơ bản
    order_number = models.CharField(
        max_length=50, unique=True, db_index=True, null=True, blank=True
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
        blank=True,
    )
    complete = models.BooleanField(default=False)

    # Thông tin người nhận
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, null=True)

    # Địa chỉ giao hàng (đã bỏ cấp huyện)
    province = models.CharField(max_length=100, blank=True)
    province_code = models.CharField(max_length=10, blank=True)
    district = models.CharField(
        max_length=100, blank=True
    )  # Giữ lại cho tương thích nhưng không dùng
    district_code = models.CharField(max_length=10, blank=True)
    ward = models.CharField(max_length=100, blank=True)
    ward_code = models.CharField(max_length=10, blank=True)
    hamlet = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True)
    full_address = models.TextField(blank=True)

    # Thanh toán
    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.COD
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    payment_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    # Số tiền
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Mã giảm giá
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    coupon_discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Ghi chú
    note = models.TextField(blank=True, null=True)
    admin_note = models.TextField(blank=True, null=True)

    # Tracking thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    packed_at = models.DateTimeField(blank=True, null=True)
    shipping_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["status"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"ĐH-{self.order_number}"

    def add_product(self, product, quantity=1):

        price = product.price_sale

        item, created = self.items.get_or_create(
            product=product,
            defaults={
                "price": price,
                "quantity": quantity,
                "total_price": price * quantity,
            },
        )

        if product.track_stock:

            new_quantity = quantity

            if not created:
                new_quantity = item.quantity + quantity

            if new_quantity > product.stock:
                raise ValidationError("Out of stock")

        if not created:
            item.quantity += quantity
            item.save(update_fields=["quantity"])

        return item

    def update_totals(self):
        """Cập nhật tổng tiền đơn hàng"""
        self.subtotal = self.items.aggregate(total=Sum("total_price"))["total"] or 0

        self.total_amount = (
            self.subtotal
            + self.shipping_fee
            - self.discount_amount
            - self.coupon_discount
        )

        self.save(
            update_fields=[
                "subtotal",
                "total_amount",
            ]
        )

    def can_cancel(self):
        """Kiểm tra có thể hủy đơn không"""
        return self.status in [self.Status.PENDING, self.Status.CONFIRMED]

    def cancel(self):
        """Hủy đơn hàng"""
        if self.can_cancel():
            self.status = self.Status.CANCELLED
            self.cancelled_at = timezone.now()
            self.save(update_fields=["status", "cancelled_at"])
            return True
        return False

    @property
    def status_display(self):
        """Hiển thị trạng thái bằng tiếng Việt"""
        return dict(self.Status.choices).get(self.status, self.status)

    @property
    def payment_method_display(self):
        """Hiển thị phương thức thanh toán bằng tiếng Việt"""
        return dict(self.PaymentMethod.choices).get(
            self.payment_method, self.payment_method
        )

    @property
    def payment_status_display(self):
        """Hiển thị trạng thái thanh toán bằng tiếng Việt"""
        return dict(self.PaymentStatus.choices).get(
            self.payment_status, self.payment_status
        )

    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="order_items"
    )
    product_name = models.CharField(
        max_length=255, blank=True
    )  # Lưu lại tên sản phẩm tại thời điểm mua
    product_image = models.CharField(max_length=500, blank=True)  # Lưu lại ảnh sản phẩm
    price = models.DecimalField(max_digits=15, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Lưu lại thông tin sản phẩm nếu chưa có
        if not self.product_name and self.product:
            self.product_name = self.product.name
            self.product_image = self.product.main_image_url

        self.total_price = self.price * self.quantity

        super().save(*args, **kwargs)

        self.order.update_totals()

    def delete(self, *args, **kwargs):

        order = self.order

        super().delete(*args, **kwargs)

        order.update_totals()

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.order.order_number} - {self.product_name or self.product.name} x{self.quantity}"
