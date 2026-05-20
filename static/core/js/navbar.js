// navbar mobile
document.addEventListener("DOMContentLoaded", function () {
  const btnSearch = document.getElementById("btnToggleSearchMobile");
  const searchBox = document.getElementById("searchMobileBox");

  // Hàm đóng tất cả các menu đang mở
  function closeAllDropdowns() {
    document.querySelectorAll(".dropdown-content, .mega-menu").forEach((d) => {
      d.classList.remove("show");
    });
  }

  // 1. Xử lý Search Mobile
  if (btnSearch) {
    btnSearch.addEventListener("click", function (e) {
      e.stopPropagation();
      searchBox.classList.toggle("active");
      closeAllDropdowns();
    });
  }

  // 2. Xử lý Click Dropdown (Cart, Account) trên Mobile
  const actionLinks = document.querySelectorAll(".nav-action-dropdown > a");
  actionLinks.forEach((link) => {
    link.addEventListener("click", function (e) {
      if (window.innerWidth < 992) {
        e.preventDefault();
        e.stopPropagation();
        const content = this.nextElementSibling;

        // Đóng cái khác trước khi mở cái này
        document
          .querySelectorAll(".dropdown-content, .mega-menu")
          .forEach((d) => {
            if (d !== content) d.classList.remove("show");
          });
        if (searchBox) searchBox.classList.remove("active");

        content.classList.toggle("show");
      }
    });
  });

  // 3. Xử lý Danh mục (Mega Menu) trên Mobile - FIX LỖI Ở ĐÂY
  const megaMenuLink = document.querySelector(".dropdown-mega > a");
  if (megaMenuLink) {
    megaMenuLink.addEventListener("click", function (e) {
      if (window.innerWidth < 992) {
        e.preventDefault();
        e.stopPropagation();
        const menu = this.nextElementSibling; // Chính là thẻ .mega-menu

        // Đóng các dropdown cart/account nếu đang mở
        document
          .querySelectorAll(".dropdown-content")
          .forEach((d) => d.classList.remove("show"));
        if (searchBox) searchBox.classList.remove("active");

        menu.classList.toggle("show");
      }
    });
  }

  // 4. Click ra ngoài thì đóng hết
  document.addEventListener("click", function (e) {
    // Nếu click không nằm trong navbar thì mới đóng
    if (!e.target.closest(".navbar")) {
      closeAllDropdowns();
      if (searchBox) searchBox.classList.remove("active");
    }
  });
});
