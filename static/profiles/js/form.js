document.addEventListener("DOMContentLoaded", function () {

  // =========================
  // Toggle password
  // =========================
  document.querySelectorAll(".toggle-password").forEach((icon) => {
    icon.addEventListener("click", () => {

      const input = document.getElementById(icon.dataset.target);

      if (!input) return;

      input.type =
        input.type === "password"
          ? "text"
          : "password";

      icon.classList.toggle("bi-eye");
      icon.classList.toggle("bi-eye-slash");
    });
  });

  // =========================
  // Detect password fields
  // =========================

  const password1 =
    document.getElementById("id_password1") ||
    document.getElementById("id_new_password1");

  const password2 =
    document.getElementById("id_password2") ||
    document.getElementById("id_new_password2");

  const result =
    document.getElementById("result");

  const matchResult =
    document.getElementById("match-result");

  const form = document.querySelector("form");

  // =========================
  // Password strength
  // =========================
  function checkPasswordStrength() {

    if (!password1 || !result) return true;

    let password = password1.value.trim();

    let hasNumber = /[0-9]/.test(password);
    let hasUpper = /[A-Z]/.test(password);
    let hasLower = /[a-z]/.test(password);
    let hasSpecial = /[^A-Za-z0-9]/.test(password);

    let errors = [];

    if (password.length < 8)
      errors.push("ít nhất 8 kí tự");

    if (!hasLower)
      errors.push("chữ thường");

    if (!hasUpper)
      errors.push("chữ hoa");

    if (!hasNumber)
      errors.push("số");

    if (!hasSpecial)
      errors.push("kí tự đặc biệt");

    if (errors.length === 0) {

      result.innerHTML =
        "✅ Mật khẩu mạnh";

      result.className =
        "small text-success mt-1";

      return true;

    } else {

      result.innerHTML =
        "⚠️ Thiếu: " + errors.join(", ");

      result.className =
        "small text-danger mt-1";

      return false;
    }
  }

  // =========================
  // Password match
  // =========================
  function checkPasswordMatch() {

    if (!password1 || !password2 || !matchResult)
      return true;

    if (password2.value === "") {

      matchResult.innerHTML = "";
      return false;
    }

    if (password1.value === password2.value) {

      matchResult.innerHTML =
        "✅ Mật khẩu khớp";

      matchResult.className =
        "small text-success mt-1";

      return true;

    } else {

      matchResult.innerHTML =
        "❌ Mật khẩu không khớp";

      matchResult.className =
        "small text-danger mt-1";

      return false;
    }
  }

  // =========================
  // Realtime check
  // =========================

  if (password1) {

    password1.addEventListener("input", () => {
      checkPasswordStrength();
      checkPasswordMatch();
    });
  }

  if (password2) {

    password2.addEventListener("input", () => {
      checkPasswordMatch();
    });
  }

  // =========================
  // Prevent submit
  // =========================

  if (form) {

    form.addEventListener("submit", function (e) {

      let strong = checkPasswordStrength();
      let matched = checkPasswordMatch();

      if (!strong || !matched) {
        e.preventDefault();
      }
    });
  }

});