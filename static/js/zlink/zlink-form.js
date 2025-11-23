document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("recode-form");
    if (!form) return;

    // باکس پیام رو به صورت داینامیک قبل فرم اضافه می‌کنیم
    const messageBox = document.createElement("div");
    messageBox.id = "recode-message";
    messageBox.className = "recode-message recode-message-hidden";
    form.parentNode.insertBefore(messageBox, form);

    const csrfInput = form.querySelector("input[name=csrfmiddlewaretoken]");
    const csrftoken = csrfInput ? csrfInput.value : "";

    function showMessage(text, type) {
        messageBox.textContent = text || "";
        messageBox.classList.remove(
            "recode-message-hidden",
            "recode-message-success",
            "recode-message-error"
        );

        if (type === "success") {
            messageBox.classList.add("recode-message-success");
        } else {
            messageBox.classList.add("recode-message-error");
        }
    }

    function clearFieldErrors() {
        form.querySelectorAll(".neo-input-error").forEach((el) => {
            el.classList.remove("neo-input-error");
        });
    }

    form.addEventListener("submit", (e) => {
        e.preventDefault();

        clearFieldErrors();

        const formData = new FormData(form);

        fetch(form.action || window.location.href, {
            method: "POST",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                ...(csrftoken && { "X-CSRFToken": csrftoken }),
                "Accept": "application/json",
            },
            body: formData,
        })
            .then(async (res) => {
                let data;
                try {
                    data = await res.json();
                } catch {
                    showMessage("خطای غیرمنتظره در پردازش پاسخ سرور.", "error");
                    return;
                }

                // موفق
                if (res.ok && data.ok) {
                    showMessage(
                        data.message || "درخواست با موفقیت ثبت شد.",
                        "success"
                    );
                    form.reset();
                    return;
                }

                // ناموفق با خطاهای فیلد
                if (data.errors) {
                    const errorTexts = [];

                    Object.entries(data.errors).forEach(
                        ([fieldName, messages]) => {
                            const input = form.querySelector(
                                `[name="${fieldName}"]`
                            );
                            if (input) {
                                input.classList.add("neo-input-error");
                            }

                            if (Array.isArray(messages)) {
                                errorTexts.push(...messages);
                            } else if (messages) {
                                errorTexts.push(messages);
                            }
                        }
                    );

                    const finalMsg =
                        errorTexts.length > 0
                            ? errorTexts.join(" • ")
                            : data.message || "فرم را بررسی کن.";

                    showMessage(finalMsg, "error");
                } else {
                    showMessage(
                        data.message || "خطا در ثبت اطلاعات.",
                        "error"
                    );
                }
            })
            .catch(() => {
                showMessage(
                    "اتصال به سرور برقرار نشد. دوباره تلاش کن.",
                    "error"
                );
            });
    });
});


