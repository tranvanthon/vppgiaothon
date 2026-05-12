from django.db.models import Q
from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
from tools.get_upload_path import get_upload_path
from tools.slug import generate_unique_slug
from django.utils.text import slugify
from django.db.models import Count, Sum
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.conf import settings
from PIL import Image
from decimal import Decimal


# Ban dieu kien kich hoat
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Brand(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name, "slug")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Banner(models.Model):
    name = models.CharField(max_length=255)
    link = models.URLField(blank=True)
    order = models.IntegerField(blank=True)
    decristion_short = models.CharField(max_length=255)
    image = models.ImageField(upload_to=get_upload_path)
    is_active = models.BooleanField(default=True, db_default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if old.image == self.image:
                return super().save(*args, **kwargs)

        super().save(*args, **kwargs)

        if self.image:
            try:
                img = Image.open(self.image.path)

                if img.width > 800 or img.height > 800:
                    img.thumbnail((800, 800))

                img.save(self.image.path, optimize=True, quality=70)

            except FileNotFoundError:
                print("Image file not found, skip processing")


class Category(MPTTModel):
    name = models.CharField(max_length=255)
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    slug = models.SlugField(unique=True, blank=True)
    icon_code = models.CharField(max_length=150, blank=True)
    # status and show
    is_active = models.BooleanField(default=True, db_default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    # SEO
    meta_title = models.CharField(max_length=200, blank=True, verbose_name="Meta Title")
    meta_description = models.TextField(
        max_length=500, blank=True, verbose_name="Meta Description"
    )
    meta_keywords = models.CharField(
        max_length=300, blank=True, verbose_name="Meta Keywords"
    )

    # Gọi manager
    objects = models.Manager()
    active = ActiveManager()

    class MPTTMeta:
        order_insertion_by = ["display_order", "name"]

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(fields=["name", "is_active"]),
            models.Index(fields=["parent", "is_active"]),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def get_absolute_url(self):
        return reverse("store:category_detail", kwargs={"slug": self.slug})

    @property
    def active_children(self):
        return self.children.filter(is_active=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name, "slug")
        super().save(*args, **kwargs)

    @property
    def product_count(self):
        """Tổng số sản phẩm (tính cả category con)"""
        descendant_ids = self.get_descendants(include_self=True)
        return Product.active.filter(category_id__in=descendant_ids).count()

    @product_count.setter
    def product_count(self, value):
        import warnings

        warnings.warn(
            "Setting product_count manually is deprecated. This value is auto-calculated."
        )
        pass

    def get_products_queryset(
        self, brand=None, min_price=None, max_price=None, sort=None, is_active=True
    ):
        """Lấy products của category (bao gồm cả subcategories)"""
        # Lấy ID của category hiện tại và tất cả descendants
        category_ids = [self.id] + list(
            self.get_descendants().values_list("id", flat=True)
        )

        # Base queryset
        queryset = Product.objects.filter(category_id__in=category_ids)

        # Filter active
        if is_active:
            queryset = queryset.filter(is_active=True)

        # Filter by brand
        if brand:
            queryset = queryset.filter(brand__slug=brand)

        # Filter by price
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Sorting
        if sort == "price_asc":
            queryset = queryset.order_by("price")
        elif sort == "price_desc":
            queryset = queryset.order_by("-price")
        elif sort == "name_asc":
            queryset = queryset.order_by("name")
        elif sort == "name_desc":
            queryset = queryset.order_by("-name")
        elif sort == "bestseller":
            queryset = queryset.annotate(sold=Sum("order_items__quantity")).order_by(
                "-sold"
            )
        else:  # default: newest
            queryset = queryset.order_by("-created_at")

        return queryset

    def get_grouped_products(self, limit=12, **kwargs):

        grouped_data = []

        children = self.children.filter(is_active=True)

        if not children.exists():
            children = [self]

        for child in children:

            products = list(child.get_products_queryset(**kwargs)[:limit])

            if products:
                grouped_data.append(
                    {
                        "category": child,
                        "products": products,
                    }
                )

        return grouped_data

    def get_homepage_preview(self):
        """Chỉ lấy 12 sản phẩm đầu tiên từ kết quả đã gom nhóm để hiển thị trang chủ"""
        return self.get_grouped_products(limit=12)

    @property
    def total_sold(self):
        """Tổng số lượng đã bán của category (tính cả category con)"""
        descendant_ids = self.get_descendants(include_self=True)
        return (
            OrderItem.objects.filter(
                product__category_id__in=descendant_ids,
                order__status__in=["PAID", "SHIPPED"],
            ).aggregate(total=Sum("quantity"))["total"]
            or 0
        )

    def delete(self, *args, **kwargs):
        """Vô hiệu hoá thay vì xoá"""
        if self.category_products.filter(is_active=True).exists():
            raise ValidationError("Cannot delete category with active products")
        self.is_active = False
        self.save(update_fields=["is_active"])

    def hard_delete(self, *args, **kwargs):
        """Xoá thật"""
        super().delete(*args, **kwargs)


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
        related_name="brand_brands",
        null=True,
        blank=True,
    )
    slug = models.SlugField(unique=True, blank=True)

    # Mô tả sản phẩm
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=300, blank=True)

    # Thông tin giá và tồn kho
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=0, default=0)
    cost_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Import price", default=10.00
    )
    sku = models.CharField(max_length=100, unique=True, verbose_name="Code SKU")
    # Quản lý tồn kho
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    low_stock_threshold = models.PositiveIntegerField(
        default=5, verbose_name="Low inventory alert threshold"
    )
    track_stock = models.BooleanField(default=True, verbose_name="Inventory tracking")
    # Trạng thái sản phẩm
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, verbose_name="Product is featured")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date publish")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date update")
    # Thông số kỹ thuật
    color = models.CharField(
        max_length=20, choices=ColorChoice.choices, default=ColorChoice.BLACK
    )
    # SEO
    meta_title = models.CharField(max_length=200, blank=True, verbose_name="Meta Title")
    meta_description = models.TextField(
        max_length=500, blank=True, verbose_name="Meta Description"
    )
    meta_keywords = models.CharField(
        max_length=300, blank=True, verbose_name="Meta Keywords"
    )
    # Category manager
    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name", "is_active"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("store:product_detail", kwargs={"slug": self.slug})

    @property
    def is_bestseller(self):
        """Tự động xác định bestseller (bán > 50 sản phẩm)"""
        return self.sold_count >= 50

    @property
    def sold_count(self):
        """Tổng số lượng đã bán (từ OrderItem)"""
        total = self.order_items.filter(
            order__status__in=["PAID", "SHIPPED"]
        ).aggregate(total=Sum("quantity"))["total"]
        return total or 0

    @property
    def view_count(self):
        """Số lượt xem - tính từ bảng riêng (nên tạo sau)"""
        # Tạm thời trả về 0, sau này có thể tracking bằng middleware
        return 0

    @property
    def total_revenue(self):
        """Tổng doanh thu từ sản phẩm này"""
        revenue = self.order_items.filter(
            order__status__in=["PAID", "SHIPPED"]
        ).aggregate(total=Sum("subtotal"))["total"]
        return revenue or 0

    @property
    def price_sale(self):
        """Giá sau khi giảm giá"""
        if self.discount_percent == 0:
            return self.price
        discount_amount = (self.price * self.discount_percent) / Decimal("100")
        return self.price - discount_amount

    @property
    def is_in_stock(self):
        """Kiểm tra còn hàng không"""
        return self.stock > 0 if self.track_stock else True

    @property
    def is_low_stock(self):
        """Kiểm tra hàng sắp hết"""
        return self.track_stock and self.stock <= self.low_stock_threshold

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name, "slug")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Order(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PAID = "PAID", "Paid"
        SHIPPED = "SHIPPED", "Shipped"
        CANCELLED = "CANCELLED", "Cancelled"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def can_be_cancelled(self):
        return self.status in [
            self.Status.DRAFT,
            self.Status.PAID,
        ]

    # Thêm sản phẩm vào cart
    def add_product(self, product, quantity=1):
        item, created = self.items.get_or_create(
            product=product, defaults={"price": product.price}
        )

        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()

    # Cập nhật giỏ hàng
    def update_item(self, product, quantity=1):
        try:
            item = self.items.get(product=product)
            if quantity <= 0:
                item.delete()
            else:
                item.quantity = quantity
                item.save()

        except OrderItem.DoesNotExist:
            pass

    @property
    def get_total(self):
        return sum(item.subtotal for item in self.items.all())

    class Meta:
        ordering = ["-created_at"]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="order_items"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        indexes = [
            models.Index(fields=["order", "product"]),
        ]

    @property
    def subtotal(self):
        return self.price * self.quantity

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")
        if not self.product.is_in_stock():
            raise ValidationError("Product is out of stock")


# Images for product
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="images"
    )
    image = models.ImageField(upload_to=get_upload_path)
    is_main = models.BooleanField(default=False)
    order = models.PositiveIntegerField(
        default=0, db_index=True
    )  # db_indext = True Giúp dữ liệu nhanh hơn

    class Meta:
        verbose_name = "ProductImage"
        verbose_name_plural = "Images of Product"
        ordering = ["order"]
        unique_together = (
            "product",
            "order",
        )  # Khi nào gặp lỗi: Tùy chọn, tránh trùng order trong 1 product

        constraints = [
            # Đảm bảo chỉ có 1 ảnh chính
            models.UniqueConstraint(
                fields=["product"],
                condition=Q(is_main=True),
                name="unique_main_image_per_product",
            )
        ]

    def __str__(self):
        return f"{self.product.name} image"

    # Chua dung den
    def get_absolute_url(self):
        return reverse("store:product_detail", kwargs={"slug": self.slug})

    # Tối ưu ảnh

    def save(self, *args, **kwargs):
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if old.image == self.image:
                return super().save(*args, **kwargs)

        super().save(*args, **kwargs)

        if self.image:
            try:
                img = Image.open(self.image.path)

                if img.width > 800 or img.height > 800:
                    img.thumbnail((800, 800))

                img.save(self.image.path, optimize=True, quality=70)

            except FileNotFoundError:
                print("Image file not found, skip processing")

    @property
    def imageURL(self):
        if self.image:
            return self.image.url
        return "/static/images/default/default.png"
