// static/js/admin_panel/worklog/admin-plans.js

document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("dateForm");
    const navField = document.getElementById("navField");
    const dateInput = document.getElementById("date_j");

    // مقدار اولیه سرور را نگه می‌داریم
    let initialServerValue = cleanDateValue(dateInput.getAttribute("value") || "");

    // 1. تنظیمات تقویم
    jalaliDatepicker.startWatch({
        date: true,
        time: false,
        showOnFocus: true,
        showOnClick: true,
        autoClose: true,
        format: "YYYY/MM/DD",
        zIndex: 99999999, // خیلی بالا
        // این آپشن کمک میکنه اگر کاربر روزی رو انتخاب کرد که قبلا انتخاب شده، باز هم ایونت فایر شه (در برخی نسخه‌ها)
        separatorChars: {date: '/'}
    });

    // 2. توابع کمکی
    function submitNav(v) {
        navField.value = v;
        form.submit();
    }

    function faToEnDigits(str) {
        const fa = "۰۱۲۳۴۵۶۷۸۹";
        const ar = "٠١٢٣٤٥٦٧٨٩";
        return String(str || "")
            .split("")
            .map(ch => {
                const iFa = fa.indexOf(ch);
                if (iFa !== -1) return String(iFa);
                const iAr = ar.indexOf(ch);
                if (iAr !== -1) return String(iAr);
                return ch;
            })
            .join("");
    }

    function cleanDateValue(v) {
        let s = faToEnDigits(v);
        s = s.replace(/%2F/gi, "/");
        s = s.replace(/[-\\]/g, "/");
        s = s.replace(/\u200c/g, "").replace(/\s/g, "");
        s = s.replace(/[^0-9/]/g, "");
        return s;
    }

    // 3. هندل کردن انتخاب تاریخ
    function handleDateSelection() {
        // یک تاخیر کوچک می‌دهیم تا تقویم مقدار را کامل در اینپوت بنویسد
        setTimeout(() => {
            const rawVal = dateInput.value;
            const cleaned = cleanDateValue(rawVal);

            // الف) اگر خالی شد (باگ دابل کلیک)، کاری نکن (سابمیت نکن)
            if (cleaned === "") {
                // آپشنال: اگر بخواهید وقتی خالی شد، مقدار قبلی را برگردانید که کاربر گیج نشود:
                // dateInput.value = initialServerValue;
                return;
            }

            // ب) اگر مقدار معتبر نیست (کامل نشده)، سابمیت نکن
            if (cleaned.length !== 10) return;

            // ج) اگر دقیقا همان مقدار قبلی است، سابمیت نکن (مگر اینکه بخواهید رفرش شود)
            if (cleaned === initialServerValue) return;

            // د) همه چی اوکی است -> سابمیت
            dateInput.value = cleaned; // مطمئن شو مقدار تمیز ارسال میشه
            navField.value = "";
            form.submit();

        }, 150); // 150 میلی‌ثانیه صبر کافیست
    }

    // وقتی مقدار تغییر کرد (توسط تقویم)
    dateInput.addEventListener("change", handleDateSelection);
    // برخی نسخه‌ها input هم میزنند
    dateInput.addEventListener("input", function (e) {
        // فقط اگر طولش ۱۰ شد چک کن (جلوگیری از رفرش موقع تایپ)
        if (cleanDateValue(e.target.value).length === 10) {
            handleDateSelection();
        }
    });

    // دکمه‌های نویگیشن
    document.getElementById("prevDay").addEventListener("click", () => submitNav("prev"));
    document.getElementById("nextDay").addEventListener("click", () => submitNav("next"));
    document.getElementById("todayBtn").addEventListener("click", () => submitNav("today"));

    // فیکس نهایی برای جلوگیری از تایپ دستی و خرابکاری فرمت
    // این باعث میشه کاربر مجبور شه از تقویم استفاده کنه و باگ کمتر شه
    dateInput.addEventListener("keydown", function (e) {
        e.preventDefault();
        // اگر خواستید اجازه پاک کردن بدید، کد کلید Backspace رو چک کنید
        // ولی بهتره بسته باشه تا فقط با کلیک کار کنه
    });
});

// ته static/js/admin_panel/worklog/admin-plans.js اضافه کن:

(function () {
    const filtersForm = document.getElementById("filtersForm");
    if (!filtersForm) return;

    const qEl = filtersForm.querySelector('input[name="q"]');
    const statusEl = filtersForm.querySelector('select[name="status"]');
    const pageEl = filtersForm.querySelector('input[name="page"]');

    let t = null;

    const submitFilters = () => {
        if (pageEl) pageEl.value = "1";
        filtersForm.submit();
    };

    if (qEl) {
        qEl.addEventListener("input", () => {
            clearTimeout(t);
            t = setTimeout(submitFilters, 450);
        });

        qEl.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                submitFilters();
            }
        });
    }

    if (statusEl) {
        statusEl.addEventListener("change", submitFilters);
    }
})();
