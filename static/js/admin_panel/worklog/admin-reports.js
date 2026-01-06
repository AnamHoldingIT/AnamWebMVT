// static/js/admin_panel/worklog/admin-reports.js
// دقیقا کپی admin-plans.js نهایی

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
    zIndex: 99999999,
    separatorChars: { date: '/' }
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
    setTimeout(() => {
        const rawVal = dateInput.value;
        const cleaned = cleanDateValue(rawVal);

        if (cleaned === "") return; // اگر خالی شد ولش کن
        if (cleaned.length !== 10) return; // هنوز کامل نیست
        if (cleaned === initialServerValue) return; // تکراریه

        dateInput.value = cleaned;
        navField.value = "";
        form.submit();

    }, 150);
  }

  // وقتی مقدار تغییر کرد (توسط تقویم)
  dateInput.addEventListener("change", handleDateSelection);
  dateInput.addEventListener("input", function(e) {
      if(cleanDateValue(e.target.value).length === 10) {
          handleDateSelection();
      }
  });

  document.getElementById("prevDay").addEventListener("click", () => submitNav("prev"));
  document.getElementById("nextDay").addEventListener("click", () => submitNav("next"));
  document.getElementById("todayBtn").addEventListener("click", () => submitNav("today"));

  dateInput.addEventListener("keydown", function(e) {
      e.preventDefault();
  });
});