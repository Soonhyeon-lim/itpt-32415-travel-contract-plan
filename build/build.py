# -*- coding: utf-8 -*-
"""ITPT-32415 기획서 빌드 — src/ 조각을 조립해 자기완결 단일 HTML 산출.

사용법:  python build/build.py            → dist/internal/index.html
        python build/build.py --verify   → 원본과 바이트 동일 여부까지 검증

설계 원칙
  - 의존성 0 (Python 표준 라이브러리만)
  - 산출물은 자기완결 = file:// 로 그냥 열려야 한다 (외부 리소스 참조 금지)
  - include 는 중첩 허용, 순환 참조는 오류로 잡는다
"""
import io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
DIST = os.path.join(ROOT, "dist")
# 콘솔이 cp949 여도 한글·기호가 깨지지 않게 한다 (윈도우 기본 콘솔 대응)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass


ORIGINAL = r"C:\Users\HANA\Desktop\local-task\00. Task\2026\ITPT-32415(여행계약서 개편)\00. 요구사항\ITPT-32415_여행계약서_시스템개선_기획서_v1.1.html"

INCLUDE_RE = re.compile(r'<!--\s*include:\s*([^\s>]+?)\s*-->')
# 마커가 그 줄에 홀로 있으면 "줄 전체(개행 포함)"를 치환한다.
# 덕분에 조각 파일이 개행으로 끝나도(= 일반적인 소스 파일 관례) 결과가 어긋나지 않는다.
LINE_INCLUDE_RE = re.compile(r'^[ \t]*<!--\s*include:\s*([^\s>]+?)\s*-->[ \t]*\r?\n', re.M)
MAX_DEPTH = 10


