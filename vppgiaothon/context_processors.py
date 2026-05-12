
from django.contrib.sites.shortcuts import get_current_site
#Lấy tên domain
from django.core.cache import cache
from store.models import Category

def global_categories(request):
    """
    Context processor để có categories ở MỌI template
    Cache 30 phút để tránh query database liên tục
    """
    # Thử lấy từ cache trước
    categories = cache.get('main_categories')
    
    if categories is None:
        # Chỉ query database khi cache hết hạn
        categories = Category.active.filter(
            parent__isnull=True
        ).prefetch_related('children')
        
        # Lưu vào cache trong 30 phút (1800 giây)
        cache.set('main_categories', categories, 1800)
    
    return {'global_categories': categories}
# Lấy site_domain và site_name
def site_info(request):
    current_site = get_current_site(request)
    return {
        'site_name': current_site.name,      
        'site_domain': current_site.domain,  
    }
