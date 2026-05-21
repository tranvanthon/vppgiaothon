import os
import glob
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from profiles.models import Profile


class Command(BaseCommand):
    help = "Dọn dẹp các ảnh orphan (ảnh không còn được tham chiếu trong database)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Chỉ hiển thị những file sẽ bị xóa mà không thực sự xóa',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS('🔍 Bắt đầu quét ảnh orphan...'))
        
        # 1. Lấy tất cả ảnh đang được sử dụng trong database
        active_avatars = set()
        for profile in Profile.objects.filter(avatar__isnull=False):
            if profile.avatar and profile.avatar.name:
                active_avatars.add(profile.avatar.name)
        
        self.stdout.write(f"📊 Tìm thấy {len(active_avatars)} ảnh đang được sử dụng")
        
        # 2. Quét tất cả file trong thư mục uploads/profiles/profile
        base_dir_relative = os.path.join("uploads", "profiles", "profile")
        base_dir_absolute = default_storage.path(base_dir_relative)
        
        if not os.path.exists(base_dir_absolute):
            self.stdout.write(self.style.WARNING(f'⚠️  Thư mục {base_dir_absolute} không tồn tại'))
            return
        
        # 3. Tìm tất cả file trong thư mục
        search_pattern = os.path.join(base_dir_absolute, "**", "*")
        all_files = glob.glob(search_pattern, recursive=True)
        
        # Chỉ lấy files (bỏ qua directories)
        all_files = [f for f in all_files if os.path.isfile(f)]
        
        self.stdout.write(f"📁 Tổng file trong thư mục: {len(all_files)}")
        
        # 4. Tìm các file orphan
        orphan_files = []
        for file_path in all_files:
            # Tạo relative path để so sánh
            file_relative = os.path.relpath(file_path, base_dir_absolute)
            file_relative = os.path.join(base_dir_relative, file_relative)
            
            # Kiểm tra xem file này có trong database không
            is_in_db = False
            for active_avatar in active_avatars:
                if file_relative in active_avatar or active_avatar in file_relative:
                    is_in_db = True
                    break
            
            if not is_in_db:
                orphan_files.append(file_path)
        
        self.stdout.write(f"🗑️  Tìm thấy {len(orphan_files)} ảnh orphan")
        
        if orphan_files:
            for file_path in orphan_files:
                rel_path = os.path.relpath(file_path, base_dir_absolute)
                
                if dry_run:
                    self.stdout.write(f"  [DRY-RUN] Sẽ xóa: {rel_path}")
                else:
                    try:
                        os.remove(file_path)
                        self.stdout.write(self.style.SUCCESS(f"  ✓ Đã xóa: {rel_path}"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  ✗ Lỗi xóa {rel_path}: {e}"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  Chế độ DRY-RUN: Không có file nào bị xóa'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Dọn dẹp xong! Đã xóa {len(orphan_files)} ảnh orphan'))
