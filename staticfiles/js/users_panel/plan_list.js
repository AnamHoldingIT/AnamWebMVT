document.addEventListener("DOMContentLoaded", () => {
  // فعال کردن دیت پیکر شمسی
  if (window.jalaliDatepicker) {
    jalaliDatepicker.startWatch({
      time: false,
      separatorChar: "-",
    });
  }

  const input = document.getElementById("planDateSearch");
  if (!input) return;

  const cards = document.querySelectorAll("#plansGrid .col-xl-3, #plansGrid .col-lg-4, #plansGrid .col-md-6");
  // برای اینکه فیلتر دقیق کار کنه باید تاریخ شمسی هر کارت رو توی data attribute ذخیره کنیم
  // راه سریع: روز/ماه داخل کارت رو از DOM می‌خونیم (ولی بهتره توی template data-date بدی)

  function normalize(s) {
    return (s || "").trim().replaceAll("۰","0").replaceAll("۱","1").replaceAll("۲","2")
      .replaceAll("۳","3").replaceAll("۴","4").replaceAll("۵","5")
      .replaceAll("۶","6").replaceAll("۷","7").replaceAll("۸","8")
      .replaceAll("۹","9");
  }

  input.addEventListener("input", () => {
    const val = normalize(input.value);
    if (!val) {
      cards.forEach(c => c.classList.remove("d-none"));
      return;
    }

    cards.forEach(card => {
      const jd = card.getAttribute("data-jalali") || ""; // از template می‌گیریم
      const ok = normalize(jd).includes(val);
      card.classList.toggle("d-none", !ok);
    });
  });
});
