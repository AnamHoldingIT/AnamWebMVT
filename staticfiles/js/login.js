document.addEventListener("DOMContentLoaded", () => {
  // --- AOS اگر بود، فعال کن ---
  if (window.AOS) {
    AOS.init({
      duration: 700,
      easing: "ease-out-cubic",
      once: true,
      offset: 80,
    });
  }

  // --- نمایش / مخفی کردن رمز عبور ---
  const togglePasswordBtn = document.querySelector(".toggle-password");
  const passwordInput = document.getElementById("password");

  if (togglePasswordBtn && passwordInput) {
    togglePasswordBtn.addEventListener("click", () => {
      const isPassword = passwordInput.getAttribute("type") === "password";
      passwordInput.setAttribute("type", isPassword ? "text" : "password");

      const icon = togglePasswordBtn.querySelector("i");
      if (icon) {
        icon.classList.toggle("bi-eye");
        icon.classList.toggle("bi-eye-slash");
      }
    });
  }

  // --- Toast خطای بالای صفحه ---
  const globalError = document.getElementById("global-error");
  const globalErrorText = document.getElementById("global-error-text");

  let errorTimeoutId = null;

  function showGlobalError(message) {
    if (!globalError || !globalErrorText) return;

    globalErrorText.textContent = message || "نام کاربری یا رمز عبور صحیح نیست";

    globalError.classList.add("is-visible");

    if (errorTimeoutId) clearTimeout(errorTimeoutId);

    errorTimeoutId = setTimeout(() => {
      globalError.classList.remove("is-visible");
    }, 4000);
  }

  // ✅ اینجا دیگه فرم رو خراب نمی‌کنیم (نه preventDefault نه ارور فیک)
  // فقط اگر از سرور پیام خطا اومده بود (از طریق data-attribute)، نمایش بده.
  const msg = document.body?.dataset?.loginError;
  if (msg) showGlobalError(msg);
});
