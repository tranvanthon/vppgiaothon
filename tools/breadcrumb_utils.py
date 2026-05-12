from collections import OrderedDict

def get_breadcrumb(category=None, product=None, extra_items=None):
    """Tạo breadcrumb cho các trang"""
    breadcrumbs = OrderedDict()
    breadcrumbs["Trang chủ"] = "/"
    
    # Breadcrumb cho category
    if category:
        # Lấy tất cả category cha
        ancestors = []
        current = category
        while current:
            ancestors.insert(0, current)
            current = current.parent
        
        # Thêm từng cấp vào breadcrumb
        for cat in ancestors:
            breadcrumbs[cat.name] = cat.get_absolute_url()
    
    # Breadcrumb cho product
    if product and product.category:
        # Lấy breadcrumb của category trước
        ancestors = []
        current = product.category
        while current:
            ancestors.insert(0, current)
            current = current.parent
        
        for cat in ancestors:
            breadcrumbs[cat.name] = cat.get_absolute_url()
        
        # Thêm sản phẩm
        breadcrumbs[product.name] = product.get_absolute_url()
    
    # Thêm custom items
    if extra_items:
        for name, url in extra_items.items():
            breadcrumbs[name] = url
    
    return breadcrumbs