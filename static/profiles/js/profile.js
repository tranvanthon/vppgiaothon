// Profile
(function () {
  const input = document.getElementById("avatarUpload");
  const preview = document.getElementById("avatarPreview");

  if (!input) return;

  const uploadUrl = input.dataset.uploadUrl;
  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

  input.addEventListener("change", function () {
    const file = this.files[0];

    if (!file) return notify("Vui lòng chọn file!", "warning");
    if (!file.type.startsWith("image/"))
      return notify("Chỉ chọn file ảnh!", "warning");
    if (file.size > 5 * 1024 * 1024)
      return notify("Ảnh tối đa 5MB!", "warning");

    const formData = new FormData();
    formData.append("avatar", file);
    formData.append("csrfmiddlewaretoken", csrfToken);

    fetch(uploadUrl, {
      method: "POST",
      body: formData,
    })
      .then((res) => {
        if (!res.ok) throw new Error("Upload thất bại");
        return res.json();
      })
      .then((data) => {
        if (data.success) {
          preview.src = data.avatar_url + "?t=" + Date.now();
          notify("Cập nhật thành công!", "success");
        } else {
          notify(data.message || "Lỗi!", "danger");
        }
      })
      .catch((err) => {
        console.error(err);
        notify(err.message, "danger");
      });
  });

  function notify(msg, type) {
    if (typeof showNotification === "function") {
      showNotification(msg, type);
    } else {
      alert(msg);
    }
  }
})();
// Form submission with AJAX
$("#profileForm").submit(function (e) {
  e.preventDefault();

  console.log("=== EDIT PROFILE DEBUG ===");
  console.log("Edit URL:", "{% url 'edit_profile' %}");
  // Kiểm tra form action
  var formAction = $("#profileForm").attr("action");
  var formData = $(this).serialize();
  console.log("Form action:", formAction);
  $.ajax({
    url: $(this).attr("action"),
    type: "POST",
    data: formData,
    success: function (response) {
      if (response.success) {
        $("#editProfileModal").modal("hide");
        location.reload();
      } else {
        showNotification(response.message || "Có lỗi xảy ra!", "danger");
      }
    },
    error: function () {
      showNotification("Có lỗi xảy ra!", "danger");
    },
  });
});

// Notification function
function showNotification(message, type) {
  var alertHtml = `
                <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                    <i class="fas fa-${type === "success" ? "check-circle" : "exclamation-circle"} me-2"></i>
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
  $(".profile-container").prepend(alertHtml);
  setTimeout(function () {
    $(".alert").fadeOut("slow");
  }, 3000);
}

// Tooltip initialization
var tooltipTriggerList = [].slice.call(
  document.querySelectorAll('[data-bs-toggle="tooltip"]'),
);
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl);
});
