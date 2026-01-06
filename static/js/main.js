document.addEventListener("DOMContentLoaded", () => {
    /* =========================
       1) Navbar scroll (RAF + passive)
       ========================= */
    const nav = document.getElementById("mainNav");

    let lastY = window.scrollY || 0;
    let ticking = false;
    let scrollStopTimer = null;

    const applyNavbarState = () => {
        if (!nav) return;
        if (lastY >= 50) nav.classList.add("scrolled");
        else nav.classList.remove("scrolled");
    };

    const onScroll = () => {
        lastY = window.scrollY || document.documentElement.scrollTop || 0;

        // توقف موقت انیمیشن‌های سنگین هنگام اسکرول
        document.body.classList.add("is-scrolling");
        clearTimeout(scrollStopTimer);
        scrollStopTimer = setTimeout(() => {
            document.body.classList.remove("is-scrolling");
        }, 220);

        // throttle با requestAnimationFrame
        if (!ticking) {
            ticking = true;
            requestAnimationFrame(() => {
                applyNavbarState();
                ticking = false;
            });
        }
    };

    applyNavbarState();
    window.addEventListener("scroll", onScroll, {passive: true});

    /* =========================
       2) Smooth scroll + close offcanvas
       ========================= */
    // ✅ فقط لینک‌های اسکرولی، نه dropdown-toggle ها
    const navLinks = document.querySelectorAll(
        '.navbar-nav .nav-link[href^="#"]:not(.dropdown-toggle)'
    );

    const offcanvasEl = document.getElementById("offcanvasNavbar");
    let offcanvasInstance = null;

    if (offcanvasEl && typeof bootstrap !== "undefined") {
        offcanvasInstance = bootstrap.Offcanvas.getOrCreateInstance(offcanvasEl);
    }

    navLinks.forEach((link) => {
        link.addEventListener("click", (e) => {
            // ✅ اگه به هر دلیلی dropdown-toggle بود، اصلاً دست نزن
            if (
                link.classList.contains("dropdown-toggle") ||
                link.getAttribute("data-bs-toggle") === "dropdown"
            ) {
                return;
            }

            const href = link.getAttribute("href");
            if (!href || href === "#") return;

            const targetEl = document.getElementById(href.slice(1));
            if (!targetEl) return;

            e.preventDefault();

            targetEl.scrollIntoView({
                behavior: "smooth",
                block: "start",
            });

            if (offcanvasInstance && window.innerWidth < 992) {
                offcanvasInstance.hide();
            }
        });
    });

    /* =========================
       3) Counters (Metrics)
       ========================= */
    const counters = document.querySelectorAll(".counter");
    const metricsSection = document.getElementById("metrics");
    let countersRan = false;

    const animateCounter = (el, duration = 900) => {
        const target = Number(el.getAttribute("data-target")) || 0;
        const startTime = performance.now();

        const step = (now) => {
            const t = Math.min(1, (now - startTime) / duration);
            const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic
            const value = Math.floor(target * eased);
            el.innerText = value.toString();

            if (t < 1) requestAnimationFrame(step);
            else el.innerText = target.toString();
        };

        requestAnimationFrame(step);
    };

    const runCounters = () => {
        if (countersRan) return;
        counters.forEach((c) => animateCounter(c));
        countersRan = true;
    };

    if (metricsSection && "IntersectionObserver" in window) {
        const io = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting) runCounters();
            },
            {threshold: 0.35}
        );
        io.observe(metricsSection);
    } else {
        runCounters();
    }

    /* =========================
       4) Contract form
       ========================= */
    const form = document.getElementById("contract-form");
    if (!form) return;

    const messageBox = document.getElementById("contract-message");
    const messageText = document.getElementById("contract-message-text");
    const submitBtn = form.querySelector('button[type="submit"]');

    const showMessage = (text, isError = true) => {
        if (!messageBox || !messageText) return;
        messageText.textContent = text;

        messageBox.style.display = "flex";
        messageBox.style.background = isError
            ? "rgba(255, 0, 0, 0.08)"
            : "rgba(0, 128, 0, 0.15)";
        messageBox.style.borderColor = isError
            ? "rgba(255, 90, 90, 0.4)"
            : "rgba(120, 255, 120, 0.4)";
    };

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const url = form.action;
        const formData = new FormData(form);
        const csrfInput = form.querySelector("[name=csrfmiddlewaretoken]");
        const csrfToken = csrfInput ? csrfInput.value : "";

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerText = "در حال ارسال...";
        }

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: formData,
            });

            const data = await response.json();

            if (response.ok && data.ok) {
                showMessage(data.message || "درخواست شما با موفقیت ثبت شد.", false);
                form.reset();
            } else {
                if (data && data.errors) {
                    const msgs = [];
                    for (const errors of Object.values(data.errors)) {
                        msgs.push(Array.isArray(errors) ? errors.join("، ") : String(errors));
                    }
                    showMessage(msgs.join(" | "));
                } else {
                    showMessage("خطایی رخ داد. لطفاً بعداً دوباره تلاش کنید.");
                }
            }
        } catch (err) {
            console.error(err);
            showMessage("خطایی در ارتباط با سرور رخ داد.");
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerText = "ارسال درخواست بررسی";
            }
        }
    });
});
