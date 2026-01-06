document.addEventListener("DOMContentLoaded", () => {
    // Jalali Datepicker
    if (window.jalaliDatepicker) {
        jalaliDatepicker.startWatch({
            time: false,
            separatorChar: "-",
        });
    }

    // ------------------------
    // Filters + Search (Jalali)
    // ------------------------
    const filterBtns = document.querySelectorAll(".filter-btn");
    const items = document.querySelectorAll(".report-item");
    const search = document.getElementById("reportDateSearch");

    let activeFilter = "all";
    let activeDate = ""; // "YYYY-MM-DD" شمسی

    function applyFilters() {
        items.forEach((item) => {
            const st = item.dataset.status || "";
            const jd = item.dataset.jalali || ""; // YYYY-MM-DD

            const okStatus = activeFilter === "all" ? true : st === activeFilter;
            const okDate = !activeDate ? true : jd.includes(activeDate);

            item.classList.toggle("d-none", !(okStatus && okDate));
        });
    }

    filterBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
            filterBtns.forEach((b) => b.classList.remove("active", "text-white"));
            btn.classList.add("active", "text-white");
            activeFilter = btn.dataset.filter || "all";
            applyFilters();
        });
    });

    if (search) {
        search.addEventListener("input", () => {
            activeDate = (search.value || "").trim();
            applyFilters();
        });
    }

    applyFilters();

    // ------------------------
    // Today Timer + Progress
    // ------------------------
    const box = document.getElementById("todayTimer");
    if (!box) return; // فقط تایمر رو رد کن (فیلترها قبلاً اجرا شدن)

    const lockedIso = box.dataset.locked;
    if (!lockedIso) return;

    const lockedAt = new Date(lockedIso);

    const remainingText = document.getElementById("remainingText");
    const progressBar = document.getElementById("progressBar");
    const lockTimeText = document.getElementById("lockTimeText");

    if (!remainingText || !progressBar || !lockTimeText) return;

    function pad(n) {
        return String(n).padStart(2, "0");
    }

    function formatRemaining(ms) {
        const s = Math.max(Math.floor(ms / 1000), 0);
        const h = Math.floor(s / 3600);
        const m = Math.floor((s % 3600) / 60);
        const sec = s % 60;
        return `${h} ساعت و ${m} دقیقه و ${sec} ثانیه`;
    }

    // شروع روز (00:00 همین تاریخ)
    const dayStart = new Date(lockedAt);
    dayStart.setHours(0, 0, 0, 0);

    // کل بازه از 00:00 تا زمان قفل
    const totalMs = Math.max(lockedAt - dayStart, 1);

    // نمایش ساعت قفل
    lockTimeText.textContent = `${pad(lockedAt.getHours())}:${pad(lockedAt.getMinutes())}`;

    function tick() {
        const now = new Date();
        const remainingMs = lockedAt - now;

        remainingText.textContent = remainingMs > 0 ? formatRemaining(remainingMs) : "بسته شد";

        // elapsed از ابتدای روز
        const elapsedMs = Math.min(Math.max(now - dayStart, 0), totalMs);
        const percent = Math.round((elapsedMs / totalMs) * 100);

        progressBar.style.width = `${percent}%`;

        if (remainingMs <= 0) {
            progressBar.style.width = "100%";
            clearInterval(timer);
        }
    }

    tick();
    const timer = setInterval(tick, 1000);
});
