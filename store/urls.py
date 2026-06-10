from django.urls import path
from store import views

app_name = "store"

urlpatterns = [
    # Cart
    path("order/tracking/<int:order_id>/", views.order_tracking, name="order_tracking"),
    path("create-order/", views.create_order, name="create_order"),
    path("order/success/<int:order_id>/", views.order_success, name="order_success"),
    path("confirm-payment/", views.confirm_payment, name="confirm_payment"),
    path("checkout/", views.checkout, name="checkout"),
    path("cart/update/<int:item_id>/", views.update_cart_item, name="cart_update"),
    path("cart/detail/", views.cart_detail, name="cart_detail"),
    path("cart/add/<slug:slug>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    # Process Order
    path("dashboard/staff/orders/", views.OrderListView.as_view(), name="order_list"),
    path(
        "dashboard/staff/orders<int:pk>/",
        views.OrderDetailView.as_view(),
        name="order_detail",
    ),
    # Dashboards
    path(
        "admin-dashboard/", views.DashboardAdminView.as_view(), name="admin_dashboard"
    ),
    path(
        "staff-dashboard/", views.DashboardStaffView.as_view(), name="staff_dashboard"
    ),
    path(
        "customer-dashboard/",
        views.DashboardCustomerView.as_view(),
        name="customer_dashboard",
    ),
    # Quản lý Sản phẩm (Products)
    path("", views.HomeView.as_view(), name="home"),
    path("search/", views.search, name="search"),
    path(
        "product/<slug:slug>/update/",
        views.ProductUpdateView.as_view(),
        name="product_update",
    ),
    path("products/create/", views.ProductCreateView.as_view(), name="product_create"),
    path(
        "product/<slug:slug>/", views.ProductDetailView.as_view(), name="product_detail"
    ),
    path(
        "product/<slug:slug>/delete/",
        views.ProductDeleteView.as_view(),
        name="product_delete",
    ),
    # Quản lý Đa ảnh (Images)
    path("image/<int:pk>/main/", views.set_main_image, name="set_main_image"),
    # Danh mục & Thương hiệu (Categories & Brands)
    path("category/trash/", views.CategoryTrashView.as_view(), name="category_trash"),
    path("category/", views.CategoryListView.as_view(), name="category_list"),
    path(
        "category/create/", views.CategoryCreateView.as_view(), name="category_create"
    ),
    path(
        "category/<slug:slug>/detail/",
        views.CategoryDetailView.as_view(),
        name="category_detail",
    ),
    path(
        "category/<slug:slug>/update/",
        views.CategoryUpdateView.as_view(),
        name="category_update",
    ),
    # soft delete
    path(
        "category/<slug:slug>/delete/",
        views.CategoryDeleteView.as_view(),
        name="category_delete",
    ),
    # restore
    path(
        "category/<slug:slug>/restore/",
        views.CategoryRestoreView.as_view(),
        name="category_restore",
    ),
    # hard delete
    path(
        "category/<slug:slug>/hard-delete/",
        views.CategoryPermanentDeleteView.as_view(),
        name="category_permanent_delete",
    ),
    path("brand/create/", views.BrandCreateView.as_view(), name="brand_create"),
]
