// Gọi hàm lần đầu để hiển thị giá trị mặc định
document.addEventListener("DOMContentLoaded", function () {
  const rangeInput = document.getElementById("rangeInput");

  if (rangeInput) {
    updatePrice(rangeInput.value);
  }
});
function updatePrice(val) {
  const priceValue = document.getElementById("priceValue");

  const rangeInput = document.getElementById("rangeInput");

  const percent = (Number(val) / Number(rangeInput.max)) * 100;

  console.log("val =", val);
  console.log("max =", rangeInput.max);
  console.log("percent =", percent);

  priceValue.textContent = new Intl.NumberFormat("vi-VN").format(val);

  priceValue.style.color = percent > 80 ? "#dc3545" : "#278aae";
}