def read(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        return f.read()


def expand(text, stack):
    """include 마커를 재귀적으로 치환. stack = 순환 참조 검출용 경로 목록."""
    if len(stack) > MAX_DEPTH:
        raise RuntimeError("include 중첩이 %d단계를 넘음: %s" % (MAX_DEPTH, " > ".join(stack)))

    def repl(m):
        rel = m.group(1)
        path = os.path.normpath(os.path.join(SRC, rel))
        if not os.path.isfile(path):
            raise RuntimeError("include 대상 없음: %s  (참조: %s)" % (rel, stack[-1]))
        if rel in stack:
            raise RuntimeError("순환 참조: %s" % " > ".join(stack + [rel]))
        return expand(read(path), stack + [rel])

    text = LINE_INCLUDE_RE.sub(repl, text)   # 단독 줄 마커 → 줄 전체 치환
    return INCLUDE_RE.sub(repl, text)        # 줄 안에 섞인 마커 → 마커만 치환


PLACEHOLDER_RE = re.compile(r'\{\{(\w+)\}\}')


def load_meta():
    p = os.path.join(SRC, "meta.json")
    if not os.path.isfile(p):
        raise RuntimeError("src/meta.json 이 없다")
    return json.loads(read(p))


def apply_meta(text, meta):
    """{{key}} 를 meta 값으로 치환. 정의되지 않은 키는 오타이므로 오류로 잡는다."""
    missing = sorted({m.group(1) for m in PLACEHOLDER_RE.finditer(text)} - set(meta))
    if missing:
        raise RuntimeError("meta.json 에 없는 플레이스홀더: %s" % ", ".join(missing))
    return PLACEHOLDER_RE.sub(lambda m: str(meta[m.group(1)]), text)


# 버전 배지 — 그 판에서 새로 들어온 요소에만 표시한다.
#   <span class="ver-new" data-ver="1.1">v1.1</span>
# 빌드가 현재 판(meta.version)과 data-ver 를 대조해, 다르면 배지를 통째로 지운다.
# release.py 가 판마다 meta.version 을 주입하므로:
#   v1.1 스냅샷 → data-ver="1.1" 배지 표시 / v1.0·v1.2 스냅샷 → 자동 제거.
# 덕분에 판을 올려도 옛 배지를 손으로 뗄 필요가 없다(마커는 소스에 영구히 둔다).
VER_BADGE_RE = re.compile(r'<span class="ver-new" data-ver="([^"]+)">.*?</span>', re.S)


def apply_version_badges(text, meta):
    cur = str(meta.get("version", ""))
    def keep(m):
        return m.group(0) if m.group(1) == cur else ""
    return VER_BADGE_RE.sub(keep, text)


TAG_RE = re.compile(r'<[^>]+>')
BLOCK_RE = re.compile(r'(?is)<(script|style)\b.*?</\1>')
ATTR_RE = re.compile(r'(?:title|alt|placeholder|aria-label)\s*=\s*"([^"]*)"', re.I)
MANIFEST = os.path.join(SRC, "styles", "fonts.charset.json")


def check_glyphs(out):
    """문서 글자가 내장 서브셋 범위 안인지 검사한다.

    폰트를 서브셋으로 내장한 대가 — 없는 글자는 두부(□)로 뜬다. 눈으로는
    놓치기 쉬우므로 빌드가 막는다. 걸리면 make_font.py 를 다시 돌리면 된다.
    """
    if not os.path.isfile(MANIFEST):
        print("  ⚠ 폰트 매니페스트 없음 — 글자 검사 생략"); return True
    allowed = set(json.loads(read(MANIFEST))["codepoints"])
    body = BLOCK_RE.sub(" ", out)          # base64 가 든 style 블록은 검사 대상이 아니다
    import html as _html
    text = _html.unescape(" ".join(ATTR_RE.findall(body)) + " " + TAG_RE.sub(" ", body))
    missing = sorted({c for c in text if ord(c) > 0x20 and ord(c) not in allowed})
    # 이모지·기호는 애초에 Pretendard 에 없어 시스템 폰트로 넘어간다 — 검사에서 뺀다
    missing = [c for c in missing if not (0x2190 <= ord(c) <= 0x2BFF or ord(c) >= 0x1F000)]
    if missing:
        print("  ❌ 내장 폰트에 없는 글자 %d자 — 두부(□)로 뜬다:" % len(missing))
        print("     %s" % " ".join(missing[:40]))
        print("     → uv run --with fonttools --with brotli python build/make_font.py")
        return False
    print("  글자 검사 OK (내장 서브셋으로 전부 렌더됨)")
    return True


def build(target=None):
    meta = load_meta()
    entry = os.path.join(SRC, "index.html")
    out = apply_meta(expand(read(entry), ["index.html"]), meta)
    out = apply_version_badges(out, meta)   # 현재 판 것만 남기고 나머지 버전 배지는 제거
    if target is None:
        target = "internal"

    # 자기완결 점검 — 외부 리소스를 끌어오면 오프라인/폐쇄망에서 깨진다.
    # 속성(src/href)뿐 아니라 CSS 의 @import·url() 까지 본다.
    ext = re.findall(r'(?:src|href)\s*=\s*["\'](https?://[^"\']+)', out)
    ext += re.findall(r'@import\s+url\(\s*[\'"]?(https?://[^\'")]+)', out)
    ext += re.findall(r'url\(\s*[\'"]?(https?://[^\'")]+)', out)
    ext = [u for u in ext if not u.startswith("http://www.w3.org")]  # SVG 네임스페이스 제외
    ext = sorted(set(ext))

    outdir = os.path.join(DIST, target)
    os.makedirs(outdir, exist_ok=True)
    dest = os.path.join(outdir, "index.html")
    with io.open(dest, "w", encoding="utf-8", newline="") as f:
        f.write(out)

    print("빌드 완료  →  dist/%s/index.html  ({:,}자)  [v%s · %s]"
          .format(len(out)) % (target, meta["version"], meta["date"]))
    if ext:
        print("  ⚠ 외부 리소스 참조 %d건 (file:// 에서 깨질 수 있음):" % len(ext))
        for u in ext[:5]:
            print("     -", u[:90])
    else:
        print("  자기완결 OK (외부 리소스 참조 0건)")
    glyphs_ok = check_glyphs(out)
    return dest, out, glyphs_ok


BASELINE = os.path.join(HERE, "baseline.html")


def set_baseline(out):
    """현재 산출물을 기준선으로 고정. 의도적으로 내용을 바꾼 직후에만 쓴다."""
    with io.open(BASELINE, "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print("\n기준선 갱신 → build/baseline.html ({:,}자)".format(len(out)))


def verify(out):
    """회귀 검증 — 기준선과 바이트 동일해야 한다.

    1~3단계(파일 분리)에서는 기준선이 분리 전 원본이었고, 그래서 '분리가 무손실인가'를
    증명했다. 이후로는 의도적으로 내용을 고칠 때마다 --set-baseline 으로 기준선을 옮기고,
    그 사이의 뜻하지 않은 변화를 이 검증이 잡는다.
    """
    ref = BASELINE if os.path.isfile(BASELINE) else ORIGINAL
    if not os.path.isfile(ref):
        print("  기준선·원본 모두 없어 검증 생략"); return False
    orig = read(ref)
    same = (orig == out)
    print()
    print("=== 기준선 대조 (%s) ===" % os.path.basename(ref))
    print("  기준 {:,}자 / 빌드 {:,}자".format(len(orig), len(out)))
    if same:
        print("  ✅ 바이트 동일 — 회귀 0")
    else:
        print("  ❌ 불일치 (의도한 변경이면 --set-baseline 으로 기준선을 옮긴다)")
        for i, (a, b) in enumerate(zip(orig, out)):
            if a != b:
                print("     첫 차이 위치 %d" % i)
                print("     원본: %r" % orig[max(0, i-40):i+40])
                print("     빌드: %r" % out[max(0, i-40):i+40])
                break
        else:
            print("     길이만 다름 (앞부분은 동일)")
    return same


if __name__ == "__main__":
    # --release : 현재 상태를 meta.json 의 버전으로 스냅샷 (dist/v1.0/index.html)
    tgt = "v" + load_meta()["version"] if "--release" in sys.argv else None
    dest, out, ok = build(tgt)
    if "--verify" in sys.argv:
        ok = verify(out) and ok
    if "--set-baseline" in sys.argv:
        set_baseline(out)          # 글자 검사 실패는 기준선을 옮겨도 덮이지 않는다
    sys.exit(0 if ok else 1)
