# 여행계약서 시스템 개선 기획서 — 빌드 구조 (ITPT-32415)

통짜 HTML 한 개였던 기획서를 **소스는 분리 / 산출물은 단일 파일**로 재구성한 저장소.

## 왜 이렇게 하나

- 이 문서의 최대 강점은 **파일 하나 보내면 어디서나 열린다**는 것 → 산출물은 계속 **자기완결 단일 HTML**로 유지한다.
  (런타임 `fetch` 방식은 `file://` 에서 CORS로 막혀 공유성을 잃으므로 채택하지 않음)
- 대신 소스를 쪼개서 **git diff·리뷰·재사용**이라는 개발 방식의 이점을 얻는다.
- 분리 전에는 실화면 임베드 한 줄이 **25,190자**여서 diff가 사실상 무의미했다.

## 사용법

```bash
python build/build.py                  # → dist/internal/index.html
python build/build.py --verify         # 기준선(build/baseline.html)과 바이트 동일한지 검증
python build/build.py --set-baseline   # 의도적으로 내용을 고친 직후 기준선을 옮긴다
python build/build.py --release        # 현재 상태를 meta.json 의 버전으로 → dist/v1.0/
python build/release.py                # 모든 v* 태그를 각자 스냅샷으로 빌드
```

`--verify` 는 회귀 그물이다. 1~3단계(파일 분리)에서는 기준선이 분리 전 원본이었고
그래서 "분리가 무손실인가"를 증명했다. 이후로는 내용을 고칠 때마다 기준선을 옮기고,
그 사이의 **뜻하지 않은 변화**를 이 검증이 잡는다.

의존성 없음(Python 표준 라이브러리만). 이 환경 venv에 pip이 없어서 의도적으로 무의존으로 설계했다.
예외는 폰트 서브셋 생성(`build/make_font.py`) 하나뿐이고, 그것도 `uv run --with` 로
격리 실행해 시스템 환경을 건드리지 않는다. **평소 빌드에는 필요 없다** — 생성물인
`src/styles/fonts.css` 가 저장소에 들어 있어서, 콘텐츠에 새 글자가 들어올 때만 다시 돌린다.

## 구조

```
src/
  index.html                    셸 — include 마커로 조각을 불러온다
  meta.json                     버전·날짜·지라·팀 — 표기의 유일한 출처
  styles/
    fonts.css                   [생성물] Pretendard Variable 서브셋 base64
    fonts.charset.json          [생성물] 내장 글자 목록 — 빌드 검사 기준
    tokens.css                  :root 토큰 · reset · body
    base.css                    Layout · 섹션코드 xref 링크 · Cover
    components.css              callout · card · table · flow · topbar · subtab
    screens.css                 화면정의 전용 (폰 프레임 · 계약서 탭 · 변경내역표 · admin grid)
  scripts/
    tabs.js · subtabs.js · ct-tabs.js · scrollspy.js · xref.js
  embeds/
    sc02-contract.html          SC-02 mqatour 실화면 임베드 (전체의 44.9%)
  content/
    plan/improve/               IM-01 배경목적 · IM-02 범위 · IM-03 정책확정요약
                                IM-04 개선항목상세 · IM-05 기대효과AC
    plan/logic/                 LG-01 변경내역도출로직 · LG-02 항목별구현로직
                                LG-03 변경지점 · LG-04 개발확인
    plan/existing/              AS-01 교부라이프사이클 · AS-02 문구차수규칙
    screens/                    SC-01 조회진입 · SC-02 계약서조회동의 · SC-03 하나허브교부내역
    history.html · refs.html
build/
  build.py                      조립 + meta 주입 + 자기완결 점검 + 글자 검사 + 기준선 대조
  make_font.py                  폰트 서브셋 생성 (fonttools 필요 — uv 로 격리 실행)
  release.py                    git 태그별 스냅샷 빌드 (임시 worktree 사용)
  vendor/                       Pretendard Variable 원본 woff2 + OFL 라이선스
  baseline.html                 회귀 검증 기준선
  split_step*.py                각 단계 분리에 쓴 일회성 스크립트 (이력 보존용)
dist/                           빌드 산출물 (git 제외)
  index.html                    최신판으로 보내는 진입점
  v1.0/index.html               버전 스냅샷
  internal/index.html           작업 중 상태
```

## 폰트

Pretendard Variable 을 **서브셋으로 내장**한다. CDN `@import` 를 쓰지 않는다.

