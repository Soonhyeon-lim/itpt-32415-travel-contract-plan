
(() => {
  const dialog = document.getElementById('expense-items-dialog');
  const opener = document.getElementById('expense-items-open');
  let priorOverflow = '';
  opener.addEventListener('click', () => {
    if (dialog.open) return;
    priorOverflow = document.body.style.overflow;
    dialog.showModal();
    dialog.scrollTop = 0;
    document.body.style.overflow = 'hidden';
  });
  dialog.querySelectorAll('.expense-close').forEach(button => {
    button.addEventListener('click', () => dialog.close());
  });
  dialog.addEventListener('close', () => {
    document.body.style.overflow = priorOverflow;
    opener.focus({ preventScroll: true });
  });
})();

(() => {
  const ids = new Set(['field-spec','product-fields','booking-fields','field-open-items','field-display-rules']);
  function openFieldHash() {
    const id = location.hash.slice(1);
    if (!ids.has(id)) return;
    document.querySelector('[data-tab="panel-fields"]').click();
    requestAnimationFrame(() => document.getElementById(id).scrollIntoView({block:'start'}));
  }
  window.addEventListener('hashchange', openFieldHash);
  openFieldHash();
})();

document.addEventListener('click', e => {
  const link = e.target.closest('a[href^="#"]');
  if (!link) return;
  const target = document.getElementById(link.getAttribute('href').slice(1));
  if (!target || !target.closest('#panel-fields')) return;
  document.querySelector('[data-tab="panel-fields"]').click();
  requestAnimationFrame(() => target.scrollIntoView({block:'start'}));
});
