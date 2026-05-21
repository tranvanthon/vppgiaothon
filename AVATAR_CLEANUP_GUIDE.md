# 🖼️ Avatar Image Cleanup - Hướng dẫn

## Vấn đề đã giải quyết

✅ Ảnh cũ được xóa tự động khi update avatar  
✅ Tất cả bản resize/cache được dọn dẹp  
✅ Xóa Profile sẽ xóa tất cả ảnh liên quan

## Cách hoạt động

### 1. **Update Avatar (Tự động xóa ảnh cũ)**

```python
# Trong profiles/views.py - upload_avatar()
profile.avatar = new_avatar_file
profile.save()  # Tự động xóa ảnh cũ và resize
```

Khi `profile.save()` được gọi:

- 🗑️ Xóa file ảnh gốc cũ
- 🗑️ Quét và xóa tất cả bản resize/cache (.../resized_300x300_crop/...)
- ✅ Lưu ảnh mới
- ⚙️ Tối ưu kích thước ảnh (resize về 1200x1200 nếu cần)

### 2. **Xóa Profile (Xóa tất cả ảnh)**

```python
# Khi profile được xóa
profile.delete()  # Signal tự động xóa tất cả file ảnh
```

Signal `delete_profile_image_files` trong `profiles/signals.py` sẽ:

- 🗑️ Xóa ảnh gốc
- 🗑️ Quét và xóa tất cả bản resize liên quan

### 3. **Dọn dẹp Ảnh Orphan (Không còn được sử dụng)**

```bash
# Kiểm tra (DRY-RUN) - không xóa gì
python manage.py cleanup_orphan_images --dry-run

# Thực sự xóa ảnh orphan
python manage.py cleanup_orphan_images
```

Management command `cleanup_orphan_images`:

- 📊 Quét tất cả file trong `media/uploads/profiles/profile/`
- 🔍 So sánh với các ảnh đang được sử dụng trong database
- 🗑️ Xóa các ảnh không còn tham chiếu (orphan)

## Cấu trúc Thư mục

```
media/uploads/profiles/profile/
├── original/           # Ảnh gốc sau khi tối ưu
│   └── 2026/05/abc.jpg
├── resized_80x80_crop/     # Bản resize 80x80
│   └── 2026/05/abc.webp
├── resized_300x300_crop/   # Bản resize 300x300
│   └── 2026/05/abc.webp
└── resized_800x800_thumbnail/
    └── 2026/05/abc.webp
```

## Files Được Thay Đổi

### profiles/models.py

- ✏️ Cải tiến logic xóa ảnh trong `Profile.save()`
- ✏️ Xử lý lỗi an toàn
- ✏️ Quét tất cả bản resize

### profiles/views.py

- ✏️ Đơn giản hóa `upload_avatar()`
- ✏️ Thêm validation
- ✏️ Loại bỏ debug code

### profiles/signals.py

- ✅ Thêm signal `delete_profile_image_files`
- Tự động xóa ảnh khi profile bị xóa

### profiles/management/commands/cleanup_orphan_images.py

- ✅ Tạo management command mới
- Dọn dẹp ảnh orphan

## Test Verifikasi

```bash
# Kiểm tra Django config
python manage.py check

# Chạy test dọn dẹp (DRY-RUN)
python manage.py cleanup_orphan_images --dry-run
```

## Best Practices

1. **Định kỳ chạy cleanup**

   ```bash
   # Thêm vào cron job (hàng tuần)
   0 3 * * 0 cd /path && python manage.py cleanup_orphan_images
   ```

2. **Monitoring**
   - Theo dõi file uploads
   - Kiểm tra kích thước media folder

3. **Backup**
   - Backup media folder trước khi chạy cleanup lớn
