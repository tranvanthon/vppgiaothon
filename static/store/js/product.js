// Cấu hình các tùy chọn Lightbox2
if (window.lightbox) {
  lightbox.option({
    wrapAround: true,
    alwaysShowNavOnTouchDevices: true,
    albumLabel: "Ảnh %1 / %2",
    fadeDuration: 300,
    imageFadeDuration: 300,
  });
}

// 2. Xử lý sự kiện click "Xem nhanh"
$(document).ready(function () {
  $(document).on("click", ".quick-view-btn", function (e) {
    e.preventDefault();
    e.stopPropagation(); // Ngăn chặn nổi bọt sự kiện

    // Tìm link ảnh trong đúng card hiện tại và kích hoạt như click trực tiếp vào ảnh.
    const firstImageLink = $(this)
      .closest(".product-img-wrapper")
      .find("a[data-lightbox]")
      .get(0);

    if (!firstImageLink) {
      return;
    }

    firstImageLink.click();
  });
});

function previewImages(event) {
  const preview = document.getElementById("preview");
  preview.innerHTML = "";

  for (const file of event.target.files) {
    const wrapper = document.createElement("div");
    wrapper.style.display = "inline-block";
    wrapper.style.position = "relative";
    wrapper.style.margin = "5px";

    const img = document.createElement("img");
    img.src = URL.createObjectURL(file);
    img.width = 100;

    // nút xoá ❌
    const btn = document.createElement("button");
    btn.innerHTML = "❌";
    btn.style.position = "absolute";
    btn.style.top = "0";
    btn.style.right = "0";
    //btn.style.background = 'red'
    btn.style.color = "white";
    btn.style.border = "none";
    btn.style.cursor = "pointer";

    btn.onclick = () => wrapper.remove();

    wrapper.appendChild(img);
    wrapper.appendChild(btn);
    preview.appendChild(wrapper);
  }
}
