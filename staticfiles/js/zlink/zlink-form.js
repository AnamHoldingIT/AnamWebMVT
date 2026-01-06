document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("recode-form");
    if (!form) return;

    // جلوگیری از اجرای تکراری
    if (form.dataset.ajaxBound === "1") return;
    form.dataset.ajaxBound = "1";

    const submitBtn = form.querySelector('button[type="submit"]');
    const defaultBtnText = submitBtn ? submitBtn.textContent : "ثبت درخواست";

    // باکس پیام
    let messageBox = document.getElementById("recode-message");
    if (!messageBox) {
        messageBox = document.createElement("div");
        messageBox.id = "recode-message";
        messageBox.className = "recode-message recode-message-hidden";
        form.parentNode.insertBefore(messageBox, form);
    }

    let submitting = false;

    // --- توابع کمکی ---

    function showMessage(text, type) {
        messageBox.innerHTML = text; // استفاده از innerHTML برای خط‌شکنی
        messageBox.classList.remove("recode-message-hidden", "recode-message-success", "recode-message-error");
        messageBox.classList.add(type === "success" ? "recode-message-success" : "recode-message-error");

        // اسکرول نرم به سمت پیام
        messageBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function clearFieldErrors() {
        form.querySelectorAll(".neo-input-error").forEach((el) => el.classList.remove("neo-input-error"));
        messageBox.classList.add("recode-message-hidden");
    }

    function setLoading(isLoading) {
        if (!submitBtn) return;
        submitBtn.disabled = isLoading;
        if (isLoading) {
            submitBtn.textContent = "در حال پردازش...";
            submitBtn.classList.add("btn-loading");
        } else {
            submitBtn.textContent = defaultBtnText;
            submitBtn.classList.remove("btn-loading");
        }
    }

    // --- هندلر فرم ---

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (submitting) return;
        submitting = true;
        setLoading(true);
        clearFieldErrors();

        const formData = new FormData(form);
        const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]')?.value;

        try {
            const response = await fetch(form.action, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": csrfToken,
                    "Accept": "application/json",
                },
                body: formData,
            });

            // تلاش برای پارس کردن JSON
            let data;
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                data = await response.json();
            } else {
                throw new Error("پاسخ سرور معتبر نیست.");
            }

            // === موفقیت (Status 200) ===
            if (response.ok && data.ok) {
                showMessage(`
                    <i class="bi bi-check-circle-fill"></i>
                    ${data.message || "درخواست شما با موفقیت ثبت شد."}
                `, "success");

                form.reset();

                // غیرفعال کردن دکمه برای جلوگیری از ثبت مجدد
                if (submitBtn) {
                    submitBtn.textContent = "ثبت شد ✅";
                    submitBtn.disabled = true;
                }
                // اگر خواستی بعد از چند ثانیه رفرش کنی یا کاری کنی اینجا بنویس
            }
            // === ارور ولیدیشن (Status 400) ===
            else if (response.status === 400 || !data.ok) {

                if (data.errors) {
                    let errorList = [];

                    // هایلایت کردن اینپوت‌های قرمز
                    Object.entries(data.errors).forEach(([fieldName, messages]) => {
                        const input = form.querySelector(`[name="${fieldName}"]`);
                        if (input) {
                            input.classList.add("neo-input-error");
                            // برای UX بهتر: فوکوس روی اولین فیلد خطا دار
                            if (errorList.length === 0) input.focus();
                        }

                        // جمع‌آوری متن ارورها
                        const msgText = Array.isArray(messages) ? messages.join("، ") : messages;
                        errorList.push(`• ${msgText}`);
                    });

                    showMessage(errorList.join("<br>"), "error");
                } else {
                    showMessage(data.message || "اطلاعات وارد شده صحیح نیست.", "error");
                }
            }
            // === سایر ارورها ===
            else {
                showMessage("خطایی در سرور رخ داد. لطفاً مجدداً تلاش کنید.", "error");
            }

        } catch (err) {
            console.error(err);
            showMessage("مشکل در برقراری ارتباط با سرور.", "error");
        } finally {
            // اگر موفقیت آمیز بود، دکمه را قفل نگه دار، وگرنه آزاد کن
            const isSuccess = document.querySelector(".recode-message-success");
            if (!isSuccess) {
                submitting = false;
                setLoading(false);
            }
        }
    });
});