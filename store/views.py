from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.views.generic import (
    DeleteView,
    DetailView,
    CreateView,
    ListView,
    UpdateView,
    View,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.contrib.messages.views import SuccessMessageMixin
from django.forms import modelform_factory
from django.utils import timezone
from collections import OrderedDict
import unicodedata
from django.core.exceptions import ValidationError

from .models import (
    Product,
    Banner,
    Category,
    Brand,
    ProductImage,
    Order,
    OrderItem,
)
from store.forms import ProductUpdateForm, CategoryUpdateForm
from tools.breadcrumb_utils import get_breadcrumb
from tools.required_role import RoleRequiredMixin
from tools.utils import get_or_create_cart
import json, uuid
from django.views.decorators.csrf import csrf_exempt


# Cart
def order_tracking(request, order_id):
    """Trang theo dõi đơn hàng"""
    order = get_object_or_404(Order, id=order_id)

    if order.customer and order.customer != request.user:
        if not request.user.is_staff:
            return redirect("home")

    timeline = get_order_timeline(order)

    context = {
        "order": order,
        "order_items": order.items.all(),
        "timeline": timeline,
    }
    return render(request, "store/cart/order_tracking.html", context)


def order_success(request, order_id):
    """Trang xác nhận đơn hàng thành công"""
    order = get_object_or_404(Order, id=order_id)

    # Kiểm tra quyền truy cập
    if order.customer and order.customer != request.user:
        if not request.user.is_staff and not request.user.is_superuser:
            return redirect("home")

    # Tạo timeline cho đơn hàng
    timeline = {
        "order_placed": {
            "name": "Đơn hàng đã đặt",
            "description": "Hệ thống đã xác nhận đơn hàng của bạn",
            "completed": True,
            "time": (
                order.created_at.strftime("%d/%m/%Y - %H:%M")
                if order.created_at
                else None
            ),
        },
        "confirmed": {
            "name": "Đã xác nhận",
            "description": "Đơn hàng đã được xác nhận",
            "completed": order.status
            in ["CONFIRMED", "PACKED", "SHIPPING", "DELIVERED", "COMPLETED"],
            "time": (
                order.confirmed_at.strftime("%d/%m/%Y - %H:%M")
                if order.confirmed_at
                else None
            ),
        },
        "packed": {
            "name": "Đã đóng gói",
            "description": "Kiện hàng đã sẵn sàng để gửi đi",
            "completed": order.status
            in ["PACKED", "SHIPPING", "DELIVERED", "COMPLETED"],
            "time": (
                order.packed_at.strftime("%d/%m/%Y - %H:%M")
                if order.packed_at
                else None
            ),
        },
        "shipping": {
            "name": "Đang giao hàng",
            "description": "Đơn hàng đang trên đường đến bạn",
            "completed": order.status in ["SHIPPING", "DELIVERED", "COMPLETED"],
            "time": (
                order.shipping_at.strftime("%d/%m/%Y - %H:%M")
                if order.shipping_at
                else None
            ),
        },
        "delivered": {
            "name": "Giao hàng thành công",
            "description": "Đơn hàng đã được giao",
            "completed": order.status in ["DELIVERED", "COMPLETED"],
            "time": (
                order.delivered_at.strftime("%d/%m/%Y - %H:%M")
                if order.delivered_at
                else None
            ),
        },
    }

    context = {
        "order": order,
        "timeline": timeline,
    }

    return render(request, "order_success.html", context)


def get_order_timeline(order):
    """Tạo timeline cho đơn hàng"""
    timeline = {
        "order_placed": {
            "name": "Đơn hàng đã đặt",
            "icon": "bi-receipt",
            "description": "Hệ thống đã xác nhận đơn hàng của bạn",
            "completed": True,
            "time": (
                order.created_at.strftime("%d/%m/%Y - %H:%M")
                if order.created_at
                else None
            ),
        },
        "confirmed": {
            "name": "Đã xác nhận",
            "icon": "bi-check-circle",
            "description": "Đơn hàng đã được xác nhận",
            "completed": order.status
            in ["CONFIRMED", "PACKED", "SHIPPING", "DELIVERED", "COMPLETED"],
            "time": (
                order.confirmed_at.strftime("%d/%m/%Y - %H:%M")
                if order.confirmed_at
                else None
            ),
        },
        "packed": {
            "name": "Đã đóng gói",
            "icon": "bi-box-seam",
            "description": "Kiện hàng đã sẵn sàng để gửi đi",
            "completed": order.status
            in ["PACKED", "SHIPPING", "DELIVERED", "COMPLETED"],
            "time": (
                order.packed_at.strftime("%d/%m/%Y - %H:%M")
                if order.packed_at
                else None
            ),
        },
        "shipping": {
            "name": "Đang giao hàng",
            "icon": "bi-truck",
            "description": "Đơn hàng đang trên đường đến bạn",
            "completed": order.status in ["SHIPPING", "DELIVERED", "COMPLETED"],
            "time": (
                order.shipping_at.strftime("%d/%m/%Y - %H:%M")
                if order.shipping_at
                else None
            ),
        },
        "delivered": {
            "name": "Giao hàng thành công",
            "icon": "bi-house-check",
            "description": "Đơn hàng đã được giao",
            "completed": order.status in ["DELIVERED", "COMPLETED"],
            "time": (
                order.delivered_at.strftime("%d/%m/%Y - %H:%M")
                if order.delivered_at
                else None
            ),
        },
    }
    return timeline


def create_order(request):
    if request.method != "POST":
        return redirect("store:cart_detail")

    order = get_or_create_cart(request)

    if not order.items.exists():
        return redirect("store:cart_detail")

    payment_method = request.POST.get("payment_method", "COD").upper()

    # Thông tin khách hàng
    order.full_name = request.POST.get("full_name")
    order.phone = request.POST.get("phone")
    order.email = request.POST.get("email", "")

    # Địa chỉ
    order.province = request.POST.get("province_name", "")
    order.province_code = request.POST.get("province_code", "")
    order.ward = request.POST.get("ward_name", "")
    order.ward_code = request.POST.get("ward_code", "")
    order.hamlet = request.POST.get("hamlet", "")
    order.address = request.POST.get("address", "")
    order.full_address = request.POST.get("full_address", "")

    # Ghi chú
    order.note = request.POST.get("note", "")

    # Mã đơn hàng
    if not order.order_number:
        order.order_number = (
            f"DH{timezone.now().strftime('%y%m%d')}" f"{uuid.uuid4().hex[:6].upper()}"
        )

    # Trạng thái đơn hàng
    order.status = Order.Status.PENDING
    order.complete = True

    # Thanh toán
    order.payment_method = payment_method

    order.payment_status = (
        Order.PaymentStatus.PENDING
        if payment_method == "COD"
        else Order.PaymentStatus.AWAITING
    )

    # Tính lại tiền
    order.update_totals()

    order.save()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "success": True,
                "order_id": order.id,
                "order_code": order.order_number,
                "total_amount": float(order.total_amount),
            }
        )

    return redirect(
        "order_success",
        order_id=order.id,
    )


