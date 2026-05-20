function showPage(pageId, element) {
  // 1. Ẩn tất cả các trang
  document.querySelectorAll(".page-content").forEach((page) => {
    page.classList.remove("active");
  });

  // 2. Hiện trang được chọn (nếu ID tồn tại)
  const targetPage = document.getElementById(pageId);
  if (targetPage) {
    targetPage.classList.add("active");

    // 3. Lưu ID trang vào localStorage để "ghi nhớ" khi F5
    localStorage.setItem("currentPage", pageId);
  }

  // 4. Cập nhật trạng thái active của menu sidebar
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.classList.remove("active");
  });

  // Nếu có truyền element (click chuột), hoặc tìm element dựa trên ID (khi F5)
  if (element) {
    element.classList.add("active");
  } else {
    const activeLink = document.querySelector(`[onclick*="'${pageId}'"]`);
    if (activeLink) activeLink.classList.add("active");
  }
}

// 5. KHẮC PHỤC F5: Tự động chạy khi trang web tải xong
window.onload = function () {
  // Lấy ID trang đã lưu, nếu chưa có thì mặc định là 'dashboard'
  const lastPage = localStorage.getItem("currentPage") || "dashboard";
  showPage(lastPage);
};
