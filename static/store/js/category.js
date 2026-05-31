document.addEventListener("DOMContentLoaded", function () {
  const rangeInput = document.getElementById("rangeInput");

  if (rangeInput) {
    updatePrice(rangeInput.value);
  }
});
