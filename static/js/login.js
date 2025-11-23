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
      icon.classList.toggle("bi-eye");
      icon.classList.toggle("bi-eye-slash");
    });
  }

  // --- Toast خطای بالای صفحه ---
  const form = document.querySelector("form"); // ساده و مطمئن
  const globalError = document.getElementById("global-error");
  const globalErrorText = document.getElementById("global-error-text");

  let errorTimeoutId = null;

  function showGlobalError(message) {
    if (!globalError || !globalErrorText) return;

    globalErrorText.textContent = message;

    // نمایش
    globalError.classList.add("is-visible");

    // اگر تایمر قبلی هست، خنثی کن
    if (errorTimeoutId) {
      clearTimeout(errorTimeoutId);
    }

    // بعد از چند ثانیه مخفی کن
    errorTimeoutId = setTimeout(() => {
      globalError.classList.remove("is-visible");
    }, 4000);
  }

  // چون بک‌اند نداریم، هر بار کلیک روی "ورود به پرتال" → خطا
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault(); // جلو گیری از رفرش صفحه
      showGlobalError("ایمیل یا رمز عبور صحیح نیست");
    });
  }
});
