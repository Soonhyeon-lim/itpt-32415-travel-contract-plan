# -*- coding: utf-8 -*-
"""ITPT-32415 기획서 빌드 — src/ 조각을 조립해 자기완결 단일 HTML 산출.

사용법:  python build/build.py            → dist/internal/index.html
        python build/build.py --verify   → 원본과 바이트 동일 여부까지 검증

설계 원칙
  - 의존성 0 (Python 표준 라이브러리만)
  - 산출물은 자기완결 = file:// 로 그냥 열려야 한다 (외부 리소스 참조 금지)
  - include 는 중첩 허용, 순환 참조는 오류로 잡는다
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
DIST = os.path.join(ROOT, "dist")

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


def build(target="internal"):
    entry = os.path.join(SRC, "index.html")
    out = expand(read(entry), ["index.html"])

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

    print("빌드 완료  →  dist/%s/index.html  ({:,}자)".format(len(out)) % target)
    if ext:
        print("  ⚠ 외부 리소스 참조 %d건 (file:// 에서 깨질 수 있음):" % len(ext))
        for u in ext[:5]:
            print("     -", u[:90])
    else:
        print("  자기완결 OK (외부 리소스 참조 0건)")
    return dest, out


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
    dest, out = build()
    ok = True
    if "--verify" in sys.argv:
        ok = verify(out)
    if "--set-baseline" in sys.argv:
        set_baseline(out); ok = True
    sys.exit(0 if ok else 1)