```bash
uv run --with fonttools --with brotli python build/make_font.py
uv run --with fonttools --with brotli python build/make_font.py --measure   # 용량만 비교
```

`build/vendor/PretendardVariable.woff2`(원본 2.06MB) → 서브셋 450KB → base64 로
`src/styles/fonts.css` 에 박힌다. 문서는 163KB → 764KB 가 된다.

**왜 내장하나.** CDN 참조를 남기면 폐쇄망·오프라인에서 대체글꼴(맑은 고딕)로 떨어지는데,
맑은 고딕은 Regular·Bold **두 단계뿐**이다. 이 문서는 400/500/600/700/800 **다섯 단계**를
정보 위계로 쓰므로, 대체되는 순간 강조 체계가 통째로 평평해진다. 레이아웃만 유지되면
되는 문제가 아니었다.

**왜 전체가 아니라 서브셋인가.** 전체 내장은 base64 2.7MB 라 문서가 18배로 불어난다.

**왜 KS X 1001 까지 넣나.** 문서에 지금 쓰인 글자만 담으면 128KB 로 더 작지만, 한 글자만
새로 써도 두부(□)가 뜬다. 이 문서는 계속 고쳐지므로 한글 음절 2,350자를 함께 넣어
편집 내성을 확보했다. 그래도 안전망으로 **빌드가 매번 「문서 글자 ⊆ 서브셋」을 검사**하고,
벗어나면 빌드를 실패시킨다(`fonts.charset.json` 이 그 기준).

> 판정에 `iso2022_kr` 을 쓴다. 파이썬의 `euc_kr` 코덱은 실제로 CP949(UHC)라
> 현대 한글 11,172자를 전부 받아 줘서 걸러지지 않는다(실측 11,309자 → 서브셋 1.74MB).

`fonts.css` 와 `fonts.charset.json` 은 **생성물**이다. 직접 고치지 말 것.

**임베드 주의** — SC-02 실화면 임베드의 인라인 스택은 하나투어 원본 그대로라 첫 항목이
`Pretendard`(static 판 이름)다. 내장 폰트는 `Pretendard Variable` 이라 이름이 맞물리지 않아
그대로 두면 그 블록만 맑은 고딕으로 떨어진다. 원본 파일은 손대지 않고 `screens.css` 에서
`.hnt-contract-embed{font-family:var(--font)!important}` 로 되돌린다(인라인 `style=` 이라
`!important` 가 아니면 못 이긴다).

## 버전 표기

`meta.json` 이 유일한 출처다. 문서 안에서는 `{{version}}` `{{date}}` `{{jira}}`
`{{title}}` `{{shortTitle}}` `{{team}}` 로 쓰고 빌드가 채운다.
meta.json 에 없는 키를 쓰면 빌드가 오류로 잡는다(오타 방지).

전에는 버전 문자열이 title·상단바·LNB·커버 배지·갱신일 등 7곳에 흩어져 있어
하나라도 놓치면 문서가 어긋났다.

## 버전 스냅샷

판을 하나 찍을 때:

```bash
# 1) meta.json 의 version·date 를 올린다
# 2) 히스토리 표에 새 행을 추가하고, 지난 판의 버전 칸을 링크로 바꾼다
#      <td><a href="../v1.0/index.html"><b>v1.0</b></a></td>
git commit -am "v1.1 …"
git tag -a v1.1 -m "…"
python build/release.py          # dist/v1.0/, dist/v1.1/, dist/index.html
```

`release.py` 는 각 태그를 **임시 worktree** 로 꺼내 그 시점 소스로 빌드한다.
작업 트리를 건드리지 않으므로 작업 중이어도 안전하다.

옛 판이 최신 CSS·JS 로 다시 그려지지 않는 것이 핵심이다 — 기획서는
"그때 무엇으로 합의했나"가 내용이라, 판마다 그 시점 그대로 남아야 한다.

배포는 `dist/` 를 정적 루트로 두면 된다. 모든 판이 `/vX.Y/` 아래 있어서
판끼리 잇는 링크가 `../vX.Y/` 상대경로로 통일되고, 웹서버에서도 `file://`
에서도 똑같이 동작한다.

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
- [x] **3단계 — 콘텐츠 섹션 분리** (16개 조각, 바이트 동일 검증 통과)
      → `src/index.html` 이 5,855자 순수 셸이 됐다. 섹션 한 곳을 고치면
        diff 도 `1 file changed, 1 insertion(+)` 로 그 파일에만 잡힌다(실측 확인).
