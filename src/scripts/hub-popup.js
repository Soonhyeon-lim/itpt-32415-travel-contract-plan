// SC-03 preview only; no service requests or delivery actions.
document.querySelectorAll('[data-hubpop]').forEach(btn => {
  const pop = document.getElementById(btn.dataset.hubpop);
  if (!pop) return;
  const close = () => { pop.classList.remove('on'); btn.focus({preventScroll:true}); };
  btn.addEventListener('click', () => { pop.classList.add('on'); pop.querySelector('[data-hubclose]')?.focus(); });
  pop.querySelectorAll('[data-hubclose]').forEach(x => x.addEventListener('click',close));
  pop.addEventListener('click',e => { if(e.target===pop)close(); });
  document.addEventListener('keydown',e => {if(e.key==='Escape' && pop.classList.contains('on'))close();});
});
