document.addEventListener('DOMContentLoaded', () => {

    // --- Jalali DatePicker (اگر پلاگینش رو اضافه کردی) ---
    if (window.jalaliDatepicker) {
        jalaliDatepicker.startWatch({
            time: false,
            separatorChar: "-",
            autoClose: true,
            zIndex: 99999,
        });
    }

    let currentStep = 1;
    const totalSteps = 3;

    const form = document.getElementById('wizardForm');

    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');
    const submitBtn = document.getElementById('submitBtn');

    const steps = document.querySelectorAll('.step-content');
    const indicators = document.querySelectorAll('.step-indicator');

    // hidden inputs
    const achievementsJson = document.getElementById("achievements_json");
    const blocksJson = document.getElementById("blocks_json");
    const extrasJson = document.getElementById("extras_json");

    // --- Step 2 Core Hours: render 08:00-20:00 ---
    const coreHoursList = document.getElementById("coreHoursList");

    function pad(n) {
        return String(n).padStart(2, "0");
    }

    function renderCoreHours() {
        // 08..19 => 12 بازه (08-09 ... 19-20)
        for (let h = 8; h < 20; h++) {
            const start = `${pad(h)}:00`;
            const end = `${pad(h + 1)}:00`;

            const row = document.createElement("div");
            row.className = "time-row";
            row.innerHTML = `
        <span class="time-label">${start} - ${end}</span>
        <input
          type="text"
          class="form-control luxury-input-transparent core-task"
          placeholder="عنوان فعالیت..."
          data-start="${start}"
          data-end="${end}"
          required
        >
      `;
            coreHoursList.appendChild(row);
        }
    }

    renderCoreHours();

    // --- Wizard UI ---
    function updateWizard() {
        steps.forEach(step => {
            step.classList.remove('active');
            if (step.id === `step${currentStep}`) step.classList.add('active');
        });

        indicators.forEach(ind => {
            const stepNum = parseInt(ind.dataset.step);
            ind.classList.toggle('active', stepNum <= currentStep);
        });

        prevBtn.classList.toggle('disabled', currentStep === 1);

        if (currentStep === totalSteps) {
            nextBtn.classList.add('d-none');
            submitBtn.classList.remove('d-none');
        } else {
            nextBtn.classList.remove('d-none');
            submitBtn.classList.add('d-none');
        }
    }

    function validateStep(stepNum) {
        if (stepNum === 1) {
            const jd = document.getElementById("jalali_date");
            return jd && jd.value.trim().length > 0;
        }

        if (stepNum === 2) {
            const inputs = document.querySelectorAll(".core-task");
            for (const inp of inputs) {
                if (!inp.value.trim()) return false; // ✅ اجباری در UX
            }
            return true;
        }

        return true;
    }

    nextBtn.addEventListener('click', () => {
        if (!validateStep(currentStep)) return;

        if (currentStep < totalSteps) {
            currentStep++;
            updateWizard();
        }
    });

    prevBtn.addEventListener('click', () => {
        if (currentStep > 1) {
            currentStep--;
            updateWizard();
        }
    });

    // --- Step 1: Achievements ---
    const achieveInput = document.getElementById('achieveInput');
    const addAchieveBtn = document.getElementById('addAchieveBtn');
    const achieveList = document.getElementById('achievementsList');

    function addAchievement() {
        const val = achieveInput.value.trim();
        if (!val) return;

        const li = document.createElement('li');
        li.className = 'achieve-item';
        li.innerHTML = `
      <span class="ach-text">${val}</span>
      <i class="bi bi-trash3 text-danger" style="cursor:pointer" title="حذف"></i>
    `;
        li.querySelector("i").addEventListener("click", () => li.remove());
        achieveList.appendChild(li);

        achieveInput.value = '';
        achieveInput.focus();
    }

    addAchieveBtn.addEventListener('click', addAchievement);
    achieveInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addAchievement();
        }
    });

    // --- Step 3: Extra Hours ---
    const addExtraBtn = document.getElementById('addExtraBtn');
    const extraContainer = document.getElementById('extraHoursContainer');

    addExtraBtn.addEventListener('click', () => {
        const div = document.createElement('div');
        div.className = 'extra-card';
        div.innerHTML = `
      <i class="bi bi-x-lg btn-delete-extra" title="حذف"></i>
      <div class="row g-3">
        <div class="col-6">
          <label class="super-small text-white-50">از ساعت</label>
          <input type="time" class="form-control luxury-input text-center extra-start">
        </div>
        <div class="col-6">
          <label class="super-small text-white-50">تا ساعت</label>
          <input type="time" class="form-control luxury-input text-center extra-end">
        </div>
        <div class="col-12">
          <input type="text" class="form-control luxury-input extra-title" placeholder="عنوان فعالیت...">
        </div>
        <div class="col-12">
          <input type="text" class="form-control luxury-input extra-desc" placeholder="توضیحات تکمیلی (اختیاری)">
        </div>
      </div>
    `;
        div.querySelector(".btn-delete-extra").addEventListener("click", () => div.remove());
        extraContainer.appendChild(div);
    });

    // --- Submit: pack data into JSON and submit real form ---
    submitBtn.addEventListener("click", () => {
        // قبل از submit مرحله 2 هم اجباریه
        if (!validateStep(1) || !validateStep(2)) return;

        // achievements
        const ach = [];
        document.querySelectorAll("#achievementsList .ach-text").forEach(el => {
            const t = el.textContent.trim();
            if (t) ach.push(t);
        });
        achievementsJson.value = JSON.stringify(ach);

        // core blocks 08-20
        const blocks = [];
        document.querySelectorAll(".core-task").forEach(inp => {
            const title = inp.value.trim();
            if (!title) return;
            blocks.push({
                start: inp.dataset.start,
                end: inp.dataset.end,
                title: title,
                desc: ""
            });
        });
        blocksJson.value = JSON.stringify(blocks);

        // extras
        const extras = [];
        document.querySelectorAll("#extraHoursContainer .extra-card").forEach(card => {
            const st = card.querySelector(".extra-start")?.value || "";
            const en = card.querySelector(".extra-end")?.value || "";
            const tt = card.querySelector(".extra-title")?.value || "";
            const ds = card.querySelector(".extra-desc")?.value || "";

            // فقط اگر حداقل title و start/end داشت، بفرست
            if (st && en && tt.trim()) {
                extras.push({start: st, end: en, title: tt.trim(), desc: ds.trim()});
            }
        });
        extrasJson.value = JSON.stringify(extras);

        form.submit();
    });

    updateWizard();
});
