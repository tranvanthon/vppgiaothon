from django.urls import path
from store import views

app_name = "store"

urlpatterns = [
    # Dashboards hệ thống
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
