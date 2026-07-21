// ── 기획서 내부 서브탭 전환 (개선 항목 / 기존 로직 점검) ──
const subtabBtns = [...document.querySelectorAll('.subtab-btn')];
subtabBtns.forEach(btn=>btn.addEventListener('click',()=>{
  subtabBtns.forEach(b=>b.classList.toggle('active', b.dataset.subtab===btn.dataset.subtab));
  document.querySelectorAll('.subtab-panel').forEach(p=>p.hidden = (p.id!==btn.dataset.subtab));
  document.querySelectorAll('.toc-list').forEach(l=>l.hidden = (l.dataset.for!==btn.dataset.subtab));
  window.scrollTo({top:0});
}));

