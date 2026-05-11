from django.urls import path
from store import views as store_views

app_name = "store"
urlpatterns = [
    path("", store_views.HomeView.as_view(), name="home"),
]
