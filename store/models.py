from decimal import Decimal
from django.db import models
from django.db.models import Q, Sum
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey
from PIL import Image
from tools.get_upload_path import get_upload_path
from tools.slug import generate_unique_slug
from core.mixins.image_mixins import ImageMixin

from core.paths.upload import (
    original_upload_path,
    thumb_upload_path,
    medium_upload_path,
)


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


class Banner(models.Model):
    name = models.CharField(max_length=255)
    link = models.URLField(blank=True)
    order = models.IntegerField(blank=True, default=0)
    decristion_short = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to=get_upload_path)
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


class Category(MPTTModel):
    name = models.CharField(max_length=255)
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    slug = models.SlugField(unique=True, blank=True)
    icon_code = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to=get_upload_path, blank=True)
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
        return f"{self.parent.name} > {self.name}" if self.parent else self.name

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
        if self.image:
            try:
                img = Image.open(self.image.path)
                if img.width > 32 or img.height > 32:
                    img.thumbnail((32, 32))
                    img.save(self.image.path, optimize=True, quality=70)
            except FileNotFoundError:
                pass

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
    class ColorChoice(models.TextChoices):
        BLACK = "BLACK", "Black"
        GOLD = "GOLD", "Gold"
        RED = "RED", "Red"

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
    color = models.CharField(
        max_length=20, choices=ColorChoice.choices, default=ColorChoice.BLACK
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


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PAID = "PAID", "Paid"
        SHIPPED = "SHIPPED", "Shipped"
        CANCELLED = "CANCELLED", "Cancelled"

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="order_items"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    @property
    def subtotal(self):
        return self.price * self.quantity


class ProductImage(ImageMixin, models.Model):
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
    resize_mode = "crop"

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
    def imageURL(self):
        return self.image.url if self.image else "/static/images/default/default.png"

    def save(self, *args, **kwargs):
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).exclude(
                pk=self.pk
            ).update(is_main=False)

        super().save(*args, **kwargs)
        try:
            img = Image.open(self.image.path)
            if img.width > 800 or img.height > 800:
                img.thumbnail((800, 800))
                img.save(self.image.path, optimize=True, quality=70)
        except FileNotFoundError:
            pass
