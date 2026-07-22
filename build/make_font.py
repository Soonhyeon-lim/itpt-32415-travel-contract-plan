# -*- coding: utf-8 -*-
"""Pretendard Variable 서브셋을 만들어 src/styles/fonts.css 로 내장한다.

    uv run --with fonttools --with brotli python build/make_font.py
    ... --measure        후보 문자 집합별 용량만 재보고 파일은 쓰지 않는다

왜 서브셋인가
  전체 내장은 woff2 2.06MB → base64 2.7MB 라, 163KB 짜리 문서를 18배로 불린다.
  반면 CDN 참조를 남기면 폐쇄망·오프라인에서 대체글꼴(맑은 고딕)로 떨어지는데,
  맑은 고딕은 Regular·Bold 두 단계뿐이라 이 문서가 위계로 쓰는
  400/500/600/700/800 다섯 단계가 전부 뭉개진다. 그래서 서브셋이 유일한 답이다.

왜 KS X 1001 까지 넣나
  문서에 지금 쓰인 글자만 담으면 가장 작지만, 한 글자만 새로 써도 두부(□)가 뜬다.
  기획서는 계속 고쳐지는 문서라 그 함정이 실제로 밟힌다. euc-kr 로 인코딩되는
  한글 음절 2,350 자(KS X 1001 완성형)를 함께 넣어 편집 내성을 확보한다.
  그래도 안전망이 필요해서 build.py 가 매 빌드마다 문서 글자 ⊆ 서브셋을 검사한다.

가변 축(wght)은 유지한다 — 다섯 단계 굵기가 이 폰트를 쓰는 이유 그 자체다.
"""
import base64, io, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
VENDOR = os.path.join(HERE, "vendor", "PretendardVariable.woff2")
OUT_CSS = os.path.join(SRC, "styles", "fonts.css")
OUT_MANIFEST = os.path.join(SRC, "styles", "fonts.charset.json")

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, HERE)
import build as B  # noqa: E402  (조립 로직을 그대로 쓴다 — 두 벌 관리하지 않으려고)


TAG_RE = re.compile(r"<[^>]+>")
BLOCK_RE = re.compile(r"(?is)<(script|style)\b.*?</\1>")
# 화면에 글자로 드러나는 속성들 — 태그를 지우면 같이 사라지므로 따로 걷는다
ATTR_RE = re.compile(r'(?:title|alt|placeholder|aria-label)\s*=\s*"([^"]*)"', re.I)


def ensure_stub():
    """fonts.css 가 없으면 빈 파일을 먼저 만든다.

    index.html 이 fonts.css 를 include 하는데 그 파일을 만들려면 문서를 조립해야
    하는 순환이 생긴다(첫 생성·클린 체크아웃에서 실제로 걸린다). 스텁으로 끊는다.
    """
    if not os.path.isfile(OUT_CSS):
        with io.open(OUT_CSS, "w", encoding="utf-8", newline="") as f:
            f.write("/* 자리표시자 — make_font.py 가 채운다 */\r\n")


def document_text():
    """조립된 문서에서 '사람이 보는 글자'만 뽑는다.

    style/script 블록은 통째로 버린다 — 여기에 base64 가 들어가므로,
    버리지 않으면 '서브셋을 넣을수록 문자 집합이 커지는' 순환이 생긴다.
    """
    ensure_stub()
    meta = B.load_meta()
    html = B.apply_meta(B.expand(B.read(os.path.join(SRC, "index.html")), ["index.html"]), meta)
    body = BLOCK_RE.sub(" ", html)
    text = " ".join(ATTR_RE.findall(body)) + " " + TAG_RE.sub(" ", body)
    return html_unescape(text)


def html_unescape(s):
    import html
    return html.unescape(s)


def ks_x_1001_hangul():
    """KS X 1001 완성형 한글 음절 2,350 자.

    판정에 iso2022_kr 을 쓴다. 파이썬의 'euc_kr' 코덱은 실제로 CP949(UHC)라
    현대 한글 11,172 자를 전부 받아 주기 때문에 걸러지지 않는다(실측 11,309 자).
    """
    out = []
    for cp in range(0xAC00, 0xD7A4):
        ch = chr(cp)
        try:
            ch.encode("iso2022_kr")
        except UnicodeEncodeError:
            continue
        out.append(ch)
    return out


def charsets():
    doc = {c for c in document_text() if ord(c) > 0x20}
    ascii_printable = {chr(c) for c in range(0x20, 0x7F)}
    base = doc | ascii_printable
    return {
        "doc": sorted(base),
        "ksx1001": sorted(base | set(ks_x_1001_hangul())),
    }


