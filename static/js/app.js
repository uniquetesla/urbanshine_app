document.addEventListener('DOMContentLoaded', () => {
  const shell = document.querySelector('.app-shell');
  const menuToggle = document.getElementById('menuToggle');

  if (!shell || !menuToggle) {
    return;
  }

  menuToggle.addEventListener('click', () => {
    const isOpen = shell.getAttribute('data-sidebar-open') === 'true';
    shell.setAttribute('data-sidebar-open', String(!isOpen));
  });

  if (window.innerWidth <= 1080) {
    shell.setAttribute('data-sidebar-open', 'false');
  }
});
