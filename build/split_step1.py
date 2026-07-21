# -*- coding: utf-8 -*-
"""1단계 분리 — SC-02 실화면 임베드(hnt-contract-embed)만 src/embeds/로 격리.
원본은 건드리지 않고 읽기만 한다. 결과: src/index.html + src/embeds/sc02-contract.html
"""
import io, os, re, sys

SRC = r"C:\Users\HANA\Desktop\local-task\00. Task\2026\ITPT-32415(여행계약서 개편)\00. 요구사항\ITPT-32415_여행계약서_시스템개선_기획서_v1.1.html"
BASE = r"C:\Users\HANA\Desktop\local-task\00. Task\2026\ITPT-32415(여행계약서 개편)\01. 기획\HTMl_기획서"

# newline="" 필수 — 안 주면 CRLF가 LF로 변환돼 원본과 바이트 동일이 깨진다
s = io.open(SRC, encoding="utf-8", newline="").read()

MARK = '<div class="hnt-contract-embed"'
start = s.find(MARK)
if start < 0:
    print("!! hnt-contract-embed 시작 못 찾음"); sys.exit(1)

# div 깊이 세서 매칭되는 닫는 태그 찾기 (self-closing div는 HTML에 없음)
tok = re.compile(r'<div\b|</div>')
depth = 0
end = None
for m in tok.finditer(s, start):
    depth += 1 if m.group() == '<div' or m.group().startswith('<div') else -1
    if m.group() == '</div>':
        pass
    if depth == 0:
        end = m.end()
        break
if end is None:
    print("!! 매칭 </div> 못 찾음"); sys.exit(1)

block = s[start:end]
print("임베드 추출: {:,}자 ({:.1f}%)".format(len(block), len(block) / len(s) * 100))
print("  시작: %s..." % block[:60].replace("\n", " "))
print("  끝  : ...%s" % block[-60:].replace("\n", " "))

INCLUDE = "<!-- include: embeds/sc02-contract.html -->"
shell = s[:start] + INCLUDE + s[end:]

os.makedirs(os.path.join(BASE, "src", "embeds"), exist_ok=True)
io.open(os.path.join(BASE, "src", "embeds", "sc02-contract.html"), "w", encoding="utf-8", newline="").write(block)
io.open(os.path.join(BASE, "src", "index.html"), "w", encoding="utf-8", newline="").write(shell)

print()
print("src/index.html            {:>9,}자".format(len(shell)))
print("src/embeds/sc02-contract  {:>9,}자".format(len(block)))
print("합계 {:,} == 원본 {:,} + 마커 {} → {}".format(
    len(shell) + len(block), len(s), len(INCLUDE),
    "OK" if len(shell) + len(block) == len(s) + len(INCLUDE) else "MISMATCH"))
