// 5. KHẮC PHỤC F5: Tự động chạy khi trang web tải xong
window.onload = function () {
  // Lấy ID trang đã lưu, nếu chưa có thì mặc định là 'dashboard'
  const lastPage = localStorage.getItem("currentPage") || "dashboard";
  showPage(lastPage);
};
