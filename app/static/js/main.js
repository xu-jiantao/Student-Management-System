(function () {
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('sidebarToggle');
  const submenuButtons = document.querySelectorAll('[data-submenu]');
  const userToggle = document.getElementById('userMenuToggle');
  const userMenuWrapper = userToggle ? userToggle.closest('.topbar__user') : null;

  if (toggle && sidebar) {
    toggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
    });
  }

  submenuButtons.forEach((button) => {
    const submenuId = button.getAttribute('data-submenu');
    const parent = button.closest('.sidebar__item');
    const submenu = submenuId ? document.getElementById(submenuId) : null;
    if (!parent || !submenu) return;

    button.addEventListener('click', function () {
      const isOpen = parent.classList.contains('open');
      document.querySelectorAll('.sidebar__item.has-children.open').forEach((item) => {
        if (item !== parent) item.classList.remove('open');
      });
      parent.classList.toggle('open', !isOpen);
    });
  });

  if (userToggle && userMenuWrapper) {
    userToggle.addEventListener('click', function () {
      const expanded = userToggle.getAttribute('aria-expanded') === 'true';
      userToggle.setAttribute('aria-expanded', String(!expanded));
      userMenuWrapper.classList.toggle('open', !expanded);
    });
  }

  document.addEventListener('click', function (event) {
    const insideSidebar = event.target.closest('.sidebar');
    const insideToggle = event.target.closest('#sidebarToggle');
    if (!insideSidebar && !insideToggle && sidebar) {
      sidebar.classList.remove('open');
    }

    const insideUser = event.target.closest('.topbar__user');
    if (userMenuWrapper && !insideUser) {
      userMenuWrapper.classList.remove('open');
      if (userToggle) userToggle.setAttribute('aria-expanded', 'false');
    }
  });
})();
