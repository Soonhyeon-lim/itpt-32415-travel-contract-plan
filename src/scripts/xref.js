// ── 섹션 코드(IM/LG/AS/SC-00) 자동 링크 + 해당 섹션으로 이동 ──
const XREF_MAP = {
  IM: {tab:'panel-plan',    sub:'content-improve',  pre:'imp'},
  LG: {tab:'panel-plan',    sub:'content-logic',    pre:'lgc'},
  AS: {tab:'panel-plan',    sub:'content-existing', pre:'ref'},
  SC: {tab:'panel-screens', sub:null,               pre:'sc'}
};
function xrefTarget(code){
  const m = /^(IM|LG|AS|SC)-(\d{2})$/.exec(code);
  if(!m) return null;
  const cfg = XREF_MAP[m[1]];
  if(!cfg) return null;
  const id = (m[1]==='SC') ? 'sc'+m[2] : cfg.pre + parseInt(m[2],10);
  return document.getElementById(id) ? {tab:cfg.tab, sub:cfg.sub, id} : null;
}

// 본문 텍스트에서 코드 패턴을 찾아 링크로 감싼다 (배지·목차·실화면 임베드는 제외)
(function linkifyCodes(){
  const RE = /\b(IM|LG|AS|SC)-(\d{2})\b/g;
  const SKIP_TAG = new Set(['A','CODE','SCRIPT','STYLE','BUTTON','TEXTAREA']);
  const SKIP_CLS = ['sec-num','toc','scr-nav','hnt-contract-embed','hnt-sc01-embed','xref','scid'];
  document.querySelectorAll('#panel-plan main, #panel-screens .scr-main, #panel-history, #panel-refs').forEach(root=>{
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node){
        RE.lastIndex = 0;
        if(!RE.test(node.nodeValue)) return NodeFilter.FILTER_REJECT;
        for(let p=node.parentElement; p && p!==root.parentElement; p=p.parentElement){
          if(SKIP_TAG.has(p.tagName)) return NodeFilter.FILTER_REJECT;
          if(p.classList && SKIP_CLS.some(c=>p.classList.contains(c))) return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    const nodes = []; let n;
    while((n = walker.nextNode())) nodes.push(n);
    nodes.forEach(node=>{
      const txt = node.nodeValue, frag = document.createDocumentFragment();
      let last = 0, m; RE.lastIndex = 0;
      while((m = RE.exec(txt))){
        if(!xrefTarget(m[0])) continue;              // 존재하지 않는 코드는 링크 안 함
        if(m.index > last) frag.appendChild(document.createTextNode(txt.slice(last, m.index)));
        const a = document.createElement('a');
        a.className = 'xref'; a.dataset.code = m[0]; a.textContent = m[0];
        a.setAttribute('role','link'); a.tabIndex = 0;
        a.title = m[0] + ' 섹션으로 이동';
        frag.appendChild(a);
        last = m.index + m[0].length;
      }
      if(!frag.childNodes.length) return;
      if(last < txt.length) frag.appendChild(document.createTextNode(txt.slice(last)));
      node.parentNode.replaceChild(frag, node);
    });
  });
})();

function gotoXref(code){
  const t = xrefTarget(code);
  if(!t) return;
  const tabBtn = document.querySelector('.tab-btn[data-tab="'+t.tab+'"]');
  if(tabBtn && !tabBtn.classList.contains('active')) tabBtn.click();
  if(t.sub){
    const subBtn = document.querySelector('.subtab-btn[data-subtab="'+t.sub+'"]');
    if(subBtn && !subBtn.classList.contains('active')) subBtn.click();
  }
  // 탭 전환이 스크롤을 0으로 되돌리므로 그 다음 프레임에 이동
  setTimeout(function(){
    const el = document.getElementById(t.id);
    if(!el) return;
    el.scrollIntoView({behavior:'smooth', block:'start'});
    el.classList.remove('xref-target');
    void el.offsetWidth;                              // 애니메이션 재시작
    el.classList.add('xref-target');
  }, 60);
}
document.addEventListener('click', function(e){
  const a = e.target.closest && e.target.closest('.xref');
  if(!a) return;
  e.preventDefault();
  gotoXref(a.dataset.code);
});
document.addEventListener('keydown', function(e){
  if(e.key !== 'Enter') return;
  const a = e.target.closest && e.target.closest('.xref');
  if(!a) return;
  e.preventDefault();
  gotoXref(a.dataset.code);
});