def subset(chars, dest):
    """pyftsubset 호출. --font-features 를 지정하지 않으면 기본 기능만 남는다."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8",
                                     delete=False, newline="") as f:
        f.write("".join(chars))
        listfile = f.name
    try:
        cmd = [
            sys.executable, "-m", "fontTools.subset", VENDOR,
            "--text-file=" + listfile,
            "--output-file=" + dest,
            "--flavor=woff2",
            "--layout-features=*",
            "--drop-tables+=DSIG",
            # 가변 축을 고정하지 않는다 — 400~800 다섯 단계가 이 폰트의 존재 이유다
            "--no-hinting",
            "--desubroutinize",
            "--name-IDs=1,2,3,4,5,6",
            "--notdef-outline",
            "--recalc-bounds",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            raise RuntimeError("pyftsubset 실패:\n" + (r.stderr or r.stdout))
    finally:
        os.unlink(listfile)
    return os.path.getsize(dest)


CSS_TEMPLATE = """/* Pretendard Variable {version} — 서브셋 내장 (SIL OFL 1.1)
   Copyright (c) 2021 Kil Hyung-jin, with Reserved Font Name Pretendard.
   https://github.com/orioncactus/pretendard · 라이선스 전문 build/vendor/OFL.txt

   ⚠ 이 파일은 생성물이다. 직접 고치지 말고 아래를 다시 돌린다.
       uv run --with fonttools --with brotli python build/make_font.py

   글자 {count:,}자 (문서 실사용 + KS X 1001 완성형 2,350자) · woff2 {size:,} bytes
   가변 축 wght {axis} 유지 — 이 문서는 400/500/600/700/800 다섯 단계를 위계로 쓴다. */
@font-face{{
  font-family:'Pretendard Variable';
  font-weight:{axis};
  font-style:normal;
  font-display:swap;
  src:url(data:font/woff2;base64,{b64}) format('woff2-variations');
}}
"""


def wght_range(path):
    from fontTools.ttLib import TTFont
    f = TTFont(path)
    for a in f["fvar"].axes:
        if a.axisTag == "wght":
            return "%g %g" % (a.minValue, a.maxValue)
    raise RuntimeError("wght 축이 없다 — 가변 폰트가 아닌 것 같다")


def write_output(chars, woff2_path, size):
    b64 = base64.b64encode(open(woff2_path, "rb").read()).decode("ascii")
    css = CSS_TEMPLATE.format(
        version="v1.3.9", count=len(chars), size=size,
        axis=wght_range(woff2_path), b64=b64,
    ).replace("\n", "\r\n")          # 저장소 규칙 — 개행은 CRLF 고정
    with io.open(OUT_CSS, "w", encoding="utf-8", newline="") as f:
        f.write(css)
    manifest = {
        "source": "Pretendard Variable v1.3.9 (SIL OFL 1.1)",
        "note": "build.py 가 매 빌드마다 문서 글자가 이 범위 안인지 검사한다",
        "count": len(chars),
        "codepoints": sorted(ord(c) for c in chars),
    }
    with io.open(OUT_MANIFEST, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(manifest, ensure_ascii=False, indent=1).replace("\n", "\r\n"))
    return len(css)


if __name__ == "__main__":
    if not os.path.isfile(VENDOR):
        sys.exit("원본 폰트가 없다: build/vendor/PretendardVariable.woff2")
    sets = charsets()
    tmpdir = tempfile.mkdtemp()

    if "--measure" in sys.argv:
        print("원본 woff2 {:,} bytes\n".format(os.path.getsize(VENDOR)))
        for name, chars in sets.items():
            dest = os.path.join(tmpdir, name + ".woff2")
            size = subset(chars, dest)
            print("{:<10} 글자 {:>6,}자   woff2 {:>9,} bytes   base64 약 {:>9,} bytes"
                  .format(name, len(chars), size, size * 4 // 3))
        sys.exit(0)

    chars = sets["ksx1001"]
    dest = os.path.join(tmpdir, "subset.woff2")
    size = subset(chars, dest)
    css_len = write_output(chars, dest, size)
    print("서브셋 생성 완료")
    print("  글자      {:,}자 (문서 실사용 + KS X 1001 완성형)".format(len(chars)))
    print("  woff2     {:,} bytes  (원본 {:,} bytes 대비 {:.1%})"
          .format(size, os.path.getsize(VENDOR), size / os.path.getsize(VENDOR)))
    print("  → src/styles/fonts.css  {:,}자".format(css_len))
