import os, uuid

def get_upload_path(instance, filename):
    """
    Tạo đường dẫn upload: uploads/app_name/tên_file_uuid.ext
    """
    # Lấy tên app (app_label) từ model
    app_name = instance._meta.app_label
    # Lấy tên model
    model_name = instance._meta.model_name

    ext = filename.split('.')[-1].lower()

    unique_filename = f"{uuid.uuid4()}.{ext}"
    
    return os.path.join('uploads', app_name,model_name, unique_filename)
