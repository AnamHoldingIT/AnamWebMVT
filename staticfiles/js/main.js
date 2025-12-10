// اطمینان از آماده بودن DOM
document.addEventListener('DOMContentLoaded', () => {
    /* =========================
       1. اسکرول نوبار (کلاس scrolled)
       ========================= */
    const nav = document.getElementById('mainNav');

    const handleNavbarScroll = () => {
        if (document.body.scrollTop >= 50 || document.documentElement.scrollTop >= 50) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
    };

    handleNavbarScroll();
    window.addEventListener('scroll', handleNavbarScroll);

    /* =========================
       2. اسکرول نرم + بستن منوی موبایل
       ========================= */
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link[href^="#"]');
    const offcanvasEl = document.getElementById('offcanvasNavbar');

    let offcanvasInstance = null;
    if (offcanvasEl && typeof bootstrap !== 'undefined') {
        offcanvasInstance = bootstrap.Offcanvas.getOrCreateInstance(offcanvasEl);
    }

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');

            // فقط لینک‌های داخلی #...
            if (href && href.startsWith('#')) {
                const targetId = href.replace('#', '');
                const targetEl = document.getElementById(targetId);

                if (targetEl) {
                    e.preventDefault();
                    targetEl.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }

            // بستن منوی موبایل بعد از کلیک
            if (offcanvasInstance && window.innerWidth < 992) {
                offcanvasInstance.hide();
            }
        });
    });

    /* =========================
       3. انیمیشن کانترها (Metrics)
       ========================= */
    const counters = document.querySelectorAll('.counter');
    const speed = 200; // هرچه کمتر، سرعت بیشتر

    const animateCounters = () => {
        counters.forEach(counter => {
            const updateCount = () => {
                const target = +counter.getAttribute('data-target');
                const count = +counter.innerText;

                const inc = target / speed;

                if (count < target) {
                    counter.innerText = Math.ceil(count + inc);
                    setTimeout(updateCount, 20);
                } else {
                    counter.innerText = target;
                }
            };
            updateCount();
        });
    };

    let hasRun = false;
    const metricsSection = document.getElementById('metrics');

    if (metricsSection && 'IntersectionObserver' in window) {
        const sectionObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting && !hasRun) {
                animateCounters();
                hasRun = true;
            }
        }, {
            threshold: 0.4
        });

        sectionObserver.observe(metricsSection);
    } else {
        // اگر IntersectionObserver نبود (مرورگر قدیمی)، مستقیم اجرا کن
        animateCounters();
    }
});


document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("contract-form");
  if (!form) return;

  const messageBox = document.getElementById("contract-message");
  const messageText = document.getElementById("contract-message-text");
  const submitBtn = form.querySelector('button[type="submit"]');

  function showMessage(text, isError = true) {
    if (!messageBox || !messageText) return;

    messageText.textContent = text;

    // استایل خطا/موفقیت ساده
    messageBox.style.display = "flex";
    messageBox.style.background = isError
      ? "rgba(255, 0, 0, 0.08)"
      : "rgba(0, 128, 0, 0.15)";
    messageBox.style.borderColor = isError
      ? "rgba(255, 90, 90, 0.4)"
      : "rgba(120, 255, 120, 0.4)";
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    const url = form.action;
    const formData = new FormData(form);
    const csrfInput = form.querySelector("[name=csrfmiddlewaretoken]");
    const csrfToken = csrfInput ? csrfInput.value : "";

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerText = "در حال ارسال...";
    }

    fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
        "X-Requested-With": "XMLHttpRequest",
      },
      body: formData,
    })
      .then((response) =>
        response.json().then((data) => ({ ok: response.ok, data }))
      )
      .then(({ ok, data }) => {
        if (ok && data.ok) {
          showMessage(data.message || "درخواست شما با موفقیت ثبت شد.", false);
          form.reset();
        } else {
          // ساختن پیام خطا از روی errors فرم
          if (data && data.errors) {
            let msgs = [];
            for (const [field, errors] of Object.entries(data.errors)) {
              if (Array.isArray(errors)) {
                msgs.push(errors.join("، "));
              } else {
                msgs.push(errors);
              }
            }
            showMessage(msgs.join(" | "));
          } else {
            showMessage("خطایی رخ داد. لطفاً بعداً دوباره تلاش کنید.");
          }
        }
      })
      .catch((err) => {
        console.error(err);
        showMessage("خطایی در ارتباط با سرور رخ داد.");
      })
      .finally(() => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerText = "ارسال درخواست بررسی";
        }
      });
  });
});



