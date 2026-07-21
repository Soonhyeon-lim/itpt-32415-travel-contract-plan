# -*- coding: utf-8 -*-
"""2단계 분리 — <style>/<script> 인라인 블록을 src/styles, src/scripts 로 격리.

전제: 빌드는 '단독 줄 마커 = 줄 전체 치환' 규칙을 쓴다.
      따라서 조각 파일은 개행으로 끝나야 하고, 마커도 각자 제 줄을 차지한다.
1단계 임베드 파일도 이 규칙에 맞춰 끝 개행을 보정한다.
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
NL = "\r\n"

# (파일명, 시작줄, 끝줄) — 1-based, 끝줄 포함. CSS 주석 섹션 경계에서 끊었다.
# 줄번호는 태그 바로 뒤 개행을 뺀 '실제 코드 1번째 줄' 기준.
CSS_PARTS = [
    ("tokens.css",     1,  20),   # :root 토큰 · reset · body
    ("base.css",      21,  59),   # Layout · 섹션코드 xref 링크 · Cover
    ("components.css", 60, 244),  # Section · callout · card · table · flow · concept · topbar · subtab
    ("screens.css",   245, None), # 화면정의 전용: 폰 프레임 · 계약서 탭 · 변경내역표 · admin grid · description
]                                 # None = 블록 끝까지
JS_PARTS = [
    ("tabs.js",       1,   9),
    ("subtabs.js",   10,  18),
    ("ct-tabs.js",   19,  32),
    ("scrollspy.js", 33,  55),
    ("xref.js",      56, None),
]


def read(p):
    return io.open(p, encoding="utf-8", newline="").read()


def write(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline="").write(t)


def carve(block, parts, subdir, kind):
    """block(태그 내부 원문)을 parts 대로 잘라 파일로 쓰고, 마커 텍스트를 돌려준다."""
    lines = block.split(NL)
    # 블록은 NL 로 시작·끝난다. 선두 개행은 여는 태그 쪽(<style>\r\n)이 맡고,
    # 말미 빈 요소는 버려서 '실제 코드 줄'만 남긴다.
    if lines and lines[0] == "":
        lines = lines[1:]
    if lines and lines[-1] == "":
        lines = lines[:-1]
    total = len(lines)
    # 조각 경계가 블록 전체를 빠짐없이 덮는지 먼저 확인 (누락/중복 방지)
    covered = []
    for _, a, b in parts:
        covered.append((a, total if b is None else b))
    if covered[0][0] != 1 or covered[-1][1] != total:
        print("!! %s 경계가 블록을 다 덮지 않음: %s / 실제 1~%d" % (kind, covered, total)); sys.exit(1)
    for (a1, b1), (a2, _) in zip(covered, covered[1:]):
        if a2 != b1 + 1:
            print("!! %s 경계 불연속: %d~%d 다음이 %d" % (kind, a1, b1, a2)); sys.exit(1)

    markers = []
    for (name, a, _), (_, b) in zip(parts, covered):
        chunk = NL.join(lines[a - 1:b]) + NL          # 조각은 개행으로 끝난다
        write(os.path.join(SRC, subdir, name), chunk)
        markers.append("<!-- include: %s/%s -->" % (subdir, name))
        print("   %-16s L%-4d~%-4d  %7d자" % (name, a, b, len(chunk)))
    return NL.join(markers) + NL


s = read(os.path.join(SRC, "index.html"))

# ── 1단계 임베드 파일: 끝 개행 보정 (새 규칙과 맞추기) ──
emb_path = os.path.join(SRC, "embeds", "sc02-contract.html")
emb = read(emb_path)
if not emb.endswith(NL):
    write(emb_path, emb + NL)
    print("1단계 임베드 파일 끝 개행 보정 (+%d자)" % len(NL))

print("\n[CSS]")
m = re.search(r"<style>(.*?)</style>", s, re.S)
css_markers = carve(m.group(1), CSS_PARTS, "styles", "CSS")
s = s[:m.start()] + "<style>" + NL + css_markers + "</style>" + s[m.end():]

print("\n[JS]")
m = re.search(r"<script>(.*?)</script>", s, re.S)
js_markers = carve(m.group(1), JS_PARTS, "scripts", "JS")
s = s[:m.start()] + "<script>" + NL + js_markers + "</script>" + s[m.end():]

write(os.path.join(SRC, "index.html"), s)
print("\nsrc/index.html  →  {:,}자".format(len(s)))
