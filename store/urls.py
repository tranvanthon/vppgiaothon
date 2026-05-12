from django.urls import path
from store import views

app_name = "store"
urlpatterns = [
    # Product
    path(
        "product/<slug:slug>/", views.ProductDetailView.as_view(), name="product_detail"
    ),
    path("image/<int:pk>/main/", views.set_main_image, name="set-main-image"),
    path(
        "product/<slug:slug>/update/",
        views.ProducUpdateView.as_view(),
        name="product_update",
    ),
    path("products/create/", views.ProductCreateView.as_view(), name="product_create"),
    path("", views.HomeView.as_view(), name="home"),
    # Url Category
    path("category/", views.CategoryListView.as_view(), name="category_list"),
    path(
        "category/<slug:slug>/detail/",
        views.CategoryDetailView.as_view(),
        name="category_detail",
    ),
]
