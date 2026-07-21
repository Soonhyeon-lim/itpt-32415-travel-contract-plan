// ── 화면정의 스크롤스파이 ──
const scrLinks = [...document.querySelectorAll('.scr-nav a')];
const scrMap = {};
scrLinks.forEach(a=>{const el=document.getElementById(a.getAttribute('href').slice(1));if(el)scrMap[el.id]=a;});
if(scrLinks.length){
  const scrObs = new IntersectionObserver((es)=>{es.forEach(e=>{if(e.isIntersecting){scrLinks.forEach(l=>l.classList.remove('active'));const a=scrMap[e.target.id];if(a)a.classList.add('active');}});},{rootMargin:'-30% 0px -60% 0px',threshold:0});
  Object.keys(scrMap).forEach(id=>scrObs.observe(document.getElementById(id)));
}

// 스크롤스파이 — 현재 섹션 TOC 하이라이트
const links = [...document.querySelectorAll('.toc a')];
const map = {};
links.forEach(a=>{const id=a.getAttribute('href').slice(1);const el=document.getElementById(id);if(el)map[id]=a;});
const obs = new IntersectionObserver((entries)=>{
  entries.forEach(e=>{
    if(e.isIntersecting){
      links.forEach(l=>l.classList.remove('active'));
      const a=map[e.target.id]; if(a)a.classList.add('active');
    }
  });
},{rootMargin:'-45% 0px -50% 0px',threshold:0});
Object.keys(map).forEach(id=>obs.observe(document.getElementById(id)));

