from django.contrib.sites.shortcuts import get_current_site

# Lấy tên domain
from django.core.cache import cache
from store.models import Category, Order
from django.db.models import Prefetch


def global_categories(request):
    """
    Context processor để có categories ở MỌI template
    Cache 30 phút để tránh query database liên tục
    """
    # Thử lấy từ cache trước
    categories = cache.get("main_categories")

    if categories is None:
        # Nếu không có trong cache, truy vấn database
        categories = list(
            Category.active.filter(parent__isnull=True).prefetch_related(
                Prefetch(
                    "children",
                    queryset=Category.active.all(),
                    to_attr="active_children",
                )
            )
        )
        # Lưu vào cache trong 30 phút (1800 giây)
        cache.set("main_categories", categories, 1800)

    return {"global_categories": categories}


# Lấy site_domain và site_name
def site_info(request):
    current_site = get_current_site(request)
    return {
        "site_name": current_site.name,
        "site_domain": current_site.domain,
    }


def cart_summary(request):

    cart_order = None
    cart_items = []
    cart_items_count = 0

    user = getattr(request, "user", None)

    # User login
    if user and user.is_authenticated:

        cart_order = (
            Order.objects.filter(
                customer=user,
                complete=False,
            )
            .prefetch_related("items__product__images")
            .first()
        )

    # Guest cart
    if not cart_order:

        cart_id = request.session.get("cart_id")

        if cart_id:
            cart_order = (
                Order.objects.filter(
                    id=cart_id,
                    complete=False,
                )
                .prefetch_related("items__product__images")
                .first()
            )

    if cart_order:

        cart_items = list(cart_order.items.all())

        cart_items_count = sum(item.quantity for item in cart_items)

    return {
        "cart_order": cart_order,
        "cart_items": cart_items,
        "cart_items_count": cart_items_count,
    }
