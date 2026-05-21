import os
from django.core.files.storage import default_storage
from core.paths.upload import build_upload_path
from core.utils.image import normalize_image_mode, resize_image, Image

def get_or_create_image_version(instance, image_field_name, width, height, mode="crop", quality=80):
    """
    Hàm dịch vụ: Trả về URL của ảnh với kích thước tùy biến theo yêu cầu từ View/Template.
    Nếu kích thước này chưa từng được tạo, hệ thống sẽ tự động tạo và lưu lại (on-the-fly).
    """
    # 1. Lấy ra trường ảnh gốc 
    image_field = getattr(instance, image_field_name, None)
    if not image_field or not image_field.name:
        return ""
        
    filename = os.path.basename(image_field.name)
    
    # 2. Định nghĩa một thư mục lưu cache ảnh resize dựa trên kích thước yêu cầu
    # Sử dụng lại hàm build_upload_path của bạn nhưng thay đổi type thành kích thước mong muốn
    size_label = f"resized_{width}x{height}_{mode}"
    relative_path = build_upload_path(instance, filename, image_type=size_label)
    absolute_path = default_storage.path(relative_path)
    
    # 3. Nếu ảnh kích thước này đã tồn tại rồi, trả về URL luôn không cần xử lý lại
    if default_storage.exists(relative_path):
        return default_storage.url(relative_path)
        
    # 4. Nếu chưa có, tiến hành resize bằng Pillow (dựa trên các hàm bạn đã viết)
    try:
        os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
        
        img = Image.open(image_field.path)
        img = normalize_image_mode(img)
        resized_img = resize_image(img, (width, height), mode=mode)
        
        # Lưu đè dưới định dạng WEBP siêu nhẹ giống như bạn thiết lập
        resized_img.save(
            absolute_path,
            format="WEBP",
            quality=quality,
            optimize=True
        )
        return default_storage.url(relative_path)
    except Exception as e:
        # Nếu có lỗi gì xảy ra, fallback về ảnh gốc để không chết giao diện
        return image_field.url