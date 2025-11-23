document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("admin-login-form");
    const usernameInput = document.getElementById("admin-username");
    const passwordInput = document.getElementById("admin-password");

    const toast = document.getElementById("admin-login-toast");
    const toastText = document.getElementById("admin-login-toast-text");

    // ===== toggle نمایش/مخفی کردن پسورد =====
    const togglePasswordBtn = document.querySelector(".admin-toggle-password");

    if (togglePasswordBtn && passwordInput) {
        const toggleIcon = togglePasswordBtn.querySelector("i");

        togglePasswordBtn.addEventListener("click", () => {
            const isHidden = passwordInput.type === "password";

            // عوض‌کردن نوع input
            passwordInput.type = isHidden ? "text" : "password";

            // عوض‌کردن آیکون
            if (toggleIcon) {
                toggleIcon.classList.toggle("bi-eye");
                toggleIcon.classList.toggle("bi-eye-slash");
            }
        });
    }

    // ===== Toast helper =====
    function showToast(message) {
        if (!toast || !toastText) return;
        toastText.textContent = message;
        toast.classList.add("is-visible");
        setTimeout(() => toast.classList.remove("is-visible"), 4000);
    }

    // اگه فرم نباشه، دیگه بخش لاگین AJAX لازم نیست
    if (!form) return;

    // csrf رو امن بخونیم که اگه نبود، اسکریپت کرش نکنه
    const csrfInput = document.querySelector("[name=csrfmiddlewaretoken]");
    const csrftoken = csrfInput ? csrfInput.value : "";

    form.addEventListener("submit", (e) => {
        e.preventDefault();

        const username = usernameInput ? usernameInput.value.trim() : "";
        const password = passwordInput ? passwordInput.value.trim() : "";

        if (!username || !password) {
            showToast("لطفاً نام کاربری و رمز عبور را کامل وارد کنید.");
            return;
        }

        fetch(form.action, {
            method: "POST",
            headers: {
                ...(csrftoken && { "X-CSRFToken": csrftoken }),
                "Accept": "application/json"
            },
            body: new FormData(form)
        })
        .then(async (res) => {
            const data = await res.json();

            // ورود موفق
            if (res.status === 200 && data.ok) {
                window.location.href = data.redirect;
                return;
            }

            // خطای ورود (رمز/یوزر اشتباه)
            if (res.status === 400) {
                showToast(data.error || "نام کاربری یا رمز عبور صحیح نیست.");
                return;
            }

            // دسترسی نداشتن
            if (res.status === 403) {
                showToast(data.error || "دسترسی شما به این بخش محدود شده است.");
                return;
            }

            // خطای دیگر
            showToast("خطای ناشناخته. دوباره تلاش کنید.");
        })
        .catch(() => {
            showToast("خطای ارتباط با سرور.");
        });
    });
});
