from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.generic import (
    DeleteView,
    DetailView,
    CreateView,
    ListView,
    UpdateView,
    View,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.contrib.messages.views import SuccessMessageMixin
from django.forms import modelform_factory
from collections import OrderedDict

from .models import Product, Banner, Category, Brand, ProductImage
from store.forms import ProductUpdateForm, CategoryUpdateForm
from tools.breadcrumb_utils import get_breadcrumb
from tools.required_role import RoleRequiredMixin


# --- MIXIN CHUNG CHO DASHBOARD TỐI ƯU CODE ---
class DashboardBaseView(RoleRequiredMixin, ListView):
    model = Product
    context_object_name = "products"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "categories": Category.objects.all().order_by("display_order", "name"),
                "brands": Brand.objects.all(),
                "total_products_count": Product.objects.count(),
                "total_categories_count": Category.objects.count(),
            }
        )
        return context


class DashboardCustomerView(DashboardBaseView):
    template_name = "core/dashboard_customer.html"
    allowed_roles = ["admin", "staff", "customer"]


class DashboardStaffView(DashboardBaseView):
    template_name = "core/dashboard_staff.html"
    allowed_roles = ["admin", "staff"]


class DashboardAdminView(DashboardBaseView):
    template_name = "core/dashboard_admin.html"
    allowed_roles = ["admin"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        CategoryForm = modelform_factory(
            Category, fields=["name", "parent", "image", "icon_code"]
        )
        context["category_form"] = CategoryForm()
        context["categories"] = Category.objects.filter(is_active=True)
        return context


# --- PRODUCT VIEWS ---
def search(request):
    query = request.GET.get("query", "")
    products = Product.active.filter(is_sold=False)
    if query:
        products = products.filter(Q(name__icontains=query))
    return render(request, "core/search.html", {"products": products, "query": query})


class ProductDetailView(DetailView):
    model = Product
    slug_field = "slug"

    def get_queryset(self):
        return Product.objects.select_related("category").prefetch_related("images")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context.update(
            {
                "related_products": Product.active.filter(
                    category=product.category
                ).exclude(id=product.id)[:4],
                "featured_products": Product.active.filter(is_featured=True)[:4],
                "categories": Category.active.filter(
                    parent__isnull=True
                ).prefetch_related("children"),
            }
        )
        return context


@login_required
def set_main_image(request, pk):
    img = get_object_or_404(ProductImage, pk=pk)
    product = img.product
    ProductImage.objects.filter(product=product).update(is_main=False)
    img.is_main = True
    img.save(update_fields=["is_main"])
    return redirect("store:product_detail", slug=product.slug)


class ProductCreateView(RoleRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductUpdateForm
    template_name = "store/product_form.html"
    success_message = "Đã tạo sản phẩm thành công: %(name)s"
    allowed_roles = ["admin", "staff"]

    def get_success_url(self):
        return (
            reverse("store:admin_dashboard")
            if self.request.user.is_superuser
            else reverse("store:home")
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        images = self.request.FILES.getlist("images")
        for index, img in enumerate(images):
            ProductImage.objects.create(
                product=self.object, order=index, image=img, is_main=(index == 0)
            )
        return response


class ProductUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductUpdateForm
    slug_field = "slug"
    success_message = "Update product successfully!"
    template_name = "store/product_update_form.html"

    def get_success_url(self):
        return (
            reverse("store:admin_dashboard")
            if self.request.user.is_superuser
            else reverse("store:home")
        )

    def form_valid(self, form):

        response = super().form_valid(form)

        images = self.request.FILES.getlist("images")

        last_order = ProductImage.objects.filter(product=self.object).count()

        for index, img in enumerate(images):
            ProductImage.objects.create(
                product=self.object, image=img, order=last_order + index
            )

        return response

    def form_invalid(self, form):

        print("FORM INVALID")
        print(form.errors)
        print(form.non_field_errors())

        return super().form_invalid(form)


class ProductDeleteView(RoleRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Product
    allowed_roles = ["admin", "staff"]

    def get_success_url(self):
        if self.request.user.is_superuser:
            return reverse("store:admin_dashboard")
        if self.request.user.is_staff:
            return reverse("store:staff_dashboard")

    def get_queryset(self):
        if self.request.user.role == "admin":
            return self.model.objects.all()
        return self.model.objects.filter(create_by=self.request.user)


# --- CATEGORY VIEWS ---
class CategoryCreateView(RoleRequiredMixin, SuccessMessageMixin, CreateView):
    model = Category
    fields = ["name", "parent", "image", "icon_code"]
    success_message = "Create category successfully!"
    allowed_roles = ["admin", "staff"]

    def get_success_url(self):
        return (
            reverse("store:admin_dashboard")
            if self.request.user.is_superuser
            else reverse("store:staff_dashboard")
        )


class CategoryUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryUpdateForm
    success_message = "Category updated successfully!"

    def get_success_url(self):
        # KHẮC PHỤC: Chuyển hướng đúng về trang chi tiết category thay vì category_list bị thiếu tham số slug
        return reverse("store:category_detail", kwargs={"slug": self.object.slug})


class CategoryDetailView(DetailView):
    model = Category
    context_object_name = "category"

    def get_object(self):
        return get_object_or_404(Category.active, slug=self.kwargs["slug"])

    def get(self, request, *args, **kwargs):
        category = self.get_object()
        breadcrumb_items = OrderedDict()
        ancestors = []
        current = category
        while current:
            ancestors.insert(0, current)
            current = current.parent
        for cat in ancestors:
            breadcrumb_items[cat.name] = reverse(
                "store:category_detail", kwargs={"slug": cat.slug}
            )
        request.custom_breadcrumb = breadcrumb_items
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object

        brand = self.request.GET.get("brand")
        min_p = self.request.GET.get("min_price")
        max_p = self.request.GET.get("max_price")
        sort = self.request.GET.get("sort")

        products = category.get_products_queryset(
            brand=brand, min_price=min_p, max_price=max_p, sort=sort
        )
        paginator = Paginator(products, 12)
        page_obj = paginator.get_page(self.request.GET.get("page"))

        context.update(
            {
                "breadcrumb": get_breadcrumb(category=category),
                "grouped_products": category.get_grouped_products(
                    brand=brand, min_price=min_p, max_price=max_p, sort=sort
                ),
                "page_obj": page_obj,
                "products": page_obj,
                "brands": Brand.objects.all(),
                "categories": Category.active.filter(
                    parent__isnull=True
                ).prefetch_related("children"),
                "custom_breadcrumb": getattr(self.request, "custom_breadcrumb", {}),
            }
        )
        return context


class CategoryListView(ListView):
    model = Category
    template_name = "store/category/category_list.html"
    context_object_name = "categories"
    paginate_by = 12

    def get_queryset(self):
        return (
            Category.active.filter(parent__isnull=True)
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "breadcrumbs": get_breadcrumb(extra_items={"Danh mục sản phẩm": None}),
                "featured_categories": Category.active.filter(
                    is_featured=True, parent__isnull=True
                ).order_by("display_order")[:6],
                "total_products": Product.active.count(),
                "total_categories": Category.active.filter(parent__isnull=True).count(),
            }
        )
        return context


class CategoryPermanentDeleteView(LoginRequiredMixin, View):

    def post(self, request, slug):

        category = get_object_or_404(Category.objects, slug=slug, is_active=False)

        category.hard_delete()

        messages.success(request, "Deleted permanently")

        return redirect("store:category_trash")


class CategoryTrashView(LoginRequiredMixin, ListView):

    model = Category

    template_name = "store/category/trash.html"

    context_object_name = "categories"

    def get_queryset(self):

        return Category.objects.filter(is_active=False)


class CategoryDeleteView(SuccessMessageMixin, RoleRequiredMixin, DeleteView):
    model = Category
    allowed_roles = [
        "admin",
    ]

    def get_success_url(self):
        return reverse("store:admin_dashboard")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # 1. Kiểm tra điều kiện ngay tại View
        if self.object.category_products.filter(is_active=True).exists():
            messages.error(
                request,
                f"Không thể xóa danh mục '{self.object.name}' vì vẫn còn sản phẩm đang hoạt động bên trong!",
            )
            return HttpResponseRedirect(self.get_success_url())

        # 2. Nếu không vướng sản phẩm nào, tiến hành soft delete
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())


class CategoryRestoreView(LoginRequiredMixin, View):
    def post(self, request, slug):
        category = get_object_or_404(Category.objects, slug=slug, is_active=False)
        category.restore()

        messages.success(request, "Restore success")
        return redirect("store:category_trash")


class BrandCreateView(SuccessMessageMixin, RoleRequiredMixin, CreateView):
    model = Brand
    fields = ["name"]
    success_message = "Đã tạo thương hiệu thành công: %(name)s"
    success_url = reverse_lazy("store:product_create")
    allowed_roles = [
        "admin",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create brand"
        return context


# --- HOME VIEW ---
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
                grouped_categories.append({"main_category": cat, "groups": preview})

        # KHẮC PHỤC: Sửa lỗi chính tả từ "chirldren__children" thành "children__children" chống sập website
        featured_categories = (
            Category.active.filter(category_products__isnull=False)
            .annotate(product_count=Count("category_products"))
            .order_by("-product_count")[:8]
        )

        best_sellers = [
            p
            for p in Product.active.all().prefetch_related("images")
            if p.is_bestseller
        ][:8]

        context.update(
            {
                "banners": Banner.objects.filter(is_active=True).order_by("order")[:5],
                "latest_products": Product.active.order_by(
                    "-created_at"
                ).prefetch_related("images")[:8],
                "best_sellers": best_sellers,
                "featured_categories": featured_categories,
                "grouped_categories": grouped_categories,
                "title": "home",
            }
        )
        return context
