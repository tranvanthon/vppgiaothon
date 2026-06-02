function updatePrice(val) {
  // Định dạng số có dấu chấm ngăn cách hàng nghìn
  const formattedPrice = new Intl.NumberFormat("vi-VN").format(val);
  document.getElementById("priceValue").innerText = formattedPrice;

  // Hiệu ứng đổi màu khi kéo cực đại
  const label = document.getElementById("priceValue");
  if (val > 40000000) label.style.color = "#dc3545";
  else label.style.color = "#278aae";
}

// Gọi hàm lần đầu để hiển thị giá trị mặc định
document.addEventListener("DOMContentLoaded", function () {
  updatePrice(document.getElementById("rangeInput").value);
});