- [x] **v1.0 초판 지정** (2026-07-21) — 대외 배포 첫 판. 내부 작업 이력은 git 에만 남기고
      문서 히스토리는 v1.0 한 줄로 시작. 버전 표기 5곳 동기화.
- [x] **4단계 — `meta.json` + 버전 스냅샷 빌드** (`dist/v1.0/`, 태그별 worktree 빌드, 루트 진입점)
- [x] **폰트 내장** (2026-07-22) — variable 판 + 버전 핀 → 서브셋 base64 내장.
      **외부 리소스 0건 달성**. 글자 검사로 두부(□) 방지, 서브셋 재생성해도 빌드는 바이트 동일(결정적).
- [ ] (보안 검토 후) 공개용 축약 빌드 `dist/shared/` — 내부 API명·관리자 화면·개발확인 제외

## 규칙 — 어기면 검증이 깨진다

1. **개행은 CRLF.** 원본이 CRLF라 `.gitattributes`에서 `* -text`로 자동 변환을 껐고,
   스크립트는 읽기·쓰기 모두 `newline=""` 를 쓴다. (1단계에서 이걸 빠뜨려 1,393자 차이가 났었다)
2. **산출물에 외부 리소스를 넣지 않는다.** `http(s)` 참조가 생기면 오프라인·폐쇄망에서 깨진다.
   빌드가 `src`/`href` 뿐 아니라 CSS 의 `@import`·`url()` 까지 점검해 경고한다.
   ✅ **0건 달성** — 폰트까지 서브셋으로 내장했다(아래 「폰트」).
3. **원본(`00. 요구사항/…_v1.1.html`)은 아직 정본이다.** 이 저장소가 검증될 때까지 원본을 지우지 않는다.

## 정본 관계

- 기획서는 **HTML이 단일 정본**. 중복이던 `기획서_v1.1.md`는 폐기 대상.
- `여행계약서_서비스정책(안)_v0.4.md` 는 **별개 문서로 계속 유지**한다(7축 정책 상세).
- ~~`0_여행계약서_개편_통합정본.md`~~ — **2026-07-22 폐기·삭제.** 구 SSOT였으나 v0.3(07-14)에서
  갱신이 멈춰 07-20~21 결정 4건이 미반영이었다. 정본이 둘이면 헷갈리므로 이 HTML로 일원화했다.
  백업은 `00. 요구사항\_archive_삭제본\`.

## 배포

GitHub(Private) → Vercel 정적 호스팅.

```
/            →  dist/index.html      최신판으로 이동
/v1.0        →  dist/v1.0/index.html
```

`vercel.json` 이 `outputDirectory: dist` 를 지정하므로 **빌드 단계가 없다.**
빌드된 판(`dist/vX.Y/`)을 커밋해 두기 때문이다. 그 이유는:

- Vercel 빌드 환경에 파이썬·git 태그가 있는지에 배포가 좌우되지 않는다
  (`release.py` 는 태그를 worktree 로 꺼내므로 얕은 클론에서는 동작하지 않는다)
- 공개된 판이 git 에 그대로 남아 "그때 무엇을 내보냈나"를 나중에 확인할 수 있다
- 판은 자주 늘지 않아 저장소가 비대해지지 않는다

작업 중 빌드(`dist/internal/`)는 커밋하지 않는다.

### 새 판 배포

```bash
# meta.json 의 version·date 수정 → 히스토리 표에 행 추가
git commit -am "v1.1 …" && git tag -a v1.1 -m "…"
python build/release.py        # dist/v1.0/, dist/v1.1/, dist/index.html 갱신
git add dist && git commit -m "release v1.1" && git push --follow-tags
```

푸시하면 Vercel 이 자동 배포한다.

### 접근 통제

- **검색 색인 차단** — `vercel.json` 의 `X-Robots-Tag: noindex, nofollow, noarchive`
  + `dist/robots.txt`. 링크를 아는 사람만 본다.
- ⚠️ **URL 을 아는 사람은 누구나 열람 가능하다**(무료 플랜 기준). 더 막으려면
  Edge Middleware 로 Basic Auth 를 세우거나 Vercel 의 Password Protection(유료)을 쓴다.
- HTML 은 브라우저로 전달되는 순간 소스가 읽힌다. 난독화로는 막을 수 없으므로,
  통제가 필요하면 **접근**(위)이나 **내용**(공개용 축약 빌드)에서 다뤄야 한다.
