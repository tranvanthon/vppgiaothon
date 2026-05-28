from decimal import Decimal

from django.core.management.base import BaseCommand

from store.models import Brand, Category, Product


class Command(BaseCommand):
    help = "Seed office-supply focused categories and sample products."

    def handle(self, *args, **options):
        categories = self.seed_categories()
        self.seed_products(categories)
        self.stdout.write(self.style.SUCCESS("Seeded catalog data successfully."))

    def get_or_create_category(self, name, **defaults):
        matches = [
            category
            for category in Category.objects.all()
            if category.name.casefold() == name.casefold()
        ]
        category = matches[0] if matches else None
        if category is None:
            category = Category.objects.create(name=name, **defaults)
        else:
            for field, value in defaults.items():
                setattr(category, field, value)
            category.name = name
            category.save()
            for duplicate in matches[1:]:
                for child in duplicate.children.all():
                    child.parent = category
                    child.save()
                Product.objects.filter(category=duplicate).update(category=category)
                duplicate.hard_delete()
        return category

    def seed_categories(self):
        root_data = [
            {
                "name": "Văn phòng phẩm",
                "icon_code": "bi bi-pencil-square",
                "display_order": 1,
                "is_featured": True,
                "meta_title": "Văn phòng phẩm",
                "meta_description": "Các sản phẩm văn phòng phẩm phục vụ học tập, làm việc và vận hành văn phòng.",
                "meta_keywords": "văn phòng phẩm, bút viết, giấy in, sổ tay",
            },
            {
                "name": "Dụng cụ thể thao",
                "icon_code": "bi bi-dribbble",
                "display_order": 2,
                "is_featured": True,
                "meta_title": "Dụng cụ thể thao",
                "meta_description": "Dụng cụ và phụ kiện thể thao cơ bản cho luyện tập hằng ngày.",
                "meta_keywords": "dụng cụ thể thao, bóng, vợt, phụ kiện tập luyện",
            },
        ]
        categories = {}
        for item in root_data:
            name = item.pop("name")
            categories[name] = self.get_or_create_category(name, parent=None, **item)

        child_data = [
            ("Bút viết", "Văn phòng phẩm", "bi bi-pen", 11),
            ("Giấy in & giấy note", "Văn phòng phẩm", "bi bi-file-earmark-text", 12),
            ("Sổ tay & tập vở", "Văn phòng phẩm", "bi bi-journal-text", 13),
            ("Bìa hồ sơ & lưu trữ", "Văn phòng phẩm", "bi bi-folder2-open", 14),
            ("Dụng cụ bàn làm việc", "Văn phòng phẩm", "bi bi-paperclip", 15),
            ("Thiết bị văn phòng", "Văn phòng phẩm", "bi bi-printer", 16),
            ("Mực in & phụ kiện in", "Văn phòng phẩm", "bi bi-droplet", 17),
            ("Dụng cụ mỹ thuật", "Văn phòng phẩm", "bi bi-palette", 18),
            ("Bóng thể thao", "Dụng cụ thể thao", "bi bi-circle", 21),
            ("Vợt & phụ kiện", "Dụng cụ thể thao", "bi bi-bullseye", 22),
            ("Tập luyện thể lực", "Dụng cụ thể thao", "bi bi-activity", 23),
            ("Phụ kiện thể thao", "Dụng cụ thể thao", "bi bi-bag", 24),
        ]
        for name, parent_name, icon_code, display_order in child_data:
            categories[name] = self.get_or_create_category(
                name,
                parent=categories[parent_name],
                icon_code=icon_code,
                display_order=display_order,
                is_featured=parent_name == "Văn phòng phẩm",
                meta_title=name,
                meta_description=f"Danh mục {name.lower()} trong ngành hàng {parent_name.lower()}.",
                meta_keywords=f"{name.lower()}, {parent_name.lower()}",
            )

        return categories

    def seed_products(self, categories):
        brand_data = [
            "Thiên Long",
            "Double A",
            "Campus",
            "Deli",
            "Pentel",
            "VPP Gia Thôn",
            "Mikasa",
            "Yonex",
            "GoodFit",
        ]
        brands = {name: Brand.objects.get_or_create(name=name)[0] for name in brand_data}

        product_data = [
            ("TL-BUT-BI-027", "Bút bi Thiên Long TL-027 xanh", "Bút viết", "Thiên Long", 4500, 300),
            ("PEN-GEL-ENERGEL", "Bút gel Pentel EnerGel 0.5mm", "Bút viết", "Pentel", 32000, 80),
            ("DA-A4-70G", "Giấy in Double A A4 70gsm", "Giấy in & giấy note", "Double A", 82000, 120),
            ("NOTE-3X3-PASTEL", "Giấy note pastel 3x3 inch", "Giấy in & giấy note", "Deli", 18000, 150),
            ("CAMPUS-A5-200", "Sổ tay Campus A5 200 trang", "Sổ tay & tập vở", "Campus", 42000, 70),
            ("NOTEBOOK-BIZ-A5", "Sổ lò xo ghi chép công việc A5", "Sổ tay & tập vở", "VPP Gia Thôn", 36000, 90),
            ("FOLDER-CLEAR-A4", "Bìa hồ sơ nhựa trong A4", "Bìa hồ sơ & lưu trữ", "Deli", 9500, 240),
            ("BOX-FILE-7CM", "Hộp lưu trữ hồ sơ 7cm", "Bìa hồ sơ & lưu trữ", "VPP Gia Thôn", 28000, 60),
            ("CLIP-BINDER-32", "Kẹp bướm binder clip 32mm", "Dụng cụ bàn làm việc", "Deli", 22000, 110),
            ("SCISSORS-OFFICE", "Kéo văn phòng 17cm", "Dụng cụ bàn làm việc", "Deli", 26000, 95),
            ("PRINTER-LASER-MINI", "Máy in laser mini văn phòng", "Thiết bị văn phòng", "VPP Gia Thôn", 1890000, 8),
            ("CALCULATOR-12DIGIT", "Máy tính để bàn 12 số", "Thiết bị văn phòng", "Deli", 125000, 35),
            ("INK-BLK-001", "Mực in đen văn phòng 100ml", "Mực in & phụ kiện in", "VPP Gia Thôn", 69000, 55),
            ("ART-WATERCOLOR-12", "Màu nước học sinh 12 màu", "Dụng cụ mỹ thuật", "VPP Gia Thôn", 58000, 48),
            ("BALL-FOOTBALL-S5", "Bóng đá size 5 tập luyện", "Bóng thể thao", "Mikasa", 185000, 25),
            ("BALL-BASKET-S7", "Bóng rổ cao su size 7", "Bóng thể thao", "Mikasa", 210000, 18),
            ("YONEX-BADMINTON-RACKET", "Vợt cầu lông Yonex beginner", "Vợt & phụ kiện", "Yonex", 420000, 12),
            ("FIT-RESISTANCE-BAND", "Dây kháng lực tập luyện", "Tập luyện thể lực", "GoodFit", 99000, 40),
            ("SPORT-BOTTLE-750", "Bình nước thể thao 750ml", "Phụ kiện thể thao", "GoodFit", 79000, 65),
        ]

        for sku, name, category_name, brand_name, price, stock in product_data:
            Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "category": categories[category_name],
                    "brand": brands[brand_name],
                    "description": f"{name} phù hợp cho nhu cầu sử dụng hằng ngày.",
                    "short_description": "Sản phẩm mẫu cho danh mục quản trị.",
                    "price": Decimal(price),
                    "cost_price": Decimal(price) * Decimal("0.7"),
                    "stock": stock,
                    "discount_percent": 0,
                    "is_active": True,
                    "is_featured": category_name in ["Bút viết", "Giấy in & giấy note", "Sổ tay & tập vở"],
                    "is_sold": False,
                    "meta_title": name,
                    "meta_description": f"Mua {name.lower()} tại VPP Gia Thôn.",
                    "meta_keywords": f"{name.lower()}, {category_name.lower()}",
                },
            )
