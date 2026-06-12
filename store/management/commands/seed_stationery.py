from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from store.models import Category, Product


CATEGORIES = [
    {
        "name": "Bút viết",
        "slug": "but-viet",
        "icon_code": "bi bi-pen",
        "products": [
            ("Bút bi Thiên Long TL-027 xanh", 5000, 120),
            ("Bút bi Thiên Long TL-027 đen", 5000, 100),
            ("Bút gel Pilot G2 0.5mm", 32000, 60),
            ("Bút nước Uni-ball Eye Fine", 38000, 45),
            ("Bút máy học sinh Hồng Hà", 45000, 35),
            ("Bút chì gỗ 2B Staedtler", 12000, 90),
            ("Bút chì kim Pentel 0.5mm", 55000, 40),
            ("Bút dạ quang Stabilo vàng", 18000, 70),
            ("Bút lông dầu Thiên Long PM-09", 15000, 55),
            ("Bộ bút màu 12 cây Colokit", 68000, 30),
        ],
    },
    {
        "name": "Sổ và giấy",
        "slug": "so-va-giay",
        "icon_code": "bi bi-journal-text",
        "products": [
            ("Sổ lò xo A5 200 trang", 42000, 65),
            ("Sổ da văn phòng A5", 95000, 25),
            ("Sổ tay bỏ túi A6", 28000, 80),
            ("Tập sinh viên 200 trang", 18000, 110),
            ("Giấy in Double A A4 70gsm", 85000, 50),
            ("Giấy in PaperOne A4 80gsm", 105000, 40),
            ("Giấy note vàng 3x3 inch", 16000, 100),
            ("Giấy note 5 màu phân trang", 22000, 75),
            ("Giấy bìa màu A4 100 tờ", 65000, 35),
            ("Giấy decal A4 100 tờ", 125000, 20),
        ],
    },
    {
        "name": "Dụng cụ học tập",
        "slug": "dung-cu-hoc-tap",
        "icon_code": "bi bi-rulers",
        "products": [
            ("Thước kẻ nhựa 20cm", 8000, 100),
            ("Bộ thước Eke học sinh", 25000, 60),
            ("Compa kim loại Deli", 45000, 35),
            ("Gôm tẩy Staedtler trắng", 12000, 90),
            ("Gọt bút chì 2 lỗ Deli", 18000, 70),
            ("Hộp bút vải 2 ngăn", 55000, 40),
            ("Bảng con học sinh 2 mặt", 32000, 50),
            ("Phấn không bụi 10 viên", 15000, 65),
            ("Máy tính Casio FX-580VN X", 720000, 18),
            ("Bộ dụng cụ học sinh 8 món", 89000, 30),
        ],
    },
    {
        "name": "Dụng cụ văn phòng",
        "slug": "dung-cu-van-phong",
        "icon_code": "bi bi-scissors",
        "products": [
            ("Kéo văn phòng Deli 17cm", 35000, 45),
            ("Dao rọc giấy lớn Deli", 28000, 55),
            ("Bấm kim số 10 Plus", 48000, 40),
            ("Kim bấm số 10 Max", 9000, 120),
            ("Bấm lỗ 2 lỗ Deli", 85000, 25),
            ("Băng keo trong 5cm", 18000, 80),
            ("Cắt băng keo để bàn", 65000, 30),
            ("Keo khô 15g Thiên Long", 12000, 75),
            ("Kẹp giấy tam giác 100 cái", 15000, 90),
            ("Kẹp bướm đen 25mm 12 cái", 22000, 65),
        ],
    },
    {
        "name": "Hồ sơ và lưu trữ",
        "slug": "ho-so-va-luu-tru",
        "icon_code": "bi bi-folder2-open",
        "products": [
            ("Bìa lá A4 100 cái", 95000, 35),
            ("Bìa nút A4 trong suốt", 8000, 100),
            ("Bìa còng 5cm Kokuyo", 78000, 30),
            ("Bìa trình ký đôi A4", 45000, 45),
            ("File hộp 10cm", 55000, 40),
            ("Túi hồ sơ dây A4", 18000, 70),
            ("Bìa phân trang 12 màu", 32000, 55),
            ("Khay tài liệu 3 tầng", 185000, 20),
            ("Hộp đựng name card 600 thẻ", 125000, 18),
            ("Tủ hồ sơ mini 5 ngăn", 245000, 15),
        ],
    },
]


class Command(BaseCommand):
    help = "Tạo 5 danh mục văn phòng phẩm và 10 sản phẩm cho mỗi danh mục."

    @transaction.atomic
    def handle(self, *args, **options):
        category_count = 0
        product_count = 0

        for category_order, category_data in enumerate(CATEGORIES, start=1):
            category, category_created = Category.objects.update_or_create(
                slug=category_data["slug"],
                defaults={
                    "name": category_data["name"],
                    "icon_code": category_data["icon_code"],
                    "is_active": True,
                    "is_featured": category_order <= 3,
                    "display_order": category_order,
                    "meta_title": f"{category_data['name']} chính hãng",
                    "meta_description": (
                        f"Danh mục {category_data['name'].lower()} dành cho học tập "
                        "và công việc văn phòng."
                    ),
                    "meta_keywords": "văn phòng phẩm, học tập, văn phòng",
                },
            )
            category_count += int(category_created)

            sku_prefix = f"VPP-{category_order:02d}"
            for product_order, (name, price, stock) in enumerate(
                category_data["products"], start=1
            ):
                sku = f"{sku_prefix}-{product_order:03d}"
                discount = Decimal("10") if product_order % 4 == 0 else Decimal("0")
                _, product_created = Product.objects.update_or_create(
                    sku=sku,
                    defaults={
                        "name": name,
                        "slug": f"{slugify(name)}-{sku.lower()}",
                        "category": category,
                        "description": (
                            f"{name} phù hợp cho học sinh, sinh viên và nhân viên "
                            "văn phòng. Sản phẩm dùng để thực hành và kiểm thử cửa hàng."
                        ),
                        "short_description": (
                            f"{name} - sản phẩm văn phòng phẩm tiện dụng, dễ sử dụng."
                        ),
                        "price": Decimal(price),
                        "cost_price": Decimal(price) * Decimal("0.65"),
                        "discount_percent": discount,
                        "stock": stock,
                        "low_stock_threshold": 10,
                        "track_stock": True,
                        "is_active": True,
                        "is_featured": product_order <= 2,
                        "is_sold": False,
                        "meta_title": name,
                        "meta_description": f"Mua {name.lower()} tại cửa hàng văn phòng phẩm.",
                        "meta_keywords": f"{name}, văn phòng phẩm",
                    },
                )
                product_count += int(product_created)

        self.stdout.write(
            self.style.SUCCESS(
                "Đã seed 5 danh mục và 50 sản phẩm "
                f"({category_count} danh mục mới, {product_count} sản phẩm mới)."
            )
        )
