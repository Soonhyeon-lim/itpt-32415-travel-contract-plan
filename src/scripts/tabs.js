// ── 탭 전환 ──
const tabBtns = [...document.querySelectorAll('.tab-btn')];
tabBtns.forEach(btn=>btn.addEventListener('click',()=>{
  tabBtns.forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.tab-panel').forEach(p=>p.hidden = (p.id!==btn.dataset.tab));
  window.scrollTo({top:0});
}));

