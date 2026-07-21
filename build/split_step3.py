# -*- coding: utf-8 -*-
"""3단계 분리 — 콘텐츠 섹션을 src/content/ 로 격리.

IM/LG/AS 섹션·SC 화면·history·refs 를 각각 파일로 뽑는다.
이 단계부터 "IM-04만 고쳤다"가 git diff 에 그대로 드러난다.

경계는 1-based·양끝 포함. 아래에서 위로 치환해 줄번호가 밀리지 않게 한다.
"""
import io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
NL = "\r\n"

# (출력경로, 시작줄, 끝줄)  — src/content/ 기준
REGIONS = [
    ("plan/improve/IM-01-배경목적.html",      81,  98),
    ("plan/improve/IM-02-범위.html",         100, 146),
    ("plan/improve/IM-03-정책확정요약.html",  148, 168),
    ("plan/improve/IM-04-개선항목상세.html",  170, 236),
    ("plan/improve/IM-05-기대효과AC.html",    238, 257),

    ("plan/logic/LG-01-변경내역도출로직.html", 263, 331),
    ("plan/logic/LG-02-항목별구현로직.html",   333, 373),
    ("plan/logic/LG-03-변경지점.html",         375, 397),
    ("plan/logic/LG-04-개발확인.html",         399, 414),

    ("plan/existing/AS-01-교부라이프사이클.html", 420, 511),
    ("plan/existing/AS-02-문구차수규칙.html",     513, 556),

    ("screens/SC-01-조회진입.html", 581, 613),
    ("screens/SC-02-계약서조회동의.html", 615, 683),
    ("screens/SC-03-하나허브교부내역.html", 685, 730),

    ("history.html", 737, 756),
    ("refs.html",    759, 781),
]


def read(p):
    return io.open(p, encoding="utf-8", newline="").read()


def write(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline="").write(t)


idx = os.path.join(SRC, "index.html")
lines = read(idx).split(NL)

# 겹침 검사 — 아래에서 위로 처리하기 전에 먼저 확인한다
ordered = sorted(REGIONS, key=lambda r: r[1])
for (n1, a1, b1), (n2, a2, _) in zip(ordered, ordered[1:]):
    if a2 <= b1:
        print("!! 영역 겹침: %s(%d~%d) 와 %s(%d~)" % (n1, a1, b1, n2, a2)); sys.exit(1)

total = 0
for name, a, b in sorted(REGIONS, key=lambda r: r[1], reverse=True):
    chunk = NL.join(lines[a - 1:b]) + NL
    write(os.path.join(SRC, "content", name), chunk)
    lines[a - 1:b] = ["<!-- include: content/%s -->" % name]
    total += len(chunk)
    print("   {:<44} L{:<4}~{:<4} {:>7,}자".format(name, a, b, len(chunk)))

write(idx, NL.join(lines))
print("\n분리 합계 {:,}자 / 조각 {}개".format(total, len(REGIONS)))
print("src/index.html  →  {:,}자".format(len(NL.join(lines))))
