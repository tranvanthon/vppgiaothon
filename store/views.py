from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import DetailView, CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product, Banner


class HomeView(ListView):
    model = Product
    template_name = "core/index.html"

    def get_queryset(self):
        return Product.active.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Banner
        banners = Banner.objects.filter(is_active=True).order_by("order")[:5]
        context.update(
            {
                "banners": banners,
            }
        )

        return context