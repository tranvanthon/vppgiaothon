from django.contrib import messages
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import DetailView, CreateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Q
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from collections import OrderedDict
from tools.breadcrumb_utils import get_breadcrumb
from .models import Product, Banner, Category, Brand, ProductImage
from tools.breadcrumb_utils import get_breadcrumb
from django.contrib.messages.views import SuccessMessageMixin
from store.forms import ProductUpdateForm


class ProductDetailView(DetailView):
    model = Product
    fields = "__all__"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Product.objects.select_related("category")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        product = self.object  # type: ignore
        # Lấy các sản phẩm liên quan (cùng danh mục) trừ chính nó
        context["related_products"] = (
            Product.objects.filter(category=product.category)
            .exclude(id=product.id)
            .distinct()[:4]
        )
        context["featured_products"] = Product.objects.filter(is_featured=True)[:4]
        context["categories"] = Category.objects.filter(
            parent__isnull=True
        ).prefetch_related("children")

        return context


# Dat anh lam anh chinh
def set_main_image(request, pk):
    img = get_object_or_404(ProductImage, pk=pk)
    product = img.product

    # Reset toan bo
    ProductImage.objects.filter(product=product).update(is_main=False)
    # Set image curent
    img.is_main = True
    img.save(update_fields=["is_main"])

    return redirect("store:product_detail", slug=product.slug)


class ProducUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductUpdateForm
    template_name_suffix = "_update_form"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    success_message = "Update product successfully!"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Save Update"
        return context

    def form_valid(self, form):

        response = super().form_valid(form)

        images = self.request.FILES.getlist("images")

        # lấy order lớn nhất hiện tại
        last_order = ProductImage.objects.filter(product=self.object).count()

        for index, img in enumerate(images):

            ProductImage.objects.create(
                product=self.object,
                image=img,
                order=last_order + index,
            )

        return response


class ProductCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    success_message = "Đã tạo sản phẩm thành công: %(name)s"
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
    success_url = reverse_lazy("store:product_create")

    def form_valid(self, form):

        # ✅ Lưu product trước
        response = super().form_valid(form)

        # ✅ Lưu multiple images
        images = self.request.FILES.getlist("images")
        for index, img in enumerate(images):
            ProductImage.objects.create(
                product=self.object,
                order=index,
                image=img,
                is_main=(index == 0),  # ảnh đầu tiên là ảnh chính
            )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create product"
        return context


class CategoryDetailView(DetailView):
    model = Category
    context_object_name = "category"

    def get_object(self):
        return get_object_or_404(Category.active, slug=self.kwargs["slug"])

    def get(self, request, *args, **kwargs):
        # Thêm custom breadcrumb
        category = self.get_object()

        # Tạo breadcrumb cho category hierarchy
        breadcrumb_items = OrderedDict()

        # Xây dựng đường dẫn đầy đủ các category cha
        ancestors = []
        current = category
        while current:
            ancestors.insert(0, current)
            current = current.parent

        # Thêm từng cấp vào breadcrumb
        for cat in ancestors:
            breadcrumb_items[cat.name] = reverse(
                "store:category_detail", kwargs={"slug": cat.slug}
            )

        # Gán vào request để context processor sử dụng
        request.custom_breadcrumb = breadcrumb_items

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object

        # Tạo breadcrumb riêng cho category
        context["breadcrumb"] = get_breadcrumb(category=category)

        brand = self.request.GET.get("brand")
        min_p = self.request.GET.get("min_price")
        max_p = self.request.GET.get("max_price")
        sort = self.request.GET.get("sort")
        grouped_products = category.get_grouped_products(
            brand=brand,
            min_price=min_p,
            max_price=max_p,
            sort=sort,
        )
        products = category.get_products_queryset(
            brand=brand,
            min_price=min_p,
            max_price=max_p,
            sort=sort,
        )

        context["grouped_products"] = grouped_products

        # paginator
        paginator = Paginator(products, 12)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["page_obj"] = page_obj
        context["products"] = page_obj
        context["brands"] = Brand.objects.all()

        context["categories"] = Category.active.filter(
            parent__isnull=True
        ).prefetch_related("children", "chirldren__children")
        context["custom_breadcrumb"] = getattr(self.request, "custom_breadcrumb", {})
        return context


class CategoryListView(ListView):
    model = Category
    template_name = "store/category_list.html"
    context_object_name = "categories"
    paginate_by = 12

    def get_queryset(self):
        """Lấy danh sách category cha (level=0) đang active"""
        queryset = (
            Category.active.filter(parent__isnull=True)
            .select_related("parent")
            .prefetch_related("children")
            .annotate(
                direct_product_count=Count(
                    "category_products", filter=Q(category_products__is_active=True)
                ),
                active_children_count=Count(
                    "children", filter=Q(children__is_active=True)
                ),
            )
            .order_by("display_order", "name")
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Sử dụng hàm breadcrumb
        breadcrumbs = get_breadcrumb(
            category=None,  # Không có category cụ thể
            product=None,  # Không có product
            extra_items={"Danh mục sản phẩm": None},  # Item cuối cùng (current page)
        )

        context["breadcrumbs"] = breadcrumbs
        context["page_title"] = "Tất cả danh mục sản phẩm"
        context["meta_description"] = (
            "Khám phá các danh mục sản phẩm đa dạng tại cửa hàng của chúng tôi"
        )

        # Thêm featured categories
        context["featured_categories"] = Category.active.filter(
            is_featured=True, parent__isnull=True
        ).order_by("display_order")[:6]

        # Thống kê
        context["total_products"] = Product.active.count()
        context["total_categories"] = Category.active.filter(
            parent__isnull=True
        ).count()

        return context


class HomeView(ListView):
    model = Product
    template_name = "core/index.html"

    def get_queryset(self):
        return Product.active.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        root_categories = Category.active.filter(parent__isnull=True).order_by(
            "-created_at"
        )[:12]
        grouped_categories = []

        for cat in root_categories:
            preview = cat.get_homepage_preview()

            if preview:
                grouped_categories.append(
                    {
                        "main_category": cat,
                        "groups": preview,
                    }
                )

        banners = Banner.objects.filter(is_active=True).order_by("order")[:5]
        # Sản phẩm mới nhất
        latest_products = Product.active.order_by("-created_at")[:8]
        # Danh mục nổi bật
        featured_categories = (
            Category.active.filter(category_products__isnull=False)
            .annotate(product_count=Count("category_products"))
            .order_by("-product_count")[:8]
        )
        # Dùng property is_bestseller (tính tự động)
        best_sellers = [p for p in Product.active.all() if p.is_bestseller][:8]

        context.update(
            {
                "banners": banners,
                "latest_products": latest_products,
                "best_sellers": best_sellers,
                "featured_categories": featured_categories,
                "grouped_categories": grouped_categories,
                "title": "home",
            }
        )

        return context