def order_success(request, order_id):

    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        id=order_id,
    )

    if (
        order.customer
        and request.user.is_authenticated
        and order.customer != request.user
    ):
        return redirect("home")

    context = {
        "order": order,
        "order_items": order.items.all(),
        "timeline": get_order_timeline(order),
    }

    return render(
        request,
        "store/cart/order_success.html",
        context,
    )


@csrf_exempt
def confirm_payment(request):
    """Xác nhận thanh toán qua chuyển khoản"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed"})

    try:
        data = json.loads(request.body)
        order_id = data.get("order_id")

        if not order_id:
            return JsonResponse({"success": False, "error": "Thiếu mã đơn hàng"})

        order = get_object_or_404(Order, id=order_id)

        # Cập nhật trạng thái thanh toán
        order.payment_status = Order.PaymentStatus.PAID
        order.status = Order.Status.CONFIRMED
        order.paid_at = timezone.now()
        order.save()

        return JsonResponse(
            {
                "success": True,
                "redirect_url": reverse("store:order_success", args=[order_id]),
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Dữ liệu không hợp lệ"})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def get_order_timeline(order):
    """Tạo timeline cho đơn hàng"""
    timeline = {
        "order_placed": {
            "name": "Đơn hàng đã đặt",
            "icon": "bi-receipt",
            "description": "Hệ thống đã xác nhận đơn hàng của bạn",
            "completed": True,
            "time": order.created_at.strftime("%d/%m/%Y - %H:%M"),
        },
        "packed": {
            "name": "Đã đóng gói",
            "icon": "bi-box-seam",
            "description": "Kiện hàng đã sẵn sàng để gửi đi",
            "completed": order.status
            in ["packed", "shipping", "delivered", "completed"],
            "time": (
                order.packed_at.strftime("%d/%m/%Y - %H:%M")
                if order.packed_at
                else None
            ),
        },
        "shipping": {
            "name": "Đang giao hàng",
            "icon": "bi-truck",
            "description": "Đơn hàng đang trên đường đến bạn",
            "completed": order.status in ["shipping", "delivered", "completed"],
            "time": (
                order.shipping_at.strftime("%d/%m/%Y - %H:%M")
                if order.shipping_at
                else None
            ),
        },
        "delivered": {
            "name": "Giao hàng thành công",
            "icon": "bi-house-check",
            "description": "Đơn hàng đã được giao",
            "completed": order.status in ["delivered", "completed"],
            "time": (
                order.delivered_at.strftime("%d/%m/%Y - %H:%M")
                if order.delivered_at
                else None
            ),
        },
    }
    return timeline


# Check out
def checkout(request):

    order = get_or_create_cart(request)

    if not order.items.exists():
        return redirect("store:cart_detail")

    context = {
        "order": order,
        "cart_items": order.items.select_related("product"),
        "total_amount": order.total_amount,
    }

    return render(
        request,
        "store/cart/checkout.html",
        context,
    )


# update_from_cart
def update_cart_item(request, item_id):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Method not allowed"}, status=405
        )

    order = get_or_create_cart(request)
    item = get_object_or_404(OrderItem, id=item_id, order=order)

    try:
        data = json.loads(request.body)
        quantity = int(data.get("quantity", item.quantity))

        if quantity <= 0:
            item.delete()
            return JsonResponse({"success": True, "deleted": True})
        else:
            item.quantity = quantity
            item.save()
            return JsonResponse(
                {
                    "success": True,
                    "quantity": item.quantity,
                    "item_total": item.price * item.quantity,
                }
            )

    except (ValueError, ValidationError, json.JSONDecodeError):
        return JsonResponse(
            {"success": False, "error": "Số lượng không hợp lệ!"}, status=400
        )


def remove_from_cart(request, item_id):

    order = get_or_create_cart(request)

    item = get_object_or_404(
        OrderItem,
        id=item_id,
        order=order,
    )

    item.delete()

    return redirect("store:cart_detail")


# Cart detail
def cart_detail(request):

    order = get_or_create_cart(request)

    context = {
        "order": order,
        "cart_items": order.items.all(),
        "total_amount": order.total_amount,
    }

    return render(
        request,
        "store/cart/cart_detail.html",
        context,
    )


def add_to_cart(request, slug):
    product = get_object_or_404(Product, slug=slug)
    order = get_or_create_cart(request)
    # if order is None:
    #     return redirect("account_login")
    order.add_product(product, quantity=1)
    return redirect(request.META.get("HTTP_REFERER", "/"))


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

    @staticmethod
    def _format_vnd(value):
        return f"{int(value or 0):,}".replace(",", ".") + "đ"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        CategoryForm = modelform_factory(
            Category, fields=["name", "parent", "image", "icon_code"]
        )
        today = timezone.localdate()
        yesterday = today - timezone.timedelta(days=1)
        revenue_expression = ExpressionWrapper(
            F("price") * F("quantity"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        paid_statuses = [Order.Status.PAID, Order.Status.SHIPPED]
        daily_revenue = (
            OrderItem.objects.filter(
                order__complete=True,
                order__status__in=paid_statuses,
                order__created_at__date=today,
            ).aggregate(total=Sum(revenue_expression))["total"]
            or 0
        )
        yesterday_revenue = (
            OrderItem.objects.filter(
                order__complete=True,
                order__status__in=paid_statuses,
                order__created_at__date=yesterday,
            ).aggregate(total=Sum(revenue_expression))["total"]
            or 0
        )
        if yesterday_revenue:
            revenue_change = (
                (daily_revenue - yesterday_revenue) / yesterday_revenue
            ) * 100
            revenue_trend_text = f"{revenue_change:+.0f}% so với hôm qua"
            revenue_trend_icon = (
                "bi-arrow-up" if revenue_change >= 0 else "bi-arrow-down"
            )
        elif daily_revenue:
            revenue_trend_text = "Có doanh thu mới hôm nay"
            revenue_trend_icon = "bi-arrow-up"
        else:
            revenue_trend_text = "Chưa có doanh thu hôm nay"
            revenue_trend_icon = "bi-dash-circle"

        User = get_user_model()
        context["category_form"] = CategoryForm()
        context["categories"] = Category.objects.filter(is_active=True)
        context.update(
            {
                "daily_revenue": self._format_vnd(daily_revenue),
                "revenue_trend_text": revenue_trend_text,
                "revenue_trend_icon": revenue_trend_icon,
                "new_orders_today": Order.objects.filter(
                    complete=True, created_at__date=today
                ).count(),
                "pending_orders_count": Order.objects.filter(
                    complete=True, status=Order.Status.DRAFT
                ).count(),
                "customer_count": User.objects.filter(role="customer").count(),
                "new_customers_today": User.objects.filter(
                    role="customer", date_joined__date=today
                ).count(),
            }
        )
        return context


# --- PRODUCT VIEWS ---
def normalize_search_text(value):
    value = unicodedata.normalize("NFD", value or "")
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    return value.replace("đ", "d").replace("Đ", "D").casefold()


def product_matches_search(product, normalized_query):
    normalized_name = normalize_search_text(product.name)
    normalized_brand = normalize_search_text(
        product.brand.name if product.brand else ""
    )
    normalized_category = normalize_search_text(
        product.category.name if product.category else ""
    )
    searchable_text = " ".join([normalized_name, normalized_brand, normalized_category])
    words = searchable_text.split()

    if normalized_name.startswith(normalized_query):
        return 0
    if any(word.startswith(normalized_query) for word in words):
        return 1
    if normalized_query in searchable_text:
        return 2
    return None


def search(request):
    query = request.GET.get("query", "").strip()
    products = (
        Product.active.filter(is_sold=False)
        .select_related("brand", "category")
        .prefetch_related("images")
    )
    if query:
        normalized_query = normalize_search_text(query)
        matched_products = []

        for product in products:
            rank = product_matches_search(product, normalized_query)
            if rank is not None:
                matched_products.append((rank, product.name.casefold(), product))

        products = [
            product
            for _, _, product in sorted(matched_products, key=lambda item: item[:2])
        ]
    return render(request, "core/search.html", {"products": products, "query": query})


class ProductDetailView(DetailView):
    model = Product
    slug_field = "slug"

    def get_queryset(self):
        return Product.objects.select_related(
            "category",
            "brand",
        ).prefetch_related(
            "images",
            "variants",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        product = self.object
        variant_id = self.request.GET.get("variant")

        selected_variant = (
            product.variants.filter(id=variant_id).first() or product.variants.first()
        )

        context.update(
            {
                "selected_variant": selected_variant,
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
    template_name = "store/category_update_form.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_success_url(self):
        return (
            reverse("store:admin_dashboard")
            if self.request.user.is_superuser
            else reverse("store:staff_dashboard")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Update category",
            }
        )
        return context


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
