document.addEventListener('DOMContentLoaded', () => {
  const btns = document.querySelectorAll('.filter-btn');
  const items = document.querySelectorAll('.project-item');

  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      btns.forEach(b => {
        b.classList.remove('active', 'text-white', 'fw-bold');
        b.classList.add('text-white-50');
      });
      btn.classList.add('active', 'text-white', 'fw-bold');
      btn.classList.remove('text-white-50');

      const filter = btn.dataset.filter;

      items.forEach((item, index) => {
        item.style.animation = 'none';
        item.offsetHeight;

        if (filter === 'all' || item.dataset.role === filter) {
          item.classList.remove('d-none');
          item.style.animation = `fadeInUp 0.6s cubic-bezier(0.23, 1, 0.32, 1) ${index * 0.1}s forwards`;
        } else {
          item.classList.add('d-none');
        }
      });
    });
  });

  items.forEach((item, index) => {
    item.classList.add('animate-fade-in-up');
    item.style.animationDelay = `${index * 0.15}s`;
  });
});
