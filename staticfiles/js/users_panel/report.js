// static/js/users_panel/report.js

function updateRowColor(select) {
    const row = select.closest('.report-row');
    if (!row) return;

    row.classList.remove('failed-bg', 'blocked-bg');

    const v = parseInt(select.value, 10);

    // 0 = NOT_DONE, 3 = BLOCKED
    if (v === 0) row.classList.add('failed-bg');
    if (v === 3) row.classList.add('blocked-bg');
}

function removeUnplanned(btn) {
    const card = btn.closest('.unplanned-item');
    if (card) card.remove();

    const container = document.getElementById('unplannedContainer');
    const hasAny = container.querySelectorAll('.unplanned-item').length > 0;

    if (!hasAny) {
        let empty = document.getElementById('emptyUnplanned');
        if (!empty) {
            empty = document.createElement('div');
            empty.id = 'emptyUnplanned';
            empty.className = 'glass-card p-4 text-center text-white-50 dashed-border';
            empty.innerHTML = '<span class="small">موردی ثبت نشده است.</span>';
            container.appendChild(empty);
        } else {
            empty.style.display = '';
        }
    }
}

function buildExtrasJson() {
    const items = document.querySelectorAll('.unplanned-item');
    const arr = [];

    items.forEach((it) => {
        const start = (it.querySelector('.extra-start')?.value || '').trim();
        const end = (it.querySelector('.extra-end')?.value || '').trim();
        const title = (it.querySelector('.extra-title')?.value || '').trim();
        const desc = (it.querySelector('.extra-desc')?.value || '').trim();

        if (!title) return;

        arr.push({
            start: start || null,
            end: end || null,
            title,
            desc,
        });
    });

    return arr;
}

document.addEventListener('DOMContentLoaded', () => {
    // init existing rows color (if server rendered)
    document.querySelectorAll('.status-select').forEach((s) => updateRowColor(s));

    // achievement checkbox text update
    document.querySelectorAll('.achieve-checkbox').forEach((chk) => {
        chk.addEventListener('change', (e) => {
            const item = e.target.closest('.achievement-check-item');
            if (!item) return;

            const text = item.querySelector('.check-status');
            if (!text) return;

            if (e.target.checked) {
                text.textContent = 'محقق شد';
                text.className = 'check-status text-success';
            } else {
                text.textContent = 'انجام نشد';
                text.className = 'check-status text-white-50';
            }
        });
    });

    // add unplanned
    const addBtn = document.getElementById('addUnplannedBtn');
    if (addBtn) {
        addBtn.addEventListener('click', () => {
            const container = document.getElementById('unplannedContainer');
            if (!container) return;

            const empty = document.getElementById('emptyUnplanned');
            if (empty) empty.style.display = 'none';

            const div = document.createElement('div');
            div.className = 'glass-card p-3 animate-fade-in position-relative unplanned-item';
            div.innerHTML = `
        <button type="button" class="btn-close-white position-absolute top-0 end-0 m-2 btn btn-sm" onclick="removeUnplanned(this)">
          <i class="bi bi-x text-white-50"></i>
        </button>

        <div class="row g-3 align-items-end">
          <div class="col-md-2">
            <label class="super-small text-white-50 mb-1">شروع</label>
            <input type="time" class="form-control luxury-input p-2 text-center extra-start">
          </div>
          <div class="col-md-2">
            <label class="super-small text-white-50 mb-1">پایان</label>
            <input type="time" class="form-control luxury-input p-2 text-center extra-end">
          </div>
          <div class="col-md-8">
            <label class="super-small text-white-50 mb-1">شرح فعالیت</label>
            <input type="text" class="form-control luxury-input p-2 extra-title" placeholder="چه کاری انجام دادید؟">
            <input type="text" class="form-control luxury-input p-2 mt-2 extra-desc" placeholder="توضیح (اختیاری)">
          </div>
        </div>
      `;
            container.appendChild(div);
        });
    }

    // before submit -> put extras_json
    const form = document.getElementById('reportForm');
    if (form) {
        form.addEventListener('submit', () => {
            const arr = buildExtrasJson();
            const hidden = document.getElementById('extras_json');
            if (hidden) hidden.value = JSON.stringify(arr);
        });
    }
});
