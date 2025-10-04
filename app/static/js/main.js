(function () {
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('sidebarToggle');
  const submenuButtons = document.querySelectorAll('[data-submenu]');
  const userToggle = document.getElementById('userMenuToggle');
  const userMenuWrapper = userToggle ? userToggle.closest('.topbar__user') : null;

  if (toggle && sidebar) {
    toggle.addEventListener('click', function () {
      const isDesktop = window.matchMedia('(min-width: 1024px)').matches;
      if (isDesktop) {
        const hidden = document.body.classList.toggle('sidebar-hidden');
        toggle.setAttribute('aria-expanded', String(!hidden));
        if (hidden) {
          sidebar.classList.remove('open');
        }
        return;
      }

      const expanded = toggle.getAttribute('aria-expanded') === 'true';
      const nextState = !expanded;
      toggle.setAttribute('aria-expanded', String(nextState));
      sidebar.classList.toggle('open', nextState);
    });
  }

  submenuButtons.forEach((button) => {
    const submenuId = button.getAttribute('data-submenu');
    const parent = button.closest('.sidebar__item');
    const submenu = submenuId ? document.getElementById(submenuId) : null;
    if (!parent || !submenu) return;

    button.addEventListener('click', function () {
      const nextState = !parent.classList.contains('open');
      parent.classList.toggle('open', nextState);
      submenu.classList.toggle('open', nextState);
      button.setAttribute('aria-expanded', String(nextState));
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
    const isDesktop = window.matchMedia('(min-width: 1024px)').matches;
    if (!isDesktop && !insideSidebar && !insideToggle && sidebar) {
      sidebar.classList.remove('open');
      if (toggle) toggle.setAttribute('aria-expanded', 'false');
    }

    const insideUser = event.target.closest('.topbar__user');
    if (userMenuWrapper && !insideUser) {
      userMenuWrapper.classList.remove('open');
      if (userToggle) userToggle.setAttribute('aria-expanded', 'false');
    }
  });

  window.addEventListener('resize', function () {
    const isDesktop = window.matchMedia('(min-width: 1024px)').matches;
    if (isDesktop) {
      sidebar?.classList.remove('open');
      if (toggle) {
        const hidden = document.body.classList.contains('sidebar-hidden');
        toggle.setAttribute('aria-expanded', String(!hidden));
      }
    } else {
      document.body.classList.remove('sidebar-hidden');
      if (toggle) toggle.setAttribute('aria-expanded', 'false');
    }
  });
})();
