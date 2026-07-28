// ── SC-03 하나허브 [보기 N] → 변경 내역 팝업 ──
// 목업이 실제로 동작해야 리뷰어가 "여기서 이렇게 뜬다"를 눌러서 확인할 수 있다.
// 0건 차수(1차)에는 .vbtn 자체가 없으므로 진입점 미노출 규칙이 목업에서도 지켜진다.
document.querySelectorAll('[data-hubpop]').forEach(function (btn) {
  var pop = document.getElementById(btn.dataset.hubpop);
  if (!pop) return;
  btn.addEventListener('click', function () { pop.classList.add('on'); });
  // 닫기 — × · [닫기] 버튼 · 딤 영역 클릭
  pop.querySelectorAll('[data-hubclose]').forEach(function (x) {
    x.addEventListener('click', function () { pop.classList.remove('on'); });
  });
  pop.addEventListener('click', function (e) {
    if (e.target === pop) pop.classList.remove('on');
  });
});
