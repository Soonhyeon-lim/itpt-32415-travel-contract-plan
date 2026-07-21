// ── 계약서 목업 내 [계약서 / 변경 내역] 탭 전환 ──
document.querySelectorAll('.ct-tabs').forEach(bar=>{
  const scope = bar.closest('.rs-phone-body') || document;
  const tabs = [...bar.querySelectorAll('.ct-tab')];
  tabs.forEach(tab=>tab.addEventListener('click',()=>{
    tabs.forEach(t=>t.classList.toggle('on', t===tab));
    scope.querySelectorAll('.ct-panel').forEach(p=>{
      p.hidden = (p.dataset.ctPanel !== tab.dataset.ct);
    });
    const body = bar.closest('.rs-phone-body');
    if(body) body.scrollTop = 0;
  }));
});

