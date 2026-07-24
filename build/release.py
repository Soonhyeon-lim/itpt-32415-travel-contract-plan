# -*- coding: utf-8 -*-
"""버전 스냅샷 빌더 — git 태그마다 그 시점의 기획서를 통째로 뽑는다.

    python build/release.py            모든 v* 태그 → dist/v1.0/ , dist/v1.1/ …
    python build/release.py v1.0       특정 태그만

각 태그를 임시 worktree 로 꺼내 거기서 빌드하므로 **작업 트리를 건드리지 않는다**.
(작업 중이던 파일이 있어도 안전하다)

왜 스냅샷인가
  기획서는 "그때 무엇으로 합의했나"가 핵심이라, 옛 버전이 최신 CSS·JS 로
  다시 그려지면 안 된다. 그래서 버전마다 그 시점 소스로 통째 빌드한다.
"""
import io, os, subprocess, sys, shutil, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(ROOT, "dist")
# 콘솔이 cp949 여도 한글·기호가 깨지지 않게 한다 (윈도우 기본 콘솔 대응)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass



# 자식 프로세스에게 UTF-8 출력을 강제한다.
# 지난 태그의 build.py 에는 콘솔 인코딩 대응이 없을 수 있으므로(그 시점 소스 그대로다)
# 부모가 환경변수로 못박아야 어느 판을 꺼내 빌드하든 출력이 깨지지 않는다.
CHILD_ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")


def git(*args, cwd=ROOT):
    r = subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=CHILD_ENV)
    if r.returncode:
        raise RuntimeError("git %s 실패:\n%s" % (" ".join(args), (r.stderr or "").strip()))
    return r.stdout.strip()


def tags():
    out = git("tag", "--list", "v*", "--sort=v:refname")
    return [t for t in out.split("\n") if t.strip()]


# 버전 스냅샷에서 예외로 두는 조각 — 그 시점 소스 대신 현재(HEAD 작업트리) 것으로 덮어쓴다.
# 히스토리 탭은 어느 판을 열든 전체 목록이 보여야 판끼리 오갈 수 있으므로, 옛 판에도 최신 이력을
# 주입한다. 스타일은 이 조각 안에 인라인으로 들어 있어 옛 시점 CSS 와 무관하게 함께 따라온다.
LIVE_FRAGMENTS = [os.path.join("src", "content", "history.html")]


def build_tag(tag):
    tmp = tempfile.mkdtemp(prefix="wt_")
    wt = os.path.join(tmp, "src")
    try:
        git("worktree", "add", "--detach", "--quiet", wt, tag)
        for rel in LIVE_FRAGMENTS:
            live = os.path.join(ROOT, rel)
            dst = os.path.join(wt, rel)
            if os.path.isfile(live) and os.path.isdir(os.path.dirname(dst)):
                shutil.copyfile(live, dst)
        r = subprocess.run([sys.executable, os.path.join(wt, "build", "build.py")],
                           cwd=wt, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=CHILD_ENV)
        if r.returncode:
            print("   빌드 실패:\n%s" % (r.stderr or r.stdout)); return False
        built = os.path.join(wt, "dist", "internal", "index.html")
        if not os.path.isfile(built):
            print("   산출물 없음"); return False
        dest_dir = os.path.join(DIST, tag)
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copyfile(built, os.path.join(dest_dir, "index.html"))
        size = os.path.getsize(built)
        print("   {:<8} → dist/{}/index.html  ({:,} bytes)".format(tag, tag, size))
        return True
    finally:
        try:
            git("worktree", "remove", "--force", wt)
        except Exception:
            pass
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    want = sys.argv[1:] or tags()
    if not want:
        print("v* 태그가 없다. 먼저 `git tag -a v1.0 -m ...` 로 판을 찍어라."); sys.exit(1)
    print("버전 스냅샷 빌드 — %d개" % len(want))
    ok = all([build_tag(t) for t in want])
    if ok:
        latest = want[-1]
        # 루트 진입점 — 최신판으로 보낸다.
        # 리다이렉트 페이지로 둔 이유: 모든 판이 /vX.Y/ 아래 있으면 판끼리 잇는 링크가
        # ../v1.1/ 같은 상대경로로 통일돼 웹서버에서도 file:// 에서도 똑같이 동작한다.
        io.open(os.path.join(DIST, "index.html"), "w", encoding="utf-8", newline="").write(
            '<!doctype html><html lang="ko"><head><meta charset="utf-8">\r\n'
            '<title>여행계약서 시스템 개선 기획서</title>\r\n'
            '<meta http-equiv="refresh" content="0; url=./%s/index.html">\r\n'
            '<link rel="canonical" href="./%s/index.html"></head>\r\n'
            '<body style="font-family:system-ui;padding:40px">\r\n'
            '최신판(%s)으로 이동합니다 — <a href="./%s/index.html">바로가기</a>\r\n'
            '</body></html>\r\n' % (latest, latest, latest, latest))
        print("\n최신판 = %s" % latest)
        print("   dist/index.html → %s 로 보내는 진입점 생성" % latest)
        print("\n배포 배치")
        print("   /          →  dist/index.html   (최신판으로 이동)")
        for t in want:
            print("   /%-9s →  dist/%s/index.html" % (t + "/", t))
    sys.exit(0 if ok else 1)
