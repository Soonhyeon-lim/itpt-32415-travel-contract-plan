# 여행계약서 시스템 개선 기획서 — 빌드 구조 (ITPT-32415)

통짜 HTML 한 개였던 기획서를 **소스는 분리 / 산출물은 단일 파일**로 재구성한 저장소.

## 왜 이렇게 하나

- 이 문서의 최대 강점은 **파일 하나 보내면 어디서나 열린다**는 것 → 산출물은 계속 **자기완결 단일 HTML**로 유지한다.
  (런타임 `fetch` 방식은 `file://` 에서 CORS로 막혀 공유성을 잃으므로 채택하지 않음)
- 대신 소스를 쪼개서 **git diff·리뷰·재사용**이라는 개발 방식의 이점을 얻는다.
- 분리 전에는 실화면 임베드 한 줄이 **25,190자**여서 diff가 사실상 무의미했다.

## 사용법

```bash
python build/build.py            # → dist/internal/index.html
python build/build.py --verify   # 빌드 결과가 원본과 바이트 동일한지까지 검증
```

의존성 없음(Python 표준 라이브러리만). 이 환경 venv에 pip이 없어서 의도적으로 무의존으로 설계했다.

## 구조

```
src/
  index.html                    셸 — include 마커로 조각을 불러온다
  styles/
    tokens.css                  :root 토큰 · reset · body
    base.css                    Layout · 섹션코드 xref 링크 · Cover
    components.css              callout · card · table · flow · topbar · subtab
    screens.css                 화면정의 전용 (폰 프레임 · 계약서 탭 · 변경내역표 · admin grid)
  scripts/
    tabs.js · subtabs.js · ct-tabs.js · scrollspy.js · xref.js
  embeds/
    sc02-contract.html          SC-02 mqatour 실화면 임베드 (전체의 44.9%)
build/
  build.py                      조립 + 자기완결 점검 + 원본 대조
  split_step1.py                1단계 분리에 쓴 일회성 스크립트 (이력 보존용)
dist/
  internal/index.html           빌드 산출물 (git 제외)
```

`include` 문법은 한 가지뿐이다:

```html
<!-- include: embeds/sc02-contract.html -->
```

중첩 가능하고, 순환 참조와 없는 파일은 빌드가 오류로 잡는다.

**마커가 그 줄에 홀로 있으면 줄 전체(개행 포함)를 치환한다.** 덕분에 조각 파일이
개행으로 끝나도(= 일반적인 소스 파일 관례) 결과가 어긋나지 않는다.
줄 안에 섞여 있으면 마커 자리만 바뀐다.

## 진행 상태

- [x] **1단계 — 실화면 임베드 격리** (44.9% 분리, 원본과 바이트 동일 검증 통과)
- [x] **2단계 — CSS·JS 분리** (CSS 4개 · JS 5개, 바이트 동일 검증 통과)
- [ ] 3단계 — 콘텐츠 섹션 분리 (IM/LG/AS·SC·history·refs)
- [ ] 4단계 — `meta.json` + 버전 스냅샷 빌드(`dist/v1.1/`), 히스토리 탭 버전 링크
- [ ] (보안 검토 후) 공개용 축약 빌드 `dist/shared/` — 내부 API명·관리자 화면·개발확인 제외

## 규칙 — 어기면 검증이 깨진다

1. **개행은 CRLF.** 원본이 CRLF라 `.gitattributes`에서 `* -text`로 자동 변환을 껐고,
   스크립트는 읽기·쓰기 모두 `newline=""` 를 쓴다. (1단계에서 이걸 빠뜨려 1,393자 차이가 났었다)
2. **산출물에 외부 리소스를 넣지 않는다.** `http(s)` 참조가 생기면 오프라인·폐쇄망에서 깨진다.
   빌드가 `src`/`href` 뿐 아니라 CSS 의 `@import`·`url()` 까지 점검해 경고한다.
   ⚠️ **현재 1건 미해결** — `tokens.css` 가 Pretendard 웹폰트를 jsdelivr CDN 에서 `@import` 한다.
   인터넷이 없으면 폰트만 대체글꼴로 떨어진다(레이아웃은 유지). 폐쇄망 배포 시 폰트 내장 검토.
3. **원본(`00. 요구사항/…_v1.1.html`)은 아직 정본이다.** 이 저장소가 검증될 때까지 원본을 지우지 않는다.

## 정본 관계

- 기획서는 **HTML이 단일 정본**. 중복이던 `기획서_v1.1.md`는 폐기 대상.
- `0_여행계약서_개편_통합정본.md` · `여행계약서_서비스정책(안)_v0.4.md` 는 **별개 문서로 계속 유지**한다.
