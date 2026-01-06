// static/js/portfolio/portfolio-list.js

document.addEventListener('DOMContentLoaded', () => {
    const filterChips = document.querySelectorAll('.filter-chip');
    const items = document.querySelectorAll('.portfolio-item');

    if (!filterChips.length || !items.length) return;

    filterChips.forEach(chip => {
        chip.addEventListener('click', () => {
            // active chip
            filterChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');

            const filter = chip.getAttribute('data-filter');

            items.forEach(item => {
                const category = item.getAttribute('data-category');

                if (filter === 'all' || category === filter) {
                    item.classList.remove('pf-hidden');
                    item.style.pointerEvents = 'auto';
                } else {
                    item.classList.add('pf-hidden');
                    item.style.pointerEvents = 'none';
                }
            });
        });
    });
});
