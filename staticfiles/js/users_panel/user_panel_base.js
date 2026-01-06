document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  const openBtn = document.getElementById('openSidebar');
  const closeBtn = document.getElementById('closeSidebar');
  const overlay = document.getElementById('sidebarOverlay');

  function toggleSidebar(show) {
    if (!sidebar || !overlay) return;
    if (show) {
      sidebar.classList.add('show');
      overlay.classList.remove('d-none');
    } else {
      sidebar.classList.remove('show');
      overlay.classList.add('d-none');
    }
  }

  openBtn?.addEventListener('click', () => toggleSidebar(true));
  closeBtn?.addEventListener('click', () => toggleSidebar(false));
  overlay?.addEventListener('click', () => toggleSidebar(false));
});
