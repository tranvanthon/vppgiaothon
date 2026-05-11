from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
from tools.get_upload_path import get_upload_path
from tools.slug import generate_unique_slug
from django.utils.text import slugify


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

    objects = models.Manager()
    active = ActiveManager()

    def __str__(self):
        return self.name


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
        descendant_ids = self.get_descendants_ids()
        return Product.active.filter(category_id__in=descendant_ids).count()

    @product_count.setter
    def product_count(self, value):
        import warnings

        warnings.warn(
            "Setting product_count manually is deprecated. This value is auto-calculated."
        )
        pass

    @property
    def total_sold(self):
        """Tổng số lượng đã bán của category (tính cả category con)"""
        descendant_ids = self.get_descendants_ids()
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
    # Trạng thái sản phẩm
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, verbose_name="Product is featured")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date publish")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date update")

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

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name, "slug")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
